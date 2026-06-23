"""Hallucination risk tests.

Validates that answers do not contain facts not present in the knowledge base,
using rule-based detection (no LLM judge needed).
"""

import pytest

from .conftest import MockRAGPipeline, MockRetriever


# Known facts NOT in the knowledge base — if these appear in the answer, it's a hallucination.
HALLUCINATION_MARKERS = [
    # Company info not in KB
    "headquarters",
    "founded in",
    "CEO",
    "stock",
    "IPO",
    "revenue",
    # Specific numbers not in KB
    "billion",
    "million",
    "employees",
    "offices in",
    # Chinese hallucination markers
    "创始人",
    "总部在",
    "成立于",
    "上市",
    "股票代码",
    "员工人数",
    "年收入",
]


class TestHallucinationRisk:
    """Verify that answers don't contain fabricated facts."""

    def test_hallucination_cases_produce_no_answer(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Cases flagged as hallucination_risk should ideally produce no_answer."""
        halluc_cases = [c for c in rag_eval_cases if c["scenario"] == "hallucination_risk"]
        assert len(halluc_cases) >= 2, "Need at least 2 hallucination risk cases"

        for case in halluc_cases:
            result = mock_rag_pipeline.query(case["query"])
            # These queries have no matching content in the KB
            assert result["no_answer"] is True or result["confidence"] == "none", (
                f"{case['test_id']}: hallucination-risk query '{case['query']}' "
                f"should produce no_answer or confidence=none, "
                f"got no_answer={result['no_answer']}, confidence={result['confidence']}"
            )

    def test_answer_does_not_contain_hallucination_markers(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Answers should not contain known hallucination markers."""
        for case in rag_eval_cases:
            result = mock_rag_pipeline.query(case["query"])
            answer_lower = result["answer"].lower()
            found_markers = [m for m in HALLUCINATION_MARKERS if m.lower() in answer_lower]
            assert not found_markers, (
                f"{case['test_id']}: answer contains hallucination markers {found_markers}: "
                f"'{result['answer'][:200]}'"
            )

    def test_answer_keywords_traceable_to_retrieved_chunks(
        self,
        mock_rag_pipeline: MockRAGPipeline,
        rag_eval_cases: list[dict],
    ):
        """For non-no-answer cases, answer content should overlap with retrieved chunk text.

        Uses substring matching to handle both English and Chinese text correctly
        (Chinese text has no whitespace word boundaries).
        """
        import re

        for case in rag_eval_cases:
            result = mock_rag_pipeline.query(case["query"])
            if result["no_answer"]:
                continue

            # Build corpus from retrieved chunks
            corpus = " ".join(c["text"].lower() for c in result["retrieved_chunks"])
            if not corpus:
                continue

            answer_lower = result["answer"].lower()

            # Extract meaningful tokens: English words (3+ chars) and Chinese bigrams
            en_words = set(re.findall(r'[a-zA-Z]{3,}', answer_lower))
            zh_chars = re.findall(r'[一-鿿]', answer_lower)
            zh_bigrams = set(zh_chars[i] + zh_chars[i + 1] for i in range(len(zh_chars) - 1))

            # Check English words via substring match
            en_hits = sum(1 for w in en_words if w in corpus)
            en_ratio = en_hits / len(en_words) if en_words else 1.0

            # Check Chinese bigrams via substring match
            zh_hits = sum(1 for bg in zh_bigrams if bg in corpus)
            zh_ratio = zh_hits / len(zh_bigrams) if zh_bigrams else 1.0

            # At least one of the two must have good overlap
            has_overlap = (
                (en_words and en_ratio >= 0.3) or
                (zh_bigrams and zh_ratio >= 0.3) or
                (not en_words and not zh_bigrams)  # nothing to check
            )
            assert has_overlap, (
                f"{case['test_id']}: answer content does not overlap with retrieved chunks "
                f"(en={en_ratio:.0%} of {len(en_words)}, zh={zh_ratio:.0%} of {len(zh_bigrams)}) — "
                f"possible hallucination. Answer: '{result['answer'][:100]}'"
            )

    def test_hallucination_risk_low_for_normal_cases(self, mock_rag_pipeline: MockRAGPipeline, rag_eval_cases: list[dict]):
        """Normal-hit cases should have no_answer=False and high confidence."""
        normal_cases = [c for c in rag_eval_cases if c["scenario"] == "normal_hit"]

        for case in normal_cases:
            result = mock_rag_pipeline.query(case["query"])
            assert result["no_answer"] is False, (
                f"{case['test_id']}: normal-hit query should not be no_answer"
            )
            assert result["confidence"] in ("high", "medium"), (
                f"{case['test_id']}: normal-hit query should have high/medium confidence, "
                f"got '{result['confidence']}'"
            )
