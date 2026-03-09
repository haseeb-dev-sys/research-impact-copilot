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


class AnalyzeResponse(BaseModel):
    impact_score: float
    impact_label: str
    top_keywords: List[str]
    suggested_title: str
    word_count: int
    message: str
    score_breakdown: Optional[dict] = None
    researcher: Optional[ResearcherMetadata] = None
    actions: Optional[List[Action]] = None