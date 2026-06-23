# RAG Evaluation Report

**Generated**: 2026-06-23T13:17:32.046642+00:00
**Test Mode**: mock

## Summary

| Metric | Value |
|---|---|
| Total Cases | 15 |
| Passed | 15 (100%) |
| Failed | 0 (0%) |

## Retrieval Metrics

| Metric | Value |
|---|---|
| Precision@3 | 0.567 |
| Recall@3 | 0.978 |
| Precision@5 | 0.527 |
| Recall@5 | 1.000 |
| MRR | 0.600 |

## Quality Metrics

| Metric | Value |
|---|---|
| No-Answer Accuracy | 100.0% |
| Citation Accuracy | 88.9% |
| Hallucination Risk Cases | 0 |

## Test Results

### Passed Cases

- TC001: How do I return a product? ✅ (normal_hit)
- TC002: 产品保修多久？ ✅ (normal_hit)
- TC003: 如何重置设备到出厂设置？ ✅ (normal_hit)
- TC004: What is the warranty and return policy for electronics? ✅ (multi_doc_retrieval)
- TC005: 设备出现故障但已经过了保修期，还能退货吗？ ✅ (multi_doc_retrieval)
- TC006: What is the weather like today? ✅ (no_answer_fallback)
- TC007: 你们公司的股票代码是什么？ ✅ (no_answer_fallback)
- TC008: Can you recommend a good restaurant nearby? ✅ (low_relevance_reject)
- TC009: 你能帮我写一首诗吗？ ✅ (low_relevance_reject)
- TC010: What is the return window for purchases? ✅ (evidence_citation)
- TC011: 产品保修包含哪些情况？ ✅ (evidence_citation)
- TC012: What is the company's headquarters address? ✅ (hallucination_risk)
- TC013: 你们的创始人是谁？哪一年成立的？ ✅ (hallucination_risk)
- TC014: 设备无法开机怎么办？ ✅ (normal_hit)
- TC015: How long does shipping take? ✅ (normal_hit)

## Notes

- All results from **mock mode** (no API keys, no Qdrant)
- Retrieval uses deterministic char-based embedding (not semantic)
- To evaluate real RAG quality, integrate with actual Qdrant + embedding API
