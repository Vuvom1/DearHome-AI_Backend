from src.database.db_connection import get_db_engine
from src.database.models import Base
import logging

logger = logging.getLogger(__name__)

def init_db():
    """
    Initialize the database by creating all tables defined in the models.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        engine = get_db_engine()
        if not engine:
            logger.error("Failed to get database engine")
            return False
            
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

def drop_tables():
    """
    Drop all tables from the database. Use with caution!
    
    Returns:
        bool: True if dropping tables was successful, False otherwise
    """
    try:
        engine = get_db_engine()
        if not engine:
            logger.error("Failed to get database engine")
            return False
            
        # Drop all tables
        Base.metadata.drop_all(engine)
        logger.info("Database tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        return False

def reset_db():
    """
    Reset the database by dropping all tables and recreating them.
    
    Returns:
        bool: True if reset was successful, False otherwise
    """
    try:
        if drop_tables():
            return init_db()
        return False
    except Exception as e:
        logger.error(f"Failed to reset database: {str(e)}")
        return False

if __name__ == "__main__":
    # This allows running this file directly to initialize the database
    init_db()