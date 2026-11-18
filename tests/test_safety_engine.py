"""
tests/test_safety_engine.py
===========================
Unit tests for the MedGuard Safety Engine (backend/interactions.py).

This module tests the four core safety checks:
1. Unidentified medication detection
2. Duplicate active ingredient detection
3. Known drug-drug interaction detection
4. Safe medication verification (no false positives)

Test Approach:
- Tests construct normalized medicine lists matching the structure
  returned by rxnorm.normalize_drugs()
- Tests call run_safety_engine() and validate report structure
- Tests use real interaction data from backend/data/interactions_seed.json
- Tests use real Beers criteria data from backend/data/beers_elderly.json
"""

import unittest
import sys
import os

# Add the project root to Python path so we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.interactions import run_safety_engine


class TestUnidentifiedMedication(unittest.TestCase):
    """
    Test Case 1: Unidentified medication handling.

    REQUIREMENT: An unidentified medicine must appear in report["unmatched"].
    The assessment must not report an all-clear result when a medicine
    remains unchecked.

    This is a critical safety check: we must never falsely mark an unknown
    drug as "safe".
    """

    def test_unidentified_drug_appears_in_unmatched_and_prevents_ok_status(self):
        """
        When a drug name cannot be normalized (not in cache, not in RxNav),
        the safety engine must:
        1. Include it in the "unmatched" list
        2. Set summary["ok"] = False (NOT safe)
        """
        # Construct a normalized medicine list with an unknown drug
        # This matches the structure returned by rxnorm.normalize_drugs()
        unknown_drug = "SomeUnknownBrand123XYZ"
        normalized_meds = [
            {
                "input": unknown_drug,
                "normalized": unknown_drug.lower(),
                "ingredient": None,  # No ingredient found
                "rxcui": None,
                "matched": False  # Explicitly marked as unmatched
            }
        ]

        report = run_safety_engine(normalized_meds, patient_age=0)

        # Verify the unknown drug appears in unmatched list
        self.assertIn(
            unknown_drug,
            [med["input"] for med in report["unmatched"]],
            f"Unknown drug '{unknown_drug}' should be in report['unmatched']"
        )

        # Verify summary["ok"] is False (NOT safe)
        self.assertFalse(
            report["summary"]["ok"],
            "Summary ok should be False when there are unmatched medications"
        )

        # Verify no findings (unmatched drugs don't generate findings)
        self.assertEqual(
            len(report["findings"]),
            0,
            "Unmatched drugs should not generate safety findings"
        )


class TestDuplicateIngredients(unittest.TestCase):
    """
    Test Case 2: Duplicate active ingredient detection.

    REQUIREMENT: Two medicines with the same active ingredient must produce
    a finding with type == "duplicate".

    This catches dangerous scenarios like:
    - Patient taking both "Brufen 400" and "Advil 200"
    - Both contain "ibuprofen" â†’ accidental double dosing
    """

    def test_two_brands_with_same_ingredient_generates_duplicate_finding(self):
        """
        When a patient takes two different brand names that share the same
        active ingredient, the engine must detect this and generate a
        duplicate-finding with type == "duplicate".
        """
        # Brufen and Advil are both ibuprofen
        normalized_meds = [
            {
                "input": "Brufen 400",      # Brand name 1
                "normalized": "brufen 400",
                "ingredient": "ibuprofen",  # Same active ingredient
                "rxcui": None,
                "matched": True
            },
            {
                "input": "Advil 200",       # Brand name 2
                "normalized": "advil 200",
                "ingredient": "ibuprofen",  # Same active ingredient
                "rxcui": None,
                "matched": True
            }
        ]

        report = run_safety_engine(normalized_meds, patient_age=0)

        # Verify a duplicate finding was generated
        duplicate_findings = [
            f for f in report["findings"]
            if f["type"] == "duplicate"
        ]

        self.assertGreater(
            len(duplicate_findings),
            0,
            "Expected a duplicate finding for same-ingredient drugs"
        )

        # Verify the finding details
        duplicate = duplicate_findings[0]
        self.assertEqual(
            duplicate["type"],
            "duplicate",
            "Finding type should be 'duplicate'"
        )
        self.assertEqual(
            duplicate["severity"],
            "high",
            "Duplicate ingredient findings should be high severity"
        )
        self.assertIn(
            "ibuprofen",
            duplicate["ingredients"],
            "Finding should mention the shared ingredient"
        )
        self.assertIn(
            "Brufen 400",
            duplicate["drugs"],
            "Finding should list both brand names"
        )
        self.assertIn(
            "Advil 200",
            duplicate["drugs"],
            "Finding should list both brand names"
        )


class TestKnownInteractions(unittest.TestCase):
    """
    Test Case 3: Known drug-drug interaction detection.

    REQUIREMENT: Warfarin and ibuprofen must produce an interaction finding,
    but only if this pair exists in the project's interaction dataset.

    We verify against the actual data in interactions_seed.json first,
    then test the behavior.
    """

    def test_warfarin_ibuprofen_interaction_exists_in_data(self):
        """
        FIRST: Verify that warfarin + ibuprofen exists in our interaction data.

        The data uses lowercase ingredient names and sorted alphabetical keys.
        Warfarin + ibuprofen â†’ key = "ibuprofen|warfarin"
        """
        import json
        from pathlib import Path

        data_path = Path(__file__).parent.parent / "backend" / "data" / "interactions_seed.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        interaction_keys = set()
        for interaction in data["interactions"]:
            key = "|".join(sorted([interaction["drug_a"], interaction["drug_b"]]))
            interaction_keys.add(key)

        # Verify the pair exists
        warfarin_ibuprofen_key = "ibuprofen|warfarin"
        self.assertIn(
            warfarin_ibuprofen_key,
            interaction_keys,
            "Warfarin + Ibuprofen interaction should exist in interactions_seed.json"
        )

    def test_warfarin_ibuprofen_pair_generates_interaction_finding(self):
        """
        THEN: When a patient takes both warfarin and ibuprofen,
        the engine must generate an interaction finding.

        Severity should be "high" based on the interaction data.
        """
        normalized_meds = [
            {
                "input": "Warfarin 5mg",    # Original input for display
                "normalized": "warfarin 5mg",
                "ingredient": "warfarin",   # The normalized ingredient
                "rxcui": None,
                "matched": True
            },
            {
                "input": "Ibuprofen 400mg",
                "normalized": "ibuprofen 400mg",
                "ingredient": "ibuprofen",
                "rxcui": None,
                "matched": True
            }
        ]

        report = run_safety_engine(normalized_meds, patient_age=0)

        # Verify an interaction finding was generated
        interaction_findings = [
            f for f in report["findings"]
            if f["type"] == "interaction"
        ]

        self.assertGreater(
            len(interaction_findings),
            0,
            "Expected an interaction finding for warfarin + ibuprofen"
        )

        # Verify the finding details
        interaction = interaction_findings[0]
        self.assertEqual(
            interaction["type"],
            "interaction",
            "Finding type should be 'interaction'"
        )
        self.assertEqual(
            interaction["severity"],
            "high",
            "Warfarin + Ibuprofen should be high severity"
        )
        self.assertIn(
            "warfarin",
            interaction["ingredients"],
            "Finding should list both ingredients"
        )
        self.assertIn(
            "ibuprofen",
            interaction["ingredients"],
            "Finding should list both ingredients"
        )
        # Check title mentions both drugs (original input, not ingredient)
        self.assertIn(
            "Warfarin",
            interaction["title"],
            "Title should reference the original drug names"
        )
        self.assertIn(
            "Ibuprofen",
            interaction["title"],
            "Title should reference the original drug names"
        )


class TestSafeMedications(unittest.TestCase):
    """
    Test Case 4: Safe medication verification (no false positives).

    REQUIREMENT: Metformin alone should produce no findings, provided this
    matches the current safety-engine rules and data.

    This test verifies we don't have false positives â€” a safe medication
    shouldn't generate warnings.
    """

    def test_metformin_alone_generates_no_findings(self):
        """
        When a patient takes only metformin (a common diabetes medication),
        the engine should return an all-clear report with no findings.

        Based on interactions_seed.json:
        - Metformin only interacts with "contrast dye"
        - Metformin is NOT in the Beers criteria list

        Therefore, metformin alone should produce:
        - Zero findings
        - summary["ok"] == True
        """
        normalized_meds = [
            {
                "input": "Glycomet 500mg",
                "normalized": "glycomet 500mg",
                "ingredient": "metformin",
                "rxcui": None,
                "matched": True
            }
        ]

        report = run_safety_engine(normalized_meds, patient_age=0)

        # Verify no findings
        self.assertEqual(
            len(report["findings"]),
            0,
            "Metformin alone should produce no safety findings"
        )

        # Verify ok status
        self.assertTrue(
            report["summary"]["ok"],
            "Metformin alone should result in ok=True (all-clear)"
        )

        # Verify the medicine is matched and not in unmatched list
        self.assertEqual(
            len(report["unmatched"]),
            0,
            "Metformin should be recognized and not in unmatched list"
        )
        self.assertEqual(
            len(report["medicines"]),
            1,
            "Metformin should appear in matched medicines list"
        )
        self.assertEqual(
            report["medicines"][0]["ingredient"],
            "metformin",
            "Medicine should have correct ingredient"
        )


# ==============================================================================
# Additional edge case tests (for completeness)
# ==============================================================================

class TestEmptyMedicationList(unittest.TestCase):
    """Test edge case: empty medication list."""

    def test_empty_list_returns_ok_status(self):
        """An empty medication list should return ok=True."""
        report = run_safety_engine([], patient_age=0)
        self.assertTrue(report["summary"]["ok"])


class TestSingleUnknownMedication(unittest.TestCase):
    """Test edge case: single unknown medication."""

    def test_single_unknown_not_ok(self):
        """A single unknown medication should not result in ok=True."""
        normalized_meds = [
            {
                "input": "UnknownDrug123",
                "normalized": "unknowndrug123",
                "ingredient": None,
                "rxcui": None,
                "matched": False
            }
        ]
        report = run_safety_engine(normalized_meds, patient_age=0)
        self.assertFalse(report["summary"]["ok"])



class TestAssessmentCompleteness(unittest.TestCase):
    """
    Test Case 5: Assessment completeness (new feature).
    
    REQUIREMENT: The report must include an "assessment_complete" field
    that is True only when all medicines are recognized (no unmatched items).
    """

    def test_assessment_complete_false_when_unmatched_exists(self):
        """When there are unmatched medicines, assessment_complete must be False."""
        normalized_meds = [
            {
                "input": "UnknownMed123",
                "normalized": "unknownmed123",
                "ingredient": None,
                "rxcui": None,
                "matched": False
            }
        ]
        report = run_safety_engine(normalized_meds, patient_age=0)
        self.assertIn("assessment_complete", report, "Report must include assessment_complete field")
        self.assertFalse(report["assessment_complete"], "Assessment should be incomplete when there are unmatched medicines")
        self.assertFalse(report["summary"]["ok"], "Summary ok should also be False")

    def test_assessment_complete_true_when_all_medicines_recognized(self):
        """When all medicines are recognized, assessment_complete must be True."""
        normalized_meds = [
            {
                "input": "Glycomet 500mg",
                "normalized": "glycomet 500mg",
                "ingredient": "metformin",
                "rxcui": None,
                "matched": True
            }
        ]
        report = run_safety_engine(normalized_meds, patient_age=0)
        self.assertIn("assessment_complete", report, "Report must include assessment_complete field")
        self.assertTrue(report["assessment_complete"], "Assessment should be complete when all medicines are recognized")
        self.assertTrue(report["summary"]["ok"], "Summary ok should be True")
        self.assertEqual(len(report["unmatched"]), 0, "No unmatched medicines expected")

    def test_assessment_complete_false_with_mixed_known_unknown(self):
        """When some medicines are unknown, assessment_complete must be False."""
        normalized_meds = [
            {
                "input": "Glycomet 500mg",
                "normalized": "glycomet 500mg",
                "ingredient": "metformin",
                "rxcui": None,
                "matched": True
            },
            {
                "input": "UnknownDrugXYZ",
                "normalized": "unknowndrugxyz",
                "ingredient": None,
                "rxcui": None,
                "matched": False
            }
        ]
        report = run_safety_engine(normalized_meds, patient_age=0)
        self.assertFalse(report["assessment_complete"], "Assessment should be incomplete with unknown medicines")
        self.assertEqual(len(report["unmatched"]), 1, "Should have exactly 1 unmatched medicine")
        self.assertEqual(len(report["medicines"]), 1, "Should have exactly 1 matched medicine")


if __name__ == "__main__":
    unittest.main()

