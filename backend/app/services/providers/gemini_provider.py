import os
from typing import Literal, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# SOURCE MODEL
# ---------------------------------------------------------

class AnatomySource(BaseModel):
    title: str
    url: str


# ---------------------------------------------------------
# REVIEW MODELS
# ---------------------------------------------------------

class AnatomyReview(BaseModel):
    claim_id: int

    status: Literal[
        "likely_correct",
        "possible_error",
        "needs_review",
    ]

    reason: str

    suggested_correction: Optional[str] = None

    sources: list[AnatomySource] = Field(
        default_factory=list
    )


class AnatomyReviewBatch(BaseModel):
    reviews: list[AnatomyReview]


# ---------------------------------------------------------
# GEMINI CLIENT
# ---------------------------------------------------------

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    return genai.Client(
        api_key=api_key
    )


# ---------------------------------------------------------
# SOURCE EXTRACTION
# ---------------------------------------------------------

def extract_grounding_sources(
    response,
) -> list[AnatomySource]:

    sources = []

    if not response.candidates:
        return sources

    candidate = response.candidates[0]

    grounding_metadata = getattr(
        candidate,
        "grounding_metadata",
        None,
    )

    if not grounding_metadata:
        return sources

    grounding_chunks = getattr(
        grounding_metadata,
        "grounding_chunks",
        None,
    )

    if not grounding_chunks:
        return sources

    seen_urls = set()

    for chunk in grounding_chunks:

        web = getattr(
            chunk,
            "web",
            None,
        )

        if not web:
            continue

        url = getattr(
            web,
            "uri",
            None,
        )

        title = getattr(
            web,
            "title",
            None,
        )

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        sources.append(
            AnatomySource(
                title=title or "External source",
                url=url,
            )
        )

    return sources


# ---------------------------------------------------------
# STEP 1:
# GROUNDED FACTUAL RESEARCH
# ---------------------------------------------------------

def research_claim(
    claim_text: str,
) -> tuple[str, list[AnatomySource]]:

    client = get_gemini_client()

    prompt = f"""
You are assisting with factual review of university anatomy lecture notes.

Research the following anatomy claim using reliable external sources:

CLAIM:
{claim_text}

Determine whether reliable anatomy or medical references
support or contradict this statement.

Prefer trustworthy sources such as:

- NCBI / NIH
- university medical schools
- professional medical organizations
- established academic medical references

Avoid low-quality blogs, forums, and unverified sources.

Write a concise factual research summary.

Do not make the instructor's final decision.
"""

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=0.1,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty grounded research response"
        )

    sources = extract_grounding_sources(
        response
    )

    return response.text, sources


# ---------------------------------------------------------
# STEP 2:
# STRUCTURED REVIEW
# ---------------------------------------------------------

def create_structured_review(
    claim_id: int,
    claim_text: str,
    research_summary: str,
    sources: list[AnatomySource],
) -> AnatomyReview:

    client = get_gemini_client()

    source_text = "\n".join(
        [
            f"- {source.title}: {source.url}"
            for source in sources
        ]
    )

    if not source_text:
        source_text = (
            "No verifiable external sources were returned."
        )

    prompt = f"""
You are assisting with factual review of university anatomy lecture notes.

Original claim:

{claim_text}

External research summary:

{research_summary}

Retrieved sources:

{source_text}

Classify the original claim as exactly one of:

1. likely_correct
   The available evidence supports the claim.

2. possible_error
   Reliable evidence indicates that the claim is incorrect
   or materially misleading.

3. needs_review
   The claim is ambiguous, incomplete, context-dependent,
   evidence is insufficient, or reliable sources disagree.

Rules:

- Do not make the instructor's final decision.
- Do not modify a claim that appears correct.
- Keep the reason concise.
- If status is likely_correct,
  suggested_correction must be null.
- If status is possible_error,
  provide a concise suggested correction.
- If evidence is insufficient,
  use needs_review rather than guessing.
"""

    class StructuredReview(BaseModel):
        status: Literal[
            "likely_correct",
            "possible_error",
            "needs_review",
        ]

        reason: str

        suggested_correction: Optional[str] = None

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StructuredReview,
            temperature=0.1,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty structured review"
        )

    structured = (
        StructuredReview.model_validate_json(
            response.text
        )
    )

    return AnatomyReview(
        claim_id=claim_id,
        status=structured.status,
        reason=structured.reason,
        suggested_correction=(
            structured.suggested_correction
        ),
        sources=sources,
    )


# ---------------------------------------------------------
# SINGLE CLAIM REVIEW
# ---------------------------------------------------------

def review_anatomy_claim(
    claim_text: str,
) -> AnatomyReview:

    research_summary, sources = research_claim(
        claim_text
    )

    return create_structured_review(
        claim_id=1,
        claim_text=claim_text,
        research_summary=research_summary,
        sources=sources,
    )


# ---------------------------------------------------------
# BATCH REVIEW
# ---------------------------------------------------------

def review_anatomy_claims(
    claims: list[dict],
) -> AnatomyReviewBatch:

    reviews = []

    for claim in claims:

        research_summary, sources = research_claim(
            claim["text"]
        )

        review = create_structured_review(
            claim_id=claim["claim_id"],
            claim_text=claim["text"],
            research_summary=research_summary,
            sources=sources,
        )

        reviews.append(review)

    return AnatomyReviewBatch(
        reviews=reviews
    )