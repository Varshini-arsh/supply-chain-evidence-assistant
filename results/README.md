# Results and screenshots

Evidence from the Supply Chain Evidence Assistant, a local hybrid RAG and LLM-planned analytics project. All bundled business records and policies are synthetic.

## Verified results

| Check | Observed result |
|---|---|
| Automated unit and HTTP tests | 36 passed, 0 failed |
| Workflow evaluation checks | 29 / 29 passed |
| Labeled retrieval questions | 30 |
| BM25 recall@4 | 70% |
| Hybrid retrieval recall@4 | 90% |
| Live local-model planning and composition | Passed |
| Desktop/mobile browser flows | Passed, no page errors |
| Historical policy filtering and missing-data handling | Passed in fresh screenshot capture |

Retrieval measurements come from a small manually labeled synthetic corpus. They do not establish general accuracy or production performance. Answers use constrained selection of supported evidence facts rather than unrestricted prose generation.

## Live AI investigation

The February Atlas result shows 65% on-time delivery, seven late shipments out of 20, and a change of -25 percentage points from January. The cited February agreement specifies a 95% target. The trace shows local-model planning, hybrid retrieval, composition, and source checks.

![Live AI results](screenshots/01-live-ai-results.png)

## Source evidence

The source dialog displays the actual retrieved agreement text and its effective period.

![Retrieved policy evidence](screenshots/02-source-evidence.png)

## Evaluation dashboard

![Evaluation results](screenshots/06-evaluation-results.png)

## Additional screenshots

- [Mobile AI results](screenshots/03-mobile-ai-results.png)
- [Historical January agreement](screenshots/04-historical-policy.png): the 90% target is selected; February's version is excluded.
- [Missing-data response](screenshots/05-missing-data.png): March performance is withheld because records are absent.
- [Workspace](screenshots/07-workspace.png)
- [PDF ingestion and document library](screenshots/08-pdf-ingestion-library.png): captured by the browser test using an isolated fixture database.

## Machine-readable evidence

- [Evaluation report](reports/evaluation.md)
- [Per-query retrieval results and workflow checks](reports/evaluation.json)
- [Final recorded verification summary](reports/verification.json)
- [Browser checks](reports/browser-checks.json)
- [Live agent trace](reports/live_agent.json)
- [Fresh screenshot checks and underlying results](reports/capture-checks.json)
- [Retrieval comparison CSV](retrieval-comparison.csv)
- [Artifact SHA-256 manifest](manifest.json)

## Reproduce

Run these commands from the project root:

```powershell
python -m unittest -v
python evaluate.py
python ui_check.py
python capture_results.py
```

The screenshot command requires the app at http://127.0.0.1:8000, both local models, Playwright, and Microsoft Edge. It writes fresh screenshots directly into results/screenshots. The evaluation and browser commands write their full reports into reports at the project root; copy updated reports into this folder when refreshing the GitHub results.

Include this entire results folder in the GitHub repository so relative image links render in this README. Model weights, local databases, and development dependencies remain excluded by the project's .gitignore.
