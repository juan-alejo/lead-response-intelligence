# Example pipeline outputs

These files were produced by running the pipeline end-to-end against the
mock fixtures in [`../data/fixtures`](../data/fixtures):

```bash
python -m src.cli run-weekly --all-verticals --borough manhattan
```

- [`reports/outreach_priority.csv`](./reports/outreach_priority.csv) —
  submissions sorted by slowest response. Never-responders float to the top;
  sub-2-minute responders are filtered out (they're already operationally
  tight, so pitching them isn't worth the sales team's time).
- [`reports/vertical_stats.csv`](./reports/vertical_stats.csv) —
  per-vertical avg response time + percent-within-24h + percent-never-
  responded. This is the slide that goes to the VP of sales.
- [`reports/competitor_distribution.csv`](./reports/competitor_distribution.csv) —
  which chat / booking tools each vertical runs. Useful for targeting
  ("every med spa in our dataset uses Calendly or Acuity").

## How matching works in the demo

The mock response fixtures impersonate each prospect's published phone /
email. The `ResponseMatcher` normalizes the phone numbers (stripping
formatting) and does case-insensitive email lookups, so a response from
`intake@sutter-law.example.com` or from `+12125550101` correctly attributes
to the corresponding submission regardless of casing or punctuation.
