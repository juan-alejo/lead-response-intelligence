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
from .i18n import tr

# --------------------------------------------------------------- Help blurbs
#
# Kept as bilingual dicts so the help expanders flip with the language
# selector. Keys match `get_lang()` output.

_HELP_ANTHROPIC = {
    "es": """\
**Qué hace:** clasifica qué tipo de formulario de contacto tiene cada
sitio web (formulario normal, chat tipo Intercom, agenda tipo Calendly,
o ninguno). Las reglas regex resuelven el 70% gratis; Claude solo entra
cuando el sitio es raro.

**Cómo sacar una API key:**

1. Andá a [console.anthropic.com](https://console.anthropic.com/) y logueate (o creá cuenta gratis).
2. Perfil → **API Keys** → **Create Key**. Copiá el valor `sk-ant-...`.

**Costo:** $5 USD de crédito gratis al registrarse. Después ~$1-2 USD/semana
para el volumen típico (~200 negocios por semana).

**Si lo apagás:** el sistema usa solo las reglas regex, sin IA. Pierde
~15% de precisión en sitios raros. Sirve para arrancar gratis o para
clientes que no pueden abrir cuenta en Anthropic.
""",
    "en": """\
**What it does:** classifies the type of contact form on each prospect's
website (contact form, chat widget, booking widget, or none). The
heuristic regex classifier handles 70% of sites for free; Claude handles
the ambiguous 30%.

**How to get an API key:**

1. Go to [console.anthropic.com](https://console.anthropic.com/) and sign in.
2. Profile → **API Keys** → **Create Key**. Copy the `sk-ant-...` value.

**Cost:** $5 free credits on signup, then ~$1-2 per week at typical scale
(~200 prospects/week).

**If you disable this:** the pipeline falls back to regex-only classification.
Accuracy drops ~15% on custom-built sites, but it's fine for early testing.
""",
}

_HELP_GOOGLE_PLACES = {
    "es": """\
**Qué hace:** descubre negocios para testear. Le pregunta a Google Places
cosas tipo "estudios de abogados en Palermo, Buenos Aires" y te trae
nombre, web, teléfono de los primeros N resultados.

**Cómo sacar una API key:**

1. [console.cloud.google.com](https://console.cloud.google.com/) → creá un proyecto.
2. APIs & Services → Library → habilitá **"Places API"**.
3. Credentials → Create credentials → **API Key**. Copiá el `AIza...`.

**Costo:** Google da **$200 USD/mes de crédito gratuito** — te alcanza
para ~10.000 búsquedas. Más que suficiente para casi cualquier cliente.

**Ojo:** Google te pide tarjeta de crédito en archivo aunque uses el free tier.
No te cobra si no pasás los $200 mensuales.

**Si lo apagás:** hay que cargar los negocios vía CSV manualmente (ver tab
"Datos detallados"). El resto del sistema anda normal.
""",
    "en": """\
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
""",
}

_HELP_TWILIO_SMS = {
    "es": """\
**Qué hace:** recibe respuestas de SMS + llamadas en un número de
teléfono de prueba que vos controlás.

**Dónde se usa:** principalmente **Estados Unidos, Canadá y Europa**,
donde los negocios responden por SMS o llamada cuando llenás un
formulario en su web.

**Cómo configurar:**
1. Registrate en [twilio.com/try-twilio](https://www.twilio.com/try-twilio) (trial gratis ~$15 de crédito).
2. Dashboard → Account SID + Auth Token (arriba a la derecha).
3. Phone Numbers → Buy a Number (~$1 USD/mes por un número norteamericano).

**Costo:** $1/mes por el número, ~$0.01 USD por SMS recibido.

**Si lo apagás:** el sistema no recolecta SMS ni llamadas. Útil si tus
clientes targetean mercados donde se responde por email o WhatsApp
(como LatAm).
""",
    "en": """\
**What it does:** receives SMS + voicemail responses from prospects on a
dedicated test phone number you own.

**Where to use it:** mainly US / Canada / Europe, where businesses reply
via SMS or phone when you fill out a form on their website.

**How to set up:**
1. Sign up at [twilio.com/try-twilio](https://www.twilio.com/try-twilio) (free trial ~$15 credit).
2. Dashboard → Account SID + Auth Token (top right).
3. Phone Numbers → Buy a Number (~$1 / month for a US number).

**Cost:** $1/month for the number, ~$0.01 per inbound SMS.

**If you disable this:** the pipeline doesn't collect SMS or voice
responses. Useful if your market communicates via email or WhatsApp.
""",
}

_HELP_WHATSAPP = {
    "es": """\
**Qué hace:** recibe respuestas de WhatsApp Business de los negocios.
Usa la API de WhatsApp de Twilio por detrás, **comparte las credenciales
con la sección SMS/llamadas** — no tenés que abrir otra cuenta.

**Dónde se usa:** esencial para **Argentina, Brasil, México, India,
sudeste asiático, España** — en general, todo mercado fuera de Estados
Unidos donde los negocios responden por WhatsApp en vez de SMS.

> **Para clientes argentinos:** esto es lo que necesitás. Las empresas
> acá responden por WhatsApp; SMS casi no se usa. Activá este canal y
> apagá el de SMS/llamadas para ahorrarte el costo del número gringo.

**Cómo configurar:**
1. Misma cuenta de Twilio que SMS (usás el mismo Account SID + Auth Token).
2. Twilio Console → **Messaging → Senders → WhatsApp senders**.
3. Activás el **Twilio Sandbox for WhatsApp** (gratis, ideal para desarrollo) o
   registrás un número real de WhatsApp Business (~$5-15 USD/mes).
4. Pegás el número sandbox o business arriba.

**Costo:** free tier sirve para demos. Número real desde ~$5 USD/mes +
~$0.005 USD por mensaje recibido.

**Si lo apagás:** no se recolectan respuestas de WhatsApp.
""",
    "en": """\
**What it does:** receives WhatsApp Business replies from prospects. Uses
Twilio's WhatsApp API under the hood, so it **shares credentials with
the SMS/voice section** — no extra account to manage.

**Where to use it:** essential for **Argentina, Brazil, Mexico, India,
Southeast Asia, Spain**, and most markets outside the US where
businesses reply via WhatsApp, not SMS.

**How to set up:**
1. Same Twilio account as SMS (reuse the Account SID + Auth Token).
2. Twilio Console → **Messaging → Senders → WhatsApp senders**.
3. Either enable the **Twilio Sandbox for WhatsApp** (free, for dev) or
   register a real WhatsApp Business number (~$5-15/month).
4. Paste the sandbox/business WhatsApp number above.

**Cost:** free tier usable for dev/demos. Live numbers start ~$5/mo +
~$0.005 per message received.

**If you disable this:** no WhatsApp responses are collected.
""",
}

_HELP_GMAIL = {
    "es": """\
**Qué hace:** revisa una casilla de Gmail dedicada para leer las
respuestas que mandan los negocios por email. Email es el canal más
universal — todo formulario de contacto pide email.

**Cómo configurar:**
1. Creás un Gmail dedicado (ej: `respuestas+cliente@gmail.com`).
2. [console.cloud.google.com](https://console.cloud.google.com/) → habilitás **Gmail API**.
3. Creás OAuth 2.0 Client ID (Desktop app) → descargás `credentials.json`.
4. Pegás el path del archivo arriba. El primer run abre una pantalla de
   consentimiento OAuth; después guarda un token reutilizable.

**Si lo apagás:** no se recolectan respuestas por email. En general es
mala idea apagarlo — email es el canal más confiable.
""",
    "en": """\
**What it does:** polls a dedicated Gmail inbox for replies to forms
that you filled out. Email is the most universal response channel —
every prospect's website form has an email field.

**How to set up:**
1. Create a dedicated Gmail address (e.g., `responses+clientname@gmail.com`).
2. [console.cloud.google.com](https://console.cloud.google.com/) → enable **Gmail API**.
3. Create OAuth 2.0 Client ID (Desktop app) → download `credentials.json`.
4. Paste the file path above. First run triggers an OAuth consent screen;
   a reusable token is saved afterwards.

**If you disable this:** no email responses are collected. Usually
unadvisable — email is the most reliable channel.
""",
}

_HELP_AIRTABLE = {
    "es": """\
**Qué hace:** guarda negocios / contactos / respuestas en una base de
Airtable así el equipo del cliente puede filtrar, armar views y
trabajar directamente desde la UI de Airtable sin saber programar.

**Cuándo usarlo:** cuando el cliente ya usa Airtable y querés que el
equipo de ventas tenga vista compartida en vivo. Si no, quedate con
SQLite — más simple, rápido, sin config.

**Cómo configurar:**
1. [airtable.com/create/tokens](https://airtable.com/create/tokens) → creás un personal access token con permisos read/write.
2. Abrís tu base → la URL tiene `appXXXXXXX` — ese es el Base ID.
3. Pegás token + Base ID arriba.
4. El schema esperado está documentado en `src/storage/airtable_store.py`.

**Si lo dejás en SQLite:** los datos quedan en un archivo `.sqlite` local.
Perfecto para setups de un solo operador.
""",
    "en": """\
**What it does:** persists prospects / submissions / responses in an
Airtable base so non-technical users can query, filter, and build
views directly in Airtable's UI.

**When to use it:** when the client's sales team works in Airtable
already and you want them to have a shared live view of the pipeline
data. Otherwise stick with SQLite — it's simpler, faster, zero-config.

**How to set up:**
1. [airtable.com/create/tokens](https://airtable.com/create/tokens) → create a personal access token with read/write scopes.
2. Open your base → URL contains `appXXXXXXX` — that's the Base ID.
3. Paste token + Base ID above.
4. Base schema is documented in `src/storage/airtable_store.py`.

**If you disable this (use SQLite):** pipeline data lives in a local
`.sqlite` file only. Fine for single-operator setups.
""",
}

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


def _mode_label(mode: str) -> str:
    return tr(f"settings.mode_{mode}")


def _mode_selector(
    label: str, current: str, *, disabled: bool = False, key: str
) -> str:
    """Uniform dropdown so every channel's state is readable at a glance."""
    idx = _MODE_OPTIONS.index(current) if current in _MODE_OPTIONS else 0
    return st.selectbox(
        label,
        options=_MODE_OPTIONS,
        index=idx,
        format_func=_mode_label,
        disabled=disabled,
        key=key,
    )


def _lang_help(mapping: dict[str, str]) -> str:
    """Pick the right language variant of a help blurb."""
    from .i18n import get_lang

    return mapping.get(get_lang()) or next(iter(mapping.values()))


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
        st.markdown(tr("settings.status_title"))
        state_to_css = {
            "ready": "pill-real",
            "mock": "pill-mock",
            "disabled": "pill-off",
            "needs_creds": "pill-off",
        }
        state_to_key = {
            "ready": "settings.status_ready",
            "mock": "settings.status_mock",
            "disabled": "settings.status_disabled",
            "needs_creds": "settings.status_needs_key",
        }
        pill_html = [
            f'<span class="pill {state_to_css[state]}">'
            f"{tr(state_to_key[state], name=name)}</span>"
            for name, state in states.items()
        ]
        st.markdown(" ".join(pill_html), unsafe_allow_html=True)

    with col_progress:
        st.markdown("### ")
        st.progress(
            ready / total,
            text=tr("settings.status_progress", ready=ready, total=total),
        )

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
        st.markdown(tr("settings.demo_title"))
        st.caption(tr("settings.demo_caption"))
    with demo_col2:
        st.write("")
        demo = st.toggle(
            tr("settings.demo_toggle"),
            value=current_demo,
            help=tr("settings.demo_toggle_help"),
            key="demo_mode_toggle",
            label_visibility="visible",
        )

    if demo != current_demo and st.button(
        tr("settings.demo_apply", mode="mock" if demo else "real"),
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
        st.success(tr("settings.demo_success", mode=target))
        st.rerun()

    if demo:
        st.info(tr("settings.demo_on_warning"))

    st.divider()

    # ---------------------------- API keys & per-channel configuration

    st.markdown(tr("settings.integrations_title"))
    st.caption(tr("settings.integrations_caption"))

    with st.form("integrations_form"):
        # ── Claude (AI classification) ─────────────────────────────────
        st.markdown(tr("settings.claude_title"))
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
        with st.expander(tr("settings.help_expander")):
            st.markdown(_lang_help(_HELP_ANTHROPIC))

        # ── Google Places (prospect discovery) ─────────────────────────
        st.markdown(tr("settings.places_title"))
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
        with st.expander(tr("settings.help_expander")):
            st.markdown(_lang_help(_HELP_GOOGLE_PLACES))

        # ── Twilio SMS / Voice ─────────────────────────────────────────
        st.markdown(tr("settings.twilio_title"))
        st.caption(tr("settings.twilio_caption"))
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
        with st.expander(tr("settings.help_expander")):
            st.markdown(_lang_help(_HELP_TWILIO_SMS))

        # ── WhatsApp (Twilio Business API) ─────────────────────────────
        st.markdown(tr("settings.whatsapp_title"))
        st.caption(tr("settings.whatsapp_caption"))
        col1, col2 = st.columns([3, 1])
        whatsapp_number = col1.text_input(
            "Twilio WhatsApp sender number (E.164)",
            value=env.get("TWILIO_WHATSAPP_NUMBER", ""),
            placeholder="whatsapp:+14155238886 (Twilio sandbox) o +54...",
            disabled=demo,
        )
        whatsapp_mode = _mode_selector(
            "Mode",
            env.get("WHATSAPP_MODE", "mock"),
            disabled=demo,
            key="whatsapp_mode_sel",
        )
        with st.expander(tr("settings.help_expander")):
            st.markdown(_lang_help(_HELP_WHATSAPP))

        # ── Gmail ──────────────────────────────────────────────────────
        st.markdown(tr("settings.gmail_title"))
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
        with st.expander(tr("settings.help_expander")):
            st.markdown(_lang_help(_HELP_GMAIL))

        # ── Airtable ────────────────────────────────────────────────
        st.markdown(tr("settings.storage_title"))
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
        with st.expander(tr("settings.help_expander")):
            st.markdown(_lang_help(_HELP_AIRTABLE))

        # ── Save ───────────────────────────────────────────────────────
        st.divider()
        submitted = st.form_submit_button(
            tr("settings.save_integrations"), type="primary", disabled=demo
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
            st.success(tr("settings.saved_to_env", path=env_path))

    # ---------------------------- Verticals section

    st.divider()
    st.markdown(tr("settings.verticals_title"))
    st.caption(tr("settings.verticals_caption"))

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
                tr("settings.verticals_col_name"), required=True
            ),
            "display_name": st.column_config.TextColumn(
                tr("settings.verticals_col_display"), required=True
            ),
            "query": st.column_config.TextColumn(
                tr("settings.verticals_col_query"), required=True
            ),
        },
        key="verticals_editor",
    )

    if st.button(tr("settings.verticals_save"), type="primary"):
        seen: set[str] = set()
        cleaned: list[Vertical] = []
        for row in edited:
            name = (row.get("name") or "").strip()
            display = (row.get("display_name") or "").strip()
            query = (row.get("query") or "").strip()
            if not (name and display and query):
                st.error(tr("settings.verticals_error_required"))
                continue
            if not re.match(r"^[a-z][a-z0-9_]*$", name):
                st.error(tr("settings.verticals_error_name", name=repr(name)))
                continue
            if name in seen:
                st.error(tr("settings.verticals_error_dup", name=repr(name)))
                continue
            seen.add(name)
            cleaned.append(Vertical(name=name, display_name=display, query=query))

        if cleaned:
            registry.save(cleaned)
            st.success(tr("settings.verticals_saved", count=len(cleaned)))
            st.rerun()
        else:
            st.warning(tr("settings.verticals_warning"))
