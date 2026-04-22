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
        "app.title": "📡 ReachRate",
        "app.tagline": "Medí cómo responde tu mercado.",
        "app.subtitle": (
            "ReachRate mide cada semana cuánto tarda cada negocio de tu "
            "mercado en contestar mensajes — los más lentos son tus "
            "mejores prospectos."
        ),
        "app.github_button": "📖 Código (GitHub)",
        "app.language": "Idioma",

        # --- First-run welcome hero ---
        "welcome.banner": (
            "👋 **¡Bienvenido!** Todavía no hay datos. Probá una búsqueda de "
            "demo para ver cómo funciona — usa datos de ejemplo, no gasta nada."
        ),
        "welcome.step1": "**1. Correr demo** — usamos negocios de ejemplo preconfigurados.",
        "welcome.step2": "**2. Mirar resultados** — se llenan las tabs con lista priorizada y estadísticas.",
        "welcome.step3": "**3. Conectar APIs reales** — cuando quieras, vas a la tab **Configuración**.",
        "welcome.cta": "🚀 Correr búsqueda de demo (30 segundos)",

        # --- Last run indicator ---
        "lastrun.label": "Última búsqueda:",
        "lastrun.never": "aún no se ejecutó",
        "lastrun.ago_minutes": "hace {n} min",
        "lastrun.ago_hours": "hace {n} h",
        "lastrun.ago_days": "hace {n} día(s)",
        "lastrun.just_now": "recién",

        # --- Run history in sidebar ---
        "history.title": "📋 Historial de corridas",
        "history.empty": "Aún no hay corridas.",
        "history.col.when": "Cuándo",
        "history.col.found": "Encontrados",
        "history.col.matched": "Identificadas",


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
        "run.location": "Ubicación",
        "run.limit": "Máximo de negocios a revisar (por tipo)",
        "run.button": "🚀 Buscar ahora",
        "run.verticals_info": "Se van a buscar **{count}** tipo(s) de negocio configurados (editá la lista en la tab Configuración).",
        "run.status_running": "Buscando clientes potenciales en todos los tipos de negocio…",
        "run.status_done": "Listo — encontrados {ingested}, {matched}/{pulled} respuestas identificadas.",
        "run.success": "✅ Reportes actualizados. Mirá las tabs de abajo.",
        "run.error": "❌ Error al correr la búsqueda: {error}. Revisá la tab **Configuración** para verificar que las APIs estén bien seteadas.",

        # --- Home tab ---
        "home.navigation_hint": "👉 Usá las tabs de arriba para ver la **Lista prioritaria**, **Estadísticas**, **Herramientas detectadas** o ajustar la **Configuración**.",

        # --- Home tab: insights cards ---
        "home.insight_title": "💡 Recomendación del día",
        "home.insight_worst_responder": (
            "El peor respondedor es **{name}** ({vertical}) — "
            "tardó **{elapsed}** en responder. Llamalo primero."
        ),
        "home.insight_never_responded": (
            "Hay **{count} negocio(s)** que nunca respondieron — "
            "ésos son tus mejores prospectos. Empezá por ahí."
        ),
        "home.insight_good_match_rate": (
            "📈 Tu tasa de identificación es del **{rate:.0%}** — excelente. "
            "Los datos están bien cargados."
        ),
        "home.insight_low_match_rate": (
            "⚠ Tu tasa de identificación es del **{rate:.0%}** — revisá "
            "que los teléfonos y emails de los prospects coincidan con "
            "las respuestas (pueden venir con formato distinto)."
        ),
        "home.action_title": "🎯 Próxima acción recomendada",
        "home.action_no_data": (
            "📡 Todavía no corriste ninguna búsqueda. Tocá **Buscar ahora** "
            "en el panel lateral para generar tu primera lista."
        ),
        "home.action_demo_mode": (
            "🧪 Estás en **modo demo** — los datos son de ejemplo. Andá a "
            "la tab **Configuración** y apagá el modo demo para conectar "
            "tus APIs reales."
        ),
        "home.action_ready_to_work": (
            "✅ Tenés **{count} clientes potenciales** listos. Abrí la tab "
            "**Lista prioritaria** y empezá a contactarlos."
        ),

        # --- Chart labels ---
        "stats.y_label": "Segundos promedio de respuesta",
        "competitors.y_label": "Cantidad de negocios",
        "competitors.legend": "Herramienta",

        # --- Tabs ---
        "tab.home": "🏠 Inicio",
        "tab.outreach": "🎯 Lista prioritaria",
        "tab.stats": "📊 Estadísticas",
        "tab.competitors": "🕵 Herramientas que usan",
        "tab.data": "🗂 Datos detallados",
        "tab.phase2": "🤖 Envío automático",
        "tab.settings": "⚙ Configuración",

        # --- Outreach tab ---
        "outreach.empty_title": "📭 Todavía no hay lista generada",
        "outreach.empty_desc": (
            "Acá aparece la **lista priorizada de clientes potenciales** "
            "ordenada de más lento a más rápido en responder. Los que "
            "nunca responden van arriba — son tus mejores prospectos."
        ),
        "outreach.empty_cta": "👉 Abrí el panel lateral y tocá **Buscar ahora** para generarla.",
        "outreach.empty": "📭 Todavía no hay lista generada — tocá **Buscar ahora** arriba.",
        "outreach.summary": (
            "**{total} clientes potenciales** para contactar — "
            "**{never}** nunca respondieron (máxima prioridad). "
            "Los que responden en menos de 2 minutos se filtran automáticamente."
        ),
        "outreach.filter": "Filtrar por tipo de negocio",
        "outreach.only_never": "Solo los que nunca respondieron",
        "outreach.download": "⬇ Descargar CSV filtrado",
        "outreach.col.business": "Negocio",
        "outreach.col.vertical": "Tipo",
        "outreach.col.method": "Cómo contactarlos",
        "outreach.col.elapsed_sec": "Tiempo (seg)",
        "outreach.col.elapsed_human": "Tiempo",
        "outreach.col.email": "Email",
        "outreach.col.phone": "Teléfono",
        "outreach.col.elapsed_sec_help": "Vacío = nunca respondieron.",
        "outreach.aggregated_hint": (
            "🧺 Modo agregado activo — mostrando todos los negocios juntos, "
            "sin segmentar por tipo."
        ),

        # --- Stats tab ---
        "stats.empty_title": "📊 Sin estadísticas todavía",
        "stats.empty_desc": (
            "Acá vas a ver el **tiempo promedio de respuesta por tipo "
            "de negocio** — útil para encontrar nichos enteros que "
            "responden lento (oportunidades comerciales grandes)."
        ),
        "stats.empty_cta": "👉 Abrí el panel lateral y tocá **Buscar ahora**.",
        "stats.empty": "📭 Sin estadísticas todavía — corré la búsqueda para generarlas.",
        "stats.caption": (
            "Tiempo de respuesta promedio por tipo de negocio. Barras más "
            "cortas = negocios más ágiles (menos oportunidad). Más altas = "
            "clientes potenciales para vos."
        ),
        "stats.aggregated_caption": (
            "🧺 Vista agregada — KPIs globales ponderados por cantidad de "
            "contactos. El chart por tipo queda oculto; desactivá el modo "
            "agregado en Configuración para verlo."
        ),
        "stats.kpi_total_submissions": "Total de contactos",
        "stats.kpi_avg_response": "Tiempo promedio",
        "stats.kpi_within_24h": "Respondieron <24h",
        "stats.kpi_never": "Nunca respondieron",

        # --- Competitors tab ---
        "competitors.empty_title": "🕵 Sin datos de herramientas todavía",
        "competitors.empty_desc": (
            "Acá aparece **qué herramientas de chat o agenda** usan los "
            "negocios que revisamos (Intercom, Calendly, Drift, etc). "
            "Útil para calibrar el pitch: integrar o reemplazar."
        ),
        "competitors.empty_cta": "👉 Abrí el panel lateral y tocá **Buscar ahora**.",
        "competitors.empty": (
            "📭 Sin datos de herramientas todavía — corré la búsqueda primero."
        ),
        "competitors.caption": (
            "Qué herramientas de chat o agenda tienen instaladas los negocios "
            "que revisamos. Si muchos en el mismo rubro usan la misma "
            "herramienta, es una señal: **integrate** con ella, no la reemplaces."
        ),
        "competitors.aggregated_caption": (
            "🧺 Distribución global — cantidad total por herramienta sin "
            "agrupar por tipo de negocio."
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
        "settings.test_connection": "🔌 Probar conexión",
        "settings.testing": "Probando…",

        # --- Settings: aggregated mode ---
        "settings.aggregated_title": "### 🧺 Modo agregado (sin segmentar por tipo)",
        "settings.aggregated_caption": (
            "Cuando lo activás, el dashboard trata a todos los negocios como "
            "un solo bucket — útil para clientes que venden a muchos rubros "
            "y no les interesa el filtro por tipo. La búsqueda sigue corriendo "
            "todos los tipos configurados; lo que cambia es solo la presentación."
        ),
        "settings.aggregated_toggle": "Activar modo agregado",
        "settings.aggregated_toggle_help": (
            "ON = lista única sin filtros por tipo, stats colapsadas a KPIs "
            "globales. OFF = vista por tipo como siempre."
        ),

        # --- Settings: category packs ---
        "settings.packs_title": "### 📦 Packs de categorías listos",
        "settings.packs_caption": (
            "Plantillas pre-configuradas por región. Elegí un pack, revisá "
            "las categorías que trae, y aplicalo — se reemplazan (o se "
            "suman) a tus tipos actuales con queries probadas en el idioma local."
        ),
        "settings.packs_empty": "No hay packs cargados.",
        "settings.packs_select": "Pack",
        "settings.packs_mode": "Cómo aplicar",
        "settings.packs_mode_replace": "Reemplazar mis tipos actuales",
        "settings.packs_mode_append": "Sumar a mis tipos actuales",
        "settings.packs_preview": "👀 Ver categorías del pack",
        "settings.packs_apply": "✔ Aplicar pack ({mode})",
        "settings.packs_applied": "✅ Pack aplicado — {count} tipos activos.",

        # --- Settings: Claude category generator ---
        "settings.generator_title": "### 🧠 Generar categorías con Claude",
        "settings.generator_caption": (
            "¿No encontrás un pack para tu país o sector? Describile a Claude "
            "lo que buscás y te genera una lista de categorías en el idioma "
            "correcto, con queries que funcionan bien en Google Places para esa región."
        ),
        "settings.generator_disabled_info": (
            "Claude está apagado. Prendelo arriba (Modo real o Modo prueba) "
            "para habilitar el generador."
        ),
        "settings.generator_country": "País / región",
        "settings.generator_country_placeholder": "Argentina, México, Brasil, United States, España…",
        "settings.generator_sector": "Sector / tipo general",
        "settings.generator_sector_placeholder": "servicios profesionales, salud, comercio minorista, hospitalidad…",
        "settings.generator_button": "✨ Generar categorías",
        "settings.generator_mode_mock": "🧪 Modo prueba — ejemplo pre-cargado por país.",
        "settings.generator_mode_real": "🌐 Modo real — llamada a Claude en vivo.",
        "settings.generator_running": "Generando categorías con Claude…",
        "settings.generator_success": "{count} categorías generadas — revisalas abajo.",
        "settings.generator_applied": "✅ Aplicadas — {count} tipos activos ahora.",
        "settings.generator_error": "❌ Error al generar: {error}",
        "settings.generator_preview": "Vista previa",
        "settings.generator_preview_meta": (
            "📍 {country} · 🎯 {sector} · {count} categorías — revisá antes de aplicar"
        ),
        "settings.generator_apply_replace": "✔ Reemplazar mis tipos actuales",
        "settings.generator_apply_append": "➕ Sumar a los existentes",
        "settings.generator_apply_discard": "🗑 Descartar",

        # --- Settings: quick actions ---
        "settings.actions_title": "### 🛠 Acciones rápidas",
        "settings.actions_caption": (
            "Exportá o importá tu configuración para moverte entre "
            "máquinas, o reseteá los datos de demo para empezar de cero."
        ),
        "settings.action_export": "⬇ Exportar configuración (JSON)",
        "settings.action_export_help": (
            "Descarga un archivo con todas las API keys, modos y tipos de "
            "negocio. Útil para backup o para mover la config a otra máquina."
        ),
        "settings.action_import": "⬆ Importar configuración",
        "settings.action_import_help": (
            "Subí un JSON exportado previamente. Sobreescribe tu `.env` y "
            "`verticals.yaml`."
        ),
        "settings.action_import_success": "✅ Configuración importada correctamente.",
        "settings.action_import_error": "⚠ Error al importar: {error}",
        "settings.action_reset": "🗑 Resetear datos de demo",
        "settings.action_reset_help": (
            "Borra la base local de prospectos, envíos y respuestas. "
            "La próxima búsqueda genera todo desde cero. No toca tus API keys."
        ),
        "settings.action_reset_success": "✅ Datos reseteados. Corré la búsqueda para regenerar.",
        "settings.action_reset_confirm": (
            "⚠ Esto borra permanentemente todos los prospectos / envíos / "
            "respuestas almacenados. ¿Continuar?"
        ),

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

        # --- Settings: locations editor ---
        "settings.locations_title": "### 📍 Ubicaciones que podés buscar",
        "settings.locations_caption": (
            "Una fila por zona o país. El **nombre interno** es snake_case "
            "(ej: `caba`, `cordoba_ar`, `mexico_all`). El **sufijo** se "
            "agrega al final de la búsqueda de Google — probá frases como "
            "'in Palermo, Buenos Aires, Argentina' o 'in Argentina' para "
            "cobertura nacional."
        ),
        "settings.locations_col_name": "Nombre interno (snake_case)",
        "settings.locations_col_display": "Nombre para mostrar",
        "settings.locations_col_suffix": "Sufijo para Google (ej: 'in Buenos Aires, Argentina')",
        "settings.locations_saved": "✅ Guardadas {count} ubicaciones.",

        # --- Phase 2 — automated form submission ---
        "phase2.title": "### 🤖 Envío automático de formularios (Phase 2)",
        "phase2.caption": (
            "Automatizamos el paso manual de Phase 1 — el bot llena los "
            "formularios de contacto por vos y guarda una evidencia auditable "
            "de cada envío."
        ),
        "phase2.disabled_banner": (
            "🧪 **Phase 2 está disponible pero desactivada.** Activala desde "
            "el archivo `.env` (`PHASE_2_ENABLED=true`) o contactame para una "
            "cotización de la implementación con Playwright real."
        ),
        "phase2.teaser_what_title": "Qué hace",
        "phase2.teaser_what_body": (
            "- Llena formularios web en modo headless (Playwright / Chromium)\n"
            "- Detecta CAPTCHAs y deriva esos casos a tu cola manual\n"
            "- Maneja chat widgets (Intercom, Drift) y booking widgets "
            "(Calendly, Acuity) vía handlers dedicados\n"
            "- Guarda screenshot + texto de confirmación como evidencia\n"
            "- Reintenta transitorios (timeouts, 502s) con backoff exponencial"
        ),
        "phase2.teaser_cost_title": "Cuánto sale",
        "phase2.teaser_cost_body": (
            "- **Setup base:** USD 800-1200 (implementación + configuración)\n"
            "- **Retainer opcional:** USD 150-250/mes (cuando los sitios "
            "cambian layout, hay que actualizar selectores)\n"
            "- Incluye docs/PHASE_2_SPEC.md — scope, arquitectura, SLA, "
            "entregables, qué NO incluye."
        ),
        "phase2.enable_hint": (
            "👉 Para probar en modo demo: seteá `{flag}` en `.env` y reiniciá "
            "el dashboard. El spec completo está en [`{spec_path}`]({spec_path})."
        ),
        "phase2.metric_pending": "Pendientes",
        "phase2.metric_completed": "Enviados OK",
        "phase2.metric_needs_manual": "Requieren humano",
        "phase2.metric_failed": "Fallaron",
        "phase2.run_title": "▶ Correr el bot sobre la cola pendiente",
        "phase2.run_caption": (
            "Ejecuta el submitter (mock en modo demo, Playwright en prod) "
            "sobre los próximos N envíos pendientes. Los que ya tienen un "
            "intento terminal se saltean."
        ),
        "phase2.run_limit": "Máximo por lote",
        "phase2.run_limit_help": (
            "Empezá bajo (5-10) para ver el comportamiento. En prod típico "
            "se usa 50-100."
        ),
        "phase2.run_button": "🚀 Enviar lote ahora",
        "phase2.run_status_running": "Enviando formularios…",
        "phase2.run_status_done": (
            "Listo — {attempted} intentados, {completed} OK, {manual} "
            "requieren humano, {failed} fallaron."
        ),
        "phase2.run_status_error": "❌ Falló el lote: {error}",
        "phase2.run_success": "✅ Lote completado. Revisá el detalle abajo.",
        "phase2.no_attempts": (
            "Todavía no se ejecutó ningún intento. Tocá **Enviar lote ahora** arriba."
        ),
        "phase2.no_attempts_filtered": "Ningún intento matchea los filtros actuales.",
        "phase2.attempts_title": "Intentos",
        "phase2.filter_status": "Filtrar por estado",
        "phase2.status_pending": "pendiente",
        "phase2.status_submitting": "enviando",
        "phase2.status_completed": "OK",
        "phase2.status_failed": "falló",
        "phase2.status_needs_manual": "requiere humano",
        "phase2.col_status": "Estado",
        "phase2.col_business": "Negocio",
        "phase2.col_vertical": "Tipo",
        "phase2.col_method": "Método",
        "phase2.col_attempts": "Intentos",
        "phase2.col_duration_ms": "Duración",
        "phase2.col_completed_at": "Completado",
        "phase2.col_started_at": "Empezó",
        "phase2.download_csv": "⬇ Descargar CSV",
        "phase2.drilldown_title": "🔎 Detalle por envío",
        "phase2.drilldown_caption": (
            "Elegí un envío para ver los logs y la evidencia (confirmación "
            "del sitio, screenshot, errores)."
        ),
        "phase2.drilldown_select": "Envío a inspeccionar",
        "phase2.attempt_header": "Intento {n} · {icon} {status}",

        # --- Footer ---
        "footer.source": "Código fuente: [github.com/juan-alejo/reachrate](https://github.com/juan-alejo/reachrate)",
    },

    "en": {
        # --- App shell ---
        "app.title": "📡 ReachRate",
        "app.tagline": "Measure how your market responds.",
        "app.subtitle": (
            "ReachRate audits how fast every business in your target market "
            "replies to inbound contact — every week. The slowest are your "
            "best prospects."
        ),
        "app.github_button": "📖 GitHub repo",
        "app.language": "Language",

        # --- First-run welcome hero ---
        "welcome.banner": (
            "👋 **Welcome!** No data yet. Try a demo search to see how this works — "
            "uses bundled example data, costs zero."
        ),
        "welcome.step1": "**1. Run demo** — we use a preconfigured set of example businesses.",
        "welcome.step2": "**2. See results** — tabs fill with a priority list and stats.",
        "welcome.step3": "**3. Plug real APIs** — whenever you're ready, hit the **Settings** tab.",
        "welcome.cta": "🚀 Run demo search (30 seconds)",

        # --- Last run indicator ---
        "lastrun.label": "Last search:",
        "lastrun.never": "never run yet",
        "lastrun.ago_minutes": "{n} min ago",
        "lastrun.ago_hours": "{n} h ago",
        "lastrun.ago_days": "{n} day(s) ago",
        "lastrun.just_now": "just now",

        # --- Run history in sidebar ---
        "history.title": "📋 Run history",
        "history.empty": "No runs yet.",
        "history.col.when": "When",
        "history.col.found": "Found",
        "history.col.matched": "Matched",


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
        "run.location": "Location",
        "run.limit": "Max businesses per type",
        "run.button": "🚀 Search now",
        "run.verticals_info": "Will search **{count}** configured business type(s) (edit the list in the Settings tab).",
        "run.status_running": "Searching for prospects across every business type…",
        "run.status_done": "Done — {ingested} found, {matched}/{pulled} responses attributed.",
        "run.success": "✅ Reports refreshed. See the tabs below.",
        "run.error": "❌ Search failed: {error}. Check the **Settings** tab to verify your APIs are configured correctly.",

        # --- Home tab ---
        "home.navigation_hint": "👉 Use the tabs above to see the **Priority list**, **Stats**, **Detected tools**, or adjust **Settings**.",

        # --- Home tab: insights cards ---
        "home.insight_title": "💡 Today's recommendation",
        "home.insight_worst_responder": (
            "Slowest responder is **{name}** ({vertical}) — took "
            "**{elapsed}** to reply. Call them first."
        ),
        "home.insight_never_responded": (
            "**{count} business(es)** never responded — those are your "
            "best prospects. Start there."
        ),
        "home.insight_good_match_rate": (
            "📈 Your attribution rate is **{rate:.0%}** — excellent. "
            "Data is well-formed."
        ),
        "home.insight_low_match_rate": (
            "⚠ Your attribution rate is **{rate:.0%}** — check that "
            "prospect phones/emails match incoming responses (they may "
            "be coming from different formats)."
        ),
        "home.action_title": "🎯 Next recommended action",
        "home.action_no_data": (
            "📡 No search run yet. Hit **Search now** in the side panel "
            "to generate your first priority list."
        ),
        "home.action_demo_mode": (
            "🧪 You're in **demo mode** — sample data only. Go to the "
            "**Settings** tab and turn off demo mode to connect your real "
            "APIs."
        ),
        "home.action_ready_to_work": (
            "✅ You have **{count} prospects** ready. Open the **Priority "
            "list** tab and start contacting them."
        ),

        # --- Chart labels ---
        "stats.y_label": "Average response seconds",
        "competitors.y_label": "Number of businesses",
        "competitors.legend": "Tool",

        # --- Tabs ---
        "tab.home": "🏠 Home",
        "tab.outreach": "🎯 Priority list",
        "tab.stats": "📊 Stats",
        "tab.competitors": "🕵 Tools they use",
        "tab.data": "🗂 Raw data",
        "tab.phase2": "🤖 Auto-submit",
        "tab.settings": "⚙ Settings",

        # --- Outreach tab ---
        "outreach.empty_title": "📭 No priority list yet",
        "outreach.empty_desc": (
            "This is where the **prioritized prospect list** will show "
            "up — sorted from slowest to fastest responders. Never-"
            "responders float to the top: those are your best leads."
        ),
        "outreach.empty_cta": "👉 Open the side panel and click **Search now** to generate it.",
        "outreach.empty": "📭 No priority list yet — hit **Search now** above.",
        "outreach.summary": (
            "**{total} prospects** to contact — **{never}** never responded "
            "(highest priority). Sub-2-minute responders are filtered out "
            "automatically."
        ),
        "outreach.filter": "Filter by business type",
        "outreach.only_never": "Only show never-responders",
        "outreach.download": "⬇ Download filtered CSV",
        "outreach.col.business": "Business",
        "outreach.col.vertical": "Type",
        "outreach.col.method": "How to reach them",
        "outreach.col.elapsed_sec": "Elapsed (sec)",
        "outreach.col.elapsed_human": "Elapsed",
        "outreach.col.email": "Email",
        "outreach.col.phone": "Phone",
        "outreach.col.elapsed_sec_help": "Null = never responded.",
        "outreach.aggregated_hint": (
            "🧺 Aggregated mode on — showing every prospect in one bucket, "
            "no per-type segmentation."
        ),

        # --- Stats tab ---
        "stats.empty_title": "📊 No stats yet",
        "stats.empty_desc": (
            "This tab shows **average response time per business type** "
            "— handy for spotting whole niches that respond slowly "
            "(large commercial opportunities)."
        ),
        "stats.empty_cta": "👉 Open the side panel and click **Search now**.",
        "stats.empty": "📭 No stats yet — run the search to generate them.",
        "stats.caption": (
            "Average response time per business type. Shorter bars = faster "
            "businesses (less opportunity). Taller bars = your best prospects."
        ),
        "stats.aggregated_caption": (
            "🧺 Aggregated view — global KPIs weighted by submission count. "
            "The per-type chart is hidden; turn off aggregated mode in "
            "Settings to see it."
        ),
        "stats.kpi_total_submissions": "Total submissions",
        "stats.kpi_avg_response": "Avg response time",
        "stats.kpi_within_24h": "Replied <24h",
        "stats.kpi_never": "Never replied",

        # --- Competitors tab ---
        "competitors.empty_title": "🕵 No tool data yet",
        "competitors.empty_desc": (
            "This is where **which chat / booking tools each business "
            "uses** (Intercom, Calendly, Drift, etc.) shows up. Helps "
            "you calibrate the pitch: integrate or replace."
        ),
        "competitors.empty_cta": "👉 Open the side panel and click **Search now**.",
        "competitors.empty": "📭 No tool data yet — run the search first.",
        "competitors.caption": (
            "Chat and booking tools detected on each business's website. "
            "A cluster of one tool in one business type is a pitch signal: "
            "**integrate** with it, don't replace it."
        ),
        "competitors.aggregated_caption": (
            "🧺 Global distribution — total counts per tool without "
            "grouping by business type."
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
        "settings.test_connection": "🔌 Test connection",
        "settings.testing": "Testing…",

        # --- Settings: aggregated mode ---
        "settings.aggregated_title": "### 🧺 Aggregated mode (no type segmentation)",
        "settings.aggregated_caption": (
            "When enabled, the dashboard treats every prospect as a single "
            "bucket — useful for clients selling across many verticals who "
            "don't want per-type filters. Ingestion still runs every "
            "configured type; only the presentation collapses."
        ),
        "settings.aggregated_toggle": "Enable aggregated mode",
        "settings.aggregated_toggle_help": (
            "ON = one list without per-type filters, stats collapsed to "
            "global KPIs. OFF = per-type view as usual."
        ),

        # --- Settings: category packs ---
        "settings.packs_title": "### 📦 Ready-made category packs",
        "settings.packs_caption": (
            "Pre-configured templates per region. Pick a pack, preview the "
            "categories, and apply — either replacing or appending to your "
            "current verticals, with queries vetted for the local language."
        ),
        "settings.packs_empty": "No packs loaded.",
        "settings.packs_select": "Pack",
        "settings.packs_mode": "How to apply",
        "settings.packs_mode_replace": "Replace my current verticals",
        "settings.packs_mode_append": "Append to my current verticals",
        "settings.packs_preview": "👀 Preview pack contents",
        "settings.packs_apply": "✔ Apply pack ({mode})",
        "settings.packs_applied": "✅ Pack applied — {count} verticals active.",

        # --- Settings: Claude category generator ---
        "settings.generator_title": "### 🧠 Generate categories with Claude",
        "settings.generator_caption": (
            "No pack fits your country/sector? Describe what you want to "
            "target and Claude returns a list of categories in the correct "
            "language, with queries that work on Google Places for the region."
        ),
        "settings.generator_disabled_info": (
            "Claude is disabled. Turn it on above (Live or Demo mode) to "
            "enable the generator."
        ),
        "settings.generator_country": "Country / region",
        "settings.generator_country_placeholder": "Argentina, Mexico, Brazil, United States, Spain…",
        "settings.generator_sector": "Sector / broad target",
        "settings.generator_sector_placeholder": "professional services, healthcare, retail, hospitality…",
        "settings.generator_button": "✨ Generate categories",
        "settings.generator_mode_mock": "🧪 Demo mode — pre-loaded sample per country.",
        "settings.generator_mode_real": "🌐 Live mode — real Claude API call.",
        "settings.generator_running": "Generating categories with Claude…",
        "settings.generator_success": "{count} categories generated — review them below.",
        "settings.generator_applied": "✅ Applied — {count} verticals active now.",
        "settings.generator_error": "❌ Generation error: {error}",
        "settings.generator_preview": "Preview",
        "settings.generator_preview_meta": (
            "📍 {country} · 🎯 {sector} · {count} categories — review before applying"
        ),
        "settings.generator_apply_replace": "✔ Replace my current verticals",
        "settings.generator_apply_append": "➕ Append to existing",
        "settings.generator_apply_discard": "🗑 Discard",

        # --- Settings: quick actions ---
        "settings.actions_title": "### 🛠 Quick actions",
        "settings.actions_caption": (
            "Export or import your config to move between machines, or "
            "reset demo data to start fresh."
        ),
        "settings.action_export": "⬇ Export config (JSON)",
        "settings.action_export_help": (
            "Downloads a JSON file with all API keys, modes, and business "
            "types. Handy for backup or moving to another machine."
        ),
        "settings.action_import": "⬆ Import config",
        "settings.action_import_help": (
            "Upload a previously exported JSON file. Overwrites your `.env` "
            "and `verticals.yaml`."
        ),
        "settings.action_import_success": "✅ Config imported.",
        "settings.action_import_error": "⚠ Import error: {error}",
        "settings.action_reset": "🗑 Reset demo data",
        "settings.action_reset_help": (
            "Clears local prospects / submissions / responses. Next search "
            "generates everything from scratch. API keys are kept."
        ),
        "settings.action_reset_success": "✅ Data cleared. Run the search to regenerate.",
        "settings.action_reset_confirm": (
            "⚠ This permanently deletes all stored prospects / submissions / "
            "responses. Continue?"
        ),

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

        # --- Settings: locations editor ---
        "settings.locations_title": "### 📍 Searchable locations",
        "settings.locations_caption": (
            "One row per area or country. The **internal name** is "
            "snake_case (e.g. `manhattan`, `cordoba_ar`, `mexico_all`). "
            "The **suffix** is appended to every Google Places query — "
            "write phrases like 'in Brooklyn, New York' or 'in Argentina' "
            "for country-wide coverage."
        ),
        "settings.locations_col_name": "Internal name (snake_case)",
        "settings.locations_col_display": "Display name",
        "settings.locations_col_suffix": "Google suffix (e.g. 'in Buenos Aires, Argentina')",
        "settings.locations_saved": "✅ Saved {count} locations.",

        # --- Phase 2 — automated form submission ---
        "phase2.title": "### 🤖 Automated form submission (Phase 2)",
        "phase2.caption": (
            "We automate the one manual step in Phase 1 — the bot fills "
            "contact forms for you and keeps an auditable record of every "
            "submission."
        ),
        "phase2.disabled_banner": (
            "🧪 **Phase 2 is available but currently disabled.** Flip "
            "`PHASE_2_ENABLED=true` in `.env` to try the demo submitter, or "
            "reach out for a quote on the full Playwright implementation."
        ),
        "phase2.teaser_what_title": "What it does",
        "phase2.teaser_what_body": (
            "- Fills web forms in headless mode (Playwright / Chromium)\n"
            "- Detects CAPTCHAs and bounces those cases to the human queue\n"
            "- Handles chat widgets (Intercom, Drift) and booking widgets "
            "(Calendly, Acuity) via dedicated handlers\n"
            "- Captures a post-submit screenshot + confirmation text as "
            "audit evidence\n"
            "- Retries transient errors (timeouts, 502s) with exponential backoff"
        ),
        "phase2.teaser_cost_title": "What it costs",
        "phase2.teaser_cost_body": (
            "- **Setup:** USD 800-1,200 (implementation + configuration)\n"
            "- **Optional retainer:** USD 150-250/month (sites change "
            "layouts, selectors need maintenance)\n"
            "- Includes docs/PHASE_2_SPEC.md — scope, architecture, SLAs, "
            "deliverables, out-of-scope."
        ),
        "phase2.enable_hint": (
            "👉 To try the demo submitter: set `{flag}` in `.env` and restart "
            "the dashboard. Full spec at [`{spec_path}`]({spec_path})."
        ),
        "phase2.metric_pending": "Pending",
        "phase2.metric_completed": "Submitted OK",
        "phase2.metric_needs_manual": "Needs human",
        "phase2.metric_failed": "Failed",
        "phase2.run_title": "▶ Run the bot on the pending queue",
        "phase2.run_caption": (
            "Runs the submitter (mock in demo, Playwright in production) "
            "over the next N pending submissions. Anything already in a "
            "terminal state is skipped."
        ),
        "phase2.run_limit": "Max per batch",
        "phase2.run_limit_help": (
            "Start small (5-10) to watch behavior. Typical prod uses 50-100."
        ),
        "phase2.run_button": "🚀 Submit batch now",
        "phase2.run_status_running": "Submitting forms…",
        "phase2.run_status_done": (
            "Done — {attempted} attempted, {completed} OK, {manual} need "
            "human, {failed} failed."
        ),
        "phase2.run_status_error": "❌ Batch failed: {error}",
        "phase2.run_success": "✅ Batch complete. See the detail below.",
        "phase2.no_attempts": (
            "No attempts yet. Hit **Submit batch now** above."
        ),
        "phase2.no_attempts_filtered": "No attempts match the current filters.",
        "phase2.attempts_title": "Attempts",
        "phase2.filter_status": "Filter by status",
        "phase2.status_pending": "pending",
        "phase2.status_submitting": "submitting",
        "phase2.status_completed": "OK",
        "phase2.status_failed": "failed",
        "phase2.status_needs_manual": "needs human",
        "phase2.col_status": "Status",
        "phase2.col_business": "Business",
        "phase2.col_vertical": "Type",
        "phase2.col_method": "Method",
        "phase2.col_attempts": "Attempts",
        "phase2.col_duration_ms": "Duration",
        "phase2.col_completed_at": "Completed",
        "phase2.col_started_at": "Started",
        "phase2.download_csv": "⬇ Download CSV",
        "phase2.drilldown_title": "🔎 Per-submission detail",
        "phase2.drilldown_caption": (
            "Pick a submission to see its logs and audit evidence (site "
            "confirmation, screenshot, errors)."
        ),
        "phase2.drilldown_select": "Submission to inspect",
        "phase2.attempt_header": "Attempt {n} · {icon} {status}",

        # --- Footer ---
        "footer.source": "Source: [github.com/juan-alejo/reachrate](https://github.com/juan-alejo/reachrate)",
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
