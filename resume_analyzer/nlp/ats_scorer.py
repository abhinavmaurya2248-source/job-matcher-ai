"""
ATS-style resume scoring (Milestone 8).

Builds on the Milestone 7 matcher output; nothing here is random or
external. Same resume + same job description -> same ATS score.

    ATS score = 40% Skill Match + 35% Keyword Relevance + 25% Text Similarity

Why these weights:
  * Skill Match (40%)       - named technical skills are the clearest,
                              most explainable signal a recruiter scans for.
  * Keyword Relevance (35%) - how many of the job's meaningful words the
                              resume actually uses (ATS tools are keyword-led).
  * Text Similarity (25%)   - TF-IDF cosine similarity captures overall
                              wording overlap, but is low for short texts,
                              so it gets the smallest weight.

If the job description contains no recognised skills, skill match cannot be
measured, so its 40% is shared proportionally between the other two parts:
    ATS = 58.33% Keyword Relevance + 41.67% Text Similarity
(35/60 and 25/60 of the score; the ratio between them stays the same.)

This is an ATS-style estimate for learning purposes, not the scoring
system of any real ATS software.
"""

from collections import Counter
from typing import Dict, List, Optional

from . import text_processor

SKILL_WEIGHT = 0.40
KEYWORD_WEIGHT = 0.35
SIMILARITY_WEIGHT = 0.25

# Score bands (inclusive lower bounds), checked from the top down.
STATUS_BANDS = [
    (80, "Strong Match"),
    (60, "Good Match"),
    (40, "Moderate Match"),
    (0, "Low Match"),
]

MIN_KEYWORD_LENGTH = 3      # ignore very short tokens such as "an", "ok"
MAX_KEYWORDS_SHOWN = 12     # keep the on-screen keyword list concise


def _meaningful_tokens(text: str) -> List[str]:
    """Milestone 6 tokenizer + stop-word removal, minus numbers/tiny words."""
    tokens = text_processor.remove_stopwords(text_processor.tokenize(text or ""))
    return [
        t for t in tokens
        if len(t) >= MIN_KEYWORD_LENGTH and not t.replace(".", "").isdigit()
    ]


def keyword_relevance(resume_text: str, job_text: str) -> Dict:
    """Share of the job's distinct meaningful keywords found in the resume.

    relevance = |job keywords that also appear in resume| / |job keywords|
    Shown keywords are the overlapping ones, most frequent in the job first.
    """
    job_counts = Counter(_meaningful_tokens(job_text))
    resume_set = set(_meaningful_tokens(resume_text))
    if not job_counts:
        return {"percent": 0.0, "keywords": [], "job_keyword_count": 0, "matched_count": 0}

    overlap = [w for w in job_counts if w in resume_set]
    overlap.sort(key=lambda w: (-job_counts[w], w))
    return {
        "percent": round(len(overlap) / len(job_counts) * 100, 2),
        "keywords": overlap[:MAX_KEYWORDS_SHOWN],
        "job_keyword_count": len(job_counts),
        "matched_count": len(overlap),
    }


def ats_status(score: float) -> str:
    for lower, label in STATUS_BANDS:
        if score >= lower:
            return label
    return STATUS_BANDS[-1][1]


def calculate(resume_text: str, job_text: str, match: Dict) -> Optional[Dict]:
    """ATS-style score from real texts plus the Milestone 7 matcher output.

    `match` must contain similarity_percent, matched_skills and job_skills
    (as returned by nlp.matcher.analyze). Returns None if that data is missing.
    """
    if not match or match.get("similarity_percent") is None:
        return None

    similarity = float(match["similarity_percent"])
    job_skills = match.get("job_skills") or []
    matched = match.get("matched_skills") or []
    keywords = keyword_relevance(resume_text, job_text)

    if job_skills:
        skill_pct = round(len(matched) / len(job_skills) * 100, 2)
        score = (SKILL_WEIGHT * skill_pct
                 + KEYWORD_WEIGHT * keywords["percent"]
                 + SIMILARITY_WEIGHT * similarity)
        basis = "skills + keywords + similarity"
    else:
        skill_pct = None   # not measurable - never shown as 0%
        rest = KEYWORD_WEIGHT + SIMILARITY_WEIGHT
        score = (KEYWORD_WEIGHT / rest * keywords["percent"]
                 + SIMILARITY_WEIGHT / rest * similarity)
        basis = "keywords + similarity"

    score = round(max(0.0, min(100.0, score)), 1)
    return {
        "score": score,
        "status": ats_status(score),
        "skill_percent": skill_pct,
        "keyword_percent": keywords["percent"],
        "similarity_percent": round(similarity, 2),
        "keywords": keywords["keywords"],
        "keyword_matched_count": keywords["matched_count"],
        "job_keyword_count": keywords["job_keyword_count"],
        "job_skill_count": len(job_skills),
        "matched_skill_count": len(matched),
        "basis": basis,
    }
