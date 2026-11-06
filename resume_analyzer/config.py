"""
Application configuration.

Keeping configuration in one place makes the project easy to understand
and easy to change later (e.g. switching upload folder or file size limit).
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY signs the Flask session cookie. It must come from the
    # environment in production; a development-only fallback keeps local
    # development simple. The key value itself is never printed or logged.
    IS_PRODUCTION = (
        os.environ.get("APP_ENV", "").strip().lower() in {"prod", "production"}
        or os.environ.get("FLASK_ENV", "").strip().lower() == "production"
    )

    _secret_key = os.environ.get("SECRET_KEY", "")
    if not _secret_key:
        if IS_PRODUCTION:
            # Fail fast instead of running with a publicly known key.
            raise RuntimeError(
                "SECRET_KEY is not set. Production mode requires a securely "
                "configured SECRET_KEY environment variable (a long random "
                "string). Set it before starting the app in production."
            )
        _secret_key = "dev-secret-key-change-me"
    SECRET_KEY = _secret_key

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
