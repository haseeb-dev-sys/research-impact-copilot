import httpx
from typing import Optional

OPENALEX_BASE = "https://api.openalex.org"
POLITE_EMAIL = "ric-app@haseebbuilds.com"

async def fetch_researcher_metadata(scholar_url: str) -> Optional[dict]:
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
        return {"name": "Unknown", "citation_count": 0, "h_index": 0, "works_count": 0, "institution": "Unknown", "openalex_id": "", "note": "Please enter your name or ORCID URL instead of a Google Scholar link."}
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
            return {"name": author.get("display_name", "Unknown"), "citation_count": author.get("cited_by_count", 0), "h_index": summary.get("h_index", 0), "works_count": author.get("works_count", 0), "institution": institution, "openalex_id": author.get("id", "")}
    except Exception:
        return None
