# Project Structure

```text
.
|-- .github/
|   `-- prompts/
|       |-- create-readme.prompt.md
|       `-- document-api.prompt.md
|-- .gitignore
|-- README.md
|-- activate.bat
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
|   |   |-- datasets_schema.py
|   |   `-- user_schema.py
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
|   `-- project-structure.md
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