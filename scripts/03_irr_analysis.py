"""
Inter-rater reliability for the 28-claim blinded sample, reading
../data/irr_sample.csv (claim_id, coder1_manipulation_type,
coder2_manipulation_type).

Reports raw agreement and Cohen's kappa for both the fine-grained
manipulation-type variable and the grouped primary variable
(authentic-content misuse / AI-related / other).

Usage:
    python 03_irr_analysis.py
"""
import sys
import csv
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = "../data"

GROUP = {
    "recycled old content": "authentic-content misuse",
    "recycled old content + audio-manipulated": "authentic-content misuse",
    "false context / wrong location": "authentic-content misuse",
    "AI-generated": "AI-related",
    "AI-manipulated": "AI-related",
    "fabricated quote": "other",
    "fabricated document": "other",
    "other": "other",
}


def cohens_kappa(pairs):
    n = len(pairs)
    categories = sorted(set(a for a, b in pairs) | set(b for a, b in pairs))
    r1 = Counter(a for a, b in pairs)
    r2 = Counter(b for a, b in pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pe = sum((r1.get(c, 0) / n) * (r2.get(c, 0) / n) for c in categories)
    kappa = float("nan") if pe == 1 else (po - pe) / (1 - pe)
    return kappa, po


def report(title, pairs):
    kappa, po = cohens_kappa(pairs)
    agree = sum(1 for a, b in pairs if a == b)
    print(f"{title}: {agree}/{len(pairs)} = {100*po:.1f}% agreement, Cohen's kappa = {kappa:.3f}")
    disagreements = [i for i, (a, b) in enumerate(pairs) if a != b]
    return disagreements


def main():
    with open(f"{DATA_DIR}/irr_sample.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    fine_pairs = [(r["coder1_manipulation_type"], r["coder2_manipulation_type"]) for r in rows]
    grouped_pairs = [(GROUP[a], GROUP[b]) for a, b in fine_pairs]

    print(f"Sample size: {len(rows)}\n")
    fine_disagree_idx = report("Fine-grained", fine_pairs)
    print("Disagreements:", [rows[i]["claim_id"] for i in fine_disagree_idx])
    print()
    grouped_disagree_idx = report("Grouped (primary variable)", grouped_pairs)
    print("Disagreements:", [rows[i]["claim_id"] for i in grouped_disagree_idx])


if __name__ == "__main__":
    main()
