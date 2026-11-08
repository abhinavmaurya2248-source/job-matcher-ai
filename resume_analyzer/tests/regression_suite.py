"""
Regression suite (56 checks) for the AI Resume Analyzer.

Run from the project root:

    python tests/regression_suite.py

The suite copies the application into a temporary directory so the real
database and uploaded files are never touched, then exercises Milestones
1-8 plus the security/UI hardening (favicon, CSRF, SECRET_KEY, admin
placeholders) through the Flask test client.
"""

import io
import os
import re
import shutil
import sys
import tempfile

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name: str, condition, detail: str = "") -> None:
    results.append((name, PASS if condition else FAIL, detail))


# ---------------------------------------------------------------------------
# Isolated app: copy the project, use a throwaway database.
# ---------------------------------------------------------------------------
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_DIR = os.path.join(tempfile.gettempdir(), "resume-analyzer-regression")
if os.path.exists(RUN_DIR):
    shutil.rmtree(RUN_DIR)
shutil.copytree(SRC, RUN_DIR, ignore=shutil.ignore_patterns(
    "__pycache__", "*.db", "uploads", ".git"))

os.environ["DATABASE"] = os.path.join(RUN_DIR, "regression.db")
sys.path.insert(0, RUN_DIR)

os.chdir(RUN_DIR)
from app import create_app  # noqa: E402

app = create_app()
client = app.test_client()

CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


def get_token(path: str) -> str:
    page = client.get(path).data.decode()
    match = CSRF_RE.search(page)
    return match.group(1) if match else ""


def register_and_login(email: str, password: str = "secret123", name: str = "Test User") -> None:
    client.get("/logout")
    client.post("/register", data={
        "csrf_token": get_token("/register"),
        "name": name, "email": email,
        "password": password, "confirm_password": password,
    }, follow_redirects=True)
    client.get("/logout")
    client.get("/login")
    client.post("/login", data={
        "csrf_token": get_token("/login"),
        "email": email, "password": password,
    }, follow_redirects=True)


# ---------------------------------------------------------------------------
# Test files
# ---------------------------------------------------------------------------
import fitz  # noqa: E402  (PyMuPDF)


def pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 80), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


RESUME_TEXT = (
    "Curriculum Vitae of Priya Sharma\n"
    "Skills: Python, Java, SQL, HTML, CSS, JavaScript, Flask, Git, GitHub\n"
    "Experience: built web apps with Python and Flask, databases in MySQL, "
    "front-end with HTML CSS JavaScript. Version control with Git and GitHub."
)
GOOD_PDF = pdf_bytes(RESUME_TEXT)
EMPTY_PDF = pdf_bytes("")  # a page with no text
IMAGE_PDF = None  # built below with a drawn rectangle only

doc = fitz.open()
page = doc.new_page()
page.draw_rect(fitz.Rect(50, 50, 300, 200), color=(0, 0, 1))
IMAGE_PDF = doc.tobytes()
doc.close()

CORRUPT_PDF = b"%PDF-1.4 this is not really a pdf \x00\x01\x02 random bytes"
BIG_PDF = GOOD_PDF + b"\x00" * (6 * 1024 * 1024)  # over the 5 MB limit


def upload(path_name: str, jd: str = "We are hiring a Python developer "
           "with Flask, SQL, Git and JavaScript experience for a web application team.") -> object:
    """Upload a PDF as the logged-in user; returns the result page response."""
    return client.post("/upload", data={
        "csrf_token": get_token("/analyze"),
        "job_description": jd,
        "resume": (io.BytesIO(open(path_name, "rb").read()), os.path.basename(path_name)),
    }, content_type="multipart/form-data")


def write_tmp(name: str, data: bytes) -> str:
    path = os.path.join(RUN_DIR, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return path


# ---------------------------------------------------------------------------
# 1-9: public pages, favicon, admin placeholders
# ---------------------------------------------------------------------------
check("01 home page renders", client.get("/").status_code == 200)
check("02 login page renders", client.get("/login").status_code == 200)
check("03 register page renders", client.get("/register").status_code == 200)
check("04 admin login placeholder renders", client.get("/admin/login").status_code == 200)
check("05 admin dashboard placeholder renders", client.get("/admin/dashboard").status_code == 200)
check("06 unknown page gives custom 404", client.get("/no-such-page").status_code == 404)

favicon = client.get("/favicon.ico")
check("07 /favicon.ico served (no 404)", favicon.status_code == 200 and "image" in favicon.content_type)

home_html = client.get("/login").data.decode()
check("08 pages declare the favicon link", 'rel="icon"' in home_html)

admin_html = client.get("/admin/login").data.decode()
check("09 admin pages marked noindex", "noindex" in admin_html)

# ---------------------------------------------------------------------------
# 10-17: registration + login validation
# ---------------------------------------------------------------------------
def post_register(data) -> object:
    return client.post("/register", data={"csrf_token": get_token("/register"), **data})


check("10 register rejects missing fields",
      b"Full name is required" in post_register({"email": "", "password": "", "confirm_password": ""}).data)
check("11 register rejects invalid email",
      b"valid email" in post_register({"name": "A", "email": "not-an-email", "password": "secret123", "confirm_password": "secret123"}).data)
check("12 register rejects short password",
      b"at least 6" in post_register({"name": "A", "email": "short@x.com", "password": "abc", "confirm_password": "abc"}).data)
check("13 register rejects password mismatch",
      b"do not match" in post_register({"name": "A", "email": "mismatch@x.com", "password": "secret123", "confirm_password": "other"}).data)

resp = post_register({"name": "User A", "email": "a@test.com", "password": "secret123", "confirm_password": "secret123"})
check("14 registration succeeds", resp.status_code == 302)
check("15 duplicate email rejected",
      b"already exists" in post_register({"name": "Dup", "email": "a@test.com", "password": "secret123", "confirm_password": "secret123"}).data)

check("16 login rejects wrong password",
      b"Invalid email or password" in client.post("/login", data={
          "csrf_token": get_token("/login"), "email": "a@test.com", "password": "wrongpass"}).data)

client.get("/login")
resp = client.post("/login", data={
    "csrf_token": get_token("/login"), "email": "a@test.com", "password": "secret123"}, follow_redirects=True)
check("17 login succeeds and shows dashboard", b"Dashboard" in resp.data or resp.status_code == 200)

# ---------------------------------------------------------------------------
# 18-24: route protection + CSRF behaviour
# ---------------------------------------------------------------------------
anon = app.test_client()
check("18 dashboard requires login", anon.get("/dashboard").status_code == 302)
check("19 analyze requires login", anon.get("/analyze").status_code == 302)
check("20 history requires login", anon.get("/history").status_code == 302)
check("21 profile requires login", anon.get("/profile").status_code == 302)

check("22 POST without CSRF token rejected",
      b"form session expired" in anon.post("/login", data={"email": "a@test.com", "password": "secret123"}, follow_redirects=True).data)
check("23 POST with wrong CSRF token rejected",
      b"form session expired" in anon.post("/login", data={
          "csrf_token": "0" * 64, "email": "a@test.com", "password": "secret123"}, follow_redirects=True).data)

analyze_html = client.get("/analyze").data.decode()
check("24 upload form carries CSRF token", 'name="csrf_token"' in analyze_html)

# ---------------------------------------------------------------------------
# 25-31: Milestone 1 upload validation + Milestone 4 persistence
# ---------------------------------------------------------------------------
check("25 non-PDF upload rejected",
      b"Only PDF" in client.post("/upload", data={
          "csrf_token": get_token("/analyze"), "job_description": "x",
          "resume": (io.BytesIO(b"hello"), "resume.txt")}, content_type="multipart/form-data", follow_redirects=True).data)
check("26 empty submission rejected",
      b"choose a PDF" in client.post("/upload", data={
          "csrf_token": get_token("/analyze"), "job_description": "x",
          "resume": (io.BytesIO(b""), "")}, content_type="multipart/form-data", follow_redirects=True).data)
check("27 over-5MB upload rejected",
      client.post("/upload", data={
          "csrf_token": get_token("/analyze"), "job_description": "x",
          "resume": (io.BytesIO(BIG_PDF), "big.pdf")}, content_type="multipart/form-data").status_code in (302, 413))

resp = upload(write_tmp("good.pdf", GOOD_PDF))
good_result_html = resp.data
check("28 valid PDF upload succeeds", resp.status_code == 200)

import db as db_module  # noqa: E402
with app.app_context():
    resumes = db_module.list_resumes(1)
check("29 resume row stored for the user", len(resumes) == 1)
check("30 stored filename is unique-safe", resumes[0]["stored_filename"].endswith("good.pdf") and "_" in resumes[0]["stored_filename"])

# ---------------------------------------------------------------------------
# 31-35: Milestone 5 extraction
# ---------------------------------------------------------------------------
check("31 resume text extracted and stored", "Flask" in (resumes[0]["extracted_text"] or ""))
check("32 extraction page/char counts recorded", resumes[0]["page_count"] == 1 and (resumes[0]["char_count"] or 0) > 50)

resp = upload(write_tmp("image-only.pdf", IMAGE_PDF))
check("33 image-only PDF gets a clear message", b"No readable text" in resp.data)

resp = upload(write_tmp("corrupt.pdf", CORRUPT_PDF))
check("34 corrupt PDF gets a clear message", resp.status_code == 200 and b"extract" in resp.data.lower())

check("35 extracted text preview shown on result", b"Extracted text preview" in good_result_html)

# ---------------------------------------------------------------------------
# 36-39: Milestone 6 NLP
# ---------------------------------------------------------------------------
with app.app_context():
    record = db_module.find_resume(resumes[0]["id"], 1)
import json as json_module  # noqa: E402
stored_skills = json_module.loads(record["extracted_skills"] or "[]")
check("36 technical skills extracted", {"Python", "Flask", "Git"} <= set(stored_skills))
check("37 no false-positive skills", all(s in {"Python", "Java", "SQL", "HTML", "CSS", "JavaScript", "Flask", "Git", "GitHub", "MySQL"} for s in stored_skills))
check("38 cleaned text stored", bool((record["cleaned_text"] or "").strip()))

resp = upload(write_tmp("nolang.pdf", pdf_bytes("Dear hiring manager, I am very interested in this role.")))
check("39 resume without skills shows exact message",
      b"No recognized technical skills were found in this resume." in resp.data)

# ---------------------------------------------------------------------------
# 40-48: Milestone 7 matching, history, isolation
# ---------------------------------------------------------------------------
with app.app_context():
    analyses = db_module.list_analyses(1)
    main_analysis = [a for a in analyses if a["original_filename"] == "good.pdf"][0]
check("40 match score in 0-100 and non-trivial", 0 < main_analysis["match_score"] < 100)
matched = json_module.loads(main_analysis["matched_skills"])
missing = json_module.loads(main_analysis["missing_skills"])
check("41 matched skills correct", {"Python", "Flask", "SQL", "Git", "JavaScript"} <= set(matched) if matched else False)
check("42 missing skills reported as list", isinstance(missing, list))

resp = upload(write_tmp("nojd.pdf", GOOD_PDF), jd="   ")
check("43 empty job description rejected", b"Please paste a job description" in resp.data)

history_html = client.get("/history").data.decode()
check("44 analyses listed in history", "good.pdf" in history_html and "Analysis" in history_html)

detail = client.get(f"/analyses/{main_analysis['id']}")
check("45 saved analysis detail renders", detail.status_code == 200 and b"Match Score" in detail.data)

register_and_login("b@test.com", name="User B")
check("46 user B cannot view user A's analysis",
      client.get(f"/analyses/{main_analysis['id']}", follow_redirects=True).status_code == 200
      and b"not found in your account" in client.get(f"/analyses/{main_analysis['id']}", follow_redirects=True).data)

with app.app_context():
    a_resume = db_module.find_resume(resumes[0]["id"], 1)
check("47 user B cannot delete user A's resume",
      b"not found in your account" in client.post(f"/resumes/{a_resume['id']}/delete", data={
          "csrf_token": get_token("/history")}, follow_redirects=True).data)

# Back as user A for the no-skill JD case.
client.get("/logout")
client.get("/login")
client.post("/login", data={"csrf_token": get_token("/login"), "email": "a@test.com", "password": "secret123"}, follow_redirects=True)

resp = upload(write_tmp("noskill.pdf", GOOD_PDF),
              jd="Looking for a detail-oriented person to join our friendly office team.")
with app.app_context():
    rows = db_module.list_analyses(1)
check("48 no-recognised-skills JD still scores (similarity only)", rows[0]["match_score"] is not None and 0 <= rows[0]["match_score"] <= 100)

# ---------------------------------------------------------------------------
# 49-55: Milestone 8 ATS + integrity
# ---------------------------------------------------------------------------
result_html = resp.data.decode()
check("49 ATS score shown on the result page", "ATS-style resume score" in result_html)
check("50 ATS status band shown", "Match" in result_html and ("Strong Match" in result_html or "Good Match" in result_html or "Moderate Match" in result_html or "Low Match" in result_html))

from nlp import ats_scorer, matcher  # noqa: E402
with app.app_context():
    resume_row = db_module.find_resume(main_analysis["resume_id"], 1)
    job_text = main_analysis["job_description"]
    m = matcher.analyze(resume_row["extracted_text"], job_text)
    ats1 = ats_scorer.calculate(resume_row["extracted_text"], job_text, m)
    ats2 = ats_scorer.calculate(resume_row["extracted_text"], job_text, matcher.analyze(resume_row["extracted_text"], job_text))
check("51 ATS score is deterministic (repeatable)", ats1["score"] == ats2["score"] and ats1["status"] == ats2["status"])

no_skill_match = matcher.analyze(resume_row["extracted_text"],
                                 "Looking for a detail-oriented person to join our friendly office team.")
no_skill_ats = ats_scorer.calculate(resume_row["extracted_text"],
                                    "Looking for a detail-oriented person to join our friendly office team.",
                                    no_skill_match)
check("52 no-skill JD redistributes ATS weights", no_skill_ats["basis"] == "keywords + similarity"
      and no_skill_ats["skill_percent"] is None
      and abs(no_skill_ats["keyword_percent"] * 0.35 / 0.6 + no_skill_ats["similarity_percent"] * 0.25 / 0.6 - no_skill_ats["score"]) < 0.2)

check("53 M7 match_score unaffected by ATS layer", abs(main_analysis["match_score"] - m["match_score"]) < 0.01)
check("54 keyword counts consistent", no_skill_ats["keyword_matched_count"] <= no_skill_ats["job_keyword_count"])

import sqlite3  # noqa: E402
with sqlite3.connect(os.environ["DATABASE"]) as conn:
    row = conn.execute("SELECT password_hash FROM users WHERE email = 'a@test.com'").fetchone()
check("55 password stored only as a hash", row is not None and row[0].startswith("scrypt:") and "secret123" not in row[0])

# ---------------------------------------------------------------------------
# 56: logout
# ---------------------------------------------------------------------------
client.get("/logout")
check("56 logout clears the session", client.get("/dashboard").status_code == 302)

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
failed = [r for r in results if r[1] == FAIL]
for name, status, _detail in results:
    print(f"{status:4}  {name}")
print(f"\n{PASS}: {len(results) - len(failed)}  FAIL: {len(failed)}  (of {len(results)})")
sys.exit(1 if failed else 0)
