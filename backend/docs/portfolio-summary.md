# Portfolio Summary

## Project Background

**CustomerOpsAgent_2** is a secondary development project on the open-source AI customer support platform [Basjoo](https://github.com/haoyiyin/basjoo). The goal is to enhance RAG quality evaluation capabilities and create reproducible engineering artifacts.

### Why Basjoo?

- **MIT License** — permissive for secondary development
- **Modern stack** — Python/FastAPI + Next.js 14 + PostgreSQL + Qdrant
- **Active maintenance** — recent commits, responsive maintainer
- **Good architecture** — clean separation of concerns, testable code
- **RAG-ready** — built-in vector search with Qdrant

## What I Did

### Phase 1: RAG Evaluation Harness (v1.0)

**Problem**: No way to evaluate RAG retrieval quality without real API keys and Qdrant.

**Solution**: Built a mock-friendly evaluation framework that:
- Uses character-frequency embeddings (no API key)
- Uses in-memory cosine similarity (no Qdrant)
- Uses extractive answer generation (no LLM)
- Produces deterministic, reproducible results

**Result**: 37 pytest tests passed, 15 eval cases all pass.

### Phase 2: Demo Data (v1.1)

**Problem**: No realistic test data for the SmartHome Support scenario.

**Solution**: Created a comprehensive demo dataset:
- 2 demo agents with system prompts
- 3 knowledge base documents
- 15 demo questions with categories
- 3 conversation scenarios
- 8 adversarial bad cases

**Result**: seed_demo_data.py supports 3 modes (validate-only, dry-run, mock).

### Phase 3: Documentation and Reports (v1.2)

**Problem**: Documentation was incomplete, reports were basic.

**Solution**: Polished all documentation:
- Enhanced evaluation report with executive summary
- Created portfolio summary (this file)
- Added enhancement summary
- Improved usage documentation

**Result**: Professional-grade documentation suitable for portfolio display.

## Technical Highlights

### 1. Mock RAG Pipeline

**Challenge**: How to test RAG quality without real APIs?

**Solution**: Designed a deterministic mock pipeline:
- **Mock Embedding**: Character-frequency vectors (32-dim) — same input always produces same vector
- **Mock Retriever**: In-memory cosine similarity — no external dependencies
- **Mock Pipeline**: Extractive answers — copies relevant sentences from chunks

**Learning**: Demonstrates understanding of embedding spaces, similarity search, and RAG architecture.

### 2. Evaluation Metrics

**Challenge**: How to measure RAG quality?

**Solution**: Implemented standard IR metrics:
- **Precision@k**: Fraction of top-k results that are relevant
- **Recall@k**: Fraction of relevant docs found in top-k
- **MRR**: Mean Reciprocal Rank of first relevant result
- **No-Answer Accuracy**: Correct refusal rate for irrelevant queries
- **Citation Accuracy**: Rate of correct source attribution
- **Hallucination Risk**: Number of fabricated facts

**Learning**: Shows understanding of information retrieval evaluation methodology.

### 3. Reproducible Testing

**Challenge**: How to ensure tests are deterministic and CI-friendly?

**Solution**: 
- No API keys required
- No external services (no Docker, no Qdrant)
- Deterministic mock components
- JSON fixtures for test data

**Learning**: Demonstrates engineering discipline and CI/CD awareness.

### 4. Demo Data Design

**Challenge**: How to create realistic test data?

**Solution**:
- Modeled real customer support scenarios
- Included edge cases (no-answer, low-relevance)
- Added adversarial cases (hallucination traps)
- Structured for both testing and portfolio display

**Learning**: Shows understanding of test design and data modeling.

## Test Results

### RAG Eval Tests

```
tests/rag_eval/: 37 passed
```

### Eval Runner

```
Total cases: 15
Passed: 15 (100%)
Failed: 0 (0%)

Precision@3: 0.567
Recall@3: 0.978
Precision@5: 0.527
Recall@5: 1.000
MRR: 0.600

No-Answer Accuracy: 100.0%
Citation Accuracy: 88.9%
Hallucination Risk Cases: 0
```

### Baseline Safety

```
Existing tests: 267 passed, 36 failed, 1 skipped (no change)
New regression: 0
```

## Interview Talking Points

### "Tell me about this project"

"I enhanced an open-source AI customer support platform called Basjoo. My focus was on RAG quality evaluation — building a framework to test retrieval precision, no-answer handling, citation accuracy, and hallucination risk. The key challenge was making it work without real API keys, so I built a mock pipeline using character-frequency embeddings and in-memory similarity search. This made the tests deterministic and CI-friendly."

### "What was the hardest part?"

"Designing the mock embedding system. I needed something that would produce consistent similarity scores without calling a real embedding API. I settled on character-frequency vectors — they're not semantic, but they're deterministic and fast. The trade-off is that the metrics don't reflect real RAG quality, but they do validate the evaluation framework itself."

### "What would you do differently?"

"For production, I'd integrate real embeddings (Jina or OpenAI) and a real vector store (Qdrant). The mock pipeline is great for development and testing, but real RAG quality depends on semantic understanding. I'd also add latency metrics and multi-turn conversation evaluation."

### "What did you learn?"

"Three things: First, the importance of reproducible testing — mock components let me iterate fast without paying for API calls. Second, RAG evaluation is nuanced — precision/recall are just the basics; you also need to check for hallucinations and citation accuracy. Third, documentation matters — a well-documented project is easier to maintain and showcase."

## Resume Bullets

### Chinese

基于开源 AI 客服系统 Basjoo 进行二次开发，构建 RAG Evaluation Harness 与 SmartHome Demo Data，支持检索精度、无答案回退、证据引用与幻觉风险等评估场景，在无真实 API Key / 无 Qdrant 环境下通过 Mock pipeline 完成可复现评估，并生成 JSON / Markdown 评估报告。

### English

Enhanced an open-source AI customer support platform by adding a mock-friendly RAG evaluation harness, demo dataset, no-answer fallback checks, citation validation, hallucination risk tests, and reproducible JSON/Markdown evaluation reports.

### Detailed (for portfolio)

- Designed and implemented a RAG evaluation framework with 15 test cases covering 6 scenario types
- Built mock embedding system using character-frequency vectors for deterministic, API-key-free testing
- Implemented standard IR metrics: Precision@k, Recall@k, MRR, No-Answer Accuracy, Citation Accuracy
- Created SmartHome demo dataset with 2 agents, 3 knowledge docs, 15 questions, 3 conversations, 8 bad cases
- Achieved 37 pytest tests passed, 15/15 eval cases passed, no regression to existing tests
- Generated JSON + Markdown evaluation reports with executive summary and metrics analysis

## Project Links

| Resource | URL |
|---|---|
| Management Repository | https://github.com/Strange-Men/CustomerOpsAgent_2 |
| Code Repository | https://github.com/Strange-Men/basjoo/tree/phase1-rag-eval-harness |
| Enhancement Summary | [ENHANCEMENT_SUMMARY.md](../../ENHANCEMENT_SUMMARY.md) |
| RAG Evaluation Docs | [rag-evaluation.md](rag-evaluation.md) |
| Evaluation Report | [../reports/rag_eval_report.md](../reports/rag_eval_report.md) |

---

*Version: v1.2-docs-and-report*
*Last updated: 2026-06-20*
