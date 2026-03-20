# Hybrid Search Engine (BM25 + Vector)

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Status](https://img.shields.io/badge/status-active%20development-orange)

A local-first hybrid retrieval engine that combines lexical relevance (BM25) and semantic similarity (Sentence Transformers + HNSW) to return high-quality ranked results.

## What This Project Does

This project provides a document search pipeline you can embed in Python applications:

- Persists datasets to disk
- Builds an inverted index for lexical retrieval
- Builds an HNSW vector index for semantic retrieval
- Merges both signals with weighted hybrid ranking
- Returns ranked documents plus score metadata

The main integration entry point is `SearchService` in [app/services/search_service.py](app/services/search_service.py).

## Why This Project Is Useful

- Better relevance than lexical-only search: hybrid BM25 + vector scoring
- Local persistence: indexes and data are stored under `data/<dataset_id>/...`
- Clean architecture: dataset, indexing, ranking, and retrieval are modular services
- Incremental updates: add new documents and refresh indexes via service methods
- Good test coverage for the core pipeline in [tests/services](tests/services)

## How To Get Started

### 1. Install dependencies

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Notes:

- The first vector operation downloads `all-MiniLM-L6-v2` model assets.
- Tokenization uses NLTK and downloads `punkt_tab` during tokenizer import.

### 2. Index and search documents

```python
from app.services.search_service import SearchService

documents = [
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

service = SearchService(dataset_id="products", path="data/products")

# Required for indexing and ranking.
service.dataset.config = {
    "searchable_fields": ["title", "description"],
    "vector_terms": ["title", "description"],
}

service.index(documents)

results = service.search("apple laptop", top_k=3)
print(results["results"])  # ranked documents
print(results["meta"])     # bm25/vector/combined scores
```

### 3. Load persisted indexes in a new process

```python
from app.services.search_service import SearchService

service = SearchService(dataset_id="products", path="data/products")
service.load()

results = service.search("android phone", top_k=3)
print(results)
```

### 4. Run the test suite

```bash
pytest -q tests/
```

Useful test files:

- [tests/services/test_search_service.py](tests/services/test_search_service.py)
- [tests/services/test_vector_search.py](tests/services/test_vector_search.py)
- [tests/services/test_ranker.py](tests/services/test_ranker.py)

### 5. Project layout

```text
.
|-- .gitignore
|-- README.md
|-- app/
|   |-- api/
|   |   `-- v1/
|   |       |-- apikeys.py
|   |       |-- datasets.py
|   |       `-- search.py
|   |-- core/
|   |-- db/
|   |   |-- database.py
|   |   `-- manager.py
|   |-- main.py
|   |-- models/
|   |-- schemas/
|   |   |-- apikeys_schema.py
|   |   |-- datasets_schema.py
|   |   |-- feedback_schema.py
|   |   |-- usage_schema.py
|   `-- services/
|       |-- bm25.py
|       |-- dataset.py
|       |-- indexer.py
|       |-- inverted_index.py
|       |-- ranker.py
|       |-- search_service.py
|       |-- tokenizer.py
|       `-- vector_search.py
|-- data/
|   |-- docs/
|   |-- mock_dataset/
|   |   `-- vector/
|   |       |-- id_map.json
|   |       `-- vector_index.bin
|   `-- test_dataset/
|       |-- inverted/
|       `-- vector/
|           |-- id_map.json
|           `-- vector_index.bin
|-- docs/
|-- requirements.txt
|-- scripts/
|-- search_test.db
`-- tests/
    |-- database/
    |   |-- test_database_manager.py
    |   `-- test_db.py
    `-- services/
        |-- test_bm25.py
        |-- test_dataset.py
        |-- test_indexer.py
        |-- test_inverted_index.py
        |-- test_ranker.py
        |-- test_search_service.py
        |-- test_tokenizer.py
        `-- test_vector_search.py
```

This tree excludes local environment and cache directories such as `.env/` and `__pycache__/`.

## Where To Get Help

- Read the service tests in [tests/services](tests/services) for real usage patterns.
- Inspect core implementations in [app/services](app/services).
- Use repository issues/discussions in your host platform for bug reports and questions.

## Who Maintains And Contributes

### Maintainers

Maintainer information is not yet declared in repository metadata. Add maintainers in this section when available.

### Contributing

Contributions are welcome. A lightweight workflow:

1. Create a feature branch.
2. Add or update tests in [tests](tests).
3. Run `pytest -q tests/` locally.
4. Open a pull request with behavior changes and test evidence.

If you later add a contributor guide, link it here (for example `CONTRIBUTING.md`).
