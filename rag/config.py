from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
CHAT_MODEL = os.environ.get("RAG_CHAT_MODEL", "qwen2.5:0.5b")
EMBED_MODEL = os.environ.get("RAG_EMBED_MODEL", "all-minilm")
OLLAMA_URL = "http://127.0.0.1:11434"
CARRIERS = ("Atlas", "Beacon", "Cedar")

