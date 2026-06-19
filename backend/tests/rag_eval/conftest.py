"""
RAG Evaluation Harness — shared fixtures.

All fixtures are pure mocks: no Qdrant, no Embedding API, no LLM API.
"""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def rag_eval_cases() -> list[dict[str, Any]]:
    """Load eval cases from JSON."""
    with open(FIXTURES_DIR / "rag_eval_cases.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def demo_knowledge_base() -> dict[str, Any]:
    """Load demo knowledge base from JSON."""
    with open(FIXTURES_DIR / "demo_knowledge_base.json", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Mock embedding — deterministic, no API key
# ---------------------------------------------------------------------------

class MockEmbeddingProvider:
    """Deterministic word-level bag-of-words embedding.

    Uses word tokens (not characters) to avoid "weather" ≈ "warranty" confusion.
    Uses a deterministic hash (not Python's built-in hash which randomises per session)
    and 256 dimensions to reduce collisions.
    """

    DIM = 256

    _STOP = frozenset({
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should", "may",
        "might", "can", "shall", "of", "in", "on", "at", "to", "for", "with",
        "by", "from", "as", "into", "about", "between", "through", "during",
        "and", "or", "but", "not", "no", "so", "if", "than", "that", "this",
        "it", "its", "i", "you", "he", "she", "we", "they", "me", "him", "her",
        "us", "them", "my", "your", "his", "our", "their",
        "的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "这", "那",
        "吗", "呢", "吧", "啊", "和", "与", "或", "但", "不", "没", "有",
    })

    @staticmethod
    def _det_hash(token: str) -> int:
        """Deterministic hash (same across sessions)."""
        h = 5381
        for ch in token:
            h = ((h << 5) + h + ord(ch)) & 0xFFFFFFFF
        return h

    def _tokenize(self, text: str) -> list[str]:
        import re
        return re.findall(r'[a-zA-Z0-9]+|[一-鿿]', text.lower())

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.DIM
        for token in self._tokenize(text):
            weight = 0.2 if token in self._STOP else 1.0
            # Use 3 independent hash positions per token to reduce collisions
            for seed in (0, 1, 2):
                h = self._det_hash(token + str(seed)) % self.DIM
                vec[h] += weight
        norm = sum(v ** 2 for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


@pytest.fixture(scope="session")
def mock_embedding_provider() -> MockEmbeddingProvider:
    return MockEmbeddingProvider()


# ---------------------------------------------------------------------------
# Mock retriever — in-memory, deterministic
# ---------------------------------------------------------------------------

def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x ** 2 for x in a) ** 0.5
    nb = sum(x ** 2 for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


class MockRetriever:
    """In-memory retriever using hybrid scoring: keyword overlap + vector similarity.

    Keyword matching provides the primary signal (handles semantic relevance reliably),
    while vector similarity provides a secondary boost for ranking.
    """

    def __init__(self, kb: dict[str, Any], embedder: MockEmbeddingProvider):
        self._chunks: list[dict[str, Any]] = []
        self._embedder = embedder
        self._vectors: list[list[float]] = []

        for doc in kb["documents"]:
            for chunk in doc["chunks"]:
                record = {
                    "text": chunk["text"],
                    "doc_id": doc["doc_id"],
                    "chunk_index": chunk["chunk_index"],
                    "source_title": doc["source_title"],
                    "source_url": doc["source_url"],
                    "source_type": doc["source_type"],
                }
                self._chunks.append(record)
                self._vectors.append(embedder.embed(chunk["text"]))

    @staticmethod
    def _keyword_overlap(query: str, text: str) -> float:
        """Fraction of query tokens found in chunk text (case-insensitive).

        Handles both English words and Chinese characters/bigrams.
        """
        import re
        # English words (2+ chars)
        en_tokens = re.findall(r'[a-zA-Z]{2,}', query.lower())
        # Chinese characters as individual chars + bigrams
        zh_chars = re.findall(r'[一-鿿]', query)
        zh_bigrams = [zh_chars[i] + zh_chars[i + 1] for i in range(len(zh_chars) - 1)]
        q_tokens = set(en_tokens + zh_chars + zh_bigrams)
        if not q_tokens:
            return 0.0
        text_lower = text.lower()
        hits = sum(1 for t in q_tokens if t in text_lower)
        return hits / len(q_tokens)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        q_vec = self._embedder.embed(query)
        scored = []
        for i, c_vec in enumerate(self._vectors):
            vec_score = _cosine_sim(q_vec, c_vec)
            kw_score = self._keyword_overlap(query, self._chunks[i]["text"])
            # Hybrid: keyword 70% + vector 30%
            score = 0.7 * kw_score + 0.3 * vec_score
            if score >= threshold:
                entry = {**self._chunks[i], "score": round(score, 4)}
                scored.append(entry)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


@pytest.fixture(scope="session")
def mock_retriever(
    demo_knowledge_base: dict[str, Any],
    mock_embedding_provider: MockEmbeddingProvider,
) -> MockRetriever:
    return MockRetriever(demo_knowledge_base, mock_embedding_provider)


# ---------------------------------------------------------------------------
# Mock RAG pipeline — retriever + simple answer generator (no LLM)
# ---------------------------------------------------------------------------

class MockRAGPipeline:
    """End-to-end mock RAG: retrieve → build answer from context.

    Does NOT call any LLM.  Answer is synthesised from retrieved chunks
    so it is always faithful to the context (unless deliberately overridden).
    """

    NO_ANSWER_THRESHOLD = 0.30  # below this → no-answer

    def __init__(self, retriever: MockRetriever):
        self._retriever = retriever

    def query(
        self,
        question: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Return a RAG response dict.

        Returns:
            {
              "answer": str,
              "sources": [...],
              "confidence": "high" | "medium" | "low" | "none",
              "no_answer": bool,
              "retrieved_chunks": [...]
            }
        """
        chunks = self._retriever.retrieve(question, top_k=top_k, threshold=0.0)

        if not chunks or chunks[0]["score"] < self.NO_ANSWER_THRESHOLD:
            return {
                "answer": "I don't have enough information to answer this question.",
                "sources": [],
                "confidence": "none",
                "no_answer": True,
                "retrieved_chunks": chunks,
            }

        # Determine confidence
        top_score = chunks[0]["score"]
        if top_score >= 0.50:
            confidence = "high"
        elif top_score >= 0.30:
            confidence = "medium"
        else:
            confidence = "low"

        # Build answer from top chunks (faithful extraction)
        used_chunks = [c for c in chunks if c["score"] >= self.NO_ANSWER_THRESHOLD][:top_k]
        answer_parts = []
        for c in used_chunks:
            # Take first sentence as summary
            text = c["text"]
            first_sentence = text.split(". ")[0] if ". " in text else text[:200]
            answer_parts.append(first_sentence)

        answer = ". ".join(answer_parts)
        if not answer.endswith("."):
            answer += "."

        # Deduplicate sources
        seen_sources = set()
        sources = []
        for c in used_chunks:
            if c["doc_id"] not in seen_sources:
                seen_sources.add(c["doc_id"])
                sources.append({
                    "doc_id": c["doc_id"],
                    "source_title": c["source_title"],
                    "source_url": c["source_url"],
                    "source_type": c["source_type"],
                })

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "no_answer": False,
            "retrieved_chunks": used_chunks,
        }


@pytest.fixture(scope="session")
def mock_rag_pipeline(mock_retriever: MockRetriever) -> MockRAGPipeline:
    return MockRAGPipeline(mock_retriever)
