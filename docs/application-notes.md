# Application and interview notes

## Project title
Supply Chain Evidence Assistant — Hybrid RAG and LLM-Planned Analytics Agent

## Short description
Built a local supply-chain assistant combining version-aware document retrieval, dense embeddings, read-only SQL analytics, constrained LLM planning, cited evidence composition, and persistent review approvals. It supports PDF ingestion, source inspection, evaluation reporting, and a responsive browser interface.

## Resume bullets
- Built a hybrid RAG assistant using BM25, local dense embeddings, reciprocal rank fusion, and relevance reranking; increased recall@4 from 70% to 90% on 30 manually labeled synthetic retrieval questions.
- Implemented an LLM-planned workflow with allowlisted analytics tools, bounded retries, canonical evidence facts, provenance checks, persistent investigation history, and local approval state; passed 36 automated tests and 29 evaluation checks.

These are completed capabilities and measured local results. Do not call this an industrial deployment or imply access to real customer data.

## Questions to prepare for
1. Why combine keyword and dense retrieval?
   Exact identifiers and policy terms favor keywords; paraphrases benefit from embeddings. The benchmark compares both and preserves per-query failures.
2. Why filter before ranking?
   Carrier and effective-month filters prevent an otherwise highly ranked but inapplicable policy version from reaching the answer.
3. Why not ask the LLM to calculate delivery rates?
   Fixed SQL computes deterministic metrics; the model chooses tools and relevant supporting facts.
4. What makes this agentic?
   The model selects tools, plans evidence gathering, can repair empty retrieval once, and chooses cited facts for the response. Execution is bounded by application controls.
5. How are hallucinated numbers handled?
   The model cannot directly write arbitrary numeric claims into the final answer. The renderer accepts known evidence IDs and renders their canonical text.
6. What is the trade-off?
   Answers are constrained/extractive and less conversational. Source checking does not prove truth or completeness.
7. How did you evaluate it?
   Thirty manually labeled retrieval questions, 29 workflow checks including live inference, 36 automated tests, and browser verification. The corpus is small and synthetic.
8. What would you improve for a real customer?
   Larger representative evaluation data, authorization controls, a stronger chat model, learned reranking if justified, OCR when required, production observability, and real operational integration.

## Submission
Use the hiring form in the job post. Upload or link this project only where the form permits it. No resume or application has been sent by this project.

