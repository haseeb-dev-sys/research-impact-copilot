# backend/app/services/analyzer.py
# -----------------------------------------------
# Local analysis functions — no API needed.
# 1. extract_keywords   — from abstract
# 2. calculate_impact_score — heuristic score
# 3. get_impact_label   — High / Medium / Low
# 4. suggest_title      — UPDATED: uses real gap
#                         keywords from OpenAlex
# -----------------------------------------------

import re
from typing import List, Optional


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "this", "that", "these", "those",
    "it", "its", "we", "our", "their", "they", "he", "she", "as", "into",
    "also", "than", "then", "so", "such", "both", "each", "not", "no",
    "can", "use", "used", "using", "show", "shows", "showed", "result",
    "results", "study", "studies", "paper", "research", "method", "methods",
    "data", "based", "between", "which", "while", "within", "among",
    "however", "therefore", "thus", "were", "there", "here", "when",
    "where", "how", "what", "all", "more", "one", "two", "three", "new",
    "high", "low", "large", "small", "different", "significant", "present"
}

POWER_WORDS = {
    "novel", "innovative", "significant", "breakthrough", "first",
    "unique", "improved", "enhanced", "superior", "optimal", "effective",
    "efficient", "accurate", "robust", "scalable", "validated",
    "clinical", "therapy", "treatment", "cancer", "drug", "disease",
    "patient", "bioavailability", "solubility", "nanoparticle",
    "machine learning", "deep learning", "artificial intelligence",
    "systematic", "meta-analysis", "randomized", "controlled"
}


def extract_keywords(text: str, top_n: int = 6) -> List[str]:
    """
    Extract most meaningful words from abstract text.
    Used as the initial keyword set before OpenAlex gap analysis.
    """
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]

    frequency = {}
    for word in filtered:
        frequency[word] = frequency.get(word, 0) + 1

    sorted_words = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:top_n]]


def calculate_impact_score(title: str, abstract: str) -> tuple:
    """
    Heuristic discoverability score from 0.0 to 10.0.
    Returns (score, breakdown_dict).
    """
    score = 0.0
    breakdown = {}
    abstract_lower = abstract.lower()
    title_lower = title.lower()

    # Factor 1: Abstract length
    word_count = len(abstract.split())
    if word_count >= 150:
        score += 2.0
        breakdown["Abstract Length"] = f"+2.0 ({word_count} words — ideal)"
    elif word_count >= 100:
        score += 1.5
        breakdown["Abstract Length"] = f"+1.5 ({word_count} words — good)"
    elif word_count >= 50:
        score += 1.0
        breakdown["Abstract Length"] = f"+1.0 ({word_count} words — short)"
    else:
        score += 0.5
        breakdown["Abstract Length"] = f"+0.5 ({word_count} words — too short)"

    # Factor 2: Power words in abstract
    power_hits = sum(1 for pw in POWER_WORDS if pw in abstract_lower)
    abstract_points = round(min(power_hits * 0.5, 4.0), 1)
    score += abstract_points
    breakdown["Impact Words in Abstract"] = (
        f"+{abstract_points} ({power_hits} words like 'novel', 'validated', 'bioavailability')"
    )

    # Factor 3: Power words in title
    title_hits = sum(1 for pw in POWER_WORDS if pw in title_lower)
    title_points = round(min(title_hits * 0.5, 2.0), 1)
    score += title_points
    breakdown["Impact Words in Title"] = (
        f"+{title_points} ({title_hits} impact words found in title)"
    )

    # Factor 4: Title length — ideal is 8–15 words
    title_word_count = len(title.split())
    if 8 <= title_word_count <= 15:
        score += 2.0
        breakdown["Title Length"] = f"+2.0 ({title_word_count} words — ideal)"
    elif 5 <= title_word_count <= 20:
        score += 1.0
        breakdown["Title Length"] = f"+1.0 ({title_word_count} words — acceptable)"
    else:
        breakdown["Title Length"] = f"+0.0 ({title_word_count} words — too short or long)"

    return round(min(score, 10.0), 1), breakdown


def get_impact_label(score: float) -> str:
    if score >= 7.0:
        return "High"
    elif score >= 4.0:
        return "Medium"
    else:
        return "Low"


def suggest_title(
    title: str,
    keywords: List[str],
    gap_keywords: Optional[List[dict]] = None
) -> str:
    """
    Suggest an improved title using real gap keywords from OpenAlex.

    Priority order:
    1. Use gap keywords missing from the abstract (highest value — these are
       keywords top-cited papers in their field use that they don't have)
    2. Fall back to extracted keywords if no gap data available

    Args:
        title: Original paper title
        keywords: Extracted keywords from abstract
        gap_keywords: Real citation-backed keywords from OpenAlex (optional)

    Returns:
        Improved title string with high-citation keywords incorporated
    """
    title_lower = title.lower()

    # ── Priority 1: Use real gap keywords from OpenAlex ──
    if gap_keywords:
        # Find keywords missing from both title and abstract — highest priority
        missing_gap = [
            gk["keyword"] for gk in gap_keywords
            if not gk["in_your_abstract"] and gk["keyword"] not in title_lower
        ][:2]

        if len(missing_gap) >= 2:
            k1 = missing_gap[0].title()
            k2 = missing_gap[1].title()
            return f"{title}: Implications for {k1} and {k2}"

        if len(missing_gap) == 1:
            k1 = missing_gap[0].title()
            return f"{title}: A {k1}-Focused Approach"

        # All top gap keywords are already in the abstract — suggest a structural rewrite
        present_gap = [
            gk["keyword"] for gk in gap_keywords
            if gk["in_your_abstract"] and gk["keyword"] not in title_lower
        ][:1]

        if present_gap:
            k1 = present_gap[0].title()
            return f"{title}: Role of {k1} and Clinical Implications"

    # ── Priority 2: Fall back to extracted keywords ──
    title_words = title.split()
    top_two = keywords[:2] if len(keywords) >= 2 else keywords
    missing_keywords = [kw for kw in top_two if kw not in title_lower]

    if not missing_keywords:
        return f"{title}: A Comprehensive Analysis"

    if len(title_words) < 6:
        keyword_phrase = " and ".join(missing_keywords)
        return f"{title}: Role of {keyword_phrase.title()} and Its Implications"

    focus = missing_keywords[0].title()
    return f"{title} with Enhanced {focus}-Based Approach"