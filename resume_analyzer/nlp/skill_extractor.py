"""
Rule-based technical skill extraction (Milestone 6).

The skill dictionary lives here (never inside Flask routes) so it is easy
to extend: add one entry to SKILL_DICTIONARY and the whole application
picks it up.

Matching rules:
  * case-insensitive
  * whole-phrase matching with custom boundaries, so "java" does NOT match
    "javascript" and "c" does not match every word containing the letter c
  * multi-word skills ("machine learning") are supported
  * duplicates are removed and display names are returned
"""

import re
from typing import Dict, List

from . import text_processor

# display name -> list of accepted spellings / aliases (lower-case)
SKILL_DICTIONARY: Dict[str, Dict[str, List[str]]] = {
    "Programming Languages": {
        "Python": ["python"],
        "Java": ["java"],
        "C": ["c"],
        "C++": ["c++", "cpp"],
        "C#": ["c#", "c sharp", "csharp"],
        "JavaScript": ["javascript", "java script", "js"],
        "TypeScript": ["typescript"],
        "PHP": ["php"],
        "SQL": ["sql"],
        ".NET": [".net", "dotnet", "dot net"],
    },
    "Web": {
        "HTML": ["html", "html5"],
        "CSS": ["css", "css3"],
        "React": ["react", "react.js", "reactjs"],
        "Angular": ["angular", "angular.js", "angularjs"],
        "Vue": ["vue", "vue.js", "vuejs"],
        "Node.js": ["node.js", "nodejs", "node js"],
        "Express": ["express", "express.js", "expressjs"],
        "Bootstrap": ["bootstrap"],
        "Flask": ["flask"],
        "Django": ["django"],
        "REST API": ["rest api", "restful api", "rest apis"],
    },
    "Databases": {
        "MySQL": ["mysql"],
        "PostgreSQL": ["postgresql", "postgres"],
        "SQLite": ["sqlite"],
        "MongoDB": ["mongodb", "mongo db"],
        "Oracle": ["oracle"],
    },
    "Data / AI": {
        "NumPy": ["numpy"],
        "Pandas": ["pandas"],
        "Scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
        "TensorFlow": ["tensorflow", "tensor flow"],
        "PyTorch": ["pytorch"],
        "Machine Learning": ["machine learning", "ml"],
        "Deep Learning": ["deep learning"],
        "NLP": ["nlp", "natural language processing"],
        "Data Analysis": ["data analysis", "data analytics"],
    },
    "Tools": {
        "Git": ["git"],
        "GitHub": ["github"],
        "Docker": ["docker"],
        "Linux": ["linux"],
        "VS Code": ["vs code", "visual studio code", "vscode"],
    },
}


def _flatten() -> List[tuple]:
    """[(display_name, category, alias)] sorted longest alias first."""
    pairs = []
    for category, skills in SKILL_DICTIONARY.items():
        for display_name, aliases in skills.items():
            for alias in aliases:
                pairs.append((display_name, category, alias))
    pairs.sort(key=lambda item: len(item[2]), reverse=True)
    return pairs


_FLAT_SKILLS = _flatten()


def _pattern(alias: str) -> re.Pattern:
    """Whole-phrase pattern with boundaries that respect +, # and .

    Standard \b does not work for "c++" or "c#", so we require that the
    match is not glued to another word/number character, and that a "."
    or "+" does not continue the token.
    """
    escaped = re.escape(alias).replace(r"\ ", r"[\s\-_]+")
    return re.compile(
        r"(?<![a-z0-9+#.])" + escaped + r"(?![a-z0-9+#])(?!\.[a-z0-9])"
    )


_COMPILED = [
    (display_name, category, _pattern(alias))
    for display_name, category, alias in _FLAT_SKILLS
]


def extract_skills(text: str) -> dict:
    """Find supported technical skills in resume text.

    Matching runs against the cleaned (lower-cased, punctuation-trimmed)
    text so that formatting in the PDF does not affect the result.

    Returns:
        {"skills": [display names], "by_category": {category: [names]}}
    """
    if not text or not text.strip():
        return {"skills": [], "by_category": {}}

    haystack = " " + text_processor.clean_text(text) + " "

    found: List[str] = []
    by_category: Dict[str, List[str]] = {}

    for display_name, category, pattern in _COMPILED:
        if display_name in found:
            continue
        if pattern.search(haystack):
            found.append(display_name)
            by_category.setdefault(category, []).append(display_name)

    # Stable, readable output order.
    found.sort(key=str.lower)
    for names in by_category.values():
        names.sort(key=str.lower)

    ordered = {
        category: sorted(by_category[category], key=str.lower)
        for category in SKILL_DICTIONARY
        if category in by_category
    }
    return {"skills": found, "by_category": ordered}


def all_skill_names() -> List[str]:
    """Every display name in the dictionary (useful for later milestones)."""
    return sorted(
        {name for skills in SKILL_DICTIONARY.values() for name in skills},
        key=str.lower,
    )
