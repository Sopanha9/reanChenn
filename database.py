import os
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# Get database URL from environment variable (Railway provides this)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Get a database connection. Uses PostgreSQL if DATABASE_URL is set, otherwise SQLite."""
    if DATABASE_URL:
        # Parse the DATABASE_URL
        result = urlparse(DATABASE_URL)
        return psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    else:
        # Fallback to SQLite for local development
        import sqlite3
        return sqlite3.connect("chinese.db")

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards (
                id SERIAL PRIMARY KEY,
                chinese_word TEXT NOT NULL,
                pinyin TEXT NOT NULL,
                english_meaning TEXT NOT NULL,
                date_saved TEXT NOT NULL
            )
        ''')
    else:
        # SQLite syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chinese_word TEXT NOT NULL,
                pinyin TEXT NOT NULL,
                english_meaning TEXT NOT NULL,
                date_saved TEXT NOT NULL
            )
        ''')

    conn.commit()
    conn.close()

def save_word(chinese_word: str, pinyin: str, english_meaning: str):
    """Inserts a new flashcard into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    date_saved = datetime.now().isoformat()

    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('''
            INSERT INTO flashcards (chinese_word, pinyin, english_meaning, date_saved)
            VALUES (%s, %s, %s, %s)
        ''', (chinese_word, pinyin, english_meaning, date_saved))
    else:
        # SQLite syntax
        cursor.execute('''
            INSERT INTO flashcards (chinese_word, pinyin, english_meaning, date_saved)
            VALUES (?, ?, ?, ?)
        ''', (chinese_word, pinyin, english_meaning, date_saved))

    conn.commit()
    conn.close()

def get_all_words() -> list:
    """Returns all saved flashcards."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, chinese_word, pinyin, english_meaning, date_saved
        FROM flashcards
        ORDER BY id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "chinese_word": row[1],
            "pinyin": row[2],
            "english_meaning": row[3],
            "date_saved": row[4]
        }
        for row in rows
    ]

def delete_word(card_id: int) -> bool:
    """Deletes a flashcard from the database by ID. Returns True if a row was deleted."""
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('DELETE FROM flashcards WHERE id = %s', (card_id,))
    else:
        # SQLite syntax
        cursor.execute('DELETE FROM flashcards WHERE id = ?', (card_id,))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def update_word(card_id: int, chinese_word: str, pinyin: str, english_meaning: str) -> bool:
    """Updates an existing flashcard by ID. Returns True if a row was updated."""
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('''
            UPDATE flashcards
            SET chinese_word = %s, pinyin = %s, english_meaning = %s
            WHERE id = %s
        ''', (chinese_word, pinyin, english_meaning, card_id))
    else:
        # SQLite syntax
        cursor.execute('''
            UPDATE flashcards
            SET chinese_word = ?, pinyin = ?, english_meaning = ?
            WHERE id = ?
        ''', (chinese_word, pinyin, english_meaning, card_id))

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_word_by_id(card_id: int) -> dict | None:
    """Returns a single flashcard by ID, or None if not found."""
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('''
            SELECT id, chinese_word, pinyin, english_meaning, date_saved
            FROM flashcards
            WHERE id = %s
        ''', (card_id,))
    else:
        # SQLite syntax
        cursor.execute('''
            SELECT id, chinese_word, pinyin, english_meaning, date_saved
            FROM flashcards
            WHERE id = ?
        ''', (card_id,))

    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "chinese_word": row[1],
            "pinyin": row[2],
            "english_meaning": row[3],
            "date_saved": row[4]
        }
    return None
