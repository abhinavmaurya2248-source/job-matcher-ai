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
        """Dashboard UI. Counts come from the database; the score stays a
        placeholder because no analysis engine exists yet."""
        user = current_user()
        try:
            resume_count = db.count_resumes(user["id"])
            analysis_count = db.count_analyses(user["id"])
            resumes = db.list_resumes(user["id"])
        except sqlite3.Error:
            flash("Could not read your data. Please try again.", "error")
            resume_count = analysis_count = 0
            resumes = []

        return render_template(
            "dashboard.html",
            resume_count=resume_count,
            analysis_count=analysis_count,
            latest_resume=resumes[0] if resumes else None,
        )

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
        """History page - real resume records plus (still empty) analyses,
        always scoped to the logged-in user."""
        user = current_user()
        try:
            analyses = db.list_analyses(user["id"])
            resumes = db.list_resumes(user["id"])
        except sqlite3.Error:
            flash("Could not read your history. Please try again.", "error")
            analyses, resumes = [], []

        return render_template("history.html", analyses=analyses, resumes=resumes)

    @app.route("/resumes/<int:resume_id>/delete", methods=["POST"])
    @login_required
    def delete_resume(resume_id: int):
        """Delete one of the logged-in user's own uploaded resumes."""
        user = current_user()
        try:
            record = db.find_resume(resume_id, user["id"])
            if record is None:
                flash("That resume was not found in your account.", "error")
                return redirect(url_for("history"))

            db.delete_resume(resume_id, user["id"])
        except sqlite3.Error:
            flash("Database error while deleting the resume.", "error")
            return redirect(url_for("history"))

        # Remove the stored file too, but never fail the request over it.
        try:
            os.remove(record["file_path"])
        except OSError:
            pass

        flash("Resume deleted.", "success")
        return redirect(url_for("history"))

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
    @login_required
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

        file_size_bytes = os.path.getsize(stored_path)
        file_size_kb = round(file_size_bytes / 1024, 2)

        # The job description is captured by the form but not analysed yet.
        job_description = (request.form.get("job_description") or "").strip()

        # Milestone 4: store the resume metadata for the logged-in user.
        user_id = current_user()["id"]
        try:
            resume_id = db.create_resume(
                user_id=user_id,
                original_filename=safe_name,
                stored_filename=stored_name,
                file_path=stored_path,
                file_size=file_size_bytes,
            )
        except sqlite3.Error:
            resume_id = None
            flash(
                "The file was uploaded but could not be saved to the database.",
                "error",
            )

        # Milestone 5: read the text out of the PDF with PyMuPDF.
        extraction = {"status": "failed", "message": None, "page_count": None,
                      "char_count": None, "preview": None}
        try:
            result = extractor.extract_text(stored_path)
        except extractor.ExtractionError as error:
            extraction["message"] = str(error)
            flash(str(error), "error")
            if resume_id is not None:
                try:
                    db.save_extracted_text(
                        resume_id, user_id, None, None, 0, "failed"
                    )
                except sqlite3.Error:
                    pass
        else:
            extraction.update(
                status="success",
                page_count=result["page_count"],
                char_count=result["char_count"],
                preview=extractor.preview(result["text"]),
            )
            if resume_id is not None:
                try:
                    db.save_extracted_text(
                        resume_id,
                        user_id,
                        result["text"],
                        result["page_count"],
                        result["char_count"],
                        "success",
                    )
                except sqlite3.Error:
                    flash(
                        "Text was extracted but could not be saved to the database.",
                        "error",
                    )
            flash("Resume text extracted successfully.", "success")

        return render_template(
            "result.html",
            uploaded={
                "resume_id": resume_id,
                "original_name": safe_name,
                "stored_name": stored_name,
                "file_size_kb": file_size_kb,
                "job_description_chars": len(job_description),
            },
            extraction=extraction,
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
