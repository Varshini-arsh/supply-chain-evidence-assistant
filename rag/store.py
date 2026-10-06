import collections
import datetime as dt
import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager, closing
from .config import DATA, CARRIERS

INJECTION = re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|system|above)\s+instructions|reveal\s+(?:the\s+)?(?:system\s+prompt|secrets)|(?:system|assistant)\s*:\s*(?:ignore|override)|execute\s+(?:shell|sql)|drop\s+table", re.I)

@contextmanager
def connect():
    db = sqlite3.connect(DATA / "knowledge.sqlite3", timeout=30)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def valid_month(value):
    if not isinstance(value, str) or not re.fullmatch(r"20\d{2}-\d{2}", value):
        raise ValueError("Dates must use YYYY-MM.")
    dt.date.fromisoformat(value + "-01")
    return value

def split_text(text, size=140, overlap=25):
    words = text.split()
    if not words:
        return []
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size-overlap)]

def add_document(doc, pages=None):
    if doc["carrier"] not in (*CARRIERS, "all"):
        raise ValueError("Unsupported carrier.")
    valid_month(doc["start"])
    if doc.get("end"):
        valid_month(doc["end"])
        if doc["end"] < doc["start"]:
            raise ValueError("End date precedes start date.")
    pages = pages or [(1, doc["text"])]
    parts = []
    for page, text in pages:
        heading = doc["title"]
        # Headings are retained as section metadata, then bounded word chunks.
        for section in re.split(r"(?m)(?=^#{1,3} )", text):
            first = section.splitlines()[0] if section.strip() else ""
            if first.startswith("#"):
                heading = first.lstrip("# ").strip()
                section = "\n".join(section.splitlines()[1:])
            for part in split_text(section):
                parts.append((page, heading, part))
    if not parts:
        raise ValueError("No text could be extracted. Scanned PDFs require OCR.")
    quarantine = bool(INJECTION.search("\n".join(t for _,_,t in parts)))
    metadata = {k: v for k,v in doc.items() if k != "text"}
    metadata["quarantined"] = quarantine
    metadata["chunk_count"] = len(parts)
    with connect() as db:
        db.execute("INSERT INTO documents(id,metadata) VALUES (?,?)", (doc["id"],json.dumps(metadata)))
        db.executemany("INSERT INTO chunks(id,document_id,page,section,text) VALUES (?,?,?,?,?)",
                       [(f"{doc['id']}:p{p}:c{i+1}", doc["id"], p, h, t) for i,(p,h,t) in enumerate(parts)])
    return metadata

def initialize():
    DATA.mkdir(exist_ok=True)
    with connect() as db:
        db.executescript("""
CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY,document_id TEXT NOT NULL,page INTEGER NOT NULL,section TEXT NOT NULL,text TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS embeddings(cache_key TEXT PRIMARY KEY,vector TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,created TEXT NOT NULL,result TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,state TEXT NOT NULL,payload TEXT NOT NULL);
""")
        ids = {r[0] for r in db.execute("SELECT id FROM documents")}
    seed = json.loads((DATA/"documents.json").read_text(encoding="utf-8-sig"))
    seed += json.loads((DATA/"extra_documents.json").read_text(encoding="utf-8-sig"))
    for doc in seed:
        if doc["id"] not in ids:
            add_document({**doc, "source_name": doc["id"]+".md", "synthetic": True})
    # Preserve the original reproducible shipment database.
    with closing(sqlite3.connect(DATA/"shipments.sqlite3")) as db:
        db.execute("CREATE TABLE IF NOT EXISTS shipments (id TEXT PRIMARY KEY,carrier TEXT,month TEXT,promised TEXT,delivered TEXT,exception TEXT)")
        if not db.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]:
            rows = []
            for carrier, counts in [("Atlas",[2,7]),("Beacon",[4,3]),("Cedar",[1,5])]:
                for month, late_count in enumerate(counts,1):
                    for i in range(20):
                        promised = dt.date(2026,month,i+1)
                        late = i<late_count
                        delivered = promised+dt.timedelta(days=2 if late else 0)
                        reason = ("vehicle_breakdown" if i%2==0 else "weather") if late else "none"
                        rows.append((f"{carrier}-{month}-{i}",carrier,f"2026-{month:02}",str(promised),str(delivered),reason))
            db.executemany("INSERT INTO shipments VALUES (?,?,?,?,?,?)", rows)
        db.commit()

def documents():
    with connect() as db:
        return [json.loads(r["metadata"]) for r in db.execute("SELECT metadata FROM documents ORDER BY id")]

def chunks(carrier, month):
    with connect() as db:
        rows = db.execute("SELECT c.*,d.metadata FROM chunks c JOIN documents d ON d.id=c.document_id").fetchall()
    result = []
    for row in rows:
        meta = json.loads(row["metadata"])
        if meta["quarantined"] or meta["carrier"] not in ("all",carrier) or meta["start"] > month or (meta.get("end") and month>meta["end"]):
            continue
        result.append({**meta, "id":row["id"],"document_id":row["document_id"],"page":row["page"],"section":row["section"],"text":row["text"]})
    return result

def source(chunk_id):
    with connect() as db:
        row = db.execute("SELECT c.*,d.metadata FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.id=?",(chunk_id,)).fetchone()
    return {**dict(row),"metadata":json.loads(row["metadata"])} if row else None

def embedding_key(model,text):
    return hashlib.sha256((model+"\0"+text).encode()).hexdigest()

def cached_embedding(model,text):
    with connect() as db:
        row = db.execute("SELECT vector FROM embeddings WHERE cache_key=?",(embedding_key(model,text),)).fetchone()
    return json.loads(row[0]) if row else None

def save_embedding(model,text,vector):
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO embeddings VALUES (?,?)",(embedding_key(model,text),json.dumps(vector)))

def shipment_metrics(carrier,month):
    if carrier not in CARRIERS:
        return {"carrier":carrier,"month":month,"total":0,"late":0,"on_time_pct":None,"exceptions":{},"late_shipment_ids":[]}
    valid_month(month)
    with closing(sqlite3.connect((DATA/"shipments.sqlite3").as_uri()+"?mode=ro",uri=True)) as db:
        rows = db.execute("SELECT id,promised,delivered,exception FROM shipments WHERE carrier=? AND month=? ORDER BY id",(carrier,month)).fetchall()
    late = [r for r in rows if r[2]>r[1]]
    return {"carrier":carrier,"month":month,"total":len(rows),"late":len(late),"on_time_pct":round(100*(len(rows)-len(late))/len(rows),2) if rows else None,
            "exceptions":dict(collections.Counter(r[3] for r in late)),"late_shipment_ids":[r[0] for r in late]}

def save_run(result):
    with connect() as db:
        db.execute("INSERT INTO runs VALUES (?,?,?)",(result["run_id"],dt.datetime.now(dt.timezone.utc).isoformat(),json.dumps(result)))

def history(limit=15):
    with connect() as db:
        rows=db.execute("SELECT id,created,result FROM runs ORDER BY created DESC LIMIT ?",(limit,)).fetchall()
    return [{"run_id":r["id"],"created":r["created"],"question":json.loads(r["result"])["question"],"status":json.loads(r["result"])["status"]} for r in rows]

def load_run(run_id):
    with connect() as db:
        row=db.execute("SELECT result FROM runs WHERE id=?",(run_id,)).fetchone()
    return json.loads(row[0]) if row else None

