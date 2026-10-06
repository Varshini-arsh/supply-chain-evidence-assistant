import argparse
import json
from rag import ingest, store

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Ingest a PDF, Markdown, or TXT source.")
    parser.add_argument("path")
    parser.add_argument("--title",required=True)
    parser.add_argument("--carrier",choices=["all","Atlas","Beacon","Cedar"],default="all")
    parser.add_argument("--start",default="2026-01")
    parser.add_argument("--end")
    args=parser.parse_args()
    store.initialize()
    print(json.dumps(ingest.ingest_file(args.path,args.title,args.carrier,args.start,args.end),indent=2))

