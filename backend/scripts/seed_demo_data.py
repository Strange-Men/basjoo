#!/usr/bin/env python3
"""
Demo Data Seeder for SmartHome Support Demo.

Validates, previews, and exports demo data for the RAG evaluation harness.
Supports modes:
  --validate-only  : Validate JSON schema only (no output files)
  --dry-run        : Print what would be created (no DB write, no file write)
  --mock           : Generate/refresh mock fixtures for tests/rag_eval/
  --write-db       : Write demo knowledge base to Qdrant (real mode, v2.0)
  --write-qdrant   : Alias for --write-db

Default: validate-only (safe, no side effects).

Usage:
    python scripts/seed_demo_data.py --validate-only
    python scripts/seed_demo_data.py --dry-run
    python scripts/seed_demo_data.py --mock
    python scripts/seed_demo_data.py --write-db
    python scripts/seed_demo_data.py --write-qdrant
    python scripts/seed_demo_data.py --write-db --reset
    python scripts/seed_demo_data.py --write-db --collection-name my_collection
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
# Database write — real Qdrant mode (v2.0)
# ---------------------------------------------------------------------------

DEFAULT_COLLECTION = "customerops_demo_real_eval"
EMBEDDING_DIM = 1024


def _load_env_or_exit() -> dict:
    """Load required env vars for real Qdrant write. Returns config dict."""
    from dotenv import load_dotenv
    # .env lives in repo root (basjoo/), not backend/
    repo_root = BACKEND_DIR.parent
    env_path = repo_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    api_key = os.environ.get("SILICONFLOW_API_KEY", "")
    base_url = os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    model = os.environ.get("SILICONFLOW_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")

    if not api_key:
        print("ERROR: SILICONFLOW_API_KEY not set in environment or .env file.")
        print("Set it in backend/.env or as an environment variable.")
        sys.exit(1)

    return {
        "qdrant_url": qdrant_url,
        "api_key": api_key,
        "base_url": base_url.rstrip("/") + "/embeddings",
        "model": model,
    }


def _embed_texts_sync(texts: list[str], cfg: dict) -> list[list[float]]:
    """Call SiliconFlow embedding API (sync) with retry. Returns list of vectors."""
    import httpx
    import time

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    payload = {"model": cfg["model"], "input": texts}

    max_retries = 3
    last_err = None
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=60.0, verify=False) as client:
                resp = client.post(cfg["base_url"], json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return [item["embedding"] for item in data.get("data", [])]
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                time.sleep(wait)
    raise last_err


def write_to_db(data: dict, collection_name: str = DEFAULT_COLLECTION, reset: bool = False):
    """Write demo knowledge base to Qdrant with real SiliconFlow embeddings.

    Steps:
    1. Load demo knowledge base (from fixtures)
    2. Generate embeddings via SiliconFlow API
    3. Create/recreate Qdrant collection
    4. Upsert all chunks as points
    """
    import uuid
    import urllib.request
    import urllib.error

    cfg = _load_env_or_exit()
    qdrant_url = cfg["qdrant_url"].rstrip("/")

    # Load knowledge base from fixtures
    kb_path = FIXTURES_DIR / "demo_knowledge_base.json"
    if not kb_path.exists():
        print(f"ERROR: Knowledge base fixture not found: {kb_path}")
        print("Run --mock first to generate fixtures.")
        sys.exit(1)

    with open(kb_path, encoding="utf-8") as f:
        kb = json.load(f)

    docs = kb.get("documents", [])
    if not docs:
        print("ERROR: No documents in knowledge base.")
        sys.exit(1)

    # Collect all chunks with metadata
    all_chunks = []
    for doc in docs:
        for chunk in doc.get("chunks", []):
            all_chunks.append({
                "doc_id": doc["doc_id"],
                "chunk_id": chunk.get("chunk_id", f"{doc['doc_id']}_{chunk['chunk_index']}"),
                "source_title": doc["source_title"],
                "source_type": doc.get("source_type", "file"),
                "content": chunk["text"],
            })

    print("=" * 60)
    print("  Seed Demo Data — Real Qdrant Write (v2.0)")
    print("=" * 60)
    print(f"  Documents:       {len(docs)}")
    print(f"  Chunks:          {len(all_chunks)}")
    print(f"  Collection:      {collection_name}")
    print(f"  Embedding model: {cfg['model']}")
    print(f"  Embedding dim:   {EMBEDDING_DIM}")
    print(f"  Qdrant URL:      {qdrant_url}")
    print(f"  Reset:           {reset}")
    print()

    # Generate embeddings in batch
    print("  Generating embeddings via SiliconFlow API...")
    texts = [c["content"] for c in all_chunks]
    try:
        vectors = _embed_texts_sync(texts, cfg)
    except Exception as e:
        print(f"ERROR: Embedding API call failed: {e}")
        sys.exit(1)

    if len(vectors) != len(texts):
        print(f"ERROR: Expected {len(texts)} embeddings, got {len(vectors)}")
        sys.exit(1)

    actual_dim = len(vectors[0]) if vectors else 0
    print(f"  Embeddings generated: {len(vectors)} (dim={actual_dim})")

    if actual_dim != EMBEDDING_DIM:
        print(f"  WARNING: Expected dim={EMBEDDING_DIM}, got dim={actual_dim}. Using actual dim.")

    # Connect to Qdrant via HTTP (urllib, avoids httpx/qdrant_client issues)
    print("\n  Connecting to Qdrant...")
    try:
        with urllib.request.urlopen(f"{qdrant_url}/collections", timeout=30) as resp:
            data = json.loads(resp.read())
            existing_names = [c["name"] for c in data.get("result", {}).get("collections", [])]
            print(f"  Connected. Existing collections: {len(existing_names)}")
    except Exception as e:
        print(f"ERROR: Cannot connect to Qdrant at {qdrant_url}: {e}")
        sys.exit(1)

    def _qdrant_request(method: str, path: str, body: dict | None = None):
        """Helper for Qdrant REST API calls via urllib."""
        url = f"{qdrant_url}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    # Create or recreate collection
    # Delete if reset requested
    if reset and collection_name in existing_names:
        status, _ = _qdrant_request("DELETE", f"/collections/{collection_name}")
        if status in (200, 404):
            print(f"  Deleted existing collection: {collection_name}")
            existing_names.remove(collection_name)
        else:
            print(f"  WARNING: Failed to delete collection: {status}")

    # Create collection if it doesn't exist
    if collection_name not in existing_names:
        create_payload = {
            "vectors": {
                "size": actual_dim,
                "distance": "Cosine",
            },
        }
        status, resp_data = _qdrant_request("PUT", f"/collections/{collection_name}", create_payload)
        if status in (200, 201):
            print(f"  Created collection: {collection_name} (dim={actual_dim}, COSINE)")
        else:
            print(f"ERROR: Failed to create collection: {status} {resp_data}")
            sys.exit(1)
    else:
        print(f"  Collection '{collection_name}' already exists, will upsert.")

    # Upsert points
    print("\n  Upserting points...")
    points = []
    for i, chunk in enumerate(all_chunks):
        points.append({
            "id": str(uuid.uuid4()),
            "vector": vectors[i],
            "payload": {
                "doc_id": chunk["doc_id"],
                "chunk_id": chunk["chunk_id"],
                "source_title": chunk["source_title"],
                "source_type": chunk["source_type"],
                "content": chunk["content"],
            },
        })

    # Batch upsert (max 100 per call)
    total_upserted = 0
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        upsert_payload = {"points": batch}
        status, resp_data = _qdrant_request(
            "PUT",
            f"/collections/{collection_name}/points?wait=true",
            upsert_payload,
        )
        if status not in (200, 201):
            print(f"ERROR: Upsert failed: {status} {resp_data}")
            sys.exit(1)
        total_upserted += len(batch)

    print(f"  Upserted {total_upserted} points.")

    # Verify
    status, resp_data = _qdrant_request("GET", f"/collections/{collection_name}")
    if status == 200:
        info = resp_data.get("result", {})
        points_count = info.get("points_count", "unknown")
        print(f"\n  Verification:")
        print(f"    Collection:   {collection_name}")
        print(f"    Points count: {points_count}")
        print(f"    Vector dim:   {actual_dim}")

    print("\n" + "=" * 60)
    print("  SUCCESS: Demo data written to Qdrant.")
    print("=" * 60)


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
    group.add_argument("--write-db", action="store_true",
                       help="Write demo knowledge base to Qdrant (real mode, v2.0)")
    group.add_argument("--write-qdrant", action="store_true",
                       help="Alias for --write-db")
    parser.add_argument("--reset", action="store_true",
                        help="Delete and recreate Qdrant collection before writing")
    parser.add_argument("--collection-name", default=DEFAULT_COLLECTION,
                        help=f"Qdrant collection name (default: {DEFAULT_COLLECTION})")
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
    if args.write_db or args.write_qdrant:
        write_to_db(data, collection_name=args.collection_name, reset=args.reset)
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
