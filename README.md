# VeloxSearch

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688?logo=fastapi&logoColor=white) ![Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)

VeloxSearch is a Python backend for building and serving hybrid search indexes. It combines BM25 lexical retrieval with SentenceTransformers embeddings and an HNSW vector index, then merges the signals into one ranked result set. Datasets and generated indexes are stored on disk, while Supabase stores application metadata and Redis coordinates indexing work, caching, and rate limiting.

## Contents

- [What the project does](#what-the-project-does)
- [Why it is useful](#why-it-is-useful)
- [Getting started](#getting-started)
- [Using the API](#using-the-api)
- [Project layout](#project-layout)
- [Where to get help](#where-to-get-help)
- [Maintainers and contributing](#maintainers-and-contributing)

## What the project does

VeloxSearch provides:

- JSON dataset storage in `data/<dataset_id>/`.
- Persistent inverted indexes for BM25 keyword search.
- Persistent HNSW indexes for semantic vector search.
- Hybrid ranking through the `SearchService`.
- Dataset creation, upload, configuration, parsing, listing, and deletion routes.
- JWT-protected user and dataset management.
- Dataset-scoped API keys for search clients.
- Redis-backed caching, token-bucket rate limiting, and RQ indexing jobs.
- A WebSocket that reports indexing progress.

The application is assembled in [app/main.py](app/main.py). Search orchestration lives in [app/services/search_service.py](app/services/search_service.py); dataset persistence is handled by [app/services/dataset.py](app/services/dataset.py); and index construction is handled by [app/services/indexer.py](app/services/indexer.py).

## Why it is useful

Hybrid retrieval handles both exact terms and meaning-based matches. BM25 is useful when a query contains an important product name, identifier, or phrase; vector retrieval helps when the query and document use different wording. The two indexes are persisted locally, so a loaded dataset can be searched without rebuilding its indexes after every restart.

The code is split into API routers, storage/database services, queue utilities, and search services. That separation makes it practical to run the API as a service while testing the ranking and indexing components independently.

## Getting started

### Prerequisites

- Python 3.12 or newer.
- A Supabase project with the application tables available.
- A Redis instance reachable through `REDIS_URL`.
- Enough disk space for the SentenceTransformers model and generated indexes.

### Install dependencies

From the repository root:

```powershell
py -3.12 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux, use `python3 -m venv .venv` and `source .venv/bin/activate` instead. The repository imports the `supabase` package, but it is not currently listed in `requirements.txt`; install it explicitly until the dependency manifest is updated:

```bash
python -m pip install supabase
```

### Configure the environment

Create a local `.env` file in the repository root. Do not commit it. Set the values for your own services:

```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
REDIS_URL=redis://localhost:6379/0
API_KEY_ENCRYPTION_KEY=your-fernet-key
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
API_KEY_SECRET=your-api-key-secret
POSTGRES=True
```

`SUPABASE_URL`, `SUPABASE_KEY`, `REDIS_URL`, and `API_KEY_ENCRYPTION_KEY` are required by the application path. `JWT_ALGORITHM` defaults to `HS256`; the Supabase JWT validation path also retrieves signing keys from the Supabase URL. Generate a Fernet-compatible encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The checked-in `.gitignore` excludes `.env`, local database files, API-key fixtures, and generated `data/*`. Keep credentials and generated indexes out of source control.

### Start the API and worker

Start Redis first, then run the API from the repository root:

```bash
uvicorn app.main:app --host localhost --port 8080 --reload
```

In a second terminal, activate the same virtual environment and start the RQ worker:

```bash
rq worker --worker-class rq.worker.SimpleWorker --url "$REDIS_URL" index_queue
```

On Windows, `start_worker.bat` reads `.env` and starts the worker. The application preloads the embedding model during startup, so the first launch may take longer and may download model files.

The API is available at `http://localhost:8080`. FastAPI's interactive documentation is available at `http://localhost:8080/docs` once the server is running.

### Run the tests

```bash
python -m pytest -q tests
```

The service-level tests cover tokenization, BM25, vector search, ranking, dataset persistence, and index persistence. API and rate-limit tests may require live Supabase/Redis services and their test fixtures.

> **Current setup note:** `scripts/init_db.py` and parts of the database test suite still contain SQLite-oriented code, while the runtime `DatabaseManager` uses Supabase. Treat Supabase table creation and schema setup as a deployment prerequisite; the initializer should be considered unfinished until that migration is completed.

## Using the API

The management routes use a Supabase JWT in the `Authorization` header. Search uses a dataset-scoped API key in the same header.

### Create and upload a dataset

```bash
curl -X POST "http://localhost:8080/dataset/create" \
  -H "Authorization: Bearer <supabase-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"database_name":"products","description":"Product catalog"}'
```

Use the returned `dataset_id` to upload a JSON array of documents:

```bash
curl -X POST "http://localhost:8080/dataset/upload" \
  -H "Authorization: Bearer <supabase-jwt>" \
  -F "id=<dataset-id>" \
  -F "file=@products.json;type=application/json"
```

Each document should have an identifier field. A typical `products.json` file is:

```json
[
  {"id": "p-001", "title": "Running shoes", "description": "Lightweight daily trainers"},
  {"id": "p-002", "title": "Trail backpack", "description": "Water-resistant hiking pack"}
]
```

### Configure and index

Upload a configuration describing the fields used for lexical and vector retrieval:

```bash
curl -X POST "http://localhost:8080/dataset/config" \
  -H "Authorization: Bearer <supabase-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"id":"<dataset-id>","config":"{\"searchable_fields\":[\"title\",\"description\"],\"vector_terms\":[\"title\",\"description\"],\"length\":2,\"id_field\":\"id\"}"}'
```

Open a WebSocket connection to `ws://localhost:8080/index/`, then send the following JSON message to queue indexing and receive progress events:

```json
{"token":"<supabase-jwt>","id":"<dataset-id>"}
```

The worker builds both indexes and publishes status messages through Redis. A dataset must be indexed before it can be searched.

### Generate an API key and search

Generate a key with a management JWT. The key is returned only from this operation, so store it securely:

```bash
curl -X POST "http://localhost:8080/apikey/generate?name=local-client&dataset_id=<dataset-id>" \
  -H "Authorization: Bearer <supabase-jwt>"
```

Then query the indexed dataset:

```bash
curl -X POST "http://localhost:8080/search/query?query=lightweight%20shoes&limit=5" \
  -H "Authorization: Bearer <api-key>"
```

The response contains the matching documents and ranking metadata. Search responses are cached in Redis for one hour. The global middleware advertises rate-limit headers, and API-key requests are also subject to the configured per-key rate and quota limits.

### Route summary

| Area | Routes | Authentication |
| --- | --- | --- |
| Users | `/users/register`, `/users/registered` | JWT |
| Datasets | `/dataset/create`, `/dataset/upload`, `/dataset/config`, `/dataset/parse/{id}`, `/dataset/list`, `/dataset/get/{id}`, `/dataset/delete/{id}` | JWT |
| API keys | `/apikey/generate`, `/apikey/deactivate`, `/apikey/list` | JWT |
| Indexing | `/index/` and the `/index/` WebSocket | JWT in WebSocket payload |
| Search | `/search/query` | Dataset API key |

Detailed request and response behavior is defined by the routers in [app/routers](app/routers) and can be explored through `/docs`.

## Project layout

```text
app/
  core/       Environment-backed application settings
  db/         Supabase database manager and metadata service
  routers/    FastAPI HTTP and WebSocket routes
  schemas/    User, dataset, API-key, usage, and feedback schemas
  services/   Dataset storage, BM25, vector search, ranking, and queues
  utils/      Authentication, hashing, rate limiting, and Redis helpers
data/         Local datasets and generated indexes (ignored by Git)
scripts/      Project utility scripts
tests/        API, database, service, and utility tests
```

For a module dependency overview, see [dependency_graph.mmd](dependency_graph.mmd).

## Where to get help

- Start with the interactive API documentation at `/docs` while the API is running.
- Read the route implementations in [app/routers](app/routers) for authentication and payload details.
- Read the focused tests in [tests](tests) for expected indexing and ranking behavior.
- Review [app/services](app/services) for the search pipeline and persisted file format.
- Use the repository issue tracker for reproducible bugs and setup questions.

Do not include credentials, `.env` contents, generated indexes, or private API keys in issues or pull requests.

## Maintainers and contributing

VeloxSearch is maintained by **Sai Sreenadh Chilukuri**.

Contributions are welcome. For a focused change:

1. Open an issue for a substantial feature or design change.
2. Make the smallest change that addresses the issue and add or update focused tests.
3. Run `python -m pytest -q tests` from the repository root.
4. Explain environment requirements and any Supabase or Redis behavior in the pull request.

Please keep secrets out of commits and avoid committing generated files under `data/`. A separate `CONTRIBUTING.md` can provide longer project-specific conventions when the contribution process grows.