"""
interactions.py — The MedGuard Safety Engine
=============================================
Purpose: Given a list of normalized drug ingredients (from rxnorm.py),
run three clinical safety checks and return a structured findings list.

THE THREE CHECKS (in order of execution):
  1. Duplicate Active Ingredient Detection
     → Same molecule, different brand names → immediate 🔴 DANGER
  2. Pairwise Drug-Drug Interaction Check
     → Every pair of ingredients checked against our curated seed data
  3. Beers Criteria Check (elderly patients, age >= 65)
     → Individual drug checked against geriatric warning list

DESIGN PRINCIPLES:
  - This module is PURELY deterministic — no AI, no randomness
  - Input: list of ingredient strings → Output: list of Finding objects
  - The LLM (explainer.py) only ever READS these findings, never modifies them
  - "Facts from data, words from the model" — this is where facts live

TEACHING NOTE — What is "combinatorics" / pairwise checking?
  If you have drugs [A, B, C, D], the pairs are: AB, AC, AD, BC, BD, CD
  That's n×(n-1)/2 combinations. Python's itertools.combinations()
  generates these efficiently without writing nested loops manually.
  For n=5 drugs → 10 pairs. For n=10 drugs → 45 pairs.
  Google checks 1 pair at a time. We check all 45 in one API call.
"""

import json
import logging
import itertools  # Python standard library — tools for working with sequences
from pathlib import Path  # Better than os.path for handling file paths

logger = logging.getLogger(__name__)

# =============================================================================
# DATA LOADING — Load datasets once at module startup
# =============================================================================
# TEACHING NOTE — Why load at module startup and not inside each function?
# Loading from disk is slow (I/O). If we loaded inside each function,
# we'd re-read the JSON file on EVERY API request (hundreds of times per minute).
# Loading once at startup means the data lives in memory — instant access.
# This is called "eager loading" or "module-level initialization."

# Path(__file__) = the path to THIS file (interactions.py)
# .parent = the folder containing it (backend/)
# / "data" / "..." = path joining (Path uses / operator for this)
_DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename: str) -> dict:
    """
    Helper to load a JSON file from the data directory.
    Returns empty dict on any error to prevent crashing.
    """
    filepath = _DATA_DIR / filename
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Data file not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return {}


# Load both datasets into module-level variables (loaded once, reused forever)
_INTERACTIONS_DATA = _load_json("interactions_seed.json")
_BEERS_DATA = _load_json("beers_elderly.json")

# Build a fast lookup structure for interactions
# Instead of searching through the list every time, we build a dictionary
# keyed by a "canonical pair key": sorted drug pair joined by "|"
# Example: (warfarin, ibuprofen) → key = "ibuprofen|warfarin" (sorted alphabetically)
# WHY SORT? "warfarin+ibuprofen" and "ibuprofen+warfarin" are the same pair.
# Sorting ensures we always generate the same key regardless of order.
_INTERACTION_LOOKUP: dict[str, dict] = {}
for interaction in _INTERACTIONS_DATA.get("interactions", []):
    key = "|".join(sorted([interaction["drug_a"], interaction["drug_b"]]))
    _INTERACTION_LOOKUP[key] = interaction

# Build a fast lookup for Beers Criteria: ingredient name → warning entry
_BEERS_LOOKUP: dict[str, dict] = {}
for warning in _BEERS_DATA.get("elderly_warnings", []):
    _BEERS_LOOKUP[warning["ingredient"]] = warning

logger.info(
    f"Safety engine loaded: {len(_INTERACTION_LOOKUP)} interaction pairs, "
    f"{len(_BEERS_LOOKUP)} Beers Criteria entries"
)

# =============================================================================
# SEVERITY RANKING — for sorting findings
# =============================================================================
# We want findings sorted: high → moderate → low
# Python's sort() can use a "key" function to determine sort order.
# We map severity strings to integers: high=0 (sorts first), moderate=1, low=2
SEVERITY_ORDER = {"high": 0, "moderate": 1, "low": 2}


# =============================================================================
# CHECK 1: DUPLICATE ACTIVE INGREDIENT DETECTOR
# =============================================================================

def check_duplicate_ingredients(normalized_meds: list[dict]) -> list[dict]:
    """
    Detect cases where multiple brand-name medicines share the same active ingredient.

    This is the "wow factor" of MedGuard:
    "Grandma is taking Brufen 400 AND Advil 200 — she doesn't know
    they're BOTH ibuprofen. She's accidentally double-dosing."

    HOW IT WORKS:
      1. Group medicines by their ingredient
      2. Any ingredient appearing more than once is a DUPLICATE
      3. Generate a 🔴 HIGH severity finding for each duplicate group

    TEACHING NOTE — collections.defaultdict:
      defaultdict(list) is like a regular dict, but if you access a
      key that doesn't exist, it AUTOMATICALLY creates it with a
      default value (here, an empty list []).
      Without it: if "ibuprofen" not in groups: groups["ibuprofen"] = []
      With it:    groups["ibuprofen"].append(...)  # works even first time

    Args:
        normalized_meds: list of dicts from rxnorm.normalize_drugs()
                         Each dict has keys: input, ingredient, matched, etc.
    Returns:
        list of finding dicts, one per duplicate ingredient found
    """
    from collections import defaultdict  # imported here to show it's a standard library tool

    # Group by ingredient — only consider matched (known) drugs
    ingredient_groups: dict[str, list[str]] = defaultdict(list)
    for med in normalized_meds:
        if med.get("matched") and med.get("ingredient"):
            ingredient_groups[med["ingredient"]].append(med["input"])

    findings = []
    for ingredient, brand_names in ingredient_groups.items():
        if len(brand_names) > 1:  # Duplicate! More than one brand → same ingredient
            findings.append({
                "severity": "high",
                "type": "duplicate",
                "drugs": brand_names,           # Original user-typed names
                "ingredients": [ingredient],    # The shared active ingredient
                "title": f"Duplicate Ingredient: '{ingredient.title()}' appears in {len(brand_names)} medicines",
                "detail": (
                    f"You have {len(brand_names)} different medicines that all contain "
                    f"'{ingredient}' as their active ingredient: {', '.join(brand_names)}. "
                    f"This means you may be taking a double (or triple) dose of {ingredient} "
                    f"without realizing it. This is a very common mistake when medicines "
                    f"are prescribed by different doctors."
                ),
                "source": "MedGuard Ingredient Normalization (RxNorm)"
            })
            logger.info(f"Duplicate detected: '{ingredient}' in {brand_names}")

    return findings


# =============================================================================
# CHECK 2: PAIRWISE DRUG-DRUG INTERACTION CHECKER
# =============================================================================

def check_pairwise_interactions(normalized_meds: list[dict]) -> list[dict]:
    """
    Check every possible pair of drugs for known dangerous interactions.

    WHY PAIRWISE?
    With N drugs, there are N*(N-1)/2 unique pairs to check.
    5 drugs → 10 pairs. 8 drugs → 28 pairs.
    We check ALL of them. A user manually searching Google would have
    to do 10 separate searches. We do it in milliseconds.

    HOW itertools.combinations WORKS:
      combinations(["A", "B", "C"], 2) generates: (A,B), (A,C), (B,C)
      The 2 means "take 2 at a time". Order doesn't matter (A,B == B,A).

    HOW THE LOOKUP WORKS:
      1. For pair (warfarin, ibuprofen):
         → key = sorted → ["ibuprofen", "warfarin"] → "ibuprofen|warfarin"
         → check _INTERACTION_LOOKUP["ibuprofen|warfarin"]
         → Found! → add finding
      2. For pair (lisinopril, omeprazole):
         → key = "lisinopril|omeprazole"
         → Not in lookup → safe (or at least not in our dataset)

    Args:
        normalized_meds: list of dicts from rxnorm.normalize_drugs()
    Returns:
        list of finding dicts, one per interaction found
    """
    # Only work with matched (known) drugs
    matched_meds = [m for m in normalized_meds if m.get("matched") and m.get("ingredient")]

    if len(matched_meds) < 2:
        # Need at least 2 drugs to check interactions
        return []

    findings = []

    # itertools.combinations generates all unique pairs without repetition
    for med_a, med_b in itertools.combinations(matched_meds, 2):
        ingredient_a = med_a["ingredient"]
        ingredient_b = med_b["ingredient"]

        # Generate the canonical lookup key (sorted alphabetically)
        pair_key = "|".join(sorted([ingredient_a, ingredient_b]))

        # Look up in our pre-built interaction dictionary
        interaction = _INTERACTION_LOOKUP.get(pair_key)

        if interaction:
            finding = {
                "severity": interaction["severity"],
                "type": "interaction",
                # Show user-friendly names (original input), not ingredient names
                "drugs": [med_a["input"], med_b["input"]],
                "ingredients": [ingredient_a, ingredient_b],
                "title": interaction["title"],
                "detail": interaction["detail"],
                "source": interaction["source"]
            }
            findings.append(finding)
            logger.info(
                f"Interaction found: '{ingredient_a}' + '{ingredient_b}' "
                f"[{interaction['severity']}]"
            )

    return findings


# =============================================================================
# CHECK 3: BEERS CRITERIA — ELDERLY-SPECIFIC WARNINGS
# =============================================================================

def check_beers_criteria(normalized_meds: list[dict], patient_age: int) -> list[dict]:
    """
    Apply Beers Criteria warnings for elderly patients (age >= 65).

    The AGS Beers Criteria is a peer-reviewed list of medications that
    are "potentially inappropriate" for older adults — drugs that are
    commonly prescribed but carry disproportionate risks in the elderly
    due to age-related changes in metabolism, kidney function, and
    brain sensitivity.

    WHY AGE 65?
    That's the clinical threshold defined by the American Geriatrics
    Society (AGS) in their Beers Criteria guidelines. It's also the
    most memorable and universally recognized cutoff for "elderly" in
    pharmacology.

    Args:
        normalized_meds: list of dicts from rxnorm.normalize_drugs()
        patient_age: integer (if 0 or None, this check is skipped)
    Returns:
        list of finding dicts, one per Beers warning triggered
    """
    if not patient_age or patient_age < 65:
        return []  # Beers Criteria only applies to patients 65+

    findings = []
    for med in normalized_meds:
        if not med.get("matched") or not med.get("ingredient"):
            continue

        ingredient = med["ingredient"]
        beers_entry = _BEERS_LOOKUP.get(ingredient)

        if beers_entry:
            finding = {
                "severity": beers_entry["severity"],
                "type": "beers_elderly",
                "drugs": [med["input"]],
                "ingredients": [ingredient],
                "title": beers_entry["title"],
                "detail": beers_entry["detail"],
                "source": beers_entry["source"],
                "drug_class": beers_entry.get("drug_class", "")
            }
            findings.append(finding)
            logger.info(f"Beers Criteria hit: '{ingredient}' for patient age {patient_age}")

    return findings


# =============================================================================
# CHECK 4: PATIENT ALLERGY CONFLICT DETECTION
# =============================================================================

def check_allergy_conflicts(
    normalized_meds: list[dict],
    patient_allergies: list[str] = None
) -> list[dict]:
    """
    Check if any prescribed medicine conflicts with the patient's documented allergies.

    Example:
      Patient allergic to: "Aspirin"
      Prescribed: "Ecosprin 75mg" (Active ingredient: "aspirin")
      → Flags Critical Allergy Contraindication.
    """
    if not patient_allergies:
        return []

    findings = []
    # Clean and lowercase all allergy terms
    clean_allergies = [a.lower().strip() for a in patient_allergies if a and a.strip()]

    for med in normalized_meds:
        if not med.get("matched"):
            continue

        ingredient = (med.get("ingredient") or "").lower().strip()
        input_name = med.get("input", "").lower().strip()

        for allergy in clean_allergies:
            # Check if allergy matches ingredient, or is contained within the ingredient/name
            # Handles broad classes like 'penicillin' vs 'amoxicillin', 'sulfa', etc.
            is_match = (
                allergy == ingredient
                or allergy in ingredient
                or ingredient in allergy
                or allergy in input_name
                or (allergy == "penicillin" and any(p in ingredient for p in ["amoxicillin", "ampicillin", "penicillin"]))
                or (allergy == "nsaid" and any(n in ingredient for n in ["ibuprofen", "aspirin", "naproxen", "diclofenac"]))
            )

            if is_match:
                finding = {
                    "severity": "high",
                    "type": "allergy_conflict",
                    "drugs": [med["input"]],
                    "ingredients": [ingredient],
                    "title": f"Known Allergy Contraindication: {med['input']} ({ingredient.title()})",
                    "detail": (
                        f"The patient has a documented allergy to '{allergy.title()}'. "
                        f"The prescribed medicine '{med['input']}' contains '{ingredient}', "
                        f"which carries a significant risk of allergic reaction."
                    ),
                    "source": "Patient Allergy Profile"
                }
                findings.append(finding)
                logger.warning(f"Allergy conflict detected: '{med['input']}' conflicts with patient allergy '{allergy}'")

    return findings


# =============================================================================
# MAIN ENGINE FUNCTION — runs all checks and assembles the report
# =============================================================================

def run_safety_engine(
    normalized_meds: list[dict],
    patient_age: int = 0,
    patient_allergies: list[str] = None
) -> dict:
    """
    Run all three safety checks and return a complete, structured report.

    This is the function that main.py calls directly.

    REPORT STRUCTURE:
    {
        "medicines": [...],       # Normalized medicine info (input + ingredient)
        "findings": [...],        # All warnings sorted by severity
        "summary": {              # Quick count for the UI badges
            "high": N,
            "moderate": N,
            "low": N,
            "total": N,
            "ok": bool            # True only if ZERO findings
        },
        "unmatched": [...],       # Drugs we couldn't identify
        "disclaimer": "..."       # Mandatory safety disclaimer
    }

    TEACHING NOTE — Why sort findings?
    Users should see the most dangerous findings FIRST.
    Python's sort() with key=lambda uses our SEVERITY_ORDER dict
    to convert "high"→0, "moderate"→1, "low"→2 for comparison.
    Lower number = higher priority = appears first.

    Args:
        normalized_meds: output from rxnorm.normalize_drugs()
        patient_age: patient's age in years (0 = unknown/not provided)
    Returns:
        complete safety report dict
    """
    logger.info(
        f"Running safety engine for {len(normalized_meds)} medicines, "
        f"patient age: {patient_age or 'unknown'}"
    )

    # ─── Run all checks ───────────────────────────────────────────────────────
    duplicate_findings = check_duplicate_ingredients(normalized_meds)
    interaction_findings = check_pairwise_interactions(normalized_meds)
    beers_findings = check_beers_criteria(normalized_meds, patient_age)
    allergy_findings = check_allergy_conflicts(normalized_meds, patient_allergies)

    # ─── Combine all findings ─────────────────────────────────────────────────
    all_findings = duplicate_findings + interaction_findings + beers_findings + allergy_findings

    # ─── Sort by severity (high → moderate → low) ─────────────────────────────
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))

    # ─── Build summary counts ─────────────────────────────────────────────────
    summary = {
        "high": sum(1 for f in all_findings if f["severity"] == "high"),
        "moderate": sum(1 for f in all_findings if f["severity"] == "moderate"),
        "low": sum(1 for f in all_findings if f["severity"] == "low"),
        "total": len(all_findings),
        "ok": len(all_findings) == 0  # True only if absolutely no warnings
    }

    # ─── Separate matched and unmatched medicines ─────────────────────────────
    # Unmatched drugs are flagged as ⚪ "Not Checked" — never green "Safe"
    medicines = []
    unmatched = []

    for med in normalized_meds:
        if med.get("matched"):
            medicines.append({
                "input": med["input"],
                "ingredient": med["ingredient"],
                "rxcui": med.get("rxcui"),
                "matched": True
            })
        else:
            unmatched.append({
                "input": med["input"],
                "matched": False,
                "status": "⚪ Not Checked — drug not recognized in our database"
            })

    # ─── Assemble final report ────────────────────────────────────────────────
    report = {
        "medicines": medicines,
        "unmatched": unmatched,
        "findings": all_findings,
        "summary": summary,
        "patient_age": patient_age if patient_age else None,
        "disclaimer": (
            "⚠️ MedGuard provides decision support only. These findings are "
            "informational and are NOT a substitute for professional medical advice. "
            "Always confirm with your doctor or pharmacist before making any changes "
            "to your medications. Interaction data is sourced from FDA labels, DDInter, "
            "and the AGS Beers Criteria 2023."
        )
    }

    logger.info(
        f"Safety engine complete: {summary['high']} high, "
        f"{summary['moderate']} moderate, {summary['low']} low findings"
    )

    return report
