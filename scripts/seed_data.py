# One-off seed script used to generate the initial data/plans.json from
# GloBird invoice 11067803, Energy Made Easy screenshots, and a Finder.com.au
# comparison (all captured 2026-07-18). Kept for provenance/reference only -
# ongoing edits should go through cli/plans.py, not this file.

import json
from datetime import date

household = {
    "supplyAddress": "F 2/5 Woids Ave, Hurstville, NSW 2220",
    "distributor": "Ausgrid",
    "nmi": "41026090458",
    "postcode": "2220",
    "avgDailyUsageKwh": 17.49,
    "billingCycleDays": 28,
    "currentPlanId": "globird-glosave",
    "notes": "Baseline usage taken from GloBird invoice 11067803 (15-Jun-2026 to 12-Jul-2026), which states an average daily usage of 17.49 kWh."
}

plans = []

def add(id, retailer, planName, tariffType, dailyChargeCents, rateLowCents, rateHighCents=None,
        stepThresholdKwhPerDay=None, discountPct=0, source="", sourceDate="", notes="", isCurrent=False):
    plans.append({
        "id": id,
        "retailer": retailer,
        "planName": planName,
        "isCurrent": isCurrent,
        "tariffType": tariffType,  # "block" | "single_rate" | "time_of_use"
        "dailyCharge": round(dailyChargeCents/100, 5),
        "rateLow": round(rateLowCents/100, 5),
        "rateHigh": round((rateHighCents if rateHighCents is not None else rateLowCents)/100, 5),
        "stepThresholdKwhPerDay": stepThresholdKwhPerDay,
        "discountPct": discountPct,
        "source": source,
        "sourceDate": sourceDate,
        "notes": notes
    })

# --- Current plan (from GloBird invoice 11067803) ---
add("globird-glosave", "GloBird Energy", "GLOSAVE", "block",
    95.7, 32.45, 36.3, stepThresholdKwhPerDay=15.0, discountPct=3,
    source="GloBird invoice 11067803", sourceDate="2026-07-13",
    notes="Current plan. Discount = 2% pay-on-time + 1% direct debit, conditional. Daily charge/usage rates shown are from 1-Jul-2026 (most recent).",
    isCurrent=True)

# --- Energy Made Easy screenshots (2026-07-18) ---
add("globird-boost-eme", "GloBird Energy", "BOOST Residential (Flat Rate) - Ausgrid", "block",
    125.40, 29.04, 33.55, stepThresholdKwhPerDay=15.0, discountPct=10.75,
    source="Energy Made Easy screenshot", sourceDate="2026-07-18",
    notes="EME estimated cost $1,860 -> $1,660/yr (1 discount, ~10.75%, exact condition unclear). Step threshold assumed 15kWh/day (same as GLOSAVE) - not confirmed on screenshot, verify against plan fact sheet.")

add("1st-opal-eme", "1st Energy", "1st Opal - Single Rate", "single_rate",
    132.88, 26.40, None, discountPct=3.98,
    source="Energy Made Easy screenshot", sourceDate="2026-07-18",
    notes="EME estimated cost $1,760 -> $1,690/yr (1 discount, ~3.98%). Ongoing benefit period.")

add("sumo-winter-saver-eme", "Sumo", "Sumo Winter Saver", "single_rate",
    91.82, 29.46, None, discountPct=0,
    source="Energy Made Easy screenshot", sourceDate="2026-07-18",
    notes="New-customer-of-Sumo eligibility condition applies. EME estimated cost ~$1,750/yr (exact figure cropped in screenshot), no discount.")

add("nectr-power-perks-eme", "Nectr", "Nectr Power Perks", "single_rate",
    105.59, 33.16, None, discountPct=10,
    source="Energy Made Easy screenshot", sourceDate="2026-07-18",
    notes="EME estimated cost ~$1,980 -> ~$1,780/yr (2 discounts, figures partially cropped in screenshot - treat discount % as approximate).")

add("kogan-free-first-eme", "Kogan Energy", "Kogan Energy with free FIRST", "single_rate",
    98.80, 31.56, None, discountPct=0,
    source="Energy Made Easy screenshot", sourceDate="2026-07-18",
    notes="1 special offer noted (unspecified). EME estimated cost ~$1,880/yr, no ongoing discount applicable.")

add("powershop-power-house-eme", "Powershop", "Power House", "single_rate",
    98.80, 31.56, None, discountPct=0,
    source="Energy Made Easy screenshot", sourceDate="2026-07-18",
    notes="Environmental options plan. EME estimated cost $1,880/yr, no discount.")

add("agl-seniors-saver-eme", "AGL", "Residential Seniors Saver - New To AGL", "single_rate",
    142.91, 28.49, None, discountPct=0,
    source="Energy Made Easy screenshot", sourceDate="2026-07-18",
    notes="Likely requires a Seniors Card / new-to-AGL - confirm eligibility. No estimated cost visible in screenshot (cropped).")

# --- Finder.com.au comparison, postcode 2220, Ausgrid, Time of Use filter (2026-07-18) ---
finder_rows = [
    ("agl-smart-saver-finder", "AGL", "Residential Smart Saver", 158.63, 21.63, 54.18, -10, 2960, "Up to $300 online sign-up credit across electricity & gas plans, varies by state, 90-day rolling offer."),
    ("alinta-homedeal-smart-finder", "Alinta Energy", "HomeDeal Smart", 155.24, 21.15, 52.86, -12, 2120, ""),
    ("1st-quartz-finder", "1st Energy", "1st Quartz", 141.02, 19.14, 48.07, -20, 1920, ""),
    ("1st-opal-finder", "1st Energy", "1st Opal", 141.02, 19.14, 48.07, -20, 1920, ""),
    ("origin-go-variable-finder", "Origin Energy", "Go Variable Ongoing", 159.70, 21.64, 54.12, -10, 2160, ""),
    ("agl-netflix-finder", "AGL", "Residential Netflix Plan", 163.45, 21.63, 54.16, -9, 2180, "Netflix Standard with ads included; can upgrade tier for extra cost."),
    ("origin-everyday-rewards-finder", "Origin Energy", "Everyday Rewards Variable Ongoing", 165.75, 22.59, 56.33, -6, 2260, "Earn Everyday Rewards points, ~5000 points/yr, charged on bill."),
    ("alinta-solarbalance-finder", "Alinta Energy", "SolarBalance Choice", 165.82, 22.59, 56.58, -6, 2260, ""),
    ("origin-basic-finder", "Origin Energy", "Basic", 176.53, 24.04, 60.14, 0, 2400, ""),
    ("agl-solar-savers-finder", "AGL", "Residential Solar Savers", 176.26, 24.04, 60.20, 0, 2400, "Up to $300 sign-up credit across electricity & gas plans."),
    ("1st-standing-offer-finder", "1st Energy", "Standing Offer", 176.41, 24.04, 60.20, 0, 2400, ""),
    ("flipped-freedom-finder", "Flipped Energy", "Freedom Switched On 2.0", 119.90, 14.87, 56.40, -18, 2090, ""),
    ("diamond-standing-finder", "Diamond Energy", "Standing", 176.41, 24.04, 60.20, 0, 2400, ""),
    ("sumo-winter-saver-finder", "Sumo", "Winter Saver", 95.48, 24.32, 44.70, -22, 1930, ""),
    ("sumo-sunrise-plus-tou-finder", "Sumo", "Sunrise Plus Residential TOU", 100.51, 25.07, 46.09, -19, 2000, "$50 (incl. GST) sign-up credit for new residential electricity customers who join within 30 days; applied within 1-3 billing cycles."),
    ("sumo-sunrise-tou-finder", "Sumo", "Sunrise Residential TOU", 100.51, 25.07, 46.13, -19, 2000, ""),
    ("kogan-free-first-finder", "Kogan Energy", "Kogan Energy with free FIRST", 109.19, 22.86, 57.24, -16, 2070, "12 months free FIRST membership for new Kogan Energy customers who sign up + switch to Kogan FIRST."),
    ("powershop-power-house-finder", "Powershop", "Power House", 109.19, 22.86, 57.24, -16, 2070, ""),
    ("kogan-current-first-finder", "Kogan Energy", "Kogan Energy for current FIRST members", 109.19, 22.86, 57.24, -16, 2070, "$100 (incl. GST) sign-up credit for eligible existing FIRST members."),
    ("globird-wholesave-finder", "GloBird Energy", "WHOLESAVE Resi", 121.00, 16.31, 35.73, -15, 1970, "Time of Use meter required."),
    ("ovo-one-plan-finder", "OVO Energy", "The One Plan", 145.01, 21.38, 53.57, -14, 2080, "Interest Rewards - pays interest on credit balances after charges considered."),
    ("globird-boost-finder", "GloBird Energy", "BOOST Residential", 132.00, 23.10, 43.45, -13, 2130, "NOTE: differs from EME-sourced BOOST figures - verify which is current before relying on it."),
    ("engie-nrma-elec-finder", "ENGIE", "NRMA Elec", 176.41, 24.04, 60.19, -12, 2110, "$50 (incl. GST) sign-up credit, one-off, first 12 months, not redeemable for cash."),
    ("sumo-homegrown-tou-finder", "Sumo", "Homegrown Residential TOU", 102.04, 28.01, 51.55, -12, 2200, ""),
    ("engie-nrma-greenpower-finder", "ENGIE", "NRMA GreenPower Elec", 176.41, 24.04, 60.19, -12, 2170, "$50 (incl. GST) sign-up credit, one-off, first 12 months."),
    ("engie-perks-finder", "ENGIE", "Perks Elec", 176.41, 24.04, 60.19, -12, 2170, "$50 (incl. GST) sign-up credit, one-off, first 12 months."),
    ("red-taronga-finder", "Red Energy", "Red Taronga Plan", 100.92, 24.18, 48.24, -11, 2220, "Taronga Family Membership - 1 free child/family pass per year while an Active Pack member; address verification required."),
    ("engie-greenpower-finder", "ENGIE", "GreenPower Elec", 176.41, 24.04, 60.19, -11, 2140, "$50 (incl. GST) sign-up credit, one-off, first 12 months."),
    ("engie-everyday-finder", "ENGIE", "Everyday Elec", 176.41, 24.04, 60.19, -11, 2140, "$50 (incl. GST) sign-up credit, one-off, first 12 months."),
    ("engie-home-business-finder", "ENGIE", "Home Business Everyday Elec", 176.41, 24.04, 60.19, -11, 2140, "$50 (incl. GST) sign-up credit, one-off, first 12 months."),
]

for id_, retailer, plan, daily_c, low_c, high_c, ref_pct, ann_cost, notes in finder_rows:
    add(id_, retailer, plan, "time_of_use", daily_c, low_c, high_c, discountPct=0,
        source="Finder.com.au comparison (postcode 2220, Ausgrid, Time of Use filter)",
        sourceDate="2026-07-18",
        notes=(notes + (" " if notes else "") +
               f"Finder reference-price comparison: {ref_pct}% vs reference. Finder estimated annual cost: ${ann_cost}/yr (Finder's own usage assumption, not this household's).").strip())

data = {
    "meta": {
        "generatedBy": "scripts_build_json.py",
        "lastUpdated": str(date.today()),
        "schemaVersion": 1,
        "notes": [
            "tariffType 'block' = daily-usage-threshold stepped tariff (rateLow up to stepThresholdKwhPerDay, then rateHigh).",
            "tariffType 'single_rate' = one flat usage rate (rateLow == rateHigh).",
            "tariffType 'time_of_use' = rateLow/rateHigh represent off-peak/peak (or similar) rates that vary by time of day, NOT by daily volume. Actual cost depends on the household's peak-vs-off-peak usage split, which is unknown - the calculator applies an adjustable blend (see peakSharePct) as an approximation only.",
            "discountPct is an ONGOING conditional discount (e.g. pay-on-time, direct debit) applied to the subtotal. It is distinct from one-off sign-up credits, which are stored in 'notes' and not applied to the recurring cost calculation.",
            "Finder's own referenceComparisonPct/estimatedAnnualCost figures (folded into notes) reflect FINDER's assumed usage, not this household's - they are informational only, not used in this repo's calculations."
        ]
    },
    "household": household,
    "plans": plans
}

with open("/home/claude/energy-repo/data/plans.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Wrote {len(plans)} plans")
