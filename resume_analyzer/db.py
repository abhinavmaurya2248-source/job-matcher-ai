"""
SQLite database helpers.

Milestone 3: users table + authentication queries.
Milestone 4: resumes and analyses tables + user-scoped data access helpers.

Only the standard library `sqlite3` module is used. The database file and all
tables are created automatically on startup, and initialisation is safe to run
many times (every statement uses IF NOT EXISTS, nothing is dropped).
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

CREATE TABLE IF NOT EXISTS resumes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,
    original_filename TEXT NOT NULL,
    stored_filename   TEXT NOT NULL,
    file_path         TEXT NOT NULL,
    file_size         INTEGER,
    uploaded_at       TIMESTAMP NOT NULL DEFAULT (datetime('now')),
    extracted_text    TEXT,
    page_count        INTEGER,
    char_count        INTEGER,
    extraction_status TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analyses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    resume_id       INTEGER NOT NULL,
    job_description TEXT,
    match_score     REAL,
    matched_skills  TEXT,
    missing_skills  TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id);
"""


def get_db() -> sqlite3.Connection:
    """Return a per-request SQLite connection (rows behave like dicts)."""
    if "db" not in g:
        from flask import current_app

        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        # Foreign-key enforcement is off by default in SQLite.
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None) -> None:
    """Close the connection at the end of the request."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


# Columns added after the first release. Each one is created only when the
# existing database does not have it yet - nothing is dropped or recreated.
RESUME_MIGRATIONS = {
    "extracted_text": "TEXT",
    "page_count": "INTEGER",
    "char_count": "INTEGER",
    "extraction_status": "TEXT",
}


def migrate_db(connection: sqlite3.Connection) -> None:
    """Safely add missing columns to an existing resumes table."""
    existing = {
        row["name"] if isinstance(row, sqlite3.Row) else row[1]
        for row in connection.execute("PRAGMA table_info(resumes)")
    }
    for column, column_type in RESUME_MIGRATIONS.items():
        if column not in existing:
            connection.execute(
                f"ALTER TABLE resumes ADD COLUMN {column} {column_type}"
            )


def init_db(app: Flask) -> None:
    """Create the database file and tables if they do not exist yet."""
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        migrate_db(connection)


def init_app(app: Flask) -> None:
    """Wire the database into the Flask app."""
    app.teardown_appcontext(close_db)
    init_db(app)


# ------------------------------------------------------------------ users
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


# ---------------------------------------------------------------- resumes
# Every resume helper takes user_id so a user can only reach their own rows.

def create_resume(
    user_id: int,
    original_filename: str,
    stored_filename: str,
    file_path: str,
    file_size: int,
) -> int:
    """Save the metadata of an uploaded resume and return the new row id."""
    db = get_db()
    cursor = db.execute(
        """INSERT INTO resumes
               (user_id, original_filename, stored_filename, file_path, file_size)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, original_filename, stored_filename, file_path, file_size),
    )
    db.commit()
    return int(cursor.lastrowid)


def list_resumes(user_id: int):
    """All resumes of one user, newest first."""
    return get_db().execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY datetime(uploaded_at) DESC, id DESC",
        (user_id,),
    ).fetchall()


def find_resume(resume_id: int, user_id: int) -> Optional[sqlite3.Row]:
    """One resume, but only if it belongs to this user."""
    return get_db().execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
    ).fetchone()


def count_resumes(user_id: int) -> int:
    return int(
        get_db().execute(
            "SELECT COUNT(*) AS n FROM resumes WHERE user_id = ?", (user_id,)
        ).fetchone()["n"]
    )


def delete_resume(resume_id: int, user_id: int) -> bool:
    """Delete one of the user's own resumes. Returns True when a row was
    removed. Analyses of that resume are removed by ON DELETE CASCADE."""
    db = get_db()
    cursor = db.execute(
        "DELETE FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


# --------------------------------------------------------------- analyses
# The analysis columns exist now; they are filled by a later milestone.

def create_analysis(
    user_id: int,
    resume_id: int,
    job_description: str = "",
    match_score: Optional[float] = None,
    matched_skills: Optional[str] = None,
    missing_skills: Optional[str] = None,
) -> int:
    """Insert an analysis row for one of the user's own resumes."""
    db = get_db()
    cursor = db.execute(
        """INSERT INTO analyses
               (user_id, resume_id, job_description, match_score,
                matched_skills, missing_skills)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            resume_id,
            job_description,
            match_score,
            matched_skills,
            missing_skills,
        ),
    )
    db.commit()
    return int(cursor.lastrowid)


def list_analyses(user_id: int):
    """All analyses of one user with the related resume file name."""
    return get_db().execute(
        """SELECT a.*, r.original_filename
           FROM analyses AS a
           JOIN resumes AS r ON r.id = a.resume_id
           WHERE a.user_id = ?
           ORDER BY datetime(a.created_at) DESC, a.id DESC""",
        (user_id,),
    ).fetchall()


def find_analysis(analysis_id: int, user_id: int) -> Optional[sqlite3.Row]:
    return get_db().execute(
        """SELECT a.*, r.original_filename
           FROM analyses AS a
           JOIN resumes AS r ON r.id = a.resume_id
           WHERE a.id = ? AND a.user_id = ?""",
        (analysis_id, user_id),
    ).fetchone()


def count_analyses(user_id: int) -> int:
    return int(
        get_db().execute(
            "SELECT COUNT(*) AS n FROM analyses WHERE user_id = ?", (user_id,)
        ).fetchone()["n"]
    )


def delete_analysis(analysis_id: int, user_id: int) -> bool:
    db = get_db()
    cursor = db.execute(
        "DELETE FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0
