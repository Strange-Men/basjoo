"""Evidence / citation tests.

Validates that RAG answers can be traced back to retrieved context and that
source metadata (doc_id, source_title, source_url) is correct.
"""

import pytest

from .conftest import MockRAGPipeline


class TestEvidenceCitation:
    """Verify that answers include proper citations and source attribution."""

    def test_answer_has_sources(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Cases with expected sources should return at least one source."""
        citation_cases = [
            c for c in rag_eval_cases
            if c["scenario"] in ("normal_hit", "multi_doc_retrieval", "evidence_citation")
        ]

        for case in citation_cases:
            result = mock_rag_pipeline.query(case["query"])
            if result["no_answer"]:
                continue  # skip if pipeline decided no-answer
            assert len(result["sources"]) > 0, (
                f"{case['test_id']}: answer returned but no sources provided"
            )

    def test_source_doc_id_matches_expected(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Returned source doc_ids should include at least one expected source."""
        citation_cases = [
            c for c in rag_eval_cases
            if c["scenario"] in ("normal_hit", "multi_doc_retrieval", "evidence_citation")
        ]

        for case in citation_cases:
            result = mock_rag_pipeline.query(case["query"])
            if result["no_answer"]:
                continue
            source_doc_ids = {s["doc_id"] for s in result["sources"]}
            expected = set(case["expected_sources"])
            overlap = source_doc_ids & expected
            assert len(overlap) > 0, (
                f"{case['test_id']}: expected sources {expected} not found in "
                f"returned sources {source_doc_ids}"
            )

    def test_sources_have_required_fields(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Every source entry must have doc_id, source_title, source_url, source_type."""
        required_fields = {"doc_id", "source_title", "source_url", "source_type"}

        for case in rag_eval_cases:
            result = mock_rag_pipeline.query(case["query"])
            for src in result["sources"]:
                missing = required_fields - set(src.keys())
                assert not missing, (
                    f"{case['test_id']}: source missing fields {missing}: {src}"
                )

    def test_citation_source_title_is_nonempty(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Source titles should be non-empty strings."""
        for case in rag_eval_cases:
            result = mock_rag_pipeline.query(case["query"])
            for src in result["sources"]:
                assert isinstance(src["source_title"], str) and len(src["source_title"]) > 0, (
                    f"{case['test_id']}: source_title is empty or not a string: {src}"
                )

    def test_citation_source_url_is_valid(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Source URLs should start with http:// or https://."""
        for case in rag_eval_cases:
            result = mock_rag_pipeline.query(case["query"])
            for src in result["sources"]:
                url = src.get("source_url", "")
                if url:  # only check if present
                    assert url.startswith("http://") or url.startswith("https://"), (
                        f"{case['test_id']}: source_url '{url}' is not a valid URL"
                    )

    def test_no_fabricated_sources(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Returned doc_ids should exist in the knowledge base."""
        all_valid_doc_ids = {"return_policy.md", "product_faq.md", "troubleshooting.md"}

        for case in rag_eval_cases:
            result = mock_rag_pipeline.query(case["query"])
            for src in result["sources"]:
                assert src["doc_id"] in all_valid_doc_ids, (
                    f"{case['test_id']}: fabricated source doc_id '{src['doc_id']}' "
                    f"not in knowledge base"
                )
