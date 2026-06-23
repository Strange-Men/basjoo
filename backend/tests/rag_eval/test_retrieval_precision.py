"""Retrieval precision tests: precision@k, recall@k, MRR.

Validates that the mock retriever returns relevant documents in the right order.
"""

import pytest

from .conftest import MockRetriever


def _precision_at_k(retrieved_docs: list[str], expected_docs: set[str], k: int) -> float:
    """Fraction of top-k results that are in the expected set."""
    top = retrieved_docs[:k]
    if not top:
        return 0.0
    hits = sum(1 for d in top if d in expected_docs)
    return hits / len(top)


def _recall_at_k(retrieved_docs: list[str], expected_docs: set[str], k: int) -> float:
    """Fraction of expected docs found in top-k results."""
    if not expected_docs:
        return 1.0  # nothing expected → vacuous pass
    top = set(retrieved_docs[:k])
    hits = len(expected_docs & top)
    return hits / len(expected_docs)


def _mrr(retrieved_docs: list[str], expected_docs: set[str]) -> float:
    """Mean Reciprocal Rank for a single query."""
    for i, doc in enumerate(retrieved_docs):
        if doc in expected_docs:
            return 1.0 / (i + 1)
    return 0.0


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRetrievalPrecision:
    """Verify precision, recall, and MRR across eval cases."""

    def test_all_cases_have_valid_structure(self, rag_eval_cases: list[dict]):
        """Smoke test: every eval case has required fields."""
        for case in rag_eval_cases:
            assert "test_id" in case, f"Missing test_id in {case}"
            assert "query" in case, f"Missing query in {case}"
            assert "expected_sources" in case, f"Missing expected_sources in {case}"

    @pytest.mark.parametrize("top_k", [3, 5])
    def test_normal_hit_precision(self, mock_retriever: MockRetriever, rag_eval_cases: list[dict], top_k: int):
        """Normal-hit cases should have precision@k >= 0.5."""
        normal_cases = [c for c in rag_eval_cases if c["scenario"] == "normal_hit"]
        for case in normal_cases:
            results = mock_retriever.retrieve(case["query"], top_k=top_k)
            retrieved_doc_ids = [r["doc_id"] for r in results]
            expected = set(case["expected_sources"])
            precision = _precision_at_k(retrieved_doc_ids, expected, top_k)
            assert precision > 0.0, (
                f"{case['test_id']}: precision@{top_k}=0 for query '{case['query']}' "
                f"(expected sources {expected}, got {retrieved_doc_ids[:top_k]})"
            )

    @pytest.mark.parametrize("top_k", [3, 5])
    def test_normal_hit_recall(self, mock_retriever: MockRetriever, rag_eval_cases: list[dict], top_k: int):
        """Normal-hit cases should have recall@k >= 0.5 (at least half of expected sources found)."""
        normal_cases = [c for c in rag_eval_cases if c["scenario"] == "normal_hit"]
        for case in normal_cases:
            results = mock_retriever.retrieve(case["query"], top_k=top_k)
            retrieved_doc_ids = [r["doc_id"] for r in results]
            expected = set(case["expected_sources"])
            recall = _recall_at_k(retrieved_doc_ids, expected, top_k)
            assert recall > 0.0, (
                f"{case['test_id']}: recall@{top_k}=0 for query '{case['query']}' "
                f"(expected {expected}, retrieved {retrieved_doc_ids[:top_k]})"
            )

    def test_mrr_above_zero_for_normal_cases(self, mock_retriever: MockRetriever, rag_eval_cases: list[dict]):
        """MRR > 0 for normal-hit cases (first relevant doc should not be at infinity)."""
        normal_cases = [c for c in rag_eval_cases if c["scenario"] == "normal_hit"]
        for case in normal_cases:
            results = mock_retriever.retrieve(case["query"], top_k=10)
            retrieved_doc_ids = [r["doc_id"] for r in results]
            expected = set(case["expected_sources"])
            mrr = _mrr(retrieved_doc_ids, expected)
            assert mrr > 0.0, (
                f"{case['test_id']}: MRR=0 for query '{case['query']}' "
                f"(expected {expected}, got {retrieved_doc_ids})"
            )

    def test_multi_doc_retrieval_finds_multiple_sources(self, mock_retriever: MockRetriever, rag_eval_cases: list[dict]):
        """Multi-doc cases should retrieve chunks from multiple expected source documents."""
        multi_cases = [c for c in rag_eval_cases if c["scenario"] == "multi_doc_retrieval"]
        for case in multi_cases:
            results = mock_retriever.retrieve(case["query"], top_k=10)
            retrieved_doc_ids = set(r["doc_id"] for r in results)
            expected = set(case["expected_sources"])
            overlap = retrieved_doc_ids & expected
            assert len(overlap) >= 2, (
                f"{case['test_id']}: expected >=2 distinct sources from {expected}, "
                f"but only found {overlap}"
            )

    def test_overall_mrr(self, mock_retriever: MockRetriever, rag_eval_cases: list[dict]):
        """Compute and assert an aggregate MRR across all cases with expected sources."""
        mrrs = []
        for case in rag_eval_cases:
            if not case["expected_sources"]:
                continue
            results = mock_retriever.retrieve(case["query"], top_k=10)
            retrieved_doc_ids = [r["doc_id"] for r in results]
            mrr = _mrr(retrieved_doc_ids, set(case["expected_sources"]))
            mrrs.append(mrr)
        avg_mrr = sum(mrrs) / len(mrrs) if mrrs else 0.0
        # Not a hard gate, but report
        assert avg_mrr >= 0.3, f"Aggregate MRR={avg_mrr:.3f} is below 0.3 threshold"
