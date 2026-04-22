"""Phase 2 dashboard tab — automated form submission queue.

Surfaces the three things an operator actually cares about:

1. **Queue state** — how many submissions are pending / attempted / stuck.
2. **Audit trail** — per-attempt logs so a human can verify what the bot did.
3. **Manual kick-off** — a single CTA that runs the mock submitter on the
   current pending batch (live Playwright runs come through the same code
   path once the operator plugs in the custom Phase 2 submitter).

Follows the dashboard-wide UX rules: every string flows through `tr()`, and
the whole tab stays useful whether the flag is on or off — showing a
teaser + link to the commercial spec when Phase 2 is disabled.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..config import Settings
from ..models import (
    Submission,
    SubmissionAttempt,
    SubmissionAttemptStatus,
)
from ..pipeline import Pipeline
from ..storage import Storage
from .i18n import tr

_STATUS_LABELS = {
    SubmissionAttemptStatus.PENDING: ("pending", "🕓"),
    SubmissionAttemptStatus.SUBMITTING: ("submitting", "⏳"),
    SubmissionAttemptStatus.COMPLETED: ("completed", "✅"),
    SubmissionAttemptStatus.FAILED: ("failed", "❌"),
    SubmissionAttemptStatus.NEEDS_MANUAL: ("needs_manual", "🙋"),
}


def render_phase2_tab(*, settings: Settings, store: Storage) -> None:
    """Render the Phase 2 tab. Self-contained; no state leakage into other tabs."""
    st.markdown(tr("phase2.title"))
    st.caption(tr("phase2.caption"))

    if not settings.phase_2_enabled:
        _render_disabled_teaser()
        return

    _render_summary(store)
    st.divider()
    _render_run_panel(settings, store)
    st.divider()
    _render_attempts_table(store)


# ---------------------------------------------------------------- disabled view


def _render_disabled_teaser() -> None:
    st.info(tr("phase2.disabled_banner"))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"##### {tr('phase2.teaser_what_title')}")
        st.markdown(tr("phase2.teaser_what_body"))
    with col2:
        st.markdown(f"##### {tr('phase2.teaser_cost_title')}")
        st.markdown(tr("phase2.teaser_cost_body"))

    st.markdown("")
    st.markdown(
        tr(
            "phase2.enable_hint",
            flag="PHASE_2_ENABLED=true",
            spec_path="docs/PHASE_2_SPEC.md",
        )
    )


# ---------------------------------------------------------------- summary row


def _render_summary(store: Storage) -> None:
    submissions = store.all_submissions()
    attempts = store.all_attempts()
    latest_by_sub = _latest_attempt_by_submission(attempts)

    pending = sum(
        1 for s in submissions if s.submission_id not in latest_by_sub
    )
    completed = sum(
        1
        for a in latest_by_sub.values()
        if a.status == SubmissionAttemptStatus.COMPLETED
    )
    failed = sum(
        1
        for a in latest_by_sub.values()
        if a.status == SubmissionAttemptStatus.FAILED
    )
    needs_manual = sum(
        1
        for a in latest_by_sub.values()
        if a.status == SubmissionAttemptStatus.NEEDS_MANUAL
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr("phase2.metric_pending"), pending)
    c2.metric(tr("phase2.metric_completed"), completed)
    c3.metric(tr("phase2.metric_needs_manual"), needs_manual)
    c4.metric(tr("phase2.metric_failed"), failed)


# ---------------------------------------------------------------- run panel


def _render_run_panel(settings: Settings, store: Storage) -> None:
    """Single CTA + per-batch limit. Uses MockFormSubmitter when mode=mock."""
    st.markdown(f"##### {tr('phase2.run_title')}")
    st.caption(tr("phase2.run_caption"))

    col1, col2 = st.columns([1, 2])
    with col1:
        limit = st.number_input(
            tr("phase2.run_limit"),
            min_value=1,
            max_value=500,
            value=min(settings.submitter_batch_limit, 50),
            step=5,
            help=tr("phase2.run_limit_help"),
        )
    with col2:
        st.write("")
        st.write("")
        go = st.button(
            tr("phase2.run_button"),
            type="primary",
            use_container_width=True,
            disabled=(settings.submitter_mode == "disabled"),
        )

    if go:
        _execute_batch(settings=settings, store=store, limit=int(limit))


def _execute_batch(*, settings: Settings, store: Storage, limit: int) -> None:
    # We reuse the pipeline's Phase 2 method so the dashboard path and the
    # cron path share the same behavior — fewer surprises for operators.
    with st.status(tr("phase2.run_status_running"), expanded=True) as status:
        try:
            pipeline = Pipeline(settings, storage=store)
            summary = pipeline.run_form_submission(limit=limit)
            status.update(
                label=tr(
                    "phase2.run_status_done",
                    attempted=summary.attempted,
                    completed=summary.completed,
                    manual=summary.needs_manual,
                    failed=summary.failed,
                ),
                state="complete",
            )
        except Exception as e:  # noqa: BLE001
            status.update(label=tr("phase2.run_status_error", error=str(e)[:200]), state="error")
            return
    st.success(tr("phase2.run_success"))
    st.rerun()


# ---------------------------------------------------------------- attempts


def _render_attempts_table(store: Storage) -> None:
    submissions = {s.submission_id: s for s in store.all_submissions()}
    attempts = store.all_attempts()
    if not attempts:
        st.info(tr("phase2.no_attempts"))
        return

    st.markdown(f"##### {tr('phase2.attempts_title')}")

    # Filter controls
    status_values = [s.value for s in SubmissionAttemptStatus]
    status_filter = st.multiselect(
        tr("phase2.filter_status"),
        options=status_values,
        default=[
            SubmissionAttemptStatus.COMPLETED.value,
            SubmissionAttemptStatus.NEEDS_MANUAL.value,
            SubmissionAttemptStatus.FAILED.value,
        ],
    )

    latest = _latest_attempt_by_submission(attempts)
    rows = []
    for sub_id, attempt in latest.items():
        if status_filter and attempt.status.value not in status_filter:
            continue
        sub: Submission | None = submissions.get(sub_id)
        label, icon = _STATUS_LABELS[attempt.status]
        rows.append(
            {
                "status": f"{icon} {tr(f'phase2.status_{label}')}",
                "business": sub.business_name if sub else sub_id,
                "vertical": sub.vertical if sub else "",
                "method": sub.submission_method.value if sub else "",
                "attempts": attempt.attempt_number,
                "duration_ms": attempt.duration_ms or 0,
                "completed_at": attempt.completed_at,
                "_id": attempt.attempt_id,
                "_sub_id": sub_id,
            }
        )

    if not rows:
        st.caption(tr("phase2.no_attempts_filtered"))
        return

    df = pd.DataFrame(rows).sort_values(
        by="completed_at", ascending=False, na_position="last"
    )

    visible = df.drop(columns=["_id", "_sub_id"])
    st.dataframe(
        visible,
        use_container_width=True,
        hide_index=True,
        column_config={
            "status": st.column_config.TextColumn(tr("phase2.col_status")),
            "business": st.column_config.TextColumn(tr("phase2.col_business")),
            "vertical": st.column_config.TextColumn(tr("phase2.col_vertical")),
            "method": st.column_config.TextColumn(tr("phase2.col_method")),
            "attempts": st.column_config.NumberColumn(
                tr("phase2.col_attempts"), format="%d"
            ),
            "duration_ms": st.column_config.NumberColumn(
                tr("phase2.col_duration_ms"), format="%d ms"
            ),
            "completed_at": st.column_config.DatetimeColumn(
                tr("phase2.col_completed_at")
            ),
        },
    )

    st.download_button(
        tr("phase2.download_csv"),
        data=visible.to_csv(index=False).encode("utf-8"),
        file_name="phase2_attempts.csv",
        mime="text/csv",
    )

    # Per-submission drill-down
    st.markdown(f"##### {tr('phase2.drilldown_title')}")
    st.caption(tr("phase2.drilldown_caption"))

    options = [(r["_sub_id"], r["business"]) for r in rows[:50]]
    if options:
        labels = {sub_id: biz for sub_id, biz in options}
        pick = st.selectbox(
            tr("phase2.drilldown_select"),
            options=[opt[0] for opt in options],
            format_func=lambda sid: labels.get(sid, sid),
            key="phase2_drilldown",
        )
        if pick:
            _render_attempt_log(store, pick)


def _render_attempt_log(store: Storage, submission_id: str) -> None:
    attempts = store.attempts_for_submission(submission_id)
    if not attempts:
        st.info(tr("phase2.no_attempts"))
        return

    for attempt in attempts:
        label, icon = _STATUS_LABELS[attempt.status]
        header = tr(
            "phase2.attempt_header",
            n=attempt.attempt_number,
            icon=icon,
            status=tr(f"phase2.status_{label}"),
        )
        with st.expander(header, expanded=(attempt == attempts[-1])):
            meta_cols = st.columns(3)
            meta_cols[0].caption(
                f"**{tr('phase2.col_duration_ms')}:** "
                f"{attempt.duration_ms or 0} ms"
            )
            meta_cols[1].caption(
                f"**{tr('phase2.col_started_at')}:** "
                f"{attempt.started_at or '—'}"
            )
            meta_cols[2].caption(
                f"**URL:** {attempt.form_url or '—'}"
            )
            if attempt.confirmation_text:
                st.success(f"💬 {attempt.confirmation_text}")
            if attempt.error_message:
                st.error(f"⚠ {attempt.error_message}")
            if attempt.logs:
                st.code("\n".join(attempt.logs), language="text")


# ---------------------------------------------------------------- helpers


def _latest_attempt_by_submission(
    attempts: list[SubmissionAttempt],
) -> dict[str, SubmissionAttempt]:
    latest: dict[str, SubmissionAttempt] = {}
    for a in attempts:
        prev = latest.get(a.submission_id)
        if prev is None or a.attempt_number > prev.attempt_number:
            latest[a.submission_id] = a
    return latest
