# VeloxSearch

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688?logo=fastapi&logoColor=white)
![Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Status](https://img.shields.io/badge/status-active%20development-orange)

Hybrid Search Service is a local-first search backend that combines lexical ranking (BM25) and semantic vector similarity (Sentence Transformers + HNSWLib).

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Why This Project Is Useful](#why-this-project-is-useful)
- [How To Get Started](#how-to-get-started)
- [Where To Get Help](#where-to-get-help)
- [Who Maintains And Contributes](#who-maintains-and-contributes)

## What This Project Does

This project provides:

- Dataset persistence on disk under `data/<dataset_id>/`
- Inverted indexing for BM25 retrieval
- HNSW vector indexing for semantic retrieval
- Hybrid ranking that merges lexical and vector scores
- A FastAPI app with Redis-backed async indexing progress over WebSocket

Primary components:

- [app/services/search_service.py](app/services/search_service.py): high-level indexing and search API
- [app/services/indexer.py](app/services/indexer.py): builds and loads inverted + vector indexes
- [app/main.py](app/main.py): FastAPI app entrypoint
- [app/routers/index.py](app/routers/index.py): `/index` routes and indexing-status WebSocket

## Why This Project Is Useful

- Improves relevance versus lexical-only retrieval by combining BM25 and embeddings
- Keeps data and indexes local (no mandatory external search service)
- Supports incremental updates via `add_documents(...)`
- Separates concerns cleanly across dataset, indexing, ranking, and API layers
- Includes tests for core behavior in [tests/services](tests/services) and [tests/database](tests/database)

## How To Get Started

### Prerequisites

- Python 3.12+
- Redis (for queue + progress pub/sub used by async indexing)

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Notes:

- The first vector operation downloads the `all-MiniLM-L6-v2` model.
- Tokenization setup may download NLTK resources on first use.

### 2. Build an index and run a search (Python API)

```python
from app.services.search_service import SearchService

documents = [
    {"id": "1", "title": "Apple iPhone 15", "description": "Latest Apple smartphone"},
    {"id": "2", "title": "Samsung Galaxy S24", "description": "Android flagship phone"},
    {"id": "3", "title": "Apple MacBook Pro", "description": "Powerful laptop for developers"},
]

service = SearchService(dataset_id="products", path="data/products")

service.dataset.config = {
    "searchable_fields": ["title", "description"],
    "vector_terms": ["title", "description"],
}

# Save dataset first, then build both indexes.
service.dataset.save_dataset(documents)
service.index()

results = service.search("apple laptop", top_k=3)
print(results["results"])  # matched documents
print(results["meta"])     # ranking metadata/scores
```

### 3. Reload persisted indexes in another process

```python
from app.services.search_service import SearchService

service = SearchService(dataset_id="products", path="data/products")
service.load()

results = service.search("android phone", top_k=3)
print(results)
```

### 4. Run the API server and async indexing worker

Start FastAPI:

```bash
uvicorn app.main:app --host localhost --port 8000 --reload
```

In a second terminal, start an RQ worker:

```bash
rq worker default
```

Indexing progress endpoint:

- HTTP: `GET /index/`
- WebSocket: `ws://localhost:8000/index/`

The WebSocket expects a JSON payload containing a dataset ID (for example: `{"id": "d123", "message": "start"}`), then streams progress updates published through Redis.

### 5. Initialize local metadata database

```bash
python scripts/init_db.py
```

### 6. Run tests

```bash
pytest -q tests/
```

Good starting test references:

- [tests/services/test_search_service.py](tests/services/test_search_service.py)
- [tests/services/test_indexer.py](tests/services/test_indexer.py)
- [tests/services/test_vector_search.py](tests/services/test_vector_search.py)
- [tests/database/test_database_manager.py](tests/database/test_database_manager.py)

### 7. Project structure

See [docs/project-structure.md](docs/project-structure.md).

## Where To Get Help

- Read implementation modules in [app/services](app/services) and [app/routers](app/routers)
- Use tests in [tests](tests) as executable usage examples
- Check schema definitions in [app/schemas](app/schemas) for metadata models
- Open an issue in this repository for bugs or feature requests

## Who Maintains And Contributes

### Maintainers

- Sai Sreenadh Chilukuri ([Portfolio](https://sreenadh.vercel.app/))

### Contributing

Contributions are welcome.

1. Create a feature branch.
2. Add or update tests in [tests](tests).
3. Run `pytest -q tests/` locally.
4. Open a pull request with a concise change summary.

<!-- If you add contributor docs later, link them here (for example, `CONTRIBUTING.md`). -->
