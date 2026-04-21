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

from ..models import Prospect, Response, Submission
from .base import Storage

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prospects (
    place_id        TEXT PRIMARY KEY,
    business_name   TEXT NOT NULL,
    vertical        TEXT NOT NULL,
    borough         TEXT NOT NULL,
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
"""


class SQLiteStore(Storage):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
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
                    place_id, business_name, vertical, borough,
                    website, phone, email, discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(place_id) DO UPDATE SET
                    business_name=excluded.business_name,
                    vertical=excluded.vertical,
                    borough=excluded.borough,
                    website=excluded.website,
                    phone=excluded.phone,
                    email=excluded.email
                """,
                [
                    (
                        p.place_id,
                        p.business_name,
                        p.vertical,
                        p.borough.value,
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
