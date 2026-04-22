# Lead Response Intelligence Pipeline

> A B2B lead-intelligence pipeline that discovers prospects, classifies
> their inbound-contact mechanisms, watches for responses across SMS /
> WhatsApp / email / voice, and produces a prioritized outreach list
> every Monday morning.

[![CI](https://github.com/juan-alejo/lead-response-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/juan-alejo/lead-response-intelligence/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Playwright](https://img.shields.io/badge/browser-Playwright%20Chromium-45ba4b)
![Claude API](https://img.shields.io/badge/LLM-Claude-d97757)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

---

## What it does

Sales teams at B2B service companies targeting local businesses (law
firms, home services, med spas, dentists, …) live or die by
response-time data: which prospects answer quickly, which never answer
at all, and which chat or booking tool each prospect runs. This pipeline
gathers that signal at scale.

Every Monday morning the pipeline:

1. Pulls fresh prospect businesses from **Google Places** based on
   operator-configured verticals (law firm, dentist, hair salon — edit
   the list from the dashboard).
2. Fetches each prospect's homepage + `/contact` page with **Playwright**
   so JavaScript-heavy sites render correctly.
3. Classifies the primary inbound mechanism with **Claude** — contact
   form, chat widget, booking widget, or none — after a cheap regex
   prefilter handles the obvious cases.
4. Detects competitor tools via **script-signature fingerprinting**
   (Intercom, Drift, Calendly, Acuity, HubSpot Meetings, Intaker,
   JuvoLeads, LiveChat).
5. Watches every response channel — **Twilio** SMS + voice,
   **WhatsApp Business API**, **Gmail** IMAP — and normalizes inbound
   messages into a unified response table.
6. Matches responses to their originating submissions via phone-number
   normalization + case-insensitive email lookup (≥95% attribution on
   well-formed data).
7. Writes three CSVs under `reports/` and refreshes the operator
   dashboard.

---

## Operator dashboard

Built with **Streamlit**. The whole UI is bilingual
(Spanish default, English alternate) and written in operator-friendly
language — no "pipeline", no "classifier", no "ingestion".

![Dashboard preview — main view](docs/screenshots/dashboard-main.png)

Features:

- 🏁 **One-click demo mode** — every integration forced to mock,
  zero API cost, safe sandbox.
- 🌐 **Per-service mode switching** — `mock` / `real` / `disabled`
  so clients that only use WhatsApp can skip Twilio SMS entirely.
- 💾 **Auto-save** — no "Save" button. Every field persists as you
  type.
- 🔌 **Test connection buttons** — live verification of Anthropic,
  Google Places, Airtable, Twilio credentials.
- 📋 **Run history** — last 5 pipeline runs visible at a glance.
- 🛠 **Quick actions** — export config as JSON, import config,
  reset demo data.
- 🎯 **Editable verticals** — add "dentistas en Córdoba" from the UI,
  no code change, no redeploy.
- 🇦🇷 **LatAm-aware help text** — WhatsApp section calls out directly
  to Argentine operators about skipping the SMS/voice channel.

---

## Quick start for operators (no coding required)

### One-click deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/deploy?template=https%3A%2F%2Fgithub.com%2Fjuan-alejo%2Flead-response-intelligence)

Railway gives you $5/mo of free credit — enough to host this for small
clients indefinitely.

### Docker (one command)

```bash
git clone https://github.com/juan-alejo/lead-response-intelligence.git
cd lead-response-intelligence
docker compose up -d
# open http://localhost:8501
```

### Python directly

```bash
pip install -r requirements.txt
playwright install chromium
streamlit run src/dashboard/app.py
```

**Full non-technical walkthrough** (in Spanish):
[docs/CLIENT_ONBOARDING.md](./docs/CLIENT_ONBOARDING.md)

---

## Example output

Running against the bundled mock fixtures (zero API keys needed):

```
$ streamlit run src/dashboard/app.py
→ click "🚀 Correr búsqueda de demo (30 segundos)"

[mock] places returned 3 prospects for law_firm in manhattan
[mock] places returned 2 prospects for home_services in manhattan
[twilio-mock] pulled 4 responses
[whatsapp-mock] pulled 2 responses
[gmail-mock] pulled 2 responses
[matcher] matched 5 / 8 responses (63%)
[report] wrote outreach_priority (7 rows) → reports/outreach_priority.csv
```

Sample reports committed under [`examples/reports/`](./examples/reports/).
The `outreach_priority.csv` looks like this:

```csv
business_name,vertical,submission_method,elapsed_seconds,elapsed_human,prospect_email,prospect_phone
Hoch & Park Family Law,law_firm,chat_widget,,never responded,contact@hochpark.example.com,+12125550103
Empire Roofing Contractors,home_services,contact_form,,never responded,,+12125550202
Aurora Med Spa,med_spa,booking_widget,248700,2d,hello@auroramedspa.example.com,+12125550301
Uptown HVAC & Heating,home_services,contact_form,17100,4h,dispatch@uptownhvac.example.com,+12125550201
Sutter & Associates Law,law_firm,contact_form,4320,1h,intake@sutter-law.example.com,+12125550101
Ramirez Immigration Attorneys,law_firm,chat_widget,1800,30m,intake@ramirez-immigration.example.com,+12125550102
```

The sales team works the never-responders first, then multi-day
offenders — businesses that responded in seconds are filtered out
because they're already operationally tight.

---

## Architecture

```
                 ┌──────────────────────┐
                 │   orgs.yaml / .env   │   (editable from the dashboard)
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │      Pipeline        │     async orchestrator
                 └─┬──────┬──────┬────┬─┘
                   │      │      │    │
              ┌────▼─┐  ┌─▼──┐ ┌▼──┐ ┌▼──────┐
              │Ingest│  │Clas│ │Str│ │Monitor│
              └──┬───┘  │sify│ │age│ │+ Match│
                 │      └─┬──┘ └─┬─┘ └─┬─────┘
                 │        │      │     │
           ┌─────┴┐  ┌────▼──┐   │     │
           │Places│  │Plwrgt │   │   ┌─┴────────────────┐
           │      │  │fetcher│   │   │ SMS / WhatsApp   │
           └──────┘  └───┬───┘   │   │ voice / Email    │
                         │       │   │ (mocks + real    │
                   ┌─────▼────┐  │   │  adapters)       │
                   │  Claude  │  │   └──────────────────┘
                   │ classify │  │
                   └──────────┘  │
                                 │
                           ┌─────▼────┐
                           │  SQLite  │      (or Airtable)
                           └──────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
    ┌─────────▼──────────┐              ┌──────────▼──────────┐
    │  Streamlit         │              │   Weekly CSV        │
    │  operator          │              │   reports/          │
    │  dashboard         │              │                     │
    └────────────────────┘              └─────────────────────┘
```

Every external integration sits behind an abstract interface with
both `mock` and `real` implementations. The operator selects the mode
from the dashboard — no code changes required to swap between local
dev, live APIs, or disable a channel entirely.

---

## Phase 2 — automated form submission (available)

The one manual step in Phase 1 — a human working through the submission
queue — is now automated end-to-end behind a feature flag.

- **Try it in demo mode today.** Set `PHASE_2_ENABLED=true` in `.env`,
  restart the dashboard, open the new **🤖 Auto-submit** tab. The
  bundled `MockFormSubmitter` runs a realistic ~80% success / ~10%
  needs-manual / ~10% failure distribution against the existing
  submission queue.
- **Architecture is already in `main`:** `FormSubmitter` ABC,
  `SubmissionAttempt` data model, storage table + indexes, dashboard
  tab, pipeline integration, 20+ tests.
- **The live Playwright submitter is a paid engagement.** Full
  commercial spec — scope, architecture, pricing tiers, acceptance
  criteria, SLAs, what is NOT included — is in
  [**docs/PHASE_2_SPEC.md**](./docs/PHASE_2_SPEC.md). Starting at
  $800 USD for a single-tenant delivery.

What's covered in the live submitter:

- Standard contact forms (single-page + multi-step + iframe-hosted)
- Chat widgets: Intercom, Drift, Tawk.to, LiveChat, Crisp
- Booking widgets: Calendly, Acuity, HubSpot Meetings
- CAPTCHA detection → graceful hand-off to the human queue (policy
  choice — we don't solve live CAPTCHAs)
- Retries, rate limiting, per-host throttling, audit screenshots

Rolling back is a single flag flip. Phase 1 behavior is unchanged
with the flag off.

---

## Tech stack

- **Python 3.11+**
- **[Playwright](https://playwright.dev/python/)** — JS-aware page
  fetching.
- **[Anthropic Claude](https://www.anthropic.com/claude)** — LLM-based
  form classification with a regex prefilter for cost control.
- **[Streamlit](https://streamlit.io/)** — operator dashboard with
  bilingual UI (`es` / `en`) and per-service config panels.
- **[Pydantic v2](https://docs.pydantic.dev/)** + **pydantic-settings** —
  data models and environment-variable config.
- **[Tenacity](https://tenacity.readthedocs.io/)** / **Loguru** /
  **Typer** / **Rich** — retries, structured logs, CLI, pretty terminal
  output.
- **SQLite** (stdlib) + **Airtable** (via `pyairtable`) — dual storage
  backends behind a shared interface.
- **pytest** + **ruff** + **GitHub Actions CI** — 27 tests green on
  every push.

---

## Real-world challenges solved

The interesting part of the README — design decisions that surface the
moment you build against real data.

### 1. Hybrid classification: regex prefilter + LLM fallback

A naive approach ships every page to Claude. At 200+ prospects per week
that's workable but wasteful — 70% of pages have obvious signatures you
can classify with a handful of regexes. Only the ambiguous 30% hit the
API, shaving ~70% of classifier cost.

### 2. Mock-first architecture — anyone can clone and run

Every external service has two implementations behind a shared abstract
class: a mock backed by JSON fixtures and a real wrapper around the
provider SDK. The `*_MODE` env vars (`mock` / `real` / `disabled`)
select which. CI runs end-to-end against mocks with zero secrets, and
production flips flags with no code changes.

### 3. Phone-number normalization for response matching

`"+1 (555) 123-4567"`, `"5551234567"`, and `"+15551234567"` all refer to
the same number. A naive string-equality matcher hits ~40% attribution.
The matcher strips non-digits and compares the trailing ten digits —
tests confirm ≥95% on a golden set.

### 4. Disabled state per integration

Most clients only use a subset of the integrations. Argentine clients
care about WhatsApp; US clients care about SMS; neither cares about
both. A third state (`disabled`) completely skips the adapter so the
pipeline doesn't waste cycles polling inboxes nobody reads.

### 5. LatAm-aware product copy

The Settings tab's WhatsApp section includes an explicit Spanish-language
callout telling Argentine operators to disable the SMS channel — because
in Argentina, SMS is dead and WhatsApp is the universal inbound channel.
The product speaks the operator's language, not the developer's.

### 6. Auto-save everywhere

The Settings tab has no "Save" button. Every field persists on change
via `on_change` callbacks that write to `.env`. The cognitive load of
"did I save?" is eliminated — any change in the UI is live.

---

## Configuration

Every setting is editable from the **Settings tab** in the dashboard.
Under the hood, values are persisted to:

- **`.env`** — API keys and modes (gitignored, treated as secrets).
- **`config/verticals.yaml`** — the list of business types the
  operator targets. Edit via the data-editor in the UI.
- **`data/*`** — SQLite DB, session files, run history (gitignored).

See [docs/CLIENT_ONBOARDING.md](./docs/CLIENT_ONBOARDING.md) for the
operator-facing version in Spanish.

---

## Selling / delivering this tool

For devs who want to **deliver this to clients**, see
[docs/SELLING_GUIDE.md](./docs/SELLING_GUIDE.md) — pricing tiers,
Upwork proposal templates, demo tips, and protection-against-resale
strategies.

---

## Testing

```bash
pytest              # unit + integration tests (27 green)
ruff check .        # lint
```

The browser flow is deliberately excluded from CI (requires live
Salesforce orgs and interactive MFA). Run it manually against a Dev
Edition org.

---

## Project layout

```
src/
├── config.py                    # pydantic Settings (reads .env)
├── models.py                    # domain types + enums
├── verticals.py                 # YAML-backed Vertical registry
├── pipeline.py                  # end-to-end orchestrator
├── cli.py                       # Typer CLI
├── ingestion/                   # Google Places + CSV + 90-day dedup
├── classification/              # Playwright + Claude + competitor detector
├── storage/                     # SQLite + Airtable (interface stub)
├── monitoring/                  # SMS / voice / WhatsApp / email + matcher
├── reporting/                   # weekly CSV reports
├── submitter/                   # Phase 2 — auto form submission (FormSubmitter ABC, MockFormSubmitter, queue)
└── dashboard/
    ├── app.py                   # Streamlit operator dashboard
    ├── settings_tab.py          # per-service config UI (auto-save)
    ├── connection_tests.py      # live API verification helpers
    ├── phase2_tab.py            # 🤖 Auto-submit queue + drill-down
    └── i18n.py                  # bilingual translations

config/verticals.yaml            # editable vertical definitions
data/fixtures/                   # JSON fixtures driving mock mode
docs/                            # operator + selling guides
tests/                           # pytest suite
.github/workflows/ci.yml         # lint + test on every push
Dockerfile                       # production container image
docker-compose.yml               # one-command local deploy
railway.json                     # Railway deploy config
```

---

## Roadmap

- [x] Ingestion: Google Places + CSV + 90-day dedup
- [x] Classification: Playwright fetch + Claude LLM + competitor detection
- [x] Response monitoring: SMS / voice / WhatsApp / email adapters
- [x] Storage: SQLite + Airtable (interface stub)
- [x] Weekly reporter: 3 CSVs
- [x] Streamlit operator dashboard with bilingual UI + per-service config
- [x] Auto-save, test-connection, run history, export/import config
- [x] Docker + Railway deploy story
- [x] **Phase 2 scaffolding** — `FormSubmitter` ABC + `MockFormSubmitter`
      + dashboard tab + feature flag + commercial spec. Available to try
      today (`PHASE_2_ENABLED=true`); live Playwright submitter delivered
      as a paid engagement — see
      [docs/PHASE_2_SPEC.md](./docs/PHASE_2_SPEC.md) for scope & pricing.
- [ ] Phase 2 live: `PlaywrightFormSubmitter` with widget handlers
      (Intercom, Drift, Calendly, Acuity, HubSpot Meetings)
- [ ] Phase 3 — Multi-tenant / SaaS mode for reselling

---

## License

MIT — see [LICENSE](./LICENSE).
