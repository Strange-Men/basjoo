# Enhancement Summary

> 中文说明见：[ENHANCEMENT_SUMMARY.zh-CN.md](./ENHANCEMENT_SUMMARY.zh-CN.md)

## Overview

This document describes the enhancements made to the Basjoo AI customer support platform through secondary development. The work focuses on **RAG quality evaluation**, **demo data provisioning**, and **engineering verifiability** — all achievable without real API keys or external services.

**Branch**: `phase1-rag-eval-harness`
**Current Version**: v1.2-docs-and-report

## What Was Added

### 1. RAG Evaluation Harness (v1.0)

A lightweight, mock-friendly evaluation framework for testing RAG retrieval quality.

**Key features**:
- 15 curated eval cases covering 6 scenario types
- Mock retriever using character-frequency embeddings (no API key)
- Mock RAG pipeline (no LLM calls)
- Automated metrics: Precision@k, Recall@k, MRR, No-Answer Accuracy, Citation Accuracy
- Hallucination risk detection
- JSON + Markdown report generation

### 2. SmartHome Demo Data (v1.1)

A reusable demo dataset for the SmartHome Support scenario.

**Key features**:
- 2 demo agents with system prompts and escalation policies
- 3 knowledge base documents (product FAQ, return policy, troubleshooting)
- 15 demo questions with categories and risk types
- 3 multi-turn conversation scenarios
- 8 adversarial bad cases (hallucination traps, policy fabrication)

### 3. Documentation and Reports (v1.2)

Polished documentation and formal evaluation reports.

**Key features**:
- Enhanced evaluation report with executive summary
- Portfolio summary for interview preparation
- This enhancement summary

## File Map

```
backend/
├── tests/
│   └── rag_eval/
│       ├── conftest.py                    # Shared fixtures
│       ├── fixtures/
│       │   ├── demo_knowledge_base.json   # v1.0 KB fixture
│       │   ├── demo_knowledge_base_full.json  # v1.1 expanded KB
│       │   └── rag_eval_cases.json        # 15 eval cases
│       ├── test_retrieval_precision.py    # Precision/recall tests
│       ├── test_no_answer_fallback.py     # No-answer handling tests
│       ├── test_evidence_citation.py      # Citation accuracy tests
│       ├── test_hallucination_risk.py     # Hallucination detection tests
│       └── test_demo_data_integrity.py    # Demo data validation tests
├── scripts/
│   ├── run_rag_eval.py                    # Standalone eval runner
│   ├── seed_demo_data.py                  # Demo data seeder
│   └── demo_data/
│       ├── agents.json                    # Demo agent configs
│       ├── demo_questions.json            # 15 demo questions
│       ├── conversations.json             # 3 conversation scenarios
│       ├── expected_evidence.json         # Source attribution mapping
│       ├── bad_cases.json                 # 8 adversarial cases
│       └── knowledge/
│           ├── product_faq.md             # Product FAQ
│           ├── return_policy.md           # Return policy
│           └── troubleshooting.md         # Troubleshooting guide
├── reports/
│   ├── rag_eval_report.json              # Machine-readable report
│   ├── rag_eval_report.md                # Human-readable report
│   └── README.md                         # Report documentation
└── docs/
    ├── rag-evaluation.md                  # Usage documentation
    └── portfolio-summary.md              # Portfolio/interview guide

ENHANCEMENT_SUMMARY.md                     # This file
```

## How to Run RAG Eval

### Run pytest

```powershell
cd backend

# Run all RAG eval tests
.\venv\Scripts\python.exe -m pytest tests\rag_eval -v

# Run specific test file
.\venv\Scripts\python.exe -m pytest tests\rag_eval\test_retrieval_precision.py -v

# Run specific test
.\venv\Scripts\python.exe -m pytest tests\rag_eval\test_no_answer_fallback.py::TestNoAnswerFallback::test_unrelated_query_returns_no_answer -v
```

### Run Eval Runner

```powershell
cd backend

# Mock mode (default, no API key needed)
.\venv\Scripts\python.exe scripts\run_rag_eval.py --mock

# Custom top-k
.\venv\Scripts\python.exe scripts\run_rag_eval.py --mock --top-k 3
```

Output files:
- `reports/rag_eval_report.json` — machine-readable
- `reports/rag_eval_report.md` — human-readable

## How to Run Demo Data Seeder

```powershell
cd backend

# Validate JSON schema only (no side effects)
.\venv\Scripts\python.exe scripts\seed_demo_data.py --validate-only

# Print summary of what would be seeded
.\venv\Scripts\python.exe scripts\seed_demo_data.py --dry-run

# Generate mock fixtures for tests
.\venv\Scripts\python.exe scripts\seed_demo_data.py --mock
```

### Mode Differences

| Mode | Reads | Writes | Use Case |
|---|---|---|---|
| `--validate-only` | demo_data/*.json | Nothing | CI validation, pre-commit check |
| `--dry-run` | demo_data/*.json | Nothing | Preview before seeding |
| `--mock` | demo_data/*.json, knowledge/*.md | `fixtures/demo_knowledge_base_full.json` | Generate expanded KB fixture |

## Test Results

### RAG Eval Tests

```
tests/rag_eval/: 37 passed
```

### Eval Runner (Mock Mode)

```
Total cases: 15
Passed: 15 (100%)
Failed: 0 (0%)

Retrieval Metrics:
- Precision@3: 0.567
- Recall@3: 0.978
- Precision@5: 0.527
- Recall@5: 1.000
- MRR: 0.600

Quality Metrics:
- No-Answer Accuracy: 100.0%
- Citation Accuracy: 88.9%
- Hallucination Risk Cases: 0
```

### Demo Data Seeder

```
--validate-only: PASS
--dry-run: PASS
--mock: PASS
```

### Baseline Comparison

| Metric | Before | After | Change |
|---|---|---|---|
| Existing tests | 267 passed, 36 failed, 1 skipped | 267 passed, 36 failed, 1 skipped | No change |
| New RAG eval tests | — | 37 passed | +37 |
| New regression | — | 0 | None |

## No-API-Key / No-Qdrant Strategy

### Why Mock Mode?

The evaluation harness is designed to:
1. **Validate the evaluation framework itself** — not real RAG quality
2. **Run without secrets** — safe for CI/CD and local development
3. **Be deterministic** — same inputs produce same outputs
4. **Be lightweight** — no heavy dependencies (no RAGAS, no DeepEval, no LangChain)

### How Mock Mode Works

| Component | Mock Implementation | Real Equivalent |
|---|---|---|
| Embedding | Character-frequency vectors (32-dim) | Jina API / OpenAI Embeddings |
| Retriever | In-memory cosine similarity | Qdrant vector search |
| Pipeline | Extractive (copy from chunks) | LLM-generated answer |
| Knowledge Base | JSON fixture | PostgreSQL + Qdrant |

### What This Proves

- The test structure is correct and runnable
- The metrics computation logic works
- The eval cases cover the intended scenarios
- The report generation produces valid output
- No regression to existing tests

## Limitations

1. **Mock embedding is character-based, not semantic** — cosine similarity is approximate
2. **Mock pipeline does not use a real LLM** — answer is extracted from chunks, not generated
3. **Eval cases are manually curated** — not auto-generated
4. **No multi-turn conversation evaluation** — single-turn only
5. **No latency/performance metrics** — quality-focused
6. **`--write-db` not implemented** — mock mode only

## Next Steps

### v1.3 — Phase 1 Complete

- Final documentation review
- Tag v1.3-phase1-complete
- Prepare for Phase 2

### Phase 2 — Real RAG Integration (Future)

1. Start Qdrant: `docker compose up -d qdrant`
2. Set environment variables: `JINA_API_KEY`, `QDRANT_URL`
3. Ingest demo knowledge base into Qdrant
4. Replace `MockRetriever` with real `KbRetrievalService`
5. Replace mock pipeline with real chat endpoint

The test structure remains the same — only the retrieval and generation backends change.

---

*Version: v1.2-docs-and-report*
*Last updated: 2026-06-20*
