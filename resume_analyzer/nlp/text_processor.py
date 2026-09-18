"""
NLP text preprocessing (Milestone 6).

Turns the resume text extracted in Milestone 5 into a cleaned, normalised
form plus a token list, using NLTK for stop-word removal.

Design notes for a small academic project:
  * Everything here is deterministic and rule-based - no LLMs, no models.
  * Technical tokens such as C++, C#, .NET, Node.js, React.js, HTML5 and
    CSS3 must survive cleaning, so punctuation is removed *selectively*
    instead of stripping every non-letter character.
  * NLTK data may not be downloaded on a fresh machine. Every NLTK call is
    wrapped, and a small built-in stop-word list is used as a fallback so
    the application never crashes because of a missing corpus.
"""

import re
from typing import List

# ------------------------------------------------------------------ NLTK
# `stopwords` is the only NLTK resource we need. If it is missing we fall
# back to the small list below instead of failing.
FALLBACK_STOPWORDS = {
    "a", "об", "about", "above", "after", "again", "all", "also", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "can", "did", "do",
    "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "just",
    "me", "more", "most", "my", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "will",
    "with", "you", "your",
}

_STOPWORD_CACHE = None
NLTK_STOPWORDS_AVAILABLE = None  # None = not checked yet


def get_stopwords() -> set:
    """Return the English stop-word set (NLTK when available)."""
    global _STOPWORD_CACHE, NLTK_STOPWORDS_AVAILABLE
    if _STOPWORD_CACHE is not None:
        return _STOPWORD_CACHE

    try:
        from nltk.corpus import stopwords as nltk_stopwords

        words = set(nltk_stopwords.words("english"))
        NLTK_STOPWORDS_AVAILABLE = True
    except Exception:
        # Missing corpus, missing NLTK, or any load error.
        words = set(FALLBACK_STOPWORDS)
        NLTK_STOPWORDS_AVAILABLE = False

    _STOPWORD_CACHE = words
    return words


# ------------------------------------------------------------- cleaning
# Characters kept because they are part of real technology names:
#   +  C++            #  C#            .  .NET / Node.js
KEEP_CHARS = "+#."

_ALLOWED = re.compile(r"[^a-z0-9+#.\s]")


def normalize_case(text: str) -> str:
    """Lower-case the text so matching is case-insensitive."""
    return (text or "").lower()


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs into single spaces."""
    return re.sub(r"\s+", " ", text or "").strip()


def remove_punctuation(text: str) -> str:
    """Remove punctuation and symbols, keeping +, # and . for tech names.

    Leading/trailing keep-characters that are not part of a name (for
    example the full stop ending a sentence) are trimmed per token.
    """
    text = _ALLOWED.sub(" ", text)
    cleaned_tokens = []
    for token in text.split():
        # Strip stray dots at the edges ("python." -> "python") but keep
        # ".net" and "node.js" intact.
        token = token.strip(".") if token.strip(".") else token
        if token:
            cleaned_tokens.append(token)
    return " ".join(cleaned_tokens)


def clean_text(text: str) -> str:
    """Full cleaning pipeline: case -> punctuation -> whitespace."""
    return normalize_whitespace(remove_punctuation(normalize_case(text)))


def tokenize(text: str) -> List[str]:
    """Split cleaned text into tokens.

    A simple regex tokenizer is used instead of NLTK's `word_tokenize`
    because that requires the downloadable `punkt` model and would split
    "node.js" and "c++" apart. This keeps technical tokens whole.
    """
    return re.findall(r"[a-z0-9]+(?:[+#.][a-z0-9+#]*)*", clean_text(text))


def remove_stopwords(tokens: List[str]) -> List[str]:
    """Drop English stop-words and single characters that carry no meaning.

    "c" is kept because it is a programming language.
    """
    stops = get_stopwords()
    keep_single = {"c", "r"}
    return [
        token
        for token in tokens
        if token not in stops and (len(token) > 1 or token in keep_single)
    ]


def preprocess(text: str) -> dict:
    """Run the whole preprocessing pipeline on extracted resume text.

    Returns:
        {
          "cleaned_text": str,   # cleaned, stop-words removed
          "tokens": [str],       # tokens after stop-word removal
          "raw_cleaned": str,    # cleaned text with stop-words kept
        }
    Raises ValueError when there is no usable text.
    """
    if not text or not text.strip():
        raise ValueError("There is no extracted text to process.")

    raw_cleaned = clean_text(text)
    tokens = remove_stopwords(tokenize(raw_cleaned))

    return {
        "cleaned_text": " ".join(tokens),
        "tokens": tokens,
        "raw_cleaned": raw_cleaned,
    }
