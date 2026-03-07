from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Research Impact Co-Pilot (RIC)",
    description="Helps researchers understand and amplify their paper's impact.",
    version="0.1.0",
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
        "version": "0.1",
        "message": "Haseeb's Research Impact Co-Pilot is running! 🔬"
    }

@app.get("/")
def root():
    return {
        "app": "Research Impact Co-Pilot",
        "docs": "/docs",
        "hello": "/hello"
    }
    # backend/app/main.py
# -----------------------------------------------
# Main FastAPI application file.
# This is where all our URL endpoints live.
# -----------------------------------------------

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import AnalyzeRequest, AnalyzeResponse
from backend.app.services.analyzer import (
    extract_keywords,
    calculate_impact_score,
    get_impact_label,
    suggest_title
)

# Create the FastAPI app
app = FastAPI(
    title="Research Impact Co-Pilot (RIC)",
    description="Helps researchers understand and amplify their paper's impact.",
    version="0.1.0",
)

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------
# ROUTE: /hello
# Health check — confirms server is running
# -----------------------------------------------
@app.get("/hello")
def hello():
    return {
        "status": "RIC hello",
        "version": "0.1",
        "message": "Haseeb's Research Impact Co-Pilot is live! 🔬"
    }


# -----------------------------------------------
# ROUTE: /
# Root path
# -----------------------------------------------
@app.get("/")
def root():
    return {
        "app": "Research Impact Co-Pilot",
        "docs": "/docs",
        "analyze": "/analyze"
    }


# -----------------------------------------------
# ROUTE: /analyze  (THE MAIN FEATURE)
# Accepts a paper title + abstract as JSON input.
# Returns keywords, impact score, and title suggestion.
#
# HTTP POST means we are SENDING data to the server
# (unlike GET which just fetches data).
# -----------------------------------------------
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_paper(request: AnalyzeRequest):
    """
    Analyze a research paper and return impact insights.

    Input JSON example:
    {
        "title": "Enhanced Solubility of Docetaxel Using Cyclodextrin",
        "abstract": "This study investigates..."
    }
    """

    # Basic validation — make sure inputs are not empty
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    if not request.abstract.strip():
        raise HTTPException(status_code=400, detail="Abstract cannot be empty.")
    if len(request.abstract.split()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Abstract is too short. Please provide at least 10 words."
        )

    # Step 1: Extract keywords from the abstract
    keywords = extract_keywords(request.abstract)

    # Step 2: Calculate the impact score
    score = calculate_impact_score(request.title, request.abstract)

    # Step 3: Get human-readable label
    label = get_impact_label(score)

    # Step 4: Suggest an improved title
    new_title = suggest_title(request.title, keywords)

    # Step 5: Count words in abstract
    word_count = len(request.abstract.split())

    # Step 6: Build a helpful message
    message = (
        f"Your paper scored {score}/10 ({label} impact potential). "
        f"The abstract contains {word_count} words. "
        f"Top keywords suggest focus on: {', '.join(keywords[:3])}."
    )

    # Return everything as a structured response
    return AnalyzeResponse(
        impact_score=score,
        impact_label=label,
        top_keywords=keywords,
        suggested_title=new_title,
        word_count=word_count,
        message=message
    )
