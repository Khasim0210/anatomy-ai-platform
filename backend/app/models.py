from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database import Base


# ---------------------------------------------------------
# PROFESSOR
# ---------------------------------------------------------

class Professor(Base):
    __tablename__ = "professors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    courses = relationship(
        "Course",
        back_populates="professor",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------
# COURSE
# ---------------------------------------------------------

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professors.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    professor = relationship(
        "Professor",
        back_populates="courses",
    )

    documents = relationship(
        "Document",
        back_populates="course",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------
# DOCUMENT
# ---------------------------------------------------------

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    course = relationship(
        "Course",
        back_populates="documents",
    )

    claims = relationship(
        "Claim",
        back_populates="document",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------
# CLAIM
# ---------------------------------------------------------

class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    claim_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    page: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # -----------------------------------------------------
    # AI REVIEW
    # -----------------------------------------------------

    ai_status: Mapped[str] = mapped_column(
        String(50),
        default="not_reviewed",
        nullable=False,
    )

    ai_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    suggested_correction: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # -----------------------------------------------------
    # PROFESSOR REVIEW
    #
    # Expected values:
    # pending
    # accepted
    # rejected
    # edited
    # needs_review
    # -----------------------------------------------------

    instructor_decision: Mapped[str] = mapped_column(
        String(100),
        default="pending",
        nullable=False,
    )

    # If Dr. Stuart edits the AI correction,
    # his final edited wording is stored here.
    professor_correction: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # When the professor last made a decision.
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # -----------------------------------------------------
    # DOCUMENT RELATIONSHIP
    # -----------------------------------------------------

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    document = relationship(
        "Document",
        back_populates="claims",
    )

    # External evidence used during AI verification.
    sources = relationship(
        "ClaimSource",
        back_populates="claim",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------
# CLAIM SOURCE / EXTERNAL EVIDENCE
# ---------------------------------------------------------

class ClaimSource(Base):
    __tablename__ = "claim_sources"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claims.id"),
        nullable=False,
        index=True,
    )

    # Example:
    # "NCBI Bookshelf"
    source_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Actual grounded URL returned by the provider.
    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Optional supporting text.
    # We are not generating this yet, but keeping the
    # field now prevents another schema change later.
    evidence_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    claim = relationship(
        "Claim",
        back_populates="sources",
    )