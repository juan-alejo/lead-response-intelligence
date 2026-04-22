"""Streamlit operator dashboard.

Launch with:

    streamlit run src/dashboard/app.py

UX rules (keep these — they're why the dashboard is readable):

1. The main area shows only what the operator reads every day:
   title → metrics → tabs. Nothing else.
2. Integration status, language, GitHub, and run controls live in the
   sidebar so they're available without taking screen real estate.
3. The 'Run now' button is a single primary CTA in the sidebar. The
   options (borough, limit) default to sensible values; advanced users
   tweak them inside the same panel.

All user-visible strings flow through `i18n.tr()`. Default language is
Spanish — the primary market is LatAm — with English as the alternate.
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
from src.dashboard.i18n import LANGUAGES, get_lang, set_lang, tr  # noqa: E402
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

# ------------------------------------------------------------ minimal CSS

st.markdown(
    """
    <style>
      .pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px 2px;
        border: 1px solid transparent;
      }
      .pill-real { background: #dcfce7; color: #14532d; border-color: #86efac; }
      .pill-mock { background: #fef3c7; color: #713f12; border-color: #fde047; }
      .pill-off  { background: #e5e7eb; color: #374151; border-color: #9ca3af; }

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


def _load_run_history(path: Path = Path("data/run_history.json")) -> list[dict]:
    if not path.exists():
        return []
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _humanize_ago(iso_timestamp: str) -> str:
    """Turn an ISO timestamp into a 'hace X min/h/días' human string."""
    from datetime import datetime

    from src.models import _utc_now

    try:
        dt = datetime.fromisoformat(iso_timestamp)
    except ValueError:
        return iso_timestamp

    delta = _utc_now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return tr("lastrun.just_now")
    if seconds < 3600:
        return tr("lastrun.ago_minutes", n=seconds // 60)
    if seconds < 86400:
        return tr("lastrun.ago_hours", n=seconds // 3600)
    return tr("lastrun.ago_days", n=seconds // 86400)


settings = get_settings()
store = _load_store(settings.sqlite_path)

# ============================================================================
# SIDEBAR — every control that doesn't need to be front-and-center lives here.
# ============================================================================

with st.sidebar:
    # --- Language ---
    current_lang = get_lang()
    chosen = st.selectbox(
        tr("app.language"),
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(current_lang),
        format_func=lambda k: LANGUAGES[k],
        key="language_selector",
    )
    if chosen != current_lang:
        set_lang(chosen)
        st.rerun()

    st.divider()

    # --- Run pipeline (primary action) ---
    st.markdown(f"#### {tr('run.title').replace('### ', '').replace('▶ ', '▶ ')}")
    borough_choice = st.selectbox(
        tr("run.borough"),
        options=[b.value for b in Borough],
        index=0,
        format_func=lambda v: v.replace("_", " ").title(),
        key="borough_choice",
    )
    limit_choice = st.slider(
        tr("run.limit"), min_value=10, max_value=400, value=50, step=10
    )
    _vertical_count = len(get_registry().all())
    st.caption(tr("run.verticals_info", count=_vertical_count))
    run_now = st.button(tr("run.button"), type="primary", use_container_width=True)

    st.divider()

    # --- Integration status (compact) ---
    def _pill(label_key: str, mode: str) -> str:
        css = {"real": "pill-real", "mock": "pill-mock", "disabled": "pill-off"}[mode]
        icon = {"real": "🌐", "mock": "🧪", "disabled": "⏸"}[mode]
        return (
            f'<span class="pill {css}">{icon} {tr(label_key)}: '
            f'{tr(f"pills.mode.{mode}")}</span>'
        )

    st.markdown(f"**{tr('pills.header').replace('**', '')}**")
    pills_md = " ".join(
        [
            _pill("pills.label.places", settings.places_mode),
            _pill("pills.label.claude", settings.claude_mode),
            _pill("pills.label.twilio", settings.twilio_mode),
            _pill("pills.label.whatsapp", settings.whatsapp_mode),
            _pill("pills.label.gmail", settings.gmail_mode),
        ]
    )
    st.markdown(pills_md, unsafe_allow_html=True)
    storage_icon = "🗂" if settings.storage_backend == "sqlite" else "☁"
    st.caption(
        f"{tr('pills.storage').replace('**', '')} {storage_icon} {settings.storage_backend}"
    )

    st.divider()

    # --- Run history ---
    st.markdown(f"**{tr('history.title')}**")
    runs = _load_run_history()
    if not runs:
        st.caption(tr("history.empty"))
    else:
        history_rows = [
            {
                tr("history.col.when"): _humanize_ago(r["timestamp"]),
                tr("history.col.found"): r.get("ingested", 0),
                tr("history.col.matched"): (
                    f"{r.get('responses_matched', 0)}/{r.get('responses_pulled', 0)}"
                ),
            }
            for r in runs[:5]
        ]
        st.dataframe(
            pd.DataFrame(history_rows),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()
    st.link_button(
        tr("app.github_button"),
        "https://github.com/juan-alejo/lead-response-intelligence",
        use_container_width=True,
    )

# ============================================================================
# MAIN — header (compact) → metrics → tabs. No other noise.
# ============================================================================

st.markdown(f"# {tr('app.title')}")
st.caption(tr("app.subtitle"))

# --- Data loading ---

prospects_recent = store.recent_place_ids()
submissions = store.all_submissions()
responses = store.all_responses()
matched = [r for r in responses if r.matched_submission_id is not None]
match_rate = (len(matched) / len(responses)) if responses else 0.0

# --- Welcome hero for first-run (empty state) ---

_is_first_run = not prospects_recent and not submissions and not responses
if _is_first_run:
    st.info(tr("welcome.banner"))
    welcome_cols = st.columns([1, 1, 1])
    welcome_cols[0].markdown(tr("welcome.step1"))
    welcome_cols[1].markdown(tr("welcome.step2"))
    welcome_cols[2].markdown(tr("welcome.step3"))
    if st.button(tr("welcome.cta"), type="primary", use_container_width=False):
        with st.status(tr("run.status_running"), expanded=True) as status:
            result = run_all_verticals(
                settings,
                borough=Borough.MANHATTAN,
                limit=50,
                fetch_pages=False,
            )
            status.update(
                label=tr(
                    "run.status_done",
                    ingested=result.ingested,
                    matched=result.responses_matched,
                    pulled=result.responses_pulled,
                ),
                state="complete",
            )
        st.rerun()
    st.divider()

# --- Last-run indicator ---

_runs = _load_run_history()
if _runs:
    st.caption(f"🕒 {tr('lastrun.label')} {_humanize_ago(_runs[0]['timestamp'])}")

# --- Metrics ---

m1, m2, m3, m4 = st.columns(4)
m1.metric(tr("metrics.prospects"), len(prospects_recent), help=tr("metrics.prospects_help"))
m2.metric(tr("metrics.submissions"), len(submissions), help=tr("metrics.submissions_help"))
m3.metric(tr("metrics.responses"), len(responses), help=tr("metrics.responses_help"))
m4.metric(
    tr("metrics.match_rate"),
    f"{match_rate:.0%}" if responses else "—",
    help=tr("metrics.match_rate_help"),
)

# --- Run pipeline trigger (fires from sidebar button) ---

if run_now:
    with st.status(tr("run.status_running"), expanded=True) as status:
        result = run_all_verticals(
            settings,
            borough=Borough(borough_choice),
            limit=limit_choice,
            fetch_pages=False,
        )
        status.update(
            label=tr(
                "run.status_done",
                ingested=result.ingested,
                matched=result.responses_matched,
                pulled=result.responses_pulled,
            ),
            state="complete",
        )
    st.success(tr("run.success"))
    st.rerun()

# --- Tabs ---

tab_outreach, tab_stats, tab_competitors, tab_data, tab_settings = st.tabs(
    [
        tr("tab.outreach"),
        tr("tab.stats"),
        tr("tab.competitors"),
        tr("tab.data"),
        tr("tab.settings"),
    ]
)

# ---------- Tab 1: Outreach priority ----------

def _render_empty_state(title_key: str, desc_key: str, cta_key: str) -> None:
    """Uniform empty-state card: icon/title + explanation + action pointer."""
    st.markdown(f"### {tr(title_key)}")
    st.write(tr(desc_key))
    st.info(tr(cta_key))


with tab_outreach:
    df = _load_report(settings.report_output_dir / "outreach_priority.csv")
    if df.empty:
        _render_empty_state(
            "outreach.empty_title", "outreach.empty_desc", "outreach.empty_cta"
        )
    else:
        total = len(df)
        never = int((df["elapsed_human"] == "never responded").sum())
        st.markdown(tr("outreach.summary", total=total, never=never))

        vertical_options = sorted(df["vertical"].unique().tolist())
        vertical_filter = st.multiselect(
            tr("outreach.filter"),
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
                    tr("outreach.col.elapsed_sec"),
                    format="%d",
                    help=tr("outreach.col.elapsed_sec_help"),
                ),
                "elapsed_human": st.column_config.TextColumn(tr("outreach.col.elapsed_human")),
                "prospect_email": st.column_config.TextColumn(tr("outreach.col.email")),
                "prospect_phone": st.column_config.TextColumn(tr("outreach.col.phone")),
                "business_name": st.column_config.TextColumn(tr("outreach.col.business")),
                "vertical": st.column_config.TextColumn(tr("outreach.col.vertical")),
                "submission_method": st.column_config.TextColumn(tr("outreach.col.method")),
            },
        )

        st.download_button(
            tr("outreach.download"),
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="outreach_priority_filtered.csv",
            mime="text/csv",
            use_container_width=False,
        )

# ---------- Tab 2: Vertical stats ----------

with tab_stats:
    df = _load_report(settings.report_output_dir / "vertical_stats.csv")
    if df.empty:
        _render_empty_state(
            "stats.empty_title", "stats.empty_desc", "stats.empty_cta"
        )
    else:
        st.caption(tr("stats.caption"))

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
        _render_empty_state(
            "competitors.empty_title",
            "competitors.empty_desc",
            "competitors.empty_cta",
        )
    else:
        st.caption(tr("competitors.caption"))

        pivoted = df.pivot(
            index="vertical", columns="competitor_tool", values="count"
        ).fillna(0)
        st.bar_chart(pivoted, height=320)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Tab 4: Raw data ----------

with tab_data:
    st.caption(tr("data.caption"))

    data_tab = st.radio(
        tr("data.radio"),
        options=[tr("data.option.submissions"), tr("data.option.responses")],
        horizontal=True,
    )

    if data_tab == tr("data.option.submissions"):
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
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info(tr("data.empty.submissions"))
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
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info(tr("data.empty.responses"))

# ---------- Tab 5: Settings ----------

with tab_settings:
    render_settings_tab(env_path=_REPO_ROOT / ".env")

st.divider()
st.caption(tr("footer.source"))
