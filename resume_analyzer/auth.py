"""
Authentication helpers (Milestone 3).

Contains:
- basic form validation helpers
- the `login_required` decorator used to protect pages
- `current_user()` which loads the logged-in user for the current request
"""

import re
from functools import wraps

from flask import flash, g, redirect, session, url_for

import db

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
MIN_PASSWORD_LENGTH = 6


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email or ""))


def current_user():
    """Return the logged-in user row, or None. Cached per request in `g`."""
    if "user" not in g:
        user_id = session.get("user_id")
        g.user = db.find_user_by_id(user_id) if user_id else None
    return g.user


def login_user(user) -> None:
    """Store the minimum identity information in the session."""
    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["full_name"]


def logout_user() -> None:
    session.clear()


def login_required(view):
    """Redirect anonymous visitors to the login page."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped
