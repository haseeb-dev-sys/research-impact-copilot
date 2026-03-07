from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import AnalyzeRequest, AnalyzeResponse, ResearcherMetadata
from backend.app.services.analyzer import (
    extract_keywords,
    calculate_impact_score,
    get_impact_label,
    suggest_title
)
from backend.app.services.openalex import fetch_researcher_metadata

app = FastAPI(
    title="Research Impact Co-Pilot (RIC)",
    description="Helps researchers understand and amplify their paper's impact.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def hello():
    return {
        "status": "RIC hello",
        "version": "0.2",
        "message": "Haseeb's Research Impact Co-Pilot is live! 🔬"
    }

@app.get("/")
def root():
    return {
        "app": "Research Impact Co-Pilot",
        "docs": "/docs",
        "analyze": "/analyze"
    }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_paper(request: AnalyzeRequest):
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    if not request.abstract.strip():
        raise HTTPException(status_code=400, detail="Abstract cannot be empty.")
    if len(request.abstract.split()) < 10:
        raise HTTPException(status_code=400, detail="Abstract is too short. Please provide at least 10 words.")

    keywords = extract_keywords(request.abstract)
    score = calculate_impact_score(request.title, request.abstract)
    label = get_impact_label(score)
    new_title = suggest_title(request.title, keywords)
    word_count = len(request.abstract.split())

    researcher = None
    if request.scholar_url and request.scholar_url.strip():
        raw_metadata = await fetch_researcher_metadata(request.scholar_url.strip())
        if raw_metadata:
            researcher = ResearcherMetadata(**raw_metadata)

    message = (
        f"Your paper scored {score}/10 ({label} impact potential). "
        f"The abstract contains {word_count} words. "
        f"Top keywords suggest focus on: {', '.join(keywords[:3])}."
    )

    return AnalyzeResponse(
        impact_score=score,
        impact_label=label,
        top_keywords=keywords,
        suggested_title=new_title,
        word_count=word_count,
        message=message,
        researcher=researcher
    )