# backend/app/services/openalex.py
# -----------------------------------------------
# OpenAlex API integration.
# Handles:
#   1. fetch_researcher_metadata — author h-index, citations etc
#   2. fetch_keyword_gap — THE CORE FEATURE
#      Queries top 20 cited papers in the user's field.
#      Extracts concepts from those papers.
#      Compares against the user's abstract.
#      Returns what's MISSING — with real citation data.
#   3. get_journals_for_field — dynamic journal recommendations
# -----------------------------------------------

import httpx
from typing import Optional, List, Tuple

OPENALEX_BASE = "https://api.openalex.org"
POLITE_EMAIL = "ric-app@haseebbuilds.com"

# Concepts too broad/generic to be useful as gap keywords
# We filter these out so we only show meaningful academic concepts
GENERIC_CONCEPTS = {
    "research", "science", "medicine", "chemistry", "biology", "physics",
    "engineering", "technology", "study", "analysis", "method", "review",
    "management", "social science", "economics", "mathematics", "statistics",
    "computer science", "materials science", "psychology", "education",
    "art", "history", "philosophy", "literature", "language", "nursing",
    "surgery", "internal medicine", "general medicine", "biochemistry"
}

# -----------------------------------------------
# JOURNAL DATABASE
# Curated journals per research field.
# These are shown dynamically based on detected_field.
# -----------------------------------------------
JOURNALS_BY_FIELD = {
    "pharma": [
        {
            "name": "Journal of Pharmaceutical Sciences",
            "meta": "Drug delivery · Formulation · Solubility",
            "if_score": "IF 3.7",
            "url": "https://www.sciencedirect.com/journal/journal-of-pharmaceutical-sciences"
        },
        {
            "name": "European Journal of Pharmaceutics and Biopharmaceutics",
            "meta": "Biopharmaceutics · Drug release · Cyclodextrin",
            "if_score": "IF 4.4",
            "url": "https://www.sciencedirect.com/journal/european-journal-of-pharmaceutics-and-biopharmaceutics"
        },
        {
            "name": "International Journal of Pharmaceutics",
            "meta": "Formulation science · Dissolution · Drug delivery systems",
            "if_score": "IF 5.3",
            "url": "https://www.sciencedirect.com/journal/international-journal-of-pharmaceutics"
        }
    ],
    "medicine": [
        {
            "name": "PLOS Medicine",
            "meta": "Clinical research · Public health · Evidence-based medicine",
            "if_score": "IF 15.8",
            "url": "https://journals.plos.org/plosmedicine/"
        },
        {
            "name": "BMC Medicine",
            "meta": "Clinical trials · Translational medicine · Health outcomes",
            "if_score": "IF 9.3",
            "url": "https://bmcmedicine.biomedcentral.com/"
        },
        {
            "name": "Journal of Clinical Medicine",
            "meta": "Clinical practice · Diagnostics · Treatment outcomes",
            "if_score": "IF 3.9",
            "url": "https://www.mdpi.com/journal/jcm"
        }
    ],
    "cs": [
        {
            "name": "IEEE Transactions on Neural Networks and Learning Systems",
            "meta": "Machine learning · Deep learning · Neural networks",
            "if_score": "IF 10.4",
            "url": "https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=5962385"
        },
        {
            "name": "Pattern Recognition",
            "meta": "Computer vision · Image processing · AI",
            "if_score": "IF 7.7",
            "url": "https://www.sciencedirect.com/journal/pattern-recognition"
        },
        {
            "name": "Expert Systems with Applications",
            "meta": "Applied AI · Data mining · Intelligent systems",
            "if_score": "IF 8.5",
            "url": "https://www.sciencedirect.com/journal/expert-systems-with-applications"
        }
    ],
    "biology": [
        {
            "name": "PLOS Biology",
            "meta": "Molecular biology · Cell biology · Genetics",
            "if_score": "IF 9.8",
            "url": "https://journals.plos.org/plosbiology/"
        },
        {
            "name": "BMC Biology",
            "meta": "Evolutionary biology · Systems biology · Genomics",
            "if_score": "IF 4.4",
            "url": "https://bmcbiol.biomedcentral.com/"
        },
        {
            "name": "Frontiers in Molecular Biosciences",
            "meta": "Biochemistry · Structural biology · Proteomics",
            "if_score": "IF 3.9",
            "url": "https://www.frontiersin.org/journals/molecular-biosciences"
        }
    ],
    "engineering": [
        {
            "name": "Engineering Applications of Artificial Intelligence",
            "meta": "Applied engineering · AI systems · Automation",
            "if_score": "IF 8.0",
            "url": "https://www.sciencedirect.com/journal/engineering-applications-of-artificial-intelligence"
        },
        {
            "name": "Journal of Cleaner Production",
            "meta": "Sustainable engineering · Environmental · Systems",
            "if_score": "IF 11.1",
            "url": "https://www.sciencedirect.com/journal/journal-of-cleaner-production"
        },
        {
            "name": "Applied Sciences",
            "meta": "Applied engineering · Materials · Processes",
            "if_score": "IF 2.7",
            "url": "https://www.mdpi.com/journal/applsci"
        }
    ],
    "environment": [
        {
            "name": "Environmental Science & Technology",
            "meta": "Pollution · Water quality · Environmental chemistry",
            "if_score": "IF 11.4",
            "url": "https://pubs.acs.org/journal/esthag"
        },
        {
            "name": "Science of The Total Environment",
            "meta": "Environmental monitoring · Ecosystem · Climate",
            "if_score": "IF 9.8",
            "url": "https://www.sciencedirect.com/journal/science-of-the-total-environment"
        },
        {
            "name": "Environmental Research",
            "meta": "Health-environment · Toxicology · Pollution",
            "if_score": "IF 8.3",
            "url": "https://www.sciencedirect.com/journal/environmental-research"
        }
    ],
    "default": [
        {
            "name": "PLOS ONE",
            "meta": "Multidisciplinary · Open access · All fields of research",
            "if_score": "IF 3.7",
            "url": "https://journals.plos.org/plosone/"
        },
        {
            "name": "Scientific Reports",
            "meta": "Natural sciences · Technology · Medicine",
            "if_score": "IF 4.6",
            "url": "https://www.nature.com/srep/"
        },
        {
            "name": "Frontiers in Research Metrics and Analytics",
            "meta": "Research impact · Bibliometrics · Open science",
            "if_score": "IF 2.1",
            "url": "https://www.frontiersin.org/journals/research-metrics-and-analytics"
        }
    ]
}


def detect_field_category(keywords: List[str], concept_names: List[str]) -> str:
    """
    Detect research field from user's keywords and OpenAlex concept names.
    Returns: pharma | cs | medicine | biology | engineering | environment | default
    """
    all_terms = " ".join(keywords + concept_names).lower()

    field_terms = {
        "pharma": [
            "drug", "pharmaceutical", "cyclodextrin", "bioavailability",
            "dissolution", "tablet", "capsule", "dosage", "pharmacokinetic",
            "solubility", "formulation", "excipient", "nanoparticle",
            "liposome", "therapeutic", "pharmacology", "oral delivery",
            "encapsulation", "complexation", "drug release"
        ],
        "cs": [
            "machine learning", "deep learning", "neural network", "algorithm",
            "computer vision", "natural language", "reinforcement learning",
            "classification", "clustering", "optimization", "dataset",
            "convolutional", "transformer", "attention mechanism", "nlp"
        ],
        "medicine": [
            "clinical", "patient", "hospital", "disease", "treatment",
            "diagnosis", "therapy", "randomized", "trial", "cohort",
            "epidemiology", "mortality", "surgery", "cancer", "tumor",
            "cardiovascular", "diabetes", "infection", "vaccine", "prevalence"
        ],
        "biology": [
            "protein", "gene", "cell", "molecular", "dna", "rna",
            "enzyme", "bacteria", "virus", "genome", "metabol",
            "chromosome", "receptor", "antibody", "mutation", "sequencing",
            "transcription", "expression", "pathway", "signaling"
        ],
        "engineering": [
            "structural", "mechanical", "electrical", "thermal", "fluid",
            "composite", "alloy", "manufacturing", "fabrication", "tensile",
            "compressive", "finite element", "simulation", "modelling"
        ],
        "environment": [
            "environment", "pollution", "water", "soil", "air quality",
            "ecosystem", "climate", "carbon", "emission", "waste",
            "sustainable", "biodiversity", "contamination", "groundwater",
            "heavy metal", "remediation", "greenhouse"
        ]
    }

    scores = {
        field: sum(1 for term in terms if term in all_terms)
        for field, terms in field_terms.items()
    }

    best_field = max(scores, key=scores.get)
    return best_field if scores[best_field] > 0 else "default"


def get_journals_for_field(field: str) -> List[dict]:
    """Return the curated journal list for a detected field."""
    return JOURNALS_BY_FIELD.get(field, JOURNALS_BY_FIELD["default"])


async def fetch_keyword_gap(
    abstract: str,
    keywords: List[str]
) -> Tuple[List[dict], str]:
    """
    THE CORE FEATURE.

    Queries OpenAlex for the top 20 most-cited papers matching
    the user's research area. Extracts real concepts from those
    papers. Compares against the user's abstract. Returns what's
    MISSING — with real citation data behind each keyword.

    This is what makes the tool irreplaceable. No free tool does this.

    Returns:
        gap_keywords: List of dicts with keyword, avg_citations,
                      found_in_top_papers, in_your_abstract
        detected_field: str — used for journal matching
    """
    if not keywords:
        return [], "default"

    abstract_lower = abstract.lower()

    # Search OpenAlex for top cited papers matching these keywords
    search_query = " ".join(keywords[:3])
    url = f"{OPENALEX_BASE}/works"
    params = {
        "search": search_query,
        "sort": "cited_by_count:desc",
        "per_page": 20,
        "filter": "cited_by_count:>50",   # Only papers with real citation traction
        "mailto": POLITE_EMAIL
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                return [], "default"
            data = response.json()
            papers = data.get("results", [])
    except Exception:
        return [], "default"

    if not papers:
        return [], "default"

    # Aggregate concept data across all 20 papers
    # concept_name -> { count: how many papers had it, total_citations: sum }
    concept_data: dict = {}
    all_concept_names: List[str] = []

    for paper in papers:
        paper_citations = paper.get("cited_by_count", 0)
        paper_concepts = paper.get("concepts", [])

        for concept in paper_concepts:
            # score < 0.3 = weak/tangential relation to this paper — skip
            if concept.get("score", 0) < 0.3:
                continue

            name = concept.get("display_name", "").lower().strip()

            if not name or len(name) < 4:
                continue
            if name in GENERIC_CONCEPTS:
                continue

            all_concept_names.append(name)

            if name not in concept_data:
                concept_data[name] = {"count": 0, "total_citations": 0}
            concept_data[name]["count"] += 1
            concept_data[name]["total_citations"] += paper_citations

    # Detect field from the most common concepts in those top papers
    top_concept_names = sorted(
        concept_data.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )
    top_names = [c[0] for c in top_concept_names[:15]]
    detected_field = detect_field_category(keywords, top_names)

    # Build the gap keyword list
    gap_keywords = []
    for name, stats in concept_data.items():
        # Must appear in at least 2 of top 20 papers to be meaningful
        if stats["count"] < 2:
            continue

        in_abstract = name in abstract_lower
        avg_citations = int(stats["total_citations"] / stats["count"])

        gap_keywords.append({
            "keyword": name,
            "avg_citations": avg_citations,
            "found_in_top_papers": stats["count"],
            "in_your_abstract": in_abstract
        })

    # Sort: missing from abstract first (highest priority),
    # then by how often they appear in top papers
    gap_keywords.sort(
        key=lambda x: (not x["in_your_abstract"], x["found_in_top_papers"]),
        reverse=True
    )

    # Return top 10
    return gap_keywords[:10], detected_field


async def fetch_researcher_metadata(scholar_url: str) -> Optional[dict]:
    """
    Fetch researcher profile from OpenAlex.
    Supports ORCID URLs and name search.
    """
    if not scholar_url:
        return None

    if "orcid.org" in scholar_url:
        orcid_id = scholar_url.strip("/").split("/")[-1]
        url = f"{OPENALEX_BASE}/authors"
        params = {"filter": f"orcid:{orcid_id}", "mailto": POLITE_EMAIL}
    elif not scholar_url.startswith("http"):
        url = f"{OPENALEX_BASE}/authors"
        params = {"search": scholar_url, "per_page": 1, "mailto": POLITE_EMAIL}
    else:
        return {
            "name": "Unknown", "citation_count": 0, "h_index": 0,
            "works_count": 0, "institution": "Unknown", "openalex_id": "",
            "note": "Please enter your name or ORCID URL instead of a Google Scholar link."
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                return None
            data = response.json()
            results = data.get("results", [])
            if not results:
                return None
            author = results[0]
            summary = author.get("summary_stats", {})
            affiliations = author.get("affiliations", [])
            institution = "Unknown"
            if affiliations:
                inst = affiliations[0].get("institution", {})
                institution = inst.get("display_name", "Unknown")
            return {
                "name": author.get("display_name", "Unknown"),
                "citation_count": author.get("cited_by_count", 0),
                "h_index": summary.get("h_index", 0),
                "works_count": author.get("works_count", 0),
                "institution": institution,
                "openalex_id": author.get("id", "")
            }
    except Exception:
        return None