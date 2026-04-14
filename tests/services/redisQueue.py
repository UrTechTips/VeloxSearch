import pytest
import time
from app.services.redisQueue import IndexQueue

# 1. Define a standard function instead of a fixture
def dummy_processing_func(data): 
    print(f"Processing {data}")
    return f"Processed {data}"

@pytest.fixture
def index_queue():
    """Fixture to create an instance of IndexQueue for testing."""
    # Pass the actual function object
    queue = IndexQueue(func=dummy_processing_func)
    yield queue
    # Ensure clear() handles Redis connection cleanup if necessary
    queue.clear() 

def test_initialization(index_queue):
    """Test that the IndexQueue is initialized correctly."""
    # Compare against the function object directly
    assert index_queue.function == dummy_processing_func
    assert len(index_queue) == 0

def test_offer(index_queue):
    """Test that offering a dataset ID returns a job ID and increments length."""
    job_id = index_queue.offer("dataset_1")
    assert job_id is not None
    assert len(index_queue) == 1

def test_clear(index_queue):
    """Test that clearing the queue removes all jobs."""
    index_queue.offer("dataset_1")
    index_queue.offer("dataset_2")
    assert len(index_queue) == 2
    index_queue.clear()
    assert len(index_queue) == 0

# def test_offer_executes_function(index_queue, capsys):
#     job_id = index_queue.offer("dataset_1")
    
#     captured = capsys.readouterr()
#     assert "Processing dataset_1" in captured.out