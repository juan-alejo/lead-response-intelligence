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
- Everything auto-saves. No explicit Save button — changes persist as
  you type and the next pipeline run picks them up.

Persistence:
- API keys → `.env` (gitignored, treated as secrets).
- Verticals → `config/verticals.yaml` (tracked so defaults travel with the repo).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import streamlit as st

from ..verticals import Vertical, get_registry
from .i18n import get_lang, tr

# --------------------------------------------------------------- Help blurbs

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


def _save_single(env_path: Path, env_key: str, value: str) -> None:
    """Persist a single env var. Used by every on_change callback."""
    current = _read_env(env_path)
    current[env_key] = value
    _write_env(env_path, current)


# --------------------------------------------------------------- UI helpers

_MODE_OPTIONS = ["mock", "real", "disabled"]


def _mode_label(mode: str) -> str:
    return tr(f"settings.mode_{mode}")


def _lang_help(mapping: dict[str, str]) -> str:
    return mapping.get(get_lang()) or next(iter(mapping.values()))


def _on_change_factory(env_path: Path, env_key: str, widget_key: str) -> Callable:
    """Build an on_change callback that writes widget value to `env_key`.

    Kept as a factory because Streamlit calls callbacks without args — we
    need to capture the env_key and widget_key in a closure.
    """

    def _cb() -> None:
        value = st.session_state.get(widget_key, "")
        _save_single(env_path, env_key, str(value))

    return _cb


def _service_state(env: dict[str, str], mode_key: str, cred_key: str) -> str:
    """Compute the state of an integration for status chips + expansion logic."""
    mode = env.get(mode_key, "mock")
    if mode == "disabled":
        return "disabled"
    if mode == "real" and env.get(cred_key, ""):
        return "ready"
    if mode == "real":
        return "needs_creds"
    return "mock"


_STATE_ICONS = {
    "ready": "✅",
    "mock": "🧪",
    "disabled": "⏸",
    "needs_creds": "⚠",
}


def _section_title(name: str, state: str) -> str:
    return f"{_STATE_ICONS[state]}  {name}"


# --------------------------------------------------------------- Integration sections


def _section_claude(env: dict[str, str], env_path: Path) -> None:
    state = _service_state(env, "CLAUDE_MODE", "ANTHROPIC_API_KEY")
    with st.expander(
        _section_title(tr("settings.claude_title").replace("#### 🤖 ", ""), state),
        expanded=(state == "needs_creds"),
    ):
        col1, col2 = st.columns([3, 1])
        col1.text_input(
            "Anthropic API key",
            value=env.get("ANTHROPIC_API_KEY", ""),
            type="password",
            placeholder="sk-ant-...",
            key="anthropic_key_input",
            on_change=_on_change_factory(env_path, "ANTHROPIC_API_KEY", "anthropic_key_input"),
        )
        col2.selectbox(
            "Modo",
            options=_MODE_OPTIONS,
            index=_MODE_OPTIONS.index(env.get("CLAUDE_MODE", "mock")),
            format_func=_mode_label,
            key="claude_mode_sel",
            on_change=_on_change_factory(env_path, "CLAUDE_MODE", "claude_mode_sel"),
        )
        with st.expander(tr("settings.help_expander"), expanded=False):
            st.markdown(_lang_help(_HELP_ANTHROPIC))


def _section_places(env: dict[str, str], env_path: Path) -> None:
    state = _service_state(env, "PLACES_MODE", "GOOGLE_PLACES_API_KEY")
    with st.expander(
        _section_title(tr("settings.places_title").replace("#### 🗺 ", ""), state),
        expanded=(state == "needs_creds"),
    ):
        col1, col2 = st.columns([3, 1])
        col1.text_input(
            "Google Places API key",
            value=env.get("GOOGLE_PLACES_API_KEY", ""),
            type="password",
            placeholder="AIza...",
            key="places_key_input",
            on_change=_on_change_factory(env_path, "GOOGLE_PLACES_API_KEY", "places_key_input"),
        )
        col2.selectbox(
            "Modo",
            options=_MODE_OPTIONS,
            index=_MODE_OPTIONS.index(env.get("PLACES_MODE", "mock")),
            format_func=_mode_label,
            key="places_mode_sel",
            on_change=_on_change_factory(env_path, "PLACES_MODE", "places_mode_sel"),
        )
        with st.expander(tr("settings.help_expander"), expanded=False):
            st.markdown(_lang_help(_HELP_GOOGLE_PLACES))


def _section_twilio(env: dict[str, str], env_path: Path) -> None:
    state = _service_state(env, "TWILIO_MODE", "TWILIO_ACCOUNT_SID")
    with st.expander(
        _section_title(tr("settings.twilio_title").replace("#### 📱 ", ""), state),
        expanded=(state == "needs_creds"),
    ):
        st.caption(tr("settings.twilio_caption"))
        col1, col2 = st.columns([3, 1])
        col1.text_input(
            "Twilio Account SID",
            value=env.get("TWILIO_ACCOUNT_SID", ""),
            type="password",
            placeholder="AC...",
            key="twilio_sid_input",
            on_change=_on_change_factory(env_path, "TWILIO_ACCOUNT_SID", "twilio_sid_input"),
        )
        col2.selectbox(
            "Modo",
            options=_MODE_OPTIONS,
            index=_MODE_OPTIONS.index(env.get("TWILIO_MODE", "mock")),
            format_func=_mode_label,
            key="twilio_mode_sel",
            on_change=_on_change_factory(env_path, "TWILIO_MODE", "twilio_mode_sel"),
        )
        st.text_input(
            "Twilio Auth Token",
            value=env.get("TWILIO_AUTH_TOKEN", ""),
            type="password",
            key="twilio_token_input",
            on_change=_on_change_factory(env_path, "TWILIO_AUTH_TOKEN", "twilio_token_input"),
        )
        st.text_input(
            "Teléfono SMS (formato E.164)",
            value=env.get("TWILIO_PHONE_NUMBER", ""),
            placeholder="+15551234567",
            key="twilio_phone_input",
            on_change=_on_change_factory(env_path, "TWILIO_PHONE_NUMBER", "twilio_phone_input"),
        )
        with st.expander(tr("settings.help_expander"), expanded=False):
            st.markdown(_lang_help(_HELP_TWILIO_SMS))


def _section_whatsapp(env: dict[str, str], env_path: Path) -> None:
    state = _service_state(env, "WHATSAPP_MODE", "TWILIO_ACCOUNT_SID")
    with st.expander(
        _section_title(tr("settings.whatsapp_title").replace("#### 💬 ", ""), state),
        expanded=(state == "needs_creds"),
    ):
        st.caption(tr("settings.whatsapp_caption"))
        col1, col2 = st.columns([3, 1])
        col1.text_input(
            "Número de WhatsApp (E.164)",
            value=env.get("TWILIO_WHATSAPP_NUMBER", ""),
            placeholder="whatsapp:+14155238886 (sandbox) o +54...",
            key="whatsapp_number_input",
            on_change=_on_change_factory(
                env_path, "TWILIO_WHATSAPP_NUMBER", "whatsapp_number_input"
            ),
        )
        col2.selectbox(
            "Modo",
            options=_MODE_OPTIONS,
            index=_MODE_OPTIONS.index(env.get("WHATSAPP_MODE", "mock")),
            format_func=_mode_label,
            key="whatsapp_mode_sel",
            on_change=_on_change_factory(env_path, "WHATSAPP_MODE", "whatsapp_mode_sel"),
        )
        with st.expander(tr("settings.help_expander"), expanded=False):
            st.markdown(_lang_help(_HELP_WHATSAPP))


def _section_gmail(env: dict[str, str], env_path: Path) -> None:
    state = _service_state(env, "GMAIL_MODE", "GMAIL_CREDENTIALS_PATH")
    with st.expander(
        _section_title(tr("settings.gmail_title").replace("#### 📧 ", ""), state),
        expanded=(state == "needs_creds"),
    ):
        col1, col2 = st.columns([3, 1])
        col1.text_input(
            "Path a credentials.json",
            value=env.get("GMAIL_CREDENTIALS_PATH", ""),
            placeholder="C:/path/to/credentials.json",
            key="gmail_creds_input",
            on_change=_on_change_factory(
                env_path, "GMAIL_CREDENTIALS_PATH", "gmail_creds_input"
            ),
        )
        col2.selectbox(
            "Modo",
            options=_MODE_OPTIONS,
            index=_MODE_OPTIONS.index(env.get("GMAIL_MODE", "mock")),
            format_func=_mode_label,
            key="gmail_mode_sel",
            on_change=_on_change_factory(env_path, "GMAIL_MODE", "gmail_mode_sel"),
        )
        st.text_input(
            "Path a token.json (se crea solo la primera vez)",
            value=env.get("GMAIL_TOKEN_PATH", ""),
            placeholder="C:/path/to/token.json",
            key="gmail_token_input",
            on_change=_on_change_factory(env_path, "GMAIL_TOKEN_PATH", "gmail_token_input"),
        )
        with st.expander(tr("settings.help_expander"), expanded=False):
            st.markdown(_lang_help(_HELP_GMAIL))


def _section_storage(env: dict[str, str], env_path: Path) -> None:
    backend = env.get("STORAGE_BACKEND", "sqlite")
    has_airtable_creds = bool(env.get("AIRTABLE_API_KEY") and env.get("AIRTABLE_BASE_ID"))
    if backend == "airtable" and not has_airtable_creds:
        state = "needs_creds"
    elif backend == "airtable":
        state = "ready"
    else:
        state = "mock"  # sqlite is always "ready" but we treat it as neutral demo

    with st.expander(
        _section_title(tr("settings.storage_title").replace("#### 🗃 ", ""), state),
        expanded=(state == "needs_creds"),
    ):
        col1, col2 = st.columns([3, 1])
        col1.text_input(
            "Airtable Personal Access Token",
            value=env.get("AIRTABLE_API_KEY", ""),
            type="password",
            placeholder="pat...",
            key="airtable_key_input",
            on_change=_on_change_factory(env_path, "AIRTABLE_API_KEY", "airtable_key_input"),
        )
        col2.selectbox(
            "Backend",
            options=["sqlite", "airtable"],
            index=0 if backend == "sqlite" else 1,
            format_func=lambda v: "🗂 SQLite (local)" if v == "sqlite" else "☁ Airtable",
            key="storage_backend_sel",
            on_change=_on_change_factory(env_path, "STORAGE_BACKEND", "storage_backend_sel"),
        )
        st.text_input(
            "Airtable Base ID",
            value=env.get("AIRTABLE_BASE_ID", ""),
            placeholder="app...",
            key="airtable_base_input",
            on_change=_on_change_factory(env_path, "AIRTABLE_BASE_ID", "airtable_base_input"),
        )
        with st.expander(tr("settings.help_expander"), expanded=False):
            st.markdown(_lang_help(_HELP_AIRTABLE))


# --------------------------------------------------------------- Demo mode callback


def _toggle_demo_mode(env_path: Path) -> None:
    """Callback for the master demo toggle — fans out to all *_MODE keys."""
    target = "mock" if st.session_state.get("demo_mode_toggle") else "real"
    env = _read_env(env_path)
    for key in ("CLAUDE_MODE", "PLACES_MODE", "TWILIO_MODE", "WHATSAPP_MODE", "GMAIL_MODE"):
        env[key] = target
    _write_env(env_path, env)


# --------------------------------------------------------------- Verticals auto-save


def _save_verticals(new_rows: list[dict]) -> tuple[int, list[str]]:
    """Validate + persist the edited verticals table. Returns (count, errors)."""
    errors: list[str] = []
    seen: set[str] = set()
    cleaned: list[Vertical] = []
    for row in new_rows:
        name = (row.get("name") or "").strip()
        display = (row.get("display_name") or "").strip()
        query = (row.get("query") or "").strip()
        if not (name and display and query):
            # Skip empty rows silently (data_editor creates them on "add row")
            if name or display or query:
                errors.append(tr("settings.verticals_error_required"))
            continue
        if not re.match(r"^[a-z][a-z0-9_]*$", name):
            errors.append(tr("settings.verticals_error_name", name=repr(name)))
            continue
        if name in seen:
            errors.append(tr("settings.verticals_error_dup", name=repr(name)))
            continue
        seen.add(name)
        cleaned.append(Vertical(name=name, display_name=display, query=query))

    if cleaned and not errors:
        get_registry().save(cleaned)
    return len(cleaned), errors


# --------------------------------------------------------------- Main render


def render_settings_tab(env_path: Path) -> None:
    env = _read_env(env_path)

    # ---------------------------- Setup status panel

    services = [
        ("Claude AI", "CLAUDE_MODE", "ANTHROPIC_API_KEY"),
        ("Google Places", "PLACES_MODE", "GOOGLE_PLACES_API_KEY"),
        ("Twilio SMS", "TWILIO_MODE", "TWILIO_ACCOUNT_SID"),
        ("WhatsApp", "WHATSAPP_MODE", "TWILIO_ACCOUNT_SID"),
        ("Gmail", "GMAIL_MODE", "GMAIL_CREDENTIALS_PATH"),
    ]
    states = {name: _service_state(env, m, c) for name, m, c in services}
    ready_count = sum(1 for s in states.values() if s in ("ready", "mock", "disabled"))
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
            ready_count / total,
            text=tr("settings.status_progress", ready=ready_count, total=total),
        )

    # Save confirmation banner (subtle, at the top)
    st.caption("💾 " + tr("settings.autosave_hint"))

    st.divider()

    # ---------------------------- Demo mode master toggle

    current_demo = all(
        env.get(k, "mock") == "mock"
        for k in ("CLAUDE_MODE", "PLACES_MODE", "TWILIO_MODE", "WHATSAPP_MODE", "GMAIL_MODE")
    )

    demo_col1, demo_col2 = st.columns([3, 1])
    with demo_col1:
        st.markdown(tr("settings.demo_title"))
        st.caption(tr("settings.demo_caption"))
    with demo_col2:
        st.write("")
        # Seed session_state once so the widget reflects env state on first render.
        if "demo_mode_toggle" not in st.session_state:
            st.session_state["demo_mode_toggle"] = current_demo
        st.toggle(
            tr("settings.demo_toggle"),
            help=tr("settings.demo_toggle_help"),
            key="demo_mode_toggle",
            on_change=_toggle_demo_mode,
            args=(env_path,),
        )

    if current_demo:
        st.info(tr("settings.demo_on_warning"))

    st.divider()

    # ---------------------------- Integrations

    st.markdown(tr("settings.integrations_title"))
    st.caption(tr("settings.integrations_caption"))

    _section_claude(env, env_path)
    _section_places(env, env_path)
    _section_twilio(env, env_path)
    _section_whatsapp(env, env_path)
    _section_gmail(env, env_path)
    _section_storage(env, env_path)

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

    # Auto-save verticals on each rerun (data_editor returns current state).
    # We compare against the last saved snapshot to avoid spurious writes.
    last_saved = st.session_state.get("_verticals_last_saved")
    current_signature = tuple(
        (r.get("name", ""), r.get("display_name", ""), r.get("query", ""))
        for r in edited
    )
    if last_saved != current_signature:
        count, errors = _save_verticals(edited)
        if not errors and count > 0:
            st.session_state["_verticals_last_saved"] = current_signature
            st.toast(tr("settings.verticals_saved", count=count), icon="✅")
        elif errors:
            for err in errors[:3]:  # cap at 3 to avoid spam
                st.warning(err)
