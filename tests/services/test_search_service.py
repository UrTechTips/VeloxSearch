import shutil
from pathlib import Path

import pytest

from app.services.search_service import SearchService


@pytest.fixture
def temp_search_service(tmp_path):
    """
    Creates a SearchService with an isolated temp directory.
    """
    dataset_id = "test_dataset"
    path = tmp_path / dataset_id

    service = SearchService(
        dataset_id=dataset_id,
        path=str(path)
    )
    service.dataset.config = {
        "searchable_fields": ["title", "description"],
        "vector_terms": ["title", "description"],
    }

    yield service

    # Cleanup (pytest tmp_path usually auto-cleans, but explicit is safer)
    if path.exists():
        shutil.rmtree(path)


@pytest.fixture
def sample_documents():
    return [
        {
            "id": "1",
            "title": "Apple iPhone 15",
            "description": "Latest Apple smartphone",
        },
        {
            "id": "2",
            "title": "Samsung Galaxy S24",
            "description": "Android flagship phone",
        },
        {
            "id": "3",
            "title": "Apple MacBook Pro",
            "description": "Powerful laptop for developers",
        },
    ]


def test_index_and_search(temp_search_service: SearchService, sample_documents):
    """
    Basic index + search sanity test.
    """
    service = temp_search_service

    service.index(sample_documents)
    service.load()

    results = service.search("Apple", top_k=2)

    assert service.inverted_index.get_average_doc_length() > 0
    assert isinstance(results["results"], list)
    assert len(results["results"]) > 0

    ids = {doc["id"] for doc in results["results"]}
    assert "1" in ids or "3" in ids


def test_persistence_load_and_search(tmp_path, sample_documents):
    """
    Ensure index survives restart (disk persistence).
    """
    dataset_id = "persist_dataset"
    path = tmp_path / dataset_id

    # First run: index
    service = SearchService(dataset_id=dataset_id, path=str(path))
    service.dataset.config = {
        "searchable_fields": ["title", "description"],
        "vector_terms": ["title", "description"],
    }
    service.index(sample_documents)

    # Simulate app restart
    del service

    # Second run: load
    service = SearchService(dataset_id=dataset_id, path=str(path))
    service.load()

    results = service.search("Galaxy", top_k=3)

    assert len(results["results"]) == 3
    assert results["results"][0]["id"] == "2"

def test_add_documents_updates_index(temp_search_service: SearchService, sample_documents):
    """
    Incremental document addition should be searchable.
    """
    service = temp_search_service
    service.index(sample_documents[:2])

    new_docs = [
        {
            "id": "99",
            "title": "Apple Watch Ultra",
            "description": "Smartwatch for fitness and outdoors",
        }
    ]

    service.add_documents(new_docs)

    results = service.search("Watch", top_k=5)
    print(results)
    ids = {doc["id"] for doc in results['results']}

    assert "99" in ids

def test_search_returns_documents_not_scores(temp_search_service, sample_documents):
    """
    SearchService should return raw documents, not internal ranking objects.
    """
    service = temp_search_service
    service.index(sample_documents)

    results = service.search("laptop", top_k=5)

    assert isinstance(results["results"], list)
    assert isinstance(results["results"][0], dict)
    assert "id" in results["results"][0]
    assert "title" in results["results"][0]


def test_empty_search_does_not_crash(temp_search_service, sample_documents):
    """
    Empty or unknown query should not crash.
    """
    service = temp_search_service
    service.index(sample_documents)

    results = service.search("nonexistentquery", top_k=5)

    assert isinstance(results["results"], list)
