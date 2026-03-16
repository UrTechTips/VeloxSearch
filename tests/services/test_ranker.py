import pytest
from app.services.ranker import Ranker


class MockBM25:
    def search(self, query_tokens, top_k):
        return [
            {"id": "doc1", "score": 0.9},
            {"id": "doc2", "score": 0.6},
        ]


class MockVectorSearch:
    def search(self, query, top_k):
        return [
            {"id": "doc2", "vector_score": 0.8},
            {"id": "doc3", "vector_score": 0.7},
        ]


def test_hybrid_merge():
    ranker = Ranker("ds", MockBM25(), MockVectorSearch())
    results = ranker.rank("query", k=3)

    doc_ids = [r["id"] for r in results]
    assert set(doc_ids) == {"doc1", "doc2", "doc3"}


def test_vector_only():
    class EmptyBM25:
        def search(self, query_tokens, top_k):
            return []

    ranker = Ranker("ds", EmptyBM25(), MockVectorSearch())
    results = ranker.rank("query", k=2)

    assert [r["id"] for r in results] == ["doc2", "doc3"]


def test_bm25_only():
    class EmptyVector:
        def search(self, query, top_k):
            return []

    ranker = Ranker("ds", MockBM25(), EmptyVector())
    results = ranker.rank("query", k=2)

    assert [r["id"] for r in results] == ["doc1", "doc2"]


def test_top_k_limit():
    ranker = Ranker("ds", MockBM25(), MockVectorSearch())
    results = ranker.rank("query", k=1)

    assert len(results) == 1
