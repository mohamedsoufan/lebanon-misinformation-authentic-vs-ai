# 2026 Lebanon Conflict Misinformation Study

Data and analysis code for a descriptive computational study of fact-checked
misinformation claims related to the 2026 Israel-Hezbollah/Lebanon conflict.
The study classifies 142 unique Arabic- and English-language fact-checked
claims by manipulation type (authentic content reused/recontextualized vs.
AI-generated/AI-manipulated), reports inter-rater reliability on that
classification, tests the sensitivity of the main distribution to the
corpus's reliance on one fact-checking organization, and reports whether any
claims were identified as having penetrated professional news coverage.

Full methodology, taxonomy definitions, and coding rules are in
`docs/Codebook_v1.1.docx` and `supplementary/Supplementary_Material.docx`.

## Repository layout

```
data/            Final coded dataset (CSV) + the complete frozen workbook
scripts/         Analysis pipeline (see below)
figures/         Figures 1-3 (SVG)
supplementary/   Supplementary material referenced in the paper
docs/            Study codebook (taxonomy, coding rules, outlet roster)
```

## Data

| File | Rows | Description |
|---|---|---|
| `data/claims.csv` | 142 | One row per unique claim: normalized description, media type, manipulation-type code, observed language(s). |
| `data/factchecks.csv` | 152 | One row per fact-check article (a claim can have more than one). |
| `data/newsroom_search_log.csv` | 142 | One row per claim: newsroom-penetration search method, date, and result. |
| `data/newsroom_coverage.csv` | 3 | The professional-news articles identified as category-2 penetration, with outlet, URL, and correction details. |
| `data/irr_sample.csv` | 28 | The blinded inter-rater reliability sample: both coders' manipulation-type labels. |
| `data/full_dataset_with_triage_and_correction_log.xlsx` | — | The complete frozen workbook, including the pre-triage candidate pool, exclusion decisions, and a log of one post-freeze correction. Included for full transparency; `claims.csv`/`factchecks.csv` above are the derived tables actually used in the analysis. |

**What isn't fully scriptable.** Turning retrieved candidates into the final
142-claim corpus involved human coding: deciding topical eligibility,
merging multiple fact-checks of the same underlying claim, and assigning a
manipulation-type code from a direct reading of each fact-check (Codebook
Sections 1.3-1.4, 4.1, 4.6). This is standard for content-analysis research
and is not a bug in the pipeline — `01_collect_candidates.py` reproduces the
retrieval step, and the coded output of the human-judgment step is what's
provided directly in `data/`.

## Scripts

Run from inside `scripts/`. Requires Python 3.10+ and `pip install -r
../requirements.txt`.

1. **`01_collect_candidates.py`** — Retrieves candidate fact-checks from the
   Google Fact Check Tools API and Misbar's listing API. Needs a Google
   Fact Check API key (copy `.env.example` to `.env` in the repo root and
   add your own). Output will differ from the frozen corpus over time, since
   it depends on live API/site state and does not perform the human-coding
   step described above.
2. **`02_statistical_analysis.py`** — Reproduces Table 1 and every
   descriptive statistic in the Results section (manipulation-type
   distribution with Wilson 95% CIs, the three Misbar sensitivity analyses,
   newsroom-penetration rates, source composition) directly from the CSVs
   in `data/`. No API key needed.
3. **`03_irr_analysis.py`** — Reproduces the inter-rater reliability results
   (raw agreement and Cohen's kappa, fine-grained and grouped) from
   `data/irr_sample.csv`.
4. **`04_generate_figures.py`** — Regenerates Figures 1-3 as SVG directly
   from `data/claims.csv` and `data/factchecks.csv`.

Each script's output can be checked against the numbers reported in the
paper.

## Manipulation-type taxonomy (summary)

- **AI-generated** — wholly synthetic image, video, or audio.
- **AI-manipulated** — real media digitally altered with AI tools.
- **recycled old content** — genuine media from a real, different event or
  date, presented as current.
- **false context / wrong location** — genuine, contemporaneous media
  misattributed to the wrong place or actor.
- **fabricated quote** / **fabricated document** / **other** — no
  manipulated media involved.

For the primary analysis these are grouped into **authentic-content
misuse**, **AI-related**, and **other** (mutually exclusive, by primary
mechanism — see `docs/Codebook_v1.1.docx` Section 4.1 and the Methods
section of the paper). Full definitions and the complete
major-international-outlet roster used for the newsroom-penetration
analysis are in `supplementary/Supplementary_Material.docx`.

## Status

This repository accompanies a manuscript currently in preparation. Citation
details and a license will be added on publication.
