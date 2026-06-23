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
