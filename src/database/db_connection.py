import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
import urllib.parse

# Load environment variables if not already done
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global engine variable
engine = None

def get_db_engine():
    """
    Creates or returns the SQLAlchemy database engine with connection pooling.
    
    Returns:
        The SQLAlchemy engine instance
    """
    global engine
    
    if engine is not None:
        return engine
        
    try:
        # Get connection parameters from environment variables
        server = os.getenv("SQL_SERVER")
        database = os.getenv("SQL_DATABASE")
        username = os.getenv("SQL_USERNAME")
        password = os.getenv("SQL_PASSWORD")
        
        if not all([server, database, username, password]):
            logger.error("SQL connection parameters not found in environment variables")
            return None
            
        # Clean the server name (remove 'tcp:' prefix if present)
        if server.startswith('tcp:'):
            server = server[4:]
        
        # Try with pyodbc following Azure best practices
        try:
            import pyodbc
            logger.info("Using pyodbc driver for connection")
            
            # URL encode the password to handle special characters
            quoted_password = urllib.parse.quote_plus(password)
            
            # The direct pyodbc connection approach for macOS
            # Use DSN-less connection which is more reliable on macOS with Azure SQL
            conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER=127.0.0.1;DATABASE=INTERIOR_SHOPPING;UID={username};PWD={quoted_password};Encrypt=yes;TrustServerCertificate=yes;ConnectionTimeout=30;'
            
            # Create connection string for SQLAlchemy
            connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}"
            
            # Create the SQLAlchemy engine with connection pooling
            engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,  
                pool_pre_ping=True,  
                fast_executemany=True  
            )
            
            # Test the connection
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                
            logger.info("Database connection established successfully using pyodbc")
            return engine
            
        except (ImportError, Exception) as e:
            logger.warning(f"Could not connect using pyodbc: {str(e)}. Trying pymssql...")
            
            # Fall back to pymssql if pyodbc fails
            import pymssql
            logger.info("Using pymssql driver for connection")
            
            # Parse server and port if needed
            if ',' in server:
                server_parts = server.split(',')
                host = server_parts[0]
                port = int(server_parts[1]) if len(server_parts) > 1 else 1433
            else:
                host = server
                port = 1433
            
            # Create connection string for pymssql
            connection_string = f"mssql+pymssql://{username}:{password}@{host}:{port}/{database}"
            
            # Create the SQLAlchemy engine with connection pooling
            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,  # Recycle connections after 30 minutes (Azure best practice)
                pool_pre_ping=True  # Verify connections before using from pool
            )
            
            # Test the connection
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                
            logger.info("Database connection established successfully using pymssql")
            return engine
            
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine: {str(e)}")
        return None

def create_session():
    """
    Creates a new SQLAlchemy session.
    
    Returns:
        dict: A dictionary containing the session object or error information
    """
    engine = get_db_engine()
    
    if engine is None:
        return {
            "success": False,
            "error": "Failed to create database engine"
        }
    
    try:
        # Create a sessionmaker bound to the engine
        Session = sessionmaker(bind=engine)
        session = Session()
        
        return {
            "success": True,
            "message": "Successfully created database session",
            "session": session
        }
    except Exception as e:
        logger.error(f"Failed to create database session: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to create database session: {str(e)}"
        }

def execute_sql_query(query, params=None, timeout=30):
    """
    Execute a SQL query and return the results.
    
    Args:
        query (str): The SQL query to execute
        params (dict, optional): Parameters for the query
        timeout (int): Query timeout in seconds
        
    Returns:
        dict: A dictionary containing the query results or error information
    """
    start_time = datetime.now()
    session_result = create_session()
    
    if not session_result.get("success"):
        return session_result
    
    session = session_result["session"]
    
    try:
        # Create a text object for the SQL query
        sql_text = text(query)
        
        # Set the timeout for the query
        execution_options = {"timeout": timeout}
        
        if params:
            # Execute the query with parameters
            result = session.execute(sql_text, params, execution_options=execution_options)
        else:
            # Execute the query without parameters
            result = session.execute(sql_text, execution_options=execution_options)
        
        # Check if the query returns results
        try:
            # For SELECT queries, fetch results
            results = [dict(row) for row in result.mappings()]
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Query executed in {execution_time:.2f} seconds")
            
            return {
                "success": True,
                "results": results,
                "execution_time": execution_time
            }
        except SQLAlchemyError:
            # For non-SELECT queries (INSERT, UPDATE, DELETE)
            session.commit()
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Query executed in {execution_time:.2f} seconds")
            
            return {
                "success": True,
                "message": "Query executed successfully",
                "execution_time": execution_time
            }
    except Exception as e:
        session.rollback()  # Roll back any changes if an error occurs
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Query execution failed in {execution_time:.2f} seconds: {str(e)}")
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}",
            "execution_time": execution_time
        }
    finally:
        session.close()

def close_connection(session):
    """
    Closes the database session.
    """
    if session:
        session.close()
