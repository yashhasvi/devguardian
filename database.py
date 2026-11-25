
import sqlite3
from pathlib import Path


# Find the backend folder
BASE_DIR = Path(__file__).resolve().parent

# Database file location
DATABASE_PATH = BASE_DIR / "devguardian.db"


def get_connection():
    """
    Connect Python to the SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # Enable foreign key relationships
    connection.execute("PRAGMA foreign_keys = ON")

    # Allow us to access rows using column names
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """
    Create all five DevGuardian tables.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            is_monitored INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_full_name TEXT NOT NULL,
            github_run_id TEXT UNIQUE NOT NULL,
            workflow_name TEXT,
            branch TEXT,
            commit_sha TEXT,
            status TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id INTEGER NOT NULL,
            failed_test TEXT,
            error_type TEXT,
            error_message TEXT,
            raw_logs TEXT,
            changed_files_json TEXT,
            FOREIGN KEY (workflow_run_id)
                REFERENCES workflow_runs(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id INTEGER NOT NULL,
            current_step TEXT,
            root_cause TEXT,
            confidence REAL,
            patch_diff TEXT,
            files_modified_json TEXT,
            tests_before_summary TEXT,
            tests_after_summary TEXT,
            docker_logs TEXT,
            report_markdown TEXT,
            draft_pr_url TEXT,
            status TEXT DEFAULT 'running',
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            FOREIGN KEY (workflow_run_id)
                REFERENCES workflow_runs(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id INTEGER NOT NULL,
            step_key TEXT NOT NULL,
            label TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (execution_id)
                REFERENCES agent_executions(id)
        )
    """)

    connection.commit()
    connection.close()

    print("DevGuardian database initialized!")


def add_repository(full_name, url):
    """
    Save a new GitHub repository.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO repositories (full_name, url)
            VALUES (?, ?)
            """,
            (full_name, url)
        )

        connection.commit()

        repository_id = cursor.lastrowid

        return {
            "id": repository_id,
            "full_name": full_name,
            "url": url,
            "is_monitored": True
        }

    except sqlite3.IntegrityError:
        raise ValueError("This repository is already registered.")

    finally:
        connection.close()


def get_repositories():
    """
    Retrieve all registered repositories.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM repositories
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    repositories = [dict(row) for row in rows]

    connection.close()

    return repositories


if __name__ == "__main__":
    initialize_database()
