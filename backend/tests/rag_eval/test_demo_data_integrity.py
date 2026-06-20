"""Demo data integrity tests.

Validates that all demo data files are well-formed, cross-referenced,
and compatible with the RAG evaluation harness.
"""

import json
from pathlib import Path

import pytest

DEMO_DATA_DIR = Path(__file__).resolve().parents[2] / "scripts" / "demo_data"
KNOWLEDGE_DIR = DEMO_DATA_DIR / "knowledge"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(filename: str):
    path = DEMO_DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _knowledge_files() -> set[str]:
    return {f.name for f in KNOWLEDGE_DIR.glob("*.md")}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDemoDataIntegrity:
    """Validate demo data file structure and cross-references."""

    # --- JSON format ---

    def test_agents_json_is_valid(self):
        """agents.json should be a non-empty list with required fields."""
        data = _load_json("agents.json")
        assert isinstance(data, list) and len(data) >= 2
        required = {"id", "name", "description", "language", "system_prompt",
                     "allowed_topics", "escalation_policy", "no_answer_policy"}
        for agent in data:
            assert required.issubset(set(agent.keys())), (
                f"Agent '{agent.get('id')}' missing fields: {required - set(agent.keys())}"
            )

    def test_demo_questions_json_is_valid(self):
        """demo_questions.json should be a non-empty list with required fields."""
        data = _load_json("demo_questions.json")
        assert isinstance(data, list) and len(data) >= 10
        required = {"id", "question", "language", "category",
                     "expected_answer_keywords", "expected_sources",
                     "should_answer", "risk_type"}
        for q in data:
            assert required.issubset(set(q.keys())), (
                f"Question '{q.get('id')}' missing fields: {required - set(q.keys())}"
            )

    def test_conversations_json_is_valid(self):
        """conversations.json should be a non-empty list with required fields."""
        data = _load_json("conversations.json")
        assert isinstance(data, list) and len(data) >= 3
        required = {"conversation_id", "agent_id", "turns",
                     "expected_outcome", "should_escalate"}
        for conv in data:
            assert required.issubset(set(conv.keys())), (
                f"Conversation '{conv.get('conversation_id')}' missing fields: "
                f"{required - set(conv.keys())}"
            )

    def test_expected_evidence_json_is_valid(self):
        """expected_evidence.json should be a dict with required fields per entry."""
        data = _load_json("expected_evidence.json")
        assert isinstance(data, dict) and len(data) >= 10
        for key, val in data.items():
            assert "expected_sources" in val, f"Evidence '{key}' missing expected_sources"
            assert "key_facts" in val, f"Evidence '{key}' missing key_facts"

    def test_bad_cases_json_is_valid(self):
        """bad_cases.json should be a non-empty list with required fields."""
        data = _load_json("bad_cases.json")
        assert isinstance(data, list) and len(data) >= 5
        required = {"id", "type", "question", "language", "risk_type",
                     "description", "expected_behavior"}
        for bc in data:
            assert required.issubset(set(bc.keys())), (
                f"Bad case '{bc.get('id')}' missing fields: {required - set(bc.keys())}"
            )

    # --- Knowledge files ---

    def test_knowledge_files_exist(self):
        """All expected knowledge markdown files should exist."""
        files = _knowledge_files()
        for expected in ["product_faq.md", "return_policy.md", "troubleshooting.md"]:
            assert expected in files, f"Missing knowledge file: {expected}"

    def test_knowledge_files_are_nonempty(self):
        """Knowledge files should have content."""
        for fname in _knowledge_files():
            path = KNOWLEDGE_DIR / fname
            assert path.stat().st_size > 100, f"{fname} is suspiciously small"

    # --- Cross-references ---

    def test_question_sources_exist_in_knowledge(self):
        """Every expected_source in demo_questions should reference an existing knowledge file."""
        questions = _load_json("demo_questions.json")
        kb_files = _knowledge_files()
        for q in questions:
            for src in q.get("expected_sources", []):
                assert src in kb_files, (
                    f"{q['id']}: expected_source '{src}' not found in knowledge/"
                )

    def test_evidence_sources_exist_in_knowledge(self):
        """Every expected_source in expected_evidence should reference an existing knowledge file."""
        evidence = _load_json("expected_evidence.json")
        kb_files = _knowledge_files()
        for key, val in evidence.items():
            for src in val.get("expected_sources", []):
                assert src in kb_files, (
                    f"Evidence '{key}': expected_source '{src}' not found in knowledge/"
                )

    def test_all_questions_have_evidence_entry(self):
        """Every demo question should have a corresponding entry in expected_evidence."""
        questions = _load_json("demo_questions.json")
        evidence = _load_json("expected_evidence.json")
        for q in questions:
            assert q["id"] in evidence, (
                f"Question '{q['id']}' has no entry in expected_evidence.json"
            )

    # --- Bad cases ---

    def test_bad_cases_have_risk_type(self):
        """Every bad case should have a non-null risk_type."""
        bad_cases = _load_json("bad_cases.json")
        for bc in bad_cases:
            assert bc.get("risk_type") is not None, (
                f"Bad case '{bc['id']}' has null risk_type"
            )

    # --- Conversations ---

    def test_conversations_have_expected_outcome(self):
        """Every conversation should have an expected_outcome."""
        convs = _load_json("conversations.json")
        for conv in convs:
            assert conv.get("expected_outcome"), (
                f"Conversation '{conv['conversation_id']}' missing expected_outcome"
            )

    def test_conversations_reference_valid_agents(self):
        """Conversation agent_ids should match a defined agent."""
        convs = _load_json("conversations.json")
        agents = _load_json("agents.json")
        agent_ids = {a["id"] for a in agents}
        for conv in convs:
            assert conv["agent_id"] in agent_ids, (
                f"Conversation '{conv['conversation_id']}' references "
                f"unknown agent '{conv['agent_id']}'"
            )

    def test_conversation_turns_have_role_and_content(self):
        """Every conversation turn should have 'role' and 'content'."""
        convs = _load_json("conversations.json")
        for conv in convs:
            for i, turn in enumerate(conv.get("turns", [])):
                assert "role" in turn, (
                    f"{conv['conversation_id']} turn {i}: missing 'role'"
                )
                assert "content" in turn, (
                    f"{conv['conversation_id']} turn {i}: missing 'content'"
                )
                assert turn["role"] in ("user", "assistant"), (
                    f"{conv['conversation_id']} turn {i}: "
                    f"unexpected role '{turn['role']}'"
                )
