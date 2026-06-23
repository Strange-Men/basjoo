# RAG Evaluation Harness

## Purpose

This document describes the RAG (Retrieval-Augmented Generation) evaluation framework for the Basjoo customer support platform. The harness provides:

- **Automated test suite** for retrieval precision, no-answer fallback, citation accuracy, and hallucination risk
- **Standalone eval runner** that generates JSON + Markdown reports
- **Demo fixtures** with pre-defined eval cases and a mock knowledge base
- **Demo data seeder** for populating the knowledge base with realistic scenarios

**Important**: This is a **mock-friendly reproducible evaluation framework**, not a production RAG quality assessment. Real Qdrant/Embedding/LLM integration is a future v2 extension.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Eval Harness                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Eval Cases   │    │ Mock Retriever│    │ Mock Pipeline│  │
│  │  (15 cases)   │───▶│ (in-memory)  │───▶│ (extractive) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Metrics      │    │  Knowledge   │    │   Reports    │  │
│  │  Computation  │    │  Base (JSON) │    │  JSON + MD   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Location | Purpose |
|---|---|---|
| Eval Cases | `tests/rag_eval/fixtures/rag_eval_cases.json` | 15 test scenarios |
| Knowledge Base | `tests/rag_eval/fixtures/demo_knowledge_base.json` | Mock KB (3 docs, 11 chunks) |
| Mock Embedding | `tests/rag_eval/conftest.py` | Character-frequency vectors (32-dim) |
| Mock Retriever | `tests/rag_eval/conftest.py` | In-memory cosine similarity |
| Mock Pipeline | `scripts/run_rag_eval.py` | Extractive answer generation |
| Eval Runner | `scripts/run_rag_eval.py` | Orchestrates evaluation |
| Demo Data | `scripts/demo_data/` | Richer dataset for seeding |
| Seeder | `scripts/seed_demo_data.py` | Validates and seeds demo data |

## Mock RAG Pipeline

### How It Works

1. **Query Embedding**: Converts query to 32-dim character-frequency vector
2. **Retrieval**: Computes cosine similarity against knowledge base chunks
3. **Answer Generation**: Extracts relevant sentences from top-k chunks
4. **Citation**: Maps answer content to source documents

### Why Mock?

- **No API keys required** — safe for CI/CD and local development
- **Deterministic** — same inputs always produce same outputs
- **Lightweight** — no heavy dependencies (no RAGAS, no DeepEval, no LangChain)
- **Non-invasive** — does not modify any existing Basjoo code

### Mock vs Real

| Component | Mock | Real (Future) |
|---|---|---|
| Embedding | Character-frequency (32-dim) | Jina API / OpenAI |
| Retriever | In-memory cosine | Qdrant vector search |
| Pipeline | Extractive (copy from chunks) | LLM-generated |
| Knowledge Base | JSON fixture | PostgreSQL + Qdrant |

## Eval Case Format

Each eval case in `rag_eval_cases.json` has:

```json
{
  "id": "TC001",
  "query": "How do I return a product?",
  "expected_docs": ["return_policy"],
  "scenario": "normal_hit",
  "expected_answer_contains": ["return", "30 days"],
  "expected_no_answer": false,
  "expected_citations": ["return_policy.md"]
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique test case ID |
| `query` | string | User query to evaluate |
| `expected_docs` | list | Document IDs that should be retrieved |
| `scenario` | string | Test scenario type |
| `expected_answer_contains` | list | Keywords expected in answer |
| `expected_no_answer` | bool | Whether system should refuse to answer |
| `expected_citations` | list | Source documents expected in citations |

### Scenario Types

| Scenario | Count | Description |
|---|---|---|
| `normal_hit` | 5 | Query matches KB, should return correct answer + sources |
| `multi_doc_retrieval` | 2 | Query requires info from multiple documents |
| `no_answer_fallback` | 2 | Query is unrelated to KB, should refuse to answer |
| `low_relevance_reject` | 2 | Query is tangentially related, should not fabricate |
| `evidence_citation` | 2 | Verify source attribution is correct |
| `hallucination_risk` | 2 | Verify no fabricated facts in answer |

## Metrics Explanation

### Retrieval Metrics

| Metric | Formula | Description |
|---|---|---|
| **Precision@k** | relevant_in_top_k / k | Fraction of top-k results that are relevant |
| **Recall@k** | relevant_in_top_k / total_relevant | Fraction of relevant docs found in top-k |
| **MRR** | 1 / rank_of_first_relevant | Mean Reciprocal Rank of first relevant result |

### Quality Metrics

| Metric | Description |
|---|---|
| **No-Answer Accuracy** | Correct refusal rate for irrelevant queries |
| **Citation Accuracy** | Rate of correct source attribution |
| **Hallucination Risk** | Number of answers containing fabricated facts |

## Running Tests

### Prerequisites

```powershell
cd backend
# Ensure virtual environment is activated
.\venv\Scripts\activate
```

### Run All RAG Eval Tests

```powershell
.\venv\Scripts\python.exe -m pytest tests\rag_eval -v
```

### Run Specific Test File

```powershell
.\venv\Scripts\python.exe -m pytest tests\rag_eval\test_retrieval_precision.py -v
```

### Run Specific Test

```powershell
.\venv\Scripts\python.exe -m pytest tests\rag_eval\test_no_answer_fallback.py::TestNoAnswerFallback::test_unrelated_query_returns_no_answer -v
```

## Running Eval Runner

### Basic Usage

```powershell
cd backend

# Mock mode (default, no API key needed)
.\venv\Scripts\python.exe scripts\run_rag_eval.py --mock

# Custom top-k
.\venv\Scripts\python.exe scripts\run_rag_eval.py --mock --top-k 3
```

### Output

The runner generates:
- `reports/rag_eval_report.json` — machine-readable results
- `reports/rag_eval_report.md` — human-readable report

### What It Does

1. Loads eval cases from `tests/rag_eval/fixtures/rag_eval_cases.json`
2. Runs each case through the mock RAG pipeline
3. Computes precision, recall, MRR, no-answer accuracy, citation accuracy
4. Generates reports in `reports/`

## Running Demo Seeder

### Basic Usage

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

### Demo Data Files

| File | Description |
|---|---|
| `agents.json` | 2 demo agents with system prompts |
| `demo_questions.json` | 15 questions with categories |
| `conversations.json` | 3 multi-turn scenarios |
| `expected_evidence.json` | Source attribution mapping |
| `bad_cases.json` | 8 adversarial test cases |
| `knowledge/product_faq.md` | Product FAQ |
| `knowledge/return_policy.md` | Return policy |
| `knowledge/troubleshooting.md` | Troubleshooting guide |

## Report Output

### JSON Report

```json
{
  "generated_at": "2026-06-20T05:56:26.428136+00:00",
  "test_mode": "mock",
  "summary": {
    "total_cases": 15,
    "passed": 15,
    "failed": 0
  },
  "metrics": {
    "precision_at_3": 0.567,
    "recall_at_3": 0.978,
    "precision_at_5": 0.527,
    "recall_at_5": 1.000,
    "mrr": 0.600,
    "no_answer_accuracy": 1.0,
    "citation_accuracy": 0.889,
    "hallucination_risk_cases": 0
  }
}
```

### Markdown Report

The Markdown report includes:
- Executive summary
- Retrieval metrics table
- Quality metrics table
- Per-case results
- Notes and limitations

## Known Limitations

1. **Mock embedding is character-based, not semantic** — cosine similarity is approximate
2. **Mock pipeline does not use a real LLM** — answer is extracted from chunks, not generated
3. **Eval cases are manually curated** — not auto-generated
4. **No multi-turn conversation evaluation** — single-turn only
5. **No latency/performance metrics** — quality-focused
6. **Real mode evaluates retrieval only** — no LLM chat eval

## Real Qdrant Retrieval Evaluation (v2.0)

### Prerequisites

1. Start Qdrant: `docker compose up -d qdrant`
2. Set environment variables in `basjoo/.env`:
   - `SILICONFLOW_API_KEY` — for embeddings
   - `QDRANT_URL` — Qdrant endpoint (default: `http://localhost:6333`)
   - `SILICONFLOW_BASE_URL` — API base (default: `https://api.siliconflow.cn/v1`)
   - `SILICONFLOW_EMBEDDING_MODEL` — model name (default: `Qwen/Qwen3-Embedding-0.6B`)

### Step 1: Seed Knowledge Base to Qdrant

```powershell
cd backend

# Write demo knowledge base to Qdrant (creates collection customerops_demo_real_eval)
.\venv\Scripts\python.exe scripts\seed_demo_data.py --write-db

# Or with alias
.\venv\Scripts\python.exe scripts\seed_demo_data.py --write-qdrant

# Reset collection (delete + recreate)
.\venv\Scripts\python.exe scripts\seed_demo_data.py --write-db --reset
```

### Step 2: Run Real Retrieval Evaluation

```powershell
cd backend

# Real mode: 5 eval cases against Qdrant + SiliconFlow
.\venv\Scripts\python.exe scripts\run_rag_eval.py --real

# Custom collection name
.\venv\Scripts\python.exe scripts\run_rag_eval.py --real --collection-name my_collection

# Custom top-k
.\venv\Scripts\python.exe scripts\run_rag_eval.py --real --top-k 3
```

### Step 3: Review Reports

```powershell
# Real eval report
dir reports\rag_eval_real_report.json
dir reports\rag_eval_real_report.md

# Mock vs Real comparison
dir reports\rag_eval_mock_vs_real.md
```

### Real Eval Cases (5 selected)

| ID | Language | Scenario | Expected Sources |
|---|---|---|---|
| TC001 | EN | normal_hit | return_policy.md |
| TC002 | ZH | normal_hit | product_faq.md |
| TC006 | EN | no_answer_fallback | (none) |
| TC010 | EN | evidence_citation | return_policy.md |
| TC014 | ZH | normal_hit | troubleshooting.md |

### Real Mode Metrics

| Metric | Description |
|---|---|
| Precision@3 | Fraction of top-3 results that match expected docs |
| Recall@3 | Fraction of expected docs found in top-3 |
| MRR | Mean Reciprocal Rank of first relevant result |
| Hit Rate | Whether any expected doc appears in top-k |
| No-Answer Accuracy | Correct rejection rate for irrelevant queries |

### What Stays the Same

- Test structure (15 eval cases for mock, 5 for real)
- Metrics computation (precision, recall, MRR, etc.)
- Report generation (JSON + Markdown)
- Demo data format
- All mock mode functionality

### What Changed in v2.0

- `seed_demo_data.py --write-db` now writes to Qdrant (was a stub)
- `run_rag_eval.py --real` runs real retrieval eval (new)
- Uses SiliconFlow Qwen3-Embedding-0.6B (1024 dim)
- Uses Qdrant REST API (urllib, avoids qdrant_client version issues)
- Generates mock vs real comparison report

---

*Version: v2.0-real-qdrant-eval-adapter*
*Last updated: 2026-06-23*
