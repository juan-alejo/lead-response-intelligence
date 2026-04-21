"""Settings tab — lets the operator configure API keys and verticals without
touching code or redeploying.

Reads from / writes to:
- `.env` for API keys + mode toggles (kept out of git, treated as secrets)
- `config/verticals.yaml` for the editable vertical queries

Every key has a "How do I get this?" help popover with concrete step-by-step
instructions for the provider's console. That's the UX that makes the tool
salable to a non-technical buyer.
"""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from ..verticals import Vertical, get_registry

# --------------------------------------------------------------- Help blurbs

_HELP_ANTHROPIC = """\
**How to get an Anthropic Claude API key:**

1. Go to [console.anthropic.com](https://console.anthropic.com/) and sign in
   (or create a free account).
2. Click your profile → **API Keys** → **Create Key**.
3. Copy the key (it starts with `sk-ant-...`) and paste it above.

**Cost**: Anthropic gives $5 of free credits on signup. At the pipeline's
scale (~200 prospects / week), typical spend is **$1–2 per week**.
"""

_HELP_GOOGLE_PLACES = """\
**How to get a Google Places API key:**

1. Go to [console.cloud.google.com](https://console.cloud.google.com/).
2. Create a project (or use an existing one).
3. In the sidebar: **APIs & Services → Library**, search **"Places API"**
   and click **Enable**.
4. **APIs & Services → Credentials → Create credentials → API Key**.
5. Copy the key (starts with `AIza...`) and paste it above.

**Cost**: Google gives **$200 / month of free credit** automatically — that
covers ~10,000 text-search queries. More than enough for most clients.

**Requirement**: Google asks for a credit card on file even to activate the
free tier. They don't charge unless you blow past the $200 credit.
"""

_HELP_TWILIO = """\
**How to get Twilio credentials:**

1. Sign up at [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
   (free trial includes ~$15 of credit).
2. Dashboard → **Account SID** + **Auth Token** (top right).
3. **Phone Numbers → Buy a Number** — pick a US number (~$1 / month).

Paste the SID, token, and purchased number above.
"""

_HELP_GMAIL = """\
**How to set up Gmail API polling:**

1. Create a dedicated Gmail address for the test inbox (e.g.,
   `responses+clientname@gmail.com`).
2. In [Google Cloud Console](https://console.cloud.google.com/):
   - Enable the **Gmail API**.
   - Create OAuth 2.0 Client ID (Desktop app).
   - Download the JSON as `credentials.json`.
3. Put the path to that file above.
4. First run triggers an OAuth flow that writes a token file to reuse
   for subsequent runs.
"""

_HELP_AIRTABLE = """\
**How to connect Airtable as the storage backend:**

1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
   and create a Personal Access Token with `data.records:read`,
   `data.records:write`, `schema.bases:read` scopes.
2. Paste the token (starts with `pat...`) above.
3. For the Base ID: open your base in Airtable → URL looks like
   `airtable.com/appXXXXXXX/...` → `appXXXXXXX` is the base ID.

The expected base schema (3 tables: prospects / submissions / responses) is
documented in `src/storage/airtable_store.py`.
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
    # Preserve ordering + comments by rewriting known keys in-place and
    # appending any new ones at the bottom. Keeps diff-friendly.
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


# --------------------------------------------------------------- Main render


def render_settings_tab(env_path: Path) -> None:
    st.caption(
        "Everything the operator needs to configure per-client — API keys, "
        "operating modes, and the list of verticals the pipeline targets. "
        "Changes are persisted to `.env` and `config/verticals.yaml`; the "
        "next pipeline run picks them up automatically."
    )

    env = _read_env(env_path)

    # ---------------------------- API keys section

    st.subheader("🔑 API keys & modes")
    st.caption(
        "Each service can run in **mock** (zero cost, bundled fixtures) or "
        "**real** (live API calls). Switch one at a time as you validate each "
        "integration with the client's account."
    )

    with st.form("api_keys_form"):
        # Anthropic ------------------------------------------------------
        col1, col2 = st.columns([3, 1])
        anthropic_key = col1.text_input(
            "Anthropic API key",
            value=env.get("ANTHROPIC_API_KEY", ""),
            type="password",
            placeholder="sk-ant-...",
        )
        claude_mode = col2.selectbox(
            "Claude mode",
            options=["mock", "real"],
            index=0 if env.get("CLAUDE_MODE", "mock") == "mock" else 1,
            key="claude_mode",
        )
        with st.expander("❓ How do I get an Anthropic API key?"):
            st.markdown(_HELP_ANTHROPIC)

        # Google Places --------------------------------------------------
        col1, col2 = st.columns([3, 1])
        places_key = col1.text_input(
            "Google Places API key",
            value=env.get("GOOGLE_PLACES_API_KEY", ""),
            type="password",
            placeholder="AIza...",
        )
        places_mode = col2.selectbox(
            "Places mode",
            options=["mock", "real"],
            index=0 if env.get("PLACES_MODE", "mock") == "mock" else 1,
            key="places_mode",
        )
        with st.expander("❓ How do I get a Google Places API key?"):
            st.markdown(_HELP_GOOGLE_PLACES)

        # Twilio ---------------------------------------------------------
        col1, col2 = st.columns([3, 1])
        twilio_sid = col1.text_input(
            "Twilio Account SID",
            value=env.get("TWILIO_ACCOUNT_SID", ""),
            type="password",
            placeholder="AC...",
        )
        twilio_mode = col2.selectbox(
            "Twilio mode",
            options=["mock", "real"],
            index=0 if env.get("TWILIO_MODE", "mock") == "mock" else 1,
            key="twilio_mode",
        )
        twilio_token = st.text_input(
            "Twilio Auth Token",
            value=env.get("TWILIO_AUTH_TOKEN", ""),
            type="password",
        )
        twilio_number = st.text_input(
            "Twilio phone number (E.164 format)",
            value=env.get("TWILIO_PHONE_NUMBER", ""),
            placeholder="+15551234567",
        )
        with st.expander("❓ How do I set up Twilio?"):
            st.markdown(_HELP_TWILIO)

        # Gmail ----------------------------------------------------------
        col1, col2 = st.columns([3, 1])
        gmail_creds = col1.text_input(
            "Gmail credentials.json path",
            value=env.get("GMAIL_CREDENTIALS_PATH", ""),
            placeholder="C:/path/to/credentials.json",
        )
        gmail_mode = col2.selectbox(
            "Gmail mode",
            options=["mock", "real"],
            index=0 if env.get("GMAIL_MODE", "mock") == "mock" else 1,
            key="gmail_mode",
        )
        gmail_token = st.text_input(
            "Gmail token.json path (created on first run)",
            value=env.get("GMAIL_TOKEN_PATH", ""),
            placeholder="C:/path/to/token.json",
        )
        with st.expander("❓ How do I set up Gmail polling?"):
            st.markdown(_HELP_GMAIL)

        # Airtable -------------------------------------------------------
        col1, col2 = st.columns([3, 1])
        airtable_key = col1.text_input(
            "Airtable Personal Access Token",
            value=env.get("AIRTABLE_API_KEY", ""),
            type="password",
            placeholder="pat...",
        )
        storage_backend = col2.selectbox(
            "Storage backend",
            options=["sqlite", "airtable"],
            index=0 if env.get("STORAGE_BACKEND", "sqlite") == "sqlite" else 1,
            key="storage_backend",
        )
        airtable_base = st.text_input(
            "Airtable Base ID",
            value=env.get("AIRTABLE_BASE_ID", ""),
            placeholder="app...",
        )
        with st.expander("❓ How do I connect Airtable?"):
            st.markdown(_HELP_AIRTABLE)

        # Save -----------------------------------------------------------
        st.divider()
        submitted = st.form_submit_button(
            "💾 Save API keys to .env", type="primary"
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
    st.subheader("🎯 Verticals & search queries")
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
        # Validate before saving — empty fields or duplicate names break the pipeline.
        seen: set[str] = set()
        cleaned: list[Vertical] = []
        for row in edited:
            name = (row.get("name") or "").strip()
            display = (row.get("display_name") or "").strip()
            query = (row.get("query") or "").strip()
            if not (name and display and query):
                st.error(
                    "All three fields are required. Row with empty values was skipped."
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
                "up on the next run — no restart needed."
            )
            st.rerun()
        else:
            st.warning("Nothing saved — fix the errors above and retry.")
