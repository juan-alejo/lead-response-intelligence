"""SQLite implementation — zero-config, works anywhere.

The schema mirrors the three Airtable tables specified in the Phase 1 brief:
prospects, submissions, responses. Migrations are idempotent (CREATE IF NOT
EXISTS) so the store can be initialized at import time without blowing up on
re-runs.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from loguru import logger

from ..models import Prospect, Response, Submission, SubmissionAttempt
from .base import Storage

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prospects (
    place_id        TEXT PRIMARY KEY,
    business_name   TEXT NOT NULL,
    vertical        TEXT NOT NULL,
    location        TEXT NOT NULL,
    website         TEXT,
    phone           TEXT,
    email           TEXT,
    discovered_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS submissions (
    submission_id           TEXT PRIMARY KEY,
    prospect_place_id       TEXT NOT NULL,
    business_name           TEXT NOT NULL,
    vertical                TEXT NOT NULL,
    submission_method       TEXT NOT NULL,
    expected_sender_phone   TEXT,
    expected_sender_email   TEXT,
    submitted_at            TEXT,
    FOREIGN KEY (prospect_place_id) REFERENCES prospects(place_id)
);

CREATE TABLE IF NOT EXISTS responses (
    response_id             TEXT PRIMARY KEY,
    channel                 TEXT NOT NULL,
    received_at             TEXT NOT NULL,
    matched_submission_id   TEXT,
    elapsed_seconds         INTEGER,
    sender_phone            TEXT,
    sender_email            TEXT,
    content_snippet         TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (matched_submission_id) REFERENCES submissions(submission_id)
);

CREATE TABLE IF NOT EXISTS submission_attempts (
    attempt_id              TEXT PRIMARY KEY,
    submission_id           TEXT NOT NULL,
    status                  TEXT NOT NULL,
    started_at              TEXT,
    completed_at            TEXT,
    duration_ms             INTEGER,
    form_url                TEXT,
    confirmation_text       TEXT NOT NULL DEFAULT '',
    screenshot_path         TEXT,
    error_message           TEXT NOT NULL DEFAULT '',
    logs                    TEXT NOT NULL DEFAULT '[]',  -- JSON list[str]
    attempt_number          INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id)
);

CREATE INDEX IF NOT EXISTS idx_attempts_submission
    ON submission_attempts(submission_id);
CREATE INDEX IF NOT EXISTS idx_attempts_status
    ON submission_attempts(status);
"""


class SQLiteStore(Storage):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            # If an older DB still has `borough` instead of `location`, rename
            # it in-place. SQLite ≥3.25 supports ALTER TABLE RENAME COLUMN,
            # which is what all supported Python 3.11+ runtimes ship with.
            cols = {row["name"] for row in c.execute("PRAGMA table_info(prospects)")}
            if "borough" in cols and "location" not in cols:
                c.execute("ALTER TABLE prospects RENAME COLUMN borough TO location")
                logger.info("[sqlite] migrated column prospects.borough → location")
            c.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # --- Prospects ---

    def upsert_prospects(self, prospects: list[Prospect]) -> int:
        if not prospects:
            return 0
        with self._conn() as c:
            c.executemany(
                """
                INSERT INTO prospects (
                    place_id, business_name, vertical, location,
                    website, phone, email, discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(place_id) DO UPDATE SET
                    business_name=excluded.business_name,
                    vertical=excluded.vertical,
                    location=excluded.location,
                    website=excluded.website,
                    phone=excluded.phone,
                    email=excluded.email
                """,
                [
                    (
                        p.place_id,
                        p.business_name,
                        p.vertical,
                        p.location,
                        p.website,
                        p.phone,
                        p.email,
                        p.discovered_at.isoformat(),
                    )
                    for p in prospects
                ],
            )
        logger.info(f"[sqlite] upserted {len(prospects)} prospects")
        return len(prospects)

    def recent_place_ids(self, window_days: int = 90) -> dict[str, datetime]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT place_id, discovered_at FROM prospects"
            ).fetchall()
        return {r["place_id"]: datetime.fromisoformat(r["discovered_at"]) for r in rows}

    def prospect_website(self, place_id: str) -> str | None:
        """Used by the Phase 2 submitter to resolve a form URL from a place id."""
        with self._conn() as c:
            row = c.execute(
                "SELECT website FROM prospects WHERE place_id = ?", (place_id,)
            ).fetchone()
        return row["website"] if row else None

    # --- Submissions ---

    def upsert_submissions(self, submissions: list[Submission]) -> int:
        if not submissions:
            return 0
        with self._conn() as c:
            c.executemany(
                """
                INSERT INTO submissions (
                    submission_id, prospect_place_id, business_name, vertical,
                    submission_method, expected_sender_phone,
                    expected_sender_email, submitted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(submission_id) DO UPDATE SET
                    submitted_at=excluded.submitted_at
                """,
                [
                    (
                        s.submission_id,
                        s.prospect_place_id,
                        s.business_name,
                        s.vertical,
                        s.submission_method.value,
                        s.expected_sender_phone,
                        s.expected_sender_email,
                        s.submitted_at.isoformat() if s.submitted_at else None,
                    )
                    for s in submissions
                ],
            )
        return len(submissions)

    def all_submissions(self) -> list[Submission]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM submissions").fetchall()
        return [
            Submission(
                submission_id=r["submission_id"],
                prospect_place_id=r["prospect_place_id"],
                business_name=r["business_name"],
                vertical=r["vertical"],
                submission_method=r["submission_method"],
                expected_sender_phone=r["expected_sender_phone"],
                expected_sender_email=r["expected_sender_email"],
                submitted_at=(
                    datetime.fromisoformat(r["submitted_at"])
                    if r["submitted_at"]
                    else None
                ),
            )
            for r in rows
        ]

    # --- Responses ---

    def upsert_responses(self, responses: list[Response]) -> int:
        if not responses:
            return 0
        with self._conn() as c:
            c.executemany(
                """
                INSERT INTO responses
                    (response_id, channel, received_at, matched_submission_id,
                     elapsed_seconds, sender_phone, sender_email, content_snippet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(response_id) DO UPDATE SET
                    matched_submission_id=excluded.matched_submission_id,
                    elapsed_seconds=excluded.elapsed_seconds
                """,
                [
                    (
                        r.response_id,
                        r.channel.value,
                        r.received_at.isoformat(),
                        r.matched_submission_id,
                        r.elapsed_seconds,
                        r.sender_phone,
                        r.sender_email,
                        r.content_snippet,
                    )
                    for r in responses
                ],
            )
        return len(responses)

    def all_responses(self) -> list[Response]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM responses").fetchall()
        return [
            Response(
                response_id=r["response_id"],
                channel=r["channel"],
                received_at=datetime.fromisoformat(r["received_at"]),
                matched_submission_id=r["matched_submission_id"],
                elapsed_seconds=r["elapsed_seconds"],
                sender_phone=r["sender_phone"],
                sender_email=r["sender_email"],
                content_snippet=r["content_snippet"] or "",
            )
            for r in rows
        ]

    # --- Submission attempts (Phase 2) ---

    def upsert_attempts(self, attempts: list[SubmissionAttempt]) -> int:
        if not attempts:
            return 0
        import json

        with self._conn() as c:
            c.executemany(
                """
                INSERT INTO submission_attempts (
                    attempt_id, submission_id, status, started_at, completed_at,
                    duration_ms, form_url, confirmation_text, screenshot_path,
                    error_message, logs, attempt_number
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(attempt_id) DO UPDATE SET
                    status=excluded.status,
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    duration_ms=excluded.duration_ms,
                    form_url=excluded.form_url,
                    confirmation_text=excluded.confirmation_text,
                    screenshot_path=excluded.screenshot_path,
                    error_message=excluded.error_message,
                    logs=excluded.logs,
                    attempt_number=excluded.attempt_number
                """,
                [
                    (
                        a.attempt_id,
                        a.submission_id,
                        a.status.value,
                        a.started_at.isoformat() if a.started_at else None,
                        a.completed_at.isoformat() if a.completed_at else None,
                        a.duration_ms,
                        a.form_url,
                        a.confirmation_text,
                        a.screenshot_path,
                        a.error_message,
                        json.dumps(a.logs),
                        a.attempt_number,
                    )
                    for a in attempts
                ],
            )
        return len(attempts)

    def all_attempts(self) -> list[SubmissionAttempt]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM submission_attempts ORDER BY attempt_number ASC"
            ).fetchall()
        return [_row_to_attempt(r) for r in rows]

    def attempts_for_submission(self, submission_id: str) -> list[SubmissionAttempt]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM submission_attempts "
                "WHERE submission_id = ? "
                "ORDER BY attempt_number ASC",
                (submission_id,),
            ).fetchall()
        return [_row_to_attempt(r) for r in rows]


def _row_to_attempt(r) -> SubmissionAttempt:
    import json

    return SubmissionAttempt(
        attempt_id=r["attempt_id"],
        submission_id=r["submission_id"],
        status=r["status"],
        started_at=(
            datetime.fromisoformat(r["started_at"]) if r["started_at"] else None
        ),
        completed_at=(
            datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None
        ),
        duration_ms=r["duration_ms"],
        form_url=r["form_url"],
        confirmation_text=r["confirmation_text"] or "",
        screenshot_path=r["screenshot_path"],
        error_message=r["error_message"] or "",
        logs=json.loads(r["logs"] or "[]"),
        attempt_number=r["attempt_number"] or 1,
    )
