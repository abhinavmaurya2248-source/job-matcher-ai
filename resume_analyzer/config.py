"""
Application configuration.

Keeping configuration in one place makes the project easy to understand
and easy to change later (e.g. switching upload folder or file size limit).
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key is used by Flask for sessions and flash messages.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Folder where uploaded resumes are stored.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # Only PDF resumes are accepted in this project.
    ALLOWED_EXTENSIONS = {"pdf"}

    # Maximum upload size: 5 MB.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # SQLite database file used for authentication (Milestone 3).
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "resume_analyzer.db"))

    # Session cookie hardening.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
