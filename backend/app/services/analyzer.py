# backend/app/services/analyzer.py
# -----------------------------------------------
# This is the "brain" of RIC.
# It contains pure Python functions that:
# 1. Extract keywords from an abstract
# 2. Calculate an impact score
# 3. Suggest an improved title
# No external APIs needed — runs fully offline.
# -----------------------------------------------

import re
from typing import List


# -----------------------------------------------
# STOP WORDS
# These are common English words we IGNORE when
# extracting keywords. Words like "the", "and",
# "this" tell us nothing about the paper's topic.
# -----------------------------------------------
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

# -----------------------------------------------
# ACADEMIC POWER WORDS
# These words suggest a paper has strong impact
# potential. We boost the score if we find them.
# -----------------------------------------------
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
    Extract the most meaningful words from a text.

    How it works:
    1. Convert text to lowercase
    2. Split into individual words
    3. Remove stop words and short words
    4. Count how often each word appears
    5. Return the top N most frequent words

    Args:
        text: The abstract text to analyze
        top_n: How many keywords to return (default 6)

    Returns:
        A list of keyword strings
    """
    # Convert to lowercase and extract only real words (no punctuation)
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())

    # Remove stop words
    filtered = [w for w in words if w not in STOP_WORDS]

    # Count word frequency using a simple dictionary
    frequency = {}
    for word in filtered:
        frequency[word] = frequency.get(word, 0) + 1

    # Sort by frequency (most common first) and return top N
    sorted_words = sorted(frequency.items(), key=lambda x: x[1], reverse=True)

    # Return just the words, not the counts
    return [word for word, count in sorted_words[:top_n]]


def calculate_impact_score(title: str, abstract: str) -> float:
    """
    Calculate a simple heuristic impact score from 0.0 to 10.0.

    This is NOT a real citation predictor — it's a heuristic
    (a smart estimate) based on known patterns in high-impact papers.

    Scoring factors:
    - Abstract length (longer = more detailed = slightly better)
    - Presence of power words (novel, clinical, significant, etc.)
    - Title length (too short or too long = penalty)

    Args:
        title: Paper title
        abstract: Paper abstract

    Returns:
        A float score between 0.0 and 10.0
    """
    score = 0.0
    abstract_lower = abstract.lower()
    title_lower = title.lower()

    # Factor 1: Abstract length (ideal is 150-300 words)
    word_count = len(abstract.split())
    if word_count >= 150:
        score += 2.0
    elif word_count >= 100:
        score += 1.5
    elif word_count >= 50:
        score += 1.0
    else:
        score += 0.5

    # Factor 2: Power words in abstract (up to 4 points)
    power_word_hits = sum(1 for pw in POWER_WORDS if pw in abstract_lower)
    score += min(power_word_hits * 0.5, 4.0)

    # Factor 3: Power words in title (up to 2 points)
    title_power_hits = sum(1 for pw in POWER_WORDS if pw in title_lower)
    score += min(title_power_hits * 0.5, 2.0)

    # Factor 4: Title length (ideal is 8-15 words)
    title_words = len(title.split())
    if 8 <= title_words <= 15:
        score += 2.0
    elif 5 <= title_words <= 20:
        score += 1.0

    # Cap the score at 10.0
    return round(min(score, 10.0), 1)


def get_impact_label(score: float) -> str:
    """
    Convert a numeric score into a human-readable label.
    """
    if score >= 7.0:
        return "High"
    elif score >= 4.0:
        return "Medium"
    else:
        return "Low"


def suggest_title(title: str, keywords: List[str]) -> str:
    """
    Suggest an improved title by weaving in top keywords.

    Simple heuristic approach:
    - If the title is short (under 6 words), expand it with keywords
    - If the title is long, return a focused version
    - Always try to include the top 2 keywords

    Args:
        title: Original paper title
        keywords: Extracted keywords list

    Returns:
        A suggested improved title string
    """
    title_words = title.split()
    top_two = keywords[:2] if len(keywords) >= 2 else keywords

    # Check which keywords are already in the title
    title_lower = title.lower()
    missing_keywords = [kw for kw in top_two if kw not in title_lower]

    if not missing_keywords:
        # Title already contains top keywords — just polish it
        return f"{title}: A Comprehensive Study"

    if len(title_words) < 6:
        # Title is too short — expand it
        keyword_phrase = " and ".join(missing_keywords)
        return f"{title}: Role of {keyword_phrase.title()} and Its Implications"

    # Title is good length — suggest adding focus keyword
    focus = missing_keywords[0].title()
    return f"{title} with Enhanced {focus}-Based Approach"
