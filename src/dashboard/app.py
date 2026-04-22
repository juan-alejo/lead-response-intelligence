"""Streamlit operator dashboard.

Launch with:

    streamlit run src/dashboard/app.py

UI philosophy: this is the panel a non-technical operator sees when they
buy the tool. Every number should come with context, every control
should telegraph what it does before you click, and the status of every
integration should be visible without digging into a tab.

All user-visible strings go through `i18n.tr()` so the whole UI flips
language with a single dropdown. Default is Spanish — the primary market
is LatAm clients.

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

# ------------------------------------------------------------ tiny CSS polish

st.markdown(
    """
    <style>
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

      .run-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.07), rgba(14,165,233,0.07));
        padding: 18px 22px;
        border-radius: 12px;
        border: 1px solid rgba(99,102,241,0.25);
        margin-bottom: 8px;
      }

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

# ------------------------------------------------------------ Hero + language

hero_col_title, hero_col_lang, hero_col_gh = st.columns([5, 1.2, 1.2])

with hero_col_title:
    st.markdown(f"# {tr('app.title')}")
    st.caption(tr("app.subtitle"))

with hero_col_lang:
    st.write("")
    st.write("")
    current_lang = get_lang()
    chosen = st.selectbox(
        tr("app.language"),
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(current_lang),
        format_func=lambda k: LANGUAGES[k],
        key="language_selector",
        label_visibility="collapsed",
    )
    if chosen != current_lang:
        set_lang(chosen)
        st.rerun()

with hero_col_gh:
    st.write("")
    st.write("")
    st.link_button(
        tr("app.github_button"),
        "https://github.com/juan-alejo/lead-response-intelligence",
        use_container_width=True,
    )

# ------------------------------------------------------------ Integration pills row


def _mode_pill(label_key: str, mode: str) -> str:
    css = {"real": "pill-real", "mock": "pill-mock", "disabled": "pill-off"}[mode]
    icon = {"real": "🌐", "mock": "🧪", "disabled": "⏸"}[mode]
    label = tr(label_key)
    mode_label = tr(f"pills.mode.{mode}")
    return f'<span class="pill {css}">{icon} {label}: {mode_label}</span>'


pills = [
    _mode_pill("pills.label.places", settings.places_mode),
    _mode_pill("pills.label.claude", settings.claude_mode),
    _mode_pill("pills.label.twilio", settings.twilio_mode),
    _mode_pill("pills.label.whatsapp", settings.whatsapp_mode),
    _mode_pill("pills.label.gmail", settings.gmail_mode),
]
storage_icon = "🗂" if settings.storage_backend == "sqlite" else "☁"
st.markdown(
    f"{tr('pills.header')} {' '.join(pills)} &nbsp;&nbsp; "
    f"{tr('pills.storage')} {storage_icon} {settings.storage_backend}",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------ Metrics row

prospects_recent = store.recent_place_ids()
submissions = store.all_submissions()
responses = store.all_responses()
matched = [r for r in responses if r.matched_submission_id is not None]
match_rate = (len(matched) / len(responses)) if responses else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric(tr("metrics.prospects"), len(prospects_recent), help=tr("metrics.prospects_help"))
m2.metric(tr("metrics.submissions"), len(submissions), help=tr("metrics.submissions_help"))
m3.metric(tr("metrics.responses"), len(responses), help=tr("metrics.responses_help"))
m4.metric(
    tr("metrics.match_rate"),
    f"{match_rate:.0%}" if responses else "—",
    help=tr("metrics.match_rate_help"),
)

# ------------------------------------------------------------ Run pipeline card

st.markdown('<div class="run-card">', unsafe_allow_html=True)
st.markdown(tr("run.title"))
st.caption(tr("run.caption"))

run_col1, run_col2, run_col3 = st.columns([2, 2, 1])
borough_choice = run_col1.selectbox(
    tr("run.borough"),
    options=[b.value for b in Borough],
    index=0,
    format_func=lambda v: v.replace("_", " ").title(),
    key="borough_choice",
)
limit_choice = run_col2.slider(
    tr("run.limit"), min_value=10, max_value=400, value=50, step=10
)
run_col3.write("")
run_col3.write("")
run_now = run_col3.button(tr("run.button"), type="primary", use_container_width=True)

_vertical_count = len(get_registry().all())
st.caption(tr("run.verticals_info", count=_vertical_count))

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

st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------ Tabs

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

with tab_outreach:
    df = _load_report(settings.report_output_dir / "outreach_priority.csv")
    if df.empty:
        st.info(tr("outreach.empty"))
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
        st.info(tr("stats.empty"))
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
        st.info(tr("competitors.empty"))
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
