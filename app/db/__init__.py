from .database import DatabaseService
from .manager import DatabaseManager
from app.core.database_config import DATABASE_NAME

db_manager = DatabaseManager(DATABASE_NAME)
service = DatabaseService(db_manager)