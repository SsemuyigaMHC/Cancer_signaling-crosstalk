#!/usr/bin/env python3
"""
06_Analyse_Metadata_Screen_Chapter40_FINAL.py

Quality-control and visual analysis for the FINAL Chapter 40 metadata screen.

Input:
  data/metadata/Chapter40_Metadata_Screened/Chapter40_Metadata_Screened_FINAL.xlsx

Outputs:
  data/metadata/Chapter40_Metadata_Screened_FINAL_Analysis/
      Summary.txt
      Tables/
      Figures/Manuscript/
      Figures/Supplementary/
      Audit_Samples/

Design:
- Does NOT change screening decisions.
- Quantifies decision/category/tier/priority/route distributions.
- Audits mechanism, subsection, scientific-role, provenance and publication-type coverage.
- Checks metadata completeness.
- Produces stratified audit samples for human inspection.
- Generates clean matplotlib figures without manually specified colours/styles.
"""

from pathlib import Path
import argparse
import re
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    BASE_DIR / "data" / "metadata" / "Chapter40_Metadata_Screened"
    / "Chapter40_Metadata_Screened_FINAL.xlsx"
)
DEFAULT_OUTPUT = (
    BASE_DIR / "data" / "metadata"
    / "Chapter40_Metadata_Screened_FINAL_Analysis"
)

RANDOM_SEED = 40

def clean(v):
    if pd.isna(v):
        return ""
    return str(v).strip()

def split_multi(series):
    vals = []
    for v in series.fillna("").astype(str):
        if not v.strip():
            continue
        for x in re.split(r"\s*;\s*|\s*\|\s*|\s*,\s*", v):
            x = x.strip()
            if x:
                vals.append(x)
    return pd.Series(vals)

def save_bar(series, title, path, xlabel="", ylabel="Records", horizontal=False,
             percent=False, top_n=None):
    s = series.copy()
    if top_n:
        s = s.sort_values(ascending=False).head(top_n)
    if percent:
        s = s / s.sum() * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    if horizontal:
        s = s.sort_values(ascending=True)
        ax.barh(s.index.astype(str), s.values)
        ax.set_xlabel("Percent" if percent else ylabel)
        ax.set_ylabel(xlabel)
    else:
        ax.bar(s.index.astype(str), s.values)
        ax.set_ylabel("Percent" if percent else ylabel)
        ax.set_xlabel(xlabel)
        ax.tick_params(axis="x", rotation=45)

    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)

def save_heatmap(ct, title, path, normalize_rows=False):
    data = ct.astype(float).copy()
    if normalize_rows:
        data = data.div(data.sum(axis=1).replace(0, np.nan), axis=0) * 100

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(data.values, aspect="auto")
    ax.set_title(title)
    ax.set_xticks(range(len(data.columns)))
    ax.set_xticklabels(data.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(data.index)))
    ax.set_yticklabels(data.index)
    ax.set_xlabel("Metadata Decision")
    ax.set_ylabel("")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Percent" if normalize_rows else "Records")

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data.iloc[i, j]
            if pd.notna(v):
                txt = f"{v:.1f}" if normalize_rows else f"{int(v):,}"
                ax.text(j, i, txt, ha="center", va="center")

    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)

def table_multi(df, column):
    if column not in df.columns:
        return pd.DataFrame(columns=[column, "Records"])
    s = split_multi(df[column])
    if s.empty:
        return pd.DataFrame(columns=[column, "Records"])
    return s.value_counts().rename_axis(column).reset_index(name="Records")

def metadata_completeness(df):
    candidates = [
        "PMID", "DOI", "Title", "Abstract", "Publication Type",
        "Originating Search Streams", "Primary Literature Category",
        "Evidence Tier", "Mechanism Flags", "Subsection Hints",
        "Scientific Role Flags", "Metadata Relevance Score",
        "Metadata Decision", "Acquisition Priority", "Screening Route",
        "Screening Reason"
    ]
    rows = []
    for c in candidates:
        if c not in df.columns:
            continue
        s = df[c]
        missing = s.isna() | s.astype(str).str.strip().eq("")
        rows.append({
            "Field": c,
            "Present": int((~missing).sum()),
            "Missing": int(missing.sum()),
            "Completeness_%": round((~missing).mean() * 100, 2)
        })
    return pd.DataFrame(rows)

def audit_sample(df, decision, n=100):
    sub = df[df["Metadata Decision"].eq(decision)].copy()
    if len(sub) <= n:
        return sub
    return sub.sample(n=n, random_state=RANDOM_SEED)

def stratified_sample(df, n_per_group=20):
    parts = []
    group_cols = [
        "Metadata Decision",
        "Primary Literature Category"
    ]
    for keys, g in df.groupby(group_cols, dropna=False):
        parts.append(
            g.sample(
                n=min(n_per_group, len(g)),
                random_state=RANDOM_SEED
            )
        )
    if not parts:
        return df.iloc[0:0].copy()
    return pd.concat(parts, ignore_index=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_INPUT))
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    ap.add_argument("--audit-n", type=int, default=100)
    args = ap.parse_args()

    input_path = Path(args.input)
    output = Path(args.output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    tables = output / "Tables"
    manuscript = output / "Figures" / "Manuscript"
    supplementary = output / "Figures" / "Supplementary"
    audits = output / "Audit_Samples"

    for p in [tables, manuscript, supplementary, audits]:
        p.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)

    required = [
        "PMID", "Title", "Abstract", "Primary Literature Category",
        "Evidence Tier", "Mechanism Flags", "Subsection Hints",
        "Scientific Role Flags", "Metadata Relevance Score",
        "Metadata Decision", "Acquisition Priority", "Screening Route"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(
            "QC INPUT VALIDATION FAILED. Missing columns: " + ", ".join(missing)
        )

    print(f"Input: {input_path}")
    print(f"Records: {len(df):,}")
    print("QC input validation: PASS")

    # -------------------------
    # Core tables
    # -------------------------
    decision = df["Metadata Decision"].value_counts().rename_axis(
        "Metadata Decision").reset_index(name="Records")
    decision["Percent"] = decision["Records"] / len(df) * 100

    priority = df["Acquisition Priority"].value_counts().rename_axis(
        "Acquisition Priority").reset_index(name="Records")
    priority["Percent"] = priority["Records"] / len(df) * 100

    route = df["Screening Route"].value_counts().rename_axis(
        "Screening Route").reset_index(name="Records")
    route["Percent"] = route["Records"] / len(df) * 100

    category = df["Primary Literature Category"].value_counts().rename_axis(
        "Primary Literature Category").reset_index(name="Records")
    category["Percent"] = category["Records"] / len(df) * 100

    tier = df["Evidence Tier"].value_counts().rename_axis(
        "Evidence Tier").reset_index(name="Records")
    tier["Percent"] = tier["Records"] / len(df) * 100

    role = table_multi(df, "Scientific Role Flags")
    mechanism = table_multi(df, "Mechanism Flags")
    subsection = table_multi(df, "Subsection Hints")
    streams = table_multi(df, "Originating Search Streams")
    pubtypes = table_multi(df, "Publication Type")

    decision_category = pd.crosstab(
        df["Primary Literature Category"], df["Metadata Decision"]
    )
    decision_tier = pd.crosstab(
        df["Evidence Tier"], df["Metadata Decision"]
    )
    decision_priority = pd.crosstab(
        df["Metadata Decision"], df["Acquisition Priority"]
    )
    decision_route = pd.crosstab(
        df["Metadata Decision"], df["Screening Route"]
    )

    score = df["Metadata Relevance Score"].describe().to_frame("Value")

    # Signal coverage
    signal_cols = [
        c for c in [
            "Signal Resistance",
            "Signal Adaptive",
            "Signal Network_Crosstalk",
            "Signal Mechanistic",
            "Signal Cancer",
            "Signal Explicit_Resistance_Signaling",
            "Classifier Mechanism Signal",
            "Classifier Role Signal",
            "Classifier Subsection Signal",
            "NonPrimary Publication Form"
        ] if c in df.columns
    ]
    signal_rows = []
    for c in signal_cols:
        x = df[c].fillna(False).astype(bool)
        signal_rows.append({
            "Signal": c,
            "Records": int(x.sum()),
            "Percent": round(x.mean() * 100, 2)
        })
    signals = pd.DataFrame(signal_rows)

    completeness = metadata_completeness(df)

    # -------------------------
    # Save tables
    # -------------------------
    tables_to_save = {
        "decision_summary": decision,
        "priority_summary": priority,
        "route_summary": route,
        "category_summary": category,
        "tier_summary": tier,
        "decision_by_category": decision_category,
        "decision_by_tier": decision_tier,
        "decision_by_priority": decision_priority,
        "decision_by_route": decision_route,
        "scientific_roles": role,
        "mechanisms": mechanism,
        "subsections": subsection,
        "search_streams": streams,
        "publication_types": pubtypes,
        "metadata_completeness": completeness,
        "signal_coverage": signals,
        "score_distribution": score,
    }

    for name, table in tables_to_save.items():
        table.to_csv(tables / f"{name}.csv")

    # -------------------------
    # Human audit samples
    # -------------------------
    for d in ["RETAIN", "REVIEW", "EXCLUDE"]:
        audit_sample(df, d, args.audit_n).to_csv(
            audits / f"Audit_{d}_{args.audit_n}.csv", index=False
        )

    stratified_sample(df).to_csv(
        audits / "Audit_Stratified_Decision_x_Category.csv", index=False
    )

    # Highest-risk records for manual inspection:
    # records sitting near the decision boundaries.
    df_sorted = df.sort_values("Metadata Relevance Score")
    low_boundary = df_sorted[
        df_sorted["Metadata Relevance Score"].between(4, 7)
    ].head(250)
    high_boundary = df_sorted[
        df_sorted["Metadata Relevance Score"].between(8, 11)
    ].head(250)

    low_boundary.to_csv(
        audits / "Audit_Boundary_Low_4_to_7.csv", index=False
    )
    high_boundary.to_csv(
        audits / "Audit_Boundary_High_8_to_11.csv", index=False
    )

    # -------------------------
    # Manuscript figures
    # -------------------------
    save_bar(
        decision.set_index("Metadata Decision")["Records"],
        "Chapter 40 Metadata Screening Decisions",
        manuscript / "Figure_M1_Screening_Decisions.png",
        ylabel="Records"
    )

    save_bar(
        category.set_index("Primary Literature Category")["Records"],
        "Chapter 40 Literature Categories",
        manuscript / "Figure_M2_Literature_Categories.png",
        ylabel="Records"
    )

    save_bar(
        tier.set_index("Evidence Tier")["Records"],
        "Chapter 40 Evidence Tiers",
        manuscript / "Figure_M3_Evidence_Tiers.png",
        ylabel="Records"
    )

    save_heatmap(
        decision_category,
        "Metadata Decision by Literature Category",
        manuscript / "Figure_M4_Decision_by_Category.png"
    )

    save_bar(
        signals.set_index("Signal")["Records"],
        "Chapter 40 Metadata Signal Coverage",
        manuscript / "Figure_M5_Metadata_Signal_Coverage.png",
        ylabel="Records",
        horizontal=True
    )

    save_bar(
        subsection.set_index("Subsection Hints")["Records"],
        "Chapter 40 Subsection Routing Coverage",
        manuscript / "Figure_M6_Subsection_Coverage.png",
        ylabel="Records",
        horizontal=True,
        top_n=20
    )

    # Score distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df["Metadata Relevance Score"].dropna(), bins=30)
    ax.set_title("Metadata Relevance Score Distribution")
    ax.set_xlabel("Metadata Relevance Score")
    ax.set_ylabel("Records")
    fig.tight_layout()
    fig.savefig(
        manuscript / "Figure_M7_Relevance_Score_Distribution.png",
        dpi=300, bbox_inches="tight"
    )
    plt.close(fig)

    # Decision by tier
    save_heatmap(
        decision_tier,
        "Metadata Decision by Evidence Tier",
        manuscript / "Figure_M8_Decision_by_Tier.png"
    )

    # -------------------------
    # Supplementary figures
    # -------------------------
    save_bar(
        priority.set_index("Acquisition Priority")["Records"],
        "Acquisition Priority Distribution",
        supplementary / "S1_Acquisition_Priorities.png",
        ylabel="Records",
        horizontal=True
    )

    save_bar(
        route.set_index("Screening Route")["Records"],
        "Screening Route Distribution",
        supplementary / "S2_Screening_Routes.png",
        ylabel="Records",
        horizontal=True
    )

    save_bar(
        streams.set_index("Originating Search Streams")["Records"],
        "Search Stream Contributions",
        supplementary / "S3_Search_Streams.png",
        ylabel="Records",
        horizontal=True,
        top_n=25
    )

    save_bar(
        pubtypes.set_index("Publication Type")["Records"],
        "Publication Types",
        supplementary / "S4_Publication_Types.png",
        ylabel="Records",
        horizontal=True,
        top_n=25
    )

    if "Publication Year" in df.columns:
        years = pd.to_numeric(df["Publication Year"], errors="coerce").dropna()
        save_bar(
            years.value_counts().sort_index(),
            "Publication Year Distribution",
            supplementary / "S5_Publication_Years.png",
            ylabel="Records"
        )

    save_bar(
        completeness.set_index("Field")["Completeness_%"],
        "Metadata Completeness",
        supplementary / "S6_Metadata_Completeness.png",
        ylabel="Percent",
        horizontal=True
    )

    # -------------------------
    # QC summary
    # -------------------------
    summary = output / "Summary.txt"
    with summary.open("w", encoding="utf-8") as f:
        f.write("CHAPTER 40 METADATA SCREEN — QC REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Input: {input_path}\n")
        f.write(f"Total records: {len(df):,}\n\n")

        f.write("DECISION DISTRIBUTION\n")
        f.write(decision.to_string(index=False))
        f.write("\n\n")

        f.write("LITERATURE CATEGORY DISTRIBUTION\n")
        f.write(category.to_string(index=False))
        f.write("\n\n")

        f.write("DECISION × CATEGORY\n")
        f.write(decision_category.to_string())
        f.write("\n\n")

        f.write("DECISION × EVIDENCE TIER\n")
        f.write(decision_tier.to_string())
        f.write("\n\n")

        f.write("ACQUISITION PRIORITY\n")
        f.write(priority.to_string(index=False))
        f.write("\n\n")

        f.write("SCREENING ROUTE\n")
        f.write(route.to_string(index=False))
        f.write("\n\n")

        f.write("METADATA SIGNAL COVERAGE\n")
        f.write(signals.to_string(index=False))
        f.write("\n\n")

        f.write("METADATA COMPLETENESS\n")
        f.write(completeness.to_string(index=False))
        f.write("\n\n")

        f.write("RELEVANCE SCORE DESCRIPTION\n")
        f.write(score.to_string())
        f.write("\n\n")

        f.write("QC INTERPRETATION FLAGS\n")
        f.write("- C_MECHANISTIC_PRIMARY excluded: ")
        f.write(str(int(
            ((df["Primary Literature Category"] == "C_MECHANISTIC_PRIMARY") &
             (df["Metadata Decision"] == "EXCLUDE")).sum()
        )))
        f.write("\n- D_THERAPEUTIC excluded: ")
        f.write(str(int(
            ((df["Primary Literature Category"] == "D_THERAPEUTIC") &
             (df["Metadata Decision"] == "EXCLUDE")).sum()
        )))
        f.write("\n- Records with explicit resistance + signaling/adaptation: ")
        f.write(str(int(
            df["Signal Explicit_Resistance_Signaling"].fillna(False).astype(bool).sum()
        )))
        f.write("\n")

    print("\nQC COMPLETE")
    print(f"  Records analysed: {len(df):,}")
    print("\nDecision distribution:")
    print(decision.to_string(index=False))
    print("\nKey safety checks:")
    print(
        "  C_MECHANISTIC_PRIMARY excluded:",
        int(((df["Primary Literature Category"] == "C_MECHANISTIC_PRIMARY") &
             (df["Metadata Decision"] == "EXCLUDE")).sum())
    )
    print(
        "  D_THERAPEUTIC excluded:",
        int(((df["Primary Literature Category"] == "D_THERAPEUTIC") &
             (df["Metadata Decision"] == "EXCLUDE")).sum())
    )
    print("\nOutputs:")
    print(f"  Summary: {summary}")
    print(f"  Tables: {tables}")
    print(f"  Manuscript figures: {manuscript}")
    print(f"  Supplementary figures: {supplementary}")
    print(f"  Audit samples: {audits}")

if __name__ == "__main__":
    main()
