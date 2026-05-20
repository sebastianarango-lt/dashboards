# SWEAT440 NSO Dashboard — Project Summary

## What We're Building
A branded marketing performance dashboard for SWEAT440 NSO (New Studio Opening) franchise owners. Replaces Looker Studio with a custom HTML/JS dashboard, pulling data from 4 APIs and Snowflake, served as static JSON files via GitHub Actions.

---

## Architecture (3 Phases)

### Phase 1 — DONE (Testing)
- Python scripts pull from 4 APIs → write to Google Sheets for visual verification
- Test location: Herriman (Utah)
- Files: `fetch_meta_ads.py`, `fetch_google_ads.py`, `fetch_ga4.py`, `fetch_gbp.py`, `sheets_writer.py`, `run_all.py`

### Phase 2 — IN PROGRESS
- Python scripts write to JSON files (served as static assets via GitHub Pages)
- Dashboard: `nso-studios.html` — HTML/JS, no framework
- Tabs: **Summary, Scorecard, Funnel, Leads, Sales, Meta Ads, Facebook, Instagram, Google Ads, GBP**
- GitHub Actions runs daily at 3am LA time (11:00 UTC) to refresh JSON files

**3 data sources for the NSO dashboard:**
| File | Source | Contents |
|------|--------|----------|
| `data.json` | Snowflake / MindBody | Leads, first visits, first activations, first sales (all studios) |
| `nso_sales_data.json` | Snowflake / MART_SALES_DETAILS | Presales & cancellations for 5 NSO studios |
| `nso_scorecard_data.json` | Built locally from above | Weekly scorecard per studio (cumulative leads, presales, IG followers, spend, RMR) |
| `marketing_data.json` | Meta, Google Ads, GA4, Snowflake | Full raw marketing data (no studio filter) |
| `nso_google_ads.json` | Google Ads MCC | Campaign-level performance for all accounts |
| `social_insights.json` | Meta Graph API | Facebook Page + Instagram organic for all 5 studios |
| `gbp_data.json` | Google Business Profile API | Daily impressions, calls, clicks, directions for all 5 studios |

### Phase 3 — NOT STARTED
- React dashboard embedded in WordPress via iframe
- Vercel serverless function `/api/metrics`
- JWT token validates franchisee → queries Snowflake filtered by `franchise_id`
- 90-day pre-aggregated data cached in browser; all filtering client-side

---

## Repo Structure

```
nso-dashboard/
├── nso-studios.html              ← Main NSO dashboard (HTML/JS)
├── marketing_data.json           ← Meta + Google Ads + GA4 + Snowflake (raw)
├── nso_google_ads.json           ← Google Ads campaign data
├── nso_sales_data.json           ← Presales & cancellations (Snowflake)
├── nso_scorecard_data.json       ← Weekly scorecard for all 5 studios
├── social_insights.json          ← Facebook Page + Instagram organic
├── gbp_data.json                 ← GBP daily metrics
├── requirements.txt
├── config/
│   └── franchise_config.json     ← Per-studio platform account IDs (Herriman only)
└── scripts/
    ├── fetch_all_marketing.py    ← Pulls Meta + Google Ads + GA4 + Snowflake → marketing_data.json
    ├── fetch_meta_ads.py         ← Meta Ads (Phase 1, writes to Sheets)
    ├── fetch_google_ads.py       ← Google Ads (Phase 1, writes to Sheets)
    ├── fetch_ga4.py              ← GA4 (Phase 1, writes to Sheets)
    ├── fetch_gbp.py              ← GBP daily metrics → gbp_data.json
    ├── fetch_nso_sales.py        ← Presales/cancellations from Snowflake → nso_sales_data.json
    ├── fetch_social_insights.py  ← Facebook Page + Instagram → social_insights.json
    ├── build_scorecard_from_data.py ← Rebuilds leads/presales in scorecard from data.json
    ├── build_all_scorecards.py   ← Generates full nso_scorecard_data.json for all 5 studios
    ├── merge_array_json.py       ← Generic merger for flat-array JSON files (marketing_data, nso_google_ads)
    ├── merge_gbp.py              ← Incremental merge for gbp_data.json (by studio location_id)
    └── merge_nso_sales.py        ← Incremental merge for nso_sales_data.json (recalculates totals)
```

---

## 5 NSO Studios — Complete Config

| Studio | State | Snowflake ID | Google Ads CID | GBP Location ID |
|--------|-------|-------------|----------------|-----------------|
| Herriman | UT | 5752080 | 385-801-4125 | 4243744174605320602 |
| Naples - Mercato | FL | 5751381 | TBD | 9241286551304249574 |
| Dallas - Prestonwood | TX | 5750138 | TBD | 11402535545027699120 |
| Pinecrest - Palmetto Bay | FL | 5750128 | TBD | 13145255458617855723 |
| Reston | VA | 5750130 | TBD | 10767130387921211013 |

### Facebook Page & Instagram IDs (from `fetch_social_insights.py`)

| Studio | Code | Facebook Page ID | Instagram ID |
|--------|------|-----------------|--------------|
| Herriman | UT-001 | 1016504601542354 | 17841447639266583 |
| Naples - Mercato | FL-019 | 986896304505624 | None |
| Dallas - Prestonwood | TX-003 | 845182982009071 | 17841477656432324 |
| Pinecrest - Palmetto Bay | FL-017 | 848877064975048 | 17841477435248000 |
| Reston | VA-001 | 875200972337017 | 17841477453277172 |

### Scorecard Week Schedules

| Studio | Week 1 Start | Week Structure |
|--------|-------------|----------------|
| Naples - Mercato | Tue 2/10/2026 | Irregular (Excel-based, see NAPLES_DATE_RANGES in build_all_scorecards.py) |
| Dallas - Prestonwood | Mon 11/10/2025 | Standard Mon-Sun 7-day |
| Reston | Mon 11/17/2025 | Standard Mon-Sun 7-day |
| Pinecrest - Palmetto Bay | Mon 12/15/2025 | Standard Mon-Sun 7-day |
| Herriman | Mon 5/18/2026 | Standard Mon-Sun 7-day (not started yet) |

Naples targets: 1,257 leads, 440 presales, $48,660 Day-1 RMR. CPL $28-41, CPA $80-116.
Naples C/O week: 24 (7/20-7/26), Grand Open week: 27 (8/10-8/16).

---

## Data Sources & Credentials

### Meta Marketing API
- Ad account: `act_1553887681409034` (one shared corporate account)
- `fetch_all_marketing.py` pulls ad-level daily data + creative metadata (thumbnail, image, preview link)
- Credentials: `META_ACCESS_TOKEN`, `META_APP_ID`, `META_APP_SECRET`

### Google Ads
- MCC (LeadTeam): `605-546-2417`
- `fetch_all_marketing.py` lists all enabled accounts under the MCC automatically — no per-studio CID needed
- Credentials: `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

### Google Analytics 4 (GA4)
- Property ID: `341934364` (covers all sweat440.com)
- Filtering by `landingPagePlusQueryString` (BEGINS_WITH per studio path)
- `fetch_all_marketing.py` pulls 3 datasets: landing-page sessions, all-page views, conversions
- GA4 paths: Herriman `/gyms/utah-herriman/`, Pinecrest `/gyms/locations-florida-pinecrest/`
- Credentials: `GOOGLE_SERVICE_ACCOUNT_KEY_PATH`, `GA4_PROPERTY_ID`

### Google Business Profile (GBP)
- `fetch_gbp.py` uses Business Profile Performance API — all 5 location IDs now known
- Metrics: impressions (desktop/mobile, maps/search), call clicks, website clicks, direction requests
- Reviews stub: returns null (account IDs not yet available for all locations)
- Credentials: `GBP_CLIENT_ID`, `GBP_CLIENT_SECRET`, `GBP_REFRESH_TOKEN`

### Snowflake
- `fetch_nso_sales.py`: queries `MART_SALES_DETAILS` for presales/cancellations
  - Dedup: `ROW_NUMBER() OVER (PARTITION BY CLIENT_ID, PRODUCT_DESCRIPTION, SALE_DATE::DATE, QUANTITY)` — each transaction appears twice (LOCATION_ID 1 + 98)
  - Source attribution: joins `MART_LEADS_LOG` + `MART_CLIENTS`, maps raw sources to: Meta Ads, Google Ads, TikTok Ads, Local Listings, Grassroots, Website (unattributed), SWEAT440 App, etc.
  - Revenue: uses `GROSS_PAYMENTAMT_LOCAL` (`PAYMENTAMT_LOCAL` is always 0 for presales)
- `fetch_all_marketing.py`: also queries studios list, leads, memberships, sales from all SWEAT440 studios
- Credentials: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE` (default: `PLAYLIST_DATA_MART`), `SNOWFLAKE_ROLE`

---

## nso_scorecard_data.json Structure

```json
{
  "studios": [
    {
      "name": "Naples - Mercato",
      "code": "FL-019",
      "full_name": "SWEAT440 Naples - Mercato",
      "targets": { "total_leads": 1257.14, "presales_count": 440.0, ... },
      "co_week": 24,
      "go_week": 27,
      "current_week": 14,
      "weeks": [
        {
          "week": "Week 0",
          "date_range": "Pre 2/10",
          "date_start": null,
          "date_end": "2026-02-09",
          "total_leads": 0.0,
          "presales_count": 0.0,
          "presales_week": null,
          "cancellations_count": 0.0,
          "cancellations_week": null,
          "ig_new_followers": null,
          "estimated_day1_rmr": null,
          "total_marketing_spend": null,
          "blended_cpl": null,
          "blended_cpa": null
        }
      ]
    }
  ]
}
```

---

## Key Scripts — Usage

```bash
# Pull all marketing data (Meta + Google Ads + GA4 + Snowflake)
python scripts/fetch_all_marketing.py --days 90
python scripts/fetch_all_marketing.py --source meta --days 30
python scripts/fetch_all_marketing.py --source ga4 --location pinecrest

# Pull NSO presales/cancellations
python scripts/fetch_nso_sales.py --start 2025-01-01

# Pull Facebook + Instagram organic
python scripts/fetch_social_insights.py --days 90

# Pull GBP performance metrics
python scripts/fetch_gbp.py --start 2025-01-01

# Rebuild full scorecard from data.json + nso_sales_data.json + social_insights.json
python scripts/build_all_scorecards.py
python scripts/build_all_scorecards.py --dry-run

# Update only leads/presales in existing scorecard (faster)
python scripts/build_scorecard_from_data.py
python scripts/build_scorecard_from_data.py --studio "Naples - Mercato"

# Incremental merges (for daily refresh)
python scripts/merge_array_json.py --existing marketing_data.json --new marketing_data_new.json --keys meta_ads ga4_traffic
python scripts/merge_array_json.py --existing nso_google_ads.json --new nso_google_ads_new.json --keys google_ads
python scripts/merge_gbp.py --existing gbp_data.json --new gbp_data_new.json
python scripts/merge_nso_sales.py --existing nso_sales_data.json --new nso_sales_new.json
```

---

## Current Status

| Item | Status |
|------|--------|
| All Snowflake IDs | ✅ Known for all 5 studios |
| All GBP Location IDs | ✅ Known for all 5 studios |
| Facebook Page IDs | ✅ All 5 studios |
| Instagram IDs | ✅ 4/5 studios (Naples missing) |
| fetch_nso_sales.py | ✅ Built, dedup + source attribution |
| fetch_social_insights.py | ✅ Built, handles rate limits, chunked requests |
| fetch_gbp.py | ✅ Built, all location IDs configured |
| build_all_scorecards.py | ✅ Built, generates all 5 studio scorecards |
| merge scripts | ✅ Built for marketing_data, nso_google_ads, gbp, nso_sales |
| nso-studios.html | ✅ In progress — tabs: Summary, Scorecard, Funnel, Leads, Sales, Meta Ads, Facebook, Instagram, Google Ads, GBP |
| GA4 per-location filtering | ✅ Uses BEGINS_WITH on landingPagePlusQueryString |
| GBP quota | ✅ API working with OAuth2 refresh token |
| Google Ads per-studio CID | ⚠️ Only Herriman confirmed; others TBD |
| Naples Instagram | ⚠️ No IG ID available |
| Production deploy | ❌ Not started (Phase 3: Vercel + JWT + WordPress) |

---

## Tech Stack

- **Python 3** — data ingestion scripts
- **HTML/JS** — dashboard frontend (Phase 2); React planned for Phase 3
- **Snowflake** — MindBody + ClassPass data warehouse
- **Vercel** — serverless API for Phase 3
- **WordPress** — franchise portal (Phase 3, iframe embed)
- **GitHub Actions** — daily data refresh at 11:00 UTC (3am LA)
