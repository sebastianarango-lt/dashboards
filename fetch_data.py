import snowflake.connector
import json
import os
from datetime import datetime, date

# ── Credentials ───────────────────────────────────────────────────────────────
SF_ACCOUNT   = os.getenv("SF_ACCOUNT",   "MINDBODYORG-PLAYLIST_DATA_MART_SWEAT440")
SF_USER      = os.getenv("SF_USER",      "SWEAT440")
SF_ROLE      = os.getenv("SF_ROLE",      "SYSADMIN")
SF_WAREHOUSE = os.getenv("SF_WAREHOUSE", "COMPUTE_WH")
SF_DATABASE  = os.getenv("SF_DATABASE",  "MARKETING_REPORTS")
SF_SCHEMA    = os.getenv("SF_SCHEMA",    "PUBLIC")
SF_TOKEN     = os.getenv("SF_TOKEN")


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def strip_brand(name):
    """Remove 'SWEAT440 ' prefix for canonical studio names used across all data sources."""
    return name.replace("SWEAT440 ", "") if name else name


# ════════════════════════════════════════════════════════════════════════════
# SNOWFLAKE
# ════════════════════════════════════════════════════════════════════════════
print("Connecting to Snowflake...")
conn = snowflake.connector.connect(
    account=SF_ACCOUNT, user=SF_USER, token=SF_TOKEN,
    authenticator="programmatic_access_token",
    role=SF_ROLE, warehouse=SF_WAREHOUSE, database=SF_DATABASE, schema=SF_SCHEMA
)
cur = conn.cursor()

# ── Daily: previous quarter start → today ────────────────────────────────
cur.execute("""
    SELECT
        EVENT_DATE, STUDIO_NAME, SOURCE,
        SUM(SIGNUPS)            AS signups,
        SUM(FIRST_VISITS)       AS first_visits,
        SUM(FIRST_ACTIVATIONS)  AS first_activations,
        SUM(FIRST_SALES)        AS first_sales
    FROM MARKETING_REPORTS.PUBLIC.LEADS
    WHERE EVENT_DATE >= DATEADD('quarter', -1, DATE_TRUNC('quarter', CURRENT_DATE()))
      AND EVENT_DATE <= CURRENT_DATE()
    GROUP BY 1, 2, 3
    ORDER BY 1, 2, 3
""")
daily_detail = [
    {
        "date":               json_serial(r[0]),
        "studio":             strip_brand(r[1]),
        "source":             r[2],
        "signups":            int(r[3] or 0),
        "first_visits":       int(r[4] or 0),
        "first_activations":  int(r[5] or 0),
        "first_sales":        int(r[6] or 0),
    }
    for r in cur.fetchall()
]

# ── Monthly: older history, 3yr cap ──────────────────────────────────────
cur.execute("""
    SELECT
        DATE_TRUNC('month', EVENT_DATE) AS month,
        STUDIO_NAME, SOURCE,
        SUM(SIGNUPS)            AS signups,
        SUM(FIRST_VISITS)       AS first_visits,
        SUM(FIRST_ACTIVATIONS)  AS first_activations,
        SUM(FIRST_SALES)        AS first_sales
    FROM MARKETING_REPORTS.PUBLIC.LEADS
    WHERE EVENT_DATE <  DATEADD('quarter', -1, DATE_TRUNC('quarter', CURRENT_DATE()))
      AND EVENT_DATE >= DATEADD('year', -3, CURRENT_DATE())
    GROUP BY 1, 2, 3
    ORDER BY 1, 2, 3
""")
monthly_detail = [
    {
        "month":              json_serial(r[0]),
        "studio":             strip_brand(r[1]),
        "source":             r[2],
        "signups":            int(r[3] or 0),
        "first_visits":       int(r[4] or 0),
        "first_activations":  int(r[5] or 0),
        "first_sales":        int(r[6] or 0),
    }
    for r in cur.fetchall()
]

# ── Studio + source lists ─────────────────────────────────────────────────
cur.execute("""
    SELECT DISTINCT STUDIO_NAME
    FROM MARKETING_REPORTS.PUBLIC.LEADS
    WHERE STUDIO_NAME IS NOT NULL
    ORDER BY 1
""")
studios = [strip_brand(r[0]) for r in cur.fetchall()]

cur.execute("""
    SELECT DISTINCT SOURCE
    FROM MARKETING_REPORTS.PUBLIC.LEADS
    WHERE SOURCE IS NOT NULL
    ORDER BY 1
""")
sources = [r[0] for r in cur.fetchall()]

conn.close()
print(f"  Snowflake: {len(daily_detail):,} daily rows, {len(monthly_detail):,} monthly rows")

# ════════════════════════════════════════════════════════════════════════════
# WRITE data.json
# ════════════════════════════════════════════════════════════════════════════
# Studio names use the canonical short form (no "SWEAT440 " prefix).
# This is the shared merge key across data.json, paid-ads-data.json,
# and google-ads-data.json.

output = {
    "generated_at":   datetime.utcnow().isoformat() + "Z",
    "studios":        studios,
    "sources":        sources,
    "daily_detail":   daily_detail,
    "monthly_detail": monthly_detail,
}

with open("data.json", "w") as f:
    json.dump(output, f, indent=2, default=json_serial)

size_kb = os.path.getsize("data.json") / 1024
print(f"\n✅  data.json written — {size_kb:.1f} KB")
print(f"    Snowflake: {len(daily_detail):,} daily + {len(monthly_detail):,} monthly rows")
