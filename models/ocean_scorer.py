"""
OCEAN Scorer for AI-Driven Personal Preference Identifier
Computes Big Five (OCEAN) scores by combining:
  1. Likert-scale survey responses (numeric)
  2. NLP keyword signals from open-ended text answers
And generates personalized preference recommendations.
"""

from typing import List, Dict, Optional
from models.nlp_pipeline import analyze_multiple_texts

# Trait ordering must stay consistent
TRAITS = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]

# Score range: 1-5 Likert scale
LIKERT_MIN = 1
LIKERT_MAX = 5

# Weight split between Likert and NLP signals
LIKERT_WEIGHT = 0.70
NLP_WEIGHT = 0.30

# Maximum plausible NLP keyword hits per trait (for normalization)
MAX_NLP_KEYWORDS = 10


def normalize_likert(raw_scores: List[float]) -> float:
    """
    Average a list of Likert ratings (1–5) and normalize to 0–100.
    """
    if not raw_scores:
        return 50.0  # Neutral default
    avg = sum(raw_scores) / len(raw_scores)
    return round(((avg - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN)) * 100, 2)


def normalize_nlp(keyword_count: int) -> float:
    """
    Normalize NLP keyword hit count to a 0–100 score.
    """
    clamped = min(keyword_count, MAX_NLP_KEYWORDS)
    return round((clamped / MAX_NLP_KEYWORDS) * 100, 2)


def compute_ocean_scores(
    likert_answers: Dict[str, List[float]],
    open_texts: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Compute OCEAN scores.

    Args:
        likert_answers: Dict mapping trait name -> list of Likert ratings (1–5).
                        E.g. {"Openness": [4, 5, 3], "Conscientiousness": [2, 3, 4], ...}
        open_texts: Optional list of open-ended text answers.

    Returns:
        Dict mapping trait name -> final score (0–100).
    """
    # Step 1: Normalize Likert scores
    likert_scores = {
        trait: normalize_likert(likert_answers.get(trait, []))
        for trait in TRAITS
    }

    # Step 2: NLP analysis on open-ended text
    nlp_scores = {trait: 0.0 for trait in TRAITS}
    if open_texts:
        nlp_result = analyze_multiple_texts(open_texts)
        for trait in TRAITS:
            count = nlp_result["cumulative_keyword_counts"].get(trait, 0)
            nlp_scores[trait] = normalize_nlp(count)

    # Step 3: Weighted fusion
    final_scores = {}
    for trait in TRAITS:
        score = (
            LIKERT_WEIGHT * likert_scores[trait]
            + NLP_WEIGHT * nlp_scores[trait]
        )
        final_scores[trait] = round(score, 2)

    return final_scores


def generate_recommendations(scores: Dict[str, float]) -> str:
    """
    Generate a personalized recommendation paragraph based on OCEAN scores.
    """
    recommendations = []

    if scores.get("Openness", 0) >= 60:
        recommendations.append(
            "You have a highly open and curious mind. You thrive in creative roles such as "
            "design, research, writing, or entrepreneurship."
        )
    else:
        recommendations.append(
            "You prefer familiar settings and structured routines. Careers in operations, "
            "administration, or technical precision work may suit you well."
        )

    if scores.get("Conscientiousness", 0) >= 60:
        recommendations.append(
            "Your disciplined and goal-oriented nature makes you well-suited for project "
            "management, finance, engineering, or leadership roles."
        )
    else:
        recommendations.append(
            "You are flexible and spontaneous. Creative or dynamic environments where "
            "adaptability is valued would be a great fit."
        )

    if scores.get("Extraversion", 0) >= 60:
        recommendations.append(
            "As an extrovert, you excel in social roles such as sales, marketing, "
            "public relations, teaching, or team leadership."
        )
    else:
        recommendations.append(
            "As an introvert, you do your best work in focused, independent environments "
            "such as research, programming, writing, or data analysis."
        )

    if scores.get("Agreeableness", 0) >= 60:
        recommendations.append(
            "Your cooperative and empathetic nature is a great asset in healthcare, "
            "counseling, social work, HR, or customer service."
        )

    if scores.get("Neuroticism", 0) >= 60:
        recommendations.append(
            "You may benefit from mindfulness practices, structured stress-management "
            "strategies, and roles with clear expectations to support your wellbeing."
        )

    return " ".join(recommendations)


def score_and_recommend(
    likert_answers: Dict[str, List[float]],
    open_texts: Optional[List[str]] = None,
) -> Dict:
    """
    Full pipeline: compute OCEAN scores + generate recommendations.
    Returns a result dict ready for database storage.
    """
    scores = compute_ocean_scores(likert_answers, open_texts)
    recommendations = generate_recommendations(scores)

    return {
        "openness": scores["Openness"],
        "conscientiousness": scores["Conscientiousness"],
        "extraversion": scores["Extraversion"],
        "agreeableness": scores["Agreeableness"],
        "neuroticism": scores["Neuroticism"],
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    # Demo run
    sample_likert = {
        "Openness": [4, 5, 3, 4, 5],
        "Conscientiousness": [3, 3, 4, 2, 3],
        "Extraversion": [2, 2, 3, 2, 1],
        "Agreeableness": [5, 4, 5, 4, 5],
        "Neuroticism": [3, 3, 2, 4, 3],
    }
    sample_texts = [
        "I love creative ideas and exploring new places.",
        "I get stressed sometimes but I try to stay calm.",
    ]
    result = score_and_recommend(sample_likert, sample_texts)
    print("OCEAN Results:")
    for k, v in result.items():
        print(f"  {k}: {v}")
