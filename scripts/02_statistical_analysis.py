"""
Reproduces every descriptive statistic reported in the paper's Results
section and Table 1 from the four data files in ../data/:
claims.csv, factchecks.csv, newsroom_search_log.csv, newsroom_coverage.csv.

Covers: corpus composition (Table 1), fine-grained and grouped
manipulation-type distribution with Wilson 95% confidence intervals,
the three Misbar sensitivity analyses, and newsroom-penetration statistics.

Usage:
    python 02_statistical_analysis.py
"""
import sys
import csv
import math
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = "../data"
Z_95 = 1.959963985

BUCKET = {
    "recycled old content": "authentic-content misuse",
    "recycled old content + audio-manipulated": "authentic-content misuse",
    "false context / wrong location": "authentic-content misuse",
    "AI-generated": "AI-related",
    "AI-manipulated": "AI-related",
    "fabricated quote": "other",
    "fabricated document": "other",
    "other": "other",
}

# Same real organization can appear under different literal name strings
# across records (Google API vs. direct-crawl vs. Arabic self-reporting).
CANONICAL_PUB = {
    "misbar.com": "Misbar", "misbar": "Misbar", "موقع مسبار": "Misbar",
    "misbar (via al arabiya tv)": "Misbar",
    "afp fact check": "AFP", "afp fact check (afp indonesia)": "AFP", "afp fact check arabic": "AFP",
    "في ميزان فرانس برس": "AFP",
    "verify sy": "Verify-Sy", "verify-sy": "Verify-Sy", "تأكد": "Verify-Sy",
    "منصة \"تأكد\"": "Verify-Sy",
    "التقنية من اجل السلام": "Tech4Peace",
    "مسند": "Musnad",
    "\"إعلاميون من أجل صحافة استقصائية عربية (أريج)\"": "ARIJ",
}


def canon_pub(pub):
    return CANONICAL_PUB.get((pub or "").strip().lower(), (pub or "").strip())


def is_misbar(pub):
    return canon_pub(pub) == "Misbar"


def wilson_ci(x, n, z=Z_95):
    if n == 0:
        return (float("nan"), float("nan"))
    p = x / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def pct_row(label, x, n):
    lo, hi = wilson_ci(x, n)
    pct = f"{100*x/n:.1f}%" if n else "n/a"
    ci = f"[{100*lo:.1f}%, {100*hi:.1f}%]" if n else "n/a"
    return label, x, n, pct, ci


def read_csv(name):
    with open(f"{DATA_DIR}/{name}", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    claims = {r["claim_id"]: r for r in read_csv("claims.csv")}
    factchecks = read_csv("factchecks.csv")
    search_log = read_csv("newsroom_search_log.csv")
    n_total = len(claims)

    fc_by_claim = defaultdict(list)
    for r in factchecks:
        fc_by_claim[r["claim_id"]].append(r)

    # ---- Table 1: corpus characteristics ----
    lang_counts = Counter((c["observed_claim_languages"] or "").strip() for c in claims.values())
    misbar_claim_ids = {cid for cid, fcs in fc_by_claim.items() if any(is_misbar(fc["publisher"]) for fc in fcs)}
    non_misbar_only_ids = [cid for cid in claims if any(not is_misbar(fc["publisher"]) for fc in fc_by_claim.get(cid, []))]
    zero_misbar_ids = [cid for cid in claims if not any(is_misbar(fc["publisher"]) for fc in fc_by_claim.get(cid, []))]

    print("=== Table 1: Corpus characteristics ===")
    print(f"Unique claims: {n_total}")
    print(f"Fact-check records: {len(factchecks)}")
    print(f"Arabic-language claims: {lang_counts.get('ar', 0)} ({100*lang_counts.get('ar', 0)/n_total:.1f}%)")
    print(f"English-language claims: {lang_counts.get('en', 0)} ({100*lang_counts.get('en', 0)/n_total:.1f}%)")
    print(f"Both languages: {lang_counts.get('ar, en', 0)} ({100*lang_counts.get('ar, en', 0)/n_total:.1f}%)")
    print(f"Claims involving Misbar: {len(misbar_claim_ids)} ({100*len(misbar_claim_ids)/n_total:.1f}%)")
    print(f"Claims with >=1 non-Misbar fact-check: {len(non_misbar_only_ids)} ({100*len(non_misbar_only_ids)/n_total:.1f}%)")
    print(f"Claims with no Misbar involvement: {len(zero_misbar_ids)} ({100*len(zero_misbar_ids)/n_total:.1f}%)")

    # ---- Manipulation-type distribution ----
    manip_counts = Counter(c["manipulation_type"] for c in claims.values())
    group_counts = Counter(BUCKET[c["manipulation_type"]] for c in claims.values())

    print("\n=== Fine-grained manipulation type (N=%d) ===" % n_total)
    for cat, n in manip_counts.most_common():
        print(pct_row(cat, n, n_total))

    print("\n=== Grouped manipulation type ===")
    for cat, n in group_counts.most_common():
        print(pct_row(cat, n, n_total))

    # ---- Robustness: sensitivity to Misbar representation ----
    def robustness_table(ids):
        c = Counter(BUCKET[claims[cid]["manipulation_type"]] for cid in ids)
        n = len(ids)
        return {cat: pct_row(cat, c.get(cat, 0), n) for cat in ("authentic-content misuse", "AI-related", "other")}

    print(f"\n=== Robustness: full corpus (N={n_total}) ===")
    for v in robustness_table(list(claims.keys())).values():
        print(v)
    print(f"\n=== Robustness: >=1 non-Misbar fact-check (N={len(non_misbar_only_ids)}) ===")
    for v in robustness_table(non_misbar_only_ids).values():
        print(v)
    print(f"\n=== Robustness: zero Misbar involvement (N={len(zero_misbar_ids)}) ===")
    for v in robustness_table(zero_misbar_ids).values():
        print(v)

    # ---- Newsroom penetration ----
    pen_counts = Counter(int(r["penetration_code"]) for r in search_log)
    n_pen2 = pen_counts.get(2, 0)
    n_major = sum(1 for r in search_log if int(r["penetration_code"]) == 2 and r["major_international"] == "Yes")
    print("\n=== Newsroom penetration ===")
    print(pct_row("penetration_code=2 (presented/relied on as factual)", n_pen2, len(search_log)))
    print(pct_row("major_international_outlet penetration", n_major, len(search_log)))

    # ---- Source composition ----
    pub_fc_counts = Counter(canon_pub(r["publisher"]) for r in factchecks)
    pub_claims = defaultdict(set)
    for r in factchecks:
        pub_claims[canon_pub(r["publisher"])].add(r["claim_id"])
    print("\n=== Source composition ===")
    for pub, n in pub_fc_counts.most_common():
        print(f"  {pub}: {n} fact-checks, {len(pub_claims[pub])} unique claims "
              f"({100*len(pub_claims[pub])/n_total:.1f}% of corpus)")


if __name__ == "__main__":
    main()
