from app.services.bm25 import BM25
from app.services.inverted_index import InvertedIndex

# ---- Mock Inverted Index ---- #

class MockIndex(InvertedIndex):
    def __init__(self):
        # Fake small dataset
        self.docs = {
            "1": {"text": "apple banana apple"},
            "2": {"text": "banana orange"},
            "3": {"text": "apple fruit salad"}
        }

        # Token → {doc_id: tf}
        self.postings = {
            "apple": {"1": 2, "3": 1},
            "banana": {"1": 1, "2": 1},
            "orange": {"2": 1},
            "fruit": {"3": 1},
            "salad": {"3": 1},
        }

        self.doc_lengths = {
            "1": 3,
            "2": 2,
            "3": 3
        }

    def get_total_docs(self):
        return len(self.doc_lengths)

    def get_index(self):
        return self.postings

    def get_doc_length(self, doc_id):
        return self.doc_lengths[doc_id]

    def get_doc_lengths(self):
        return self.doc_lengths

    def get_average_doc_length(self):
        return sum(self.doc_lengths.values()) / len(self.doc_lengths)

    def get_term_frequencies(self, token):
        return self.postings.get(token, {})

# ---- Tests ---- #

def test_idf_computation():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    idf_apple = bm25._compute_idf("apple")
    idf_banana = bm25._compute_idf("banana")
    idf_unknown = bm25._compute_idf("nonexistent")

    assert idf_apple > 0      # appears in 2/3 docs
    assert idf_banana > 0
    assert idf_unknown > idf_apple  # rare word gets highest IDF


def test_tf_computation():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    tf = bm25._compute_tf(term_freq=2, doc_length=3, avg_doc_length=index.get_average_doc_length())
    assert tf > 0
    assert tf <= 1


def test_bm25_single_token():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    results = bm25.compute_bm25(["apple"])

    # Document 1 has apple twice → highest score
    print(results)
    assert results[0]["id"] == "1"
    assert results[0]["score"] >= results[1]["score"]


def test_bm25_multi_token_query():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    results = bm25.compute_bm25(["apple", "banana"])

    # Doc 1 contains both apple & banana → highest
    assert results[0]["id"] == "1"


def test_normalization_range():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    results = bm25.compute_bm25(["apple"])

    for r in results:
        assert 0.0 <= r["score"] <= 1.0

def test_empty_query():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    results = bm25.compute_bm25([])

    for r in results:
        assert r["score"] == 0.0

def test_nonexistent_token_query():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    results = bm25.compute_bm25(["nonexistent"])

    for r in results:
        assert r["score"] == 0.0
        
def test_mixed_query():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    results = bm25.compute_bm25(["apple", "nonexistent"])

    # Documents with "apple" should have non-zero scores
    for r in results:
        if r["id"] in ["1", "3"]:
            assert r["score"] > 0.0
        else:
            assert r["score"] == 0.0

def test_search_top_k():
    index = MockIndex()
    bm25 = BM25(k=1.2, b=0.75, index=index)

    results = bm25.compute_bm25(["apple"])

    top_k = 2
    top_results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    assert len(top_results) == top_k