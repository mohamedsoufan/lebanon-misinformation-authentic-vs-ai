"""
Regenerates Figures 1-3 as SVG directly from ../data/claims.csv and
../data/factchecks.csv, so the figures stay in sync with the underlying
data rather than hardcoded numbers.

Usage:
    python 04_generate_figures.py

Output:
    figure1_main_finding.svg
    figure2_finegrained_categories.svg
    figure3_misbar_sensitivity.svg
"""
import sys
import csv
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = "../data"

FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"
INK_PRIMARY, INK_SECONDARY, INK_MUTED = "#0b0b0b", "#52514e", "#898781"
SURFACE, BASELINE = "#ffffff", "#c3c2b7"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#898781"

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
GROUP_COLOR = {"authentic-content misuse": BLUE, "AI-related": ORANGE, "other": GRAY}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rounded_bar(x, y, w, h, r, fill):
    if w <= r:
        r = max(1, w / 2)
    return (f'<path d="M {x},{y} H {x+w-r} A {r},{r} 0 0 1 {x+w},{y+r} '
            f'V {y+h-r} A {r},{r} 0 0 1 {x+w-r},{y+h} H {x} Z" fill="{fill}"/>')


def is_misbar(pub):
    p = (pub or "").strip().lower()
    return "misbar" in p or "مسبار" in p


def read_csv(name):
    with open(f"{DATA_DIR}/{name}", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def figure1(group_counts, n_total):
    W, H = 920, 470
    ML, MR = 40, 90
    chart_w = W - ML - MR
    title = "Most fact-checked claims involved authentic content used deceptively"
    subtitle = f"Grouped manipulation type among {n_total} fact-checked misinformation claims related to the 2026 Lebanon conflict"
    note_lines = [
        "Authentic-content misuse includes recycled old content, false context/wrong location, and the single",
        "recycled-old-content + audio-manipulated case. AI-related includes AI-generated and AI-manipulated content.",
        "Other includes fabricated quotes, fabricated documents, and the residual “other” category.",
    ]
    order = ["authentic-content misuse", "AI-related", "other"]
    labels = {"authentic-content misuse": "Authentic-content misuse", "AI-related": "AI-related", "other": "Other"}
    data = [(labels[g], 100 * group_counts[g] / n_total, group_counts[g], GROUP_COLOR[g]) for g in order]

    bar_h, row_h, top = 24, 92, 118
    axis_y = top + len(data) * row_h - (row_h - bar_h) + 30
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">']
    svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{SURFACE}"/>')
    svg.append(f'<text x="{ML}" y="40" font-size="21" font-weight="700" fill="{INK_PRIMARY}">{esc(title)}</text>')
    svg.append(f'<text x="{ML}" y="66" font-size="14" fill="{INK_SECONDARY}">{esc(subtitle)}</text>')
    svg.append(f'<line x1="{ML}" y1="{top-14}" x2="{ML}" y2="{axis_y}" stroke="{BASELINE}" stroke-width="1"/>')
    for i, (label, pct, n, color) in enumerate(data):
        y = top + i * row_h
        bar_w = chart_w * (pct / 100.0)
        svg.append(f'<text x="{ML}" y="{y-10}" font-size="15" font-weight="600" fill="{INK_PRIMARY}">{esc(label)}</text>')
        svg.append(rounded_bar(ML, y, bar_w, bar_h, 4, color))
        val_x = ML + bar_w + 12
        svg.append(f'<text x="{val_x}" y="{y+bar_h-6}" font-size="17" font-weight="700" fill="{INK_PRIMARY}">{pct:.1f}%</text>')
        svg.append(f'<text x="{val_x}" y="{y+bar_h+13}" font-size="12" fill="{INK_MUTED}">({n}/{n_total})</text>')
    svg.append(f'<line x1="{ML}" y1="{axis_y}" x2="{ML+chart_w}" y2="{axis_y}" stroke="{BASELINE}" stroke-width="1"/>')
    svg.append(f'<text x="{ML}" y="{axis_y+18}" font-size="11" fill="{INK_MUTED}">0%</text>')
    svg.append(f'<text x="{ML+chart_w}" y="{axis_y+18}" font-size="11" fill="{INK_MUTED}" text-anchor="end">100%</text>')
    note_y = axis_y + 44
    for j, line in enumerate(note_lines):
        svg.append(f'<text x="{ML}" y="{note_y + j*17}" font-size="11.5" fill="{INK_SECONDARY}">{esc(line)}</text>')
    svg.append("</svg>")
    return "\n".join(svg)


def figure2(manip_counts, n_total):
    W, H = 940, 700
    ML, MR = 40, 100
    chart_w = W - ML - MR
    title = "Recycled old content was the largest fine-grained category"
    subtitle = f"Classification of {n_total} fact-checked misinformation claims in the study corpus"
    data = sorted(
        ((cat, n, 100 * n / n_total, GROUP_COLOR[GROUP[cat]]) for cat, n in manip_counts.items()),
        key=lambda x: -x[1],
    )
    bar_h, row_h, top = 20, 68, 118
    axis_y = top + len(data) * row_h - (row_h - bar_h) + 26
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">']
    svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{SURFACE}"/>')
    svg.append(f'<text x="{ML}" y="40" font-size="21" font-weight="700" fill="{INK_PRIMARY}">{esc(title)}</text>')
    svg.append(f'<text x="{ML}" y="66" font-size="14" fill="{INK_SECONDARY}">{esc(subtitle)}</text>')
    svg.append(f'<line x1="{ML}" y1="{top-14}" x2="{ML}" y2="{axis_y}" stroke="{BASELINE}" stroke-width="1"/>')
    for i, (label, n, pct, color) in enumerate(data):
        y = top + i * row_h
        bar_w = chart_w * (pct / 100.0)
        svg.append(f'<text x="{ML}" y="{y-8}" font-size="14" font-weight="600" fill="{INK_PRIMARY}">{esc(label)}</text>')
        svg.append(rounded_bar(ML, y, bar_w, bar_h, 4, color))
        val_x = ML + bar_w + 10
        svg.append(f'<text x="{val_x}" y="{y+bar_h-4}" font-size="14" font-weight="700" fill="{INK_PRIMARY}">{n} ({pct:.1f}%)</text>')
    svg.append(f'<line x1="{ML}" y1="{axis_y}" x2="{ML+chart_w}" y2="{axis_y}" stroke="{BASELINE}" stroke-width="1"/>')
    svg.append(f'<text x="{ML}" y="{axis_y+18}" font-size="11" fill="{INK_MUTED}">0%</text>')
    svg.append(f'<text x="{ML+chart_w}" y="{axis_y+18}" font-size="11" fill="{INK_MUTED}" text-anchor="end">100%</text>')
    key_y = axis_y + 40
    key_items = [("Authentic-content-misuse categories", BLUE), ("AI-related categories", ORANGE), ("Residual categories", GRAY)]
    kx = ML
    for label, color in key_items:
        svg.append(f'<rect x="{kx}" y="{key_y-11}" width="12" height="12" rx="2" fill="{color}"/>')
        svg.append(f'<text x="{kx+18}" y="{key_y}" font-size="12" fill="{INK_SECONDARY}">{esc(label)}</text>')
        kx += 18 + 8 + len(label) * 6.5 + 26
    svg.append("</svg>")
    return "\n".join(svg)


def figure3(subsets):
    """subsets: list of (label, n, {group: pct}) in display order."""
    W, H = 1000, 430
    ML, MR = 360, 60
    chart_w = W - ML - MR
    title = "Authentic-content misuse remained the majority in both Misbar sensitivity checks"
    subtitle = "Full corpus compared with claims having at least one non-Misbar fact-check and claims with no Misbar involvement"
    order = ["authentic-content misuse", "AI-related", "other"]
    bar_h, row_h, top, gap = 40, 118, 118, 2

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">']
    svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{SURFACE}"/>')
    svg.append(f'<text x="40" y="40" font-size="21" font-weight="700" fill="{INK_PRIMARY}">{esc(title)}</text>')
    svg.append(f'<text x="40" y="66" font-size="14" fill="{INK_SECONDARY}">{esc(subtitle)}</text>')

    for i, (sample_label, n, pcts) in enumerate(subsets):
        y = top + i * row_h
        svg.append(f'<text x="40" y="{y+bar_h/2-6}" font-size="14" font-weight="600" fill="{INK_PRIMARY}">{esc(sample_label)}</text>')
        svg.append(f'<text x="40" y="{y+bar_h/2+12}" font-size="12" fill="{INK_MUTED}">N = {n}</text>')
        x = ML
        for gi, g in enumerate(order):
            pct = pcts[g]
            seg_w = max(chart_w * (pct / 100.0) - gap, 1)
            color = GROUP_COLOR[g]
            if gi == len(order) - 1:
                svg.append(rounded_bar(x, y, seg_w, bar_h, 4, color))
            else:
                svg.append(f'<rect x="{x}" y="{y}" width="{seg_w}" height="{bar_h}" fill="{color}"/>')
            label_text = f"{pct:.1f}%"
            fits_inside = seg_w > (len(label_text) * 8 + 16)
            if fits_inside:
                svg.append(f'<text x="{x+seg_w/2}" y="{y+bar_h/2+5}" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">{label_text}</text>')
            else:
                svg.append(f'<text x="{x+seg_w+6}" y="{y+bar_h/2+5}" font-size="12" font-weight="700" fill="{INK_PRIMARY}">{label_text}</text>')
            x += chart_w * (pct / 100.0)

    legend_y = top + len(subsets) * row_h - (row_h - bar_h) + 26
    key_items = [("Authentic-content misuse", BLUE), ("AI-related", ORANGE), ("Other", GRAY)]
    kx = ML
    for label, color in key_items:
        svg.append(f'<rect x="{kx}" y="{legend_y-11}" width="12" height="12" rx="2" fill="{color}"/>')
        svg.append(f'<text x="{kx+18}" y="{legend_y}" font-size="12" fill="{INK_SECONDARY}">{esc(label)}</text>')
        kx += 18 + 8 + len(label) * 6.5 + 26
    svg.append("</svg>")
    return "\n".join(svg)


def group_pcts(ids, claims):
    c = Counter(GROUP[claims[cid]["manipulation_type"]] for cid in ids)
    n = len(ids)
    return n, {g: 100 * c.get(g, 0) / n for g in ("authentic-content misuse", "AI-related", "other")}


def main():
    claims = {r["claim_id"]: r for r in read_csv("claims.csv")}
    factchecks = read_csv("factchecks.csv")
    fc_by_claim = defaultdict(list)
    for r in factchecks:
        fc_by_claim[r["claim_id"]].append(r)

    n_total = len(claims)
    manip_counts = Counter(c["manipulation_type"] for c in claims.values())
    group_counts = Counter(GROUP[c["manipulation_type"]] for c in claims.values())

    non_misbar_only_ids = [cid for cid in claims if any(not is_misbar(fc["publisher"]) for fc in fc_by_claim.get(cid, []))]
    zero_misbar_ids = [cid for cid in claims if not any(is_misbar(fc["publisher"]) for fc in fc_by_claim.get(cid, []))]

    with open("figure1_main_finding.svg", "w", encoding="utf-8") as f:
        f.write(figure1(group_counts, n_total))
    with open("figure2_finegrained_categories.svg", "w", encoding="utf-8") as f:
        f.write(figure2(manip_counts, n_total))

    n1, p1 = n_total, {g: 100 * group_counts[g] / n_total for g in ("authentic-content misuse", "AI-related", "other")}
    n2, p2 = group_pcts(non_misbar_only_ids, claims)
    n3, p3 = group_pcts(zero_misbar_ids, claims)
    subsets = [
        ("Full corpus", n1, p1),
        ("At least one non-Misbar fact-check", n2, p2),
        ("No Misbar involvement", n3, p3),
    ]
    with open("figure3_misbar_sensitivity.svg", "w", encoding="utf-8") as f:
        f.write(figure3(subsets))

    print("Wrote figure1_main_finding.svg, figure2_finegrained_categories.svg, figure3_misbar_sensitivity.svg")


if __name__ == "__main__":
    main()
