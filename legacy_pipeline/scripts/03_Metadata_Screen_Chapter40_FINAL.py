#!/usr/bin/env python3
"""
03_Metadata_Screen_Chapter40_FINAL.py

Classifier-aware metadata triage for Chapter 40 literature.

Design goals:
- Uses Literature_Classified.xlsx/CSV only; never silently falls back to raw retrieval.
- Validates both source metadata and classifier outputs before screening.
- Preserves every input record.
- Uses title/abstract/keywords/MeSH for content signals.
- Uses classifier category, evidence tier, mechanism flags, subsection hints,
  and scientific-role flags as structured evidence.
- Search provenance is used for routing/diagnostics, NOT as scientific content.
- High-recall triage: RETAIN / REVIEW / EXCLUDE.
- Produces an audit-friendly score, signal columns, and explicit reasons.
"""

from pathlib import Path
import argparse
import re
import sys
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = BASE_DIR / "data" / "metadata"
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT_DIR / "Chapter40_Metadata_Screened"

REQUIRED_CLASSIFIER = [
    "Primary Literature Category",
    "Evidence Tier",
    "Mechanism Flags",
    "Subsection Hints",
    "Scientific Role Flags",
]
REQUIRED_SOURCE = [
    "PMID",
    "Title",
    "Abstract",
    "Publication Type",
    "Originating Search Streams",
]

CATEGORY_BASE = {
    "A_FOUNDATIONAL": 2,
    "B_MAJOR_REVIEW": 2,
    "C_MECHANISTIC_PRIMARY": 4,
    "D_THERAPEUTIC": 4,
    "E_TRANSLATIONAL_CLINICAL": 3,
    "F_EMERGING_DISCOVERY": 1,
}

PATTERNS = {
    "resistance": re.compile(
        r"\b(resistan\w*|refractor\w*|treatment failure|therapy failure|"
        r"drug failure|insensitiv\w*|toleran\w*)\b", re.I),
    "adaptive": re.compile(
        r"\b(adaptive resistance|adaptive reprogram\w*|adaptive response|"
        r"compensatory|bypass|feedback|rewir\w*|plasticity|"
        r"network robustness|phenotypic plasticity|dynamic adaptation|"
        r"alternative receptor|receptor switching)\b", re.I),
    "network": re.compile(
        r"\b(signaling crosstalk|signalling crosstalk|pathway crosstalk|"
        r"signaling network|signalling network|network rewiring|"
        r"network pharmacology|systems biology|pathway interaction|"
        r"cross[- ]?talk|crosstalk)\b", re.I),
    "mechanism": re.compile(
        r"\b(mechanis\w*|bypass signaling|feedback activation|"
        r"parallel survival|pathway convergence|reciprocal|"
        r"compensatory signaling|alternative signaling)\b", re.I),
    "therapy": re.compile(
        r"\b(therap\w*|treatment|drug|inhibitor|targeted|"
        r"kinase inhibitor|immunotherap\w*|chemotherap\w*|"
        r"radiotherap\w*|hormonal)\b", re.I),
    "cancer": re.compile(
        r"\b(cancer|carcinoma|tumou?r|leukemia|lymphoma|melanoma|"
        r"sarcoma|glioblastoma|myeloma|neoplasm|oncolog\w*)\b", re.I),
}

NONPRIMARY = re.compile(
    r"\b(protocol|editorial|letter|comment|meeting abstract|"
    r"congress|news)\b", re.I)

def norm(v):
    if pd.isna(v):
        return ""
    return str(v).strip().upper()

def content_norm(df):
    cols = ["Title", "Abstract", "Keywords", "MeSH Terms"]
    return df[cols].fillna("").astype(str).agg(" | ".join, axis=1).str.lower()

def find_input(input_dir):
    xlsx = input_dir / "Literature_Classified.xlsx"
    csv = input_dir / "Literature_Classified.csv"
    if xlsx.exists():
        return xlsx
    if csv.exists():
        return csv
    raise FileNotFoundError(
        f"No Literature_Classified.xlsx or Literature_Classified.csv found in {input_dir}. "
        "The script intentionally does not fall back to raw retrieval files."
    )

def load(path):
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)

def validate(df):
    missing_c = [c for c in REQUIRED_CLASSIFIER if c not in df.columns]
    missing_s = [c for c in REQUIRED_SOURCE if c not in df.columns]
    if missing_c or missing_s:
        if missing_c:
            print("Missing classifier fields:", ", ".join(missing_c))
        if missing_s:
            print("Missing source metadata:", ", ".join(missing_s))
        raise RuntimeError("INPUT VALIDATION FAILED")
    print("REQUIRED CLASSIFIER FIELDS: PASS")
    for c in REQUIRED_CLASSIFIER:
        print(f"  ✓ {c}")
    print("REQUIRED SOURCE METADATA: PASS")
    for c in REQUIRED_SOURCE:
        print(f"  ✓ {c}")

def screen(df):
    out = df.copy()
    content = content_norm(df)
    title = df["Title"].fillna("").astype(str).str.lower()

    has = {}
    for name, pat in PATTERNS.items():
        has[name] = content.str.contains(pat, na=False)

    title_has = {}
    for name, pat in PATTERNS.items():
        title_has[name] = title.str.contains(pat, na=False)

    cat = df["Primary Literature Category"].map(norm)
    tier = df["Evidence Tier"].map(norm)
    mech = df["Mechanism Flags"].map(norm)
    sub = df["Subsection Hints"].map(norm)
    role = df["Scientific Role Flags"].map(norm)
    pub = df["Publication Type"].fillna("").astype(str)

    score = np.zeros(len(df), dtype=int)
    reasons = [[] for _ in range(len(df))]

    # 1. Structured classifier evidence
    for i, c in enumerate(cat):
        b = CATEGORY_BASE.get(c, 0)
        score[i] += b
        if b:
            reasons[i].append(f"CATEGORY:{c}")

    # 2. Scientific content signals
    for name, pts in [
        ("resistance", 2),
        ("adaptive", 2),
        ("network", 3),
    ]:
        idx = has[name].to_numpy()
        score += idx.astype(int) * pts
        for i in np.flatnonzero(idx):
            reasons[i].append(f"CONTENT:{name.upper()}")

    explicit = has["resistance"] & (
        has["network"] | has["adaptive"] | has["mechanism"]
    )
    score += explicit.to_numpy().astype(int) * 3
    for i in np.flatnonzero(explicit):
        reasons[i].append("RELATION:RESISTANCE_PLUS_SIGNALING_ADAPTATION")

    # Mechanism flags: positive evidence even when abstracts do not use crosstalk wording.
    mech_signal = mech.str.contains(r"M[1-6]|P[1-4]|C1", regex=True, na=False)
    score += mech_signal.to_numpy().astype(int) * 2
    for i in np.flatnonzero(mech_signal):
        reasons[i].append("CLASSIFIER:MECHANISM_FLAG")

    role_signal = role.str.contains(
        r"MECHANISM|VULNERABILITY|INTERVENTION", regex=True, na=False
    )
    score += role_signal.to_numpy().astype(int) * 2
    for i in np.flatnonzero(role_signal):
        reasons[i].append("CLASSIFIER:MECHANISM_VULNERABILITY_INTERVENTION")

    translational_signal = role.str.contains(
        r"BIOMARKER|TRANSLATION", regex=True, na=False
    )
    score += translational_signal.to_numpy().astype(int)
    for i in np.flatnonzero(translational_signal):
        reasons[i].append("CLASSIFIER:BIOMARKER_OR_TRANSLATION")

    subsection_signal = sub.str.contains(
        r"(?:^|;\s*)(?:1\.[1-3]|2\.[1-3]|3\.[1-3]|4\.[1-3]|5\.[1-3]|6\.[1-3])(?:\s*;|$)",
        regex=True, na=False
    )
    score += subsection_signal.to_numpy().astype(int)
    for i in np.flatnonzero(subsection_signal):
        reasons[i].append("CLASSIFIER:SUBSECTION_HINT")

    title_relation = title_has["resistance"] & (
        title_has["network"] | title_has["adaptive"] | title_has["mechanism"]
    )
    score += title_relation.to_numpy().astype(int) * 3
    for i in np.flatnonzero(title_relation):
        reasons[i].append("TITLE:EXPLICIT_RESISTANCE_SIGNALING_RELATION")

    # 3. Publication-form penalty only. This prevents letters/editorials from
    # dominating acquisition, while reviews/primary articles remain eligible.
    nonprimary = pub.str.contains(NONPRIMARY, na=False)
    score -= nonprimary.to_numpy().astype(int) * 4
    for i in np.flatnonzero(nonprimary):
        reasons[i].append("PUBLICATION:NON_PRIMARY_FORM")

    # 4. Guardrail: clearly non-cancer content without structured Chapter-40 evidence.
    no_cancer = ~has["cancer"]
    weak_structured = ~(mech_signal | role_signal | subsection_signal)
    unrelated_guard = no_cancer & weak_structured & ~explicit
    score -= unrelated_guard.to_numpy().astype(int) * 3
    for i in np.flatnonzero(unrelated_guard):
        reasons[i].append("GUARDRAIL:NO_CANCER_OR_CHAPTER40_SIGNAL")

    # Decision thresholds deliberately leave an auditable REVIEW band.
    decision = np.where(score >= 10, "RETAIN",
                        np.where(score >= 6, "REVIEW", "EXCLUDE"))

    # Additional safety rules:
    # Never exclude a C/D paper with an actual mechanism/vulnerability/intervention
    # classifier signal merely because the score is depressed by publication form.
    safety_keep = (
        cat.isin(["C_MECHANISTIC_PRIMARY", "D_THERAPEUTIC"]) &
        role_signal &
        ~cat.eq("F_EMERGING_DISCOVERY")
    )
    decision = np.where(safety_keep & (decision == "EXCLUDE"), "REVIEW", decision)

    # A review with explicit resistance + signaling/adaptation is retained as framework evidence.
    review_keep = (
        cat.eq("B_MAJOR_REVIEW") & explicit & ~nonprimary
    )
    decision = np.where(review_keep, "RETAIN", decision)

    # Priority
    priority = np.full(len(df), "P4_REFERENCE_ONLY", dtype=object)
    priority[decision == "REVIEW"] = "P3_MANUAL_METADATA_REVIEW"
    priority[decision == "RETAIN"] = "P2_SUPPORTING"

    core = (
        (cat.isin(["C_MECHANISTIC_PRIMARY", "D_THERAPEUTIC"])) &
        explicit & role_signal & ~nonprimary
    )
    priority[core.to_numpy()] = "P1_CORE_FULL_TEXT"

    clinical = (cat.eq("E_TRANSLATIONAL_CLINICAL") & explicit & ~nonprimary)
    priority[clinical.to_numpy()] = "P2_TRANSLATIONAL"

    review_framework = (cat.eq("B_MAJOR_REVIEW") & explicit & ~nonprimary)
    priority[review_framework.to_numpy()] = "P2_REVIEW_FRAMEWORK"

    emerging = (cat.eq("F_EMERGING_DISCOVERY") & explicit & role_signal & ~nonprimary)
    priority[emerging.to_numpy()] = "P3_EMERGING"

    route = np.full(len(df), "LOW_RELEVANCE_OR_REFERENCE", dtype=object)
    route[decision == "REVIEW"] = "MANUAL_METADATA_REVIEW"
    route[decision == "RETAIN"] = "CHAPTER40_RELEVANT_METADATA"
    route[core.to_numpy()] = "CORE_MECHANISTIC_THERAPEUTIC"
    route[clinical.to_numpy()] = "TRANSLATIONAL_RESISTANCE_NETWORK"
    route[review_framework.to_numpy()] = "REVIEW_FRAMEWORK"
    route[emerging.to_numpy()] = "EMERGING_MECHANISTIC_DISCOVERY"

    # Human-readable reason summary
    reason_text = []
    for i, r in enumerate(reasons):
        # Keep unique order.
        seen = set()
        rr = [x for x in r if not (x in seen or seen.add(x))]
        reason_text.append("; ".join(rr[:12]))

    out["Metadata Relevance Score"] = score
    out["Metadata Decision"] = decision
    out["Acquisition Priority"] = priority
    out["Screening Route"] = route
    out["Screening Reason"] = reason_text

    # Explicit signal audit columns
    out["Signal Resistance"] = has["resistance"]
    out["Signal Adaptive"] = has["adaptive"]
    out["Signal Network_Crosstalk"] = has["network"]
    out["Signal Mechanistic"] = has["mechanism"]
    out["Signal Cancer"] = has["cancer"]
    out["Signal Explicit_Resistance_Signaling"] = explicit
    out["Classifier Mechanism Signal"] = mech_signal
    out["Classifier Role Signal"] = role_signal
    out["Classifier Subsection Signal"] = subsection_signal
    out["NonPrimary Publication Form"] = nonprimary

    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=None)
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = ap.parse_args()

    input_path = Path(args.input) if args.input else find_input(DEFAULT_INPUT_DIR)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input: {input_path}")
    df = load(input_path)
    print(f"Records: {len(df):,}")
    validate(df)

    print("\nClassifier category distribution:")
    print(df["Primary Literature Category"].value_counts(dropna=False).to_string())
    print("\nEvidence tier distribution:")
    print(df["Evidence Tier"].value_counts(dropna=False).to_string())

    print("\nSTATUS: INPUT VALIDATION PASSED")
    print("Running classifier-aware conservative metadata triage...")

    out = screen(df)

    xlsx = output_dir / "Chapter40_Metadata_Screened_FINAL.xlsx"
    csv = output_dir / "Chapter40_Metadata_Screened_FINAL.csv"
    summary = output_dir / "Chapter40_Metadata_Screened_FINAL_Summary.txt"

    out.to_excel(xlsx, index=False)
    out.to_csv(csv, index=False)

    with summary.open("w", encoding="utf-8") as f:
        f.write("Chapter 40 Metadata Screening — FINAL\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Input records: {len(out):,}\n")
        f.write(f"Output records: {len(out):,}\n\n")
        f.write("Metadata Decision\n")
        f.write(out["Metadata Decision"].value_counts().to_string())
        f.write("\n\nAcquisition Priority\n")
        f.write(out["Acquisition Priority"].value_counts().to_string())
        f.write("\n\nScreening Route\n")
        f.write(out["Screening Route"].value_counts().to_string())
        f.write("\n\nDecision by Literature Category\n")
        f.write(pd.crosstab(
            out["Primary Literature Category"], out["Metadata Decision"]
        ).to_string())
        f.write("\n\nDecision by Evidence Tier\n")
        f.write(pd.crosstab(
            out["Evidence Tier"], out["Metadata Decision"]
        ).to_string())
        f.write("\n\nScore distribution\n")
        f.write(out["Metadata Relevance Score"].describe().to_string())
        f.write("\n")

    print("\nMetadata Decision")
    print(out["Metadata Decision"].value_counts().to_string())
    print("\nAcquisition Priority")
    print(out["Acquisition Priority"].value_counts().to_string())
    print("\nScreening Route")
    print(out["Screening Route"].value_counts().to_string())
    print("\nDecision by Literature Category")
    print(pd.crosstab(
        out["Primary Literature Category"], out["Metadata Decision"]
    ).to_string())

    print("\nOUTPUTS")
    print(f"  ✓ {xlsx}")
    print(f"  ✓ {csv}")
    print(f"  ✓ {summary}")

if __name__ == "__main__":
    main()
