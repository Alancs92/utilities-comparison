# Power Plan Tracker

A small self-contained tool for tracking electricity plan rates for one household (on the Ausgrid network, NSW postcode 2220) and figuring out which plan is actually cheapest given real usage — not the generic annual estimate a comparison site shows.

## Why this exists

Comparison sites (Energy Made Easy, Finder, retailer sites) each show slightly different numbers because they assume different annual usage. This repo keeps the *raw rates* (supply charge, usage rate(s), discounts) in one place, and computes cost against **this household's actual usage** every time, so the ranking is trustworthy and easy to re-run whenever new quotes come in.

## Structure

```
data/
  plans.json        <- source of truth. All plan rates, household baseline usage.
cli/
  plans.py          <- CLI to list/add/update/remove plans and recompute rankings
web/
  index.html        <- interactive comparator (open directly in a browser, no server needed)
scripts/
  seed_data.py      <- one-off script that generated the initial plans.json (reference only)
CLAUDE.md           <- conventions for an agent maintaining this repo
```

`web/index.html` embeds a copy of `data/plans.json` between two markers:

```html
// __PLANS_DATA_START__
const PLANS_DATA = { ... };
// __PLANS_DATA_END__
```

Whenever `data/plans.json` changes, run `cli/plans.py export-html` to re-embed it — the HTML file works standalone (no fetch/CORS issues when opened as a local file) but only reflects the JSON as of the last export.

## Quick start

```bash
# See every tracked plan ranked by cost at the household's baseline usage
python3 cli/plans.py list

# Same, but only block-tariff plans, sorted by name
python3 cli/plans.py list --type block --sort name

# Full cost ranking as JSON (for scripting)
python3 cli/plans.py calc --json

# Try a different usage assumption without touching the stored baseline
python3 cli/plans.py calc --usage 20 --days 30

# Inspect one plan's raw data + calculated cost
python3 cli/plans.py show globird-glosave

# Add a plan you were just quoted (including one-off move fees, if known)
python3 cli/plans.py add \
  --id example-retailer-plan \
  --retailer "Example Retailer" \
  --plan-name "Example Plan Name" \
  --tariff-type single_rate \
  --daily-charge-cents 100.0 \
  --rate-low-cents 30.0 \
  --connection-fee-cents 12356 --disconnection-fee-cents 12356 \
  --source "Retailer website" --source-date 2026-07-20 \
  --notes "Any eligibility conditions or sign-up credits go here"

# Update a field on an existing plan (only pass the flags that change)
python3 cli/plans.py update globird-glosave --daily-charge-cents 96.0

# Remove a plan that's no longer relevant
python3 cli/plans.py remove some-old-plan-id

# Update the household's baseline usage (e.g. after a new bill)
python3 cli/plans.py set-household --avg-daily-usage-kwh 18.2 --billing-cycle-days 28

# Re-embed data/plans.json into web/index.html after any change above
python3 cli/plans.py export-html
```

Then just open `web/index.html` in a browser.

## Data model (`data/plans.json`)

Each plan has:

| Field | Meaning |
|---|---|
| `id` | Unique slug, used everywhere as the reference key |
| `retailer`, `planName` | Display name |
| `tariffType` | `block` \| `single_rate` \| `time_of_use` — see below |
| `dailyCharge` | Daily supply charge, in dollars/day |
| `rateLow`, `rateHigh` | Usage rate(s), in dollars/kWh. For `single_rate`, `rateHigh` is unused. |
| `stepThresholdKwhPerDay` | Only for `block` tariffs — the daily kWh allowance billed at `rateLow` before `rateHigh` kicks in |
| `discountPct` | An **ongoing conditional** discount (e.g. pay-on-time, direct debit) applied to the subtotal. One-off sign-up credits are NOT included here — put them in `notes` |
| `source`, `sourceDate` | Where the numbers came from and when, so stale data is easy to spot |
| `notes` | Eligibility conditions, sign-up credits, caveats, anything that doesn't fit a field |
| `isCurrent` | Marks the household's current plan |
| `fees` | Optional. `{connectionFee, disconnectionFee}` in dollars — one-off move-in/move-out fees. **Only relevant if physically relocating address**, not on a same-address retailer switch (which is what this tool is normally used for). Excluded from cost calculations unless explicitly included (see below). |
| `ineligible` | Optional `true` when the household structurally can't take this plan (e.g. it requires a solar+battery system, membership, or homeownership the household doesn't have). Such plans are **hidden by default** from `list`/`calc` and the web tool — like `requiresSmartMeter`, but for reasons other than metering. Set with `cli/plans.py add/update --ineligible-reason "..."`; clear with `--eligible`. Show them anyway with `--include-ineligible` (CLI) or the "Show ineligible" toggle (web). |
| `ineligibleReason` | Human-readable reason recorded alongside `ineligible: true`. |

### Tariff types

- **`block`** — a daily-usage threshold tariff (e.g. first 15 kWh/day at one rate, the rest at a higher rate). This is what the household's current GLOSAVE plan uses.
- **`single_rate`** — one flat usage rate, no tiers.
- **`time_of_use`** — the rate depends on *when* energy is used (peak/off-peak/shoulder), not how much is used per day. `rateLow`/`rateHigh` are treated as off-peak/peak. Since this household's actual peak-vs-off-peak split isn't tracked yet, the calculator applies an adjustable "peak share %" blend as an approximation — **this ranking is less trustworthy than `block`/`single_rate` until real TOU usage data is added.**

## Known caveats in the current data

- The household does **not** have a smart meter, so all `time_of_use` plans are flagged `requiresSmartMeter: true` and excluded by default from `list`/`calc` and from the web tool (toggle "Show TOU plans" in the UI, or pass `--include-ineligible` on the CLI, to see them anyway).
- Several `block`-tariff plans assume a 15 kWh/day threshold copied from the household's current GLOSAVE plan — this hasn't been individually confirmed against each plan's fact sheet.
- A couple of `discountPct` values (1st Opal, Nectr Power Perks) were back-calculated from partially cropped screenshots — treat as approximate.
- GloBird "BOOST Residential" appears twice with different rates — once sourced from Energy Made Easy (`block` type) and once from Finder.com.au (`time_of_use` type, and therefore not accessible without a smart meter anyway). These may be different plan variants, or a rate change between capture dates.
- Finder-sourced `estimatedAnnualCost`/`referenceComparisonPct` figures (folded into `notes`) reflect *Finder's* assumed usage, not this household's — they're informational only, not used in any calculation here.

## For an agent picking this repo up

See `CLAUDE.md` in the repo root for conventions and things to know before adding data or changing the calculator.
