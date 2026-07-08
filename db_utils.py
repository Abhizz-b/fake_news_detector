import sqlite3
import os
import hashlib
import secrets
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Database file path
DB_PATH = "factcheck.db"

def init_db():
    """Initialize the database, create required tables"""
    # Check if database file exists
    db_exists = os.path.exists(DB_PATH)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # If database doesn't exist, create tables
    if not db_exists:
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_text TEXT NOT NULL,
            claim TEXT NOT NULL,
            verdict TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Create evidence table (linked to history)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            history_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            source TEXT NOT NULL,
            similarity REAL,
            FOREIGN KEY (history_id) REFERENCES history (id)
        )
        ''')

        conn.commit()

    conn.close()

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash password using SHA-256 with a salt

    Args:
        password: plaintext password
        salt: optional salt value, generates a new one if not provided

    Returns:
        Tuple containing (password_hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)  # generate a 32-character (16-byte) random salt

    # Combine password and salt, then hash
    password_with_salt = password + salt
    password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()

    return password_hash, salt

def create_user(username: str, password: str) -> bool:
    """
    Create a new user

    Args:
        username: username
        password: password

    Returns:
        Whether creation succeeded
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False  # Username already exists

        # Hash password
        password_hash, salt = hash_password(password)

        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt)
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return False

def verify_user(username: str, password: str) -> Optional[int]:
    """
    Verify user credentials

    Args:
        username: username
        password: password

    Returns:
        User ID if verification succeeds, otherwise None
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get user record
        cursor.execute(
            "SELECT id, password_hash, salt FROM users WHERE username = ?",
            (username,)
        )

        user = cursor.fetchone()
        conn.close()

        if not user:
            return None  # User doesn't exist

        user_id, stored_hash, salt = user

        # Hash the entered password using the same salt
        calculated_hash, _ = hash_password(password, salt)

        # Compare hashes
        if calculated_hash == stored_hash:
            return user_id
        else:
            return None
    except Exception as e:
        print(f"Error verifying user: {str(e)}")
        return None

def save_fact_check(
    user_id: int,
    original_text: str,
    claim: str,
    verdict: str,
    reasoning: str,
    evidence_chunks: List[Dict[str, Any]]
) -> int:
    """
    Save fact-check result to history

    Args:
        user_id: user ID
        original_text: original text
        claim: extracted claim
        verdict: verdict (TRUE/FALSE/PARTIALLY TRUE, etc.)
        reasoning: reasoning process
        evidence_chunks: list of evidence chunks

    Returns:
        History record ID
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Insert history record
        cursor.execute(
            "INSERT INTO history (user_id, original_text, claim, verdict, reasoning) VALUES (?, ?, ?, ?, ?)",
            (user_id, original_text, claim, verdict, reasoning)
        )

        # Get the newly inserted history record ID
        history_id = cursor.lastrowid

        # Insert evidence
        for chunk in evidence_chunks:
            cursor.execute(
                "INSERT INTO evidence (history_id, text, source, similarity) VALUES (?, ?, ?, ?)",
                (history_id, chunk['text'], chunk['source'], chunk.get('similarity', 0))
            )

        conn.commit()
        conn.close()
        return history_id
    except Exception as e:
        print(f"Error saving fact-check record: {str(e)}")
        return -1

def get_user_history(user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get a user's fact-check history

    Args:
        user_id: user ID
        limit: maximum number of records to return
        offset: pagination offset

    Returns:
        List of history records
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable row factory so results act like dicts
        cursor = conn.cursor()

        # Get history records
        cursor.execute(
            """
            SELECT id, original_text, claim, verdict, reasoning, created_at 
            FROM history 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )

        history_rows = cursor.fetchall()
        history = []

        for row in history_rows:
            history_item = dict(row)

            # Get related evidence
            cursor.execute(
                "SELECT text, source, similarity FROM evidence WHERE history_id = ?",
                (row['id'],)
            )

            evidence_rows = cursor.fetchall()
            evidence = [dict(evidence_row) for evidence_row in evidence_rows]

            history_item['evidence'] = evidence
            history.append(history_item)

        conn.close()
        return history
    except Exception as e:
        print(f"Error getting user history: {str(e)}")
        return []

def get_history_by_id(history_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific history record by ID

    Args:
        history_id: history record ID

    Returns:
        History record dict, or None if not found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get history record
        cursor.execute(
            """
            SELECT id, user_id, original_text, claim, verdict, reasoning, created_at 
            FROM history 
            WHERE id = ?
            """,
            (history_id,)
        )

        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        history_item = dict(row)

        # Get related evidence
        cursor.execute(
            "SELECT text, source, similarity FROM evidence WHERE history_id = ?",
            (history_id,)
        )

        evidence_rows = cursor.fetchall()
        evidence = [dict(evidence_row) for evidence_row in evidence_rows]

        history_item['evidence'] = evidence

        conn.close()
        return history_item
    except Exception as e:
        print(f"Error getting history by ID: {str(e)}")
        return None

def count_user_history(user_id: int) -> int:
    """
    Count total history records for a user

    Args:
        user_id: user ID

    Returns:
        Number of history records
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        print(f"Error counting user history: {str(e)}")
        return 0