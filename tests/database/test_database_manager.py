from app.db.manager import DatabaseManager

def test_connection():
    db_manager = DatabaseManager(":memory:")
    with db_manager as conn:
        assert conn is not None

