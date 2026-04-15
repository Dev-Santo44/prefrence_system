"""
Jewelry Scorer for AI-Driven Personal Preference Identifier
Computes Style, Material, Occasion, Aesthetic, and Budget scores by combining:
  1. Likert-scale survey responses (numeric)
  2. NLP keyword signals from open-ended text answers
And generates personalized jewelry recommendations.
"""

from typing import List, Dict, Optional, Tuple
from models.nlp_pipeline import analyze_multiple_texts

# Trait ordering must stay consistent with the new categories
TRAITS = ["Style", "Material", "Occasion", "Aesthetic", "Budget"]

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
    Average a list of Likert ratings (1-5) and normalize to 0-100.
    """
    if not raw_scores:
        return 50.0  # Neutral default
    avg = sum(raw_scores) / len(raw_scores)
    val = float(((avg - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN)) * 100)
    return round(val, 2)


def normalize_nlp(keyword_count: int) -> float:
    """
    Normalize NLP keyword hit count to a 0-100 score.
    """
    clamped = float(min(keyword_count, MAX_NLP_KEYWORDS))
    return round((clamped / MAX_NLP_KEYWORDS) * 100, 2)


def compute_jewelry_scores(
    likert_answers: Dict[str, List[any]],
    open_texts: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Compute Jewelry category scores based on personality options.
    """
    # Mappings for the 5 new personality options (Index 0-3 -> Score 0-100)
    OPTION_MAPS = {
        "Style":     {0: 90, 1: 20, 2: 60, 3: 40},
        "Material":  {0: 95, 1: 75, 2: 30, 3: 50},
        "Occasion":  {0: 90, 1: 60, 2: 15, 3: 35},
        "Aesthetic": {0: 85, 1: 75, 2: 25, 3: 55},
        "Budget":    {0: 95, 1: 40, 2: 60, 3: 70},
    }

    final_trait_scores = {}
    for trait in TRAITS:
        answers = likert_answers.get(trait, [])
        if not answers:
            final_trait_scores[trait] = 50.0
            continue
            
        trait_scores = []
        for ans in answers:
            # Handle categorical index (int or str int)
            try:
                idx = int(ans)
                if idx in [0, 1, 2, 3]:
                    trait_scores.append(float(OPTION_MAPS[trait].get(idx, 50)))
                else:
                    # Legacy Likert 1-5 support
                    val = float(((idx - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN)) * 100)
                    trait_scores.append(val)
            except (ValueError, TypeError):
                trait_scores.append(50.0)
        
        final_trait_scores[trait] = round(sum(trait_scores) / len(trait_scores), 2)

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
        score = float(
            LIKERT_WEIGHT * final_trait_scores[trait]
            + NLP_WEIGHT * nlp_scores[trait]
        )
        final_scores[trait] = round(score, 2)

    return final_scores


def generate_recommendations(scores: Dict[str, float]) -> Tuple[str, str]:
    """
    Generate a personalized recommendation paragraph based on Jewelry category scores,
    and classify the user into a jewelry persona.
    """
    recommendations_list = []
    
    # Simple logic for Persona
    highest_score = max(scores.values())
    primary_category = [k for k, v in scores.items() if v == highest_score][0]
    
    # Persona Mapping (examples)
    persona = "Balanced Explorer"
    if primary_category == "Style" and scores["Style"] > 60:
        persona = "Statement Maker"
    elif primary_category == "Material" and scores["Material"] > 60:
        persona = "Material Connoisseur"
    elif primary_category == "Occasion" and scores["Occasion"] > 60:
        persona = "Event Specialist"
    elif primary_category == "Aesthetic" and scores["Aesthetic"] > 60:
        persona = "Aesthetic Dreamer"
    elif primary_category == "Budget" and scores["Budget"] > 60:
        persona = "Luxury Appreciator"

    # Build qualitative recommendations based on scores
    if scores.get("Style", 0) >= 60:
        recommendations_list.append(
            "You highly value distinct and bold styles. Finding pieces with unique geometric patterns or "
            "statement necklaces would fit you perfectly."
        )
    else:
        recommendations_list.append(
            "You lean towards a more minimalist approach. Delicate chains, simple bands, or stud earrings "
            "align best with your everyday style."
        )

    if scores.get("Material", 0) >= 60:
        recommendations_list.append(
            "The material of jewelry is essential to you. You'd likely appreciate high-end metals like platinum, "
            "solid gold, or ethically sourced gemstones."
        )
    else:
        recommendations_list.append(
            "You are flexible with materials and open to creative alloys or mixed-metal designs as long as "
            "they capture the right vibe."
        )

    if scores.get("Occasion", 0) >= 60:
        recommendations_list.append(
            "You select pieces with specific events in mind. We recommend looking into versatile pieces that "
            "can transition elegantly from daytime to evening wear."
        )

    if scores.get("Aesthetic", 0) >= 60:
        recommendations_list.append(
            "You hold a strong appreciation for specific aesthetics (like vintage, art deco, or modern). "
            "Curate a collection that strongly resonates with this focused theme."
        )

    if scores.get("Budget", 0) >= 60:
        recommendations_list.append(
            "You are willing to invest in premium or luxury pieces. Custom-made jewelry or high-end designer "
            "collections are likely to excite you."
        )

    return persona, " ".join(recommendations_list)


def compute_visual_scores(liked_item_ids: List[int]) -> Dict[str, float]:
    """
    Given a list of liked item IDs from the swipe interface, looks up their 
    metadata (style, material, etc) and features, and maps them to a 0-100 score 
    for each of the 5 traits.
    """
    from preference_app.models import JewelryCatalog
    visual_scores = {trait: 50.0 for trait in TRAITS} # Default neutral
    
    if not liked_item_ids:
        return visual_scores
        
    items = JewelryCatalog.objects.filter(id__in=liked_item_ids)
    if not items.exists():
        return visual_scores
        
    # Simple mapping: count occurrences of styles, materials, etc in liked items
    # and map to scores.
    counts = {"Style": 0, "Material": 0, "Occasion": 0, "Aesthetic": 0, "Budget": 0}
    
    for item in items:
        # Style mapping
        if item.style in ["Statement", "Bold"]:
            counts["Style"] += 1
        elif item.style in ["Minimalist", "Classic"]:
            counts["Style"] -= 1
            
        # Material mapping
        if item.material in ["Diamond", "Platinum", "Gold"]:
            counts["Material"] += 1
            counts["Budget"] += 1
            
        # Occasion mapping
        if item.occasion in ["Bridal", "Party", "Formal"]:
            counts["Occasion"] += 1
            
        # Aesthetic mapping
        if item.aesthetic in ["Vintage", "Art Deco", "Traditional"]:
            counts["Aesthetic"] += 1
            
        if item.price_range == "Luxury":
            counts["Budget"] += 1
            
    total_items = items.count()
    
    # Normalize mapping logic (-1 to 1) -> (0 to 100)
    for trait in TRAITS:
        # This is a heuristic translation for the visual signal
        ratio = counts[trait] / total_items
        visual_scores[trait] = 50.0 + (ratio * 50.0)
        visual_scores[trait] = max(0.0, min(100.0, visual_scores[trait]))
        
    return visual_scores

def score_and_recommend(
    likert_answers: Dict[str, List[float]],
    open_texts: Optional[List[str]] = None,
    liked_item_ids: Optional[List[int]] = None
) -> Dict:
    """
    Full pipeline: compute Jewelry scores + generate recommendations/persona.
    Fuses survey scores (60%) with Visual Swipe features (40%).
    Returns a result dict ready for database storage.
    """
    # 1. Base Survey Scores (Likert + NLP)
    survey_scores = compute_jewelry_scores(likert_answers, open_texts)
    
    final_scores = survey_scores.copy()
    
    # 2. Visual Fusion (Swipe Likes)
    if liked_item_ids:
        visual_scores = compute_visual_scores(liked_item_ids)
        for trait in TRAITS:
            s_score = float(survey_scores[trait])
            v_score = float(visual_scores[trait])
            combined = (s_score * 0.6) + (v_score * 0.4)
            final_scores[trait] = round(float(combined), 2)
            
    persona, recommendations = generate_recommendations(final_scores)

    return {
        "style": final_scores["Style"],
        "material": final_scores["Material"],
        "occasion": final_scores["Occasion"],
        "aesthetic": final_scores["Aesthetic"],
        "budget": final_scores["Budget"],
        "persona": persona,
        "recommendations": recommendations,
    }
def assign_persona(scores):
    style    = scores.get('style_score', 0)
    material = scores.get('material_score', 0)
    occasion = scores.get('occasion_score', 0)
    budget   = scores.get('budget_score', 0)

    if occasion > 0.7 and material > 0.6:
        return "Traditional Bridal Buyer"
    elif style < 0.4 and budget < 0.5:
        return "Minimalist Daily Wearer"
    elif style > 0.7 and budget < 0.5:
        return "Fashion-Forward Budget Buyer"
    elif budget > 0.7:
        return "Luxury Investment Buyer"
    else:
        return "Casual Trendy Buyer"