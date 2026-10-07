import os

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Course, Professor
from app.security import hash_password


PROFESSOR_EMAIL = os.getenv(
    "INITIAL_PROFESSOR_EMAIL",
    "professor@buffalo.edu",
)

PROFESSOR_PASSWORD = os.getenv(
    "INITIAL_PROFESSOR_PASSWORD"
)

COURSE_NAME = "Human Anatomy"
COURSE_CODE = "CDA650-ANATOMY"


def create_initial_data():
    if not PROFESSOR_PASSWORD:
        raise RuntimeError(
            "INITIAL_PROFESSOR_PASSWORD is not configured"
        )

    db = SessionLocal()

    try:
        existing_professor = db.scalar(
            select(Professor).where(
                Professor.email == PROFESSOR_EMAIL
            )
        )

        if existing_professor:
            print("Professor already exists.")
            professor = existing_professor

        else:
            professor = Professor(
                email=PROFESSOR_EMAIL,
                password_hash=hash_password(
                    PROFESSOR_PASSWORD
                ),
            )

            db.add(professor)
            db.commit()
            db.refresh(professor)

            print("Professor created.")

        existing_course = db.scalar(
            select(Course).where(
                Course.code == COURSE_CODE
            )
        )

        if existing_course:
            print("Course already exists.")

        else:
            course = Course(
                name=COURSE_NAME,
                code=COURSE_CODE,
                professor_id=professor.id,
            )

            db.add(course)
            db.commit()

            print("Course created.")

        print()
        print("Initial setup complete.")
        print(
            f"Professor email: {PROFESSOR_EMAIL}"
        )
        print(
            f"Course: {COURSE_NAME}"
        )
        print(
            f"Course code: {COURSE_CODE}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    create_initial_data()