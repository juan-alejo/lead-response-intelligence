# Phase 2 — Automated Form Submission

**Technical specification & commercial offer.** This document is the
customer-facing statement of work for implementing the Phase 2 upgrade
on top of the existing ReachRate pipeline.

> Audience: a technical buyer at a B2B lead-intelligence or sales-
> automation company who already uses Phase 1 (or is about to) and
> wants the submission step automated. Non-technical buyers should
> start from §1 and stop after §5.

---

## Table of contents

1. [Problem & goal](#1-problem--goal)
2. [What's in scope](#2-whats-in-scope)
3. [What's **out** of scope](#3-whats-out-of-scope-anti-scope-creep)
4. [Architecture](#4-architecture)
5. [Pricing tiers](#5-pricing-tiers)
6. [Timeline & milestones](#6-timeline--milestones)
7. [Deliverables](#7-deliverables)
8. [Success criteria & acceptance tests](#8-success-criteria--acceptance-tests)
9. [SLAs, warranties, and post-delivery support](#9-slas-warranties-and-post-delivery-support)
10. [Hand-off to Phase 1](#10-hand-off-to-phase-1)
11. [Frequently-asked questions](#11-frequently-asked-questions)

---

## 1. Problem & goal

Phase 1 of the pipeline discovers prospect businesses, classifies their
inbound-contact mechanisms, and produces a **manual queue** of
submissions — a list of `(business_name, form_url, expected_method)` that
a human still has to work through by hand.

On a weekly cadence with ~200 prospects, **the human submission step is
3–4 hours of click-and-type work** per operator. That cost compounds:

- It's the single reason clients can't run the pipeline at 500+ prospects/week.
- It introduces a human-scheduling bottleneck into an otherwise-automated loop.
- It's the cheapest operation to automate relative to its time cost.

**Phase 2 goal:** remove the human from the queue. Every Phase 1 submission
row gets filled automatically, with evidence captured for every attempt,
with graceful bounce-back to the human queue in the cases where automation
isn't safe (CAPTCHA, auth walls, chat-agent handoffs).

---

## 2. What's in scope

### 2.1 Core submitter

A `PlaywrightFormSubmitter` implementation of the `FormSubmitter`
abstract class (already shipped in Phase 1 at `src/submitter/base.py`).
It:

- Navigates the form URL with Chromium in headless mode.
- Detects the form type dynamically (not just from classifier output).
- Fills every required and labeled optional field from the configured
  `LeadIdentity` (`full_name`, `email`, `phone`, `company`, `message`).
- Clicks the submit control and waits for a post-submit indicator
  (redirect, success banner, thank-you page).
- Captures a full-page screenshot as proof-of-submission.
- Extracts the site's confirmation text into `SubmissionAttempt.confirmation_text`.
- Handles ~80% of real-world contact forms end-to-end (see §8 for how
  this is measured).

### 2.2 Contact forms — standard coverage

| Pattern | Handled | Notes |
|---|---|---|
| Single-page `<form>` with labeled fields | ✅ | 70% of the real world |
| Multi-step wizards (Next / Next / Submit) | ✅ | State machine detects step progression |
| Forms in iframes (HubSpot, Marketo, Pardot) | ✅ | Iframe switching via frame-locator |
| React/Next.js forms (no `name=`, only `id=` or `aria-label`) | ✅ | Accessibility-first selector fallback chain |
| Forms with client-side validation | ✅ | Real typing (not `value=` assignment) so onInput fires |
| Forms requiring checkbox consent | ✅ | Auto-clicks consent boxes; this is documented and configurable |

### 2.3 Chat widgets

| Widget | Handled | Method |
|---|---|---|
| **Intercom** | ✅ | Posts message via `/messenger/conversations` REST endpoint when available, DOM fallback otherwise |
| **Drift** | ✅ | `window.drift.api.startInteraction` injection |
| **Tawk.to / LiveChat / Crisp** | ✅ | DOM-based message send |
| **Proprietary / obscure** | ⚠ | Falls through to `needs_manual` — safer than trying to autofill a black-box widget |

### 2.4 Booking widgets

| Widget | Handled | Method |
|---|---|---|
| **Calendly** | ✅ | Fills intake form, picks first open slot in a 14-day window |
| **Acuity Scheduling** | ✅ | Same pattern as Calendly |
| **HubSpot Meetings** | ✅ | Iframe-aware version of the above |
| **Custom booking flows** | ⚠ | `needs_manual` — booking is a commitment and we refuse to guess |

> **Booking-widget policy:** we intentionally **book the latest** available
> slot in the configured window, not the earliest, to minimize calendar
> pollution on the prospect's side. The slot is immediately canceled by
> the matcher once a response arrives — so the prospect sees "someone
> booked then canceled" rather than a no-show, which preserves good will.
> This behavior is toggleable from the Settings tab.

### 2.5 CAPTCHA handling (policy-first)

CAPTCHAs are **bounced back to the human queue** — no solving, no third-
party services, no behavioral evasion. Reasoning:

- Most commercial CAPTCHA-solvers violate the TOS of the CAPTCHA provider.
- Behavioral evasion (mouse jitter, randomized delays) works today and
  breaks tomorrow. Brittle foundations lead to unhappy retainer months.
- The cost of a human solving the 5–10% of submissions that need it is
  low enough that policy purity is cheaper than running the cat-and-mouse
  game.

Covered CAPTCHA variants detected and gracefully bounced:

- Google reCAPTCHA v2 (checkbox and invisible)
- Google reCAPTCHA v3 (score-based)
- hCaptcha
- Cloudflare Turnstile
- Custom honeypot fields (invisible inputs)

Each detection writes a specific `error_message` into the attempt so the
human queue shows *why* a submission needs manual work.

### 2.6 Error handling & retries

- Transient errors (timeouts, 502/503/504, DNS glitches) retry up to
  **3 times** with exponential backoff (1s, 4s, 16s).
- Permanent errors (404, form-structure change, required field missing)
  fail immediately with a descriptive `error_message`.
- Per-submission hard timeout: **45 seconds**. Anything longer is aborted
  and marked `failed` with a `timeout` error code.

### 2.7 Observability

- Every attempt appears in the **Phase 2 tab** of the dashboard with
  status, duration, logs, confirmation text, and screenshot link.
- Aggregate metrics surface in the **Home tab**: completion rate, p50/p95
  duration, needs-manual rate, per-vertical breakdown.
- Structured logs in JSON format for ingestion into Datadog / Logfire /
  whatever the client uses.

### 2.8 Rate-limiting & throttling

Operator-configurable via Settings:

- **Max submissions per host per week** (default `1`) — a courtesy cap
  to avoid drowning any single business.
- **Min delay between submissions** (default `2s`) — spread load on
  shared DNS / CDN infrastructure.
- **Per-batch concurrency** (default `1`, max `8`) — the live submitter
  is I/O-bound and trivially parallelizable, but "more is better" isn't
  always true: many anti-bot services look for parallel request patterns.

### 2.9 Feature flag & roll-back story

Phase 2 ships gated behind `PHASE_2_ENABLED=false` (default). Operators:

1. Enable the flag in Settings → Phase 2.
2. Run a **dry-run** batch (uses `MockFormSubmitter` even in production
   mode) to verify the UI flow.
3. Flip to live mode (`SUBMITTER_MODE=real`) when comfortable.
4. Roll back by flipping the feature flag off — all Phase 1 behavior
   continues unchanged without any data migration.

---

## 3. What's **out** of scope (anti scope-creep)

Listed explicitly so the engagement can't drift. Each of these is
addressable in a separate engagement; the price reflects the scope
fixed here.

### Not included in Phase 2

- **CAPTCHA-solving-as-a-service integrations** (2Captcha, Anti-Captcha,
  Death-by-Captcha). See §2.5 for policy reasoning. Available as a
  bolted-on $300 add-on if the client accepts the TOS risk.
- **Human-in-the-loop escalation UI beyond the `needs_manual` queue.**
  The Phase 2 tab shows every bounced submission; we don't build a
  separate ops panel, ticketing integration, or on-call paging.
- **Prospect enrichment** (finding decision-maker emails, LinkedIn
  lookups, Clearbit / Apollo integration). The `LeadIdentity` is a fixed
  test identity owned by the operator; Phase 2 doesn't look up who
  should sign the lead.
- **A/B message testing** or LLM-generated outreach copy. The message
  field is static — supplied once in Settings. Generating personalized
  copy per prospect is a separate engagement (~$500).
- **Live submitter for non-English forms.** The form-detection heuristics
  are English-first. Spanish, Portuguese, and French coverage is a $400
  add-on per language; the locale selector is already wired, just not
  populated.
- **Non-HTTP submission paths.** Phone calls, faxes, mailed postcards,
  walk-in visits — automation stops at the HTML boundary.
- **Integrations with the prospect's internal tooling.** We don't push
  into the prospect's Salesforce / HubSpot / Zoho. We submit through
  their public contact surface like a real lead would.
- **Multi-tenant SaaS hosting.** Every engagement delivers a
  single-tenant instance. SaaS conversion is covered by the roadmap
  item labeled "Phase 3 — SaaS mode" (separate $4-8k engagement).
- **Dark-pattern defeats.** If a form hides the submit button until
  you scroll, or requires a specific scroll velocity, we refuse to
  reverse-engineer the trick. Legitimate forms don't need that.
- **Jurisdiction-specific compliance review.** CCPA, GDPR, LGPD, TCPA,
  CAN-SPAM implications of automated form submission are the client's
  responsibility. We provide a checklist (§11) but not legal advice.

### Conditionally in scope

| Item | Condition |
|---|---|
| Test-lead identity provisioning (number, email) | Included for Tier 3; client provides their own for Tier 1 and 2. |
| Dashboard branding customization (logo, colors) | Tier 3 only. |
| CI/CD pipeline for the client's infrastructure | If client's infra is Railway / Fly.io / Render — yes. Anything else: quote separately. |

---

## 4. Architecture

```
                      ┌──────────────────────┐
                      │  Phase 1 pipeline    │
                      │  (unchanged)         │
                      └───────────┬──────────┘
                                  │ queues Submission rows
                                  ▼
                      ┌──────────────────────┐
                      │  submissions table   │ (SQLite / Airtable)
                      └───────────┬──────────┘
                                  │
                                  │ read by
                                  ▼
        ┌─────────────────────────────────────────────┐
        │             SubmissionQueue                 │
        │  ─ filters terminal attempts                │
        │  ─ applies vertical / limit filters         │
        │  ─ dispatches to the configured submitter   │
        │  ─ writes SubmissionAttempt rows back       │
        └───────────────────┬─────────────────────────┘
                            │
          ┌─────────────────┼─────────────────────┐
          ▼                 ▼                     ▼
    MockFormSubmitter   PlaywrightFormSubmitter   (future)
    (shipped, demo)     (Phase 2 deliverable)     e.g. Selenium
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
  FormHandlers/                           Observability/
   ─ contact_form                          ─ screenshots/
   ─ chat_widget (Intercom, Drift, ...)    ─ structured logs
   ─ booking_widget (Calendly, Acuity)     ─ metrics
   ─ captcha_detector  → needs_manual
```

### 4.1 Why Playwright (not Selenium)

- **Auto-wait semantics.** Selenium needs explicit waits everywhere and
  race-conditions leak out. Playwright's "actionability checks" eliminate
  the top-3 source of flaky form automation.
- **Frame isolation.** Iframes (HubSpot, Marketo, Pardot forms) are
  first-class in Playwright's model. In Selenium they're a special case
  that's easy to get wrong.
- **Network mocking.** Cheap to stub a backend response during tests, so
  the CI pipeline exercises the submitter without hitting real sites.
- **Already a dependency.** Phase 1 uses Playwright for the page-fetch
  step — zero new infrastructure to add Phase 2.

### 4.2 Why the `FormSubmitter` abstract class

Shipped in Phase 1 expressly to make Phase 2 additive, not invasive.
The live `PlaywrightFormSubmitter` is a drop-in replacement for
`MockFormSubmitter` — the pipeline, storage, dashboard, and tests all
depend only on the abstract class. Swapping implementations is a
one-line change in `Pipeline._build_submitter`.

### 4.3 Storage impact

Phase 1 has three tables: `prospects`, `submissions`, `responses`.
Phase 2 adds one more: `submission_attempts`. Already shipped and
exercised in Phase 1's CI so the schema is stable before you add
a single line of submitter code.

### 4.4 How Phase 2 composes with Phase 1

- **Ingestion** → unchanged.
- **Classification** → unchanged.
- **Submission queueing** → unchanged.
- **Auto-submission (new)** → runs after queueing, before response monitoring.
- **Response monitoring** → unchanged. The responses the submitter
  triggers (confirmation emails, auto-responders) flow through the
  matcher exactly like human-submitted ones.
- **Reporting** → two extra columns in the outreach CSV: `auto_submitted_at`
  and `auto_attempt_status`.

Every Phase 1 assertion in the existing test suite continues to hold
with Phase 2 enabled.

---

## 5. Pricing tiers

All prices in USD. Fixed-price engagements — no hourly billing. Payment
terms: 50% on kickoff, 50% on acceptance.

### Tier 1 — **Essentials** ($800)

For clients who already have Phase 1 running and want the happy-path
automation without the bells.

- ✅ `PlaywrightFormSubmitter` for standard HTML forms (§2.2).
- ✅ Contact-form coverage (§2.2, rows 1–3, 6).
- ✅ CAPTCHA detection → `needs_manual` (§2.5).
- ✅ Basic retries + timeouts (§2.6).
- ✅ Dashboard Phase 2 tab fully wired (already shipped in Phase 1 code).
- ✅ 1 onboarding call (60 min).
- ❌ Chat/booking widgets (graceful `needs_manual` fallback only).
- ❌ Client-specific selectors for custom sites.

**Good fit for:** clients whose prospects use off-the-shelf form plugins
(WordPress / Wix / Squarespace defaults) and who are fine with a ~60%
end-to-end completion rate (the rest bouncing to manual).

### Tier 2 — **Production** ($1,200) · **recommended**

What most clients actually want. Designed to hit the §8 acceptance
target on a real prospect cohort.

- ✅ Everything in Tier 1.
- ✅ Full contact-form coverage (§2.2 all rows).
- ✅ Chat widget handlers for Intercom, Drift, Tawk.to, LiveChat, Crisp (§2.3).
- ✅ Booking-widget handlers for Calendly, Acuity, HubSpot Meetings (§2.4).
- ✅ Rate-limiting / throttling controls (§2.8).
- ✅ Structured JSON logging + screenshot capture (§2.7).
- ✅ 2 onboarding calls (kickoff + go-live review).
- ✅ 2 weeks of post-delivery support (§9).

**Expected completion rate:** 75–85% of a representative prospect list,
depending on vertical. Law firms cluster higher (standardized intake
forms); custom-built med-spa sites cluster lower.

### Tier 3 — **White-glove** ($1,800 + optional $250/mo retainer)

For clients who treat the pipeline as a core product capability.

- ✅ Everything in Tier 2.
- ✅ **Client-specific selector pack** — we audit the client's first
  100 prospects and hand-tune fallback selectors for their top 10
  most-common site frameworks.
- ✅ **Dashboard branding** — logo, color palette, custom footer. No
  "ReachRate" visible unless the client wants it.
- ✅ **Observability integration** — push structured logs + metrics to
  one of: Datadog, Grafana Cloud, Logfire, or Honeycomb.
- ✅ **Dry-run report** — we run the submitter against your entire
  prospect backlog in a staging environment and deliver a per-site
  compatibility report before going live.
- ✅ 3 onboarding calls + a 30-min Slack-office-hours window weekly
  for the first month.
- ✅ 4 weeks of post-delivery support.
- ✅ (Optional) **Retainer** — $250/mo covering selector maintenance,
  quarterly audits, and SLA upgrades (§9).

---

## 6. Timeline & milestones

Assumes Tier 2 (Production). Tier 1 is −1 week; Tier 3 is +1 week for
the selector-pack audit.

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1 | Kickoff + environment audit | Go/no-go on target sites; list of prospects sampled for coverage; `.env` template delivered. |
| 2 | Core submitter | `PlaywrightFormSubmitter` lands behind the feature flag. Mock CI runs unchanged. Happy-path contact forms working end-to-end. |
| 3 | Widget handlers + CAPTCHA policy | Intercom/Drift/Calendly/Acuity handlers + CAPTCHA detectors shipped. Dashboard shows real attempts. |
| 4 | Hardening + acceptance | Rate limiting, error taxonomy, structured logs. Acceptance test (§8) run against client's actual prospect list. Go-live sign-off. |
| 5 | Post-delivery support | Two weeks of bug-triage; any selector breakage fixed same-day. |

**Calendar weeks, not full-time weeks.** My hours-per-week budget on the
engagement is ~12–15 (this is a side-project; the day job stays).
Milestone dates move with the calendar, not with work-hours.

---

## 7. Deliverables

At acceptance (end of week 4), the client receives:

1. **Merged PR to `main`** with:
   - `src/submitter/playwright.py` — the live submitter.
   - `src/submitter/handlers/` — one file per widget handler.
   - `src/submitter/captcha.py` — CAPTCHA detectors.
   - Full pytest coverage — 50+ new tests, CI green.
   - Lint clean (`ruff check .`).
2. **Updated documentation**:
   - `docs/PHASE_2_OPERATIONS.md` — runbook for the operator.
   - `docs/PHASE_2_TROUBLESHOOTING.md` — failure taxonomy + fixes.
   - README.md updated to reflect Phase 2 availability.
3. **Deployment artifacts**:
   - Updated `Dockerfile` with Playwright browser install.
   - Updated `railway.json` + `docker-compose.yml` for the new
     browser-heavy container footprint.
4. **Sign-off package**:
   - Acceptance test results (§8) against a client-supplied 50-prospect
     sample.
   - Screenshots from 10 successful submissions as evidence.
   - Per-site compatibility matrix.
5. **Onboarding recording** — the go-live call, recorded and indexed,
   so any new operator can bootstrap cold.

---

## 8. Success criteria & acceptance tests

The engagement is **accepted** when all of the following hold against
a client-supplied representative sample of **50 prospects**:

### 8.1 Hard gates

Every gate must pass — any single gate failing blocks acceptance.

- [ ] **≥ 95% of Phase 1 tests still pass** with the new submitter wired
      in. (Target: 100%. The 5% slack covers unavoidable flakiness in
      browser tests.)
- [ ] **≥ 70% end-to-end completion rate** on contact-form prospects.
      (Excludes prospects classified as `none` or `chat_widget` without
      a handler.)
- [ ] **≥ 85% correct routing** — i.e., of the submissions the
      submitter decides NOT to auto-complete, ≥ 85% are correctly
      classified as `needs_manual` (not `failed`). Miscategorizing a
      CAPTCHA wall as a generic failure is a bug; miscategorizing a
      real page-layout change as `needs_manual` is a bug.
- [ ] **0 submissions to sites the operator hasn't approved**. The rate-
      limiter + allowlist configuration prevents accidental submissions.
- [ ] **p95 submission latency ≤ 15 seconds** at concurrency=1.

### 8.2 Soft targets

These aren't acceptance gates but are reported on the sign-off summary:

- Throughput at concurrency=4 (target: ≥ 100 submissions / 10 minutes).
- Dashboard Time-to-First-Paint (target: ≤ 1.5s on a fresh batch).
- Selector robustness — percentage of top-10 frameworks covered by
  fallback selector chains (target: ≥ 80%).

### 8.3 How the numbers get measured

At engagement start the client supplies a list of **50 representative
prospects** (ideally mixed across law firms, home services, med spas,
or whatever verticals they target). The submitter runs against that
list at the end of week 4. The results — with screenshots and logs —
are reviewed on the sign-off call. No surprises at the end.

---

## 9. SLAs, warranties, and post-delivery support

### 9.1 Default (included in every tier)

- **Bug-fix window.** 2 weeks (Tier 1/2) or 4 weeks (Tier 3) from
  acceptance. Any regression against the acceptance tests is fixed at
  no additional cost.
- **Warranty on selector drift.** If a site covered by the top-10
  framework pack changes layout within **30 days** of delivery, I ship
  a fix at no cost. Past 30 days it falls under retainer (or a T&M
  hourly rate of $80).
- **Response time.** Business-day response within 24 hours by email or
  WhatsApp. I'm in Argentina (UTC-3); overlap with US Eastern
  business hours is comfortable.

### 9.2 Retainer upgrade (+$250/mo, optional on Tier 3)

- **Selector-drift coverage extended to 90 days rolling.** Any
  site-layout change that breaks submission gets fixed within 48
  business hours, retainer months cumulatively.
- **Quarterly audit report.** Four times a year: completion-rate trend,
  needs-manual volume, emerging framework coverage gaps.
- **Priority SLA.** First-response in 4 business hours for anything
  marked urgent.

### 9.3 What's NOT covered under any SLA

- **Intentional anti-bot changes** by the prospect's site. If a target
  deploys Cloudflare Turnstile specifically to stop you, that's a
  product-policy question, not a bug.
- **Client-side environment issues.** If `playwright install chromium`
  is failing in the client's Docker image, that's a support question
  (paid) not a warranty claim.
- **Infrastructure downtime** caused by the client's hosting choice.
  Railway, Render, Fly.io, Heroku — all have independent uptime
  guarantees. If their platform is down, so is your submitter.

---

## 10. Hand-off to Phase 1

Every Phase 1 behavior must hold after Phase 2 lands. Acceptance tests
include running the original `test_pipeline.py::test_full_pipeline_law_firm_manhattan`
with the Phase 2 feature flag off — output should be byte-identical to
pre-Phase-2.

### Rollback procedure (documented for the operator)

1. Set `PHASE_2_ENABLED=false` in `.env`.
2. Restart the dashboard / cron.
3. (Optional) run `DELETE FROM submission_attempts` — Phase 1 tables
   are untouched, the attempts table is additive.

No migration needed to roll back. This is an invariant of the design
and is tested by the existing Phase 1 test suite continuing to pass.

---

## 11. Frequently-asked questions

### "Is this legal?"

Automated form submission to a publicly-available contact form is legal
in most jurisdictions where the submission mirrors what a human lead
would do — i.e., you're submitting a real inquiry on behalf of a real
business prospect, not scraping or DDOSing. That said:

- **You** are responsible for verifying compliance with your
  jurisdiction's regulations (CAN-SPAM, TCPA, GDPR, LGPD, CASL, etc.).
- **You** are responsible for the contents of the `message` field and
  for keeping `LeadIdentity` accurate to your business.
- **You** are responsible for respecting `robots.txt` directives on
  target sites — the submitter does, but content of submissions
  (frequency, targeting) is a product decision you make.

We provide a compliance-checklist starter in
`docs/PHASE_2_COMPLIANCE_CHECKLIST.md` delivered with the engagement —
not legal advice, but the checklist our most conservative clients use.

### "Will my clients' prospects know this is automated?"

Post-submission, yes — eventually. A sales team fielding one inquiry
from a real human and one from an automation eventually notices the
difference. The design deliberately makes the automation:

- **Respectful of rate limits** (§2.8): one submission per prospect per
  week, max.
- **Accurate in the lead identity**: we're not pretending to be a
  different person than the operator's business.
- **Transparent when caught**: the confirmation messages can optionally
  include a "(automated deliverability test)" suffix, which we strongly
  recommend and which is on by default.

### "What happens when a site redesigns?"

Under retainer: we fix selectors within the SLA window. Off retainer:
we bill T&M ($80/hr) or the client can wait for the 30-day warranty to
re-trigger.

The more important answer is that the selector fallback chain is
deliberately layered: `name=`, `id=`, `aria-label=`, semantic role,
nearest label text. A typical redesign breaks the top layer but not
all four. Empirically, ~15% of site redesigns break our submitter
completely; 85% degrade gracefully.

### "Can I test before paying?"

Yes. The free Phase 1 codebase ships with `MockFormSubmitter` —
flip `PHASE_2_ENABLED=true` and everything except the live submission
works. You get the full dashboard tab, the attempt audit trail, the
acceptance-test harness. What you don't get is real submissions to
real sites until the engagement delivers the live Playwright submitter.

### "What if I already have a form-submitter I want integrated?"

Two paths:

1. **Drop-in replacement.** If your existing submitter speaks our
   `FormSubmitter` ABC, we write an adapter — typically ~$200.
2. **Hybrid.** Use your submitter for some verticals, ours for others,
   wired behind `submitter_mode=custom` and a dispatch table. Priced
   per engagement.

### "Do you offer Phase 2 as a service instead of an engagement?"

Not yet. Managed hosting ("Phase 3 — SaaS mode") is on the product
roadmap for 2026 Q3. In the meantime: single-tenant engagements only.

---

## Appendix A — Change log

- **v1.0** (2026-04-22) — Initial spec, shipped alongside the Phase 2
  scaffolding (`src/submitter/` + dashboard tab + feature flag).

## Appendix B — Contact

Juan Alejo — [juanalejofarana@gmail.com](mailto:juanalejofarana@gmail.com)

GitHub: [juan-alejo/reachrate](https://github.com/juan-alejo/reachrate)
