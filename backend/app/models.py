# backend/app/models.py
from pydantic import BaseModel
from typing import Optional, List


class AnalyzeRequest(BaseModel):
    title: str
    abstract: str
    scholar_url: Optional[str] = None


class ResearcherMetadata(BaseModel):
    name: str = "Unknown"
    citation_count: int = 0
    h_index: int = 0
    works_count: int = 0
    institution: str = "Unknown"
    openalex_id: str = ""
    note: Optional[str] = None


class Action(BaseModel):
    number: int
    title: str
    description: str
    time_estimate: str
    difficulty: str
    confidence: str
    template: str


class GapKeyword(BaseModel):
    """
    A keyword found in top-cited papers in the user's field.
    in_your_abstract = False means it's MISSING from their paper — that's the gold.
    """
    keyword: str
    avg_citations: int          # Average citations of papers containing this keyword
    found_in_top_papers: int    # How many of the top 20 papers contain this keyword
    in_your_abstract: bool      # Is this keyword already in their abstract?


class AnalyzeResponse(BaseModel):
    impact_score: float
    impact_label: str
    top_keywords: List[str]
    gap_keywords: Optional[List[GapKeyword]] = None   # NEW — real citation-backed keywords
    detected_field: Optional[str] = None              # NEW — pharma / cs / medicine / etc
    suggested_title: str
    word_count: int
    message: str
    score_breakdown: Optional[dict] = None
    researcher: Optional[ResearcherMetadata] = None
    actions: Optional[List[Action]] = None