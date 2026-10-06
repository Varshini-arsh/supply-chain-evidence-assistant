import json
import math
import urllib.error
import urllib.request
from .config import OLLAMA_URL, CHAT_MODEL, EMBED_MODEL
from . import store

class ModelError(RuntimeError):
    pass

def request(path,payload=None,timeout=90):
    req=urllib.request.Request(OLLAMA_URL+path,data=json.dumps(payload).encode() if payload is not None else None,headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            return json.load(response)
    except (OSError,ValueError) as error:
        raise ModelError(f"Local model request failed: {type(error).__name__}") from error

def health():
    try:
        names=[m["name"] for m in request("/api/tags",timeout=2).get("models",[])]
        return {"available":True,"models":names,"chat_model":CHAT_MODEL,"embed_model":EMBED_MODEL,
                "chat_ready":any(n==CHAT_MODEL or n==CHAT_MODEL+":latest" for n in names),
                "embed_ready":any(n==EMBED_MODEL or n==EMBED_MODEL+":latest" for n in names)}
    except ModelError:
        return {"available":False,"models":[],"chat_model":CHAT_MODEL,"embed_model":EMBED_MODEL,"chat_ready":False,"embed_ready":False}

def embed(texts):
    result=[store.cached_embedding(EMBED_MODEL,t) for t in texts]
    missing=[i for i,v in enumerate(result) if v is None]
    for start in range(0,len(missing),12):
        batch=missing[start:start+12]
        data=request("/api/embed",{"model":EMBED_MODEL,"input":[texts[i] for i in batch],"truncate":False,"keep_alive":"2m"})
        vectors=data.get("embeddings")
        if not isinstance(vectors,list) or len(vectors)!=len(batch):
            raise ModelError("Embedding response has an invalid shape.")
        for i,v in zip(batch,vectors):
            if not isinstance(v,list) or not v or not all(isinstance(x,(float,int)) and math.isfinite(x) for x in v):
                raise ModelError("Embedding response contains an invalid vector.")
            result[i]=v
            store.save_embedding(EMBED_MODEL,texts[i],v)
    return result

def structured(system,user,schema,max_tokens=400):
    response=request("/api/chat",{"model":CHAT_MODEL,"stream":False,"format":schema,"messages":[{"role":"system","content":system},{"role":"user","content":user}],
                                 "options":{"temperature":0,"num_ctx":4096,"num_predict":max_tokens},"keep_alive":"2m"},timeout=120)
    try:
        value=json.loads(response["message"]["content"])
    except (KeyError,TypeError,ValueError) as error:
        raise ModelError("Chat model did not return valid JSON.") from error
    if not isinstance(value,dict):
        raise ModelError("Expected a JSON object.")
    return value

