# backend/app/services/action_pack.py
# -----------------------------------------------
# This file generates the Action Pack —
# 3 prioritized actions a researcher can take
# to improve their paper's impact.
#
# Each action has:
# - title: what to do
# - description: how to do it
# - time_estimate: how long it takes
# - difficulty: low / medium / high
# - confidence: how confident we are it will help
# - template: a ready-to-use text they can copy
# -----------------------------------------------

from typing import List, Optional


def generate_action_pack(
    title: str,
    abstract: str,
    keywords: List[str],
    impact_score: float,
    impact_label: str,
    suggested_title: str,
    researcher_name: Optional[str] = None,
    citation_count: int = 0,
    h_index: int = 0,
) -> List[dict]:
    """
    Generate 3 prioritized actions based on paper analysis.

    The actions are always in this order:
    1. Title/keyword optimization (quickest win)
    2. Outreach email template (medium effort)
    3. Promotion plan (longer term)

    Returns a list of 3 action dictionaries.
    """

    actions = []
    top_keywords = keywords[:3] if len(keywords) >= 3 else keywords
    keyword_str = ", ".join(top_keywords)
    name = researcher_name or "Researcher"

    # -----------------------------------------------
    # ACTION 1: Title & Keyword Optimization
    # Always first — highest ROI, lowest effort
    # -----------------------------------------------
    if impact_score < 5.0:
        title_confidence = "High"
        title_description = (
            f"Your current title has low keyword visibility. "
            f"Replacing or reordering words to include '{top_keywords[0] if top_keywords else 'key terms'}' "
            f"in the first 8 words significantly improves discoverability in academic search engines."
        )
    elif impact_score < 7.0:
        title_confidence = "Medium"
        title_description = (
            f"Your title is decent but could be more specific. "
            f"Adding terms like '{top_keywords[0] if top_keywords else 'key terms'}' "
            f"will help researchers in your field find your work more easily."
        )
    else:
        title_confidence = "Medium"
        title_description = (
            f"Your title is strong. Consider adding a subtitle that includes "
            f"'{keyword_str}' to capture broader search queries."
        )

    actions.append({
        "number": 1,
        "title": "Optimize Your Title & Keywords",
        "description": title_description,
        "time_estimate": "30 minutes",
        "difficulty": "Low",
        "confidence": title_confidence,
        "template": f"""SUGGESTED TITLE:
{suggested_title}

TOP KEYWORDS TO USE IN YOUR ABSTRACT & METADATA:
{chr(10).join(f'• {kw}' for kw in keywords[:6])}

WHERE TO ADD THESE KEYWORDS:
• Paper title (most important)
• Abstract first sentence
• Journal submission keywords field
• ResearchGate / Academia.edu profile tags"""
    })

    # -----------------------------------------------
    # ACTION 2: Outreach Email Template
    # Medium effort, high potential reward
    # -----------------------------------------------
    if citation_count < 10:
        outreach_confidence = "High"
        outreach_note = "Since your citation count is low, direct outreach to active researchers in your field is one of the fastest ways to get your first citations."
    elif citation_count < 50:
        outreach_confidence = "High"
        outreach_note = "You have some citations already. Targeted outreach to researchers who work on related problems can accelerate your growth significantly."
    else:
        outreach_confidence = "Medium"
        outreach_note = "With your citation base, outreach to international collaborators can open new research directions and cross-citations."

    actions.append({
        "number": 2,
        "title": "Send 5 Targeted Outreach Emails",
        "description": (
            f"Identify 5 researchers who have recently published on {keyword_str}. "
            f"Send a short, specific email sharing your paper. "
            f"{outreach_note}"
        ),
        "time_estimate": "1-2 hours",
        "difficulty": "Medium",
        "confidence": outreach_confidence,
        "template": f"""SUBJECT: Quick question about your work on {top_keywords[0] if top_keywords else 'this topic'}

Dear Dr. [Name],

I came across your recent work on [{top_keywords[0] if top_keywords else 'related topic'}] and found it highly relevant to my research.

I have recently published a paper titled:
"{title}"

In it, I address [{top_keywords[1] if len(top_keywords) > 1 else 'key findings'}] and believe there may be meaningful overlap with your work on [their topic].

I would be grateful if you had a chance to read it. I am also happy to share a preprint if it is behind a paywall.

[Link to paper]

Best regards,
{name}"""
    })

    # -----------------------------------------------
    # ACTION 3: Promotion Plan
    # Higher effort, builds long-term visibility
    # -----------------------------------------------
    if h_index < 3:
        promo_difficulty = "Low"
        promo_confidence = "High"
        promo_description = (
            f"As an early-career researcher, building an online presence is critical. "
            f"Posting your paper on ResearchGate, LinkedIn, and Twitter/X with the keywords "
            f"'{keyword_str}' can multiply your reach by 5-10x within 30 days."
        )
        promo_template = f"""30-DAY PROMOTION PLAN FOR:
"{title}"

WEEK 1 — PROFILE SETUP (2 hours)
• Upload paper to ResearchGate with all {len(keywords)} keywords
• Update Google Scholar profile
• Add paper to ORCID profile

WEEK 2 — SOCIAL SHARING (1 hour)
• Post on LinkedIn:
  "Excited to share my latest research on {keyword_str}.
   We found [key finding in one sentence].
   Full paper: [link] #research #{top_keywords[0] if top_keywords else 'science'}"

• Post thread on Twitter/X with 3 key findings

WEEK 3 — COMMUNITY (1 hour)
• Share in 2 relevant ResearchGate groups
• Answer 1 question on ResearchGate related to {top_keywords[0] if top_keywords else 'your field'}

WEEK 4 — FOLLOW UP (30 min)
• Email your institution's PR/communications team
• Ask them to feature it on the university website"""

    elif h_index < 10:
        promo_difficulty = "Medium"
        promo_confidence = "High"
        promo_description = (
            f"With your existing research profile, a structured 30-day promotion plan "
            f"can significantly boost visibility for this paper. "
            f"Focus on academic social networks and conference presentations."
        )
        promo_template = f"""30-DAY PROMOTION PLAN FOR:
"{title}"

WEEK 1 — MAXIMIZE DISCOVERABILITY
• Upload preprint to arXiv or bioRxiv if applicable
• Update all profiles with new paper + keywords: {keyword_str}
• Submit to 2 relevant academic newsletters

WEEK 2 — SOCIAL AMPLIFICATION
• LinkedIn post targeting {top_keywords[0] if top_keywords else 'your field'} community
• Tag 3 researchers whose work you cited
• Share key figure/chart as image post

WEEK 3 — CONFERENCE & COMMUNITY
• Submit abstract to 1 upcoming conference
• Present in lab meeting or department seminar
• Post in 2 relevant subreddits (r/MachineLearning, r/science etc)

WEEK 4 — CONSOLIDATE
• Write a 300-word plain-language summary for your institution blog
• Send to journal's social media team for resharing"""
    else:
        promo_difficulty = "Medium"
        promo_confidence = "Medium"
        promo_description = (
            f"With your established profile (h-index: {h_index}), "
            f"leverage your existing network to amplify this paper. "
            f"Focus on high-impact channels and international collaboration."
        )
        promo_template = f"""30-DAY PROMOTION PLAN FOR:
"{title}"

WEEK 1 — LEVERAGE YOUR NETWORK
• Email your top 10 co-authors with the paper link
• Post on LinkedIn mentioning collaborators
• Submit for journal press release if high-impact

WEEK 2 — INTERNATIONAL REACH
• Identify 3 international research groups working on {keyword_str}
• Propose collaboration or data sharing
• Submit to 1 international conference

WEEK 3 — MEDIA & VISIBILITY
• Write a plain-language summary for The Conversation or similar
• Contact science journalists covering {top_keywords[0] if top_keywords else 'your field'}

WEEK 4 — MEASURE & ITERATE
• Check citation alerts (Google Scholar)
• Respond to all ResearchGate questions about your paper
• Update preprint with any corrections"""

    actions.append({
        "number": 3,
        "title": "Execute a 30-Day Promotion Plan",
        "description": promo_description,
        "time_estimate": "30 days (1-2 hrs/week)",
        "difficulty": promo_difficulty,
        "confidence": promo_confidence,
        "template": promo_template
    })

    return actions
