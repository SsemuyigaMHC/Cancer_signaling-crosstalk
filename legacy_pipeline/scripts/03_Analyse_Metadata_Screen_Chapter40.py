#!/usr/bin/env python3
"""
Chapter 40 — Metadata screening analysis and visual QC.

Runs AFTER Chapter40_Metadata_Screened.xlsx is generated.

Outputs:
    data/metadata/Chapter40_Metadata_Screened_Analysis/
        Tables/
        Figures/
            Manuscript/
            Supplementary/
        Summary.txt

The analysis is descriptive/auditable. It does not establish final chapter
eligibility. Visuals emphasize:
- screening decisions
- acquisition priorities
- literature categories
- evidence tiers
- mechanism coverage
- subsection coverage
- decision x category
- decision x evidence tier
- publication years
- publication types
- search streams
- metadata completeness
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
DEFAULT_INPUT = METADATA_DIR / "Chapter40_Metadata_Screened" / "Chapter40_Metadata_Screened.xlsx"
OUT = METADATA_DIR / "Chapter40_Metadata_Screened_Analysis"
TABLES = OUT / "Tables"
FIGURES = OUT / "Figures"
MANUSCRIPT = FIGURES / "Manuscript"
SUPP = FIGURES / "Supplementary"

DECISIONS = ("RETAIN", "REVIEW", "EXCLUDE")
CATEGORIES = (
    "A_FOUNDATIONAL", "B_MAJOR_REVIEW", "C_MECHANISTIC_PRIMARY",
    "D_THERAPEUTIC", "E_TRANSLATIONAL_CLINICAL", "F_EMERGING_DISCOVERY",
)
TIERS = ("Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5")

def norm(v):
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()

def col(df, names):
    lookup = {re.sub(r"[^a-z0-9]", "", str(c).lower()): c for c in df.columns}
    for n in names:
        k = re.sub(r"[^a-z0-9]", "", n.lower())
        if k in lookup:
            return lookup[k]
    return None

def series(df, names):
    c = col(df, names)
    if c is None:
        return pd.Series([""] * len(df), index=df.index)
    return df[c].map(norm)

def split_values(series_obj):
    counts = {}
    for value in series_obj:
        for part in re.split(r"\s*[;|]\s*", norm(value)):
            part = part.strip()
            if part:
                counts[part] = counts.get(part, 0) + 1
    return pd.DataFrame({"Label": list(counts), "Count": list(counts.values())}).sort_values(
        "Count", ascending=False, kind="stable"
    ).reset_index(drop=True)

def freq(s, label="Label"):
    vc = s.replace("", "Missing").value_counts(dropna=False)
    out = vc.rename_axis(label).reset_index(name="Count")
    out["Percentage"] = out["Count"] / len(s) * 100
    return out

def crosstab(df, rows, cols, row_label):
    table = pd.crosstab(rows, cols).reindex(columns=DECISIONS, fill_value=0)
    return table.reset_index().rename(columns={table.index.name or rows.name or 0: row_label})

def savefig(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=400, bbox_inches="tight")
    plt.close(fig)

def annotate(ax, bars, fmt="{:,.0f}"):
    for b in bars:
        v = b.get_width() if b.get_width() != 0 else b.get_height()
        if b.get_width() >= b.get_height():
            ax.text(b.get_width(), b.get_y()+b.get_height()/2, fmt.format(v),
                    va="center", ha="left", fontsize=8)
        else:
            ax.text(b.get_x()+b.get_width()/2, b.get_height(), fmt.format(v),
                    va="bottom", ha="center", fontsize=8)

def barh(ax, table, label_col, title, limit=20):
    if table.empty:
        ax.text(.5,.5,"No data",ha="center",va="center"); ax.axis("off"); return
    d = table.head(limit).iloc[::-1]
    bars = ax.barh(d[label_col].astype(str), d["Count"])
    for b, v in zip(bars, d["Count"]):
        ax.text(b.get_width(), b.get_y()+b.get_height()/2, f"{v:,}", va="center", ha="left", fontsize=8)
    ax.set_title(title)
    ax.set_xlabel("Records")
    ax.grid(axis="x", alpha=.25)
    ax.set_axisbelow(True)

def stacked_crosstab(ax, table, label_col, title):
    if table.empty:
        ax.text(.5,.5,"No data",ha="center",va="center"); ax.axis("off"); return
    d = table.copy()
    x = np.arange(len(d))
    bottom = np.zeros(len(d))
    for decision in DECISIONS:
        vals = d[decision].to_numpy(dtype=float)
        ax.bar(x, vals, bottom=bottom, label=decision)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(d[label_col].astype(str), rotation=45, ha="right")
    ax.set_ylabel("Records")
    ax.set_title(title)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=.25)
    ax.set_axisbelow(True)

def main():
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if not input_file.exists():
        raise FileNotFoundError(f"Input not found: {input_file}")

    for p in (TABLES, MANUSCRIPT, SUPP):
        p.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_file)
    decision = series(df, ("Metadata Decision",))
    category = series(df, ("Primary Literature Category", "Literature Category"))
    tier = series(df, ("Evidence Tier", "Tier"))
    priority = series(df, ("Acquisition Priority",))
    route = series(df, ("Screening Route",))
    mechanisms = series(df, ("Mechanism Flags", "Mechanism Flag"))
    subsections = series(df, ("Subsection Hints", "Subsection Hint"))
    roles = series(df, ("Scientific Role Flags", "Scientific Role"))
    years = series(df, ("Publication Year", "Year"))
    pubtypes = series(df, ("Publication Type", "Publication Types", "Document Type"))
    streams = series(df, ("Originating Search Streams", "Search Stream", "Search Streams"))
    titles = series(df, ("Title", "Article Title"))
    abstracts = series(df, ("Abstract", "Abstract Text"))

    tables = {}
    tables["decision_summary"] = freq(decision, "Decision")
    tables["priority_summary"] = freq(priority, "Acquisition Priority")
    tables["route_summary"] = freq(route, "Screening Route")
    tables["category_summary"] = freq(category, "Literature Category")
    tables["tier_summary"] = freq(tier, "Evidence Tier")
    tables["mechanisms"] = split_values(mechanisms)
    tables["subsections"] = split_values(subsections)
    tables["scientific_roles"] = split_values(roles)
    tables["search_streams"] = split_values(streams)
    tables["publication_types"] = split_values(pubtypes)

    year_num = pd.to_numeric(years.str.extract(r"(\d{4})", expand=False), errors="coerce")
    year_table = pd.DataFrame({"Year": year_num.dropna().astype(int)}).value_counts().rename("Count").reset_index()
    tables["years"] = year_table.sort_values("Year")

    # Decision cross-tabs.
    cat_xt = pd.crosstab(category, decision).reindex(columns=DECISIONS, fill_value=0).reset_index()
    cat_xt = cat_xt.rename(columns={cat_xt.columns[0]: "Literature Category"})
    tables["decision_by_category"] = cat_xt

    tier_xt = pd.crosstab(tier, decision).reindex(columns=DECISIONS, fill_value=0).reset_index()
    tier_xt = tier_xt.rename(columns={tier_xt.columns[0]: "Evidence Tier"})
    tables["decision_by_tier"] = tier_xt

    # Metadata completeness.
    completeness = []
    for label, s in {
        "Title": titles, "Abstract": abstracts, "Literature Category": category,
        "Evidence Tier": tier, "Mechanism Flags": mechanisms,
        "Subsection Hints": subsections, "Scientific Role Flags": roles,
    }.items():
        missing = (s == "").sum()
        completeness.append({"Field": label, "Complete": len(df)-missing, "Missing": missing,
                             "Percent Missing": missing/len(df)*100})
    tables["metadata_completeness"] = pd.DataFrame(completeness)

    # Save tables.
    for name, table in tables.items():
        table.to_csv(TABLES / f"{name}.csv", index=False)

    # Manuscript-quality core figures.
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    d = tables["decision_summary"].set_index("Decision").reindex(DECISIONS, fill_value=0).reset_index()
    bars = ax.bar(d["Decision"], d["Count"])
    for b, v in zip(bars, d["Count"]):
        ax.text(b.get_x()+b.get_width()/2, b.get_height(), f"{v:,}\n({v/len(df)*100:.1f}%)",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Records")
    ax.set_title("Chapter 40 metadata screening decisions")
    ax.grid(axis="y", alpha=.25); ax.set_axisbelow(True)
    savefig(fig, MANUSCRIPT / "Figure_M1_Screening_Decisions.png")

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    barh(ax, tables["category_summary"], "Literature Category", "Literature categories", 10)
    savefig(fig, MANUSCRIPT / "Figure_M2_Literature_Categories.png")

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    barh(ax, tables["tier_summary"], "Evidence Tier", "Evidence tiers", 10)
    savefig(fig, MANUSCRIPT / "Figure_M3_Evidence_Tiers.png")

    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    stacked_crosstab(ax, tables["decision_by_category"], "Literature Category",
                     "Screening decision by literature category")
    savefig(fig, MANUSCRIPT / "Figure_M4_Decision_by_Category.png")

    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    barh(ax, tables["mechanisms"], "Label", "Mechanism coverage", 20)
    savefig(fig, MANUSCRIPT / "Figure_M5_Mechanism_Coverage.png")

    fig, ax = plt.subplots(figsize=(10, 5.8))
    barh(ax, tables["subsections"], "Label", "Subsection routing coverage", 18)
    savefig(fig, MANUSCRIPT / "Figure_M6_Subsection_Coverage.png")

    # Supplementary figures.
    specs = [
        ("S1_Acquisition_Priorities.png", tables["priority_summary"], "Acquisition Priority", "Acquisition priorities", 15),
        ("S2_Screening_Routes.png", tables["route_summary"], "Screening Route", "Screening routes", 15),
        ("S3_Search_Streams.png", tables["search_streams"], "Label", "Originating search streams", 20),
        ("S4_Publication_Types.png", tables["publication_types"], "Label", "Publication types", 15),
    ]
    for filename, table, label, title, limit in specs:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        barh(ax, table, label, title, limit)
        savefig(fig, SUPP / filename)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(tables["years"]["Year"].astype(str), tables["years"]["Count"])
    ax.set_title("Publication-year distribution")
    ax.set_xlabel("Year"); ax.set_ylabel("Records")
    ax.tick_params(axis="x", rotation=60)
    ax.grid(axis="y", alpha=.25); ax.set_axisbelow(True)
    savefig(fig, SUPP / "S5_Publication_Years.png")

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    d = tables["metadata_completeness"].iloc[::-1]
    ax.barh(d["Field"], d["Complete"], label="Complete")
    ax.barh(d["Field"], d["Missing"], left=d["Complete"], label="Missing")
    ax.set_title("Metadata completeness")
    ax.set_xlabel("Records"); ax.legend(frameon=False)
    ax.grid(axis="x", alpha=.25); ax.set_axisbelow(True)
    savefig(fig, SUPP / "S6_Metadata_Completeness.png")

    fig, ax = plt.subplots(figsize=(12, 9))
    fig.suptitle("Chapter 40 metadata screening overview", fontsize=14, fontweight="bold")
    panels = [
        (0,0, tables["decision_summary"], "Decision", "Screening decisions"),
        (0,1, tables["category_summary"], "Literature Category", "Literature categories"),
        (1,0, tables["mechanisms"], "Label", "Mechanism coverage"),
        (1,1, tables["subsections"], "Label", "Subsection coverage"),
    ]
    for r,c,t,label,title in panels:
        a = ax.figure.add_subplot(2,2,r*2+c)
        barh(a,t,label,title,12)
    # Hide the first unused axes created by fig, ax.
    ax.remove()
    fig.tight_layout()
    savefig(fig, MANUSCRIPT / "Figure_01_Chapter40_Metadata_Overview.png")

    total = len(df)
    retained = int((decision == "RETAIN").sum())
    reviewed = int((decision == "REVIEW").sum())
    excluded = int((decision == "EXCLUDE").sum())

    summary = [
        "Chapter 40 Metadata Screening Analysis",
        "=" * 48,
        f"Input workbook: {input_file}",
        f"Total records: {total:,}",
        "",
        f"RETAIN: {retained:,} ({retained/total*100:.1f}%)",
        f"REVIEW: {reviewed:,} ({reviewed/total*100:.1f}%)",
        f"EXCLUDE: {excluded:,} ({excluded/total*100:.1f}%)",
        "",
        "Interpretation:",
        "- RETAIN records are candidates for full-text acquisition according to priority.",
        "- REVIEW records remain in the universe and should not be silently discarded.",
        "- EXCLUDE records are retained in the workbook for audit but are not acquired.",
        "- Literature categories and evidence tiers are preserved from automated classification.",
        "- This stage is metadata triage, not final scientific eligibility.",
        "",
        "Generated figures:",
    ]
    for p in sorted(MANUSCRIPT.glob("*.png")) + sorted(SUPP.glob("*.png")):
        summary.append(f"- {p.name}")
    (OUT / "Summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("=" * 88)
    print("CHAPTER 40 — METADATA SCREENING ANALYSIS")
    print("=" * 88)
    print(f"Input: {input_file}")
    print(f"Records: {total:,}")
    print(f"RETAIN: {retained:,}")
    print(f"REVIEW: {reviewed:,}")
    print(f"EXCLUDE: {excluded:,}")
    print(f"Tables: {TABLES}")
    print(f"Figures: {FIGURES}")
    print(f"Summary: {OUT / 'Summary.txt'}")
    print("=" * 88)

if __name__ == "__main__":
    main()
