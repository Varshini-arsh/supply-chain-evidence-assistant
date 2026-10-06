# Three-minute demonstration

Before recording, start the application and confirm that the sidebar reports both local AI and embeddings ready. Choose Agentic AI + hybrid RAG.

## 0:00-0:25 — Problem
“Operations teams need explanations grounded in agreements and shipment records. This assistant combines document retrieval with read-only analytics and an LLM-planned workflow.”

Show the 18-document corpus and 120 synthetic shipment records. State that the data is fictional.

## 0:25-1:20 — Flagship investigation
Select Atlas and February 2026. Ask:
“Why did delivery performance decline and which SLA policies apply?”

Show:
- 65% February on-time delivery.
- 7 late shipments out of 20.
- -25 percentage points versus January.
- Effective February agreement with its 95% delivery target.
- Recorded breakdown/weather exceptions and the causal-evidence limitation.

Open a metric citation, then a document citation. Show the exact underlying records and source sentence.

## 1:20-1:50 — Agent behavior
Explain the workflow trace: schema-validated planning, approved tools, document retrieval, constrained composition, and provenance checks.

“The model chooses evidence tools and relevant fact IDs. SQL computes the numbers. The final renderer uses exact evidence facts so invented fact IDs are rejected.”

Stage a carrier review and approve the local record. Explain that no external notification is sent.

## 1:50-2:20 — Historical sources and abstention
Switch to January and ask which SLA applies. The historical Atlas agreement has a 90% target, demonstrating time-aware retrieval.

Switch to March and ask for delivery performance. The assistant reports missing shipment evidence.

## 2:20-2:45 — PDF ingestion
Open the document library, download the sample PDF, then upload it with an explicit carrier and effective month. Show page-preserving chunks.

## 2:45-3:00 — Measured evidence
Open Evaluation lab:
“On 30 manually labeled synthetic questions, recall@4 increased from 70% to 90% with hybrid retrieval. All 29 workflow checks passed, and 36 automated tests passed. These are development results on a small corpus.”

Finish by showing saved investigation history and JSON export.

## Recording guidance
Keep local-model waiting periods short in the recording, but do not disguise them as instantaneous performance. The saved live trace records actual elapsed time. Avoid claims of production readiness, perfect accuracy, or company affiliation.

