"""
SQLite Database and Schema for Suraksha Reports & Indicators
"""

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "suraksha.db"
DB_PATH = Path(os.environ.get("SURAKSHA_DB_PATH", str(DEFAULT_DB_PATH)))

def _create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()
    # Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scam_type TEXT NOT NULL,
        district TEXT NOT NULL,
        indicator_hash TEXT NOT NULL,
        indicator_raw TEXT,
        device_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indicators Table (Aggregated Confirmation Status)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS indicators (
        indicator_hash TEXT PRIMARY KEY,
        indicator_raw TEXT,
        scam_type TEXT,
        status TEXT DEFAULT 'Unconfirmed',
        distinct_device_count INTEGER DEFAULT 1,
        first_reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confirmed_at TIMESTAMP
    );
    """)

    # Emerging Clusters Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scam_clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        district TEXT NOT NULL,
        cluster_name TEXT NOT NULL,
        keywords TEXT NOT NULL,
        report_count INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn

def init_db():
    conn = get_connection()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
