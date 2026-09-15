"""
Candidate claim retrieval.

Two channels:
  A. Google Fact Check Tools API (needs GOOGLE_FACTCHECK_API_KEY, see .env.example)
  B. Direct crawl of Misbar's own listing API for its Lebanon-conflict tag

This script produces a pool of *candidate* fact-check records, deduplicated
by URL and filtered to the study's date window (review_date only, not
claim_date -- see docs/Codebook_v1.1.docx Section 1.2). It does not decide
which candidates are genuinely about the 2026 Lebanon conflict, merge
multiple fact-checks of the same underlying claim, or assign a
manipulation-type code -- those are human-coding steps described in the
codebook (Sections 1.3-1.4 and 4.1) and applied to produce data/claims.csv
and data/factchecks.csv.

Re-running this script will not reproduce data/claims.csv exactly: it
depends on live API/site state (URLs, ratings, and site structure can
change), and the coding step that turns raw candidates into the frozen
corpus is not automated. It is included so the retrieval method itself is
transparent and re-runnable, not so the whole corpus can be regenerated
unattended.

Usage:
    python 01_collect_candidates.py

Output:
    raw_candidates_<YYYYMMDD>.csv (in the current directory)
"""
import os
import sys
import time
import json
import csv
from datetime import datetime
from urllib.parse import unquote

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GOOGLE_FACTCHECK_API_KEY")
if not API_KEY:
    raise SystemExit(
        "GOOGLE_FACTCHECK_API_KEY not set. Copy .env.example to .env and add your own key."
    )

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

QUERIES_EN = ["Lebanon", "Hezbollah", "Beirut", "Southern Lebanon"]
QUERIES_AR = ["لبنان", "حزب الله", "بيروت"]
MISBAR_LEBANON_WAR_TAG_ID = "2141"

WINDOW_START = datetime(2026, 3, 1)
WINDOW_END = datetime(2026, 9, 13, 23, 59, 59)

RETRIEVED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def google_factcheck_search(query, language_code):
    results = []
    page_token = None
    while True:
        params = {"query": query, "languageCode": language_code, "pageSize": 50, "key": API_KEY}
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(
            "https://factchecktools.googleapis.com/v1alpha1/claims:search",
            params=params, timeout=20,
        )
        if r.status_code != 200:
            print(f"  [warn] {language_code}/{query}: HTTP {r.status_code}")
            break
        data = r.json()
        for claim in data.get("claims", []):
            for review in claim.get("claimReview", []):
                publisher = review.get("publisher", {}) or {}
                results.append({
                    "retrieval_source": "google_api",
                    "search_term": query,
                    "search_language": language_code,
                    "claim_text": claim.get("text", ""),
                    "claimant": claim.get("claimant", ""),
                    "claim_date": claim.get("claimDate", ""),
                    "publisher": publisher.get("name") or publisher.get("site", ""),
                    "language": review.get("languageCode", ""),
                    "rating": review.get("textualRating", ""),
                    "review_date": review.get("reviewDate", ""),
                    "title": review.get("title", ""),
                    "url": review.get("url", ""),
                    "retrieved_at": RETRIEVED_AT,
                })
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.2)
    return results


def misbar_tag_crawl(tag_id, page_size=20, max_pages=25):
    """Paginate Misbar's own listing API for a given tag id. Only rows with
    typeKey == "factcheck" are kept (drops editorial/analysis pieces)."""
    results = []
    for page in range(max_pages):
        params = {
            "page": page,
            "limit": page_size,
            "conditions": json.dumps([{"field_tags": tag_id}]),
            "styles": "large_425x240,medium_335x190",
            "vertical_image": "small_scale_180,small_scale_190",
        }
        r = requests.get(
            "https://www.misbar.com/ar/api/listing/node",
            params=params, headers=HEADERS, timeout=20,
        )
        if r.status_code != 200:
            print(f"  [warn] misbar page {page}: HTTP {r.status_code}")
            break
        items = r.json().get("items", [])
        if not items:
            break
        for it in items:
            if it.get("typeKey") != "factcheck":
                continue
            results.append({
                "retrieval_source": "direct_crawl_ar",
                "search_term": f"misbar tag {tag_id}",
                "search_language": "ar",
                "claim_text": it.get("claim", ""),
                "claimant": "",
                "claim_date": "",
                "publisher": "Misbar",
                "language": "ar",
                "rating": it.get("result_type", ""),
                "review_date": it.get("datePublished", ""),
                "title": it.get("title", ""),
                "url": "https://www.misbar.com" + it.get("alias", ""),
                "retrieved_at": RETRIEVED_AT,
            })
        time.sleep(0.3)
    return results


def normalize_url(u):
    return unquote(u or "").strip().lower().rstrip("/")


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def main():
    all_results = []

    print("Channel A: Google Fact Check Tools API")
    for q in QUERIES_EN:
        r = google_factcheck_search(q, "en")
        print(f"  en / {q}: {len(r)} reviews")
        all_results.extend(r)
    for q in QUERIES_AR:
        r = google_factcheck_search(q, "ar")
        print(f"  ar / {q}: {len(r)} reviews")
        all_results.extend(r)

    print("\nChannel B: direct fact-checker crawl")
    r = misbar_tag_crawl(MISBAR_LEBANON_WAR_TAG_ID)
    print(f"  Misbar tag {MISBAR_LEBANON_WAR_TAG_ID}: {len(r)} fact-checks")
    all_results.extend(r)

    seen = set()
    deduped = []
    for row in all_results:
        key = normalize_url(row["url"])
        if key and key not in seen:
            seen.add(key)
            deduped.append(row)
    print(f"\nTotal raw rows: {len(all_results)} | after URL dedup: {len(deduped)}")

    in_window = []
    for row in deduped:
        d = parse_date(row.get("review_date"))
        if d is not None and WINDOW_START <= d <= WINDOW_END:
            in_window.append(row)
    print(f"In study window ({WINDOW_START.date()} to {WINDOW_END.date()}, by review_date): {len(in_window)}")
    print("This is a count of unique fact-check URLs, not unique claims or topically-eligible "
          "claims -- both still require human triage per the codebook.")

    out_path = f"raw_candidates_{datetime.now().strftime('%Y%m%d')}.csv"
    fieldnames = list(in_window[0].keys()) if in_window else [
        "retrieval_source", "search_term", "search_language", "claim_text", "claimant",
        "claim_date", "publisher", "language", "rating", "review_date", "title", "url", "retrieved_at",
    ]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(in_window)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
