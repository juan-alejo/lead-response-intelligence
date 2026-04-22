"""Dashboard localization.

Translation strategy: write every visible UI string in **plain, operator-
friendly language** — no "pipeline", no "ingestion", no "classifier". A
salesperson should be able to read the dashboard cold and understand what
each number means.

Adding a new language: copy the `es` block, translate the values, and
append to `LANGUAGES`. The `_tr()` helper falls back to Spanish (the
primary market) when a key is missing, so partial translations don't
break the UI.
"""

from __future__ import annotations

import streamlit as st

LANGUAGES = {
    "es": "🇦🇷 Español",
    "en": "🇺🇸 English",
}

DEFAULT_LANGUAGE = "es"


# --------------------------------------------------------------- Translations
#
# Style guide:
#   - No tech jargon (no "pipeline", "ingestion", "classifier", "endpoint").
#   - Business terms: "cliente potencial" > "prospect", "zona" > "borough",
#     "tipo de negocio" > "vertical", "ronda de búsqueda" > "pipeline run".
#   - Every key starts with a section prefix so search is cheap.
# ---------------------------------------------------------------

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "es": {
        # --- App shell ---
        "app.title": "📡 Panel de Respuestas a Clientes",
        "app.subtitle": (
            "Encuentra clientes potenciales, analiza cómo se los puede "
            "contactar, y mide cuánto tardan en responder. Te genera todos "
            "los lunes una lista de los más lentos — tus mejores prospectos."
        ),
        "app.github_button": "📖 Código (GitHub)",
        "app.language": "Idioma",

        # --- Integration pills row ---
        "pills.header": "**Servicios conectados:**",
        "pills.storage": "**Base de datos:**",
        "pills.label.places": "Búsqueda de negocios",
        "pills.label.claude": "IA (clasificación)",
        "pills.label.twilio": "SMS / Llamadas",
        "pills.label.whatsapp": "WhatsApp",
        "pills.label.gmail": "Email",
        "pills.mode.real": "activo",
        "pills.mode.mock": "modo prueba",
        "pills.mode.disabled": "apagado",

        # --- Metrics row ---
        "metrics.prospects": "Clientes potenciales encontrados",
        "metrics.submissions": "Contactos por hacer",
        "metrics.responses": "Respuestas recibidas",
        "metrics.match_rate": "Tasa de identificación",
        "metrics.prospects_help": "Negocios descubiertos y guardados en los últimos 90 días.",
        "metrics.submissions_help": (
            "Formularios de contacto listos para que completes manualmente. "
            "(La automatización de este paso llega en la Fase 2.)"
        ),
        "metrics.responses_help": (
            "Todos los mensajes recibidos — SMS, WhatsApp, email, llamadas."
        ),
        "metrics.match_rate_help": (
            "Porcentaje de respuestas que pudimos asociar a un contacto "
            "específico. Objetivo: 95% o más con datos bien cargados."
        ),

        # --- Run card ---
        "run.title": "### ▶ Buscar nuevos clientes ahora",
        "run.caption": (
            "En producción esta búsqueda corre automáticamente cada lunes a "
            "las 6 AM. Este botón sirve para ejecutarla a mano — por ejemplo "
            "después de agregar un tipo de negocio nuevo o para una demo."
        ),
        "run.borough": "Zona / Ciudad",
        "run.limit": "Máximo de negocios a revisar (por tipo)",
        "run.button": "🚀 Buscar ahora",
        "run.verticals_info": "Se van a buscar **{count}** tipo(s) de negocio configurados (editá la lista en la tab Configuración).",
        "run.status_running": "Buscando clientes potenciales en todos los tipos de negocio…",
        "run.status_done": "Listo — encontrados {ingested}, {matched}/{pulled} respuestas identificadas.",
        "run.success": "✅ Reportes actualizados. Mirá las tabs de abajo.",

        # --- Tabs ---
        "tab.outreach": "🎯 Lista prioritaria",
        "tab.stats": "📊 Estadísticas",
        "tab.competitors": "🕵 Herramientas que usan",
        "tab.data": "🗂 Datos detallados",
        "tab.settings": "⚙ Configuración",

        # --- Outreach tab ---
        "outreach.empty": "📭 Todavía no hay lista generada — tocá **Buscar ahora** arriba.",
        "outreach.summary": (
            "**{total} clientes potenciales** para contactar — "
            "**{never}** nunca respondieron (máxima prioridad). "
            "Los que responden en menos de 2 minutos se filtran automáticamente."
        ),
        "outreach.filter": "Filtrar por tipo de negocio",
        "outreach.download": "⬇ Descargar CSV filtrado",
        "outreach.col.business": "Negocio",
        "outreach.col.vertical": "Tipo",
        "outreach.col.method": "Cómo contactarlos",
        "outreach.col.elapsed_sec": "Tiempo (seg)",
        "outreach.col.elapsed_human": "Tiempo",
        "outreach.col.email": "Email",
        "outreach.col.phone": "Teléfono",
        "outreach.col.elapsed_sec_help": "Vacío = nunca respondieron.",

        # --- Stats tab ---
        "stats.empty": "📭 Sin estadísticas todavía — corré la búsqueda para generarlas.",
        "stats.caption": (
            "Tiempo de respuesta promedio por tipo de negocio. Barras más "
            "cortas = negocios más ágiles (menos oportunidad). Más altas = "
            "clientes potenciales para vos."
        ),

        # --- Competitors tab ---
        "competitors.empty": (
            "📭 Sin datos de herramientas todavía — corré la búsqueda primero."
        ),
        "competitors.caption": (
            "Qué herramientas de chat o agenda tienen instaladas los negocios "
            "que revisamos. Si muchos en el mismo rubro usan la misma "
            "herramienta, es una señal: **integrate** con ella, no la reemplaces."
        ),

        # --- Data tab ---
        "data.caption": (
            "Vista directa de los datos guardados. Útil para verificar por "
            "qué un mensaje se asoció (o no) con un negocio específico."
        ),
        "data.radio": "Tabla",
        "data.option.submissions": "Contactos por hacer",
        "data.option.responses": "Respuestas recibidas",
        "data.empty.submissions": "Todavía no hay contactos queued.",
        "data.empty.responses": "Todavía no hay respuestas.",

        # --- Settings: setup status ---
        "settings.status_title": "### 🏁 Estado de configuración",
        "settings.status_progress": "{ready}/{total} servicios configurados",
        "settings.status_ready": "✅ {name}",
        "settings.status_mock": "🧪 {name} (demo)",
        "settings.status_disabled": "⏸ {name} (apagado)",
        "settings.status_needs_key": "⚠ {name} — falta la clave",

        # --- Settings: demo mode ---
        "settings.demo_title": "### 🧪 Modo demo",
        "settings.demo_caption": (
            "Un solo switch para poner todo en modo prueba — lee datos de "
            "ejemplo, no gasta nada de APIs, no puede romper nada. Apagalo "
            "cuando quieras conectar servicios reales abajo."
        ),
        "settings.demo_toggle": "Modo demo",
        "settings.demo_toggle_help": (
            "Encendido = todo usa datos de ejemplo. Apagado = configurás las "
            "APIs reales una por una."
        ),
        "settings.demo_apply": "✔ Aplicar: pasar todo a {mode}",
        "settings.demo_success": "✅ Todo cambió a modo **{mode}**. Recargando el panel…",
        "settings.demo_on_warning": (
            "🧪 **Modo demo activo** — los campos de abajo están bloqueados "
            "así no se filtra ninguna credencial por error. Apagá el modo "
            "demo arriba para editar las APIs reales."
        ),

        # --- Settings: integrations header ---
        "settings.integrations_title": "### 🔌 Conexiones con servicios externos",
        "settings.integrations_caption": (
            "Una sección por servicio. Cada uno puede estar en **modo prueba** "
            "(datos de ejemplo seguros), **real** (API en vivo), o **apagado** "
            "(se saltea). El modo demo fuerza todo a modo prueba hasta que lo apagues."
        ),
        "settings.save_integrations": "💾 Guardar configuración",
        "settings.saved_to_env": "✅ Guardado en `{path}`. La próxima búsqueda usa los nuevos valores.",
        "settings.autosave_hint": "Los cambios se guardan automáticamente — no hace falta apretar ningún botón.",

        # --- Settings: mode dropdown labels ---
        "settings.mode_mock": "🧪 Prueba (datos de ejemplo)",
        "settings.mode_real": "🌐 Real (API en vivo)",
        "settings.mode_disabled": "⏸ Apagado (saltear)",

        # --- Settings: service sections ---
        "settings.claude_title": "#### 🤖 Claude (IA) — clasifica los sitios",
        "settings.places_title": "#### 🗺 Google — busca negocios",
        "settings.twilio_title": "#### 📱 Twilio — SMS y llamadas",
        "settings.twilio_caption": (
            "Relevante sobre todo en **Estados Unidos, Canadá y Europa**. "
            "Para Argentina y la mayor parte de LatAm usá **WhatsApp** en "
            "su lugar — ahí apagá este canal."
        ),
        "settings.whatsapp_title": "#### 💬 WhatsApp — el canal de LatAm, España, Asia",
        "settings.whatsapp_caption": (
            "Usa la API de WhatsApp Business de Twilio — **comparte las "
            "credenciales** con SMS / llamadas arriba. Para clientes en "
            "**Argentina, México, Brasil, España, India** este es el canal "
            "principal de respuestas."
        ),
        "settings.gmail_title": "#### 📧 Gmail — respuestas por email",
        "settings.storage_title": "#### 🗃 Dónde se guardan los datos",
        "settings.help_expander": "❓ ¿Qué es esto y cómo se configura?",

        # --- Settings: verticals ---
        "settings.verticals_title": "### 🎯 Tipos de negocio a buscar",
        "settings.verticals_caption": (
            "Una fila por tipo de negocio que querés targetear. El `nombre` "
            "es el identificador interno (minúsculas, sin espacios). La "
            "`búsqueda` es el texto que le pasamos a Google — corto y específico."
        ),
        "settings.verticals_save": "💾 Guardar tipos de negocio",
        "settings.verticals_saved": (
            "✅ Guardados {count} tipos de negocio. La próxima búsqueda los "
            "incluye automáticamente."
        ),
        "settings.verticals_col_name": "Nombre interno (minúsculas)",
        "settings.verticals_col_display": "Nombre para mostrar",
        "settings.verticals_col_query": "Búsqueda en Google",
        "settings.verticals_error_required": "Los tres campos son obligatorios. Filas vacías omitidas.",
        "settings.verticals_error_name": (
            "Nombre inválido {name} — usá solo minúsculas, números y guiones "
            "bajos. Fila omitida."
        ),
        "settings.verticals_error_dup": "Nombre duplicado {name} — fila omitida.",
        "settings.verticals_warning": "Nada para guardar — revisá los errores arriba.",

        # --- Footer ---
        "footer.source": "Código fuente: [github.com/juan-alejo/lead-response-intelligence](https://github.com/juan-alejo/lead-response-intelligence)",
    },

    "en": {
        # --- App shell ---
        "app.title": "📡 Lead Response Intelligence",
        "app.subtitle": (
            "Finds prospect businesses, analyzes how they can be contacted, "
            "and measures how quickly they respond. Generates a prioritized "
            "outreach list every Monday — sorted with the slowest "
            "responders first (your best prospects)."
        ),
        "app.github_button": "📖 GitHub repo",
        "app.language": "Language",

        # --- Integration pills row ---
        "pills.header": "**Integrations:**",
        "pills.storage": "**Storage:**",
        "pills.label.places": "Business discovery",
        "pills.label.claude": "AI (classification)",
        "pills.label.twilio": "SMS / Voice",
        "pills.label.whatsapp": "WhatsApp",
        "pills.label.gmail": "Email",
        "pills.mode.real": "live",
        "pills.mode.mock": "demo",
        "pills.mode.disabled": "off",

        # --- Metrics row ---
        "metrics.prospects": "Prospects discovered",
        "metrics.submissions": "Contacts to make",
        "metrics.responses": "Responses received",
        "metrics.match_rate": "Attribution rate",
        "metrics.prospects_help": "Businesses found and saved in the last 90 days.",
        "metrics.submissions_help": (
            "Forms ready for the operator to submit manually. "
            "(Phase 2 will automate this step.)"
        ),
        "metrics.responses_help": "All inbound messages — SMS, WhatsApp, email, calls.",
        "metrics.match_rate_help": (
            "Percentage of responses we could attribute to a specific "
            "submission. Target: 95%+ with well-formed data."
        ),

        # --- Run card ---
        "run.title": "### ▶ Run search for new prospects",
        "run.caption": (
            "In production this runs automatically every Monday at 6 AM. "
            "This button is the manual trigger — useful after editing "
            "business types or for live demos."
        ),
        "run.borough": "Area / City",
        "run.limit": "Max businesses per type",
        "run.button": "🚀 Search now",
        "run.verticals_info": "Will search **{count}** configured business type(s) (edit the list in the Settings tab).",
        "run.status_running": "Searching for prospects across every business type…",
        "run.status_done": "Done — {ingested} found, {matched}/{pulled} responses attributed.",
        "run.success": "✅ Reports refreshed. See the tabs below.",

        # --- Tabs ---
        "tab.outreach": "🎯 Priority list",
        "tab.stats": "📊 Stats",
        "tab.competitors": "🕵 Tools they use",
        "tab.data": "🗂 Raw data",
        "tab.settings": "⚙ Settings",

        # --- Outreach tab ---
        "outreach.empty": "📭 No priority list yet — hit **Search now** above.",
        "outreach.summary": (
            "**{total} prospects** to contact — **{never}** never responded "
            "(highest priority). Sub-2-minute responders are filtered out "
            "automatically."
        ),
        "outreach.filter": "Filter by business type",
        "outreach.download": "⬇ Download filtered CSV",
        "outreach.col.business": "Business",
        "outreach.col.vertical": "Type",
        "outreach.col.method": "How to reach them",
        "outreach.col.elapsed_sec": "Elapsed (sec)",
        "outreach.col.elapsed_human": "Elapsed",
        "outreach.col.email": "Email",
        "outreach.col.phone": "Phone",
        "outreach.col.elapsed_sec_help": "Null = never responded.",

        # --- Stats tab ---
        "stats.empty": "📭 No stats yet — run the search to generate them.",
        "stats.caption": (
            "Average response time per business type. Shorter bars = faster "
            "businesses (less opportunity). Taller bars = your best prospects."
        ),

        # --- Competitors tab ---
        "competitors.empty": "📭 No tool data yet — run the search first.",
        "competitors.caption": (
            "Chat and booking tools detected on each business's website. "
            "A cluster of one tool in one business type is a pitch signal: "
            "**integrate** with it, don't replace it."
        ),

        # --- Data tab ---
        "data.caption": (
            "Direct view of the stored data. Useful for checking why a "
            "message was (or wasn't) attributed to a specific business."
        ),
        "data.radio": "Table",
        "data.option.submissions": "Contacts to make",
        "data.option.responses": "Responses received",
        "data.empty.submissions": "No contacts queued yet.",
        "data.empty.responses": "No responses yet.",

        # --- Settings: setup status ---
        "settings.status_title": "### 🏁 Setup status",
        "settings.status_progress": "{ready}/{total} services configured",
        "settings.status_ready": "✅ {name}",
        "settings.status_mock": "🧪 {name} (demo)",
        "settings.status_disabled": "⏸ {name} (off)",
        "settings.status_needs_key": "⚠ {name} — key missing",

        # --- Settings: demo mode ---
        "settings.demo_title": "### 🧪 Demo mode",
        "settings.demo_caption": (
            "One switch puts everything into safe-sandbox mode — reads from "
            "bundled example data, zero API costs, nothing can break. Turn it "
            "off when you're ready to wire up real services below."
        ),
        "settings.demo_toggle": "Demo mode",
        "settings.demo_toggle_help": (
            "ON = every integration uses example data. OFF = configure real "
            "APIs one at a time."
        ),
        "settings.demo_apply": "✔ Apply: switch everything to {mode}",
        "settings.demo_success": "✅ All channels switched to **{mode}**. Reloading…",
        "settings.demo_on_warning": (
            "🧪 **Demo mode is ON** — fields below are locked so no live API "
            "leaks by accident. Turn demo mode OFF above to edit real "
            "credentials."
        ),

        # --- Settings: integrations header ---
        "settings.integrations_title": "### 🔌 External services",
        "settings.integrations_caption": (
            "One section per service. Each can be in **demo** (safe example "
            "data), **real** (live API), or **off** (skipped entirely). Demo "
            "mode forces everything to demo until you turn it off."
        ),
        "settings.save_integrations": "💾 Save integrations",
        "settings.saved_to_env": "✅ Saved to `{path}`. Next search uses the new values.",
        "settings.autosave_hint": "Changes save automatically — no button needed.",

        # --- Settings: mode dropdown labels ---
        "settings.mode_mock": "🧪 Demo (example data)",
        "settings.mode_real": "🌐 Live (real API)",
        "settings.mode_disabled": "⏸ Off (skip)",

        # --- Settings: service sections ---
        "settings.claude_title": "#### 🤖 Claude (AI) — classifies websites",
        "settings.places_title": "#### 🗺 Google — finds businesses",
        "settings.twilio_title": "#### 📱 Twilio — SMS and voice",
        "settings.twilio_caption": (
            "Mainly relevant in **US / Canada / Europe**. For Argentina and "
            "most of LatAm use **WhatsApp** instead — turn this channel off."
        ),
        "settings.whatsapp_title": "#### 💬 WhatsApp — the main channel for LatAm, Spain, Asia",
        "settings.whatsapp_caption": (
            "Uses Twilio's WhatsApp Business API — **shares credentials** with "
            "the SMS / voice block above. For clients in **Argentina, Mexico, "
            "Brazil, Spain, India** this is the primary response channel."
        ),
        "settings.gmail_title": "#### 📧 Gmail — email responses",
        "settings.storage_title": "#### 🗃 Where data is stored",
        "settings.help_expander": "❓ What is this and how do I set it up?",

        # --- Settings: verticals ---
        "settings.verticals_title": "### 🎯 Business types to search",
        "settings.verticals_caption": (
            "One row per business type you want to target. `name` is the "
            "internal identifier (lowercase, no spaces). `query` is the text "
            "we send to Google — short and specific."
        ),
        "settings.verticals_save": "💾 Save business types",
        "settings.verticals_saved": (
            "✅ Saved {count} business types. Next search picks them up "
            "automatically."
        ),
        "settings.verticals_col_name": "Internal name (lowercase)",
        "settings.verticals_col_display": "Display name",
        "settings.verticals_col_query": "Google search text",
        "settings.verticals_error_required": "All three fields required. Empty rows skipped.",
        "settings.verticals_error_name": (
            "Invalid name {name} — use only lowercase letters, digits, "
            "underscores. Row skipped."
        ),
        "settings.verticals_error_dup": "Duplicate name {name} — row skipped.",
        "settings.verticals_warning": "Nothing saved — fix the errors above.",

        # --- Footer ---
        "footer.source": "Source: [github.com/juan-alejo/lead-response-intelligence](https://github.com/juan-alejo/lead-response-intelligence)",
    },
}


def get_lang() -> str:
    return st.session_state.get("_lang", DEFAULT_LANGUAGE)


def set_lang(lang: str) -> None:
    st.session_state["_lang"] = lang


def tr(key: str, **kwargs) -> str:
    """Translate `key` into the active language, formatting with `kwargs`.

    Falls back to the default language if a key is missing in the active one
    (so partial translations don't crash the UI).
    """
    lang = get_lang()
    table = _TRANSLATIONS.get(lang, _TRANSLATIONS[DEFAULT_LANGUAGE])
    text = table.get(key) or _TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return text.format(**kwargs) if kwargs else text
    except (KeyError, IndexError):
        return text
