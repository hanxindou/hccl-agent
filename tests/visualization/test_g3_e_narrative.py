import unittest

from tools.visualization.common import OUTPUT_ROOT
from tools.visualization.narrative import NARRATIVE_FILES, build_narrative, validate_narrative


class G3ENarrativeTests(unittest.TestCase):
    def test_narrative_is_claim_safe_and_complete(self):
        result = build_narrative()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["sentinel"], "G3_E_NARRATIVE_OK")
        self.assertEqual(result["document_count"], 5)
        self.assertEqual(result["claim_count"], 21)
        self.assertEqual(result["figure_count"], 13)
        self.assertEqual(result["final_language"], "USER_ACTION_REQUIRED")
        self.assertEqual(result["final_template"], "USER_ACTION_REQUIRED")

    def test_narrative_has_three_layers_and_no_mandatory_online_boundary(self):
        result = validate_narrative()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["layers"], ["30-second", "3-minute", "technical-defense"])
        narrative = (OUTPUT_ROOT / "competition_narrative.md").read_text(encoding="utf-8")
        self.assertIn("SIMULATED_ONLY", narrative)
        self.assertIn("HARDWARE_BLOCKED", narrative)
        self.assertNotIn("fully autonomous", narrative.lower())
        self.assertTrue(all((OUTPUT_ROOT / name).is_file() for name in NARRATIVE_FILES))


if __name__ == "__main__":
    unittest.main()
