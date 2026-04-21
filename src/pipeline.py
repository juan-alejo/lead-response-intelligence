"""End-to-end pipeline orchestration.

Single entry point that wires together ingestion → classification →
storage → monitoring → reporting. Every expensive dependency is resolved
via the `Settings` object so individual steps can be tested in isolation.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

from .classification import (
    ClaudeClassifier,
    CompetitorDetector,
    FormClassifier,
    HeuristicClassifier,
    PageFetcher,
)
from .config import Settings
from .ingestion import Deduplicator, GooglePlacesSource
from .models import (
    Borough,
    Classification,
    CompetitorTool,
    FormType,
    Prospect,
    Submission,
    SubmissionMethod,
    Vertical,
)
from .monitoring import GmailMockAdapter, ResponseMatcher, TwilioMockAdapter
from .reporting import WeeklyReporter
from .storage import SQLiteStore, Storage

_METHOD_BY_FORM_TYPE = {
    "contact_form": SubmissionMethod.CONTACT_FORM,
    "chat_widget": SubmissionMethod.CHAT_WIDGET,
    "booking_widget": SubmissionMethod.BOOKING_WIDGET,
    "none": None,
}


@dataclass
class PipelineResult:
    ingested: int = 0
    deduplicated: int = 0
    classified: int = 0
    submissions_queued: int = 0
    responses_pulled: int = 0
    responses_matched: int = 0
    report_paths: dict = field(default_factory=dict)


class Pipeline:
    def __init__(self, settings: Settings, storage: Storage | None = None) -> None:
        self.settings = settings
        self.storage = storage or SQLiteStore(settings.sqlite_path)
        self.reporter = WeeklyReporter(settings.report_output_dir)

    # ---------- public API ----------

    async def run_ingestion_and_classification(
        self,
        vertical: Vertical,
        borough: Borough,
        *,
        limit: int = 50,
        fetch_pages: bool = False,
    ) -> PipelineResult:
        """Phase 1 steps 1 + 2: discover prospects, classify their forms."""
        result = PipelineResult()

        # 1. Ingestion
        source = GooglePlacesSource(
            mode=self.settings.places_mode,
            api_key=self.settings.google_places_api_key,
            mock_fixture=self.settings.mock_places_fixture,
        )
        prospects = list(source.fetch(vertical, borough, limit=limit))
        result.ingested = len(prospects)

        recent = self.storage.recent_place_ids()
        dedup = Deduplicator(recent)
        fresh = dedup.filter(prospects)
        result.deduplicated = len(fresh)

        self.storage.upsert_prospects(fresh)

        # 2. Classification
        classifier = self._build_classifier()
        detector = CompetitorDetector()
        classifications: list[Classification] = []
        submissions: list[Submission] = []

        if fetch_pages:
            async with PageFetcher() as fetcher:
                for p in fresh:
                    if not p.website:
                        continue
                    page = await fetcher.fetch(p.website)
                    if page is None:
                        continue
                    c = self._classify_page(classifier, detector, p, page.html, page.url)
                    classifications.append(c)
                    sub = self._queue_submission(p, c)
                    if sub:
                        submissions.append(sub)
        else:
            # Offline path — hydrate classifications from the mock fixture so
            # the demo pipeline exercises competitor-detection output too.
            mock = _load_classification_fixture(self.settings.mock_classifications_fixture)
            for p in fresh:
                mock_entry = mock.get(p.place_id)
                if mock_entry is not None:
                    c = Classification(
                        prospect_place_id=p.place_id,
                        form_type=FormType(mock_entry["form_type"]),
                        form_url=p.website,
                        competitor_tools=[
                            CompetitorTool(t)
                            for t in mock_entry.get("competitor_tools", [])
                        ],
                    )
                else:
                    c = Classification(
                        prospect_place_id=p.place_id,
                        form_type=_infer_form_type_from_prospect(p),
                        form_url=p.website,
                    )
                classifications.append(c)
                sub = self._queue_submission(p, c)
                if sub:
                    submissions.append(sub)

        result.classified = len(classifications)
        result.submissions_queued = len(submissions)
        self.storage.upsert_submissions(submissions)
        self._classifications_cache = classifications  # used by reporting step
        return result

    def run_monitoring_and_reporting(self) -> PipelineResult:
        """Phase 1 steps 3 + 5: pull responses, match them, generate reports."""
        result = PipelineResult()

        twilio = TwilioMockAdapter(self.settings.mock_sms_fixture)
        gmail = GmailMockAdapter(self.settings.mock_email_fixture)

        raw_responses = list(twilio.pull_new_responses()) + list(gmail.pull_new_responses())
        result.responses_pulled = len(raw_responses)

        submissions = self.storage.all_submissions()
        matcher = ResponseMatcher(submissions)
        matched = matcher.match_all(raw_responses)
        result.responses_matched = sum(1 for r in matched if r.matched_submission_id)

        self.storage.upsert_responses(matched)

        classifications = getattr(self, "_classifications_cache", [])
        result.report_paths = self.reporter.generate(
            submissions=submissions,
            responses=matched,
            classifications=classifications,
        )
        return result

    # ---------- internals ----------

    def _build_classifier(self) -> FormClassifier:
        if self.settings.claude_mode == "real" and self.settings.anthropic_api_key:
            return ClaudeClassifier(
                api_key=self.settings.anthropic_api_key,
                model=self.settings.claude_model,
            )
        logger.info("[classifier] using heuristic (mock mode)")
        return HeuristicClassifier()

    def _classify_page(
        self,
        classifier: FormClassifier,
        detector: CompetitorDetector,
        prospect: Prospect,
        html: str,
        url: str,
    ) -> Classification:
        form_type = classifier.classify(html, url=url)
        tools = detector.detect(html)
        return Classification(
            prospect_place_id=prospect.place_id,
            form_type=form_type,
            form_url=url,
            competitor_tools=tools,
        )

    def _queue_submission(
        self, prospect: Prospect, classification: Classification
    ) -> Submission | None:
        method = _METHOD_BY_FORM_TYPE.get(classification.form_type.value)
        if method is None:
            return None  # Nothing to submit to.
        # `submitted_at` is stamped here on the assumption the operator has
        # already worked through the queue; in production this would be
        # backfilled by whichever tool actually submits the form.
        return Submission(
            submission_id=str(uuid.uuid4()),
            prospect_place_id=prospect.place_id,
            business_name=prospect.business_name,
            vertical=prospect.vertical,
            submission_method=method,
            expected_sender_phone=prospect.phone,
            expected_sender_email=prospect.email,
            submitted_at=_default_submitted_at(),
        )


def _load_classification_fixture(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _default_submitted_at() -> datetime:
    """Demo reference timestamp aligned with the response fixtures.

    Mock responses in data/fixtures/ use timestamps near 2026-04-21 14:30 —
    stamping submissions at 14:00 UTC gives realistic elapsed times in the
    reports (30 min, 3 hours, etc.) without depending on wall-clock `now()`.
    Real deployments backfill this from the operator's form submission time.
    """
    return datetime(2026, 4, 21, 14, 0, 0)


def _infer_form_type_from_prospect(prospect: Prospect) -> FormType:
    """Offline fallback used when we're not actually fetching pages.

    Assumes every discovered prospect has at least a basic contact form —
    good enough for CI smoke tests and demonstrating the pipeline shape.
    """
    return FormType.CONTACT_FORM if prospect.website else FormType.NONE


def run_full_pipeline(
    settings: Settings,
    *,
    vertical: Vertical = Vertical.LAW_FIRM,
    borough: Borough = Borough.MANHATTAN,
    limit: int = 50,
    fetch_pages: bool = False,
) -> PipelineResult:
    """Sync convenience wrapper for scripts / cron jobs."""
    pipeline = Pipeline(settings)
    ingestion_result = asyncio.run(
        pipeline.run_ingestion_and_classification(
            vertical, borough, limit=limit, fetch_pages=fetch_pages
        )
    )
    reporting_result = pipeline.run_monitoring_and_reporting()

    return PipelineResult(
        ingested=ingestion_result.ingested,
        deduplicated=ingestion_result.deduplicated,
        classified=ingestion_result.classified,
        submissions_queued=ingestion_result.submissions_queued,
        responses_pulled=reporting_result.responses_pulled,
        responses_matched=reporting_result.responses_matched,
        report_paths=reporting_result.report_paths,
    )


def run_all_verticals(
    settings: Settings,
    *,
    borough: Borough = Borough.MANHATTAN,
    limit: int = 50,
    fetch_pages: bool = False,
) -> PipelineResult:
    """Ingest every vertical sequentially, then generate one combined report.

    This is the intended weekly cron pattern: one Monday-morning run that
    covers every configured vertical in the target borough.
    """
    pipeline = Pipeline(settings)
    totals = PipelineResult()

    # Ingest + classify every vertical against the same storage, accumulating
    # classifications in the pipeline cache across calls.
    all_classifications: list[Classification] = []
    for vertical in [Vertical.LAW_FIRM, Vertical.HOME_SERVICES, Vertical.MED_SPA]:
        part = asyncio.run(
            pipeline.run_ingestion_and_classification(
                vertical, borough, limit=limit, fetch_pages=fetch_pages
            )
        )
        totals.ingested += part.ingested
        totals.deduplicated += part.deduplicated
        totals.classified += part.classified
        totals.submissions_queued += part.submissions_queued
        all_classifications.extend(pipeline._classifications_cache)

    pipeline._classifications_cache = all_classifications
    reporting = pipeline.run_monitoring_and_reporting()
    totals.responses_pulled = reporting.responses_pulled
    totals.responses_matched = reporting.responses_matched
    totals.report_paths = reporting.report_paths
    return totals
