# studios.json migration report

Built 43 studio entries.

## Flags / TODOs for review before merging

- **Music Row** (TN-001): had historical/baked Meta spend but no live `config-meta.yaml` entry. Added `meta.match="Music Row"` fresh as part of this migration -- VERIFY against real ad/campaign naming before merging.
- **Reston** (VA-001): had historical/baked Meta spend but no live `config-meta.yaml` entry. Added `meta.match="Reston"` fresh as part of this migration -- VERIFY against real ad/campaign naming before merging.
- **Fort Myers** (FL-022): present in `data.json` (has Snowflake data) but no `snowflake_id` found in `fetch_nso_sales.py`/`fetch_tier_rmr.py` -- TODO: look up the real Snowflake `studio_id` and fill in `snowflake_id` (currently `null`).
- **Dunwoody**: has a `snowflake_id` but no `tier_pricing` found in `fetch_tier_rmr.py` STUDIO_PRICING -- TODO: confirm whether it needs one.
- **Middletown**: has a `snowflake_id` but no `tier_pricing` found in `fetch_tier_rmr.py` STUDIO_PRICING -- TODO: confirm whether it needs one.
- `ga4.studio_page_path` mapped for 15 studios by reading `STUDIO_PAGE_SLUGS`' path text (e.g. "locations-florida-pinecrest" -> Pinecrest). 4 slugs (Austin - Domain, Houston, Los Angeles, San Diego) don't match any canonical studio -- likely pre-launch/unconfirmed, kept only as a fallback list in `fetch_ga4.py`, not written into `studios.json`. VERIFY the 15 path matches before merging.
- `google_ads.customer_id` (per-studio, for NSO scorecards) was only findable for **Herriman**. Other NSO studios' Google Ads Customer IDs are not recorded anywhere in the repo currently -- TODO: confirm whether they exist and should be added.
- `nso-dashboard/config/franchise_config.json` (Herriman-only, single entry) was left AS-IS, not migrated -- grepping the repo found no active script that actually reads this file at runtime (only docstring references), so it looks like a Phase-1 test artifact rather than live config. Regenerate it from studios.json later if a real consumer shows up.
- `nso-dashboard/scripts/create_nso_config_excel.py` (spreadsheet-generator tool, own 8-studio STUDIOS list) and the one-off scripts `migrate_herriman_events_spend.py` / `patch_reston_early_weeks.py` were left AS-IS -- manual/historical tools, not part of the recurring daily pipeline.
- **Madison** and **NYC - FiDi** are `status: open` (not in the default-excluded list) and have Snowflake data, but have NO Meta Ads config entry in `config-meta.yaml` -- same root-cause bug as the NSO studios, just for two established studios. Flagging since it wasn't in the original NSO-focused ask.
- **Music Row** is referenced (Meta code TN-001, Google Ads regex) but has NO `data.json` Snowflake entry -- likely pre-launch. Included in the registry so it's ready once it opens; `excluded_default`/`status` set to `nso` as a reasonable default, confirm before merging.
- **Huntsville** is referenced (Google Ads regex only, no Meta code) but has NO `data.json` Snowflake entry -- likely pre-launch, same treatment as Music Row.
- **Madison** and **NYC - FiDi** have no `code` anywhere in the repo (they were never assigned a Meta-style state-sequence code) -- TODO: assign one if/when they get wired into `config-meta.yaml`-style Meta spend tracking.
