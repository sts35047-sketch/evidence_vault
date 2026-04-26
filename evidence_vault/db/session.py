import os
import sqlite3
from typing import Generator
from evidence_vault.core.config import settings

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', settings.db_path)

def get_db() -> Generator:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        title TEXT,
        filename TEXT,
        uploaded_by TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        content TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        user TEXT,
        action TEXT,
        target TEXT,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # Create FTS virtual table if supported
    try:
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(title, content, filename, content='documents', content_rowid='id')")
    except Exception:
        # FTS5 might not be available in this sqlite build; ignore
        pass
    conn.commit()
    conn.close()

# helper to log audit
def log_action(db_conn, user, action, target='', details=''):
    db_conn.execute('INSERT INTO audit_logs (user, action, target, details) VALUES (?, ?, ?, ?)', (user, action, target, details))
    db_conn.commit()

# helper to update FTS table
def update_fts(db_conn, doc_id, title, content, filename):
    try:
        # try to insert into FTS virtual table
        db_conn.execute("INSERT INTO documents_fts(rowid, title, content, filename) VALUES (?, ?, ?, ?)", (doc_id, title, content, filename))
        db_conn.commit()
    except Exception:
        # ignore if FTS not available
        pass