import os
import json
import sqlite3
from api.pipeline.structure import ingest_document

db_path = "bis_database.db"
schema_path = "db/schema.sql"

# Document Metadata mapping
documents_metadata = {
    "IS_694_2010": {
        "is_number": "IS 694",
        "revision_label": "2010",
        "document_address": "IS694-2010",
        "valid_from": "2010-01-01",
        "valid_to": None,
        "is_current": True,
        "superseded_by": None
    },
    "IS_8130_1984": {
        "is_number": "IS 8130",
        "revision_label": "1984",
        "document_address": "IS8130-1984",
        "valid_from": "1984-01-01",
        "valid_to": None,
        "is_current": True,
        "superseded_by": None
    },
    "IS_5831_1984": {
        "is_number": "IS 5831",
        "revision_label": "1984",
        "document_address": "IS5831-1984",
        "valid_from": "1984-01-01",
        "valid_to": None,
        "is_current": True,
        "superseded_by": None
    }
}

def init_db(conn):
    """
    Initializes database tables using the schema definition.
    """
    print(f"Reading schema definition from {schema_path}...")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # SQLite can execute multiple statements in script mode
    conn.executescript(schema_sql)
    print("Database schema successfully initialized.")

def main():
    # Remove existing database if it exists to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database to start fresh.")
        
    conn = sqlite3.connect(db_path)
    try:
        # Initialize schema
        init_db(conn)
        
        # Ingest documents
        for filename, metadata in documents_metadata.items():
            json_file = f"{filename}.json"
            if not os.path.exists(json_file):
                print(f"Error: JSON file not found: {json_file}")
                continue
                
            print(f"Ingesting parsed JSON for {filename}...")
            with open(json_file, 'r') as f:
                json_data = json.load(f)
                
            ingest_document(conn, json_data, metadata)
            print(f"Successfully ingested {filename} into database.")
            
        print("All document ingestions completed successfully.")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
