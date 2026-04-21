"""Generate the weekly reports that feed the outbound sales motion.

Three outputs per run, written under REPORT_OUTPUT_DIR:

  - outreach_priority.csv: submissions sorted by slowest response, filtered
    to drop "fast responders" (< 2 minutes) so the sales team doesn't waste
    time on businesses that are already operationally tight.
  - vertical_stats.csv: per-vertical average response time, % responding in
    24h, % never responding.
  - competitor_distribution.csv: competitor-tool counts per vertical, so the
    team can spot patterns (e.g., "every med spa we test runs Calendly").
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from ..models import Classification, Response, Submission

_FAST_RESPONDER_THRESHOLD_SECONDS = 120  # 2 minutes
_WITHIN_24H_SECONDS = 24 * 3600


class WeeklyReporter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        submissions: list[Submission],
        responses: list[Response],
        classifications: list[Classification],
    ) -> dict[str, Path]:
        outreach_path = self._write_outreach_priority(submissions, responses)
        stats_path = self._write_vertical_stats(submissions, responses)
        competitors_path = self._write_competitor_distribution(submissions, classifications)
        return {
            "outreach_priority": outreach_path,
            "vertical_stats": stats_path,
            "competitor_distribution": competitors_path,
        }

    # --- Outreach priority ---

    def _write_outreach_priority(
        self, submissions: list[Submission], responses: list[Response]
    ) -> Path:
        elapsed_by_sub: dict[str, int | None] = {s.submission_id: None for s in submissions}
        for r in responses:
            if r.matched_submission_id and r.elapsed_seconds is not None:
                # Keep the fastest response per submission.
                current = elapsed_by_sub.get(r.matched_submission_id)
                if current is None or r.elapsed_seconds < current:
                    elapsed_by_sub[r.matched_submission_id] = r.elapsed_seconds

        # Drop fast responders so sales focuses on the actual opportunity.
        def priority_key(s: Submission) -> tuple[int, int]:
            elapsed = elapsed_by_sub.get(s.submission_id)
            if elapsed is None:
                # Never responded — highest priority.
                return (0, 0)
            return (1, -elapsed)

        prioritized = [
            s
            for s in submissions
            if (elapsed_by_sub.get(s.submission_id) or 10**9)
            >= _FAST_RESPONDER_THRESHOLD_SECONDS
        ]
        prioritized.sort(key=priority_key)

        path = self.output_dir / "outreach_priority.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "business_name",
                    "vertical",
                    "submission_method",
                    "elapsed_seconds",
                    "elapsed_human",
                    "prospect_email",
                    "prospect_phone",
                ]
            )
            for s in prioritized:
                elapsed = elapsed_by_sub.get(s.submission_id)
                writer.writerow(
                    [
                        s.business_name,
                        s.vertical.value,
                        s.submission_method.value,
                        elapsed if elapsed is not None else "",
                        _humanize(elapsed) if elapsed is not None else "never responded",
                        s.expected_sender_email or "",
                        s.expected_sender_phone or "",
                    ]
                )
        logger.info(f"[report] wrote outreach_priority ({len(prioritized)} rows) → {path}")
        return path

    # --- Vertical stats ---

    def _write_vertical_stats(
        self, submissions: list[Submission], responses: list[Response]
    ) -> Path:
        by_vertical: dict[str, list[Submission]] = defaultdict(list)
        for s in submissions:
            by_vertical[s.vertical.value].append(s)

        elapsed_by_sub: dict[str, int] = {}
        for r in responses:
            if r.matched_submission_id and r.elapsed_seconds is not None:
                current = elapsed_by_sub.get(r.matched_submission_id)
                if current is None or r.elapsed_seconds < current:
                    elapsed_by_sub[r.matched_submission_id] = r.elapsed_seconds

        path = self.output_dir / "vertical_stats.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "vertical",
                    "submissions",
                    "avg_response_seconds",
                    "pct_within_24h",
                    "pct_never_responded",
                ]
            )
            for vertical, subs in sorted(by_vertical.items()):
                elapseds = [
                    elapsed_by_sub[s.submission_id]
                    for s in subs
                    if s.submission_id in elapsed_by_sub
                ]
                total = len(subs)
                avg = sum(elapseds) / len(elapseds) if elapseds else None
                within_24h = sum(1 for e in elapseds if e <= _WITHIN_24H_SECONDS)
                never = total - len(elapseds)
                writer.writerow(
                    [
                        vertical,
                        total,
                        f"{avg:.0f}" if avg is not None else "",
                        f"{within_24h / total:.0%}" if total else "",
                        f"{never / total:.0%}" if total else "",
                    ]
                )
        logger.info(f"[report] wrote vertical_stats → {path}")
        return path

    # --- Competitor distribution ---

    def _write_competitor_distribution(
        self, submissions: list[Submission], classifications: list[Classification]
    ) -> Path:
        vertical_by_place: dict[str, str] = {
            s.prospect_place_id: s.vertical.value for s in submissions
        }
        counts: dict[tuple[str, str], int] = defaultdict(int)
        for c in classifications:
            vertical = vertical_by_place.get(c.prospect_place_id, "unknown")
            for tool in c.competitor_tools:
                counts[(vertical, tool.value)] += 1

        path = self.output_dir / "competitor_distribution.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["vertical", "competitor_tool", "count"])
            for (vertical, tool), count in sorted(counts.items()):
                writer.writerow([vertical, tool, count])
        logger.info(f"[report] wrote competitor_distribution → {path}")
        return path


def _humanize(seconds: int) -> str:
    td = timedelta(seconds=seconds)
    if td < timedelta(minutes=1):
        return f"{seconds}s"
    if td < timedelta(hours=1):
        return f"{seconds // 60}m"
    if td < timedelta(days=1):
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def monday_6am_et(reference: datetime | None = None) -> datetime:
    """Return the next Monday 6 AM ET from `reference` (or now)."""
    from ..models import _utc_now

    now = reference or _utc_now()
    # ET is UTC-4/5; using naive math is intentional — the scheduler
    # environment is responsible for timezone handling.
    days_ahead = (0 - now.weekday()) % 7 or 7
    return (now + timedelta(days=days_ahead)).replace(hour=10, minute=0, second=0, microsecond=0)
