# RAG Evaluation Harness

## What is this?

This is a lightweight RAG (Retrieval-Augmented Generation) evaluation framework for the Basjoo customer support platform. It provides:

- **Automated test suite** (`tests/rag_eval/`) — pytest-based tests for retrieval precision, no-answer fallback, citation accuracy, and hallucination risk
- **Standalone runner** (`scripts/run_rag_eval.py`) — runs all eval cases and generates JSON + Markdown reports
- **Demo fixtures** (`tests/rag_eval/fixtures/`) — pre-defined eval cases and a mock knowledge base

## Design Principles

- **No API keys required** — all tests run in mock mode by default
- **No external services** — no Qdrant, no Docker, no embedding API
- **Deterministic** — mock embedding uses character-frequency vectors (not random)
- **Lightweight** — no heavy dependencies (no RAGAS, no DeepEval, no LangChain)
- **Non-invasive** — does not modify any existing Basjoo core code or tests

## How to Run pytest

```bash
cd backend
# Run only the RAG eval harness
python -m pytest tests/rag_eval/ -v

# Run a specific test file
python -m pytest tests/rag_eval/test_retrieval_precision.py -v

# Run a specific test
python -m pytest tests/rag_eval/test_no_answer_fallback.py::TestNoAnswerFallback::test_unrelated_query_returns_no_answer -v
```

## How to Run the Eval Runner

```bash
cd backend

# Mock mode (default, no API key needed)
python scripts/run_rag_eval.py --mock

# Custom top-k
python scripts/run_rag_eval.py --mock --top-k 3
```

The runner will:
1. Load eval cases from `tests/rag_eval/fixtures/rag_eval_cases.json`
2. Run each case through the mock RAG pipeline
3. Compute precision, recall, MRR, no-answer accuracy, citation accuracy
4. Generate reports in `reports/`:
   - `rag_eval_report.json` (machine-readable)
   - `rag_eval_report.md` (human-readable)

## Why No API Key?

The harness is designed to validate the **evaluation framework itself**, not the real RAG quality. It uses:

- **Mock embedding**: Character-frequency vectors (32-dim) that produce deterministic similarity scores
- **Mock retriever**: In-memory cosine similarity search over the demo knowledge base
- **Mock pipeline**: Synthesises answers from retrieved chunks without calling any LLM

This lets you:
- Run CI/CD tests without secrets
- Validate test logic without paying for API calls
- Develop and iterate on eval cases locally

## Eval Cases

The `rag_eval_cases.json` file contains 15 test cases covering:

| Scenario | Count | Description |
|---|---|---|
| `normal_hit` | 5 | Query matches KB, should return correct answer + sources |
| `multi_doc_retrieval` | 2 | Query requires info from multiple documents |
| `no_answer_fallback` | 2 | Query is unrelated to KB, should refuse to answer |
| `low_relevance_reject` | 2 | Query is tangentially related, should not fabricate |
| `evidence_citation` | 2 | Verify source attribution is correct |
| `hallucination_risk` | 2 | Verify no fabricated facts in answer |

## Metrics

| Metric | Description |
|---|---|
| **Precision@k** | Fraction of top-k results that are relevant |
| **Recall@k** | Fraction of relevant docs found in top-k |
| **MRR** | Mean Reciprocal Rank of first relevant result |
| **No-Answer Accuracy** | Correct refusal rate for irrelevant queries |
| **Citation Accuracy** | Rate of correct source attribution |
| **Hallucination Risk** | Number of answers containing fabricated facts |

## Demo Data (v1.1)

### What is it?

A reusable demo dataset for the SmartHome Support scenario, located in `scripts/demo_data/`. It provides:

- **Demo agents** (`agents.json`) — 2 pre-configured support agents with system prompts, allowed topics, and escalation policies
- **Knowledge base** (`knowledge/`) — 3 markdown documents covering product FAQ, return policy, and troubleshooting
- **Demo questions** (`demo_questions.json`) — 15 questions covering product info, warranty, returns, troubleshooting, shipping, and edge cases
- **Conversations** (`conversations.json`) — 3 multi-turn conversation scenarios (normal, escalation, no-answer)
- **Expected evidence** (`expected_evidence.json`) — source attribution mapping for each question
- **Bad cases** (`bad_cases.json`) — 8 adversarial test cases (hallucination traps, policy fabrication, cross-doc confusion)

### How to Use seed_demo_data.py

```bash
cd backend

# Validate JSON schema only (default, no side effects)
python scripts/seed_demo_data.py --validate-only

# Print summary of what would be seeded
python scripts/seed_demo_data.py --dry-run

# Generate mock fixtures for tests/rag_eval/
python scripts/seed_demo_data.py --mock
```

### Mode Differences

| Mode | Reads | Writes | Use Case |
|---|---|---|---|
| `--validate-only` | demo_data/*.json | Nothing | CI validation, pre-commit check |
| `--dry-run` | demo_data/*.json | Nothing | Preview before seeding |
| `--mock` | demo_data/*.json, knowledge/*.md | `fixtures/demo_knowledge_base_full.json` | Generate expanded KB fixture |

**Note**: `--mock` preserves the original v1.0 fixtures (`demo_knowledge_base.json`, `rag_eval_cases.json`) to maintain backward compatibility with existing tests.

### Relationship Between Demo Data and Fixtures

| File | Purpose | Source |
|---|---|---|
| `fixtures/demo_knowledge_base.json` | v1.0 test fixture (3 docs, 11 chunks) | Hand-curated, paragraph-level chunks |
| `fixtures/demo_knowledge_base_full.json` | v1.1 expanded fixture (3 docs, 45 chunks) | Generated from `knowledge/*.md` via `--mock` |
| `fixtures/rag_eval_cases.json` | v1.0 eval cases (15 cases) | Hand-curated test scenarios |
| `demo_data/demo_questions.json` | v1.1 demo questions (15 questions) | Richer dataset with categories, risk types |

The v1.0 fixtures are used by `tests/rag_eval/` and `run_rag_eval.py`. The v1.1 demo data is a richer, more structured dataset suitable for seeding a real system or portfolio display.

### Why No Database Write?

`--write-db` is not implemented in v1.1 because:
- No production database is available in the mock environment
- The demo data is designed for evaluation and demonstration, not production use
- Writing to a real DB requires proper ORM integration and environment validation

To implement `--write-db` in the future:
1. Add ORM model imports for Agent, KnowledgeBase, Document, etc.
2. Implement environment detection (reject production)
3. Add transaction management and rollback support
4. Integrate with Qdrant for vector storage

## Future Extension: Real Mode

To evaluate real RAG quality (requires API keys + Qdrant):

1. Start Qdrant: `docker compose up -d qdrant`
2. Set environment variables: `JINA_API_KEY`, `QDRANT_URL`
3. Ingest demo knowledge base into Qdrant (use `seed_demo_data.py --write-db`)
4. Replace `MockRetriever` with real `KbRetrievalService`
5. Replace mock pipeline with real chat endpoint

The test structure remains the same — only the retrieval and generation backends change.

## Current Limitations

- Mock embedding is character-based, not semantic (cosine similarity is approximate)
- Mock pipeline does not use a real LLM (answer is extracted from chunks, not generated)
- Eval cases are manually curated (not auto-generated)
- No multi-turn conversation evaluation
- No latency/performance metrics
- `--write-db` not implemented (v1.1)
