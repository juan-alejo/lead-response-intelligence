"""Streamlit operator dashboard.

Launch with:

    streamlit run src/dashboard/app.py

UI philosophy: this is the panel a non-technical operator sees when they
buy the tool. Every number should come with context, every control
should telegraph what it does before you click, and the status of every
integration should be visible without digging into a tab.

Keep this file the thin presentation layer — computation that matters
to the business lives in the pipeline / reporting modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.dashboard.settings_tab import render_settings_tab  # noqa: E402
from src.models import Borough  # noqa: E402
from src.pipeline import run_all_verticals  # noqa: E402
from src.storage import SQLiteStore  # noqa: E402
from src.verticals import get_registry  # noqa: E402

st.set_page_config(
    page_title="Lead Response Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------ tiny CSS polish

st.markdown(
    """
    <style>
      /* Integration status pills shown under the hero */
      .pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 500;
        margin: 2px 4px 2px 0;
        border: 1px solid transparent;
      }
      .pill-real { background: #dcfce7; color: #14532d; border-color: #86efac; }
      .pill-mock { background: #fef3c7; color: #713f12; border-color: #fde047; }
      .pill-off  { background: #e5e7eb; color: #374151; border-color: #9ca3af; }

      /* Subtle surface for the "Run pipeline" card */
      .run-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.07), rgba(14,165,233,0.07));
        padding: 18px 22px;
        border-radius: 12px;
        border: 1px solid rgba(99,102,241,0.25);
        margin-bottom: 8px;
      }

      /* Tighter tab list */
      div[data-baseweb="tab-list"] button { font-size: 15px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def _load_store(sqlite_path: Path) -> SQLiteStore:
    return SQLiteStore(sqlite_path)


def _load_report(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


settings = get_settings()
store = _load_store(settings.sqlite_path)

# ------------------------------------------------------------ Hero

hero_col_title, hero_col_action = st.columns([5, 2])
with hero_col_title:
    st.markdown("# 📡 Lead Response Intelligence")
    st.caption(
        "Pipeline that discovers prospects, classifies their inbound-contact "
        "mechanism, watches for responses across SMS / WhatsApp / email / "
        "voice, and produces a prioritized outreach list every Monday."
    )

with hero_col_action:
    st.write("")
    st.write("")
    st.link_button(
        "📖 GitHub repo",
        "https://github.com/juan-alejo/lead-response-intelligence",
        use_container_width=True,
    )

# ------------------------------------------------------------ Integration status row

def _mode_pill(label: str, mode: str) -> str:
    """Render an integration as a colored pill so the operator can skim the
    status of the entire stack in one glance."""
    css = {"real": "pill-real", "mock": "pill-mock", "disabled": "pill-off"}[mode]
    icon = {"real": "🌐", "mock": "🧪", "disabled": "⏸"}[mode]
    return f'<span class="pill {css}">{icon} {label}: {mode}</span>'


pills = [
    _mode_pill("Places", settings.places_mode),
    _mode_pill("Claude", settings.claude_mode),
    _mode_pill("Twilio SMS", settings.twilio_mode),
    _mode_pill("WhatsApp", settings.whatsapp_mode),
    _mode_pill("Gmail", settings.gmail_mode),
    _mode_pill("Storage", settings.storage_backend),
]
st.markdown(
    f"**Integrations:** {' '.join(pills)}",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------ Summary metrics

prospects_recent = store.recent_place_ids()
submissions = store.all_submissions()
responses = store.all_responses()
matched = [r for r in responses if r.matched_submission_id is not None]
match_rate = (len(matched) / len(responses)) if responses else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Prospects tracked",
    len(prospects_recent),
    help="Businesses discovered and persisted in the last 90 days.",
)
m2.metric(
    "Submissions queued",
    len(submissions),
    help="Test leads ready for the operator to submit manually (Phase 1).",
)
m3.metric(
    "Responses captured",
    len(responses),
    help="All inbound messages across every enabled channel.",
)
m4.metric(
    "Match rate",
    f"{match_rate:.0%}" if responses else "—",
    help=(
        "Fraction of inbound responses that were successfully attributed to "
        "an originating submission. Target ≥95% on well-formed data."
    ),
)

# ------------------------------------------------------------ Run pipeline card

st.markdown(
    '<div class="run-card">',
    unsafe_allow_html=True,
)
st.markdown("### ▶ Run weekly pipeline")
st.caption(
    "In production this runs via cron every Monday at 6 AM ET. The button "
    "below is the manual trigger — useful after editing verticals or when "
    "you want to show a client a live run."
)

run_col1, run_col2, run_col3 = st.columns([2, 2, 1])
borough_choice = run_col1.selectbox(
    "Borough",
    options=[b.value for b in Borough],
    index=0,
    format_func=lambda v: v.replace("_", " ").title(),
    key="borough_choice",
)
limit_choice = run_col2.slider(
    "Max prospects per vertical", min_value=10, max_value=400, value=50, step=10
)
run_col3.write("")
run_col3.write("")
run_now = run_col3.button("🚀 Run now", type="primary", use_container_width=True)

_vertical_count = len(get_registry().all())
st.caption(
    f"Will run **{_vertical_count} vertical(s)** currently configured "
    "(edit in the Settings tab below)."
)

if run_now:
    with st.status("Running full pipeline…", expanded=True) as status:
        status.update(label="Ingesting prospects from every vertical…")
        result = run_all_verticals(
            settings,
            borough=Borough(borough_choice),
            limit=limit_choice,
            fetch_pages=False,
        )
        status.update(
            label=(
                f"Done — ingested {result.ingested}, "
                f"matched {result.responses_matched}/{result.responses_pulled} "
                "responses."
            ),
            state="complete",
        )
    st.success("✅ Reports refreshed. See tabs below.")
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------ Tabs

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
            "📭 No outreach priority report yet — hit **Run now** above to generate one."
        )
    else:
        total = len(df)
        never = (df["elapsed_human"] == "never responded").sum()
        st.markdown(
            f"**{total} prospects** queued for outreach — "
            f"**{never}** never responded (highest-priority cohort). "
            "Sub-2-minute responders are filtered out automatically."
        )

        vertical_options = sorted(df["vertical"].unique().tolist())
        vertical_filter = st.multiselect(
            "Filter by vertical",
            options=vertical_options,
            default=vertical_options,
        )
        filtered = df[df["vertical"].isin(vertical_filter)] if vertical_filter else df

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "elapsed_seconds": st.column_config.NumberColumn(
                    "Elapsed (sec)",
                    format="%d",
                    help="Null means never responded.",
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
            use_container_width=False,
        )

# ---------- Tab 2: Vertical stats ----------

with tab_stats:
    df = _load_report(settings.report_output_dir / "vertical_stats.csv")
    if df.empty:
        st.info("📭 No vertical stats yet — run the pipeline to generate them.")
    else:
        st.caption(
            "Response behaviour per vertical. Bar chart shows average response "
            "time in seconds — lower = faster — so shorter bars mean less "
            "opportunity for the sales team."
        )

        chart_df = df.copy()
        chart_df["avg_response_seconds"] = pd.to_numeric(
            chart_df["avg_response_seconds"], errors="coerce"
        ).fillna(0)
        st.bar_chart(chart_df, x="vertical", y="avg_response_seconds", height=320)

        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Tab 3: Competitor distribution ----------

with tab_competitors:
    df = _load_report(settings.report_output_dir / "competitor_distribution.csv")
    if df.empty:
        st.info(
            "📭 No competitor distribution yet — run the pipeline to generate it."
        )
    else:
        st.caption(
            "Chat / booking tools detected on prospect websites. A cluster of "
            "one tool in one vertical is a pitch signal: **integrate** with it, "
            "don't replace it."
        )

        pivoted = df.pivot(
            index="vertical", columns="competitor_tool", values="count"
        ).fillna(0)
        st.bar_chart(pivoted, height=320)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Tab 4: Raw data ----------

with tab_data:
    st.caption(
        "Direct views of the underlying SQLite tables. Useful for debugging "
        "the matcher on a specific prospect, and for spot-checking what the "
        "pipeline stored."
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
    "Pipeline source: "
    "[github.com/juan-alejo/lead-response-intelligence](https://github.com/juan-alejo/lead-response-intelligence)"
)
