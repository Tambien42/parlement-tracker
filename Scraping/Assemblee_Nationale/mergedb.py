"""
This script connects to a source SQLite database, copies all tables (excluding the 'id' column), and saves the data into a new target SQLite database. 
If the tables do not exist in the target database, they will be created with an additional 'id' column as the primary key.

Usage:
- Replace 'example.db' with the source database file path.
- Replace 'new_database.db' with the target database file path.

Steps:
1. Connect to the source and target databases.
2. Retrieve all table names from the source database.
3. Iterate through each table and replicate its structure in the target database.
4. Copy all data from the source table to the corresponding table in the target database, adding an 'id' column if it does not exist.
5. Commit changes and close all connections.

Note: If the target tables already exist, the data will be appended to the existing tables.

Dependencies:
- sqlite3: Python's built-in library for SQLite database manipulation.
"""
import sqlite3

# Connect to the source database (replace 'example.db' with your database file)
source_connection = sqlite3.connect('parlements.db')
source_cursor = source_connection.cursor()

# Connect to the target database (replace 'new_database.db' with your target database file)
target_connection = sqlite3.connect('new_database.db')
target_cursor = target_connection.cursor()

# Get all table names
source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = source_cursor.fetchall()

# Iterate over tables and save data to the new database
for table in tables:
    table_name = table[0]
    print(f"Table: {table_name}")
    
    # Fetch all columns from the table
    source_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = source_cursor.fetchall()
    column_names = [col[1] for col in columns if col[1].lower() != 'id']
    
    # Create table in the target database if it doesn't exist
    column_definitions = [f"{col[1]} {col[2]}" for col in columns if col[1].lower() != 'id']
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(column_definitions)})"
    target_cursor.execute(create_table_query)
    
    # Fetch all data from the source table
    source_cursor.execute(f"SELECT {', '.join(column_names)} FROM {table_name}")
    rows = source_cursor.fetchall()
    
    # Insert data into the target table
    placeholders = ', '.join(['?' for _ in column_names])
    insert_query = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
    target_cursor.executemany(insert_query, rows)

# Commit changes and close the connections
target_connection.commit()
source_connection.close()
target_connection.close()
