"""Settings tab — per-client configuration without code changes.

Design goals:
- Operators should never have to edit YAML or env vars by hand.
- Demo mode is a one-click "safe sandbox" that every demo starts from.
- Each external service has three states: **mock** (bundled fixtures),
  **real** (live API), or **disabled** (skipped entirely). Disabled
  matters because most clients only use a subset — LatAm clients care
  about WhatsApp, US clients about SMS, and so on.
- Help text is geographically aware — the tool explains what Twilio /
  WhatsApp / Gmail mean in the contexts where the buyer actually lives.

Persistence:
- API keys → `.env` (gitignored, treated as secrets).
- Verticals → `config/verticals.yaml` (tracked so defaults travel with the repo).
"""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from ..verticals import Vertical, get_registry

# --------------------------------------------------------------- Help blurbs

_HELP_ANTHROPIC = """\
**What it does:** classifies the type of contact form on each prospect's
website (contact form, chat widget, booking widget, or none). The
heuristic regex classifier handles 70% of sites for free; Claude handles
the ambiguous 30%.

**How to get an API key:**

1. Go to [console.anthropic.com](https://console.anthropic.com/) and sign in.
2. Profile → **API Keys** → **Create Key**. Copy the `sk-ant-...` value.

**Cost:** $5 free credits on signup, then ~$1-2 per week at the pipeline's
scale (~200 prospects/week).

**If you disable this:** the pipeline falls back to regex-only classification.
Accuracy drops ~15% on custom-built sites, but it's fine for early testing
and for clients who can't get an Anthropic account approved.
"""

_HELP_GOOGLE_PLACES = """\
**What it does:** discovers prospect businesses to test. Searches Google
Places for (e.g.) "law firm in Manhattan" and returns names, websites,
phones for the top N matches.

**How to get an API key:**

1. [console.cloud.google.com](https://console.cloud.google.com/) → create a project.
2. APIs & Services → Library → enable **"Places API"**.
3. Credentials → Create credentials → **API Key**. Copy the `AIza...` value.

**Cost:** Google gives **$200 / month free credit** — covers ~10,000
searches. Enough for almost any client.

**Catch:** Google requires a credit card on file even for the free tier.

**If you disable this:** prospects have to be uploaded via CSV (see the
"Raw data" tab). The rest of the pipeline works unchanged.
"""

_HELP_TWILIO_SMS = """\
**What it does:** receives SMS + voicemail responses from prospects on a
dedicated test phone number you own.

**Where to use it:** mainly US / Canada / Europe, where businesses reply
via SMS or phone when you fill out a form on their website.

**How to set up:**
1. Sign up at [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
   (free trial ~$15 credit).
2. Dashboard → Account SID + Auth Token (top right).
3. Phone Numbers → Buy a Number (~$1 / month for a US number).

**Cost:** $1/month for the number, ~$0.01 per inbound SMS.

**If you disable this:** the pipeline simply doesn't collect SMS or voice
responses. Useful if the prospect market communicates via email or
WhatsApp instead.
"""

_HELP_WHATSAPP = """\
**What it does:** receives WhatsApp Business replies from prospects. Uses
Twilio's WhatsApp API under the hood, so it **shares credentials with
the SMS/voice section** — no extra account to manage.

**Where to use it:** essential for **Argentina, Brazil, Mexico, India,
Southeast Asia, Spain**, and most markets outside the US where
businesses reply via WhatsApp, not SMS.

> **Para clientes en Argentina / LatAm:** esto es lo que necesitás. Las
> empresas acá responden por WhatsApp — SMS casi no se usa. Activá este
> canal y desactivá el de SMS/voz para ahorrarte el costo del número
> norteamericano.

**How to set up:**
1. Same Twilio account as SMS (reuse the Account SID + Auth Token above).
2. Twilio Console → **Messaging → Senders → WhatsApp senders**.
3. Either enable the **Twilio Sandbox for WhatsApp** (free, for dev) or
   register a real WhatsApp Business number (~$5-15/month).
4. Paste the sandbox/business WhatsApp number above.

**Cost:** free tier usable for dev/demos. Live numbers start ~$5/mo +
~$0.005 per message received.

**If you disable this:** no WhatsApp responses are collected.
"""

_HELP_GMAIL = """\
**What it does:** polls a dedicated Gmail inbox for replies to forms
that you filled out. Email is the most universal response channel —
every prospect's website form has an email field.

**How to set up:**
1. Create a dedicated Gmail address (e.g., `responses+clientname@gmail.com`).
2. [console.cloud.google.com](https://console.cloud.google.com/) → enable **Gmail API**.
3. Create OAuth 2.0 Client ID (Desktop app) → download `credentials.json`.
4. Paste the file path above. First run triggers an OAuth consent
   screen; a reusable token is saved afterwards.

**If you disable this:** no email responses are collected. Usually
unadvisable — email is the most reliable channel.
"""

_HELP_AIRTABLE = """\
**What it does:** persists prospects / submissions / responses in an
Airtable base so non-technical users can query, filter, and build
views directly in Airtable's UI.

**When to use it:** when the client's sales team works in Airtable
already and you want them to have a shared live view of the pipeline
data. Otherwise stick with SQLite — it's simpler, faster, and zero-config.

**How to set up:**
1. [airtable.com/create/tokens](https://airtable.com/create/tokens) →
   create a personal access token with read/write scopes.
2. Open your base → URL contains `appXXXXXXX` — that's the Base ID.
3. Paste token + Base ID above.
4. Base schema is documented in `src/storage/airtable_store.py`.

**If you disable this (use SQLite):** pipeline data lives in a local
`.sqlite` file only. Fine for single-operator setups.
"""

# --------------------------------------------------------------- .env I/O

_KEY_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)=(.*)$")


def _read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _KEY_RE.match(stripped)
        if match:
            data[match.group(1)] = match.group(2)
    return data


def _write_env(path: Path, values: dict[str, str]) -> None:
    existing_lines: list[str] = []
    seen: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _KEY_RE.match(line.strip())
            if match and match.group(1) in values:
                seen.add(match.group(1))
                existing_lines.append(f"{match.group(1)}={values[match.group(1)]}")
            else:
                existing_lines.append(line)
    for key, value in values.items():
        if key not in seen:
            existing_lines.append(f"{key}={value}")
    path.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------- UI helpers

_MODE_OPTIONS = ["mock", "real", "disabled"]
_MODE_LABELS = {
    "mock": "🧪 Mock (safe fixtures)",
    "real": "🌐 Real (live API)",
    "disabled": "⏸ Disabled (skip)",
}


def _mode_selector(
    label: str, current: str, *, disabled: bool = False, key: str
) -> str:
    """Uniform dropdown so every channel's state is readable at a glance."""
    idx = _MODE_OPTIONS.index(current) if current in _MODE_OPTIONS else 0
    return st.selectbox(
        label,
        options=_MODE_OPTIONS,
        index=idx,
        format_func=lambda v: _MODE_LABELS[v],
        disabled=disabled,
        key=key,
    )


# --------------------------------------------------------------- Main render


def render_settings_tab(env_path: Path) -> None:
    env = _read_env(env_path)

    # ---------------------------- Top status panel + progress bar

    services = [
        ("Claude AI", "CLAUDE_MODE", "ANTHROPIC_API_KEY"),
        ("Google Places", "PLACES_MODE", "GOOGLE_PLACES_API_KEY"),
        ("Twilio SMS", "TWILIO_MODE", "TWILIO_ACCOUNT_SID"),
        ("WhatsApp", "WHATSAPP_MODE", "TWILIO_ACCOUNT_SID"),  # shares creds
        ("Gmail", "GMAIL_MODE", "GMAIL_CREDENTIALS_PATH"),
    ]

    def _service_state(mode_key: str, cred_key: str) -> str:
        mode = env.get(mode_key, "mock")
        if mode == "disabled":
            return "disabled"
        if mode == "real" and env.get(cred_key, ""):
            return "ready"
        if mode == "real":
            return "needs_creds"
        return "mock"

    states = {
        name: _service_state(mode_key, cred_key)
        for name, mode_key, cred_key in services
    }

    ready = sum(1 for s in states.values() if s in ("ready", "mock", "disabled"))
    total = len(states)

    col_status, col_progress = st.columns([3, 2])
    with col_status:
        st.markdown("### 🏁 Setup status")
        pill_html = []
        for name, state in states.items():
            if state == "ready":
                pill_html.append(f'<span class="pill pill-real">✅ {name}</span>')
            elif state == "mock":
                pill_html.append(f'<span class="pill pill-mock">🧪 {name} (demo)</span>')
            elif state == "disabled":
                pill_html.append(f'<span class="pill pill-off">⏸ {name} (off)</span>')
            else:
                pill_html.append(f'<span class="pill pill-off">⚠ {name} — needs key</span>')
        st.markdown(" ".join(pill_html), unsafe_allow_html=True)

    with col_progress:
        st.markdown("### ")
        st.progress(ready / total, text=f"{ready}/{total} services configured")

    st.divider()

    # ---------------------------- Demo mode master toggle

    current_demo = all(
        env.get(k, "mock") == "mock"
        for k in (
            "CLAUDE_MODE",
            "PLACES_MODE",
            "TWILIO_MODE",
            "WHATSAPP_MODE",
            "GMAIL_MODE",
        )
    )

    demo_col1, demo_col2 = st.columns([3, 1])
    with demo_col1:
        st.markdown("### 🧪 Demo mode")
        st.caption(
            "One switch, everything becomes a safe sandbox — reads from bundled "
            "fixtures, no API costs, no risk of hitting production services. "
            "Turn this off when you're ready to wire up real integrations one "
            "at a time below."
        )
    with demo_col2:
        st.write("")
        demo = st.toggle(
            "Demo mode",
            value=current_demo,
            help="ON = every integration uses fixtures. OFF = configure real APIs.",
            key="demo_mode_toggle",
            label_visibility="visible",
        )

    if demo != current_demo and st.button(
        f"✔ Apply: switch everything to {'mock' if demo else 'real'}",
        key="apply_demo",
        type="primary",
    ):
        target = "mock" if demo else "real"
        updates = {
            "CLAUDE_MODE": target,
            "PLACES_MODE": target,
            "TWILIO_MODE": target,
            "WHATSAPP_MODE": target,
            "GMAIL_MODE": target,
        }
        _write_env(env_path, updates)
        st.success(
            f"✅ All channels switched to **{target}** mode. "
            "Reloading the dashboard…"
        )
        st.rerun()

    if demo:
        st.info(
            "🧪 **Demo mode is ON** — the fields below are locked to fixture "
            "values so nothing leaks to a live API. Turn demo mode OFF above "
            "to edit real credentials."
        )

    st.divider()

    # ---------------------------- API keys & per-channel configuration

    st.markdown("### 🔌 Integrations")
    st.caption(
        "One block per external service. Each can be **mock** (safe fixture), "
        "**real** (live API), or **disabled** (skipped entirely). "
        "Demo mode forces everything to mock until you turn it off."
    )

    with st.form("integrations_form"):
        # ── Claude (AI classification) ─────────────────────────────────
        st.markdown("#### 🤖 Claude AI — form classification")
        col1, col2 = st.columns([3, 1])
        anthropic_key = col1.text_input(
            "Anthropic API key",
            value=env.get("ANTHROPIC_API_KEY", ""),
            type="password",
            placeholder="sk-ant-...",
            disabled=demo,
        )
        claude_mode = _mode_selector(
            "Mode", env.get("CLAUDE_MODE", "mock"), disabled=demo, key="claude_mode_sel"
        )
        with st.expander("❓ What is this & how do I set it up?"):
            st.markdown(_HELP_ANTHROPIC)

        # ── Google Places (prospect discovery) ─────────────────────────
        st.markdown("#### 🗺 Google Places — prospect discovery")
        col1, col2 = st.columns([3, 1])
        places_key = col1.text_input(
            "Google Places API key",
            value=env.get("GOOGLE_PLACES_API_KEY", ""),
            type="password",
            placeholder="AIza...",
            disabled=demo,
        )
        places_mode = _mode_selector(
            "Mode", env.get("PLACES_MODE", "mock"), disabled=demo, key="places_mode_sel"
        )
        with st.expander("❓ What is this & how do I set it up?"):
            st.markdown(_HELP_GOOGLE_PLACES)

        # ── Twilio SMS / Voice ─────────────────────────────────────────
        st.markdown("#### 📱 Twilio — SMS & Voice responses")
        st.caption(
            "Mainly relevant in **US / Canada / Europe**. For Argentina and "
            "most of LatAm you'll want **WhatsApp** below instead — set this "
            "channel to `disabled`."
        )
        col1, col2 = st.columns([3, 1])
        twilio_sid = col1.text_input(
            "Twilio Account SID",
            value=env.get("TWILIO_ACCOUNT_SID", ""),
            type="password",
            placeholder="AC...",
            disabled=demo,
        )
        twilio_mode = _mode_selector(
            "Mode", env.get("TWILIO_MODE", "mock"), disabled=demo, key="twilio_mode_sel"
        )
        twilio_token = st.text_input(
            "Twilio Auth Token",
            value=env.get("TWILIO_AUTH_TOKEN", ""),
            type="password",
            disabled=demo,
        )
        twilio_number = st.text_input(
            "Twilio SMS phone number (E.164)",
            value=env.get("TWILIO_PHONE_NUMBER", ""),
            placeholder="+15551234567",
            disabled=demo,
        )
        with st.expander("❓ What is this & how do I set it up?"):
            st.markdown(_HELP_TWILIO_SMS)

        # ── WhatsApp (Twilio Business API) ─────────────────────────────
        st.markdown("#### 💬 WhatsApp — messaging responses (LatAm, Spain, Asia)")
        st.caption(
            "Uses Twilio's WhatsApp Business API — **shares credentials** "
            "with the SMS/voice block above. For **Argentina / Mexico / Brasil / "
            "España / India** this is the main response channel."
        )
        col1, col2 = st.columns([3, 1])
        whatsapp_number = col1.text_input(
            "Twilio WhatsApp sender number (E.164)",
            value=env.get("TWILIO_WHATSAPP_NUMBER", ""),
            placeholder="whatsapp:+14155238886 (Twilio sandbox) or +54...",
            disabled=demo,
        )
        whatsapp_mode = _mode_selector(
            "Mode",
            env.get("WHATSAPP_MODE", "mock"),
            disabled=demo,
            key="whatsapp_mode_sel",
        )
        with st.expander("❓ What is this & how do I set it up?"):
            st.markdown(_HELP_WHATSAPP)

        # ── Gmail ──────────────────────────────────────────────────────
        st.markdown("#### 📧 Gmail — email responses")
        col1, col2 = st.columns([3, 1])
        gmail_creds = col1.text_input(
            "Gmail credentials.json path",
            value=env.get("GMAIL_CREDENTIALS_PATH", ""),
            placeholder="C:/path/to/credentials.json",
            disabled=demo,
        )
        gmail_mode = _mode_selector(
            "Mode", env.get("GMAIL_MODE", "mock"), disabled=demo, key="gmail_mode_sel"
        )
        gmail_token = st.text_input(
            "Gmail token.json path (auto-created on first run)",
            value=env.get("GMAIL_TOKEN_PATH", ""),
            placeholder="C:/path/to/token.json",
            disabled=demo,
        )
        with st.expander("❓ What is this & how do I set it up?"):
            st.markdown(_HELP_GMAIL)

        # ── Airtable ────────────────────────────────────────────────
        st.markdown("#### 🗃 Storage backend — SQLite or Airtable")
        col1, col2 = st.columns([3, 1])
        airtable_key = col1.text_input(
            "Airtable Personal Access Token",
            value=env.get("AIRTABLE_API_KEY", ""),
            type="password",
            placeholder="pat...",
            disabled=demo,
        )
        storage_backend = col2.selectbox(
            "Backend",
            options=["sqlite", "airtable"],
            index=0 if env.get("STORAGE_BACKEND", "sqlite") == "sqlite" else 1,
            format_func=lambda v: "🗂 SQLite (local)" if v == "sqlite" else "☁ Airtable",
            disabled=demo,
            key="storage_backend_sel",
        )
        airtable_base = st.text_input(
            "Airtable Base ID",
            value=env.get("AIRTABLE_BASE_ID", ""),
            placeholder="app...",
            disabled=demo,
        )
        with st.expander("❓ What is this & how do I set it up?"):
            st.markdown(_HELP_AIRTABLE)

        # ── Save ───────────────────────────────────────────────────────
        st.divider()
        submitted = st.form_submit_button(
            "💾 Save integrations", type="primary", disabled=demo
        )
        if submitted:
            updates = {
                "ANTHROPIC_API_KEY": anthropic_key,
                "CLAUDE_MODE": claude_mode,
                "GOOGLE_PLACES_API_KEY": places_key,
                "PLACES_MODE": places_mode,
                "TWILIO_ACCOUNT_SID": twilio_sid,
                "TWILIO_AUTH_TOKEN": twilio_token,
                "TWILIO_PHONE_NUMBER": twilio_number,
                "TWILIO_MODE": twilio_mode,
                "TWILIO_WHATSAPP_NUMBER": whatsapp_number,
                "WHATSAPP_MODE": whatsapp_mode,
                "GMAIL_CREDENTIALS_PATH": gmail_creds,
                "GMAIL_TOKEN_PATH": gmail_token,
                "GMAIL_MODE": gmail_mode,
                "AIRTABLE_API_KEY": airtable_key,
                "AIRTABLE_BASE_ID": airtable_base,
                "STORAGE_BACKEND": storage_backend,
            }
            _write_env(env_path, updates)
            st.success(
                f"Saved to `{env_path}`. Next pipeline run uses the new values."
            )

    # ---------------------------- Verticals section

    st.divider()
    st.markdown("### 🎯 Verticals & search queries")
    st.caption(
        "One row per vertical. `name` is the stable id (snake_case, used by "
        "the CLI and storage). `query` is the search text sent to Google "
        "Places — keep it short and specific."
    )

    registry = get_registry()
    rows = [
        {"name": v.name, "display_name": v.display_name, "query": v.query}
        for v in registry.all()
    ]

    edited = st.data_editor(
        rows,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn(
                "Name (snake_case, unique)", required=True
            ),
            "display_name": st.column_config.TextColumn(
                "Display name", required=True
            ),
            "query": st.column_config.TextColumn(
                "Google Places query", required=True
            ),
        },
        key="verticals_editor",
    )

    if st.button("💾 Save verticals", type="primary"):
        seen: set[str] = set()
        cleaned: list[Vertical] = []
        for row in edited:
            name = (row.get("name") or "").strip()
            display = (row.get("display_name") or "").strip()
            query = (row.get("query") or "").strip()
            if not (name and display and query):
                st.error(
                    "All three fields are required. Empty rows were skipped."
                )
                continue
            if not re.match(r"^[a-z][a-z0-9_]*$", name):
                st.error(
                    f"Invalid name {name!r} — use lowercase letters, digits, "
                    "underscores only. Row skipped."
                )
                continue
            if name in seen:
                st.error(f"Duplicate name {name!r} — row skipped.")
                continue
            seen.add(name)
            cleaned.append(Vertical(name=name, display_name=display, query=query))

        if cleaned:
            registry.save(cleaned)
            st.success(
                f"Saved {len(cleaned)} verticals. The pipeline will pick them "
                "up on the next run."
            )
            st.rerun()
        else:
            st.warning("Nothing saved — fix the errors above and retry.")
