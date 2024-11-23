import sqlite3

def drop_table(database, table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    # Create the SQL query to drop the table
    drop_query = f"DROP TABLE IF EXISTS {table_name}"

    try:
        # Execute the drop table query
        cursor.execute(drop_query)
        # Commit the changes
        conn.commit()
        print(f"Table '{table_name}' dropped successfully.")
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

# Usage example:
database = 'parlements.db'
table_name = 'pourcentages_deputesAN'
drop_table(database, table_name)
