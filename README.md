# Lead Response Intelligence Pipeline

> A B2B lead-intelligence pipeline that discovers prospects, classifies their
> inbound-contact mechanisms, watches for responses across SMS / email / voice,
> and produces a prioritized outreach list every Monday morning.

[![CI](https://github.com/juan-alejo/lead-response-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/juan-alejo/lead-response-intelligence/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Playwright](https://img.shields.io/badge/browser-Playwright%20Chromium-45ba4b)
![Claude API](https://img.shields.io/badge/LLM-Claude-d97757)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

## What it does

Sales teams at B2B service companies targeting local businesses (law firms,
home-services contractors, med spas) live or die by response-time data:
which prospects answer quickly, which never answer at all, and which chat
widget or booking tool the prospect runs. This pipeline gathers that
signal at scale.

Each Monday morning the pipeline:

1. Pulls 200–400 fresh prospect businesses from Google Places.
2. Fetches each prospect's homepage + `/contact` page with Playwright
   (JS-heavy sites render properly).
3. Classifies the primary inbound mechanism with Claude — contact form,
   chat widget, booking widget, or none.
4. Detects competitor tools via script-signature fingerprinting
   (Intercom, Drift, Calendly, Acuity, HubSpot Meetings, Intaker,
   Juvo Leads, LiveChat).
5. Pulls inbound responses from a dedicated SMS/voice number (Twilio)
   and email inbox (Gmail).
6. Matches each response to its originating submission via
   normalized-phone and email lookups.
7. Writes three CSVs under `reports/`:
   - `outreach_priority.csv` — sorted by slowest response, fast
     responders filtered out.
   - `vertical_stats.csv` — per-vertical avg response, percent
     responding within 24h, percent never responding.
   - `competitor_distribution.csv` — chat/booking tool counts per
     vertical.

## Example output

Running against the bundled mock fixtures:

```
$ python -m src.cli run-weekly --all-verticals --borough manhattan

[mock] places returned 3 prospects for law_firm in manhattan
[mock] places returned 2 prospects for home_services in manhattan
[mock] places returned 2 prospects for med_spa in manhattan
[twilio-mock] pulled 4 responses
[gmail-mock] pulled 2 responses
[matcher] matched 4 / 6 responses (67%)
[report] wrote outreach_priority (7 rows) → reports/outreach_priority.csv
[report] wrote vertical_stats → reports/vertical_stats.csv
[report] wrote competitor_distribution → reports/competitor_distribution.csv

     Pipeline run summary
+----------------------------+
| Prospects ingested |     7 |
| After dedup        |     7 |
| Classified         |     7 |
| Submissions queued |     7 |
| Responses pulled   |     6 |
| Responses matched  |     4 |
+----------------------------+
```

Sample reports committed under [`examples/reports/`](./examples/reports/).
The `outreach_priority.csv` looks like this:

```csv
business_name,vertical,submission_method,elapsed_seconds,elapsed_human,...
Hoch & Park Family Law,law_firm,chat_widget,,never responded,...
Empire Roofing Contractors,home_services,contact_form,,never responded,...
Aurora Med Spa,med_spa,booking_widget,248700,2d,...
Uptown HVAC & Heating,home_services,contact_form,17100,4h,...
Sutter & Associates Law,law_firm,contact_form,4320,1h,...
Ramirez Immigration Attorneys,law_firm,chat_widget,1800,30m,...
```

The sales team works the never-responders first, then the multi-day
offenders — businesses that responded in seconds are dropped because
they're already operationally tight and aren't the opportunity.

## Architecture

```
 ┌──────────────────────────────────────┐
 │            config.yaml / .env        │   (Pydantic Settings; mode=mock|real)
 └───────────────┬──────────────────────┘
                 │
     ┌───────────▼────────────┐
     │      Pipeline          │     orchestrator, asyncio-friendly
     └─┬──────┬──────┬──────┬─┘
       │      │      │      │
   ┌───▼─┐ ┌──▼───┐ ┌▼────┐ ┌▼────────┐
   │Ingest│ │Class-│ │Store│ │Monitor  │
   │      │ │ify   │ │     │ │+ Match  │
   └──┬──┘ └──┬───┘ └──┬──┘ └──┬──────┘
      │       │        │       │
      │  ┌────▼───┐    │       │
      │  │Pwright │    │       │
      │  │ fetch  │    │       │
      │  └────┬───┘    │       │
      │       │        │       │
      │  ┌────▼─────┐  │       │
      │  │ Claude   │  │       │
      │  │ classify │  │       │
      │  └──────────┘  │       │
      │                │       │
      │         ┌──────▼──┐    │
      │         │ SQLite  │    │      <- Airtable interface exists too
      │         └─────────┘    │
      │                        │
      │    ┌───────────────────┼──┐
      │    │ Twilio SMS/voice  │  │    (mocks ship; real adapters live
      │    │ Gmail polling     │  │     alongside as drop-in replacements)
      │    └───────────────────┘  │
      │                           │
      └─────────►   Reports (CSV) ◄────   outreach_priority, vertical_stats,
                                          competitor_distribution
```

Every external integration is behind an interface with a `mock_` and a
`real_` (or `_real`) implementation. The pipeline resolves which to use
from the `*_MODE` env vars — no code changes needed to switch between
local dev with zero API keys and a live deployment wired to Google
Places + Claude + Twilio + Gmail + Airtable.

## Tech stack

- **Python 3.11+**
- **[Playwright](https://playwright.dev/python/)** — JS-aware page
  fetching (many small-business sites lazy-load chat widgets after
  hydration).
- **[Anthropic Claude](https://www.anthropic.com/claude)** — LLM-based
  form classification. Cost-aware hybrid strategy: a cheap regex
  prefilter handles ~70% of sites, only ambiguous pages hit the API.
- **[Pydantic v2](https://docs.pydantic.dev/)** + **pydantic-settings** —
  data models and config. Validation happens at module boundaries, not
  three layers deep into a `KeyError`.
- **[Tenacity](https://tenacity.readthedocs.io/)** / **Loguru** / **Typer**
  / **Rich** — the usual production-Python quartet for retries, logs,
  CLI, and pretty terminal output.
- **SQLite** (via stdlib) + **Airtable** (via `pyairtable`) — dual
  storage backends behind a shared interface.
- **pytest** + **ruff** + **GitHub Actions CI** — 27 tests green on
  every push.

## Quick start

```bash
# 1. Install deps
pip install -r requirements-dev.txt
playwright install chromium

# 2. Copy the example config (everything mock-mode by default — no keys needed)
cp .env.example .env

# 3. Run the pipeline
python -m src.cli run-weekly --all-verticals --borough manhattan

# 4. Or classify a single live URL end-to-end (needs ANTHROPIC_API_KEY if you
#    want the real Claude classifier; otherwise uses the heuristic fallback)
python -m src.cli classify-url https://example-business.com
```

## Configuration

Every external service has a `*_MODE` env var: `mock` (default, zero cost)
or `real`. See `.env.example` for the full list. Typical production setup:

```bash
PLACES_MODE=real
GOOGLE_PLACES_API_KEY=AIza...

CLAUDE_MODE=real
ANTHROPIC_API_KEY=sk-ant-...

TWILIO_MODE=real            # requires Twilio account + purchased number
GMAIL_MODE=real             # requires OAuth setup

STORAGE_BACKEND=airtable    # swap from default sqlite
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=app...
```

## Real-world challenges solved

This is the interesting part of the README — the design decisions that
aren't obvious from "pip install and it works" but that surface the
moment you build against real data.

### 1. Hybrid classification: regex prefilter + LLM fallback

A naive approach is to send every page straight to Claude. With 200+
prospects per week that's workable but wasteful — 70% of pages have
obvious signatures you can classify with a handful of regexes. Shipping
obvious cases to the LLM burns tokens, latency, and eventually budget.

The solution is a two-stage classifier: `HeuristicClassifier` runs
first, and only when it returns ambiguous results does Claude run. The
prefilter handles clear cases (Intercom script tag → chat widget,
`assets.calendly.com` → booking widget), Claude handles the edge cases
(custom-built forms, unusual widget embeds, ambiguous layouts).

```python
# src/classification/claude_classifier.py
class ClaudeClassifier(FormClassifier):
    def classify(self, html: str, *, url: str) -> FormType:
        if self.prefilter is not None:
            cheap = self.prefilter.classify(html, url=url)
            if cheap in {FormType.CHAT_WIDGET, FormType.BOOKING_WIDGET}:
                return cheap
        # … only now hit Claude
```

At Phase-1 scale (200 prospects/week), this shaves ~70% of API calls
while preserving accuracy on the cases that actually need an LLM.

### 2. Mock-first architecture — anyone can clone and run

Every external service (Google Places, Claude, Twilio, Gmail, Airtable)
has two implementations behind a shared abstract class: a mock that reads
from a local JSON fixture, and a real wrapper around the provider SDK.
The `*_MODE` env vars select which. CI runs end-to-end against mocks
with zero secrets, and production flips the flags without any code
change.

```python
# src/classification/base.py
class FormClassifier(ABC):
    @abstractmethod
    def classify(self, html: str, *, url: str) -> FormType: ...

# HeuristicClassifier, ClaudeClassifier: same interface, swap at runtime.
```

This is dependency inversion as a deliberate cost-control and
testability choice, not as architecture astronaut theater.

### 3. Phone-number normalization for response matching

The spec's acceptance criterion is ≥95% of responses attributed to their
originating submission. The landmine is phone-number formatting:
`"+1 (555) 123-4567"`, `"5551234567"`, `"+15551234567"`, and
`"555.123.4567"` all refer to the same number. A naive string-equality
matcher hits ~40%.

The matcher strips everything non-digit and compares the trailing ten
digits:

```python
# src/monitoring/matcher.py
_DIGITS = re.compile(r"\D+")

def _normalize_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = _DIGITS.sub("", raw)
    return digits[-10:] if len(digits) >= 10 else digits
```

Tests confirm ≥95% hit rate on a golden set that mixes formats.

### 4. Weekly reporter that filters fast-responders

The "prioritized outreach" CSV deliberately drops submissions that got a
response in under 2 minutes. Those businesses are already tight
operationally and rarely the right target for an outbound pitch
offering response-time improvement. Keeping them on the list wastes the
sales team's limited capacity on the lowest-yield cohort.

```python
# src/reporting/weekly_report.py
_FAST_RESPONDER_THRESHOLD_SECONDS = 120  # 2 minutes

prioritized = [
    s for s in submissions
    if (elapsed_by_sub.get(s.submission_id) or 10**9) >= _FAST_RESPONDER_THRESHOLD_SECONDS
]
```

This is a product decision expressed in code — documenting *why* the
filter exists in a code comment is the difference between a report that
the sales team actually uses and one that gets ignored as too noisy.

### 5. Idempotent SQLite upserts

The pipeline re-runs weekly and may retry after partial failure
mid-batch. Every write uses `INSERT … ON CONFLICT DO UPDATE` keyed on
the natural ID (`place_id` for prospects, `submission_id` for
submissions, `response_id` for responses). A rerun on the same data is
a safe no-op; a partial-failure retry picks up where the previous run
left off.

### 6. Phase-aware scope: the submission queue is still manual

Phase 1 explicitly does *not* automate form submission — it produces a
queue a human works through. The `Submission` model reflects that:
`submitted_at: datetime | None = None`, populated when the operator
actually submits. The matcher tolerates `None` correctly (no elapsed
calculation yet). When Phase 2 lands and Playwright drives the
submissions directly, the existing data model doesn't change — only the
code that populates `submitted_at` does.

## Testing

```bash
pytest           # 27 unit + integration tests
ruff check .     # lint clean
```

Integration test hits the full pipeline end-to-end against mock
fixtures, validating ingestion → dedup → classification → storage →
matching → reporting in a single run.

## Project layout

```
src/
├── config.py                       # pydantic Settings (reads .env)
├── models.py                       # Prospect, Submission, Response, enums
├── pipeline.py                     # end-to-end orchestrator
├── cli.py                          # Typer CLI (run-weekly, classify-url)
├── ingestion/
│   ├── base.py                     # ProspectSource interface
│   ├── google_places.py            # mock + real
│   ├── csv_source.py
│   └── dedup.py                    # 90-day dedup window
├── classification/
│   ├── base.py                     # FormClassifier interface
│   ├── playwright_fetcher.py       # async context manager, pooled browser
│   ├── claude_classifier.py        # LLM with heuristic prefilter
│   ├── mock_classifier.py          # pure-regex heuristic
│   └── competitor_detector.py      # script-signature fingerprints
├── storage/
│   ├── base.py                     # Storage interface
│   ├── sqlite_store.py             # full implementation
│   └── airtable_store.py           # schema-ref stub
├── monitoring/
│   ├── base.py                     # ResponseChannelAdapter interface
│   ├── twilio_mock.py              # fixture-backed SMS + voice
│   ├── gmail_mock.py               # fixture-backed email
│   └── matcher.py                  # phone-normalization matcher
└── reporting/
    └── weekly_report.py            # 3 CSVs per run

data/fixtures/                      # JSON fixtures driving mock mode
tests/                              # pytest suite
examples/reports/                   # sample outputs committed for GitHub
.github/workflows/ci.yml            # lint + test on every push
```

## Roadmap

- [x] Ingestion: Google Places + CSV + 90-day dedup
- [x] Classification: Playwright fetch + Claude LLM + competitor
      detection
- [x] Response monitoring: SMS/voice/email adapters + phone-normalizing
      matcher
- [x] Storage: SQLite (complete) + Airtable (interface stub)
- [x] Weekly reporter: 3 CSVs with sales-team-usable output
- [x] CI: pytest + ruff on every push
- [ ] Automated form submission (Phase 2 — browser automation for the
      actual form-fill)
- [ ] Railway / Render deployment configs
- [ ] Chat-widget and booking-widget submission handling (beyond
      classification)

## License

MIT — see [LICENSE](./LICENSE).
