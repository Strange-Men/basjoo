"""
Tests for real eval configuration parsing.

These tests verify config logic WITHOUT making real API calls or connecting to Qdrant.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = BACKEND_DIR / "scripts"


class TestRealEvalConfig:
    """Test real eval configuration constants and parsing."""

    def test_default_collection_name(self):
        """Default collection name should be customerops_demo_real_eval."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "seed_demo_data", SCRIPTS_DIR / "seed_demo_data.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.DEFAULT_COLLECTION == "customerops_demo_real_eval"

    def test_embedding_dim_constant(self):
        """Embedding dimension should be 1024."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "seed_demo_data", SCRIPTS_DIR / "seed_demo_data.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.EMBEDDING_DIM == 1024

    def test_real_eval_case_ids(self):
        """Real eval should select 10 specific test cases."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_rag_eval", SCRIPTS_DIR / "run_rag_eval.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert len(mod.REAL_EVAL_CASE_IDS) == 10
        # Original 5 cases
        assert "TC001" in mod.REAL_EVAL_CASE_IDS
        assert "TC002" in mod.REAL_EVAL_CASE_IDS
        assert "TC006" in mod.REAL_EVAL_CASE_IDS  # no-answer case
        assert "TC010" in mod.REAL_EVAL_CASE_IDS
        assert "TC014" in mod.REAL_EVAL_CASE_IDS
        # New 5 cases (v2.1.1)
        assert "TC004" in mod.REAL_EVAL_CASE_IDS  # multi_doc_retrieval
        assert "TC007" in mod.REAL_EVAL_CASE_IDS  # no_answer_fallback ZH
        assert "TC008" in mod.REAL_EVAL_CASE_IDS  # low_relevance_reject
        assert "TC011" in mod.REAL_EVAL_CASE_IDS  # evidence_citation ZH
        assert "TC012" in mod.REAL_EVAL_CASE_IDS  # hallucination_risk

    def test_real_no_answer_threshold(self):
        """No-answer threshold should be a reasonable float."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_rag_eval", SCRIPTS_DIR / "run_rag_eval.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert 0.0 < mod.REAL_NO_ANSWER_THRESHOLD < 1.0

    def test_load_real_env_missing_key(self):
        """_load_real_env should exit if SILICONFLOW_API_KEY is missing."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_rag_eval", SCRIPTS_DIR / "run_rag_eval.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with patch.dict(os.environ, {"SILICONFLOW_API_KEY": ""}, clear=False):
            with patch("dotenv.load_dotenv"):
                with pytest.raises(SystemExit):
                    mod._load_real_env()

    def test_load_real_env_with_key(self):
        """_load_real_env should return config dict when key is set."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_rag_eval", SCRIPTS_DIR / "run_rag_eval.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        env = {
            "SILICONFLOW_API_KEY": "test-key-123",
            "QDRANT_URL": "http://localhost:6333",
            "SILICONFLOW_BASE_URL": "https://api.siliconflow.cn/v1",
            "SILICONFLOW_EMBEDDING_MODEL": "Qwen/Qwen3-Embedding-0.6B",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("dotenv.load_dotenv"):
                cfg = mod._load_real_env()

        assert cfg["api_key"] == "test-key-123"
        assert cfg["qdrant_url"] == "http://localhost:6333"
        assert "embeddings" in cfg["base_url"]

    def test_report_paths(self):
        """Report directory should be under backend/reports."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_rag_eval", SCRIPTS_DIR / "run_rag_eval.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert "reports" in str(mod.REPORTS_DIR)


class TestMismatchAnalysis:
    """Test mismatch analysis logic — pure unit tests, no API calls."""

    @staticmethod
    def _load_mod():
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_rag_eval", SCRIPTS_DIR / "run_rag_eval.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_mismatch_type_enum(self):
        """All mismatch types should be valid strings from the defined enum."""
        mod = self._load_mod()
        assert isinstance(mod.MISMATCH_TYPES, list)
        assert len(mod.MISMATCH_TYPES) == 6
        for t in mod.MISMATCH_TYPES:
            assert isinstance(t, str)
            # Each type should be lowercase alphanumeric with underscores only
            assert all(c.isalnum() or c == "_" for c in t)

    def test_full_match_returns_none(self):
        """When all expected sources are in top-3, mismatch_type should be 'none'."""
        mod = self._load_mod()
        result = mod._compute_mismatch(
            retrieved_top3=["doc_a.md", "doc_b.md", "doc_c.md"],
            returned_sources_top5=["doc_a.md", "doc_b.md", "doc_c.md", "doc_d.md", "doc_e.md"],
            expected_set={"doc_a.md"},
            scenario="normal_hit",
            top_score=0.7,
            no_answer_detected=False,
        )
        assert result["mismatch_type"] == "none"
        assert result["matched_sources"] == ["doc_a.md"]
        assert result["missing_sources"] == []
        # unexpected_sources may contain extra docs from top-3 that are not expected
        # but mismatch_type is still "none" because all expected were found

    def test_missing_expected_source(self):
        """When expected source is not in top-5, mismatch_type should be 'missing_expected_source'."""
        mod = self._load_mod()
        result = mod._compute_mismatch(
            retrieved_top3=["doc_a.md", "doc_b.md", "doc_c.md"],
            returned_sources_top5=["doc_a.md", "doc_b.md", "doc_c.md", "doc_d.md", "doc_e.md"],
            expected_set={"doc_x.md"},
            scenario="normal_hit",
            top_score=0.7,
            no_answer_detected=False,
        )
        assert result["mismatch_type"] == "missing_expected_source"
        assert result["matched_sources"] == []
        assert "doc_x.md" in result["missing_sources"]

    def test_low_rank_expected_source(self):
        """When expected source is in top-5 but not top-3, should detect low_rank_expected_source."""
        mod = self._load_mod()
        result = mod._compute_mismatch(
            retrieved_top3=["doc_a.md", "doc_b.md", "doc_c.md"],
            returned_sources_top5=["doc_a.md", "doc_b.md", "doc_c.md", "doc_x.md", "doc_e.md"],
            expected_set={"doc_a.md", "doc_x.md"},
            scenario="multi_doc_retrieval",
            top_score=0.7,
            no_answer_detected=False,
        )
        assert result["mismatch_type"] == "low_rank_expected_source"
        assert "doc_a.md" in result["matched_sources"]
        assert "doc_x.md" in result["missing_sources"]

    def test_no_answer_with_retrieval_noise(self):
        """No-answer case with high top_score should be 'no_answer_with_retrieval_noise'."""
        mod = self._load_mod()
        result = mod._compute_mismatch(
            retrieved_top3=["doc_a.md", "doc_b.md", "doc_c.md"],
            returned_sources_top5=["doc_a.md", "doc_b.md", "doc_c.md", "doc_d.md", "doc_e.md"],
            expected_set=set(),
            scenario="no_answer_fallback",
            top_score=0.50,
            no_answer_detected=False,
        )
        assert result["mismatch_type"] == "no_answer_with_retrieval_noise"
        assert result["matched_sources"] == []
        assert result["missing_sources"] == []

    def test_no_answer_correct_low_score(self):
        """No-answer case with low top_score should be 'none' (correctly detected)."""
        mod = self._load_mod()
        result = mod._compute_mismatch(
            retrieved_top3=["doc_a.md", "doc_b.md", "doc_c.md"],
            returned_sources_top5=["doc_a.md", "doc_b.md", "doc_c.md", "doc_d.md", "doc_e.md"],
            expected_set=set(),
            scenario="no_answer_fallback",
            top_score=0.30,
            no_answer_detected=True,
        )
        assert result["mismatch_type"] == "none"
        assert result["analysis_note"] == "Correctly identified as no-answer"
