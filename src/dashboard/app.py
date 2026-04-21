"""Streamlit operator dashboard.

Launch with:

    streamlit run src/dashboard/app.py

Everything here is read-only against the pipeline's SQLite store and
the generated report CSVs, with one write-side action: the "Run
pipeline" button, which invokes `run_all_verticals` synchronously.

Keep this file the thin presentation layer — any computation that
matters to the business (priorities, stats) lives in the reporting
module, not in the UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit's `streamlit run` entrypoint doesn't add the repo root to sys.path
# the way `python -m` does. Add it explicitly so `from src....` resolves.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd  # noqa: E402 — sys.path fix must precede these imports
import streamlit as st  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.dashboard.settings_tab import render_settings_tab  # noqa: E402
from src.models import Borough  # noqa: E402
from src.pipeline import run_all_verticals  # noqa: E402
from src.storage import SQLiteStore  # noqa: E402

st.set_page_config(
    page_title="Lead Response Intelligence",
    page_icon="📡",
    layout="wide",
)


@st.cache_resource
def _load_store(sqlite_path: Path) -> SQLiteStore:
    """Reuse a single SQLiteStore across reruns — Streamlit reruns the
    entire script on every interaction, and a fresh store instance per
    keystroke would be wasteful."""
    return SQLiteStore(sqlite_path)


def _load_report(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


settings = get_settings()
store = _load_store(settings.sqlite_path)

st.title("📡 Lead Response Intelligence")
st.caption(
    "Operator dashboard — internal tool. Pipeline discovers prospects, "
    "classifies their inbound-contact mechanism, watches for responses "
    "across SMS / email / voice, and produces a prioritized outreach list."
)

# ---------------------------------------------------------------- Summary row

prospects_recent = store.recent_place_ids()
submissions = store.all_submissions()
responses = store.all_responses()

matched = [r for r in responses if r.matched_submission_id is not None]
match_rate = (len(matched) / len(responses)) if responses else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Prospects tracked", len(prospects_recent))
col2.metric("Submissions queued", len(submissions))
col3.metric("Responses captured", len(responses))
col4.metric(
    "Response match rate",
    f"{match_rate:.0%}" if responses else "—",
    help="Percentage of inbound responses successfully attributed to an originating submission.",
)

st.divider()

# -------------------------------------------------------- Pipeline run trigger

with st.expander("▶ Run weekly pipeline now", expanded=False):
    st.caption(
        "Triggers a full ingestion + classification + monitoring + reporting "
        "cycle. In production this runs via cron at 6 AM ET every Monday; "
        "this button is the manual override."
    )
    borough_choice = st.selectbox(
        "Borough",
        options=[b.value for b in Borough],
        index=0,
        format_func=lambda v: v.replace("_", " ").title(),
    )
    limit_choice = st.slider(
        "Max prospects per vertical", min_value=10, max_value=400, value=50, step=10
    )
    if st.button("Run pipeline", type="primary"):
        with st.status("Running full pipeline…", expanded=True) as status:
            status.update(label="Ingesting prospects from all verticals…")
            result = run_all_verticals(
                settings,
                borough=Borough(borough_choice),
                limit=limit_choice,
                fetch_pages=False,
            )
            status.update(
                label=f"Done — ingested {result.ingested}, "
                f"matched {result.responses_matched}/{result.responses_pulled}",
                state="complete",
            )
        st.success(
            f"Pipeline complete. Reports written to `{settings.report_output_dir}`."
        )
        st.rerun()

# ------------------------------------------------------------------- Tabs

tab_outreach, tab_stats, tab_competitors, tab_data, tab_settings = st.tabs(
    [
        "🎯 Outreach priority",
        "📊 Vertical stats",
        "🕵 Competitor distribution",
        "🗂 Raw data",
        "⚙ Settings",
    ]
)

# ---------- Tab 1: Outreach priority ----------

with tab_outreach:
    df = _load_report(settings.report_output_dir / "outreach_priority.csv")
    if df.empty:
        st.info(
            "No outreach priority report yet — run the pipeline above to generate one."
        )
    else:
        st.caption(
            f"{len(df)} prospects queued for outreach, sorted by slowest response. "
            "Never-responders float to the top; sub-2-minute responders are filtered out."
        )

        vertical_filter = st.multiselect(
            "Filter by vertical",
            options=sorted(df["vertical"].unique().tolist()),
            default=sorted(df["vertical"].unique().tolist()),
        )
        filtered = df[df["vertical"].isin(vertical_filter)] if vertical_filter else df

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "elapsed_seconds": st.column_config.NumberColumn(
                    "Elapsed (sec)", format="%d", help="null means never responded"
                ),
                "elapsed_human": st.column_config.TextColumn("Elapsed"),
                "prospect_email": st.column_config.TextColumn("Email"),
                "prospect_phone": st.column_config.TextColumn("Phone"),
                "business_name": st.column_config.TextColumn("Business"),
                "vertical": st.column_config.TextColumn("Vertical"),
                "submission_method": st.column_config.TextColumn("Method"),
            },
        )

        st.download_button(
            "⬇ Download filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="outreach_priority_filtered.csv",
            mime="text/csv",
        )

# ---------- Tab 2: Vertical stats ----------

with tab_stats:
    df = _load_report(settings.report_output_dir / "vertical_stats.csv")
    if df.empty:
        st.info("No vertical stats report yet — run the pipeline to generate one.")
    else:
        st.caption("Response behaviour per vertical — where are the opportunities?")

        # Bar chart — avg response time.
        chart_df = df.copy()
        chart_df["avg_response_seconds"] = pd.to_numeric(
            chart_df["avg_response_seconds"], errors="coerce"
        ).fillna(0)
        st.bar_chart(
            chart_df, x="vertical", y="avg_response_seconds", height=300
        )
        st.caption("Average response time (seconds) per vertical. Lower = faster.")

        # Raw stats table.
        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Tab 3: Competitor distribution ----------

with tab_competitors:
    df = _load_report(settings.report_output_dir / "competitor_distribution.csv")
    if df.empty:
        st.info(
            "No competitor distribution report yet — run the pipeline to generate one."
        )
    else:
        st.caption(
            "Chat / booking tools detected on prospect websites, grouped by vertical. "
            "A cluster of 'calendly' in med_spa is a signal: pitch an integration, "
            "not a replacement."
        )

        # Pivot: vertical on rows, tools as columns, count as values.
        pivoted = df.pivot(
            index="vertical", columns="competitor_tool", values="count"
        ).fillna(0)
        st.bar_chart(pivoted, height=300)

        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Tab 4: Raw data ----------

with tab_data:
    st.caption(
        "Direct views of the underlying SQLite tables. Useful for debugging and "
        "hand-checking the matcher on a specific prospect."
    )

    data_tab = st.radio(
        "Table",
        options=["Submissions", "Responses"],
        horizontal=True,
    )

    if data_tab == "Submissions":
        rows = [
            {
                "submission_id": s.submission_id[:8] + "…",
                "business_name": s.business_name,
                "vertical": s.vertical,
                "submission_method": s.submission_method.value,
                "expected_sender_phone": s.expected_sender_phone,
                "expected_sender_email": s.expected_sender_email,
                "submitted_at": s.submitted_at,
            }
            for s in submissions
        ]
        if rows:
            st.dataframe(
                pd.DataFrame(rows), use_container_width=True, hide_index=True
            )
        else:
            st.info("No submissions yet.")
    else:
        rows = [
            {
                "response_id": r.response_id,
                "channel": r.channel.value,
                "received_at": r.received_at,
                "matched": "✅" if r.matched_submission_id else "❌",
                "elapsed_seconds": r.elapsed_seconds,
                "sender_phone": r.sender_phone,
                "sender_email": r.sender_email,
                "content_snippet": (
                    r.content_snippet[:80] + ("…" if len(r.content_snippet) > 80 else "")
                ),
            }
            for r in responses
        ]
        if rows:
            st.dataframe(
                pd.DataFrame(rows), use_container_width=True, hide_index=True
            )
        else:
            st.info("No responses yet.")

# ---------- Tab 5: Settings ----------

with tab_settings:
    render_settings_tab(env_path=_REPO_ROOT / ".env")

st.divider()
st.caption(
    "Pipeline source: github.com/juan-alejo/lead-response-intelligence  •  "
    "Storage: SQLite (swap to Airtable via Settings tab)"
)
