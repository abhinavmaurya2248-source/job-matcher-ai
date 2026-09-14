"""
AI-Based Resume Analyzer and Job Matching System
------------------------------------------------
Milestone 1: project setup, folder structure and a working Flask application
with a resume upload form (PDF only).

Text extraction, NLP preprocessing, skill matching and job matching are added
in later milestones.

Run:
    python app.py
Then open http://127.0.0.1:5000
"""

import os
import uuid

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from config import Config


def create_app() -> Flask:
    """Application factory - keeps the app modular and testable."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the uploads folder exists before any file is saved.
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    register_routes(app)
    return app


def allowed_file(filename: str) -> bool:
    """Return True only for the file extensions we accept (PDF)."""
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in Config.ALLOWED_EXTENSIONS


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        """Home page with the resume upload form."""
        return render_template("index.html")

    @app.route("/upload", methods=["POST"])
    def upload_resume():
        """Validate and save the uploaded resume file."""
        if "resume" not in request.files:
            flash("No file part found in the request.", "error")
            return redirect(url_for("index"))

        uploaded_file = request.files["resume"]

        if uploaded_file.filename == "":
            flash("Please choose a PDF resume before uploading.", "error")
            return redirect(url_for("index"))

        if not allowed_file(uploaded_file.filename):
            flash("Invalid file type. Only PDF resumes are allowed.", "error")
            return redirect(url_for("index"))

        # A unique prefix avoids overwriting files with the same name.
        safe_name = secure_filename(uploaded_file.filename)
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        stored_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        uploaded_file.save(stored_path)

        file_size_kb = round(os.path.getsize(stored_path) / 1024, 2)

        return render_template(
            "result.html",
            original_name=safe_name,
            stored_name=stored_name,
            file_size_kb=file_size_kb,
        )

    @app.errorhandler(413)
    def file_too_large(_error):
        flash("File is too large. Maximum allowed size is 5 MB.", "error")
        return redirect(url_for("index"))


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
