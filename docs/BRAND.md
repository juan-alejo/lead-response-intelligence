# ReachRate — brand guidelines

> Single source of truth for the product's name, tagline, voice, and
> visual language. Reference this doc whenever you write marketing
> copy, spec a logo, or add a new UI surface.

---

## 1. Name

**ReachRate** — one word, camelCase (R + R capitalized).

| Context | Correct | Wrong |
|---------|---------|-------|
| UI / marketing copy | ReachRate | reachrate, Reach Rate, ReachRATE |
| URLs / paths / package | `reachrate` | `reach-rate`, `reach_rate` |
| Hashtags / social | `#ReachRate` | `#reach_rate` |
| Filename prefixes | `reachrate-config.json` | `ReachRate-Config.Json` |

The only time lowercase is acceptable is in technical identifiers —
domain names, Docker image tags, environment variables, config files.
User-facing text always uses the camelCase wordmark.

### Name rationale

- "Reach" = the act of contacting prospects (reach out to them).
- "Rate" = the measurable outcome (how fast, how often, how completely
  your market replies).
- Two short syllables, easy to type on mobile, pronounceable in both
  Spanish and English without awkward transitions.
- Evokes a dashboard metric — already the product's core artifact.
- Low collision risk in the martech / sales-automation space.

---

## 2. Tagline

### Primary tagline (always paired with the wordmark)

- **ES**: *Medí cómo responde tu mercado.*
- **EN**: *Measure how your market responds.*

Used in: hero section, GitHub repo description, social bios, pitch
decks, one-liners.

### Elevator line (when there's room for one sentence)

- **ES**: *ReachRate mide cada semana cuánto tarda cada negocio de tu
  mercado en contestar mensajes — los más lentos son tus mejores
  prospectos.*
- **EN**: *ReachRate audits how fast every business in your target
  market replies to inbound contact. The slowest are your best
  prospects.*

Used in: README hero, landing-page subtitle, first paragraph of
outreach emails, LinkedIn About section.

### Category descriptor (for listings / directories)

- **ES**: *Herramienta de inteligencia de tiempos de respuesta para
  mercados B2B locales.*
- **EN**: *Response-time intelligence for local B2B markets.*

---

## 3. Voice & tone

### What ReachRate sounds like

- **Data-driven**: we talk in numbers, percentages, concrete
  examples. "The slowest 15% never reply within 48 hours" > "most
  businesses are slow".
- **Confident, not arrogant**: we state facts from the data, not
  opinions. "This is what the pipeline measured" > "we think this is
  best".
- **Spanish-first, English equal**: every user-visible string ships in
  both languages, and the Spanish copy isn't a translation — it's
  idiomatic for an Argentine / LatAm operator. "Buscar ahora" not
  "Correr pipeline".
- **Operator-friendly, not engineer-friendly**: say "cliente potencial"
  not "prospect row", "búsqueda" not "pipeline run", "negocio" not
  "entity".
- **Honest about limits**: when Phase 2 live mode isn't shipped, the
  UI says so. No "coming soon" vaporware.

### What ReachRate doesn't sound like

- ❌ "AI-powered revolutionary game-changing sales platform"
- ❌ "Synergize your outbound funnel with disruptive intelligence"
- ❌ "10x your pipeline with ReachRate"
- ❌ Clickbait superlatives ("The ONLY tool you need...")
- ❌ Techspeak when a plain word works ("prospect", not "targeted entity")

### Example: same message, good vs. bad

> ❌ *Unlock revolutionary AI-powered insights into your B2B funnel
> performance.*

> ✅ *Cada lunes te llega una lista de los 40 negocios de tu mercado
> que más tardaron en contestar. Contactalos primero.*

---

## 4. Color palette

### Primary

| Name | Hex | Use |
|------|-----|-----|
| **Indigo 500** | `#6366f1` | Primary brand color. Logos, primary buttons, chart highlights, metric-card accents. Already embedded in the dashboard CSS. |
| **Sky 500** | `#0ea5e9` | Secondary accent. Gradient partner for Indigo 500 (e.g. the dashboard hero card). |

### Semantic

| Name | Hex | Use |
|------|-----|-----|
| **Green 500** | `#22c55e` | Success, live / active states (`pill-real`). |
| **Amber 400** | `#facc15` | Demo / mock mode (`pill-mock`). |
| **Gray 500** | `#6b7280` | Disabled / off states (`pill-off`). |
| **Red 500** | `#ef4444` | Errors, failed attempts. |

### Neutrals

Default Streamlit neutrals. Don't customize — they adapt to the
operator's OS light/dark preference and breaking that creates
accessibility issues.

### Do not introduce new colors without updating this doc first.

---

## 5. Logo direction (for future designer brief)

We don't ship a logo yet — the dashboard currently uses the 📡
emoji as a placeholder. When commissioning one:

**Wordmark**:
- Font: geometric sans-serif, modern. Candidates: *Inter*, *Satoshi*,
  *DM Sans*.
- Weight: Bold or SemiBold. Never ultralight.
- Letter-spacing: tight; the two "R"s should feel as one word.
- Case: camelCase (the capital R inside the word is a brand feature).

**Icon / mark**:
- Square, works at 16 × 16 favicon all the way to 512 × 512 app tile.
- Simple monogram: stylized "R" with a pulse-line or radar-ping wave
  emitting from it. Indigo (`#6366f1`) on white is the default; white
  on Indigo is the inverted form.
- Avoid complexity: no 3D, no gradients beyond indigo→sky, no
  illustrations.

**Reserve space**: the wordmark should have padding equal to the x-
height of the letters all around. Nothing crowds the logo.

---

## 6. Iconography — emoji conventions

The dashboard leans on emoji as lightweight icons. Keep the set
consistent:

| Concept | Emoji | Meaning |
|---------|-------|---------|
| Product / reach | 📡 | Radar / signal / outreach — ReachRate's signature emoji |
| Home / overview | 🏠 | Landing / home tab |
| Priority list | 🎯 | Where to focus |
| Stats / charts | 📊 | Numerical insight |
| Competitors / tools | 🕵 | Intelligence / detection |
| Raw data | 🗂 | Tables / records |
| Auto-submit (Phase 2) | 🤖 | Automation |
| Settings | ⚙ | Configuration |
| Success | ✅ / ✔ | Completed / OK |
| Warning | ⚠ | Attention |
| Error | ❌ | Failed |
| Money / pricing | 💰 | Commercial |
| AI / Claude | 🧠 / 🤖 | Generator / smarts |
| Argentina | 🇦🇷 | Argentina pack / LatAm focus |
| LatAm | 🌎 | Region multi-country |
| US | 🇺🇸 | US pack |
| Brasil | 🇧🇷 | Brasil pack |
| Speed / live | 🚀 | CTAs / live mode |
| Demo / sandbox | 🧪 | Mock mode |
| Off | ⏸ | Disabled |

Don't invent new emoji per surface — reuse this set.

---

## 7. Usage rules (quick)

- **Always** spell the product name "ReachRate". Never split it,
  never lowercase it in body text.
- **Always** pair the wordmark with its tagline on the first mention
  of any public surface (README, pitch, landing).
- **Never** claim capabilities the product doesn't have today. If
  Phase 2 live mode isn't shipped, don't promise it in present tense.
- **Avoid** the word "platform" unless we actually have multi-tenant
  hosted. Right now it's a "tool" or "pipeline", not a platform.
- **Prefer** "Panel" (es) / "Dashboard" (en) over "interface" or "UI".
- **Avoid** translating the product name. ReachRate stays in English
  regardless of locale — it's the brand.

---

## 8. Changelog

- **v1.0** (2026-04-22) — Brand established. Product renamed from
  "Lead Response Intelligence Pipeline" to "ReachRate". Indigo + Sky
  primary palette confirmed (carried over from the existing dashboard
  CSS). 📡 retained as signature emoji.
