
import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = Path(
    os.environ.get("LIBRARY_DB_PATH", PROJECT_ROOT / "library.db")
).expanduser().resolve()

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_table():
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                book_title TEXT NOT NULL,
                borrower_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                issue_date TEXT NOT NULL,
                expected_return_date TEXT NOT NULL,
                actual_return_date TEXT,
                status TEXT NOT NULL DEFAULT 'Borrowed'
                    CHECK (status IN ('Borrowed', 'Returned')),
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_loans_status
            ON loans(status)
        """)
        conn.commit()
    finally:
        conn.close()
