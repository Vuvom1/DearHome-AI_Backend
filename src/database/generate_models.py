import os
import sys
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

# Get connection parameters from environment variables
server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")
username = os.getenv("SQL_USERNAME")
password = os.getenv("SQL_PASSWORD")

if not all([server, database, username, password]):
    print("Error: SQL connection parameters not found in environment variables")
    sys.exit(1)

# Clean the server name (remove 'tcp:' prefix if present)
if server.startswith('tcp:'):
    server = server[4:]

# URL encode the password to handle special characters
quoted_password = urllib.parse.quote_plus(password)

# Create the connection string based on the driver availability
try:
    import pyodbc
    print("Using pyodbc driver for connection")
    
    # Create ODBC connection string
    conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={quoted_password}'
    connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}"
except ImportError:
    try:
        import pymssql
        print("Using pymssql driver for connection")
        
        # Parse server and port if needed
        if ',' in server:
            server_parts = server.split(',')
            host = server_parts[0]
            port = int(server_parts[1]) if len(server_parts) > 1 else 1433
        else:
            host = server
            port = 1433
            
        connection_url = f"mssql+pymssql://{username}:{password}@{host}:{port}/{database}"
    except ImportError:
        print("Error: Neither pyodbc nor pymssql is installed")
        sys.exit(1)

# Print the command to run (without password)
safe_connection_url = connection_url.replace(quoted_password, "********")
print(f"Running sqlacodegen with connection: {safe_connection_url}")

# Execute sqlacodegen
command = f"sqlacodegen --outfile=src/database/models.py '{connection_url}'"
print("Generating models...")
os.system(command)
print("Models generated successfully in src/database/models.py")