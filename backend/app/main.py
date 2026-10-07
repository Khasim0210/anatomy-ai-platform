from datetime import datetime
from pathlib import Path
import shutil

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Claim,
    ClaimSource,
    Course,
    Document,
    Professor,
)
from app.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.services.claim_extractor import (
    extract_claims,
)
from app.services.document_parser import (
    extract_document_text,
)
from app.services.providers.gemini_provider import (
    review_anatomy_claim,
    review_anatomy_claims,
)


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="Anatomy AI Backend"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# FILE STORAGE
# ---------------------------------------------------------

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------
# SECURITY
# ---------------------------------------------------------

security = HTTPBearer()


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------

class ProfessorLoginRequest(BaseModel):
    email: str
    password: str


class ClaimReviewRequest(BaseModel):
    claim: str


class BatchClaim(BaseModel):
    claim_id: int
    text: str


class BatchClaimReviewRequest(BaseModel):
    claims: list[BatchClaim] = Field(
        min_length=1,
        max_length=10,
    )


class ClaimDecisionRequest(BaseModel):
    decision: str
    professor_correction: str | None = None


# ---------------------------------------------------------
# AUTHENTICATION DEPENDENCY
# ---------------------------------------------------------

def get_current_professor(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = decode_access_token(
            token
        )

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid or expired access token"
            ),
        )

    professor_id = payload.get(
        "sub"
    )

    if not professor_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

    try:
        professor_id = int(
            professor_id
        )

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

    professor = db.get(
        Professor,
        professor_id,
    )

    if professor is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Professor account not found"
            ),
        )

    return professor


# ---------------------------------------------------------
# HELPER:
# CONVERT AI SOURCES TO JSON
# ---------------------------------------------------------

def serialize_sources(
    sources,
) -> list[dict]:
    serialized = []

    for source in sources or []:
        serialized.append(
            {
                "title": source.title,
                "url": source.url,
            }
        )

    return serialized


# ---------------------------------------------------------
# HELPER:
# VERIFY CLAIM OWNERSHIP
# ---------------------------------------------------------

def verify_claim_ownership(
    claim: Claim,
    professor: Professor,
):
    if (
        claim.document is None
        or
        claim.document.course is None
        or
        claim.document.course.professor_id
        != professor.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to access this claim"
            ),
        )


# ---------------------------------------------------------
# HELPER:
# VERIFY DOCUMENT OWNERSHIP
# ---------------------------------------------------------

def verify_document_ownership(
    document: Document,
    professor: Professor,
):
    if (
        document.course is None
        or
        document.course.professor_id
        != professor.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to access this document"
            ),
        )


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message":
            "Anatomy AI backend is running"
    }


# ---------------------------------------------------------
# PROFESSOR LOGIN
# ---------------------------------------------------------

@app.post("/professor/login")
def professor_login(
    request: ProfessorLoginRequest,
    db: Session = Depends(get_db),
):
    email = (
        request.email
        .strip()
        .lower()
    )

    password = request.password

    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail=(
                "Email and password are required"
            ),
        )

    professor = db.scalar(
        select(
            Professor
        ).where(
            Professor.email == email
        )
    )

    if professor is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid email or password"
            ),
        )

    if not verify_password(
        password,
        professor.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid email or password"
            ),
        )

    access_token = create_access_token(
        professor_id=professor.id,
        email=professor.email,
    )

    return {
        "message":
            "Login successful",

        "access_token":
            access_token,

        "token_type":
            "bearer",

        "professor": {
            "id":
                professor.id,

            "email":
                professor.email,
        },
    }


# ---------------------------------------------------------
# CURRENT PROFESSOR
# ---------------------------------------------------------

@app.get("/professor/me")
def professor_me(
    professor: Professor = Depends(
        get_current_professor
    ),
):
    return {
        "id":
            professor.id,

        "email":
            professor.email,
    }


# ---------------------------------------------------------
# DOCUMENT UPLOAD
# PROFESSOR ONLY
# ---------------------------------------------------------

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    professor: Professor = Depends(
        get_current_professor
    ),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail=(
                "No file name provided"
            ),
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in {
        ".docx",
        ".pdf",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only DOCX and PDF files "
                "are supported"
            ),
        )

    file_path = (
        UPLOAD_DIR /
        file.filename
    )

    try:
        with file_path.open(
            "wb"
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        extracted_text = (
            extract_document_text(
                str(file_path)
            )
        )

        return {
            "filename":
                file.filename,

            "file_type":
                extension,

            "characters_extracted":
                len(
                    extracted_text
                ),

            "text":
                extracted_text,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process document: "
                f"{str(error)}"
            ),
        )

    finally:
        await file.close()


# ---------------------------------------------------------
# CLAIM EXTRACTION + DATABASE PERSISTENCE
# PROFESSOR ONLY
# ---------------------------------------------------------

@app.post("/analyze-claims")
async def analyze_claims(
    file: UploadFile = File(...),
    professor: Professor = Depends(
        get_current_professor
    ),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail=(
                "No file name provided"
            ),
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in {
        ".docx",
        ".pdf",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only DOCX and PDF files "
                "are supported"
            ),
        )

    course = db.scalar(
        select(
            Course
        )
        .where(
            Course.professor_id
            == professor.id
        )
        .order_by(
            Course.id
        )
    )

    if course is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No course found for this professor"
            ),
        )

    file_path = (
        UPLOAD_DIR /
        file.filename
    )

    try:
        with file_path.open(
            "wb"
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        extracted_text = (
            extract_document_text(
                str(file_path)
            )
        )

        extracted_claims = (
            extract_claims(
                extracted_text
            )
        )

        document = Document(
            filename=file.filename,
            stored_path=str(
                file_path
            ),
            file_type=extension,
            course_id=course.id,
        )

        db.add(
            document
        )

        db.flush()

        saved_claims = []

        for extracted_claim in extracted_claims:
            claim = Claim(
                claim_number=(
                    extracted_claim[
                        "claim_id"
                    ]
                ),
                text=(
                    extracted_claim[
                        "text"
                    ]
                ),
                page=(
                    extracted_claim.get(
                        "page"
                    )
                ),
                document_id=(
                    document.id
                ),
            )

            db.add(
                claim
            )

            saved_claims.append(
                claim
            )

        db.flush()

        response_claims = []

        for claim in saved_claims:
            response_claims.append(
                {
                    "id":
                        claim.id,

                    "claim_number":
                        claim.claim_number,

                    "page":
                        claim.page,

                    "text":
                        claim.text,

                    "ai_status":
                        claim.ai_status,

                    "ai_reason":
                        claim.ai_reason,

                    "suggested_correction":
                        claim.suggested_correction,

                    "sources":
                        [],

                    "instructor_decision":
                        claim.instructor_decision,

                    "professor_correction":
                        claim.professor_correction,

                    "reviewed_at":
                        claim.reviewed_at,
                }
            )

        db.commit()

        return {
            "message":
                "Document analyzed and claims saved",

            "course": {
                "id":
                    course.id,

                "name":
                    course.name,

                "code":
                    course.code,
            },

            "document_id":
                document.id,

            "filename":
                file.filename,

            "file_type":
                extension,

            "total_claims":
                len(
                    response_claims
                ),

            "claims":
                response_claims,
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to analyze document: "
                f"{str(error)}"
            ),
        )

    finally:
        await file.close()


# ---------------------------------------------------------
# LIST PROFESSOR DOCUMENTS
# PROFESSOR ONLY
# ---------------------------------------------------------

@app.get("/documents")
def list_documents(
    professor: Professor = Depends(
        get_current_professor
    ),
    db: Session = Depends(get_db),
):
    documents = db.scalars(
        select(
            Document
        )
        .join(
            Course
        )
        .where(
            Course.professor_id
            == professor.id
        )
        .order_by(
            Document.uploaded_at.desc()
        )
    ).all()

    return {
        "total_documents":
            len(
                documents
            ),

        "documents": [
            {
                "id":
                    document.id,

                "filename":
                    document.filename,

                "file_type":
                    document.file_type,

                "course_id":
                    document.course_id,

                "uploaded_at":
                    document.uploaded_at,
            }

            for document
            in documents
        ],
    }


# ---------------------------------------------------------
# LOAD DOCUMENT CLAIMS
# PROFESSOR ONLY
# ---------------------------------------------------------

@app.get(
    "/documents/{document_id}/claims"
)
def get_document_claims(
    document_id: int,
    professor: Professor = Depends(
        get_current_professor
    ),
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Document not found"
            ),
        )

    verify_document_ownership(
        document,
        professor,
    )

    claims = db.scalars(
        select(
            Claim
        )
        .where(
            Claim.document_id
            == document.id
        )
        .order_by(
            Claim.claim_number
        )
    ).all()

    response_claims = []

    for claim in claims:
        sources = db.scalars(
            select(
                ClaimSource
            )
            .where(
                ClaimSource.claim_id
                == claim.id
            )
            .order_by(
                ClaimSource.id
            )
        ).all()

        response_claims.append(
            {
                "id":
                    claim.id,

                "claim_number":
                    claim.claim_number,

                "page":
                    claim.page,

                "text":
                    claim.text,

                "ai_status":
                    claim.ai_status,

                "ai_reason":
                    claim.ai_reason,

                "suggested_correction":
                    claim.suggested_correction,

                "sources": [
                    {
                        "id":
                            source.id,

                        "title":
                            source.source_title,

                        "url":
                            source.source_url,

                        "evidence_text":
                            source.evidence_text,
                    }

                    for source
                    in sources
                ],

                "instructor_decision":
                    claim.instructor_decision,

                "professor_correction":
                    claim.professor_correction,

                "reviewed_at":
                    claim.reviewed_at,

                "created_at":
                    claim.created_at,

                "updated_at":
                    claim.updated_at,
            }
        )

    return {
        "document": {
            "id":
                document.id,

            "filename":
                document.filename,

            "file_type":
                document.file_type,

            "course_id":
                document.course_id,

            "uploaded_at":
                document.uploaded_at,
        },

        "total_claims":
            len(
                response_claims
            ),

        "claims":
            response_claims,
    }


# ---------------------------------------------------------
# DELETE DOCUMENT
# PROFESSOR ONLY
# ---------------------------------------------------------

@app.delete(
    "/documents/{document_id}"
)
def delete_document(
    document_id: int,
    professor: Professor = Depends(
        get_current_professor
    ),
    db: Session = Depends(get_db),
):
    document = db.get(
        Document,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Document not found"
            ),
        )

    verify_document_ownership(
        document,
        professor,
    )

    filename = (
        document.filename
    )

    stored_path = Path(
        document.stored_path
    )

    try:
        # SQLAlchemy relationships are configured with
        # delete-orphan cascade:
        #
        # Document -> Claims
        # Claim -> ClaimSource
        #
        # Deleting the Document therefore removes the
        # associated database review data as well.
        db.delete(
            document
        )

        db.commit()

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete document: "
                f"{str(error)}"
            ),
        )

    # Delete the stored file only after the database
    # transaction succeeds.
    #
    # Important:
    # During current development several Document rows can
    # reference the same physical filename. Therefore we
    # only remove the file if no remaining Document row
    # references the same stored path.
    remaining_document = db.scalar(
        select(
            Document
        ).where(
            Document.stored_path
            == str(stored_path)
        )
    )

    file_deleted = False

    if (
        remaining_document is None
        and
        stored_path.exists()
        and
        stored_path.is_file()
    ):
        try:
            stored_path.unlink()

            file_deleted = True

        except OSError:
            # Database deletion succeeded.
            # A physical-file cleanup failure should not
            # recreate or corrupt the database records.
            file_deleted = False

    return {
        "message":
            "Document deleted successfully",

        "document_id":
            document_id,

        "filename":
            filename,

        "stored_file_deleted":
            file_deleted,
    }


# ---------------------------------------------------------
# AD-HOC SINGLE AI REVIEW
# PROFESSOR ONLY
# DOES NOT SAVE TO DATABASE
# ---------------------------------------------------------

@app.post("/review-claim")
def review_claim(
    request: ClaimReviewRequest,
    professor: Professor = Depends(
        get_current_professor
    ),
):
    claim_text = (
        request.claim.strip()
    )

    if not claim_text:
        raise HTTPException(
            status_code=400,
            detail=(
                "Claim cannot be empty"
            ),
        )

    try:
        review = (
            review_anatomy_claim(
                claim_text
            )
        )

        return {
            "claim":
                claim_text,

            "status":
                review.status,

            "reason":
                review.reason,

            "suggested_correction":
                review.suggested_correction,

            "sources":
                serialize_sources(
                    review.sources
                ),
        }

    except Exception as error:
        error_message = str(
            error
        )

        if (
            "429" in error_message
            or
            "RESOURCE_EXHAUSTED"
            in error_message
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini rate limit reached. "
                    "Please wait and try again."
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "Gemini review failed: "
                f"{error_message}"
            ),
        )


# ---------------------------------------------------------
# PERSISTED CLAIM AI REVIEW
# PROFESSOR ONLY
# ---------------------------------------------------------

@app.post(
    "/claims/{claim_id}/review"
)
def review_saved_claim(
    claim_id: int,
    professor: Professor = Depends(
        get_current_professor
    ),
    db: Session = Depends(get_db),
):
    claim = db.get(
        Claim,
        claim_id,
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Claim not found"
            ),
        )

    verify_claim_ownership(
        claim,
        professor,
    )

    try:
        review = (
            review_anatomy_claim(
                claim.text
            )
        )

        claim.ai_status = (
            review.status
        )

        claim.ai_reason = (
            review.reason
        )

        claim.suggested_correction = (
            review.suggested_correction
        )

        claim.updated_at = (
            datetime.utcnow()
        )

        db.execute(
            delete(
                ClaimSource
            ).where(
                ClaimSource.claim_id
                == claim.id
            )
        )

        for source in (
            review.sources or []
        ):
            claim_source = (
                ClaimSource(
                    claim_id=claim.id,

                    source_title=(
                        source.title
                        or
                        "External source"
                    ),

                    source_url=
                        source.url,

                    evidence_text=
                        None,
                )
            )

            db.add(
                claim_source
            )

        db.commit()

        db.refresh(
            claim
        )

        saved_sources = db.scalars(
            select(
                ClaimSource
            )
            .where(
                ClaimSource.claim_id
                == claim.id
            )
            .order_by(
                ClaimSource.id
            )
        ).all()

        return {
            "message":
                "AI review saved",

            "claim_id":
                claim.id,

            "claim_number":
                claim.claim_number,

            "claim":
                claim.text,

            "status":
                claim.ai_status,

            "reason":
                claim.ai_reason,

            "suggested_correction":
                claim.suggested_correction,

            "sources": [
                {
                    "id":
                        source.id,

                    "title":
                        source.source_title,

                    "url":
                        source.source_url,

                    "evidence_text":
                        source.evidence_text,
                }

                for source
                in saved_sources
            ],
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        error_message = str(
            error
        )

        if (
            "429" in error_message
            or
            "RESOURCE_EXHAUSTED"
            in error_message
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini rate limit reached. "
                    "No AI review was saved. "
                    "Please wait and try again."
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to review and save claim: "
                f"{error_message}"
            ),
        )


# ---------------------------------------------------------
# AD-HOC BATCH AI REVIEW
# PROFESSOR ONLY
# CURRENTLY DOES NOT SAVE TO DATABASE
# ---------------------------------------------------------

@app.post("/review-claims")
def review_claims_batch(
    request: BatchClaimReviewRequest,
    professor: Professor = Depends(
        get_current_professor
    ),
):
    claims = []

    for claim in request.claims:
        text = (
            claim.text.strip()
        )

        if not text:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Claim {claim.claim_id} "
                    "cannot be empty"
                ),
            )

        claims.append(
            {
                "claim_id":
                    claim.claim_id,

                "text":
                    text,
            }
        )

    try:
        result = (
            review_anatomy_claims(
                claims
            )
        )

        return {
            "total_reviews":
                len(
                    result.reviews
                ),

            "reviews": [
                {
                    "claim_id":
                        review.claim_id,

                    "status":
                        review.status,

                    "reason":
                        review.reason,

                    "suggested_correction":
                        review.suggested_correction,

                    "sources":
                        serialize_sources(
                            review.sources
                        ),
                }

                for review
                in result.reviews
            ],
        }

    except Exception as error:
        error_message = str(
            error
        )

        if (
            "429" in error_message
            or
            "RESOURCE_EXHAUSTED"
            in error_message
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini rate limit reached. "
                    "Please wait and try again."
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "Gemini batch review failed: "
                f"{error_message}"
            ),
        )


# ---------------------------------------------------------
# PROFESSOR CLAIM DECISION
# PROFESSOR ONLY
# ---------------------------------------------------------

@app.patch(
    "/claims/{claim_id}/decision"
)
def update_claim_decision(
    claim_id: int,
    request: ClaimDecisionRequest,
    professor: Professor = Depends(
        get_current_professor
    ),
    db: Session = Depends(get_db),
):
    allowed_decisions = {
        "accepted",
        "rejected",
        "edited",
        "needs_review",
    }

    decision = (
        request.decision
        .strip()
        .lower()
    )

    if (
        decision
        not in
        allowed_decisions
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Decision must be one of: "
                "accepted, rejected, edited, "
                "needs_review"
            ),
        )

    claim = db.get(
        Claim,
        claim_id,
    )

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Claim not found"
            ),
        )

    verify_claim_ownership(
        claim,
        professor,
    )

    professor_correction = (
        request.professor_correction.strip()
        if request.professor_correction
        else None
    )

    if (
        decision == "edited"
        and
        not professor_correction
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "A professor correction is required "
                "when decision is edited"
            ),
        )

    if decision != "edited":
        professor_correction = None

    claim.instructor_decision = (
        decision
    )

    claim.professor_correction = (
        professor_correction
    )

    claim.reviewed_at = (
        datetime.utcnow()
    )

    claim.updated_at = (
        datetime.utcnow()
    )

    try:
        db.commit()

        db.refresh(
            claim
        )

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save professor decision: "
                f"{str(error)}"
            ),
        )

    return {
        "message":
            "Professor decision saved",

        "claim_id":
            claim.id,

        "decision":
            claim.instructor_decision,

        "professor_correction":
            claim.professor_correction,

        "reviewed_at":
            claim.reviewed_at,
    }