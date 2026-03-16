import pytest
from app.db.database import DatabaseService
from app.db.manager import DatabaseManager
from app.schemas.user_schema import schema as user_schema

@pytest.fixture(scope="module")
def manager():
    db_manager = DatabaseManager("search_test.db")
    with db_manager as conn:
        cursor = conn.cursor()
        # Note: In a real test, we would want to use a more robust migration strategy rather than hardcoding the schema here.
        cursor.execute("""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                created_at TIMESTAMP,
                datasets_count INTEGER
            )
        """)
        # Create datasets table
        cursor.execute("""
            CREATE TABLE datasets (
                dataset_id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT,
                description TEXT,
                length INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()
    return db_manager

def test_database_initialization(manager: DatabaseManager):
    db_manager = manager
    db_service = DatabaseService(db_manager)
    assert db_service is not None

def test_insert_and_retrieve_dataset(manager: DatabaseManager):
    db_manager = manager
    db_service = DatabaseService(db_manager)
    
    # Insert a dataset
    dataset_id = "test_dataset"
    user_id = "test_user"
    metadata = {"name": "Test Dataset", "description": "A dataset for testing", "length": 100, "created_at": "2024-01-01 00:00:00", "updated_at": "2024-01-01 00:00:00"}
    
    insert_result = db_service.insert_dataset(dataset_id, user_id, **metadata)
    assert insert_result == True
    
    # Retrieve the dataset metadata
    retrieved_metadata = db_service.get_dataset_metadata(dataset_id)
    assert retrieved_metadata is not None
    assert retrieved_metadata['metadata'] == {"dataset_id": "test_dataset", "user_id": "test_user", "name": "Test Dataset", "description": "A dataset for testing", "length": 100, "created_at": "2024-01-01 00:00:00", "updated_at": "2024-01-01 00:00:00"}

def test_retrieve_nonexistent_dataset(manager: DatabaseManager):
    db_manager = manager
    db_service = DatabaseService(db_manager)
    
    # Attempt to retrieve metadata for a non-existent dataset
    retrieved_metadata = db_service.get_dataset_metadata("nonexistent_dataset")
    assert retrieved_metadata is None

def test_insert_duplicate_dataset(manager: DatabaseManager):
    db_manager = manager
    db_service = DatabaseService(db_manager)
    
    # Insert a dataset
    dataset_id = "testing_duplicate_dataset"
    user_id = "test_user"
    metadata = {"name": "Test Dataset", "description": "A dataset for testing", "length": 100, "created_at": "2024-01-01 00:00:00", "updated_at": "2024-01-01 00:00:00"}
    
    insert_result_1 = db_service.insert_dataset(dataset_id, user_id, **metadata)
    assert insert_result_1 == True
    
    # Attempt to insert the same dataset again
    insert_result_2 = db_service.insert_dataset(dataset_id, user_id, **metadata)
    assert insert_result_2 == False
    
def test_get_user_metadata(manager: DatabaseManager):
    db_manager = manager
    db_service = DatabaseService(db_manager)
    
    # Insert a user
    user_id = "test_user"
    metadata = {"name": "Test User", "email": "test@example.com", "created_at": "2024-01-01 00:00:00", "datasets_count": 0}
    
    insert_result = db_service.insert_user(user_id, **metadata)
    assert insert_result == True
    
    # Retrieve the user metadata
    retrieved_metadata = db_service.get_user_metadata(user_id)
    assert retrieved_metadata is not None
    assert retrieved_metadata["metadata"] == {"user_id": "test_user", "name": "Test User", "email": "test@example.com", "created_at": "2024-01-01 00:00:00", "datasets_count": 0}


def test_get_nonexistent_user_metadata(manager: DatabaseManager):
    db_manager = manager
    db_service = DatabaseService(db_manager)
    
    # Attempt to retrieve metadata for a non-existent user
    retrieved_metadata = db_service.get_user_metadata("nonexistent_user")
    assert retrieved_metadata is None

