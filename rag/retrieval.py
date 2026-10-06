import collections
import math
import re
from . import store, models

STOP=set("a an the is are was were of for to in on and or with what why how which when please carrier atlas beacon cedar month 2026 01 02 03 apply applies policy policies tell me about does do can you i it this that".split())

def terms(text):
    return [t for t in re.findall(r"[a-z0-9]+",text.lower()) if t not in STOP and not t.isdigit()]

def cosine(a,b):
    if len(a)!=len(b):
        raise models.ModelError("Embedding dimensions do not match.")
    return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)) or 1)

def search(query,carrier,month,k=4,mode="hybrid"):
    docs=store.chunks(carrier,month)
    if not docs or not terms(query):
        return {"chunks":[],"backend":"bm25","warning":None}
    counts=[collections.Counter(terms(d["title"]+" "+d["section"]+" "+d["text"])) for d in docs]
    avg=sum(sum(c.values()) for c in counts)/len(counts)
    lexical=[]
    for count in counts:
        score=0
        for term in set(terms(query)):
            tf=count[term]
            df=sum(term in c for c in counts)
            score+=math.log(1+(len(docs)-df+.5)/(df+.5))*tf*2.5/(tf+1.5*(.25+.75*sum(count.values())/max(avg,1)))
        lexical.append(score)
    semantic=[0.0]*len(docs)
    warning=None
    backend="bm25"
    if mode=="hybrid":
        try:
            vectors=models.embed([query]+[d["title"]+"\n"+d["text"] for d in docs])
            semantic=[cosine(vectors[0],v) for v in vectors[1:]]
            backend="hybrid: BM25 + dense embeddings + RRF + relevance reranking"
        except models.ModelError as error:
            warning=str(error)+"; BM25 fallback used."
    lexical_order=sorted(range(len(docs)),key=lambda i:-lexical[i])
    semantic_order=sorted(range(len(docs)),key=lambda i:-semantic[i])
    lr={i:rank+1 for rank,i in enumerate(lexical_order)}
    sr={i:rank+1 for rank,i in enumerate(semantic_order)}
    maximum=max(lexical) or 1
    scored=[]
    for i,d in enumerate(docs):
        # Require lexical evidence or sufficient dense relevance; exclude unrelated topics.
        if lexical[i]<=0 and (backend=="bm25" or semantic[i]<.45):
            continue
        rrf=1/(60+lr[i])+(1/(60+sr[i]) if backend!="bm25" else 0)
        coverage=len(set(terms(query)) & set(terms(d["title"]+" "+d["section"])))/max(len(set(terms(query))),1)
        rerank=.45*(lexical[i]/maximum)+.45*max(semantic[i],0)+.1*coverage
        score=.65*(rrf*30)+.35*rerank
        scored.append({**d,"score":round(score,5),"lexical_score":round(lexical[i],5),"semantic_score":round(semantic[i],5),"rerank_score":round(rerank,5)})
    return {"chunks":sorted(scored,key=lambda d:(-d["score"],d["id"]))[:k],"backend":backend,"warning":warning}

