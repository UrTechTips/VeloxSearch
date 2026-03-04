# Hybrid Search Engine (BM25 + Vector Search)

![Python](https://img.shields.io/badge/python-3.12+-blue)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![License](https://img.shields.io/badge/license-not%20specified-lightgrey)

A lightweight Python search engine that combines lexical relevance (BM25) with semantic similarity (SentenceTransformers + HNSW) to return better ranked results.

## What this project does

This project provides a hybrid retrieval pipeline over document datasets:

- Stores documents and dataset config on disk
- Builds an inverted index for lexical search
- Builds a vector index for semantic search
- Combines BM25 and vector scores in a ranker
- Returns ranked documents through `SearchService`

Core implementation lives in [app/services](app/services), with behavior covered by tests in [tests](tests).

## Why this project is useful

- **Better ranking quality**: combines keyword matching and semantic similarity
- **Simple local persistence**: indexes and datasets are stored in `data/<dataset_id>/...`
- **Modular design**: dataset, indexing, ranking, and search are separated into focused services
- **Fast retrieval**: HNSW index (`hnswlib`) enables efficient vector nearest-neighbor lookup
- **Tested components**: unit/integration-style tests for tokenizer, dataset, indexer, ranker, BM25, and vector search

## How to get started

### 1) Set up Python environment

From the repository root:

```bash
python3 -m venv .env
source .env/bin/activate
pip install --upgrade pip
pip install pytest nltk sentence-transformers hnswlib
```

Notes:
- `SentenceTransformer("all-MiniLM-L6-v2")` downloads model files on first run.
- `nltk` tokenizer resources are downloaded when `app/services/tokenizer.py` is imported.

### 2) Index and search documents (minimal example)

```python
from app.services.search_service import SearchService

documents = [
    {"id": "1", "title": "Apple iPhone 15", "description": "Latest Apple smartphone"},
    {"id": "2", "title": "Samsung Galaxy S24", "description": "Android flagship phone"},
    {"id": "3", "title": "Apple MacBook Pro", "description": "Powerful laptop for developers"},
]

service = SearchService(dataset_id="products", path="data/products")

# Required config fields for indexing/ranking
service.dataset.config = {
    "searchable_fields": ["title", "description"],
    "vector_terms": ["title", "description"],
}

service.index(documents)
results = service.search("Apple laptop", top_k=3)

print(results["results"])  # matched documents
print(results["meta"])     # scoring metadata (bm25/vector/combined)
```

### 3) Run tests

```bash
pytest -q tests/
```

Useful test entry points:
- [tests/test_search_service.py](tests/test_search_service.py)
- [tests/test_vector_search.py](tests/test_vector_search.py)
- [tests/test_bm25.py](tests/test_bm25.py)

### 4) Project layout

- [app/services](app/services): dataset, tokenizer, indexing, ranking, and search pipeline
- [app/api/v1](app/api/v1): API route module placeholders
- [data](data): persisted datasets and indexes
- [tests](tests): test suite

## Where users can get help

- Start with the tests in [tests](tests) to see expected usage patterns.
- Review service code in [app/services](app/services) for extension points.
- For issues in your copy/fork, open an issue or discussion in your repository.

## Who maintains and contributes

### Maintainers

Maintainer metadata is not declared in this workspace yet (no repository metadata file was found). Add maintainers here once available.

### Contributing

Contributions are welcome.

Recommended workflow:

1. Create a feature branch
2. Add or update tests in [tests](tests)
3. Run `pytest -q tests/`
4. Open a pull request with a clear summary of behavior changes

If you add contribution policy files, prefer linking them here (for example, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`).
