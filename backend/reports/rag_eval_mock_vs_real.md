# RAG Evaluation: Mock vs Real Comparison

**Generated**: 2026-06-23T09:51:46.544702+00:00

## Overview

This report compares the mock RAG evaluation (char-frequency embedding, in-memory retrieval)
with the real RAG evaluation (SiliconFlow embedding, Qdrant vector search).

## Metrics Comparison

| Metric | Mock | Real | Delta |
|---|---|---|---|
| Precision@3 | 0.567 | 0.800 | +0.233 |
| Recall@3 | 0.978 | 1.000 | +0.022 |
| MRR | 0.600 | 0.800 | +0.200 |
| Hit Rate | N/A | 0.800 | — |
| No-Answer Accuracy | 100.0% | 100.0% | — |

## Case-by-Case Comparison

| Case | Query | Mock Result | Real Result |
|---|---|---|---|
| TC001 | How do I return a product? | PASS | PASS |
| TC002 | 产品保修多久？ | PASS | PASS |
| TC006 | What is the weather like today? | PASS | PASS |
| TC010 | What is the return window for purchases? | PASS | PASS |
| TC014 | 设备无法开机怎么办？ | PASS | PASS |

## Analysis

### Mock Mode Limitations

- Char-frequency embedding is not semantic — cosine similarity is approximate
- Keyword overlap (70%) dominates scoring — favors exact keyword matches
- No-answer detection based on mock threshold (0.30), not real embedding quality

### Real Mode Limitations

- Only 5 eval cases selected (not full 15)
- Retrieval only — no LLM answer generation or hallucination check
- SiliconFlow Qwen3-Embedding-0.6B is a small model — production may use larger
- No-answer threshold: 0.45 (cosine score)

### Key Observations

- Real embedding captures semantic similarity that char-frequency misses
- Chinese queries benefit significantly from real embedding
- No-answer detection relies on cosine score threshold, not keyword rejection

## Next Steps

- Run full 15 cases with real retrieval
- Add LLM answer generation evaluation
- Test with larger embedding models
- Add latency benchmarks
