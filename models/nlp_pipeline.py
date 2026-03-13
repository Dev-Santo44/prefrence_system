"""
NLP Pipeline for AI-Driven Personal Preference Identifier
Performs tokenization, lemmatization, and sentiment/keyword extraction
using SpaCy to pre-process open-ended text answers.
"""

import re
from typing import List, Dict

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    print("Warning: SpaCy or en_core_web_sm not available. Using basic fallback.")


# Keyword lexicons associated with each Jewelry trait
TRAIT_KEYWORDS: Dict[str, List[str]] = {
    "Style": [
        "minimalist", "bold", "classic", "modern", "vintage",
        "geometric", "delicate", "statement", "unique", "simple",
        "elegant", "chic", "quirky", "trendy", "timeless"
    ],
    "Material": [
        "gold", "silver", "platinum", "diamond", "gem",
        "pearl", "metal", "alloy", "wood", "leather",
        "rose", "brass", "copper", "crystal", "stone"
    ],
    "Occasion": [
        "everyday", "casual", "work", "party", "wedding",
        "bridal", "formal", "evening", "event", "date",
        "vacation", "active", "sport", "gift", "special"
    ],
    "Aesthetic": [
        "boho", "art", "deco", "traditional", "western",
        "indie", "grunge", "preppy", "goth", "soft",
        "romantic", "edgy", "nature", "floral", "sleek"
    ],
    "Budget": [
        "cheap", "affordable", "expensive", "luxury", "custom",
        "premium", "sale", "value", "investment", "budget",
        "high", "exclusive", "designer", "fine", "costume"
    ],
}


def preprocess_text(text: str) -> str:
    """Clean and normalize raw text input."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize_and_lemmatize(text: str) -> List[str]:
    """
    Tokenize and lemmatize text using SpaCy.
    Falls back to simple whitespace splitting if SpaCy is unavailable.
    """
    cleaned = preprocess_text(text)
    if SPACY_AVAILABLE:
        doc = nlp(cleaned)
        tokens = [
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_punct and token.is_alpha
        ]
    else:
        # Basic fallback: simple split without stopwords removal
        tokens = cleaned.split()
    return tokens


def extract_trait_keywords(tokens: List[str]) -> Dict[str, List[str]]:
    """
    Match lemmatized tokens against the OCEAN keyword lexicon.
    Returns a dictionary of trait -> matched keywords.
    """
    matched: Dict[str, List[str]] = {trait: [] for trait in TRAIT_KEYWORDS}
    token_set = set(tokens)
    for trait, keywords in TRAIT_KEYWORDS.items():
        matched[trait] = [kw for kw in keywords if kw in token_set]
    return matched


def analyze_text(text: str) -> Dict:
    """
    Full NLP analysis pipeline for a single text input.
    Returns tokens, matched trait keywords, and keyword counts per trait.
    """
    tokens = tokenize_and_lemmatize(text)
    keyword_matches = extract_trait_keywords(tokens)
    keyword_counts = {trait: len(kws) for trait, kws in keyword_matches.items()}

    return {
        "tokens": tokens,
        "matched_keywords": keyword_matches,
        "keyword_counts": keyword_counts,
    }


def analyze_multiple_texts(texts: List[str]) -> Dict:
    """
    Aggregate NLP analysis across multiple text inputs (e.g., all open-ended answers).
    Returns cumulative keyword counts per trait.
    """
    cumulative = {trait: 0 for trait in TRAIT_KEYWORDS}
    details = []

    for text in texts:
        result = analyze_text(text)
        details.append(result)
        for trait, count in result["keyword_counts"].items():
            cumulative[trait] += count

    return {
        "cumulative_keyword_counts": cumulative,
        "per_text_analysis": details,
    }


if __name__ == "__main__":
    sample_texts = [
        "I love exploring creative ideas and new adventures.",
        "I always plan carefully and stay organized at work.",
        "Sometimes I feel anxious and stressed about the future.",
    ]
    results = analyze_multiple_texts(sample_texts)
    print("Cumulative Keyword Counts:")
    for trait, count in results["cumulative_keyword_counts"].items():
        print(f"  {trait}: {count}")
