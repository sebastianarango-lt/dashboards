"""
build_spend_data.py — generate spend-data.json

Combines Meta Ads and Google Ads studio-level spend into a single file:

  spend-data.json
  ├── daily   — one row per (date, studio_code) for ALL of 2026
  │             Jan–Mar 2026: monthly totals distributed evenly across days
  │             Apr 2026+:    actual daily API data
  └── monthly — one row per (month, studio_code) for everything before 2026

Run after fetch_meta_ads.py and fetch_google_ads.py have written their files.
"""

import json
import calendar
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT       = Path(__file__).resolve().parent
META_BAKED_PATH = REPO_ROOT / "meta-ads-baked.json"
META_LIVE_PATH  = REPO_ROOT / "meta-ads-data.json"
GOOGLE_PATH     = REPO_ROOT / "google-ads-data.json"
STUDIOS_PATH    = REPO_ROOT / "studios.json"
OUT_PATH        = REPO_ROOT / "spend-data.json"

DAILY_START_YEAR = 2026   # all of this year is represented as daily rows


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  Warning: could not read {path.name}: {e}")
        return {}


def days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def distribute_monthly_to_days(month_str, spend, studio_code):
    """Yield one daily row per day in the month with spend / n_days."""
    year, mo = int(month_str[:4]), int(month_str[5:7])
    n = days_in_month(year, mo)
    daily = round(spend / n, 4) if n else 0
    for day in range(1, n + 1):
        yield {
            "date":        f"{year:04d}-{mo:02d}-{day:02d}",
            "studio_code": studio_code,
            "daily":       daily,
        }


def run():
    print("Loading source files...")
    studios_raw  = json.loads(STUDIOS_PATH.read_text(encoding="utf-8"))
    meta_baked   = load_json(META_BAKED_PATH)
    meta_live    = load_json(META_LIVE_PATH)
    google_raw   = load_json(GOOGLE_PATH)

    # ── Build nametocode lookup from studios.json ─────────────────────
    studios_list = studios_raw.get("studios", studios_raw) if isinstance(studios_raw, dict) else studios_raw
    name_to_code = {}
    for s in studios_list:
        if s.get("name") and s.get("code"):
            name_to_code[s["name"]] = s["code"]

    # ── 1. Collect Meta monthly rows (baked Jan 2025–Mar 2026) ───────
    # Key: (month[:7], studio_code) to spend
    meta_monthly: dict[tuple, float] = {}
    for r in meta_baked.get("studio_monthly", []):
        k = (r["month"][:7], r["studio_code"])
        meta_monthly[k] = meta_monthly.get(k, 0) + (r.get("spend") or 0)

    # Also pull any computed monthly rows from meta-ads-data.json
    # (Apr 2026+ months that fell outside the daily window)
    for r in meta_live.get("studio_monthly", []):
        mo = r.get("month", "")[:7]
        if mo < str(DAILY_START_YEAR):  # only pre-2026 for monthly output
            k = (mo, r["studio_code"])
            meta_monthly[k] = meta_monthly.get(k, 0) + (r.get("spend") or 0)

    # ── 2. Collect Meta daily rows (Apr 2026+) ───────────────────────
    meta_daily: dict[tuple, float] = {}
    for r in meta_live.get("studio_daily", []):
        d = r.get("date", "")
        if d[:4] == str(DAILY_START_YEAR) and d >= f"{DAILY_START_YEAR}-04-01":
            k = (d, r["studio_code"])
            meta_daily[k] = meta_daily.get(k, 0) + (r.get("spend") or 0)

    # ── 3. Collect Google monthly rows (pre-2026) ────────────────────
    google_monthly: dict[tuple, float] = {}
    for r in google_raw.get("monthly", []):
        mo = r.get("month", "")[:7]
        if mo < str(DAILY_START_YEAR):
            code = name_to_code.get(r.get("studio", ""))
            if not code:
                continue
            k = (mo, code)
            google_monthly[k] = google_monthly.get(k, 0) + (r.get("spend") or 0)

    # ── 4. Collect Google daily rows (Apr 2026+) ─────────────────────
    google_daily: dict[tuple, float] = {}
    for r in google_raw.get("daily", []):
        d = r.get("date", "")
        if d[:4] == str(DAILY_START_YEAR) and d >= f"{DAILY_START_YEAR}-04-01":
            code = name_to_code.get(r.get("studio", ""))
            if not code:
                continue
            k = (d, code)
            google_daily[k] = google_daily.get(k, 0) + (r.get("spend") or 0)

    # ── 5. Build daily output rows for all of 2026 ───────────────────
    # Jan–Mar 2026: distribute from monthly totals
    # Apr 2026+:    use actual daily data

    daily_out: dict[tuple, dict] = {}

    def upsert_daily(date_str, code, meta=0.0, google=0.0):
        k = (date_str, code)
        if k not in daily_out:
            daily_out[k] = {"date": date_str, "studio_code": code, "meta_spend": 0.0, "google_spend": 0.0}
        daily_out[k]["meta_spend"]   = round(daily_out[k]["meta_spend"]   + meta,   4)
        daily_out[k]["google_spend"] = round(daily_out[k]["google_spend"] + google, 4)

    # Jan–Mar 2026 from Meta monthly
    for (mo, code), spend in meta_monthly.items():
        if mo[:4] == str(DAILY_START_YEAR):
            for row in distribute_monthly_to_days(mo, spend, code):
                upsert_daily(row["date"], code, meta=row["daily"])

    # Jan–Mar 2026 from Google monthly (pull 2026 months from google_raw.monthly)
    for r in google_raw.get("monthly", []):
        mo = r.get("month", "")[:7]
        if mo[:4] == str(DAILY_START_YEAR) and mo < f"{DAILY_START_YEAR}-04":
            code = name_to_code.get(r.get("studio", ""))
            if not code:
                continue
            for row in distribute_monthly_to_days(mo, r.get("spend") or 0, code):
                upsert_daily(row["date"], code, google=row["daily"])

    # Apr 2026+ Meta daily
    for (d, code), spend in meta_daily.items():
        upsert_daily(d, code, meta=spend)

    # Apr 2026+ Google daily
    for (d, code), spend in google_daily.items():
        upsert_daily(d, code, google=spend)

    # ── 6. Build monthly output rows (pre-2026) ──────────────────────
    all_keys = set(meta_monthly.keys()) | set(google_monthly.keys())
    monthly_out = []
    for (mo, code) in sorted(all_keys):
        if mo[:4] >= str(DAILY_START_YEAR):
            continue
        monthly_out.append({
            "month":        mo,
            "studio_code":  code,
            "meta_spend":   round(meta_monthly.get((mo, code), 0), 2),
            "google_spend": round(google_monthly.get((mo, code), 0), 2),
        })

    daily_list = sorted(daily_out.values(), key=lambda r: (r["date"], r["studio_code"]))

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "daily":        daily_list,
        "monthly":      monthly_out,
    }

    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"OK Wrote {OUT_PATH.name} — "
        f"{len(daily_list)} daily rows, {len(monthly_out)} monthly rows"
    )
    daily_months = sorted(set(r["date"][:7] for r in daily_list))
    if daily_months:
        print(f"   Daily range: {daily_months[0]} to {daily_months[-1]}")
    monthly_months = sorted(set(r["month"] for r in monthly_out))
    if monthly_months:
        print(f"   Monthly range: {monthly_months[0]} to {monthly_months[-1]}")


if __name__ == "__main__":
    run()
