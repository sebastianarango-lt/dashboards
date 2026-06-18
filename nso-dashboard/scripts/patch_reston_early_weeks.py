"""
patch_reston_early_weeks.py

For Reston (VA-001):
  1. Replaces weeks 0-29 with frozen data from reston_static_weeks.json
  2. For weeks 30+ (date_start >= 2026-06-08), assigns sequential week numbers
     and keeps Snowflake/API data from build_all_scorecards.py
  3. Recalculates cumulative total_leads from new_leads across all weeks
  4. Calibrates IG Week 0 so cumulative total = current_followers

Reston weeks are sequential (no pause weeks).
"""
import json
import calendar as cal_mod
from datetime import date, timedelta
from pathlib import Path

ROOT           = Path(__file__).parent.parent
SCORECARD_FILE = ROOT / "nso_scorecard_data.json"
STATIC_FILE    = ROOT / "reston_static_weeks.json"
RESTON_CODE    = "VA-001"
WEEK1_START    = date(2025, 11, 17)   # Reston Week 1 Monday
STATIC_CUTOFF  = "2026-06-07"         # date_end of last static week (W29)


def cal_wk_to_reston_wk(cal_wk):
    """Reston weeks are sequential — no pause weeks."""
    return max(0, cal_wk)


def date_to_cal_wk(date_start_str):
    """Return the sequential calendar week number for a given Monday date string."""
    if not date_start_str:
        return 0
    ds = date.fromisoformat(date_start_str)
    delta = (ds - WEEK1_START).days
    if delta < 0:
        return 0
    return delta // 7 + 1


# ── Load static weeks (W0-W34) ─────────────────────────────────────────────────
print("Loading reston_static_weeks.json ...")
with open(STATIC_FILE) as f:
    static_weeks = json.load(f)
print(f"  {len(static_weeks)} static weeks (W0-W29)")

# ── Load current scorecard ──────────────────────────────────────────────────────
with open(SCORECARD_FILE) as f:
    sc = json.load(f)

reston = next((s for s in sc["studios"] if s["code"] == RESTON_CODE), None)
if not reston:
    print("ERROR: Reston not found in scorecard")
    raise SystemExit(1)

# ── Extract dynamic weeks (W30+) from build_all_scorecards.py output ──────────
dynamic_weeks = [
    wk for wk in reston["weeks"]
    if wk.get("date_start") and wk.get("date_start") > STATIC_CUTOFF
]
print(f"\nDynamic weeks (W30+): {len(dynamic_weeks)}")

# ── Relabel dynamic weeks with correct sequential Reston week numbers ──────────
today_str = date.today().isoformat()
new_current = 29  # last confirmed static week

for wk in dynamic_weeks:
    cal_wk = date_to_cal_wk(wk.get("date_start"))
    reston_wk = cal_wk_to_reston_wk(cal_wk)
    old_label = wk.get("week", "")
    wk["week"] = f"WEEK {reston_wk}"
    ds = wk.get("date_start", "")
    if ds and ds <= today_str:
        new_current = reston_wk
    print(f"  {old_label:10s} -> WEEK {reston_wk}  ({wk.get('date_start')} - {wk.get('date_end')})")

# ── Combine static + dynamic ──────────────────────────────────────────────────
all_weeks = static_weeks + dynamic_weeks

# ── Recalculate cumulative total_leads from new_leads ─────────────────────────
print("\nRecalculating cumulative total_leads...")
cum = 0.0
for wk in all_weeks:
    nl = wk.get("new_leads") or 0
    cum += nl
    if cum > 0:
        wk["total_leads"] = cum
print(f"  Final cumulative leads: {cum}")

# ── Update Reston studio entry ────────────────────────────────────────────────
reston["weeks"]        = all_weeks
reston["current_week"] = new_current
reston["co_week"]      = 12   # W12 contains 2026-02-02 (C/O date)
print(f"\ncurrent_week set to {new_current}")

# Ensure founders rate is visible in the RMR breakdown
if reston.get("pricing") is not None:
    reston["pricing"]["tier0_price"] = 99

# ── IG gap → Week 0 ───────────────────────────────────────────────────────────
print("\nCalibrating IG Week 0 so cumulative = current_followers...")
try:
    with open(ROOT / "social_insights.json") as f:
        social = json.load(f)
    cf = next(
        (ig.get("current_followers") for ig in social.get("instagram", [])
         if ig.get("code") == "reston"),
        None,
    )
    if cf is not None:
        cf = int(cf)
        w0 = next((w for w in all_weeks if w.get("week") == "Week 0"), None)
        sum_rest = sum(
            (w.get("ig_new_followers") or 0)
            for w in all_weeks if w.get("week") != "Week 0"
        )
        w0_val = max(0, cf - sum_rest)
        if w0 is not None:
            old_ig = w0.get("ig_new_followers")
            w0["ig_new_followers"] = w0_val if w0_val > 0 else None
            print(f"  Week 0 ig: {old_ig} -> {w0['ig_new_followers']}  "
                  f"(current={cf}, rest={sum_rest})")
    else:
        print("  reston not found in social_insights.json, skipping")
except FileNotFoundError:
    print("  social_insights.json not found, skipping IG calibration")

# ── Write back ────────────────────────────────────────────────────────────────
with open(SCORECARD_FILE, "w") as f:
    json.dump(sc, f, indent=2)

print("\nDone. W0-W29 frozen from static file. W30+ from Snowflake with sequential week numbering.")
