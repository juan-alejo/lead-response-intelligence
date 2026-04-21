"""Weekly reporter: outreach priority + vertical stats + competitor distribution."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.models import (
    Classification,
    CompetitorTool,
    FormType,
    Response,
    ResponseChannel,
    Submission,
    SubmissionMethod,
)
from src.reporting import WeeklyReporter


def _sub(sid: str, vertical: str, *, pid: str | None = None) -> Submission:
    return Submission(
        submission_id=sid,
        prospect_place_id=pid or f"p_{sid}",
        business_name=f"Biz {sid}",
        vertical=vertical,  # free-form per the new registry-backed model
        submission_method=SubmissionMethod.CONTACT_FORM,
        expected_sender_phone="+15555550100",
        expected_sender_email="response@test.example.com",
        submitted_at=datetime(2026, 4, 21, 14, 0),
    )


def _resp(rid: str, sid: str, elapsed: int) -> Response:
    return Response(
        response_id=rid,
        channel=ResponseChannel.EMAIL,
        received_at=datetime(2026, 4, 21, 14, 0),
        matched_submission_id=sid,
        elapsed_seconds=elapsed,
    )


def test_outreach_priority_filters_fast_responders(tmp_path: Path) -> None:
    subs = [_sub("s1", "law_firm"), _sub("s2", "law_firm")]
    # s1 responds in 30 seconds → "fast responder", should be filtered out.
    # s2 responds in 3 hours → should appear on the list.
    responses = [_resp("r1", "s1", 30), _resp("r2", "s2", 3 * 3600)]

    reporter = WeeklyReporter(tmp_path)
    paths = reporter.generate(subs, responses, [])

    rows = list(csv.DictReader(paths["outreach_priority"].open(encoding="utf-8")))
    business_names = {r["business_name"] for r in rows}
    assert "Biz s2" in business_names
    assert "Biz s1" not in business_names


def test_outreach_priority_puts_never_responded_first(tmp_path: Path) -> None:
    subs = [_sub("s1", "law_firm"), _sub("s2", "law_firm")]
    # s1 responds in 3 hours (slow but responded); s2 never responds.
    responses = [_resp("r1", "s1", 3 * 3600)]

    reporter = WeeklyReporter(tmp_path)
    paths = reporter.generate(subs, responses, [])

    rows = list(csv.DictReader(paths["outreach_priority"].open(encoding="utf-8")))
    # Never-responders are highest priority, so they come first.
    assert rows[0]["business_name"] == "Biz s2"
    assert rows[0]["elapsed_human"] == "never responded"


def test_vertical_stats_computes_percentages(tmp_path: Path) -> None:
    subs = [
        _sub("s1", "law_firm"),
        _sub("s2", "law_firm"),
        _sub("s3", "law_firm"),
        _sub("s4", "law_firm"),
    ]
    # 2 out of 4 responded within 24h.
    responses = [
        _resp("r1", "s1", 3600),  # within 24h
        _resp("r2", "s2", 12 * 3600),  # within 24h
    ]

    reporter = WeeklyReporter(tmp_path)
    paths = reporter.generate(subs, responses, [])

    rows = list(csv.DictReader(paths["vertical_stats"].open(encoding="utf-8")))
    assert len(rows) == 1
    row = rows[0]
    assert row["vertical"] == "law_firm"
    assert row["submissions"] == "4"
    assert row["pct_within_24h"] == "50%"
    assert row["pct_never_responded"] == "50%"


def test_competitor_distribution_counts_per_vertical(tmp_path: Path) -> None:
    subs = [
        _sub("s1", "law_firm", pid="p1"),
        _sub("s2", "law_firm", pid="p2"),
        _sub("s3", "med_spa", pid="p3"),
    ]
    classifications = [
        Classification(
            prospect_place_id="p1",
            form_type=FormType.CHAT_WIDGET,
            competitor_tools=[CompetitorTool.INTERCOM],
        ),
        Classification(
            prospect_place_id="p2",
            form_type=FormType.CHAT_WIDGET,
            competitor_tools=[CompetitorTool.INTERCOM],
        ),
        Classification(
            prospect_place_id="p3",
            form_type=FormType.BOOKING_WIDGET,
            competitor_tools=[CompetitorTool.CALENDLY],
        ),
    ]

    reporter = WeeklyReporter(tmp_path)
    paths = reporter.generate(subs, [], classifications)

    rows = list(csv.DictReader(paths["competitor_distribution"].open(encoding="utf-8")))
    by_key = {(r["vertical"], r["competitor_tool"]): int(r["count"]) for r in rows}
    assert by_key[("law_firm", "intercom")] == 2
    assert by_key[("med_spa", "calendly")] == 1
