"""No-answer fallback tests.

Validates that queries unrelated to the knowledge base produce a no-answer response
rather than fabricated content.
"""

import pytest

from .conftest import MockRAGPipeline


class TestNoAnswerFallback:
    """Verify that the RAG pipeline correctly refuses to answer irrelevant queries."""

    def test_unrelated_query_returns_no_answer(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Completely unrelated queries should produce no_answer=True."""
        no_answer_cases = [c for c in rag_eval_cases if c["scenario"] == "no_answer_fallback"]
        assert len(no_answer_cases) >= 2, "Need at least 2 no-answer cases"

        for case in no_answer_cases:
            result = mock_rag_pipeline.query(case["query"])
            assert result["no_answer"] is True, (
                f"{case['test_id']}: expected no_answer=True for unrelated query "
                f"'{case['query']}', got no_answer={result['no_answer']}"
            )

    def test_unrelated_query_has_no_sources(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """No-answer responses should have empty sources list."""
        no_answer_cases = [c for c in rag_eval_cases if c["scenario"] == "no_answer_fallback"]

        for case in no_answer_cases:
            result = mock_rag_pipeline.query(case["query"])
            assert result["sources"] == [], (
                f"{case['test_id']}: expected empty sources for no-answer, "
                f"got {result['sources']}"
            )

    def test_unrelated_query_confidence_is_none(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """No-answer responses should have confidence='none'."""
        no_answer_cases = [c for c in rag_eval_cases if c["scenario"] == "no_answer_fallback"]

        for case in no_answer_cases:
            result = mock_rag_pipeline.query(case["query"])
            assert result["confidence"] == "none", (
                f"{case['test_id']}: expected confidence='none', "
                f"got '{result['confidence']}'"
            )

    def test_low_relevance_does_not_fabricate(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Low-relevance queries should not produce high-confidence answers with sources."""
        low_cases = [c for c in rag_eval_cases if c["scenario"] == "low_relevance_reject"]

        for case in low_cases:
            result = mock_rag_pipeline.query(case["query"])
            # Low relevance should either be no_answer or low confidence
            if not result["no_answer"]:
                assert result["confidence"] in ("low", "none"), (
                    f"{case['test_id']}: low-relevance query '{case['query']}' "
                    f"should not have high/medium confidence, got '{result['confidence']}'"
                )

    def test_no_answer_contains_disclaimer_text(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """No-answer responses should contain a disclaimer-like phrase."""
        no_answer_cases = [c for c in rag_eval_cases if c["scenario"] == "no_answer_fallback"]

        for case in no_answer_cases:
            result = mock_rag_pipeline.query(case["query"])
            answer_lower = result["answer"].lower()
            has_disclaimer = any(
                phrase in answer_lower
                for phrase in ["don't have", "cannot", "unable", "not enough", "no information", "不确定", "无法"]
            )
            assert has_disclaimer, (
                f"{case['test_id']}: no-answer response should contain a disclaimer, "
                f"got: '{result['answer'][:100]}'"
            )
