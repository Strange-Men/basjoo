#!/usr/bin/env python3
"""
Demo Data Seeder for SmartHome Support Demo.

Validates, previews, and exports demo data for the RAG evaluation harness.
Supports three modes:
  --validate-only : Validate JSON schema only (no output files)
  --dry-run       : Print what would be created (no DB write, no file write)
  --mock          : Generate/refresh mock fixtures for tests/rag_eval/

Default: validate-only (safe, no side effects).
Writing to a real database requires --write-db (NOT implemented in v1.1).

Usage:
    python scripts/seed_demo_data.py --validate-only
    python scripts/seed_demo_data.py --dry-run
    python scripts/seed_demo_data.py --mock
"""

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEMO_DATA_DIR = BACKEND_DIR / "scripts" / "demo_data"
FIXTURES_DIR = BACKEND_DIR / "tests" / "rag_eval" / "fixtures"
KNOWLEDGE_DIR = DEMO_DATA_DIR / "knowledge"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def load_json(path: Path) -> list | dict:
    """Load and return JSON data from a file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_agents(data: list) -> list[str]:
    """Validate agents.json structure."""
    errors = []
    required = {"id", "name", "description", "language", "system_prompt",
                "allowed_topics", "escalation_policy", "no_answer_policy"}
    for i, agent in enumerate(data):
        missing = required - set(agent.keys())
        if missing:
            errors.append(f"agents.json[{i}]: missing fields {missing}")
        if not isinstance(agent.get("allowed_topics", []), list):
            errors.append(f"agents.json[{i}]: allowed_topics must be a list")
    return errors


def validate_questions(data: list) -> list[str]:
    """Validate demo_questions.json structure."""
    errors = []
    required = {"id", "question", "language", "category",
                "expected_answer_keywords", "expected_sources",
                "should_answer", "risk_type"}
    for i, q in enumerate(data):
        missing = required - set(q.keys())
        if missing:
            errors.append(f"demo_questions.json[{i}]: missing fields {missing}")
        if not isinstance(q.get("expected_answer_keywords", []), list):
            errors.append(f"demo_questions.json[{i}]: expected_answer_keywords must be a list")
        if not isinstance(q.get("expected_sources", []), list):
            errors.append(f"demo_questions.json[{i}]: expected_sources must be a list")
    return errors


def validate_conversations(data: list) -> list[str]:
    """Validate conversations.json structure."""
    errors = []
    required = {"conversation_id", "agent_id", "turns", "expected_outcome", "should_escalate"}
    for i, conv in enumerate(data):
        missing = required - set(conv.keys())
        if missing:
            errors.append(f"conversations.json[{i}]: missing fields {missing}")
        for j, turn in enumerate(conv.get("turns", [])):
            if "role" not in turn:
                errors.append(f"conversations.json[{i}].turns[{j}]: missing 'role'")
            if "content" not in turn:
                errors.append(f"conversations.json[{i}].turns[{j}]: missing 'content'")
    return errors


def validate_evidence(data: dict) -> list[str]:
    """Validate expected_evidence.json structure."""
    errors = []
    for key, val in data.items():
        if "expected_sources" not in val:
            errors.append(f"expected_evidence.json['{key}']: missing expected_sources")
        if "key_facts" not in val:
            errors.append(f"expected_evidence.json['{key}']: missing key_facts")
    return errors


def validate_bad_cases(data: list) -> list[str]:
    """Validate bad_cases.json structure."""
    errors = []
    required = {"id", "type", "question", "language", "risk_type",
                "description", "expected_behavior"}
    for i, bc in enumerate(data):
        missing = required - set(bc.keys())
        if missing:
            errors.append(f"bad_cases.json[{i}]: missing fields {missing}")
    return errors


def validate_knowledge_files() -> list[str]:
    """Validate that knowledge markdown files exist."""
    errors = []
    expected_files = ["product_faq.md", "return_policy.md", "troubleshooting.md"]
    for fname in expected_files:
        fpath = KNOWLEDGE_DIR / fname
        if not fpath.exists():
            errors.append(f"knowledge/{fname}: file not found")
        elif fpath.stat().st_size == 0:
            errors.append(f"knowledge/{fname}: file is empty")
    return errors


def cross_validate(questions: list, evidence: dict) -> list[str]:
    """Cross-validate questions against evidence and knowledge files."""
    errors = []
    knowledge_files = {f.name for f in KNOWLEDGE_DIR.glob("*.md")}

    for q in questions:
        qid = q["id"]
        # Check expected_sources exist in knowledge dir
        for src in q.get("expected_sources", []):
            if src not in knowledge_files:
                errors.append(f"{qid}: expected_source '{src}' not found in knowledge/")

        # Check evidence file has entry for this question
        if qid not in evidence:
            errors.append(f"{qid}: no entry in expected_evidence.json")

    return errors


def validate_all() -> tuple[dict, list[str]]:
    """Run all validations. Returns (data_dict, errors)."""
    errors = []
    data = {}

    # Load all JSON files
    for name, filename in [
        ("agents", "agents.json"),
        ("questions", "demo_questions.json"),
        ("conversations", "conversations.json"),
        ("evidence", "expected_evidence.json"),
        ("bad_cases", "bad_cases.json"),
    ]:
        path = DEMO_DATA_DIR / filename
        if not path.exists():
            errors.append(f"{filename}: file not found")
            continue
        try:
            data[name] = load_json(path)
        except json.JSONDecodeError as e:
            errors.append(f"{filename}: invalid JSON — {e}")

    if errors:
        return data, errors

    # Schema validation
    errors.extend(validate_agents(data["agents"]))
    errors.extend(validate_questions(data["questions"]))
    errors.extend(validate_conversations(data["conversations"]))
    errors.extend(validate_evidence(data["evidence"]))
    errors.extend(validate_bad_cases(data["bad_cases"]))
    errors.extend(validate_knowledge_files())

    # Cross-validation
    if not errors:
        errors.extend(cross_validate(data["questions"], data["evidence"]))

    return data, errors


# ---------------------------------------------------------------------------
# Dry-run: print summary
# ---------------------------------------------------------------------------

def dry_run(data: dict):
    """Print a human-readable summary of what would be seeded."""
    print("=" * 60)
    print("  Demo Data — Dry Run Summary")
    print("=" * 60)

    # Agents
    agents = data.get("agents", [])
    print(f"\n  Agents: {len(agents)}")
    for a in agents:
        print(f"    - {a['id']}: {a['name']}")
        print(f"      Languages: {', '.join(a.get('language', []))}")
        print(f"      Topics: {len(a.get('allowed_topics', []))}")

    # Knowledge
    kb_files = list(KNOWLEDGE_DIR.glob("*.md"))
    print(f"\n  Knowledge Documents: {len(kb_files)}")
    for f in kb_files:
        size_kb = f.stat().st_size / 1024
        print(f"    - {f.name} ({size_kb:.1f} KB)")

    # Questions
    questions = data.get("questions", [])
    answerable = sum(1 for q in questions if q.get("should_answer"))
    print(f"\n  Demo Questions: {len(questions)}")
    print(f"    - Answerable: {answerable}")
    print(f"    - Unanswerable: {len(questions) - answerable}")
    categories = {}
    for q in questions:
        cat = q.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"    - {cat}: {count}")

    # Conversations
    convs = data.get("conversations", [])
    print(f"\n  Conversations: {len(convs)}")
    for c in convs:
        print(f"    - {c['conversation_id']}: {c.get('description', '')[:50]}")
        print(f"      Turns: {len(c.get('turns', []))}, Outcome: {c.get('expected_outcome')}")

    # Evidence
    evidence = data.get("evidence", {})
    print(f"\n  Expected Evidence Entries: {len(evidence)}")

    # Bad Cases
    bad = data.get("bad_cases", [])
    print(f"\n  Bad Cases: {len(bad)}")
    risk_types = {}
    for b in bad:
        rt = b.get("risk_type") or "none"
        risk_types[rt] = risk_types.get(rt, 0) + 1
    for rt, count in sorted(risk_types.items()):
        print(f"    - {rt}: {count}")

    print("\n" + "=" * 60)
    print("  No files written. No database changes.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Mock export: generate fixtures for tests/rag_eval/
# ---------------------------------------------------------------------------

def generate_mock_fixtures(data: dict):
    """Generate mock fixtures from demo data.

    Produces a SEPARATE knowledge base file from the demo markdown files.
    The original v1.0 fixtures (demo_knowledge_base.json, rag_eval_cases.json)
    are preserved untouched to maintain backward compatibility with tests.

    Output:
      - fixtures/demo_knowledge_base_full.json (new, from knowledge/*.md)
    """
    print("=" * 60)
    print("  Generating Mock Fixtures")
    print("=" * 60)

    # Preserve original fixtures — do NOT overwrite
    original_kb = FIXTURES_DIR / "demo_knowledge_base.json"
    original_cases = FIXTURES_DIR / "rag_eval_cases.json"
    print(f"  Preserving: {original_kb.name} (v1.0 fixture, unchanged)")
    print(f"  Preserving: {original_cases.name} (v1.0 fixture, unchanged)")

    # 1. Generate demo_knowledge_base_full.json from knowledge markdown files
    documents = []
    for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
        doc_id = md_file.name
        content = md_file.read_text(encoding="utf-8")

        # Extract title from first heading
        title = doc_id.replace(".md", "").replace("_", " ").title()
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Split into chunks (by ## headings, or paragraph-based)
        chunks = _chunk_markdown(content, doc_id)
        documents.append({
            "doc_id": doc_id,
            "source_title": title,
            "source_url": f"https://example.com/{doc_id.replace('.md', '')}",
            "source_type": "file",
            "chunks": chunks,
        })

    kb_data = {"documents": documents}
    kb_full_path = FIXTURES_DIR / "demo_knowledge_base_full.json"
    kb_full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(kb_full_path, "w", encoding="utf-8") as f:
        json.dump(kb_data, f, indent=2, ensure_ascii=False)
    print(f"\n  Written: {kb_full_path.name}")
    print(f"    Documents: {len(documents)}")
    total_chunks = sum(len(d["chunks"]) for d in documents)
    print(f"    Total chunks: {total_chunks}")

    # 2. Summary of demo eval cases (for reference, not written)
    questions = data.get("questions", [])
    answerable = sum(1 for q in questions if q.get("should_answer"))
    print(f"\n  Demo eval cases available: {len(questions)}")
    print(f"    Answerable: {answerable}")
    print(f"    Unanswerable: {len(questions) - answerable}")
    print(f"  (Original rag_eval_cases.json with 15 v1.0 cases preserved)")

    print("\n" + "=" * 60)
    print("  Mock fixtures generated successfully.")
    print("  Original v1.0 fixtures untouched — tests remain compatible.")
    print("=" * 60)


def _chunk_markdown(content: str, doc_id: str) -> list[dict]:
    """Split markdown content into paragraph-level chunks.

    Splits on blank lines. Each non-empty paragraph becomes a chunk.
    Small consecutive paragraphs (under 80 chars) are merged together.
    This produces fine-grained chunks suitable for RAG retrieval.
    """
    chunks = []
    chunk_index = 0
    prefix = doc_id.replace(".md", "")

    # Split into raw paragraphs on blank lines
    raw_paragraphs = []
    current = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped == "" and current:
            raw_paragraphs.append("\n".join(current))
            current = []
        elif stripped:
            current.append(stripped)
    if current:
        raw_paragraphs.append("\n".join(current))

    # Merge small paragraphs and skip the title heading
    buffer = ""
    for para in raw_paragraphs:
        # Skip top-level heading (title)
        if para.startswith("# ") and not para.startswith("## "):
            if buffer:
                chunks.append({
                    "chunk_id": f"{prefix}_{chunk_index}",
                    "text": buffer.strip(),
                    "chunk_index": chunk_index,
                })
                chunk_index += 1
                buffer = ""
            continue

        # If paragraph starts with ## heading, flush buffer first
        if para.startswith("## ") and buffer:
            chunks.append({
                "chunk_id": f"{prefix}_{chunk_index}",
                "text": buffer.strip(),
                "chunk_index": chunk_index,
            })
            chunk_index += 1
            buffer = para
        # Merge small paragraphs
        elif len(para) < 80 and buffer:
            buffer = buffer + "\n" + para
        else:
            if buffer:
                chunks.append({
                    "chunk_id": f"{prefix}_{chunk_index}",
                    "text": buffer.strip(),
                    "chunk_index": chunk_index,
                })
                chunk_index += 1
            buffer = para

    if buffer:
        chunks.append({
            "chunk_id": f"{prefix}_{chunk_index}",
            "text": buffer.strip(),
            "chunk_index": chunk_index,
        })

    if not chunks:
        chunks.append({
            "chunk_id": f"{prefix}_0",
            "text": content.strip(),
            "chunk_index": 0,
        })

    return chunks


# ---------------------------------------------------------------------------
# Database write (NOT implemented in v1.1)
# ---------------------------------------------------------------------------

def write_to_db(data: dict):
    """Write demo data to the database.

    NOT IMPLEMENTED in v1.1. Requires:
    - Valid database connection
    - Proper ORM models
    - Environment validation
    """
    # Check for production environment
    env = os.environ.get("ENVIRONMENT", "").lower()
    if env in ("production", "prod"):
        print("ERROR: Cannot write demo data to a production database.")
        print("Set ENVIRONMENT=development or ENVIRONMENT=staging to proceed.")
        sys.exit(1)

    print("ERROR: --write-db is not implemented in v1.1.")
    print("Demo data is designed for mock/dry-run mode only.")
    print("To write to a real database, implement this function with")
    print("proper ORM integration and environment validation.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Seed demo data for SmartHome Support Demo"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--validate-only", action="store_true", default=True,
                       help="Validate demo data files (default)")
    group.add_argument("--dry-run", action="store_true",
                       help="Print summary of what would be seeded")
    group.add_argument("--mock", action="store_true",
                       help="Generate mock fixtures for tests/rag_eval/")
    parser.add_argument("--write-db", action="store_true",
                        help="Write to database (NOT implemented in v1.1)")
    args = parser.parse_args()

    # Validate first (always)
    print("Validating demo data files...")
    data, errors = validate_all()

    if errors:
        print(f"\nValidation FAILED with {len(errors)} error(s):")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    print(f"Validation PASSED — all {len(data)} files valid.\n")

    # Dispatch
    if args.write_db:
        write_to_db(data)
    elif args.mock:
        generate_mock_fixtures(data)
    elif args.dry_run:
        dry_run(data)
    else:
        # --validate-only (default)
        print("All demo data files are valid.")
        print("Use --dry-run to see a summary, --mock to generate fixtures.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
