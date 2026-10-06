"""Run with: python app.py. Local-only supply-chain evidence application."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from rag import agent, ingest, models, retrieval, store
from rag.config import ROOT, REPORTS

initialize=store.initialize
metrics=store.shipment_metrics
answer=agent.answer

def retrieve(query,carrier,month,k=4):
    # Compatibility with original MVP API: preserve parent document IDs.
    return [{**c,"chunk_id":c["id"],"id":c["document_id"]} for c in retrieval.search(query,carrier,month,k,mode="bm25")["chunks"]]

POOL=concurrent.futures.ThreadPoolExecutor(max_workers=2)
JOBS={}
JOBS_LOCK=threading.Lock()

def new_job(payload):
    with JOBS_LOCK:
        # Bound memory growth and reject excessive concurrent model requests.
        for key in list(JOBS):
            if JOBS[key].done() and len(JOBS)>=100:
                del JOBS[key]
        if sum(not f.done() for f in JOBS.values())>=4:
            raise ValueError("Investigation queue is full. Wait for a current run to finish.")
        job_id=uuid.uuid4().hex
        JOBS[job_id]=POOL.submit(agent.answer,payload["question"],payload.get("use_llm",False),payload.get("retrieval_mode","hybrid"))
    return job_id

class Handler(BaseHTTPRequestHandler):
    def respond(self,code,value,kind="application/json"):
        body=json.dumps(value).encode() if kind=="application/json" else value
        self.send_response(code)
        self.send_header("Content-Type",kind)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed=urlparse(self.path)
        path=parsed.path
        args=parse_qs(parsed.query)
        one=lambda key: args.get(key,[""])[0]
        static={"/":("static/index.html","text/html; charset=utf-8"),
                "/style.css":("static/style.css","text/css; charset=utf-8"),
                "/ui.js":("static/ui.js","text/javascript; charset=utf-8"),
                "/sample-policy.pdf":("data/sample-policy.pdf","application/pdf")}
        if path in static:
            filename,kind=static[path]
            target=ROOT/filename
            if not target.exists():
                self.respond(404,{"error":"File not found."})
            else:
                self.respond(200,target.read_bytes(),kind)
            return
        if path=="/favicon.ico":
            self.respond(204,b"","image/x-icon")
            return
        if path=="/api/status":
            docs=store.documents()
            self.respond(200,{"models":models.health(),"documents":len(docs),"chunks":sum(d["chunk_count"] for d in docs),"quarantined":sum(d["quarantined"] for d in docs),"synthetic_shipments":120,"carriers":["Atlas","Beacon","Cedar"],"months":["2026-01","2026-02"]})
        elif path=="/api/documents":
            self.respond(200,store.documents())
        elif path=="/api/source":
            source=store.source(one("id"))
            self.respond(200 if source else 404,source or {"error":"Source not found."})
        elif path=="/api/runs":
            self.respond(200,store.history())
        elif path=="/api/run":
            result=store.load_run(one("id"))
            self.respond(200 if result else 404,result or {"error":"Run not found."})
        elif path=="/api/jobs":
            with JOBS_LOCK:
                future=JOBS.get(one("id"))
            if future is None:
                self.respond(404,{"error":"Job not found."})
            elif not future.done():
                self.respond(200,{"state":"running"})
            else:
                try:
                    self.respond(200,{"state":"complete","result":future.result()})
                except Exception:
                    self.respond(500,{"error":"Investigation failed. Check the server log."})
        elif path=="/api/evaluation":
            report=REPORTS/"evaluation.json"
            self.respond(200,json.loads(report.read_text(encoding="utf-8")) if report.exists() else {"status":"not_run"})
        elif path=="/api/reviews":
            self.respond(200,agent.pending_reviews())
        else:
            self.respond(404,{"error":"Endpoint not found."})

    def do_POST(self):
        # Browser cross-origin requests cannot set this custom header without a preflight.
        if self.headers.get("X-RAG-Client")!="local-ui":
            self.respond(403,{"error":"Missing local application header."})
            return
        origin=self.headers.get("Origin")
        if origin and urlparse(origin).netloc!=self.headers.get("Host"):
            self.respond(403,{"error":"Cross-origin requests are not allowed."})
            return
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=8*1024*1024:
                raise ValueError("Request is empty or exceeds 8 MB.")
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict):
                raise ValueError("Expected a JSON object.")
            path=urlparse(self.path).path
            if path in ("/api/ask","/api/jobs"):
                if not isinstance(payload.get("question"),str) or len(payload["question"])>2500 or not isinstance(payload.get("use_llm",False),bool):
                    raise ValueError("Invalid question or AI mode.")
                if payload.get("retrieval_mode","hybrid") not in ("hybrid","bm25"):
                    raise ValueError("Invalid retrieval mode.")
                if path=="/api/jobs":
                    value={"job_id":new_job(payload)}
                else:
                    value=agent.answer(payload["question"],payload.get("use_llm",False),payload.get("retrieval_mode","hybrid"))
            elif path=="/api/ingest":
                value=ingest.ingest(payload)
            elif path=="/api/reviews/stage":
                value=agent.stage_review(payload.get("run_id",""))
            elif path=="/api/reviews/decide":
                value=agent.decide_review(payload.get("approval_id",""),payload.get("decision"))
            else:
                self.respond(404,{"error":"Endpoint not found."})
                return
            self.respond(200,value)
        except (ValueError,TypeError,KeyError) as error:
            self.respond(400,{"error":str(error)})
        except Exception as error:
            print(f"Request error: {type(error).__name__}: {error}",flush=True)
            self.respond(500,{"error":"Internal error. Check server logs."})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8000)
    parser.add_argument("--question")
    parser.add_argument("--ai",action="store_true")
    parser.add_argument("--bm25",action="store_true")
    args=parser.parse_args()
    initialize()
    if args.question:
        print(json.dumps(agent.answer(args.question,args.ai,"bm25" if args.bm25 else "hybrid"),indent=2))
        return
    print(f"Supply Chain Evidence Assistant: http://127.0.0.1:{args.port}",flush=True)
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.",flush=True)
    finally:
        server.server_close()

if __name__=="__main__":
    main()

