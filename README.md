# VeloxSearch

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688?logo=fastapi&logoColor=white) ![Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)

VeloxSearch is a local-first hybrid search backend that combines BM25 lexical ranking with semantic vector search (SentenceTransformers + HNSWLib). It stores datasets and indexes on disk, exposes FastAPI routes for dataset and API-key management, and streams indexing progress via Redis-backed WebSockets.

Frontend for VeloxSearch can be found at [Github](https://github.com/UrTechTips/VeloxSearchFrontend)

## Table of Contents

- [What the project does](#what-the-project-does)
- [Why it is useful](#why-it-is-useful)
- [Quickstart](#quickstart)
- [Developer usage & examples](#developer-usage--examples)
- [Where to get help](#where-to-get-help)
- [Maintainers & contributing](#maintainers--contributing)

## What the project does

- Stores datasets under `data/<dataset_id>/` and persists indexes to disk.
- Builds an inverted index (BM25) and an HNSW vector index for semantic retrieval.
- Provides a hybrid ranker that merges BM25 and vector scores.
- Offers HTTP endpoints and WebSocket channels for indexing and search.
- Uses Redis + RQ for background indexing and progress notifications.
- Includes rate limiting (token-bucket) and API key / JWT protection for routes.

Key code locations:

- Application startup and routing: [app/main.py](app/main.py)
- High-level search API: [app/services/search_service.py](app/services/search_service.py)
- Index builder & loader: [app/services/indexer.py](app/services/indexer.py)
- HTTP routers: [app/routers](app/routers)
- Utilities and queueing: [app/utils](app/utils)

## Why it is useful

- Combines lexical and semantic retrieval to improve relevance.
- Runs fully locally — no external search service required.
- Supports incremental indexing and persisted indexes for faster restarts.
- Modular design: dataset management, indexing, ranking, and API layers are separated for easy extension.

## Quickstart

Prerequisites

- Python 3.12+
- Redis running at `localhost:6379`

Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Environment

Create a `.env` file or export these variables:

```bash
export JWT_SECRET="replace-me"
export JWT_ALGORITHM="HS256"
export API_KEY_SECRET="replace-me-too"
```

Initialize local DB (creates metadata for datasets, users, API keys):

```bash
python scripts/init_db.py
```

Run services

```bash
# start Redis in one terminal
redis-server

# start the API server
uvicorn app.main:app --host localhost --port 8000 --reload

# start the indexing worker in a third terminal
rq worker index_queue
```

Run tests

```bash
pytest -q tests/
```

## Developer usage & examples

Use the Python classes directly for experiments and scripting:

```python
from app.services.search_service import SearchService

docs = [
  {"id":"1","title":"Apple iPhone","description":"Smartphone"},
]

svc = SearchService(dataset_id="products", path="data/products")
svc.dataset.config = {"searchable_fields":["title","description"], "vector_terms":["title","description"]}
svc.dataset.save_dataset(docs)
svc.index()
print(svc.search("apple phone", top_k=5))
```

HTTP endpoints (protected): `/dataset`, `/index`, `/apikey`, `/search`.

Example curl (replace tokens):

```bash
curl -X POST "http://localhost:8000/apikey/generate?dataset_id=products" -H "Authorization: Bearer <jwt-token>"
curl -X POST "http://localhost:8000/search/query?query=apple%20laptop" -H "Authorization: Bearer <api-key>"
```

Indexing progress is streamed from the `/index/` WebSocket; the worker publishes progress via Redis channels.

## Where to get help

- Inspect the implementation in [app/services](app/services) and [app/routers](app/routers).
- Run and read the tests in [tests](tests) for concrete examples of expected behavior.
- See [dependency_graph.mmd](dependency_graph.mmd) for a module overview.
- Open an issue or PR on the repository for questions and bug reports.

## Maintainers & contributing

Maintainer: Sai Sreenadh Chilukuri

Contributions welcome — prefer small, focused PRs with tests. Before opening a PR:

- Run `pytest -q tests/` and ensure new tests pass.
- Keep changes scoped and document behavior in code or tests.

If you want to contribute a larger design or feature, open an issue first to discuss the approach.
