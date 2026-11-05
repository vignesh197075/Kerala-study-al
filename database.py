import sqlite3
from pathlib import Path

DB_PATH = Path("data/study.db")
DB_PATH.parent.mkdir(exist_ok=True)

def connect():
    return sqlite3.connect(DB_PATH)

def initialize():

    with connect() as db:

        db.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            description TEXT,
            headings TEXT
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT
        )
        """)

        db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS note_search
        USING fts5(filename, content)
        """)

def save_page(url, title, description, headings):

    with connect() as db:
        db.execute("""
        INSERT INTO pages
        (url, title, description, headings)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
        title=excluded.title,
        description=excluded.description,
        headings=excluded.headings
        """, (url, title, description, headings))

def save_note(filename, content):

    with connect() as db:

        cursor = db.execute(
            "INSERT INTO notes(filename, content) VALUES (?, ?)",
            (filename, content)
        )

        note_id = cursor.lastrowid

        db.execute("""
        INSERT INTO note_search(rowid, filename, content)
        VALUES (?, ?, ?)
        """, (note_id, filename, content))

def search_pages(query):

    with connect() as db:
        return db.execute("""
        SELECT title, url, description
        FROM pages
        WHERE title LIKE ? OR description LIKE ?
        LIMIT 30
        """, (f"%{query}%", f"%{query}%")).fetchall()

def search_notes(query):

    with connect() as db:
        try:
            return db.execute("""
            SELECT filename, snippet(note_search, 1, '', '', '...', 20)
            FROM note_search
            WHERE note_search MATCH ?
            LIMIT 10
            """, (query,)).fetchall()
        except sqlite3.OperationalError:
            return []