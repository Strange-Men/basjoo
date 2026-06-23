# RAG Evaluation Report — Real Retrieval

**Generated**: 2026-06-23T09:17:21.196002+00:00
**Test Mode**: real (SiliconFlow + Qdrant)
**Collection**: customerops_demo_real_eval
**Embedding Model**: Qwen/Qwen3-Embedding-0.6B

## Summary

| Metric | Value |
|---|---|
| Total Cases | 5 |
| Passed | 5 (100%) |
| Failed | 0 |

## Retrieval Metrics

| Metric | Value |
|---|---|
| Precision@3 | 0.733 |
| Recall@3 | 1.000 |
| MRR | 0.800 |
| Hit Rate | 0.800 |
| No-Answer Accuracy | 100.0% |

## Per-Case Results

- TC001: ✅ score=0.6862 p3=1.00 r3=1.00 | How do I return a product?
- TC002: ✅ score=0.6650 p3=0.67 r3=1.00 | 产品保修多久？
- TC006: ✅ score=0.2764 p3=0.00 r3=1.00 | What is the weather like today?
- TC010: ✅ score=0.6325 p3=1.00 r3=1.00 | What is the return window for purchases?
- TC014: ✅ score=0.9033 p3=1.00 r3=1.00 | 设备无法开机怎么办？

## Notes

- Real retrieval using SiliconFlow embedding + Qdrant vector search
- No-answer threshold: 0.45 (cosine score)
- This evaluates retrieval only, not LLM answer generation
