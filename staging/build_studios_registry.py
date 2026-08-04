#!/usr/bin/env python3
"""
One-time migration script: reconcile every scattered per-studio config source
in the repo into a single canonical studios.json.

This is NOT part of the ongoing pipeline — run once, review studios_migration_report.md,
hand-fix any flagged TODOs, then commit the resulting studios.json to the repo.

Sources reconciled (see plan doc for full inventory):
  - data.json                              -> canonical `name` roster (Snowflake truth)
  - config-meta.yaml                       -> meta.match, code, state (established studios)
  - fetch_google_ads.py CAMPAIGN_STUDIO_MAP -> google_ads.match/pattern
  - index.html GOOGLE_STUDIO_ALIAS/META_CODE_TO_STUDIO -> alias resolution + extra codes
  - shared/utils.js DEFAULT_EXCL/NSO_STUDIOS/CLOSED_STUDIOS -> status/excluded_default
  - nso-dashboard/config/franchise_config.json -> meta/google_ads/ga4/gbp ids (Herriman)
  - nso-dashboard/scripts/fetch_gbp.py ALL_STUDIOS -> gbp.location_id
  - nso-dashboard/scripts/fetch_social_insights.py STUDIOS -> meta.page_id / instagram_account_id / social_slug
  - nso-dashboard/scripts/fetch_tier_rmr.py + fetch_nso_sales.py -> snowflake_id, tier_pricing
  - nso-dashboard/scripts/build_all_scorecards.py EVENTS_SPEND_STUDIO_MAP -> code cross-check
"""
import json

DEFAULTS = {
    "meta_ad_account_id": "act_1553887681409034",
    "google_ads_mcc_id": "605-546-2417",
    "ga4_property_id": "341934364",
    "gbp_account_id": "accounts/4243744174605320602",
}

# ---------------------------------------------------------------------------
# Canonical name roster - exact spelling from data.json (Snowflake source of truth)
# ---------------------------------------------------------------------------
CANONICAL_NAMES = [
    "Austin - Highland", "Austin - Zilker", "Aventura", "Boca Raton", "Charlotte - Noda",
    "Coral Gables", "Coral Springs", "Dallas - Prestonwood", "Dallas - Uptown",
    "Deerfield Beach", "Doral", "Dunwoody", "Eastchester", "Fort Lauderdale - Las Olas",
    "Fort Myers", "Herriman", "Madison", "Miami - Brickell", "Miami - Coconut Grove",
    "Miami - Midtown", "Miami - Upper East Side", "Miami Beach", "Miami Lakes",
    "Middletown", "Miramar", "NYC - Chelsea", "NYC - FiDi", "NYC - Park Slope",
    "Naples - Mercato", "Nashville - Capitol View", "North Miami", "Ocean Township",
    "Old Bridge", "Orlando - Dr Phillips", "Pembroke Pines", "Pinecrest - Palmetto Bay",
    "Reston", "South Miami", "Toms River", "Wall Township", "West Palm Beach",
    # Not yet in data.json (pre-launch / no Snowflake data yet) but referenced
    # elsewhere in the repo -> included so the registry can hold them too.
    "Music Row", "Huntsville",
]

# code -> (name, state) from config-meta.yaml (established/Meta-corp-account studios)
META_CONFIG = {
    "FL-001": ("Miami Beach", "FL", "Miami Beach"),
    "FL-002": ("Miami - Brickell", "FL", "Brickell"),
    "FL-003": ("Coral Gables", "FL", "Coral Gables"),
    "FL-004": ("Doral", "FL", "Doral"),
    "FL-005": ("Miami Lakes", "FL", "Miami Lakes"),
    "FL-006": ("Deerfield Beach", "FL", "Deerfield"),
    "FL-007": ("Miami - Upper East Side", "FL", "Upper East"),
    "FL-008": ("Coral Springs", "FL", "Coral Springs"),
    "FL-009": ("South Miami", "FL", "South Miami"),
    "FL-010": ("Miami - Midtown", "FL", "Midtown"),
    "FL-011": ("Miami - Coconut Grove", "FL", "Coconut Grove"),
    "FL-012": ("Miramar", "FL", "Miramar"),
    "FL-013": ("Fort Lauderdale - Las Olas", "FL", "Las Olas"),
    "FL-014": ("Pembroke Pines", "FL", "Pembroke"),
    "FL-015": ("West Palm Beach", "FL", "West Palm"),
    "FL-016": ("Boca Raton", "FL", "Boca"),
    "NC-001": ("Charlotte - Noda", "NC", "Charlotte"),
    "NJ-001": ("Toms River", "NJ", "Toms River"),
    "NJ-002": ("Ocean Township", "NJ", "Ocean Township"),
    "NJ-003": ("Wall Township", "NJ", "Wall"),
    "NY-002": ("NYC - Chelsea", "NY", "Chelsea"),
    "NY-003": ("NYC - Park Slope", "NY", "Park Slope"),
    "NY-004": ("Eastchester", "NY", "Eastchester"),
    "TX-001": ("Austin - Zilker", "TX", "Zilker"),
    "TX-002": ("Austin - Highland", "TX", "Highland"),
    "TX-003": ("Dallas - Prestonwood", "TX", "Prestonwood"),
    "FL-017": ("Pinecrest - Palmetto Bay", "FL", "Pinecrest"),
    "FL-019": ("Naples - Mercato", "FL", "Naples"),
}

# Extra codes found in index.html's META_CODE_TO_STUDIO but ABSENT from
# config-meta.yaml -> historical/baked Meta spend exists for these codes but
# the live fetch_meta_ads.py pipeline currently has no entry to keep producing
# fresh data. Preserving the code; `meta.match` is being added fresh as part
# of this migration to close the exact gap this whole project started from -
# FLAG for Santiago to confirm against real campaign/adset naming before merge.
META_CODE_GAPS = {
    "TN-001": ("Music Row", "TN", "Music Row"),   # was Meta-tracked historically, not live
    "VA-001": ("Reston", "VA", "Reston"),          # was Meta-tracked historically, not live
}

# google_ads.match/pattern derived from CAMPAIGN_STUDIO_MAP in fetch_google_ads.py,
# already translated to canonical names via GOOGLE_STUDIO_ALIAS (Naples Mercato ->
# Naples - Mercato, Dr Phillips -> Orlando - Dr Phillips, Pinecrest -> Pinecrest -
# Palmetto Bay, Capitol View -> Nashville - Capitol View, NYC - Financial District
# -> NYC - FiDi). `pattern` is set (true regex) only where the source used
# multi-token alternation; everything else is a plain substring `match`.
GOOGLE_ADS_MAP = {
    "Miramar": {"match": "iramar"},
    "NYC - FiDi": {"pattern": "FIDI|FiDi|Financial District|NYC|New York"},
    "NYC - Chelsea": {"match": "helsea"},
    "Miami - Brickell": {"match": "rickell"},
    "Miami Beach": {"pattern": "Sobe|Miami Beach|SoBe"},
    "Doral": {"match": "Doral"},
    "Coral Gables": {"match": "Gables"},
    "Deerfield Beach": {"match": "eerfield"},
    "Miami - Upper East Side": {"pattern": "pper|iscayne"},
    "Coral Springs": {"match": "Springs"},
    "Toms River": {"pattern": "River|Toms"},
    "Music Row": {"pattern": "usic Row|Music"},
    "Austin - Highland": {"match": "ighland"},
    "Austin - Zilker": {"pattern": "ilker|Zilker"},
    "Miami - Midtown": {"match": "idtown"},
    "Nashville - Capitol View": {"pattern": "ulch|apitol"},
    "Ocean Township": {"match": "cean"},
    "Charlotte - Noda": {"match": "NODA"},
    "South Miami": {"match": "South Miami"},
    "Miami - Coconut Grove": {"pattern": "oconut|Coconut|Grove|FL011"},
    "Madison": {"match": "adison"},
    "Miami Lakes": {"match": "Lakes"},
    "Fort Lauderdale - Las Olas": {"match": "Olas"},
    "Pembroke Pines": {"match": "embroke"},
    "Boca Raton": {"match": "Boca"},
    "West Palm Beach": {"match": "West Palm"},
    "Wall Township": {"match": "Wall"},
    "Eastchester": {"match": "astchester"},
    "NYC - Park Slope": {"match": "Slope"},
    "Dallas - Prestonwood": {"match": "Prestonwood"},
    "Reston": {"match": "Reston"},
    "Pinecrest - Palmetto Bay": {"match": "inecrest"},
    "Naples - Mercato": {"match": "Naples"},
    "Aventura": {"match": "Aventura"},
    "Herriman": {"match": "Herriman"},
    "Orlando - Dr Phillips": {"pattern": "Phillips|Dr.?\\s*Phillips"},
    # Pre-launch, no data.json/Snowflake entry yet (same as Music Row) -- kept
    # so existing Google Ads campaign matching isn't silently dropped.
    "Huntsville": {"match": "untsville"},
}

# status + excluded_default, from shared/utils.js
CLOSED_STUDIOS = {"Nashville - Capitol View"}
NSO_STUDIOS_UTILS = {
    "Aventura", "Dallas - Uptown", "Dunwoody", "Fort Myers", "Herriman", "Middletown",
    "Naples - Mercato", "North Miami", "Old Bridge", "Orlando - Dr Phillips", "Reston",
}
DEFAULT_EXCL_STUDIOS = NSO_STUDIOS_UTILS | CLOSED_STUDIOS

# snowflake_id + tier_pricing, from fetch_nso_sales.py NSO_STUDIOS (authoritative,
# 10 entries - superset of fetch_tier_rmr.py's 8-entry SNOWFLAKE_IDS, which is
# missing Dunwoody/Middletown; those two ARE present here) + tier pricing from
# fetch_tier_rmr.py STUDIO_PRICING (8 studios - Dunwoody/Middletown have no
# pricing config found anywhere -> left null, genuine gap, not guessed).
NSO_SNOWFLAKE = {
    "FL-019": 5751381, "UT-001": 5752080, "VA-001": 5750130, "FL-020": 5753281,
    "FL-018": 5753604, "FL-021": 5753608, "TX-004": 5753491, "NJ-004": 5753073,
    "GA-001": 5754676, "NJ-005": 5753113,
}
TIER_PRICING = {
    "FL-019": {"tier1_price": 99, "tier2_price": 129, "tier3_price": 149},
    "VA-001": {"tier0_price": 99, "tier1_price": 129, "tier2_price": 149},
    "UT-001": {"tier1_price": 99, "tier2_price": 129, "tier3_price": 149},
    "FL-020": {"tier1_price": 99, "tier2_price": 129, "tier3_price": 149},
    "FL-018": {"tier1_price": 129, "tier2_price": 149},
    "FL-021": {"tier1_price": 129, "tier2_price": 149},
    "TX-004": {"tier1_price": 129, "tier2_price": 149},
    "NJ-004": {"tier1_price": 99, "tier2_price": 129},
}
# code -> canonical name for the NSO-specific codes (from fetch_nso_sales.py,
# cross-checked against build_all_scorecards.py EVENTS_SPEND_STUDIO_MAP)
NSO_CODE_NAME = {
    "FL-019": "Naples - Mercato", "UT-001": "Herriman", "VA-001": "Reston",
    "FL-020": "Orlando - Dr Phillips", "FL-018": "Aventura", "FL-021": "North Miami",
    "TX-004": "Dallas - Uptown", "NJ-004": "Old Bridge", "GA-001": "Dunwoody",
    "NJ-005": "Middletown",
    "FL-022": "Fort Myers",  # code exists in build_all_scorecards.py but NOT in
                              # fetch_nso_sales.py's NSO_STUDIOS -> no snowflake_id found anywhere
}

# meta.page_id / instagram_account_id / social_slug, from fetch_social_insights.py
# STUDIOS. Aliased to canonical names (this file uses shorthand names like
# "South Beach", "Brickell", "FiDi", "Chelsea", "Wall NJ", "Las Olas" etc.)
SOCIAL_ALIAS_TO_CANONICAL = {
    "Coral Gables": "Coral Gables", "Dallas - Prestonwood": "Dallas - Prestonwood",
    "Toms River": "Toms River", "South Beach": "Miami Beach", "North Miami": "North Miami",
    "Austin - Highland": "Austin - Highland", "Miami Lakes": "Miami Lakes",
    "Aventura": "Aventura", "Eastchester": "Eastchester", "Boca Raton": "Boca Raton",
    "Midtown Miami": "Miami - Midtown", "Orlando - Dr. Phillips": "Orlando - Dr Phillips",
    "Dallas - Uptown": "Dallas - Uptown", "Herriman": "Herriman", "Pinecrest": "Pinecrest - Palmetto Bay",
    "Austin - Zilker": "Austin - Zilker", "Coral Springs": "Coral Springs",
    "South Miami": "South Miami", "Deerfield Beach": "Deerfield Beach", "Doral": "Doral",
    "Brooklyn - Park Slope": "NYC - Park Slope", "West Palm Beach": "West Palm Beach",
    "Coconut Grove": "Miami - Coconut Grove", "Charlotte - NoDa": "Charlotte - Noda",
    "Ocean Township": "Ocean Township", "Upper East Side": "Miami - Upper East Side",
    "Brickell": "Miami - Brickell", "Reston": "Reston", "Wall NJ": "Wall Township",
    "Chelsea": "NYC - Chelsea", "Las Olas": "Fort Lauderdale - Las Olas", "Miramar": "Miramar",
    "Pembroke Pines": "Pembroke Pines", "FiDi": "NYC - FiDi", "Madison": "Madison",
    "Old Bridge": "Old Bridge", "Dunwoody": "Dunwoody", "Middletown": "Middletown",
    # "Corporate" entry intentionally skipped -> not a studio
}
SOCIAL_STUDIOS_RAW = [
    ("Coral Gables", "gables", "110268611810389", None),
    ("Dallas - Prestonwood", "prestonwood", "845182982009071", None),
    ("Toms River", "tomsriver", "108238962107956", None),
    ("South Beach", "sobe", "105547208952141", None),
    ("North Miami", "northmiami", "1145229115329264", None),
    ("Austin - Highland", "highland", "351629338025804", None),
    ("Miami Lakes", "miamilakes", "101752329601099", None),
    ("Aventura", "aventura", "1047698415096383", None),
    ("Eastchester", "eastchester", "664055870131827", None),
    ("Boca Raton", "boca", "637367179456983", None),
    ("Midtown Miami", "midtown", "103476569380316", None),
    ("Orlando - Dr. Phillips", "drphillips", "986634234541338", None),
    ("Dallas - Uptown", "uptown", "1013504171849728", None),
    ("Herriman", "herriman", "1016504601542354", None),
    ("Pinecrest", "pinecrest", "848877064975048", None),
    ("Austin - Zilker", "zilker", "119087484495208", None),
    ("Coral Springs", "coralsprings", "106485985557697", None),
    ("South Miami", "southmiami", "116631111441913", None),
    ("Deerfield Beach", "deerfield", "106597632212836", None),
    ("Doral", "doral", "103789732469470", None),
    ("Brooklyn - Park Slope", "parkslope", "681591261709097", None),
    ("West Palm Beach", "westpalm", "703238786198886", None),
    ("Coconut Grove", "coconutgrove", "196520916880971", None),
    ("Charlotte - NoDa", "noda", "104198619263881", None),
    ("Ocean Township", "oceantownship", "184923338027883", None),
    ("Upper East Side", "uppereastside", "108861828669519", None),
    ("Brickell", "brickell", "107873258720021", None),
    ("Reston", "reston", "875200972337017", None),
    ("Wall NJ", "wallnj", "700746796454324", None),
    ("Chelsea", "chelsea", "105456357683242", None),
    ("Las Olas", "lasolas", "300173986520471", None),
    ("Miramar", "miramar", "203760659484865", None),
    ("Pembroke Pines", "pembrokepines", "328512683684059", None),
    ("FiDi", "fidi", "149250091597748", None),
    ("Madison", "madison", "111726744769276", None),
    ("Old Bridge", "oldbridge", None, "17841439161726674"),
    ("Dunwoody", "dunwoody", "1119194191285831", "17841422592958602"),
    ("Middletown", "middletown", "1138263712703066", "17841434822163164"),
]

# gbp.location_id, from fetch_gbp.py ALL_STUDIOS (aliased "SWEAT440 X" -> canonical)
GBP_ALIAS_TO_CANONICAL = {
    "Aventura": "Aventura", "Boca Raton": "Boca Raton", "Coral Gables": "Coral Gables",
    "Coral Springs": "Coral Springs", "Deerfield Beach": "Deerfield Beach", "Doral": "Doral",
    "Fort Lauderdale - Las Olas": "Fort Lauderdale - Las Olas", "Fort Myers": "Fort Myers",
    "Miami Beach": "Miami Beach", "Miami - Brickell": "Miami - Brickell",
    "Miami - Coconut Grove": "Miami - Coconut Grove", "Miami Lakes": "Miami Lakes",
    "Miami - Midtown": "Miami - Midtown", "Miami - Upper East Side": "Miami - Upper East Side",
    "Miramar": "Miramar", "Naples - Mercato": "Naples - Mercato", "North Miami": "North Miami",
    "Orlando - Dr Phillips": "Orlando - Dr Phillips", "Pembroke Pines": "Pembroke Pines",
    "Pinecrest - Palmetto Bay": "Pinecrest - Palmetto Bay", "South Miami": "South Miami",
    "West Palm Beach": "West Palm Beach", "NYC - Chelsea": "NYC - Chelsea",
    "NYC - FiDi": "NYC - FiDi", "NYC - Park Slope": "NYC - Park Slope",
    "Eastchester": "Eastchester", "Middletown": "Middletown", "Ocean Township": "Ocean Township",
    "Old Bridge": "Old Bridge", "Toms River": "Toms River", "Wall Township": "Wall Township",
    "Austin - Highland": "Austin - Highland", "Austin - Zilker": "Austin - Zilker",
    "Dallas - Prestonwood": "Dallas - Prestonwood", "Dallas - Uptown": "Dallas - Uptown",
    "Reston": "Reston", "Herriman": "Herriman", "Charlotte - NoDa": "Charlotte - Noda",
    "Nashville - Capitol View": "Nashville - Capitol View", "Dunwoody": "Dunwoody",
    "Madison": "Madison",
}
# (canonical_alias, location_id, gbp_code) — gbp_code is fetch_gbp.py's OWN
# code scheme (e.g. "S440-Boca"), DISTINCT from the Meta/Google state-sequence
# `code` (e.g. "FL-016") — nso-studios.html joins on this scheme, so it's
# preserved as `gbp.code` rather than collapsed into the main `code` field.
GBP_STUDIOS_RAW = [
    ("Aventura", "", ""), ("Boca Raton", "7065200393670588135", "S440-Boca"),
    ("Coral Gables", "7463859448263219148", "S440-Gables"),
    ("Coral Springs", "664231527795610789", "S440-CoralSprings"),
    ("Deerfield Beach", "10754559321713930787", "S440-Deerfield"),
    ("Doral", "5492541826748651334", "S440-Doral"),
    ("Fort Lauderdale - Las Olas", "15716475017336552276", "S440-LasOlas"),
    ("Fort Myers", "2005684758562901799", "S440-FortMyers"),
    ("Miami Beach", "7903117717083019565", "S440-SOBE"),
    ("Miami - Brickell", "14204655201727465322", "S440-Brickell"),
    ("Miami - Coconut Grove", "13239535872064474502", "S440-Grove"),
    ("Miami Lakes", "17771088988285686232", "S440-Lakes"),
    ("Miami - Midtown", "7167540952370862788", "S440-Midtown"),
    ("Miami - Upper East Side", "10716690281924579206", "S440-UES"),
    ("Miramar", "17466150247466580313", "S440-Miramar"),
    ("Naples - Mercato", "9241286551304249574", "S440-Naples"),
    ("North Miami", "", ""),
    ("Orlando - Dr Phillips", "11294882594993712026", "S440-Orlando"),
    ("Pembroke Pines", "7667757151493569095", "S440-Pines"),
    ("Pinecrest - Palmetto Bay", "13145255458617855723", "S440-Pinecrest"),
    ("South Miami", "6035103980871581769", "S440-SouthMiami"),
    ("West Palm Beach", "17821267300280087598", "S440-WPB"),
    ("NYC - Chelsea", "17441960021947392889", "S440-Chelsea"),
    ("NYC - FiDi", "2621266453224563061", "S440-FIDI"),
    ("NYC - Park Slope", "17704049939806391312", "S440-ParkSlope"),
    ("Eastchester", "9100379360747055617", "S440-Eastchester"),
    ("Middletown", "9688833394650228159", "S440-Middletown"),
    ("Ocean Township", "14043102866859948554", "S440-OceanTownship"),
    ("Old Bridge", "", ""),
    ("Toms River", "11096005039049334458", "S440-TomsRiver"),
    ("Wall Township", "8536971399907740515", "S440-WallTownship"),
    ("Austin - Highland", "1169708896465579865", "S440-Highland"),
    ("Austin - Zilker", "13711200876115787193", "S440-Zilker"),
    ("Dallas - Prestonwood", "11402535545027699120", "S440-Prestonwood"),
    ("Dallas - Uptown", "", ""),
    ("Reston", "10767130387921211013", "S440-Reston"),
    ("Herriman", "4243744174605320602", "S440-Herriman"),
    ("Charlotte - NoDa", "13151717982539622083", "S440-NoDa"),
    ("Nashville - Capitol View", "", "S440-CapitolView"),
    ("Dunwoody", "14348234584447062751", "S440-Dunwoody"),
    ("Madison", "8346193268583733484", "S440-Madison"),
]

# Herriman-only full bundle from nso-dashboard/config/franchise_config.json
FRANCHISE_CONFIG_HERRIMAN = {
    "ga4_studio_page_path": "/gyms/utah-herriman/",
    "gbp_account_id": "accounts/4243744174605320602",
    "google_ads_customer_id": "385-801-4125",
}

# ga4.studio_page_path, from fetch_ga4.py's STUDIO_PAGE_SLUGS (flat, no name
# key in the source -- hand-matched here by reading the slug text; each is
# unambiguous - e.g. "locations-florida-pinecrest" -> Pinecrest). 4 of the
# original 20 slugs (Austin - Domain, Houston, Los Angeles, San Diego) don't
# correspond to any known canonical studio -- likely pre-launch/unconfirmed,
# left OUT of studios.json (same treatment as Huntsville/Music Row would get
# once confirmed) and handled as a separate fallback list in fetch_ga4.py.
GA4_PAGE_MAP = {
    "Pinecrest - Palmetto Bay": "/gyms/locations-florida-pinecrest/",
    "Doral": "/gyms/locations-florida-doral/",
    "Miami Beach": "/gyms/locations-florida-miami-beach/",
    "Miami - Brickell": "/gyms/locations-florida-brickell/",
    "Coral Gables": "/gyms/locations-florida-coral-gables/",
    "Aventura": "/gyms/locations-florida-aventura/",
    "Fort Lauderdale - Las Olas": "/gyms/locations-florida-ft-lauderdale/",
    "Pembroke Pines": "/gyms/locations-florida-pembroke-pines/",
    "Boca Raton": "/gyms/locations-florida-boca-raton/",
    "West Palm Beach": "/gyms/locations-florida-west-palm-beach/",
    "Orlando - Dr Phillips": "/gyms/locations-florida-orlando/",
    "Naples - Mercato": "/gyms/locations-florida-naples-mercato/",
    "Austin - Highland": "/gyms/locations-texas-austin-highland/",
    "Dallas - Prestonwood": "/gyms/locations-texas-dallas-prestonwood/",
    "Reston": "/gyms/virginia-reston/",
    "Herriman": "/gyms/utah-herriman/",
}
# Not resolvable to any canonical studio -- pre-launch/unconfirmed, kept only
# as a documented fallback list in fetch_ga4.py, not written into studios.json.
GA4_PAGE_UNMAPPED_PRELAUNCH = [
    "/gyms/locations-texas-austin-domain/",
    "/gyms/locations-texas-houston/",
    "/gyms/locations-california-los-angeles/",
    "/gyms/locations-california-san-diego/",
]

STATE_BY_CODE_PREFIX = {}  # filled in below


def build():
    studios = {name: {"name": name} for name in CANONICAL_NAMES}

    def get(name):
        return studios.setdefault(name, {"name": name})

    # 1) codes/state/meta.match from config-meta.yaml
    for code, (name, state, match) in META_CONFIG.items():
        s = get(name)
        s["code"] = code
        s["state"] = state
        s.setdefault("meta", {})["match"] = match

    # 2) historical-only Meta codes (Reston, Music Row) - flagged gap, match added fresh
    migration_notes = []
    for code, (name, state, match) in META_CODE_GAPS.items():
        s = get(name)
        s["code"] = code
        s["state"] = state
        s.setdefault("meta", {})["match"] = match
        migration_notes.append(
            f"- **{name}** ({code}): had historical/baked Meta spend but no live "
            f"`config-meta.yaml` entry. Added `meta.match=\"{match}\"` fresh as part of "
            f"this migration -- VERIFY against real ad/campaign naming before merging."
        )

    # 3) Google Ads match/pattern
    for name, cfg in GOOGLE_ADS_MAP.items():
        s = get(name)
        s.setdefault("google_ads", {}).update(cfg)

    # 4) status + excluded_default
    for name, s in studios.items():
        if name in CLOSED_STUDIOS:
            s["status"] = "closed"
        elif name in NSO_STUDIOS_UTILS:
            s["status"] = "nso"
        else:
            s["status"] = "open"
        s["excluded_default"] = name in DEFAULT_EXCL_STUDIOS

    # 5) NSO codes + snowflake_id + tier_pricing, keyed by NSO code -> resolve name
    # (bug fix during review: earlier draft resolved snowflake_id/tier_pricing by
    # code but never actually assigned the `code` field itself to these studios)
    STATE_BY_CODE_PREFIX = {
        "FL": "FL", "TX": "TX", "NJ": "NJ", "NY": "NY", "GA": "GA", "UT": "UT",
        "VA": "VA", "NC": "NC", "TN": "TN", "AL": "AL",
    }
    for code, name in NSO_CODE_NAME.items():
        s = get(name)
        s["code"] = s.get("code") or code
        if not s.get("state"):
            prefix = code.split("-")[0]
            s["state"] = STATE_BY_CODE_PREFIX.get(prefix)
    for code, sf_id in NSO_SNOWFLAKE.items():
        name = NSO_CODE_NAME.get(code)
        if name:
            get(name)["snowflake_id"] = sf_id
    for code, pricing in TIER_PRICING.items():
        name = NSO_CODE_NAME.get(code)
        if name:
            get(name)["tier_pricing"] = pricing

    # Fort Myers: code/state already set via NSO_CODE_NAME (FL-022) above;
    # snowflake_id genuinely not found anywhere -> stays null. social_slug
    # ("fortmyers") comes from build_all_scorecards.py's IG_SOCIAL_CODE, not
    # fetch_social_insights.py's STUDIOS (which doesn't list Fort Myers at all).
    fm = get("Fort Myers")
    fm["snowflake_id"] = None
    fm["social_slug"] = "fortmyers"
    migration_notes.append(
        "- **Fort Myers** (FL-022): present in `data.json` (has Snowflake data) but no "
        "`snowflake_id` found in `fetch_nso_sales.py`/`fetch_tier_rmr.py` -- TODO: look up "
        "the real Snowflake `studio_id` and fill in `snowflake_id` (currently `null`)."
    )
    # Dunwoody/Middletown: have snowflake_id but no tier_pricing anywhere
    for name in ("Dunwoody", "Middletown"):
        s = get(name)
        if "tier_pricing" not in s:
            s["tier_pricing"] = None
            migration_notes.append(
                f"- **{name}**: has a `snowflake_id` but no `tier_pricing` found in "
                f"`fetch_tier_rmr.py` STUDIO_PRICING -- TODO: confirm whether it needs one."
            )

    # 6) social insights (meta.page_id / instagram_account_id / social_slug)
    for raw_name, slug, page_id, ig_id in SOCIAL_STUDIOS_RAW:
        canonical = SOCIAL_ALIAS_TO_CANONICAL.get(raw_name)
        if not canonical:
            continue
        s = get(canonical)
        meta = s.setdefault("meta", {})
        if page_id:
            meta["page_id"] = page_id
        if ig_id:
            meta["instagram_account_id"] = ig_id
        s["social_slug"] = slug

    # 7) GBP location_id + gbp-specific code
    for raw_name, loc_id, gbp_code in GBP_STUDIOS_RAW:
        canonical = GBP_ALIAS_TO_CANONICAL.get(raw_name)
        if not canonical:
            continue
        s = get(canonical)
        gbp = s.setdefault("gbp", {})
        gbp["location_id"] = (loc_id or None)
        if gbp_code:
            gbp["code"] = gbp_code

    # 8) GA4 studio page paths, hand-matched from STUDIO_PAGE_SLUGS (see GA4_PAGE_MAP)
    for name, path in GA4_PAGE_MAP.items():
        get(name).setdefault("ga4", {})["studio_page_path"] = path
    migration_notes.append(
        "- `ga4.studio_page_path` mapped for 15 studios by reading `STUDIO_PAGE_SLUGS`' path "
        "text (e.g. \"locations-florida-pinecrest\" -> Pinecrest). 4 slugs (Austin - Domain, "
        "Houston, Los Angeles, San Diego) don't match any canonical studio -- likely "
        "pre-launch/unconfirmed, kept only as a fallback list in `fetch_ga4.py`, not written "
        "into `studios.json`. VERIFY the 15 path matches before merging."
    )

    # Herriman's franchise_config.json bundle also has a per-studio Google Ads
    # Customer ID -- not findable for any other NSO studio anywhere in the repo.
    herriman = get("Herriman")
    herriman.setdefault("google_ads", {})["customer_id"] = FRANCHISE_CONFIG_HERRIMAN["google_ads_customer_id"]
    migration_notes.append(
        "- `google_ads.customer_id` (per-studio, for NSO scorecards) was only findable for "
        "**Herriman**. Other NSO studios' Google Ads Customer IDs are not recorded anywhere "
        "in the repo currently -- TODO: confirm whether they exist and should be added."
    )
    migration_notes.append(
        "- `nso-dashboard/config/franchise_config.json` (Herriman-only, single entry) was left "
        "AS-IS, not migrated -- grepping the repo found no active script that actually reads "
        "this file at runtime (only docstring references), so it looks like a Phase-1 test "
        "artifact rather than live config. Regenerate it from studios.json later if a real "
        "consumer shows up."
    )
    migration_notes.append(
        "- `nso-dashboard/scripts/create_nso_config_excel.py` (spreadsheet-generator tool, "
        "own 8-studio STUDIOS list) and the one-off scripts `migrate_herriman_events_spend.py` "
        "/ `patch_reston_early_weeks.py` were left AS-IS -- manual/historical tools, not part "
        "of the recurring daily pipeline."
    )
    migration_notes.append(
        "- **Madison** and **NYC - FiDi** are `status: open` (not in the default-excluded "
        "list) and have Snowflake data, but have NO Meta Ads config entry in "
        "`config-meta.yaml` -- same root-cause bug as the NSO studios, just for two "
        "established studios. Flagging since it wasn't in the original NSO-focused ask."
    )
    migration_notes.append(
        "- **Music Row** is referenced (Meta code TN-001, Google Ads regex) but has NO "
        "`data.json` Snowflake entry -- likely pre-launch. Included in the registry so it's "
        "ready once it opens; `excluded_default`/`status` set to `nso` as a reasonable default, "
        "confirm before merging."
    )
    get("Music Row")["status"] = "nso"
    get("Music Row")["excluded_default"] = True
    get("Huntsville")["status"] = "nso"
    get("Huntsville")["excluded_default"] = True
    get("Huntsville")["state"] = "AL"
    migration_notes.append(
        "- **Huntsville** is referenced (Google Ads regex only, no Meta code) but has NO "
        "`data.json` Snowflake entry -- likely pre-launch, same treatment as Music Row."
    )

    # Madison (Alabama, per fetch_gbp.py's section comment) and NYC - FiDi:
    # state is knowable even though no code exists anywhere in the repo.
    get("Madison")["state"] = "AL"
    get("NYC - FiDi")["state"] = "NY"
    migration_notes.append(
        "- **Madison** and **NYC - FiDi** have no `code` anywhere in the repo (they were "
        "never assigned a Meta-style state-sequence code) -- TODO: assign one if/when they "
        "get wired into `config-meta.yaml`-style Meta spend tracking."
    )

    # finalize: sort keys for stable diffs, drop the temp dict wrapper
    out_studios = []
    for name in sorted(studios.keys()):
        s = studios[name]
        s.setdefault("code", None)
        s.setdefault("state", None)
        s.setdefault("status", "open")
        s.setdefault("excluded_default", False)
        s.setdefault("meta", {})
        s.setdefault("google_ads", {})
        s.setdefault("ga4", {})
        s.setdefault("gbp", {})
        s.setdefault("snowflake_id", None)
        s.setdefault("social_slug", None)
        s.setdefault("tier_pricing", None)
        # order keys nicely
        ordered = {
            "name": s["name"], "code": s["code"], "state": s["state"], "status": s["status"],
            "excluded_default": s["excluded_default"], "meta": s["meta"],
            "google_ads": s["google_ads"], "ga4": s["ga4"], "gbp": s["gbp"],
            "snowflake_id": s["snowflake_id"], "social_slug": s["social_slug"],
            "tier_pricing": s["tier_pricing"],
        }
        out_studios.append(ordered)

    registry = {"defaults": DEFAULTS, "studios": out_studios}
    return registry, migration_notes


if __name__ == "__main__":
    registry, notes = build()
    with open("studios.json", "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")

    report = ["# studios.json migration report\n",
              f"\nBuilt {len(registry['studios'])} studio entries.\n",
              "\n## Flags / TODOs for review before merging\n\n"]
    report.extend(n + "\n" for n in notes)
    with open("studios_migration_report.md", "w", encoding="utf-8") as f:
        f.writelines(report)

    print(f"Wrote studios.json with {len(registry['studios'])} studios.")
    print(f"Wrote studios_migration_report.md with {len(notes)} flagged items.")
