# Supply Chain Evidence Assistant

A complete local portfolio application demonstrating **hybrid RAG and an LLM-planned, evidence-backed agent workflow** for supply-chain investigations.

Ask why a carrier's delivery performance changed, retrieve the agreement effective in that month, inspect supporting shipment records, and stage a local carrier review for approval.

All bundled business data is synthetic. This project is independently built; it is not affiliated with DecisionOpt.

## Start on this machine

```powershell
cd D:\RAG
.\start.ps1
```

Open **http://127.0.0.1:8000**.

The startup script starts the installed Ollama service if necessary and uses the project's model directory. The chat model and embedding model have already been downloaded on this machine.

You can also run `python app.py` directly. If Ollama is stopped, use the offline evidence mode or BM25 baseline from the interface. Stop the Python server with Ctrl+C.

## Set up a fresh checkout

Requires Python 3.12+, Windows PowerShell for the convenience scripts, and Ollama for the AI modes. The Python application itself also works without PowerShell.

```powershell
.\setup.ps1
.\start.ps1
```

Setup creates a virtual environment, installs pypdf, and downloads qwen2.5:0.5b plus all-minilm (about 450 MB combined). Use `setup.ps1 -SkipModels` for offline-only setup. Use `-Dev` to install browser-test dependencies.

Manual installation:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe create_sample_pdf.py
.\.venv\Scripts\python.exe app.py
```

For model inference, start Ollama and install the chat and embedding models. The service uses its own model directory; the convenience scripts use `D:\RAG\models` when starting it. An already-running service keeps its existing model directory.

Configuration:
- `RAG_CHAT_MODEL`: default `qwen2.5:0.5b`.
- `RAG_EMBED_MODEL`: default `all-minilm`.
- `python app.py --port 8001`: alternate port.
- Inference calls use the fixed local endpoint `http://127.0.0.1:11434`.

## What the application does

**RAG**
- Ingests text-based PDFs, Markdown, and TXT files through the interface or CLI.
- Splits content into overlapping chunks with page and section provenance.
- Filters by carrier and policy effective month before retrieval.
- Combines BM25 keyword ranking with dense cosine similarity using reciprocal rank fusion.
- Reranks candidates using lexical, semantic, and title relevance.
- Caches embeddings in SQLite by text and model.
- Shows source text, policy versions, document IDs, and retrieval scores.

**Agentic AI**
- Uses the local chat model to choose allowlisted evidence tools.
- Executes fixed read-only shipment queries and previous-month comparisons.
- Validates tool plans, retries invalid plans, and performs one retrieval repair when needed.
- Uses constrained model composition: the model selects relevant canonical fact IDs.
- Checks selected fact IDs and provenance before rendering exact supported facts.
- Persists investigations, tool traces, and approval decisions.
- Supports staged local carrier reviews with explicit approve/reject decisions.
- Discloses model failures and retrieval fallbacks.

**Interface**
- Investigation workspace with verified KPI cards.
- Source inspection dialogs and JSON exports.
- Document library with PDF upload.
- Evaluation dashboard and persistent investigation history.
- Responsive desktop and mobile layouts.

## Data and demo

The seed corpus has **18 fictional versioned documents** and **120 synthetic shipments** across Atlas, Beacon, and Cedar in January-February 2026.

Try:
1. Atlas / February: “Why did delivery performance decline and which SLA policies apply?”
2. Atlas / January: “What SLA agreement applies?”
3. Cedar / February: “What escalation procedure applies to vehicle breakdown delays?”
4. Beacon / March: “What is delivery performance?” — missing-data abstention.
5. Atlas / February: “How much refund amount can we claim?” — contractual evidence limit.

For the flagship scenario, SQL calculates 65% on-time delivery in February against 90% in January, a change of -25 percentage points. The February agreement specifies a 95% target. Recorded exceptions are not treated as proof of causality.

## GitHub results folder

[Results and screenshots](results/README.md) contains the result images, measured reports, raw traces, and a GitHub-ready README.

## Verified results

- **36 automated tests passed**, including unit and HTTP integration tests.
- **29/29 evaluation workflow checks passed**, including a real local-model planner and composer.
- On **30 manually labeled synthetic retrieval questions**, recall@4 was **70% for BM25** and **90% for hybrid retrieval**.
- Browser verification exercises desktop/mobile layout, citations, PDF upload, approvals, JSON export, history replay, and evaluation display.

Measured reports:
- [Evaluation results](reports/evaluation.md)
- [Machine-readable evaluation](reports/evaluation.json)
- [Live agent evidence](reports/live_agent.json)
- [Browser checks](reports/browser-checks.json)
- [Live agent UI screenshot](reports/desktop-agentic.png)
- [Desktop investigation screenshot](reports/desktop-investigation.png)
- [Mobile investigation screenshot](reports/mobile-investigation.png)

These results describe this small development dataset. They do not establish production performance or general accuracy.

## Reproduce

```powershell
python -m unittest -v
python evaluate.py
python ui_check.py
```

Evaluation needs both local models for the full live checks. `python evaluate.py --skip-live` skips chat checks; hybrid retrieval still requires the embedding model and discloses any fallback.

Browser tests require Playwright and Microsoft Edge. On this machine, the test-only packages live in `.dev-deps`; a fresh environment can install `requirements-dev.txt`. Browser tests use a temporary isolated database and do not add fixtures to the main document library.

CLI investigation:

```powershell
python app.py --question "Atlas delivery performance decline in 2026-02 and SLA policies" --ai
python ingest_document.py data\sample-policy.pdf --title "Recovery handbook" --carrier Atlas --start 2026-02
```

## Project structure

```text
app.py                       HTTP API and entry point
rag/agent.py                 Planning, evidence tools, composition, approval state
rag/retrieval.py             BM25, dense search, fusion, reranking
rag/models.py                Local chat and embedding client
rag/ingest.py                PDF/text ingestion
rag/store.py                 SQLite state and shipment tools
static/                      Browser interface
data/                        Seed documents, shipments, labeled queries, sample PDF
tests/                       Isolated workflow, ingestion, and HTTP tests
reports/                     Actual evaluations, live trace, and screenshots
docs/                        Architecture, demonstration, and application notes
start.ps1 / setup.ps1         Startup and environment setup
package_project.py           Shareable source ZIP (excludes models and databases)
legacy/                      Preserved original MVP
```

## Engineering limits

The agent composes answers by selecting exact evidence facts rather than producing unrestricted prose. This makes numerical/source checks straightforward, but does not prove source truth or answer completeness.

The relevance reranker is a deterministic score combination, not a learned cross-encoder. PDF OCR is not included. Suspicious instruction detection is a limited quarantine heuristic, not a complete prompt-injection defense. Uploads are stored as extracted chunks, not original files. This is a local portfolio application, not a production deployment.

See [architecture](docs/architecture.md), [demo walkthrough](docs/demo.md), and [application notes](docs/application-notes.md).

Implementation references: [Ollama structured chat API](https://docs.ollama.com/api/chat), [Ollama embedding API](https://docs.ollama.com/api/embed), [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).

