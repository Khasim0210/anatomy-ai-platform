~/anatomy-ai
# Anatomy AI Platform

An AI-powered anatomy learning and lecture review platform for analyzing course notes, identifying potential factual issues, supporting instructor review with evidence, and enabling student Q&A.

## Overview

The Anatomy AI Platform is being developed as a full-stack academic support system for anatomy education.

The platform is designed around two primary users:

- Students, who can ask anatomy questions without creating an account.
- Professors, who can securely manage lecture material, review AI findings, inspect supporting evidence, and approve or reject proposed corrections.

The instructor remains the final authority for all lecture-note corrections.

## Current Features

### Professor Authentication

- Secure professor login
- Argon2 password hashing
- JWT-based authentication
- Protected professor-only API endpoints

### Lecture Document Processing

- Upload DOCX and PDF lecture notes
- Extract document text
- Extract anatomy claims from lecture notes
- Save documents and claims to SQLite
- Reopen previously analyzed lectures

### AI-Assisted Lecture Review

The system can review persisted anatomy claims using an AI provider.

Current development provider:

- Google Gemini

Planned provider support:

- University-provided AI/API services

The AI workflow is designed to:

- Review anatomy claims
- Identify likely correct statements
- Flag possible factual errors
- Flag claims requiring further review
- Suggest corrections only when appropriate
- Retrieve external supporting sources when available

AI results are advisory only.

### Instructor Review Workflow

Professors can make a final decision for each claim:

- Accept
- Reject
- Edit
- Needs Review

Professor decisions are persisted in the database.

Edited corrections are stored separately from the original lecture-note claim so the original content is preserved.

### Evidence and Sources

Each AI-reviewed claim can store external evidence including:

- Source title
- Source URL
- Supporting evidence text

The platform is designed to prioritize reliable anatomy and medical references.

### Saved Documents

Professors can:

- View previously analyzed lecture documents
- Reopen saved documents
- Continue reviewing saved claims
- Delete outdated documents

Deleting a document also removes its associated claims, reviews, and sources from the database.

## Planned Features

### Student Q&A

Students will be able to:

- Select a course
- Ask anatomy questions
- Receive answers based primarily on instructor-approved course material
- Receive clearly identified external information when the answer is not available in the course notes

Students will not have direct access to private professor-uploaded lecture files.

### Approved Course Content

Professor-approved corrections will become part of the canonical course knowledge base.

The final student-facing knowledge source will combine:

- Original professor lecture material
- Professor-approved corrections

### Document Revision

Planned support includes:

- Generating revised DOCX lecture notes
- Preserving original documents
- Version history
- Downloading professor-approved revised documents

### Student Question Analytics

The platform will eventually support:

- Saving repeated student questions
- Grouping similar questions
- Instructor analytics
- Identifying topics students frequently struggle with

### Question Generation

A later project phase may include generation of educational assessment questions using appropriate question-writing standards.

## Technology Stack

### Frontend

- React
- Vite
- React Router
- CSS

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite for development

### Document Processing

- python-docx
- PyMuPDF

### Authentication

- JWT
- Argon2 password hashing

### AI

Current development provider:

- Google Gemini

The architecture is designed so the AI provider can be replaced without rewriting the main application.

## Project Structure

```text
anatomy-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── security.py
│   │   └── services/
│   │       ├── claim_extractor.py
│   │       ├── document_parser.py
│   │       └── providers/
│   │           └── gemini_provider.py
│   ├── create_initial_data.py
│   └── migrate_database.py
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── StudentHome.jsx
│   │   │   ├── ProfessorLogin.jsx
│   │   │   ├── ProfessorDashboard.jsx
│   │   │   └── LectureReview.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   └── package.json
│
└── frontend_streamlit_backup/
