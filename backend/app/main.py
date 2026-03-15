# backend/app/main.py
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import AnalyzeRequest, AnalyzeResponse, ResearcherMetadata, Action, GapKeyword
from backend.app.services.analyzer import extract_keywords, calculate_impact_score, get_impact_label, suggest_title
from backend.app.services.openalex import fetch_researcher_metadata, fetch_keyword_gap, get_journals_for_field
from backend.app.services.action_pack import generate_action_pack

app = FastAPI(title="Research Impact Co-Pilot (RIC)", version="0.4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/hello")
def hello():
    return {"status": "RIC hello", "version": "0.4", "message": "RIC v0.4 — now with real keyword gap analysis"}


@app.get("/")
def root():
    return {"app": "Research Impact Co-Pilot", "docs": "/docs"}


@app.post("/analyze")
async def analyze_paper(request: AnalyzeRequest):
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    if not request.abstract.strip():
        raise HTTPException(status_code=400, detail="Abstract cannot be empty.")
    if len(request.abstract.split()) < 10:
        raise HTTPException(status_code=400, detail="Abstract is too short.")

    # ── Step 1: Local analysis — instant, no API ──
    keywords = extract_keywords(request.abstract)
    score, breakdown = calculate_impact_score(request.title, request.abstract)
    label = get_impact_label(score)
    word_count = len(request.abstract.split())
    scholar_url = request.scholar_url.strip() if request.scholar_url else None

    # ── Step 2: Run OpenAlex calls in PARALLEL ──
    # This saves 2–4 seconds vs running them sequentially.
    # fetch_keyword_gap and fetch_researcher_metadata run at the same time.
    if scholar_url:
        (gap_keywords_raw, detected_field), raw_metadata = await asyncio.gather(
            fetch_keyword_gap(request.abstract, keywords),
            fetch_researcher_metadata(scholar_url)
        )
    else:
        gap_keywords_raw, detected_field = await fetch_keyword_gap(request.abstract, keywords)
        raw_metadata = None

    # ── Step 3: Build optimized title using REAL gap keywords ──
    # Now suggest_title has OpenAlex data — it picks keywords that
    # top-cited papers in their field actually use.
    new_title = suggest_title(request.title, keywords, gap_keywords_raw)

    # ── Step 4: Process researcher metadata ──
    researcher = None
    if raw_metadata:
        researcher = ResearcherMetadata(**raw_metadata)

    # ── Step 5: Convert gap keywords to Pydantic models ──
    gap_keywords = [GapKeyword(**gk) for gk in gap_keywords_raw] if gap_keywords_raw else []

    # ── Step 6: Get journal recommendations for detected field ──
    # Dynamic — a pharma researcher gets pharma journals,
    # a CS researcher gets CS journals, etc.
    journals = get_journals_for_field(detected_field)

    # ── Step 7: Generate action pack ──
    raw_actions = generate_action_pack(
        title=request.title,
        abstract=request.abstract,
        keywords=keywords,
        impact_score=score,
        impact_label=label,
        suggested_title=new_title,
        researcher_name=researcher.name if researcher else None,
        citation_count=researcher.citation_count if researcher else 0,
        h_index=researcher.h_index if researcher else 0,
    )
    actions = [Action(**a) for a in raw_actions]

    # ── Step 8: Build response message ──
    missing_count = sum(1 for gk in gap_keywords if not gk.in_your_abstract)
    if missing_count > 0:
        message = (
            f"Your paper scored {score}/10 ({label} discoverability). "
            f"We found {missing_count} high-citation keywords used by top papers in your field "
            f"that are missing from your abstract. Adding these could significantly "
            f"improve your paper's visibility and citation count."
        )
    else:
        message = (
            f"Your paper scored {score}/10 ({label} discoverability). "
            f"Your abstract already contains the main keywords used by top papers in your field. "
            f"Focus on title optimization and journal selection to maximize citations."
        )

    response = AnalyzeResponse(
        impact_score=score,
        impact_label=label,
        top_keywords=keywords,
        gap_keywords=gap_keywords,
        detected_field=detected_field,
        suggested_title=new_title,
        word_count=word_count,
        message=message,
        score_breakdown=breakdown,
        researcher=researcher,
        actions=actions
    )
    return response