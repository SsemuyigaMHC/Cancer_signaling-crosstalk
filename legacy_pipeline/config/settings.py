"""Chapter 40 literature retrieval configuration.

Set NCBI_EMAIL (required by NCBI etiquette) and optionally NCBI_API_KEY in
settings/environment before running PubMed retrieval.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

BROAD_DISCOVERY_STREAMS = {
    # High-recall core discovery. Keep these broad because downstream screening
    # is responsible for final scientific eligibility.
    "BROAD_CORE_FIELD": (
        '(("signaling crosstalk" OR "signalling crosstalk" OR "pathway crosstalk" OR "signaling network" OR "signalling network") AND cancer AND ("drug resistance" OR "therapy resistance" OR "treatment resistance" OR "acquired resistance" OR "adaptive resistance"))',
        '(("adaptive resistance" OR "adaptive response" OR "adaptive reprogramming") AND (signaling OR signalling OR pathway OR network) AND cancer)',
        '(("network rewiring" OR "signaling rewiring" OR "signalling rewiring" OR "adaptive signaling" OR "adaptive signalling") AND cancer AND (resistance OR therapy))',
        '(("compensatory signaling" OR "compensatory signalling" OR "compensatory pathway" OR "alternative pathway" OR "bypass signaling" OR "bypass signalling") AND cancer AND (therapy OR treatment OR drug) AND resistance)',
        '(("non-genetic resistance" OR "nongenetic resistance" OR "drug-tolerant" OR "drug tolerant") AND (signaling OR signalling OR pathway OR network) AND cancer)',
    ),
    # Foundational mechanism discovery. These are intentionally inclusive and
    # do not require the exact phrase "signaling crosstalk".
    "FOUNDATIONAL_MECHANISMS": (
        '(("negative feedback" OR "feedback activation" OR "feedback reactivation" OR "feedback relief") AND ("targeted therapy" OR inhibitor OR treatment) AND cancer AND resistance)',
        '((bypass OR "alternative pathway" OR "alternative signaling" OR "alternative signalling" OR "compensatory pathway") AND (cancer OR tumor OR tumour) AND (resistance OR escape) AND (therapy OR treatment OR inhibitor))',
        '(("parallel pathway" OR "parallel signaling" OR "parallel signalling" OR "redundant signaling" OR "redundant signalling" OR "survival pathway") AND cancer AND resistance)',
        '((convergent OR convergence OR "common downstream" OR "shared effector" OR bottleneck) AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
        '((reciprocal OR bidirectional OR "mutual activation" OR "mutual regulation") AND (signaling OR signalling OR crosstalk OR pathway) AND cancer AND resistance)',
        '(("receptor switching" OR "receptor switch" OR "alternative receptor" OR "receptor dependence" OR "RTK switching") AND cancer AND resistance)',
        '((plasticity OR robustness OR resilience OR "state transition" OR "adaptive state") AND (signaling OR signalling OR network) AND cancer AND (resistance OR therapy))',
    ),
    # Review discovery is constrained enough to reduce obvious noise but still
    # deliberately permissive; reviews are discovery/support material, not the
    # final evidence set.
    "MAJOR_REVIEWS": (
        '((cancer OR tumor OR tumour) AND ("signaling crosstalk" OR "signalling crosstalk" OR "pathway crosstalk" OR "signaling network" OR "signalling network") AND ("drug resistance" OR "therapy resistance" OR "treatment resistance" OR "adaptive resistance"))',
        '((cancer OR tumor OR tumour) AND ("adaptive resistance" OR "adaptive response" OR "adaptive reprogramming") AND (signaling OR signalling OR pathway OR network) AND (review[pt] OR review))',
        '((cancer OR tumor OR tumour) AND ("network rewiring" OR "signaling rewiring" OR "signalling rewiring") AND (resistance OR therapy) AND (review[pt] OR review))',
        '((cancer OR tumor OR tumour) AND ("compensatory signaling" OR "compensatory signalling" OR "bypass signaling" OR "bypass signalling" OR "feedback activation") AND resistance AND (review[pt] OR review))',
        '((cancer OR tumor OR tumour) AND (systems biology OR network pharmacology OR network modeling OR "network modelling") AND (drug resistance OR therapy resistance) AND (review[pt] OR review))',
    ),
}

TARGETED_SEARCH_STREAMS = {
    "MECHANISM_M1_BYPASS": (
        '((bypass OR "bypass signaling" OR "bypass signalling" OR "alternative pathway" OR "alternative signaling" OR "alternative signalling") AND cancer AND ("drug resistance" OR "therapy resistance" OR "acquired resistance"))',
        '(("compensatory pathway" OR "compensatory signaling" OR "compensatory signalling") AND cancer AND (targeted therapy OR inhibitor) AND resistance)',
        '(("pathway reactivation" OR "alternative pathway activation") AND cancer AND resistance)',
    ),
    "MECHANISM_M2_FEEDBACK": (
        '(("negative feedback" OR "feedback activation" OR "feedback reactivation" OR "feedback relief") AND (targeted therapy OR inhibitor OR treatment) AND cancer AND resistance)',
        '(("feedback loop" OR "feedback loops") AND (signaling OR signalling) AND cancer AND (adaptive resistance OR drug resistance))',
        '((ERK OR MAPK OR PI3K OR AKT OR mTOR OR EGFR OR RTK) AND "negative feedback" AND resistance AND cancer)',
    ),
    "MECHANISM_M3_PARALLEL_SURVIVAL": (
        '(("parallel pathway" OR "parallel signaling" OR "parallel signalling" OR "parallel survival" OR "redundant signaling" OR "redundant signalling") AND cancer AND resistance)',
        '(("compensatory survival" OR "survival signaling" OR "survival signalling" OR "alternative survival pathway") AND cancer AND therapy resistance)',
        '((coactivation OR "co-activation" OR "pathway co-activation") AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
        '((PI3K OR AKT OR mTOR OR MAPK OR ERK OR JAK OR STAT OR NF-kB OR WNT OR NOTCH OR HEDGEHOG) AND (compensatory OR alternative OR parallel) AND cancer AND resistance)',
    ),
    "MECHANISM_M4_CONVERGENCE": (
        '(("signaling convergence" OR "signalling convergence" OR "convergent signaling" OR "convergent signalling") AND cancer AND resistance)',
        '(("common downstream" OR "shared downstream" OR "shared effector" OR "common effector" OR bottleneck) AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
        '(("pathway convergence" OR "network convergence") AND cancer AND (drug resistance OR therapy resistance))',
    ),
    "MECHANISM_M5_RECIPROCAL": (
        '(("reciprocal signaling" OR "reciprocal signalling" OR "bidirectional crosstalk" OR "bidirectional signaling" OR "bidirectional signalling") AND cancer AND resistance)',
        '(("mutual activation" OR "mutual regulation" OR "positive feedback") AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
        '(("cross-regulation" OR "cross regulation") AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
    ),
    "MECHANISM_M6_RECEPTOR_SWITCHING": (
        '(("receptor switching" OR "receptor switch" OR "RTK switching" OR "receptor switching") AND cancer AND resistance)',
        '(("alternative receptor" OR "alternative RTK" OR "receptor dependence" OR "ligand switching") AND cancer AND (acquired resistance OR drug resistance OR therapy resistance))',
        '((EGFR OR HER2 OR ERBB OR MET OR AXL OR FGFR OR IGF1R OR PDGFR OR RET OR ALK OR ROS1) AND ("receptor switch" OR "alternative receptor" OR "receptor dependence") AND cancer AND resistance)',
    ),
    "SUBSECTION_2_1_REWIRING": (
        '(("therapy-induced" OR "treatment-induced" OR "drug-induced") AND ("signaling rewiring" OR "signalling rewiring" OR "network rewiring" OR "adaptive signaling" OR "adaptive signalling") AND cancer)',
        '(("adaptive signaling state" OR "adaptive signalling state" OR "network reprogramming") AND cancer AND resistance)',
        '(("early adaptive response" OR "early treatment response") AND (signaling OR signalling OR network) AND cancer AND resistance)',
    ),
    "SUBSECTION_2_2_FEEDBACK_ROBUSTNESS": (
        '(("feedback loop" OR "negative feedback" OR "positive feedback" OR robustness OR resilience OR redundancy) AND (signaling OR signalling OR network) AND cancer AND resistance)',
        '(("signaling redundancy" OR "signalling redundancy" OR "network robustness" OR "network resilience") AND cancer AND (drug resistance OR therapy resistance))',
    ),
    "SUBSECTION_2_3_CONTEXT": (
        '(("context-dependent" OR genotype-dependent OR lineage-dependent OR "treatment history") AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
        '((tumor microenvironment OR tumour microenvironment OR stromal OR cytokine OR ligand) AND (signaling OR signalling OR crosstalk) AND cancer AND resistance)',
    ),
    "SUBSECTION_3_1_ACTIONABLE_CROSSTALK": (
        '(("network vulnerability" OR "signaling dependency" OR "signalling dependency" OR "signaling bottleneck" OR "signalling bottleneck") AND cancer AND resistance)',
        '((actionable OR therapeutic) AND ("signaling crosstalk" OR "signalling crosstalk" OR "pathway crosstalk" OR "signaling network") AND cancer AND resistance)',
    ),
    "SUBSECTION_3_2_OMICS_FUNCTIONAL_GENOMICS": (
        '((multi-omics OR phosphoproteomics OR proteomics OR transcriptomics OR "single-cell" OR "spatial transcriptomics") AND (signaling OR signalling OR network) AND cancer AND resistance)',
        '((functional genomics OR CRISPR OR "genetic screen" OR "perturbation screen") AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
    ),
    "SUBSECTION_3_3_SYSTEMS_NETWORK_PHARMACOLOGY": (
        '((systems biology OR network pharmacology OR network modeling OR "network modelling" OR computational network) AND cancer AND (drug resistance OR therapy resistance) AND (signaling OR signalling OR pathway))',
    ),
    "SUBSECTION_4_1_COMBINATIONS": (
        '((rational combination OR combination therapy OR vertical inhibition OR dual inhibition OR co-inhibition) AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
        '((combination targeted therapy OR dual pathway inhibition) AND cancer AND (adaptive resistance OR acquired resistance))',
    ),
    "SUBSECTION_4_2_SYNTHETIC_LETHALITY": (
        '((synthetic lethality OR synthetic lethal OR multi-target OR multitarget) AND cancer AND (resistance OR acquired resistance) AND (signaling OR signalling OR pathway))',
    ),
    "SUBSECTION_4_3_SYSTEMS_THERAPEUTICS": (
        '((network-based therapy OR network-informed therapy OR multi-node targeting OR systems therapeutics) AND cancer AND resistance)',
        '((network vulnerability OR signaling vulnerability OR signalling vulnerability) AND therapeutic AND cancer AND resistance)',
    ),
    "SUBSECTION_5_1_ADAPTIVE_EVOLUTIONARY": (
        '((adaptive therapy OR adaptive treatment OR evolutionary therapy OR evolutionary treatment) AND cancer AND resistance AND (signaling OR signalling OR pathway))',
        '((treatment scheduling OR dosing schedule OR dynamic treatment) AND cancer AND resistance AND signaling)',
    ),
    "SUBSECTION_5_2_BIOMARKER_GUIDED": (
        '((biomarker-guided OR predictive biomarker OR on-treatment biomarker OR dynamic biomarker) AND (signaling OR signalling OR network) AND cancer AND resistance)',
    ),
    "SUBSECTION_5_3_CLINICAL_TRANSLATION": (
        '((clinical trial OR clinical study OR patient) AND (signaling crosstalk OR signaling network OR adaptive resistance OR resistance) AND cancer AND (combination OR targeted therapy))',
    ),
    "SUBSECTION_6_1_HETEROGENEITY_EVOLUTION": (
        '((intratumoral heterogeneity OR tumour heterogeneity OR tumor heterogeneity OR clonal evolution OR subclonal) AND (signaling OR signalling OR network) AND cancer AND resistance)',
        '((single-cell OR longitudinal) AND (signaling OR signalling) AND cancer AND resistance AND evolution)',
    ),
    "SUBSECTION_6_2_CLINICAL_IMPLEMENTATION": (
        '((longitudinal molecular profiling OR dynamic monitoring OR serial profiling OR adaptive monitoring) AND cancer AND resistance AND therapy)',
    ),
    "SUBSECTION_6_3_EMERGING": (
        '((artificial intelligence OR machine learning OR deep learning OR "network modeling" OR "network modelling") AND (signaling OR signalling OR pathway) AND cancer AND resistance)',
        '((longitudinal single-cell OR spatial profiling OR dynamic network) AND cancer AND (therapy resistance OR adaptive resistance))',
    ),
}

SEARCH_PHASES = {
    "broad": BROAD_DISCOVERY_STREAMS,
    "targeted": TARGETED_SEARCH_STREAMS,
    "all": {**BROAD_DISCOVERY_STREAMS, **TARGETED_SEARCH_STREAMS},
}

@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    data_dir: Path = DATA_DIR
    metadata_dir: Path = DATA_DIR / "metadata"
    full_text_dir: Path = DATA_DIR / "full_text"
    logs_dir: Path = DATA_DIR / "logs"
    external_records_dir: Path = DATA_DIR / "external_records"
    search_exports_dir: Path = DATA_DIR / "search_exports"
    claims_dir: Path = DATA_DIR / "claims"
    entrez_email: str = os.getenv("NCBI_EMAIL", "")
    entrez_api_key: str = os.getenv("NCBI_API_KEY", "")
    ncbi_tool: str = "Chapter40_Literature_Pipeline"
    max_retries: int = 5
    retry_backoff_seconds: float = 2.0
    entrez_batch_size: int = 200
    pubmed_retmax: int = 500
    pubmed_sort: str = "relevance"

SETTINGS = Settings()
PUBMED_SEARCH_STREAMS = SEARCH_PHASES
