"""
Resume <-> Job description matching (Milestone 7).

Everything here is local, deterministic and explainable:

    resume text + job description
      -> Milestone 6 preprocessing (shared, not duplicated)
      -> TF-IDF vectors (scikit-learn)
      -> cosine similarity
      -> skill comparison (Milestone 6 skill dictionary)
      -> final match score

No external AI or LLM APIs, no randomness, nothing hardcoded.
"""

from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import skill_extractor, text_processor


class MatchError(Exception):
    """Raised with a user-friendly message when matching is not possible."""


# Minimum usable characters before a text is worth analysing.
MIN_TEXT_CHARS = 30

# How the final score is built (transparent and fixed).
SIMILARITY_WEIGHT = 0.5
SKILL_WEIGHT = 0.5

# Keeps tokens such as c++, c#, node.js and .net whole inside TF-IDF.
TOKEN_PATTERN = r"[a-z0-9]+(?:[+#.][a-z0-9+#]*)*"


def _prepare(text: str, label: str) -> str:
    """Clean one text with the Milestone 6 pipeline (shared code)."""
    if not text or len(text.strip()) < MIN_TEXT_CHARS:
        raise MatchError(f"The {label} does not contain enough usable text to analyse.")
    try:
        return text_processor.preprocess(text)["cleaned_text"]
    except ValueError:
        raise MatchError(f"The {label} does not contain enough usable text to analyse.")
    except Exception:
        raise MatchError("The text could not be processed. Please try again.")


def tfidf_similarity(resume_text: str, job_text: str) -> float:
    """Cosine similarity (0.0 - 1.0) between resume and job description."""
    resume_clean = _prepare(resume_text, "resume text")
    job_clean = _prepare(job_text, "job description")

    try:
        vectorizer = TfidfVectorizer(token_pattern=TOKEN_PATTERN, lowercase=True)
        matrix = vectorizer.fit_transform([resume_clean, job_clean])
        score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        # e.g. both texts contain only ignored tokens
        raise MatchError(
            "The resume and job description have no comparable words. "
            "Please check the job description."
        )
    except Exception:
        raise MatchError("The analysis could not be completed. Please try again.")

    # Guard against tiny floating point noise.
    return max(0.0, min(1.0, score))


def compare_skills(resume_text: str, job_text: str) -> Dict[str, List[str]]:
    """Compare the skills found in the resume and in the job description.

    Matching is case-insensitive and uses the Milestone 6 dictionary, so
    no random substring matches are possible.
    """
    resume_found = skill_extractor.extract_skills(resume_text or "")
    job_found = skill_extractor.extract_skills(job_text or "")

    resume_skills = resume_found["skills"]
    job_skills = job_found["skills"]
    resume_set = set(resume_skills)

    matched = [name for name in job_skills if name in resume_set]
    missing = [name for name in job_skills if name not in resume_set]

    return {
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "resume_by_category": resume_found["by_category"],
        "job_by_category": job_found["by_category"],
    }


def skill_match_ratio(matched: List[str], job_skills: List[str]) -> float:
    """Share of the job's required skills that the resume already has."""
    if not job_skills:
        return 0.0
    return len(matched) / len(job_skills)


def analyze(resume_text: str, job_text: str) -> dict:
    """Full matching analysis. Raises MatchError with a friendly message.

    Final score:
        * when the job description lists known skills:
              50% text similarity + 50% skill overlap
        * when it lists none:
              text similarity only (there is nothing to compare skills with)
    """
    similarity = tfidf_similarity(resume_text, job_text)
    skills = compare_skills(resume_text, job_text)

    job_skills = skills["job_skills"]
    skill_ratio = skill_match_ratio(skills["matched_skills"], job_skills)

    if job_skills:
        combined = SIMILARITY_WEIGHT * similarity + SKILL_WEIGHT * skill_ratio
    else:
        combined = similarity

    result = {
        "similarity_percent": round(similarity * 100, 2),
        "skill_match_percent": round(skill_ratio * 100, 2),
        "match_score": round(combined * 100, 2),
        "score_basis": "similarity + skills" if job_skills else "similarity only",
    }
    result.update(skills)
    return result
