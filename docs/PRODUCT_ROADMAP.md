# Product roadmap & brand strategy

> Internal planning doc. Written 2026-04-22 to frame the next 6–12
> months of product work toward a goal of: "this is the tool the
> industry uses, not a side-project portfolio piece".

Target buyer (from [SELLING_GUIDE.md](./SELLING_GUIDE.md)): companies
that **sell response-time automation** — chat bot platforms, automated
intake tools, booking widget vendors, lead-gen agencies, AI-for-SMB
consultants. Their pain: finding prospects that *need* their product.
Our value: the cohort of slow-responders, already prioritized.

---

## Part 1 — Naming (decided: **ReachRate**)

The product is named **ReachRate**. Full brand guidelines
(wordmark rules, tagline, voice, palette, emoji conventions) live in
[BRAND.md](./BRAND.md) — reference that doc when writing copy or
commissioning a logo.

### Why ReachRate

After iterating through a first round of options (Pulso, Sabueso,
Latentia, Respondly, ReplyRadar, LeadLag), the final pick landed on a
name that is simultaneously:

- **Descriptive** — "Reach" + "Rate" tells a buyer what the product
  measures the first time they see it. No metaphor to decode.
- **Short & memorable** — two one-syllable words, one compound
  wordmark. Types cleanly on mobile. Rhythmic to say out loud.
- **Positive framing** — names the *value* the tool delivers
  (your reach rate, a measurable outcome), not the *problem* it
  detects (lag / silence / slowness). LeadLag was rejected for this
  exact reason: you don't want "Lag" attached to your product in the
  buyer's mind.
- **Free in the martech space** — no major competitor owns this name
  at time of writing. (Confirm domain + INPI/USPTO before signing
  contracts — that's a 10-minute task Juan should do before the first
  paid invoice.)
- **Works in both languages** — "ReachRate" pronounces comfortably in
  Spanish and English without translation. The tagline handles the
  localization layer.

### Taglines locked in

- **ES**: *Medí cómo responde tu mercado.*
- **EN**: *Measure how your market responds.*

Elevator one-liner — EN: *"ReachRate audits how fast every business in
your target market replies to inbound contact. The slowest are your
best prospects."* · ES: *"ReachRate mide cada semana cuánto tarda cada
negocio de tu mercado en contestar mensajes — los más lentos son tus
mejores prospectos."*

### Pending follow-ups (short, do once when Juan has 30 min)

- **Rename the GitHub repo** `juan-alejo/lead-response-intelligence`
  → `juan-alejo/reachrate` (Settings → Rename). GitHub auto-redirects
  old URLs, so badges keep working.
- **Buy `reachrate.io`** (or `.app` / `.ai` if `.io` is taken) and
  point it at the Railway deploy.
- **Register `@ReachRate` / `@reachrate_io`** on LinkedIn, X, Indie
  Hackers, Product Hunt.
- **USPTO / INPI trademark check** — paid for $80–200 or DIY in the
  public registries in ~30 min.

---

## Part 2 — Strategic roadmap

Prioritized by `(commercial impact) ÷ (time to build)`. The goal is
not to build everything — it's to pick the 3–5 items that move the
needle from "interesting portfolio piece" to "tool the industry
knows about".

### 🔴 Critical for credibility — do next (weeks 1–4)

These close the gap between "demo that looks nice" and "something a
buyer pays for without hesitation".

**1. Public demo instance.** Host the Streamlit app in demo mode at
`demo.pulso.ai` (or similar). One click, no signup, pre-loaded sample
data for AR + US + BR. This is the single highest-leverage move —
right now a prospect has to clone a repo to see the product. Remove
that friction and every cold LinkedIn outreach can link directly to
*"see it working in 30 seconds"*.

**2. A logo + consistent visual identity.** Streamlit defaults are
fine for an MVP but scream "side project". A simple wordmark + color
palette + favicon + social cards gets the product past the sniff
test with enterprise buyers. Commission a designer on Fiverr/99designs
for $200–400, or use Playground AI + clean it up manually.

**3. First case study.** One real client at a real price, with real
numbers: "Client X closed $Y in deals from slow-responders discovered
by Pulso in Z weeks". This is the single biggest trust-builder. Offer
the first engagement at a heavy discount (even free) in exchange for a
case study + testimonial.

**4. Historical trends view.** Right now the dashboard shows a
snapshot. Add a **Tendencias** tab: "dentists in Argentina are 18%
slower to respond this quarter vs last". Time-series line charts per
vertical. This is the kind of insight that goes viral on LinkedIn
when a sales VP screenshots it. Technical cost: 1 week. Commercial
cost of *not* having it: a real weakness in demos.

### 🟠 High-leverage upgrades — next quarter (weeks 5–16)

**5. Prospect enrichment.** Integrate Apollo.io (or Clearbit if
cheaper) for every prospect: employee count, revenue bracket,
funding status, tech stack, decision-maker name + email. A
slow-responding dentist is one thing; a slow-responding dentist who
just took Series A funding and has 40 employees is a *qualified
lead at a very different price*. This is the single biggest boost
to the outreach list's commercial value. Cost: $50–200/mo in API +
2 weeks dev.

**6. Claude-generated outreach drafts.** The Priority list already
shows which business to contact. Next step: Claude drafts the first
message per prospect, using the signals detected — vertical, location,
tool they already use, response time. *"Hi Dr. Smith, noticed your
practice uses Calendly — we help dental offices convert no-show
booking clicks into qualified patients. Your competitor Dr. Jones
answered our test in 14 hours; here's what that cost him last month."*
This is what flips the product from "a list" to "a sales workflow".
Cost: 1 week using the existing Claude plumbing.

**7. CRM export connectors.** One-click export to HubSpot (first) and
Pipedrive (second). Buyers living in their CRM never leave it; if the
priority list has to be manually CSV'd in, usage drops 70% after
week 1. Covered by existing Phase 1 report CSVs — "export to CRM" is
mapping those CSVs to the CRM's API. Cost: 1 week per connector.

**8. Phase 2 live submitter.** Already spec'd in
[PHASE_2_SPEC.md](./PHASE_2_SPEC.md). Ship the custom engagement with
one client, use that as the second case study. Converts the product
from "list of slow responders" to "automated submission + list of
slow responders" — the former is a nice report, the latter is a
response bot competitor's worst fear.

### 🟡 Differentiators — 6-month horizon

**9. Phase 3 — managed SaaS mode.** Stop doing single-tenant
engagements. Bill monthly. Self-serve onboarding. Tiered pricing:
Starter $99/mo (1 location, 3 verticals, up to 50 prospects/week),
Pro $299/mo (unlimited locations/verticals, 500 prospects/week,
enrichment), Agency $799/mo (multi-tenant, white-label). Needs:
Stripe, user auth, multi-tenancy in the DB, billing UI. Cost: 6–8
weeks dev. Commercial impact: multiplies LTV by 20x+ vs one-off
engagements.

**10. "State of response times" annual report.** Aggregate
anonymized data across all clients into an industry report — *"We
measured 10,000 businesses across LatAm; here's which industries
respond fastest"*. Publish on a landing page with social sharing;
email it to every sales VP on LinkedIn. This is pure marketing
leverage *generated by the product itself*. One good report = one
LinkedIn post with 50k views = a month of inbound leads.

**11. API + webhooks.** REST endpoint: `GET /prospects?min_response=24h`.
Outbound webhook: "when a new prospect enters the priority list, POST
here". Developer-facing but unlocks integrations (Zapier, Make.com,
n8n, custom tooling). Cost: 1 week. Moves the product from "a
dashboard" to "a platform".

**12. Multi-tenant team features.** Multiple operators per account,
role-based access, audit log. Agency clients (who resell) demand this.
Needed for the Agency tier in (9).

### 🟢 Differentiators — 12-month horizon

**13. Predictive scoring.** ML model on "given all the signals
(response time, vertical, location, tools, enrichment data), which
prospect is most likely to actually convert to a sale for a response-
automation product?" Needs: a training dataset from real closed deals
(chicken-and-egg — needs first 5+ paying clients for real signal).
Cost: ongoing.

**14. Native Slack + WhatsApp notifications.** Monday report drops
into the operator's Slack channel. WhatsApp message: "12 new slow-
responders this week". Removes the need to open the dashboard; the
report comes to you.

**15. White-label mode.** Agency clients resell the tool as their
own product. Full rebrand: their logo, their colors, their domain,
their pricing. Premium tier differentiator.

---

## Part 3 — Marketing angles

Positioning themes to pick from. The tool is technically the same;
the *story* you tell changes dramatically by audience.

| Audience | Pitch |
|----------|-------|
| **Chat-bot vendors** | "Find the small businesses still answering by hand — that's your buyer." |
| **Intake-automation vendors (law, healthcare)** | "30% of law firms never reply to a contact form. That's your TAM, already qualified." |
| **Lead-gen agencies** | "Deliver pre-qualified lists: 'these 40 businesses haven't returned a single inquiry in the last quarter'." |
| **AI consultants selling to SMBs** | "Find the SMBs whose response time sucks, sell them the Claude agent that fixes it." |
| **In-house sales ops** | "Know which of our prospects are actually operational-tight (fast responders) vs not — route the bad ones to BDR, good ones to AE." |

### Content hooks for inbound marketing

- *"We sent 10,000 test contact-form submissions to businesses in 5
  countries. Here's how long they took to reply."* → LinkedIn gold.
- *"The slowest-responding law firm in Buenos Aires takes 14 days to
  answer an inquiry. Here's the one tool that would fix that."* →
  industry publications.
- *"Why 30% of dental offices never reply to contact form
  submissions"* → dental industry press.
- *"What Google Places tells you about your market that your CRM
  can't"* → DIY marketers on Twitter.

One of these per month + a 2-hour edit = a sustained inbound funnel.

---

## Part 4 — Quality & tech debt

Items that don't land buyers but make the product not embarrassing
to sell. Do in parallel with the above.

- **Playwright fetcher coverage** — Phase 1's `PageFetcher` works
  but has no tests. Add integration tests with a bundled static HTML
  corpus so a browser-version bump doesn't silently break classification.
- **Performance at scale** — tested at ~30 prospects. What happens at
  500? 2000? Load-test and document concrete limits. "Pulso handles
  5,000 prospects/week on a $5 Railway instance" is a sellable sentence.
- **Observability** — structured logging is there; no centralized
  errors/metrics. Wire to Sentry + Grafana Cloud (both have generous
  free tiers). Buyers asking "what happens when it breaks" need an
  answer.
- **Error surfaces in the dashboard** — right now failures inside a
  pipeline run sometimes silent-log to the console. Every failure
  should raise a visible alert in the Run History panel.
- **Docs for integrators** — if we add API/webhooks, we need docs.
  `docs/API_REFERENCE.md`, code samples in Python + JS + curl.
- **Security review** — the dashboard has a password option but no
  rate limiting, no audit log for config changes, secrets sit in
  `.env` unencrypted. Enterprise buyers will ask; be prepared.
- **Recovery stories** — what happens if SQLite is corrupted? If
  Airtable sync fails mid-run? Document + test.

---

## Summary — what to do first

If you have 40 hours of focused time in the next month (naming is done —
ReachRate locked in):

1. **Buy `reachrate.io` + social handles** (@ReachRate on
   LinkedIn / X / IndieHackers). Rename the GitHub repo. ~1h.
2. **Logo / visual identity**. Commission a wordmark + square icon
   from Fiverr (budget $150–300) following the brief in
   [BRAND.md §5](./BRAND.md#5-logo-direction-for-future-designer-brief).
   Integrate as SVG + favicon. 4h.
3. **Public demo site** on Railway at `demo.reachrate.io` with
   pre-loaded AR+US+BR sample data. 6h.
4. **Historical trends tab**. 8h.
5. **One case study** — give the first engagement away or heavily
   discount it in exchange for a signed testimonial + screenshots. 20h
   of delivery + 4h of case-study writeup.

That's the foundation that makes every subsequent feature sellable.

---

## Appendix — things explicitly NOT on the roadmap

For completeness, since it's as important to say "no" as "yes":

- **Mobile native app.** The dashboard is operator-facing, rarely
  used on mobile in practice. Mobile-responsive web is enough.
- **Real-time notifications on every event.** Overkill. Weekly rhythm is the
  product's shape; real-time noise breaks that.
- **Self-hosted installer wizard.** Docker compose is enough. Don't
  maintain Windows/macOS installers.
- **Arbitrary LLM provider support** (OpenAI, Gemini, Mistral).
  Claude is already wired. Multi-LLM is a distraction until a
  meaningful number of buyers ask for it.
- **Multi-language prospect sites beyond English/Spanish/Portuguese.**
  French / German / Italian form classification is off-pattern.
  Quote separately per language if asked.
