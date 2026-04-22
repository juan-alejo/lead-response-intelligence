"""Streamlit operator dashboard.

Launch with:

    streamlit run src/dashboard/app.py

UX rules (keep these — they're why the dashboard is readable):

1. Tabs are at the top of the main area so navigation is always reachable.
2. The "Inicio" tab holds metrics, the welcome hero (first-run), and the
   last-run indicator. The other tabs hold data + settings.
3. Integration status, language, GitHub, run controls, and run history
   all live in the collapsible sidebar so they're available without
   taking screen real estate.
4. The 'Run now' button is a single primary CTA in the sidebar. The
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

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.dashboard.auth import require_auth  # noqa: E402
from src.dashboard.i18n import LANGUAGES, get_lang, set_lang, tr  # noqa: E402
from src.dashboard.phase2_tab import render_phase2_tab  # noqa: E402
from src.dashboard.settings_tab import render_settings_tab  # noqa: E402
from src.locations import get_location_registry  # noqa: E402
from src.pipeline import run_all_verticals  # noqa: E402
from src.storage import SQLiteStore  # noqa: E402
from src.verticals import get_vertical_registry  # noqa: E402

st.set_page_config(
    page_title="Lead Response Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

require_auth()

# ------------------------------------------------------------ CSS

st.markdown(
    """
    <style>
      /* ---------- Status pills ---------- */
      .pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px 2px;
        border: 1px solid transparent;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
      }
      .pill:hover { transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.12); }
      .pill-real { background: #dcfce7; color: #14532d; border-color: #86efac; }
      .pill-mock { background: #fef3c7; color: #713f12; border-color: #fde047; }
      .pill-off  { background: #e5e7eb; color: #374151; border-color: #9ca3af; }

      /* ---------- Tabs — bigger, more prominent since they're at the top ---------- */
      div[data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid rgba(99, 102, 241, 0.1);
        padding-bottom: 2px;
      }
      div[data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 500;
        padding: 10px 18px !important;
      }
      div[data-baseweb="tab-list"] button[aria-selected="true"] {
        font-weight: 700;
        color: rgb(99, 102, 241) !important;
      }

      /* ---------- Metric cards ---------- */
      div[data-testid="stMetric"] {
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.18);
        border-radius: 12px;
        padding: 14px 16px;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
      }
      div[data-testid="stMetric"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.12);
      }
      div[data-testid="stMetricLabel"] { font-size: 13px; font-weight: 500; opacity: 0.9; }
      div[data-testid="stMetricValue"] { font-size: 34px !important; font-weight: 700; }

      /* ---------- Expanders ---------- */
      details[data-testid="stExpander"] {
        border: 1px solid rgba(99, 102, 241, 0.18);
        border-radius: 10px;
        margin-bottom: 8px;
      }
      details[data-testid="stExpander"] summary { padding: 10px 14px; font-weight: 500; }

      /* ---------- Buttons ---------- */
      div[data-testid="stButton"] > button {
        border-radius: 8px;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
      }
      div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.25);
      }

      /* ---------- Sidebar ---------- */
      section[data-testid="stSidebar"] hr { margin: 10px 0; opacity: 0.25; }

      /* ---------- Hero card on the Home tab ---------- */
      .hero-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(14,165,233,0.08));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 16px;
      }
      .hero-card h1 { margin-top: 0 !important; font-size: 30px !important; }

      /* ---------- Caption polish ---------- */
      div[data-testid="stCaptionContainer"] { opacity: 0.85; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------ Helpers


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


def _render_empty_state(title_key: str, desc_key: str, cta_key: str) -> None:
    st.markdown(f"### {tr(title_key)}")
    st.write(tr(desc_key))
    st.info(tr(cta_key))


def _execute_pipeline(
    *,
    location: str,
    limit: int,
    celebrate_first_run: bool = False,
) -> None:
    """Run the pipeline with friendly status updates + error handling.

    When a first-time run succeeds, throws a single confetti burst so the
    moment is memorable for demos. Failures surface as st.error instead
    of bubbling up as a raw stack trace.
    """
    had_data_before = bool(
        store.recent_place_ids() or store.all_submissions() or store.all_responses()
    )
    try:
        with st.status(tr("run.status_running"), expanded=True) as status:
            result = run_all_verticals(
                settings,
                location=location,
                limit=limit,
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
        if celebrate_first_run and not had_data_before:
            st.balloons()
        st.rerun()
    except Exception as e:  # noqa: BLE001
        st.error(tr("run.error", error=str(e)[:200]))


# ------------------------------------------------------------ Data loading

settings = get_settings()
store = _load_store(settings.sqlite_path)

prospects_recent = store.recent_place_ids()
submissions = store.all_submissions()
responses = store.all_responses()
matched = [r for r in responses if r.matched_submission_id is not None]
match_rate = (len(matched) / len(responses)) if responses else 0.0

_is_first_run = not prospects_recent and not submissions and not responses
_runs = _load_run_history()

# ============================================================================
# SIDEBAR
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

    # --- Run pipeline ---
    st.markdown(f"#### {tr('run.title').replace('### ', '').replace('▶ ', '▶ ')}")
    _location_registry = get_location_registry()
    _location_names = _location_registry.names()
    location_choice = st.selectbox(
        tr("run.location"),
        options=_location_names,
        index=0,
        format_func=lambda n: _location_registry.get(n).display_name,
        key="location_choice",
    )
    limit_choice = st.slider(
        tr("run.limit"), min_value=10, max_value=400, value=50, step=10
    )
    _vertical_count = len(get_vertical_registry().all())
    st.caption(tr("run.verticals_info", count=_vertical_count))
    run_now = st.button(tr("run.button"), type="primary", use_container_width=True)

    st.divider()

    # --- Integration status ---
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
    if not _runs:
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
            for r in _runs[:5]
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
# MAIN — tabs at the top, Inicio tab holds hero + metrics
# ============================================================================

(
    tab_home,
    tab_outreach,
    tab_stats,
    tab_competitors,
    tab_data,
    tab_phase2,
    tab_settings,
) = st.tabs(
    [
        tr("tab.home"),
        tr("tab.outreach"),
        tr("tab.stats"),
        tr("tab.competitors"),
        tr("tab.data"),
        tr("tab.phase2"),
        tr("tab.settings"),
    ]
)

# Sidebar-triggered run — we execute BEFORE rendering tab contents so any
# successful run refreshes the data the tabs read.
if run_now:
    _execute_pipeline(
        location=location_choice,
        limit=limit_choice,
        celebrate_first_run=True,
    )

# ---------- Tab: Inicio ----------

with tab_home:
    # Hero card with title + subtitle.
    st.markdown(
        f"""
        <div class="hero-card">
            <h1>{tr('app.title')}</h1>
            <p style="opacity: 0.85; font-size: 15px; margin: 0;">
                {tr('app.subtitle')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Welcome hero only on first-run.
    if _is_first_run:
        st.info(tr("welcome.banner"))
        welcome_cols = st.columns([1, 1, 1])
        welcome_cols[0].markdown(tr("welcome.step1"))
        welcome_cols[1].markdown(tr("welcome.step2"))
        welcome_cols[2].markdown(tr("welcome.step3"))
        if st.button(tr("welcome.cta"), type="primary", use_container_width=False):
            _execute_pipeline(
                location=get_location_registry().names()[0],
                limit=50,
                celebrate_first_run=True,
            )
        st.divider()

    # Last-run indicator.
    if _runs:
        st.caption(f"🕒 {tr('lastrun.label')} {_humanize_ago(_runs[0]['timestamp'])}")

    # Metrics row.
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(tr("metrics.prospects"), len(prospects_recent), help=tr("metrics.prospects_help"))
    m2.metric(tr("metrics.submissions"), len(submissions), help=tr("metrics.submissions_help"))
    m3.metric(tr("metrics.responses"), len(responses), help=tr("metrics.responses_help"))
    m4.metric(
        tr("metrics.match_rate"),
        f"{match_rate:.0%}" if responses else "—",
        help=tr("metrics.match_rate_help"),
    )

    # --- Insights + action cards (only when there's actual data) ---

    outreach_df = _load_report(settings.report_output_dir / "outreach_priority.csv")
    if not outreach_df.empty or responses:
        st.write("")  # small vertical spacer
        insight_col, action_col = st.columns(2)

        # Insight card ──
        with insight_col:
            st.markdown(f"##### {tr('home.insight_title')}")
            insights: list[str] = []
            if not outreach_df.empty:
                never_count = int(
                    (outreach_df["elapsed_human"] == "never responded").sum()
                )
                if never_count > 0:
                    insights.append(
                        tr("home.insight_never_responded", count=never_count)
                    )
                # Pick the slowest responder (highest elapsed_seconds, non-null).
                slow_df = outreach_df.dropna(subset=["elapsed_seconds"])
                if not slow_df.empty:
                    worst = slow_df.loc[slow_df["elapsed_seconds"].idxmax()]
                    insights.append(
                        tr(
                            "home.insight_worst_responder",
                            name=worst["business_name"],
                            vertical=worst["vertical"],
                            elapsed=worst["elapsed_human"],
                        )
                    )
            if responses:
                if match_rate >= 0.9:
                    insights.append(
                        tr("home.insight_good_match_rate", rate=match_rate)
                    )
                elif match_rate < 0.6 and match_rate > 0:
                    insights.append(
                        tr("home.insight_low_match_rate", rate=match_rate)
                    )
            for line in insights[:2]:  # keep the card compact
                st.markdown(f"- {line}")

        # Action card ──
        with action_col:
            st.markdown(f"##### {tr('home.action_title')}")
            in_demo = all(
                getattr(settings, f"{m}_mode") == "mock"
                for m in ("claude", "places", "twilio", "whatsapp", "gmail")
            )
            if not _runs:
                st.info(tr("home.action_no_data"))
            elif in_demo:
                st.warning(tr("home.action_demo_mode"))
            else:
                total = len(outreach_df) if not outreach_df.empty else 0
                st.success(tr("home.action_ready_to_work", count=total))

    # Quick navigation hint.
    st.caption(tr("home.navigation_hint"))

# ---------- Tab: Outreach priority ----------

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

        filter_col1, filter_col2 = st.columns([3, 2])
        with filter_col1:
            vertical_options = sorted(df["vertical"].unique().tolist())
            vertical_filter = st.multiselect(
                tr("outreach.filter"),
                options=vertical_options,
                default=vertical_options,
            )
        with filter_col2:
            st.write("")
            st.write("")
            only_never = st.toggle(tr("outreach.only_never"), value=False)

        filtered = df[df["vertical"].isin(vertical_filter)] if vertical_filter else df
        if only_never:
            filtered = filtered[filtered["elapsed_human"] == "never responded"]

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

# ---------- Tab: Vertical stats ----------

with tab_stats:
    df = _load_report(settings.report_output_dir / "vertical_stats.csv")
    if df.empty:
        _render_empty_state("stats.empty_title", "stats.empty_desc", "stats.empty_cta")
    else:
        st.caption(tr("stats.caption"))

        chart_df = df.copy()
        chart_df["avg_response_seconds"] = pd.to_numeric(
            chart_df["avg_response_seconds"], errors="coerce"
        ).fillna(0)

        # Altair bar chart — sortable, color-coded, interactive tooltip.
        chart = (
            alt.Chart(chart_df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("vertical:N", sort="-y", title=tr("outreach.col.vertical")),
                y=alt.Y(
                    "avg_response_seconds:Q",
                    title=tr("stats.y_label"),
                ),
                color=alt.Color(
                    "avg_response_seconds:Q",
                    scale=alt.Scale(scheme="redyellowgreen", reverse=True),
                    legend=None,
                ),
                tooltip=["vertical", "submissions", "avg_response_seconds",
                         "pct_within_24h", "pct_never_responded"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇ CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="vertical_stats.csv",
            mime="text/csv",
            use_container_width=False,
        )

# ---------- Tab: Competitor distribution ----------

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

        # Altair stacked bar — vertical on x, counts stacked by tool.
        chart = (
            alt.Chart(df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("vertical:N", title=tr("outreach.col.vertical")),
                y=alt.Y("count:Q", title=tr("competitors.y_label")),
                color=alt.Color(
                    "competitor_tool:N",
                    scale=alt.Scale(scheme="tableau10"),
                    legend=alt.Legend(title=tr("competitors.legend")),
                ),
                tooltip=["vertical", "competitor_tool", "count"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇ CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="competitor_distribution.csv",
            mime="text/csv",
            use_container_width=False,
        )

# ---------- Tab: Raw data ----------

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

# ---------- Tab: Phase 2 — automated form submission ----------

with tab_phase2:
    render_phase2_tab(settings=settings, store=store)

# ---------- Tab: Settings ----------

with tab_settings:
    render_settings_tab(env_path=_REPO_ROOT / ".env")

st.divider()
st.caption(tr("footer.source"))
