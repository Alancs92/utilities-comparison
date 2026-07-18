# Agent notes for this repo

This is a household electricity-plan tracker. If you're picking this up fresh, read `README.md` first — this file is conventions and gotchas specifically for an agent extending or maintaining it.

## The one rule that matters most

**`data/plans.json` is the source of truth. `web/index.html` is a generated artifact.**

Never hand-edit the `PLANS_DATA` block inside `web/index.html`. Always edit `data/plans.json` (directly, or via `cli/plans.py`), then run:

```bash
python3 cli/plans.py export-html
```

If you find yourself editing JSON inside a `<script>` tag, stop — that's a sign you're editing the wrong file.

## Adding new plan quotes

When the user pastes a new screenshot, invoice, or comparison-site result:

1. Figure out the `tariffType` first — this determines which fields matter:
   - Two rates with no time reference, described as a threshold/step ("first X kWh") → `block`.
   - One rate, no range → `single_rate`.
   - A rate range explicitly labelled "Time of Use", "Peak/Off-Peak", or filtered as such on the source site → `time_of_use`.
   - If genuinely ambiguous, ask rather than guess — the three types are calculated differently and a wrong guess silently produces a wrong ranking.
2. Use `cli/plans.py add` rather than editing the JSON by hand — it enforces the required fields and keeps formatting consistent.
3. Always fill `source` and `sourceDate`. Rates go stale; without provenance, nobody can tell what's current.
4. Put one-off sign-up credits, membership requirements, "new customers only" conditions, etc. in `notes` as plain text — do NOT fold them into `discountPct`. `discountPct` is reserved for genuine ongoing conditional discounts (pay-on-time, direct debit) that reduce every bill, not one-time credits.
5. If a plan already exists under a different source with different rates (this has happened — see README's "Known caveats"), don't silently overwrite it. Add it as a separate entry with a distinct `id` (e.g. `-eme`, `-finder` suffixes) so both are visible, and note the discrepancy in `notes`.
6. Run `python3 cli/plans.py export-html` after any change so the HTML stays in sync. Consider this step mandatory, not optional — a stale HTML file showing old rates is worse than no HTML file.

## Extending the calculator

`calcCost()` is implemented twice — once in `cli/plans.py` (Python) and once in `web/index.html` (JS) — and they must stay behaviourally identical. If you change the cost formula (e.g. to add a real time-of-use schedule instead of the peak-share approximation, or to model solar feed-in credits), change both, and sanity-check they agree:

```bash
python3 cli/plans.py show globird-glosave   # check calculatedAtHouseholdBaseline
# then compare against the same plan's row in web/index.html at the same usage/days
```

A good next improvement, if the household starts tracking actual time-of-use data (e.g. from a smart meter export), would be to replace the flat "peak share %" slider with real peak/off-peak/shoulder kWh splits per plan — the data model already separates `rateLow`/`rateHigh` in a way that supports this without a schema change, you'd just add real peak-hour definitions and a usage-by-hour input.

## Style/format conventions already in use

- Money fields in `plans.json` are stored in **dollars**, not cents (the CLI's `add`/`update` flags take cents as input for convenience when transcribing from c/day, c/kWh sources, and convert on the way in).
- Plan `id`s are lowercase-kebab-case, roughly `<retailer>-<plan-slug>[-<source>]`.
- The dark/teal/amber visual theme in `web/index.html` was a deliberate choice to avoid the generic "cream + terracotta" or "black + acid green" look AI-generated tools tend to default to — keep it if you're extending the UI rather than reverting to a default Bootstrap/Tailwind look.
- No build step, no dependencies beyond Python 3's standard library. Keep it that way unless there's a strong reason not to — the whole point is that this stays a zip-and-go tool.
