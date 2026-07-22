#!/usr/bin/env python3
"""
fetch_client_history.py — Pull individual membership sales and cancellations
for all NSO studios from Snowflake, for the Client History report.

Output JSON format:
{
    "generated_at": "2026-07-21T00:00:00",
    "studios": [
        {
            "name": "SWEAT440 Herriman",
            "code": "UT-001",
            "records": [
                {
                    "type": "sale",           -- "sale" | "cancel"
                    "client_name": "Jane Doe",
                    "email": "jane@example.com",
                    "phone": "8015551234",
                    "product": "3 Month Presale Membership",
                    "date": "2026-07-20",
                    "time": "14:32",          -- HH:MM local; "" if unknown
                    "platform": "Business Mode Web",
                    "sold_by": "Studio Staff",  -- derived from SOURCE_CHANNEL
                    "amount": 99.00
                },
                ...
            ]
        }
    ]
}

Usage:
  python scripts/fetch_client_history.py
  python scripts/fetch_client_history.py --output nso_client_history.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import snowflake.connector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import studios as studios_registry

NSO_STUDIOS = studios_registry.nso_studios_by_snowflake_id()
ID_LIST = ",".join(str(i) for i in NSO_STUDIOS)

# ---------------------------------------------------------------------------
# SOURCE_CHANNEL → human-readable "sold by" label
# ---------------------------------------------------------------------------
def _sold_by(source_channel: str | None, online_flag) -> str:
    ch = (source_channel or "").strip()
    if not ch:
        return "Unknown"
    if "business mode" in ch.lower():
        return "Studio Staff"
    if "branded mobile" in ch.lower():
        return "Client (App)"
    if "branded web" in ch.lower():
        return "Client (Web)"
    if "consumer mode" in ch.lower():
        return "Client (Consumer)"
    if "api" in ch.lower():
        return "API"
    if online_flag:
        return "Client (Online)"
    return "Studio Staff"


# ---------------------------------------------------------------------------
# Snowflake connection
# ---------------------------------------------------------------------------
def get_conn():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ.get("SNOWFLAKE_DATABASE", "PLAYLIST_DATA_MART"),
        role=os.environ.get("SNOWFLAKE_ROLE", ""),
    )


# ---------------------------------------------------------------------------
# Main query — individual presale + cancellation records with phone join
# ---------------------------------------------------------------------------
QUERY = f"""
WITH base AS (
    SELECT
        s.STUDIO_ID,
        s.CLIENT_ID,
        s.CLIENT_FULL_NAME                          AS client_name,
        s.EMAIL_ID                                  AS email,
        s.PRODUCT_DESCRIPTION                       AS product,
        s.SALE_DATE::DATE                           AS sale_date,
        s.CREATED_DATE_TIME_UTC                     AS created_utc,
        s.ONLINE_FLAG,
        s.SOURCE_CHANNEL,
        s.QUANTITY,
        s.IS_RETURN,
        COALESCE(s.GROSS_PAYMENTAMT_LOCAL, 0)       AS amount,
        -- LOC=98 dedup (same logic as fetch_nso_sales.py)
        MAX(CASE WHEN s.LOCATION_ID != 98 THEN 1 ELSE 0 END) OVER (
            PARTITION BY s.STUDIO_ID, s.CLIENT_ID, s.PRODUCT_DESCRIPTION,
                         s.SALE_DATE::DATE, s.QUANTITY
        ) AS has_non98_sibling,
        s.LOCATION_ID
    FROM PLAYLIST_DATA_MART.MINDBODY_REPORTING_ANALYTICS.MART_SALES_DETAILS s
    WHERE s.STUDIO_ID IN ({ID_LIST})
      AND s.ITEM_TYPE = 'Pricing Option'
      AND LOWER(s.PRODUCT_DESCRIPTION) LIKE '%pre%sale%'
      AND (s.EMAIL_ID IS NULL OR (
          LOWER(TRIM(s.EMAIL_ID)) NOT LIKE 'test%'
      AND LOWER(TRIM(s.EMAIL_ID)) NOT LIKE '%sweat440%'
      AND LOWER(TRIM(s.EMAIL_ID)) NOT LIKE '%leadteam%'
      ))
),
filtered AS (
    SELECT * FROM base
    WHERE LOCATION_ID != 98 OR has_non98_sibling = 0
),
phones AS (
    SELECT
        CLIENT_ID,
        STUDIO_ID,
        COALESCE(NULLIF(TRIM(CELLPHONE),''), NULLIF(TRIM(HOMEPHONE),''), NULLIF(TRIM(WORKPHONE),'')) AS phone
    FROM PLAYLIST_DATA_MART.MINDBODY_REPORTING_ANALYTICS.MART_CLIENTS
    WHERE STUDIO_ID IN ({ID_LIST})
)
SELECT
    f.STUDIO_ID,
    f.client_name,
    f.email,
    COALESCE(p.phone, '')                           AS phone,
    f.product,
    f.sale_date,
    f.created_utc,
    f.ONLINE_FLAG,
    COALESCE(f.SOURCE_CHANNEL, '')                  AS source_channel,
    CASE WHEN f.QUANTITY = 1 AND f.IS_RETURN = 0 THEN 'sale' ELSE 'cancel' END AS txn_type,
    f.amount
FROM filtered f
LEFT JOIN phones p ON p.CLIENT_ID = f.CLIENT_ID AND p.STUDIO_ID = f.STUDIO_ID
ORDER BY f.STUDIO_ID, f.sale_date DESC, f.created_utc DESC
"""


def fetch_all() -> dict:
    conn = get_conn()
    cur = conn.cursor()
    print("Running client history query...")
    cur.execute(QUERY)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    print(f"  {len(rows)} records fetched")

    # Group by studio
    studio_records: dict[int, list] = {}
    for r in rows:
        row = dict(zip(cols, r))
        sid = row["STUDIO_ID"]
        if sid not in studio_records:
            studio_records[sid] = []

        # Parse time from CREATED_DATE_TIME_UTC
        time_str = ""
        if row["CREATED_UTC"]:
            try:
                dt = row["CREATED_UTC"]
                if hasattr(dt, "strftime"):
                    time_str = dt.strftime("%H:%M")
            except Exception:
                pass

        studio_records[sid].append({
            "type":        row["TXN_TYPE"],
            "client_name": row["CLIENT_NAME"] or "",
            "email":       row["EMAIL"] or "",
            "phone":       row["PHONE"] or "",
            "product":     row["PRODUCT"] or "",
            "date":        str(row["SALE_DATE"]) if row["SALE_DATE"] else "",
            "time":        time_str,
            "platform":    row["SOURCE_CHANNEL"] or "",
            "sold_by":     _sold_by(row["SOURCE_CHANNEL"], row["ONLINE_FLAG"]),
            "amount":      float(row["AMOUNT"] or 0),
        })

    studios_out = []
    for sid, info in NSO_STUDIOS.items():
        records = studio_records.get(sid, [])
        studios_out.append({
            "name":    info["name"],
            "code":    info["code"],
            "records": records,
        })
        print(f"  {info['name']}: {len(records)} records")

    return {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        "studios": sorted(studios_out, key=lambda s: s["name"]),
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch NSO client history from Snowflake.")
    parser.add_argument("--output", default="nso_client_history.json")
    args = parser.parse_args()

    result = fetch_all()

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    total = sum(len(s["records"]) for s in result["studios"])
    print(f"\nDone. {total} total records written to {args.output}")


if __name__ == "__main__":
    main()
