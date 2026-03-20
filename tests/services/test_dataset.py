import pytest
import json
import os
import tempfile
import shutil
from app.services.dataset import Dataset

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mock_data_dir(monkeypatch, temp_dir):
    """Mock the data directory env var and working directory."""
    monkeypatch.chdir(temp_dir)
    
    # Define a clean root for data
    data_dir = os.path.join(temp_dir, "data")
    monkeypatch.setenv("DATA_DIR", data_dir)
    return temp_dir

@pytest.fixture
def sample_dataset(mock_data_dir):
    """Create a sample dataset for testing with a defined path."""
    # We construct a specific path so we know exactly where files should appear
    dataset_path = os.path.join(mock_data_dir, "data", "test_dataset")
    
    return Dataset(
        dataset_id="test_dataset",
        config={
            "searchable_fields": ["title", "content"],
            "vector_terms": ["term1", "term2", "term3"]
        },
        path=dataset_path
    )

@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return [
        {"id": 1, "title": "First Document", "content": "This is the first document"},
        {"id": 2, "title": "Second Document", "content": "This is the second document"},
        {"id": 3, "title": "Third Document", "content": "This is the third document"}
    ]

# --- Tests for __init__ ---
def test_dataset_init_with_config(sample_dataset):
    assert sample_dataset.dataset_id == "test_dataset"
    assert sample_dataset.config["searchable_fields"] == ["title", "content"]

def test_dataset_init_without_config():
    dataset = Dataset(dataset_id="empty_dataset")
    assert dataset.dataset_id == "empty_dataset"
    assert dataset.config is None

# --- Tests for save_dataset ---
def test_save_dataset_writes_files_correctly(sample_dataset: Dataset, sample_data):
    """Verifies that dataset.json and config.json are created with correct content."""
    
    # 1. Action: Save the dataset
    sample_dataset.save_dataset(sample_data)
    
    # 2. Setup paths for verification
    # Note: We use the path defined in the sample_dataset fixture
    base_path = sample_dataset.path 
    dataset_file = os.path.join(base_path, "dataset.json")
    config_file = os.path.join(base_path, "config.json")

    # 3. Verify Files Exist
    assert os.path.exists(dataset_file)
    assert os.path.exists(config_file)
    
    # 4. Verify Content
    with open(dataset_file, "r") as f:
        assert json.load(f) == sample_data
        
    with open(config_file, "r") as f:
        assert json.load(f) == sample_dataset.config

def test_save_dataset_empty_data(sample_dataset: Dataset):
    sample_dataset.save_dataset([])
    path = os.path.join(sample_dataset.path, "dataset.json")
    
    with open(path, "r") as f:
        assert json.load(f) == []

# --- Tests for load_dataset ---
def test_load_dataset_returns_data(sample_dataset: Dataset, sample_data):
    sample_dataset.save_dataset(sample_data)
    loaded_data = sample_dataset.load_dataset()
    assert loaded_data == sample_data

def test_load_dataset_updates_config(mock_data_dir):
    """Test that loading a dataset also loads its config from disk."""
    config = {"searchable_fields": ["field1"], "vector_terms": ["v1"]}
    shared_path = os.path.join(mock_data_dir, "shared_test_path")

    # 1. Setup: Create files using a temporary instance at a known path
    ds_writer = Dataset(dataset_id="test_dataset", config=config, path=shared_path)
    ds_writer.save_dataset([{"id": 1}])
    
    # 2. Action: Load using a fresh instance pointing to the SAME path
    # We must provide the path or ensure env vars resolve to this exact path
    ds_reader = Dataset(dataset_id="test_dataset", path=shared_path)
    ds_reader.load_dataset()
    
    # 3. Assertion
    assert ds_reader.config == config

def test_load_dataset_file_not_found(sample_dataset):
    # Ensure directory is clean
    if os.path.exists(sample_dataset.path):
        shutil.rmtree(sample_dataset.path)
        
    with pytest.raises(FileNotFoundError):
        sample_dataset.load_dataset()

# --- Tests for add_document ---
def test_add_document_appends_to_disk(sample_dataset: Dataset, sample_data):
    sample_dataset.save_dataset(sample_data)
    
    new_doc = {"id": 4, "title": "Fourth Document"}
    sample_dataset.add_document(new_doc)
    
    path = os.path.join(sample_dataset.path, "dataset.json")
    with open(path, "r") as f:
        data = json.load(f)
    
    assert len(data) == 4
    assert data[-1] == new_doc

def test_add_document_to_new_dataset(sample_dataset: Dataset):
    # Initialize empty file
    sample_dataset.save_dataset([]) 
    
    doc = {"id": 1, "title": "First"}
    sample_dataset.add_document(doc)
    
    path = os.path.join(sample_dataset.path, "dataset.json")
    with open(path, "r") as f:
        assert json.load(f)[0] == doc

# --- Tests for Getters ---
def test_get_searchable_fields(sample_dataset):
    assert sample_dataset.get_searchable_fields() == ["title", "content"]
    
    # Test empty config logic
    sample_dataset.config = {}
    assert sample_dataset.get_searchable_fields() == []
    
    sample_dataset.config = None
    assert sample_dataset.get_searchable_fields() == []

def test_get_vector_terms(sample_dataset):
    assert sample_dataset.get_vector_terms() == ["term1", "term2", "term3"]
    
    # Test empty config logic
    sample_dataset.config = {}
    assert sample_dataset.get_vector_terms() == []

def test_get_documents_logic(sample_dataset, sample_data):
    # Test retrieval
    sample_dataset.save_dataset(sample_data)
    assert len(sample_dataset.get_documents()) == 3
    
    # Test updates are reflected
    sample_dataset.add_document({"id": 4})
    assert len(sample_dataset.get_documents()) == 4

# --- Integration ---
def test_full_workflow(mock_data_dir):
    """End-to-end test."""
    workflow_path = os.path.join(mock_data_dir, "workflow_data")
    
    # 1. Init
    dataset = Dataset(dataset_id="workflow", config={"fields": ["a"]}, path=workflow_path)
    
    # 2. Save
    dataset.save_dataset([{"id": 1}])
    
    # 3. Add
    dataset.add_document({"id": 2})
    
    # 4. Load & Verify
    loaded = dataset.load_dataset()
    assert len(loaded) == 2
    assert loaded[1]["id"] == 2