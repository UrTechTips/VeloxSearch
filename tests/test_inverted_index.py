import os
import json
from app.services.inverted_index import InvertedIndex
from app.services.dataset import Dataset

# Mock Dataset

class MockDataset(Dataset):
    def __init__(self):
        self.dataset_id = "mock_dataset"
        self.documents = [
            {"id": 1, "content": "the quick brown fox jumps over the lazy dog", "searchable_fields": ["content"]},
            {"id": 2, "content": "the quick fox", "searchable_fields": ["content"]}
        ]

    def get_documents(self):
        return self.documents
    
    def get_document(self, document_id):
        return next((doc for doc in self.documents if doc["id"] == document_id), None)
    
    def get_searchable_fields(self):
        return ["content"]
    
    def get_dataset_id(self):
        return "mock_dataset"
    


def test_basic_inverted_index():
    dataset = MockDataset()
    idx = InvertedIndex(dataset)
    # idx.build_index(docs)
    idx.build_index()
    inv = idx.get_index()
    print(inv)

    assert inv["quick"] == {'1': 1, '2': 1}
    assert inv["fox"] == {'1': 1, '2': 1}

def test_no_duplicate_entries():
    dataset = MockDataset()
    idx = InvertedIndex(dataset)
    doc = {
        "id": 1,
        "content": "apple apple apple banana",
        "searchable_fields": ["content"]
    }
    idx.add_document(doc)

    inv = idx.get_index()
    print(inv)

    assert inv["appl"] == {'1': 3}
    assert inv["banana"] == {'1': 1}

def test_tf_counts_across_documents():
    dataset = MockDataset()
    idx = InvertedIndex(dataset)
    doc1 = {
        "id": 1,
        "content": "red red blue",
        "searchable_fields": ["content"]
    }
    doc2 = {
        "id": 2,
        "content": "red green green green",
        "searchable_fields": ["content"]
    }
    idx.add_document(doc1)
    idx.add_document(doc2)

    inv = idx.get_index()

    assert inv["red"] == {'1': 2, '2': 1}
    assert inv["green"] == {'2': 3}
    assert inv["blue"] == {'1': 1}

def test_edge_cases():
    dataset = MockDataset()
    idx = InvertedIndex(dataset)

    doc1 = {
        "id": 1,
        "content": "",
        "searchable_fields": ["content"]
    }
    doc2 = {
        "id": 2,
        "content": "one",
        "searchable_fields": ["content"]
    }
    idx.add_document(doc1)
    idx.add_document(doc2)

    inv = idx.get_index()

    assert inv == {"one": {'2': 1}}

def test_index_is_sorted_by_doc_id():
    dataset = MockDataset()
    idx = InvertedIndex(dataset)

    doc1 = {
        "id": 5,
        "content": "x",
        "searchable_fields": ["content"]
    }
    doc2 = {
        "id": 1,
        "content": "x",
        "searchable_fields": ["content"]
    }
    doc3 = {
        "id": 3,
        "content": "x",
        "searchable_fields": ["content"]
    }
    idx.add_document(doc1)
    idx.add_document(doc2)
    idx.add_document(doc3)

    inv = idx.get_index()

    assert inv["x"] == {
        '1': 1,
        '3': 1,
        '5': 1
    }

def test_dataset_save():
    docs = [
        {"id": 1, "content": "hello world", "searchable_fields": ["content"]},
        {"id": 2, "content": "goodbye world", "searchable_fields": ["content"]}
    ]
    dataset_id = "test_dataset"

    dataset = MockDataset()
    dataset.documents = docs
    dataset.dataset_id = dataset_id

    idx = InvertedIndex(dataset)
    idx.build_index()
    print(idx.save_index())

    # Check if file is created and content is correct
    assert os.path.exists(f"data/{dataset_id}/inverted/inverted_index.json")
    assert os.path.exists(f"data/{dataset_id}/inverted/doc_lengths.json")
    with open(f"data/{dataset_id}/inverted/inverted_index.json", "r") as f:
        data = json.load(f)
        assert data["world"] == {'1': 1, '2': 1}
    with open(f"data/{dataset_id}/inverted/doc_lengths.json", "r") as f:
        data = json.load(f)
        assert data["doc_lengths"] == {'1': 2, '2': 2}
    os.remove(f"data/{dataset_id}/inverted/inverted_index.json")
    os.remove(f"data/{dataset_id}/inverted/doc_lengths.json")

def test_doc_open():
    docs = [
        {"id": 1, "content": "alpha beta gamma", "searchable_fields": ["content"]},
        {"id": 2, "content": "beta delta epsilon", "searchable_fields": ["content"]}
    ]
    dataset = MockDataset()
    dataset.documents = docs

    idx = InvertedIndex(dataset)
    idx.build_index()
    idx.save_index()

    # Test open
    idx2 = InvertedIndex(dataset)
    idx2.open_index()
    inv = idx2.get_index()
    print(inv)

    assert inv["beta"] == {'1': 1, '2': 1}
    os.remove(f"data/{dataset.dataset_id}/inverted/inverted_index.json")
    os.remove(f"data/{dataset.dataset_id}/inverted/doc_lengths.json")

def test_clear_index():
    docs = [
        {"id": 1, "content": "one two three", "searchable_fields": ["content"]},
        {"id": 2, "content": "two three four", "searchable_fields": ["content"]}
    ]
    dataset = MockDataset()
    dataset.documents = docs

    idx = InvertedIndex(dataset)
    idx.build_index()
    inv_before = idx.get_index()
    print("Before clear:", inv_before)

    idx.clear_index()
    inv_after = idx.get_index()
    print("After clear:", inv_after)

    assert inv_before != {}
    assert inv_after == {}