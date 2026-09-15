"""
SQLite database helpers (Milestone 3).

Small and dependency-free: only the standard library `sqlite3` module is used.
The database file and the `users` table are created automatically on startup.
"""

import sqlite3
from typing import Optional

from flask import Flask, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db() -> sqlite3.Connection:
    """Return a per-request SQLite connection (rows behave like dicts)."""
    if "db" not in g:
        from flask import current_app

        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None) -> None:
    """Close the connection at the end of the request."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db(app: Flask) -> None:
    """Create the database file and tables if they do not exist yet."""
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        connection.executescript(SCHEMA)


def init_app(app: Flask) -> None:
    """Wire the database into the Flask app."""
    app.teardown_appcontext(close_db)
    init_db(app)


# ------------------------------------------------------------------ queries
# Every query below uses parameter placeholders (?) - never string formatting.

def create_user(full_name: str, email: str, password_hash: str) -> int:
    """Insert a new user and return its id. Raises sqlite3.IntegrityError
    when the email already exists (UNIQUE constraint)."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
        (full_name, email, password_hash),
    )
    db.commit()
    return int(cursor.lastrowid)


def find_user_by_email(email: str) -> Optional[sqlite3.Row]:
    return get_db().execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()


def find_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
