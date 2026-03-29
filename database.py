import sqlite3
from datetime import datetime

DB_NAME = "chinese.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
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
    cursor.execute('DELETE FROM flashcards WHERE id = ?', (card_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def update_word(card_id: int, chinese_word: str, pinyin: str, english_meaning: str) -> bool:
    """Updates an existing flashcard by ID. Returns True if a row was updated."""
    conn = get_connection()
    cursor = conn.cursor()
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
