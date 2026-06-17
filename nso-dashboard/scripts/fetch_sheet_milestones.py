"""
fetch_sheet_milestones.py
Reads scheduling dates AND tier pricing from the NSO Config Google Sheet,
then patches nso_scorecard_data.json with:
  - milestones: pre-launch date cards
  - pricing:    tier prices + week numbers when each tier starts

Run from the nso-dashboard/ folder:
    python scripts/fetch_sheet_milestones.py
"""
import json, re, math
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

SPREADSHEET_ID = "1Ku0VSwOY6HVXuqucduWlsbKIiNzb0ojL21rozaPpHHU"
CREDS_FILE     = "credentials/service_account.json"
SCORECARD_FILE = "nso_scorecard_data.json"

# Fixed column indices — only name/code/pricing are stable (left of scheduling section).
# All scheduling columns use header-name lookup via hdr_map (see below).
_COL_NAME  = 0
_COL_CODE  = 1
_COL_TIER1 = 3
_COL_TIER2 = 4
_COL_TIER3 = 5

# Pre-launch milestone columns (ordered by appearance in the pre-launch timeline).
# Each entry: (key, sheet_header_name)
MILESTONE_COLS = [
    ("early_lead_date",          "Early Lead Date"),
    ("mbo_date",                 "Full Marketing Build Out Complete"),
    ("paid_lead_gen_date",       "Paid Lead Gen Date"),
    ("paid_presales_start_date", "Paid Presales Start Date"),
]

MILESTONE_LABELS = {
    "early_lead_date":           "Early Lead Date",
    "mbo_date":                  "Full Marketing Build Out Complete",
    "paid_lead_gen_date":        "Paid Lead Gen Start",
    "paid_presales_start_date":  "Paid Presales Start Date",
}

MILESTONE_SUBTITLES = {
    "early_lead_date":           "Landing page & early interest list",
    "mbo_date":                  "Lead form live on website",
    "paid_lead_gen_date":        "Meta / Google paid ads begin",
    "paid_presales_start_date":  "Presales campaign begins",
}


def norm_date(s):
    """M/D/YYYY or YYYY-MM-DD → YYYY-MM-DD. Returns None if blank/n/a."""
    if not s or s.strip().lower() in ("", "n/a", "tbd", "-"):
        return None
    s = s.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def norm_price(s):
    """'$99' or '99' → 99 (int). Returns None if blank/n/a."""
    if not s or s.strip().lower() in ("", "n/a", "-"):
        return None
    try:
        return int(re.sub(r"[^0-9]", "", s.strip()))
    except (ValueError, TypeError):
        return None


def norm_float(s):
    """'1,257' or '48660' → float. Returns None if blank/n/a."""
    if not s or str(s).strip().lower() in ("", "n/a", "-"):
        return None
    try:
        return float(re.sub(r"[^0-9.]", "", str(s).strip()))
    except (ValueError, TypeError):
        return None


def cell(row, col):
    return row[col] if col < len(row) else ""


def date_to_week_num(move_date_str, week1_start_str):
    """
    'Week 1 Start' from the sheet is treated as Week 0 (the base).
    Week numbers count forward from there: ceil(days / 7).
    e.g. 22 days after Week 1 Start → ceil(22/7) = 4
    """
    if not move_date_str or not week1_start_str:
        return None
    try:
        base = datetime.strptime(week1_start_str, "%Y-%m-%d")
        move = datetime.strptime(move_date_str,   "%Y-%m-%d")
        days = (move - base).days
        if days <= 0:
            return None
        return math.ceil(days / 7)
    except ValueError:
        return None


# ── Read Google Sheet ────────────────────────────────────────────────────────
print("Reading NSO Config sheet...")
creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
svc  = build("sheets", "v4", credentials=creds)
res  = svc.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range="NSO Config"
).execute()
rows = res.get("values", [])

# Build header-name lookup from row 1 (row 0 = group headers).
hdr_row = rows[1] if len(rows) > 1 else []
hdr_map = {h.strip().lower(): i for i, h in enumerate(hdr_row)}

def _hi(name):
    """Column index by header name (case-insensitive). Returns -1 if not found."""
    return hdr_map.get(name.strip().lower(), -1)

def _hcell(row, name):
    i = _hi(name)
    return cell(row, i) if i >= 0 else ""

data_rows = rows[2:]  # skip group-header row and column-header row

# Build lookup: code -> {milestones, pricing_raw}
sheet_map = {}
for row in data_rows:
    code = cell(row, _COL_CODE).strip()
    if not code:
        continue

    # Pre-launch milestones
    milestones = []
    for key, header in MILESTONE_COLS:
        d = norm_date(_hcell(row, header))
        if d:
            milestones.append({
                "key":      key,
                "label":    MILESTONE_LABELS[key],
                "subtitle": MILESTONE_SUBTITLES[key],
                "date":     d,
            })
    milestones.sort(key=lambda m: m["date"])

    # Scheduling dates — all via header-name lookup (column positions may vary)
    week1_start = norm_date(_hcell(row, "Week 1 Start"))
    t2_move     = norm_date(_hcell(row, "Tier 2 Move Date"))
    t3_move     = norm_date(_hcell(row, "Tier 3 Move Date"))
    co_date     = norm_date(_hcell(row, "Target CO Date"))
    open_date   = norm_date(_hcell(row, "Target Open Date"))
    goal_ann    = norm_date(_hcell(row, "Goal to Announce Opening"))

    cpl_raw  = (_hcell(row, "CPL Range") or "").strip() or None
    cpa_raw  = (_hcell(row, "CPA Range") or "").strip() or None
    cr_raw   = norm_float(_hcell(row, "Conversion Rate"))

    sheet_map[code] = {
        "milestones":            milestones,
        "tier1_price":           norm_price(cell(row, _COL_TIER1)),
        "tier2_price":           norm_price(cell(row, _COL_TIER2)),
        "tier3_price":           norm_price(cell(row, _COL_TIER3)),
        "week1_start":           week1_start,
        "tier2_start_week":      date_to_week_num(t2_move, week1_start),
        "tier3_start_week":      date_to_week_num(t3_move, week1_start),
        "tier2_start_date":      t2_move,
        "tier3_start_date":      t3_move,
        "tier1_members_target":  norm_price(_hcell(row, "Tier 1 Members Target")),
        "tier2_members_target":  norm_price(_hcell(row, "Tier 2 Members Target")),
        "tier3_members_target":  norm_price(_hcell(row, "Tier 3 Members Target")),
        "estimated_roms_target": (_hcell(row, "Estimated ROMs Target") or "").strip() or None,
        "total_leads_target":    norm_float(_hcell(row, "Total Leads Target")),
        "presales_target":       norm_float(_hcell(row, "Presales Target")),
        "day1_rmr_target":       norm_float(_hcell(row, "Day 1 RMR Target")),
        "cpl_range":             f"${cpl_raw}" if cpl_raw else None,
        "cpa_range":             f"${cpa_raw}" if cpa_raw else None,
        "conversion_rate":       cr_raw,
        "co_date":               co_date,
        "co_week":               date_to_week_num(co_date, week1_start),
        "opening_date":          open_date,
        "go_week":               date_to_week_num(open_date, week1_start),
        "goal_announce_date":    goal_ann,
    }

# ── Patch scorecard JSON ────────────────────────────────────────────────────
with open(SCORECARD_FILE) as f:
    sc = json.load(f)

updated = 0
for studio in sc.get("studios", []):
    code = studio.get("code", "")
    info = sheet_map.get(code)
    if not info:
        studio.setdefault("milestones", [])
        continue

    studio["milestones"] = info["milestones"]

    # Patch Week 1 date_start to match "Week 1 Start" from sheet
    w1_start = info.get("week1_start")
    if w1_start:
        for wk in studio.get("weeks", []):
            label = re.sub(r"[^0-9]", "", wk.get("week", ""))
            if label == "1":
                if wk.get("date_start") != w1_start:
                    print(f"    fixing W1 date_start: {wk.get('date_start')} -> {w1_start}")
                    wk["date_start"] = w1_start
                break

    pricing = {}
    for key in ("tier1_price", "tier2_price", "tier3_price",
                "tier2_start_week", "tier3_start_week",
                "tier2_start_date", "tier3_start_date",
                "tier1_members_target", "tier2_members_target", "tier3_members_target",
                "estimated_roms_target"):
        if info.get(key) is not None:
            pricing[key] = info[key]

    studio["pricing"] = pricing if pricing else None

    # Update studio-level targets from sheet
    tgt = studio.setdefault("targets", {})
    for key, sheet_key in [
        ("total_leads",        "total_leads_target"),
        ("presales_count",     "presales_target"),
        ("estimated_day1_rmr", "day1_rmr_target"),
        ("blended_cpl",        "cpl_range"),
        ("blended_cpa",        "cpa_range"),
        ("conversion_rate",    "conversion_rate"),
    ]:
        v = info.get(sheet_key)
        if v is not None:
            tgt[key] = v

    # Update CO / GO dates and week numbers
    if info.get("opening_date"):
        studio["opening_date"] = info["opening_date"]
    if info.get("co_week") is not None:
        studio["co_week"] = info["co_week"]
    if info.get("go_week") is not None:
        studio["go_week"] = info["go_week"]
    if info.get("goal_announce_date"):
        studio["goal_announce_date"] = info["goal_announce_date"]

    updated += 1
    print(f"  {code} ({studio['name']}): "
          f"co_week={info.get('co_week')} go_week={info.get('go_week')} | "
          f"leads={info.get('total_leads_target')} ps={info.get('presales_target')} | "
          f"{len(info['milestones'])} milestone(s)")

with open(SCORECARD_FILE, "w") as f:
    json.dump(sc, f, indent=2)

print(f"\nDone. {SCORECARD_FILE} updated — {updated} studio(s) patched")
