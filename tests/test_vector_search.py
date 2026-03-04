import os
import shutil
import tempfile
import pytest

from app.services.vector_search import VectorSearch
from app.services.dataset import Dataset

class MockDataset(Dataset):
    def __init__(self):
        self.dataset_id = "mock_dataset"
        self.documents = [
        {
            "id": "1",
            "title": "Nike running shoes",
            "description": "Lightweight sneakers for daily runs"
        },
        {
            "id": "2",
            "title": "Adidas football boots",
            "description": "Studded shoes for firm ground"
        },
        {
            "id": "3",
            "title": "Puma casual sneakers",
            "description": "Comfortable everyday footwear"
        }
    ]

    def get_documents(self):
        return self.documents
    
    def get_document(self, document_id):
        return next((doc for doc in self.documents if doc["id"] == document_id), None)
    
    def get_searchable_fields(self):
        return ["content"]
    
    def get_dataset_id(self):
        return "mock_dataset"


@pytest.fixture(scope="module")
def vector_terms():
    return ["title", "description"]


@pytest.fixture(scope="module")
def vector_search(vector_terms):
    dataset = MockDataset()
    vs = VectorSearch(
        dataset=dataset,
        vector_terms=vector_terms
    )
    vs.build_index()
    return vs

def test_index_build(vector_search):
    assert vector_search.index.get_current_count() == 3


def test_search_returns_results(vector_search):
    results = vector_search.search("running sneakers", top_k=2)

    assert len(results) == 2
    assert "id" in results[0]
    assert "vector_score" in results[0]
    assert isinstance(results[0]["vector_score"], float)


def test_semantic_similarity(vector_search):
    results = vector_search.search("sneakers", top_k=1)

    assert results[0]["id"] in {"1", "3"}


def test_add_document(vector_search):
    vector_search.add_document(
        doc_id="4",
        document={
            "title": "Reebok training shoes",
            "description": "Gym and cross-training footwear"
        }
    )

    results = vector_search.search("training shoes", top_k=5)
    doc_ids = [r["id"] for r in results]

    assert "4" in doc_ids
    assert vector_search.index.get_current_count() == 4


def test_save_and_load_index(vector_terms):
    tmp_dir = tempfile.mkdtemp()
    dataset = MockDataset()

    try:
        vs = VectorSearch(
            dataset=dataset,
            vector_terms=vector_terms,
            path=tmp_dir
        )
        vs.build_index()

        assert vs.save_index()
        vs_loaded = VectorSearch(
            dataset=dataset,
            vector_terms=vector_terms,
            path=tmp_dir
        )

        assert vs_loaded.load_index()

        results = vs_loaded.search("casual sneakers", top_k=1)
        assert results[0]["id"] == "3"

    finally:
        shutil.rmtree(tmp_dir)


def test_vector_scores_range(vector_search):
    results = vector_search.search("shoes", top_k=3)

    for r in results:
        assert 0.0 <= r["vector_score"] <= 1.0

def test_empty_query_does_not_crash(vector_search: VectorSearch):
    results = vector_search.search("", top_k=3)
    assert isinstance(results, list)

def test_clear_index(vector_search: VectorSearch):
    initial_count = vector_search.index.get_current_count()
    vector_search.clear_index()
    vector_search.dataset.documents = [
        {
            "id": "1",
            "title": "Nike running shoes",
            "description": "Lightweight sneakers for daily runs"
        }
    ]
    vector_search.build_index()
    assert vector_search.index.get_current_count() == 1
    assert vector_search.index.get_current_count() < initial_count
