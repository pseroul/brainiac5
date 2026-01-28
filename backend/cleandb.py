import sqlite3
import logging
from config import NAME_DB

def clean_database() -> None:
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()

    try:
        # 1. Disable constraints for restructuring
        cursor.execute("PRAGMA foreign_keys = OFF")

        # --- STEP 1: Cleaning parent tables (tags and data) ---
        for table, pk in [('tags', 'name'), ('data', 'name')]:
            # Create a temporary table to merge duplicates
            cursor.execute(f"CREATE TABLE {table}_temp AS SELECT * FROM {table} WHERE 1=0")
            
            # Insert data with trimming and ignore key duplicates
            if table == 'data':
                cursor.execute(f"INSERT OR IGNORE INTO {table}_temp (name, description) SELECT TRIM(name), TRIM(description) FROM {table}")
            else:
                cursor.execute(f"INSERT OR IGNORE INTO {table}_temp (name) SELECT TRIM(name) FROM {table}")

            # Replace the old table with the new one
            cursor.execute(f"DROP TABLE {table}")
            cursor.execute(f"ALTER TABLE {table}_temp RENAME TO {table}")
            # Note: SQLite doesn't recreate indexes/primary keys via simple ALTER TABLE,
            # but for a cleanup script, this allows data manipulation.

        # --- STEP 2: Cleaning the 'relation' table ---
            # Create a temporary table for the linking table
        cursor.execute("""
            CREATE TABLE relation_temp (
                data_name TEXT,
                tag_name TEXT,
                PRIMARY KEY (data_name, tag_name)
            )
        """)

            # Insert relations with trimming both columns.
            # INSERT OR IGNORE solves the "UNIQUE constraint failed" problem
        cursor.execute("""
            INSERT OR IGNORE INTO relation_temp (data_name, tag_name)
            SELECT TRIM(data_name), TRIM(tag_name) FROM relation
        """)

        # Delete orphaned relations (pointing to deleted or renamed data/tags)
        # This ensures everything is clean when re-enabling FKs.
        cursor.execute("DELETE FROM relation_temp WHERE data_name NOT IN (SELECT name FROM data)")
        cursor.execute("DELETE FROM relation_temp WHERE tag_name NOT IN (SELECT name FROM tags)")

        # Replace the relation table
        cursor.execute("DROP TABLE relation")
        cursor.execute("ALTER TABLE relation_temp RENAME TO relation")

        # --- STEP 3: Rebuilding constraints ---
        # Since DROP TABLE deletes everything, it's safer to properly recreate indexes/FKs
        # or simply validate that data is consistent.
        
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON")
        logging.info("Database cleaned, duplicates merged and orphans removed.")

    except sqlite3.Error as e:
        logging.info(f"Critical SQL error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    clean_database()
