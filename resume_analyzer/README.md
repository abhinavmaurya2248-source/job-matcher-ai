# AI-Based Resume Analyzer and Job Matching System

BCA Minor Project — Python + Flask web application.

## Milestone 1 (current)

- Flask project structure created
- Configuration separated in `config.py`
- Working home page with resume upload form
- PDF-only validation, 5 MB size limit, safe unique file names
- Uploaded files stored in `uploads/`

Later milestones add PDF text extraction, NLP preprocessing, skill/keyword
extraction, TF-IDF + cosine similarity job matching, and results storage.

## Folder structure

```text
resume_analyzer/
├── app.py              # Flask app factory and routes
├── config.py           # Configuration (upload folder, limits, secret key)
├── requirements.txt    # Python dependencies
├── templates/
│   ├── base.html
│   ├── index.html
│   └── result.html
├── static/
│   └── css/style.css
└── uploads/            # Uploaded resumes (git-ignored)
```

## How to run

```bash
cd resume_analyzer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## What to test before the next milestone

1. Home page loads with the upload form.
2. Uploading a valid PDF shows the confirmation page with file name and size.
3. Uploading a non-PDF file (e.g. .docx, .txt) shows an error message.
4. Submitting without choosing a file shows an error message.
5. A file larger than 5 MB shows the "File is too large" message.
6. The uploaded file appears inside `uploads/` with a unique name.

## Known limitations

- No resume text extraction or analysis yet (Milestone 2 onwards).
- Uploaded files are stored on local disk only; no database yet.
- No user authentication; single-user local demo.
- This Flask app runs locally with `python app.py`; the Lovable preview
  does not execute Python, so testing is done on your machine.
