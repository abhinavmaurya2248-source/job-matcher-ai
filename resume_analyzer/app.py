"""
AI-Based Resume Analyzer and Job Matching System
------------------------------------------------
Milestone 1: project setup, PDF upload + validation (working).
Milestone 2: complete UI/UX (Jinja templates + Bootstrap), UI-only pages for
             login, register, dashboard, result, history, profile and admin.

No authentication, database, NLP or AI/ML logic yet.

Run:
    python app.py
Then open http://127.0.0.1:5000
"""

import os
import sqlite3
import uuid

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import auth
import db
from auth import current_user, login_required
from config import Config


def create_app() -> Flask:
    """Application factory - keeps the app modular and testable."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the uploads folder exists before any file is saved.
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Create the SQLite database / users table if needed (Milestone 3).
    db.init_app(app)

    # Make the logged-in user available to every template.
    @app.context_processor
    def inject_current_user():
        return {"current_user": current_user()}

    register_routes(app)
    return app


def allowed_file(filename: str) -> bool:
    """Return True only for the file extensions we accept (PDF)."""
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in Config.ALLOWED_EXTENSIONS


def register_routes(app: Flask) -> None:
    # ---------------------------------------------------------------- public
    @app.route("/")
    def index():
        """Landing page."""
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Login page - authenticates against the users table."""
        if current_user():
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""

            if not email or not password:
                flash("Please enter both your email and password.", "error")
                return render_template("login.html", form_email=email)

            try:
                user = db.find_user_by_email(email)
            except sqlite3.Error:
                flash("Database error. Please try again.", "error")
                return render_template("login.html", form_email=email)

            # One generic message so we never reveal which emails exist.
            if user is None or not check_password_hash(user["password_hash"], password):
                flash("Invalid email or password.", "error")
                return render_template("login.html", form_email=email)

            auth.login_user(user)
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Register page - creates a user with a hashed password."""
        if current_user():
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            full_name = (request.form.get("name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            confirm_password = request.form.get("confirm_password") or ""

            errors = []
            if not full_name:
                errors.append("Full name is required.")
            if not email:
                errors.append("Email is required.")
            elif not auth.is_valid_email(email):
                errors.append("Please enter a valid email address.")
            if not password:
                errors.append("Password is required.")
            elif len(password) < auth.MIN_PASSWORD_LENGTH:
                errors.append(
                    f"Password must be at least {auth.MIN_PASSWORD_LENGTH} characters."
                )
            if password != confirm_password:
                errors.append("The two passwords do not match.")

            if errors:
                for message in errors:
                    flash(message, "error")
                return render_template(
                    "register.html", form_name=full_name, form_email=email
                )

            try:
                db.create_user(full_name, email, generate_password_hash(password))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists.", "error")
                return render_template(
                    "register.html", form_name=full_name, form_email=email
                )
            except sqlite3.Error:
                flash("Database error. Please try again.", "error")
                return render_template(
                    "register.html", form_name=full_name, form_email=email
                )

            flash("Account created successfully. You can log in now.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/logout")
    def logout():
        """Clear the session and return to the home page."""
        auth.logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    # ------------------------------------------------------------- user area
    @app.route("/dashboard")
    @login_required
    def dashboard():
        """Dashboard UI. No real statistics exist yet, so nothing is faked."""
        return render_template("dashboard.html")

    @app.route("/analyze")
    @login_required
    def analyze():
        """Resume upload / analysis page (upload itself is real)."""
        return render_template("analyze.html")

    @app.route("/result")
    @login_required
    def result_placeholder():
        """Empty result layout, shown before any analysis engine exists."""
        return render_template("result.html", uploaded=None)

    @app.route("/history")
    @login_required
    def history():
        """Analysis history UI with an empty state (no database yet)."""
        return render_template("history.html", analyses=[])

    @app.route("/profile")
    @login_required
    def profile():
        """Profile page - shows the logged-in user's own account only."""
        return render_template("profile.html")

    # ----------------------------------------------------------------- admin
    @app.route("/admin/login")
    def admin_login():
        """Admin login page - UI only."""
        return render_template("admin_login.html")

    @app.route("/admin/dashboard")
    def admin_dashboard():
        """Admin dashboard UI with placeholder statistics."""
        return render_template("admin_dashboard.html")

    # ---------------------------------------------- Milestone 1 upload logic
    @app.route("/upload", methods=["POST"])
    def upload_resume():
        """Validate and save the uploaded resume file (Milestone 1 logic)."""
        if "resume" not in request.files:
            flash("No file part found in the request.", "error")
            return redirect(url_for("analyze"))

        uploaded_file = request.files["resume"]

        if uploaded_file.filename == "":
            flash("Please choose a PDF resume before uploading.", "error")
            return redirect(url_for("analyze"))

        if not allowed_file(uploaded_file.filename):
            flash("Invalid file type. Only PDF resumes are allowed.", "error")
            return redirect(url_for("analyze"))

        # A unique prefix avoids overwriting files with the same name.
        safe_name = secure_filename(uploaded_file.filename)
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        stored_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        uploaded_file.save(stored_path)

        file_size_kb = round(os.path.getsize(stored_path) / 1024, 2)

        # The job description is captured by the form but not analysed yet.
        job_description = (request.form.get("job_description") or "").strip()

        return render_template(
            "result.html",
            uploaded={
                "original_name": safe_name,
                "stored_name": stored_name,
                "file_size_kb": file_size_kb,
                "job_description_chars": len(job_description),
            },
        )

    @app.errorhandler(413)
    def file_too_large(_error):
        flash("File is too large. Maximum allowed size is 5 MB.", "error")
        return redirect(url_for("analyze"))

    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("404.html"), 404


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
