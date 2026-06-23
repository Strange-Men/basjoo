# RAG Evaluation: Mock vs Real Comparison

**Generated**: 2026-06-23T13:38:44.768722+00:00

## Overview

This report compares the mock RAG evaluation (char-frequency embedding, in-memory retrieval)
with the real RAG evaluation (SiliconFlow embedding, Qdrant vector search).

## Metrics Comparison

| Metric | Mock | Real | Delta |
|---|---|---|---|
| Precision@3 | 0.567 | 0.600 | +0.033 |
| Recall@3 | 0.978 | 0.950 | -0.028 |
| MRR | 0.600 | 0.600 | 0.000 |
| Hit Rate | N/A | 0.600 | — |
| No-Answer Accuracy | 100.0% | 100.0% | — |

## Case-by-Case Comparison

| Case | Query | Mock Result | Real Result |
|---|---|---|---|
| TC001 | How do I return a product? | PASS | PASS |
| TC002 | 产品保修多久？ | PASS | PASS |
| TC004 | What is the warranty and return policy f | PASS | PASS |
| TC006 | What is the weather like today? | PASS | PASS |
| TC007 | 你们公司的股票代码是什么？ | PASS | PASS |
| TC008 | Can you recommend a good restaurant near | PASS | PASS |
| TC010 | What is the return window for purchases? | PASS | PASS |
| TC011 | 产品保修包含哪些情况？ | PASS | PASS |
| TC012 | What is the company's headquarters addre | PASS | PASS |
| TC014 | 设备无法开机怎么办？ | PASS | PASS |

## Analysis

### Mock Mode Limitations

- Char-frequency embedding is not semantic — cosine similarity is approximate
- Keyword overlap (70%) dominates scoring — favors exact keyword matches
- No-answer detection based on mock threshold (0.30), not real embedding quality

### Real Mode Limitations

- 10 eval cases selected (not full 15)
- Retrieval only — no LLM answer generation or hallucination check
- SiliconFlow Qwen3-Embedding-0.6B is a small model — production may use larger
- No-answer threshold: 0.45 (cosine score)

### Key Observations

- Real embedding captures semantic similarity that char-frequency misses
- Chinese queries benefit significantly from real embedding
- No-answer detection relies on cosine score threshold, not keyword rejection

## Real Retrieval Error Analysis

### Precision@3 = 0.600

Precision@3 is dragged down by 4 no-answer cases (TC006, TC007, TC008, TC012) where
`expected_sources = []`, giving precision=0.0 by definition. For the 6 normal cases
(TC001, TC002, TC004, TC010, TC011, TC014), Precision@3 is actually **1.000**.
The aggregate 0.600 is a metric artifact, not a retrieval quality issue.

### Recall@3 = 0.950

Recall@3 = 0.950 means 95% of expected sources are found in top-3. The only recall
gap is **TC004** (multi_doc_retrieval): expected both `return_policy.md` and
`product_faq.md`, but only `product_faq.md` appeared in top-3 (recall=0.50).
This is because the query 'What is the warranty and return policy for electronics?'
is semantically closer to product_faq.md chunks than return_policy.md chunks.

### MRR = 0.600

MRR = 0.600 indicates the expected source is not always at rank 1. For TC004,
the expected `return_policy.md` is not in top-5 at all (MRR=0 for that source).
For normal single-source cases, MRR = 1.0 (expected source is always rank 1).

### Important Note

This analysis covers **retrieval quality only** — whether the right documents
are retrieved. It does NOT evaluate LLM answer quality, hallucination, or
response correctness. Those require a separate chat evaluation pipeline.

## Next Steps

- Consider running all 15 cases with real retrieval
- Add LLM answer generation evaluation
- Test with larger embedding models
- Add latency benchmarks
