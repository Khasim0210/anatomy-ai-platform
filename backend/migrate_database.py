import sqlite3
from pathlib import Path


DB_PATH = Path("anatomy_ai.db")


def column_exists(cursor, table_name, column_name):
    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    return any(
        column[1] == column_name
        for column in columns
    )


def table_exists(cursor, table_name):
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (table_name,),
    )

    return cursor.fetchone() is not None


def main():
    if not DB_PATH.exists():
        print(
            f"Database not found: {DB_PATH}"
        )
        return

    connection = sqlite3.connect(
        DB_PATH
    )

    cursor = connection.cursor()

    print(
        f"Using database: {DB_PATH}"
    )

    # --------------------------------------------------
    # CLAIMS TABLE MIGRATION
    # --------------------------------------------------

    if not column_exists(
        cursor,
        "claims",
        "professor_correction",
    ):
        cursor.execute(
            """
            ALTER TABLE claims
            ADD COLUMN professor_correction TEXT
            """
        )

        print(
            "Added claims.professor_correction"
        )
    else:
        print(
            "claims.professor_correction already exists"
        )


    if not column_exists(
        cursor,
        "claims",
        "reviewed_at",
    ):
        cursor.execute(
            """
            ALTER TABLE claims
            ADD COLUMN reviewed_at DATETIME
            """
        )

        print(
            "Added claims.reviewed_at"
        )
    else:
        print(
            "claims.reviewed_at already exists"
        )


    if not column_exists(
        cursor,
        "claims",
        "updated_at",
    ):
        cursor.execute(
            """
            ALTER TABLE claims
            ADD COLUMN updated_at DATETIME
            """
        )

        print(
            "Added claims.updated_at"
        )
    else:
        print(
            "claims.updated_at already exists"
        )


    # --------------------------------------------------
    # CLAIM SOURCES TABLE
    # --------------------------------------------------

    if not table_exists(
        cursor,
        "claim_sources",
    ):
        cursor.execute(
            """
            CREATE TABLE claim_sources (
                id INTEGER PRIMARY KEY,
                claim_id INTEGER NOT NULL,
                source_title VARCHAR(500) NOT NULL,
                source_url TEXT NOT NULL,
                evidence_text TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(claim_id)
                    REFERENCES claims(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX
            ix_claim_sources_id
            ON claim_sources(id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX
            ix_claim_sources_claim_id
            ON claim_sources(claim_id)
            """
        )

        print(
            "Created claim_sources table"
        )

    else:
        print(
            "claim_sources table already exists"
        )


    connection.commit()

    connection.close()

    print()
    print(
        "Database migration completed successfully."
    )


if __name__ == "__main__":
    main()