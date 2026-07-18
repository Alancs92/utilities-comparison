#!/usr/bin/env python3
"""
plans.py - CLI for maintaining data/plans.json (the electricity plan tracker).

Designed to be easy for a human OR an agent (e.g. Claude Code) to drive:
every command accepts plain flags, prints plain text or --json, and never
requires interactive input.

Usage:
    python3 cli/plans.py list [--sort cost|name|retailer] [--type block|single_rate|time_of_use]
    python3 cli/plans.py show <plan-id>
    python3 cli/plans.py calc [--usage 17.49] [--days 28] [--peak-share 50] [--json]
    python3 cli/plans.py add --id ID --retailer R --plan-name NAME --tariff-type TYPE
                              --daily-charge-cents C --rate-low-cents L [--rate-high-cents H]
                              [--step-threshold-kwh-per-day T] [--discount-pct D]
                              [--source S] [--source-date YYYY-MM-DD] [--notes N] [--current]
    python3 cli/plans.py update <plan-id> [--field value ...]   # same flags as add, only given ones change
    python3 cli/plans.py remove <plan-id>
    python3 cli/plans.py set-household [--avg-daily-usage-kwh U] [--billing-cycle-days D] [--current-plan-id ID]
    python3 cli/plans.py export-html   # regenerate the embedded dataset in web/index.html from data/plans.json

All costs are calculated in the household's local currency, GST-inclusive,
matching whatever the source rates were quoted in.
"""
import argparse
import json
import os
import re
import sys
from datetime import date

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "data", "plans.json")
HTML_PATH = os.path.join(REPO_ROOT, "web", "index.html")


def load():
    with open(DATA_PATH) as f:
        return json.load(f)


def save(data):
    data["meta"]["lastUpdated"] = str(date.today())
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def calc_plan_cost(plan, daily_usage, days, peak_share_pct):
    """Returns cost in dollars for `days` days at `daily_usage` kWh/day.
    - block: rateLow up to stepThresholdKwhPerDay*days, rateHigh above.
    - single_rate: rateLow applied to all usage (rateHigh ignored).
    - time_of_use: blended using peak_share_pct of usage at rateHigh (peak),
      the rest at rateLow (off-peak). This is an approximation - true TOU
      cost depends on when energy is actually used, which we don't track.
    """
    total_kwh = daily_usage * days
    supply_cost = days * plan["dailyCharge"]
    tariff = plan["tariffType"]

    if tariff == "block":
        threshold = plan.get("stepThresholdKwhPerDay") or 0
        cap = threshold * days
        low_kwh = min(total_kwh, cap)
        high_kwh = max(0, total_kwh - cap)
        usage_cost = low_kwh * plan["rateLow"] + high_kwh * plan["rateHigh"]
    elif tariff == "single_rate":
        usage_cost = total_kwh * plan["rateLow"]
    elif tariff == "time_of_use":
        peak_frac = max(0, min(100, peak_share_pct)) / 100
        peak_kwh = total_kwh * peak_frac
        offpeak_kwh = total_kwh * (1 - peak_frac)
        usage_cost = offpeak_kwh * plan["rateLow"] + peak_kwh * plan["rateHigh"]
    else:
        raise ValueError(f"Unknown tariffType: {tariff}")

    subtotal = supply_cost + usage_cost
    discount = subtotal * (plan.get("discountPct", 0) / 100)
    total = subtotal - discount
    return {
        "totalKwh": round(total_kwh, 2),
        "supplyCost": round(supply_cost, 2),
        "usageCost": round(usage_cost, 2),
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "total": round(total, 2),
    }


def cmd_list(args, data):
    plans = data["plans"]
    if args.type:
        plans = [p for p in plans if p["tariffType"] == args.type]
    if not args.include_ineligible:
        household = data["household"]
        if not household.get("hasSmartMeter", True):
            plans = [p for p in plans if not p.get("requiresSmartMeter")]

    household = data["household"]
    usage = args.usage or household["avgDailyUsageKwh"]
    days = args.days or household["billingCycleDays"]

    rows = []
    for p in plans:
        c = calc_plan_cost(p, usage, days, args.peak_share)
        rows.append((p, c))

    if args.sort == "cost":
        rows.sort(key=lambda r: r[1]["total"])
    elif args.sort == "retailer":
        rows.sort(key=lambda r: r[0]["retailer"])
    else:
        rows.sort(key=lambda r: r[0]["planName"])

    if args.json:
        print(json.dumps([{**p, "calculated": c} for p, c in rows], indent=2))
        return

    print(f"{'ID':32s} {'Retailer':18s} {'Plan':32s} {'Type':12s} {'/cycle':>10s} {'/yr':>10s}")
    for p, c in rows:
        marker = " *" if p.get("isCurrent") else ""
        yr = c["total"] / days * 365
        print(f"{p['id']:32s} {p['retailer']:18s} {p['planName'][:32]:32s} {p['tariffType']:12s} "
              f"${c['total']:>8.2f} ${yr:>8.0f}{marker}")
    print(f"\n(* = current plan)  usage={usage} kWh/day  days={days}  peak-share={args.peak_share}% "
          f"(only affects time_of_use plans)")


def cmd_show(args, data):
    plan = next((p for p in data["plans"] if p["id"] == args.plan_id), None)
    if not plan:
        print(f"No plan with id '{args.plan_id}'", file=sys.stderr)
        sys.exit(1)
    household = data["household"]
    c = calc_plan_cost(plan, household["avgDailyUsageKwh"], household["billingCycleDays"], 50)
    print(json.dumps({**plan, "calculatedAtHouseholdBaseline": c}, indent=2))


def cmd_calc(args, data):
    household = data["household"]
    usage = args.usage or household["avgDailyUsageKwh"]
    days = args.days or household["billingCycleDays"]
    plans = data["plans"]
    if not args.include_ineligible and not household.get("hasSmartMeter", True):
        plans = [p for p in plans if not p.get("requiresSmartMeter")]
    results = []
    for p in plans:
        c = calc_plan_cost(p, usage, days, args.peak_share)
        results.append({"id": p["id"], "retailer": p["retailer"], "planName": p["planName"],
                         "tariffType": p["tariffType"], "isCurrent": p.get("isCurrent", False), **c})
    results.sort(key=lambda r: r["total"])
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Usage: {usage} kWh/day x {days} days   |   peak-share (TOU only): {args.peak_share}%\n")
        for r in results:
            marker = " *current" if r["isCurrent"] else ""
            print(f"{r['total']:>8.2f}  {r['retailer']:18s} {r['planName']:35s} [{r['tariffType']}]{marker}")


def _plan_from_args(args, existing=None):
    plan = dict(existing) if existing else {}
    mapping = {
        "retailer": args.retailer, "plan_name": args.plan_name, "tariff_type": args.tariff_type,
        "daily_charge_cents": args.daily_charge_cents, "rate_low_cents": args.rate_low_cents,
        "rate_high_cents": args.rate_high_cents, "step_threshold_kwh_per_day": args.step_threshold_kwh_per_day,
        "discount_pct": args.discount_pct, "source": args.source, "source_date": args.source_date,
        "notes": args.notes,
    }
    if mapping["retailer"] is not None: plan["retailer"] = args.retailer
    if mapping["plan_name"] is not None: plan["planName"] = args.plan_name
    if mapping["tariff_type"] is not None: plan["tariffType"] = args.tariff_type
    if mapping["daily_charge_cents"] is not None: plan["dailyCharge"] = round(args.daily_charge_cents / 100, 5)
    if mapping["rate_low_cents"] is not None: plan["rateLow"] = round(args.rate_low_cents / 100, 5)
    if mapping["rate_high_cents"] is not None:
        plan["rateHigh"] = round(args.rate_high_cents / 100, 5)
    elif "rateHigh" not in plan and "rateLow" in plan:
        plan["rateHigh"] = plan["rateLow"]
    if mapping["step_threshold_kwh_per_day"] is not None: plan["stepThresholdKwhPerDay"] = args.step_threshold_kwh_per_day
    if mapping["discount_pct"] is not None: plan["discountPct"] = args.discount_pct
    if mapping["source"] is not None: plan["source"] = args.source
    if mapping["source_date"] is not None: plan["sourceDate"] = args.source_date
    if mapping["notes"] is not None: plan["notes"] = args.notes
    if args.current: plan["isCurrent"] = True
    plan.setdefault("discountPct", 0)
    plan.setdefault("stepThresholdKwhPerDay", None)
    plan.setdefault("notes", "")
    return plan


def cmd_add(args, data):
    if any(p["id"] == args.id for p in data["plans"]):
        print(f"Plan id '{args.id}' already exists - use 'update' instead.", file=sys.stderr)
        sys.exit(1)
    required = [args.retailer, args.plan_name, args.tariff_type, args.daily_charge_cents, args.rate_low_cents]
    if any(v is None for v in required):
        print("add requires --retailer --plan-name --tariff-type --daily-charge-cents --rate-low-cents", file=sys.stderr)
        sys.exit(1)
    plan = {"id": args.id}
    plan.update(_plan_from_args(args))
    if args.current:
        for p in data["plans"]:
            p["isCurrent"] = False
        data["household"]["currentPlanId"] = args.id
    data["plans"].append(plan)
    save(data)
    print(f"Added '{args.id}'.")


def cmd_update(args, data):
    idx = next((i for i, p in enumerate(data["plans"]) if p["id"] == args.plan_id), None)
    if idx is None:
        print(f"No plan with id '{args.plan_id}'", file=sys.stderr)
        sys.exit(1)
    updated = _plan_from_args(args, existing=data["plans"][idx])
    updated["id"] = args.plan_id
    data["plans"][idx] = updated
    if args.current:
        for p in data["plans"]:
            p["isCurrent"] = (p["id"] == args.plan_id)
        data["household"]["currentPlanId"] = args.plan_id
    save(data)
    print(f"Updated '{args.plan_id}'.")


def cmd_remove(args, data):
    before = len(data["plans"])
    data["plans"] = [p for p in data["plans"] if p["id"] != args.plan_id]
    if len(data["plans"]) == before:
        print(f"No plan with id '{args.plan_id}'", file=sys.stderr)
        sys.exit(1)
    save(data)
    print(f"Removed '{args.plan_id}'.")


def cmd_set_household(args, data):
    if args.avg_daily_usage_kwh is not None:
        data["household"]["avgDailyUsageKwh"] = args.avg_daily_usage_kwh
    if args.billing_cycle_days is not None:
        data["household"]["billingCycleDays"] = args.billing_cycle_days
    if args.current_plan_id is not None:
        data["household"]["currentPlanId"] = args.current_plan_id
        for p in data["plans"]:
            p["isCurrent"] = (p["id"] == args.current_plan_id)
    save(data)
    print("Household settings updated.")
    print(json.dumps(data["household"], indent=2))


def cmd_export_html(args, data):
    with open(HTML_PATH) as f:
        html = f.read()
    payload = json.dumps(data, indent=2)
    marker_start = "// __PLANS_DATA_START__"
    marker_end = "// __PLANS_DATA_END__"
    pattern = re.compile(re.escape(marker_start) + r".*?" + re.escape(marker_end), re.DOTALL)
    replacement = f"{marker_start}\nconst PLANS_DATA = {payload};\n{marker_end}"
    if not pattern.search(html):
        print("Could not find data markers in web/index.html - is the file intact?", file=sys.stderr)
        sys.exit(1)
    html = pattern.sub(replacement, html)
    with open(HTML_PATH, "w") as f:
        f.write(html)
    print(f"Synced {len(data['plans'])} plans into {HTML_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Manage the household electricity plan tracker.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List all plans with computed cost")
    p_list.add_argument("--sort", choices=["cost", "name", "retailer"], default="cost")
    p_list.add_argument("--type", choices=["block", "single_rate", "time_of_use"])
    p_list.add_argument("--usage", type=float, help="Override daily usage kWh/day")
    p_list.add_argument("--days", type=int, help="Override billing cycle length")
    p_list.add_argument("--peak-share", type=float, default=50, help="TOU: %% of usage assumed at peak rate")
    p_list.add_argument("--include-ineligible", action="store_true", help="Also show plans the household can't access (e.g. TOU plans without a smart meter)")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show one plan's raw data + calculated cost")
    p_show.add_argument("plan_id")
    p_show.set_defaults(func=cmd_show)

    p_calc = sub.add_parser("calc", help="Rank all plans by cost at a given usage")
    p_calc.add_argument("--usage", type=float)
    p_calc.add_argument("--days", type=int)
    p_calc.add_argument("--peak-share", type=float, default=50)
    p_calc.add_argument("--include-ineligible", action="store_true", help="Also show plans the household can't access (e.g. TOU plans without a smart meter)")
    p_calc.add_argument("--json", action="store_true")
    p_calc.set_defaults(func=cmd_calc)

    def add_plan_fields(sp):
        sp.add_argument("--retailer")
        sp.add_argument("--plan-name")
        sp.add_argument("--tariff-type", choices=["block", "single_rate", "time_of_use"])
        sp.add_argument("--daily-charge-cents", type=float)
        sp.add_argument("--rate-low-cents", type=float)
        sp.add_argument("--rate-high-cents", type=float)
        sp.add_argument("--step-threshold-kwh-per-day", type=float)
        sp.add_argument("--discount-pct", type=float)
        sp.add_argument("--source")
        sp.add_argument("--source-date")
        sp.add_argument("--notes")
        sp.add_argument("--current", action="store_true", help="Mark this as the household's current plan")

    p_add = sub.add_parser("add", help="Add a new plan")
    p_add.add_argument("--id", required=True)
    add_plan_fields(p_add)
    p_add.set_defaults(func=cmd_add)

    p_update = sub.add_parser("update", help="Update fields on an existing plan")
    p_update.add_argument("plan_id")
    add_plan_fields(p_update)
    p_update.set_defaults(func=cmd_update)

    p_remove = sub.add_parser("remove", help="Remove a plan")
    p_remove.add_argument("plan_id")
    p_remove.set_defaults(func=cmd_remove)

    p_household = sub.add_parser("set-household", help="Update household baseline usage/settings")
    p_household.add_argument("--avg-daily-usage-kwh", type=float)
    p_household.add_argument("--billing-cycle-days", type=int)
    p_household.add_argument("--current-plan-id")
    p_household.set_defaults(func=cmd_set_household)

    p_export = sub.add_parser("export-html", help="Sync data/plans.json into web/index.html")
    p_export.set_defaults(func=cmd_export_html)

    args = parser.parse_args()
    data = load()
    args.func(args, data)


if __name__ == "__main__":
    main()
