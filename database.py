import sqlite3

DB_NAME = "emails.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            frequency TEXT NOT NULL,
            day_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_schedule(email, frequency, day_value=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO email_reports (email, frequency, day_value)
        VALUES (?, ?, ?)
        """,
        (email, frequency, day_value)
    )

    conn.commit()
    conn.close()


def get_all_schedules():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT email, frequency, day_value FROM email_reports"
    )

    rows = cursor.fetchall()
    conn.close()
    return rows
