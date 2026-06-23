# RAG Evaluation Report — Real Retrieval

**Generated**: 2026-06-23T13:38:44.749296+00:00
**Test Mode**: real (SiliconFlow + Qdrant)
**Collection**: customerops_demo_real_eval
**Embedding Model**: Qwen/Qwen3-Embedding-0.6B

## Summary

| Metric | Value |
|---|---|
| Total Cases | 10 |
| Passed | 10 (100%) |
| Failed | 0 |

## Retrieval Metrics

| Metric | Value |
|---|---|
| Precision@3 | 0.600 |
| Recall@3 | 0.950 |
| MRR | 0.600 |
| Hit Rate | 0.600 |
| No-Answer Accuracy | 100.0% |

## Per-Case Results

- TC001: ✅ score=0.6862 p3=1.00 r3=1.00 | How do I return a product?
- TC002: ✅ score=0.6672 p3=1.00 r3=1.00 | 产品保修多久？
- TC004: ✅ score=0.6914 p3=1.00 r3=0.50 | What is the warranty and return policy for electro
- TC006: ✅ score=0.2767 p3=0.00 r3=1.00 | What is the weather like today?
- TC007: ✅ score=0.3459 p3=0.00 r3=1.00 | 你们公司的股票代码是什么？
- TC008: ✅ score=0.2472 p3=0.00 r3=1.00 | Can you recommend a good restaurant nearby?
- TC010: ✅ score=0.6302 p3=1.00 r3=1.00 | What is the return window for purchases?
- TC011: ✅ score=0.6668 p3=1.00 r3=1.00 | 产品保修包含哪些情况？
- TC012: ✅ score=0.3116 p3=0.00 r3=1.00 | What is the company's headquarters address?
- TC014: ✅ score=0.9034 p3=1.00 r3=1.00 | 设备无法开机怎么办？

## Mismatch Analysis

Per-case mismatch diagnostics for retrieval quality debugging.

| Case | Scenario | Mismatch Type | Matched | Missing | Unexpected | Note |
|---|---|---|---|---|---|---|
| TC001 | normal_hit | none | return_policy.md | — | — | All expected sources found in top-3 |
| TC002 | normal_hit | none | product_faq.md | — | — | All expected sources found in top-3 |
| TC004 | multi_doc_retrieval | missing_expected_source | product_faq.md | return_policy.md | — | Expected ['return_policy.md'] not found in top-5 |
| TC006 | no_answer_fallback | none | — | — | product_faq.md | Correctly identified as no-answer |
| TC007 | no_answer_fallback | none | — | — | troubleshooting.md | Correctly identified as no-answer |
| TC008 | low_relevance_reject | none | — | — | product_faq.md | Correctly identified as no-answer |
| TC010 | evidence_citation | none | return_policy.md | — | — | All expected sources found in top-3 |
| TC011 | evidence_citation | none | product_faq.md | — | — | All expected sources found in top-3 |
| TC012 | hallucination_risk | none | — | — | product_faq.md | Correctly identified as no-answer |
| TC014 | normal_hit | none | troubleshooting.md | — | — | All expected sources found in top-3 |

### Summary

- **Full match**: 5 cases — TC001, TC002, TC010, TC011, TC014
- **Source mismatch**: 1 cases — TC004
- **No-answer with retrieval noise**: 0 cases — none

### Observations

- **TC004** (multi_doc_retrieval): Expected ['return_policy.md'] not found in top-5

## Notes

- Real retrieval using SiliconFlow embedding + Qdrant vector search
- No-answer threshold: 0.45 (cosine score)
- This evaluates retrieval only, not LLM answer generation
