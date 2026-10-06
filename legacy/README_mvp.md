# Supply Chain Evidence Assistant

First runnable MVP for a RAG and agentic AI portfolio.

## Run
Requires Python 3.12. No third-party dependencies for the baseline.

```powershell
cd D:\RAG
python app.py
```

Open http://127.0.0.1:8000. Stop using Ctrl+C.

Run verification:
```powershell
python -m unittest -v
```

## Included
- BM25 document retrieval with carrier and effective-month filters.
- Six fictional, versioned policies and 120 reproducible synthetic shipments.
- Parameterized, read-only SQLite tools calculating on-time delivery and monthly changes.
- Conditional workflow: validate request, select analytics, retrieve evidence, render sources.
- Visible document citations, shipment IDs, assumptions, and workflow trace.
- Optional local Ollama model generation. The model draft remains labeled unverified.

## Optional local model
If Ollama is installed and running with llama3.2 downloaded, enable the checkbox.
Set OLLAMA_MODEL before launching Python to choose another installed model.
Only the fixed local endpoint at 127.0.0.1:11434 is contacted.
Unavailable models fall back to the extractive evidence baseline.

Without a model, output is extractive evidence, not LLM-generated text.
Tool routing is currently rule-based: this is an agentic workflow scaffold, not an LLM-planned agent.

## Example questions
- Why did Atlas delivery performance decline in 2026-02 and which SLA policies apply?
- What SLA policy applies to Atlas in 2026-01?
- What escalation policy applies to Cedar late delivery in 2026-02?
- What is Beacon delivery performance in 2026-03? (missing-data demonstration)

## Architecture
Browser -> local Python server -> request validation -> conditional SQL analytics
-> version-filtered BM25 retrieval -> evidence output -> optional local LLM draft.

## Next development steps
1. Semantic embeddings and hybrid retrieval, benchmarked against this BM25 baseline.
2. Schema-validated LLM tool selection with bounded retries.
3. PDF ingestion, chunking, reranking, and section citations.
4. Labeled evaluations for retrieval recall, citation accuracy, numeric correctness, and abstention.
5. Prompt-injection evaluations and claim-level checks for generated answers.

All data and policies are fictional. This is a local development demo.
Current limits: small corpus, monthly version filters, no semantic search or reranking,
and no automatic factual verification of generated model drafts.
Report only completed capabilities in your application.

