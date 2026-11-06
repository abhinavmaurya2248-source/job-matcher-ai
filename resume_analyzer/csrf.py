"""
Lightweight CSRF protection for the app's POST forms (no extra dependencies).

How it works:
- when a page with a form is rendered, a random token is generated and
  stored in the signed Flask session;
- every POST form sends that token back in a hidden `csrf_token` field;
- a `before_request` hook rejects any POST whose token is missing or does
  not match, so a form forged on another site cannot be submitted.

The token is compared with `hmac.compare_digest` to avoid timing attacks,
and it is regenerated whenever the session is cleared (login/logout).
"""

import hmac
import secrets
from urllib.parse import urlsplit

from flask import flash, redirect, request, session, url_for

SESSION_KEY = "_csrf_token"
FORM_FIELD = "csrf_token"


def csrf_token() -> str:
    """Return this session's CSRF token, creating it on first use."""
    token = session.get(SESSION_KEY)
    if not token:
        token = secrets.token_hex(32)
        session[SESSION_KEY] = token
    return token


def _same_origin(referrer: str) -> bool:
    """True only when the referrer points at this very host."""
    try:
        return urlsplit(referrer).netloc == urlsplit(request.host_url).netloc
    except ValueError:
        return False


def register_csrf_protection(app) -> None:
    """Expose `csrf_token()` to templates and validate it on every POST."""
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def _check_csrf_token():
        if request.method != "POST":
            return None
        sent = request.form.get(FORM_FIELD, "")
        expected = session.get(SESSION_KEY, "")
        if not sent or not expected or not hmac.compare_digest(sent, expected):
            flash("Your form session expired. Please try again.", "error")
            referrer = request.referrer
            if referrer and _same_origin(referrer):
                return redirect(referrer)
            return redirect(url_for("index"))
        return None
