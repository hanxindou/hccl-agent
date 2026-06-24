"""Tests for calibration report generation."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.calibration_explanation_skill import CalibrationExplanationSkill
from calibration.calibration_registry import get_registry


class TestCalibrationReport(unittest.TestCase):

    def test_explanation_has_keys(self):
        reg = get_registry()
        expl = CalibrationExplanationSkill.explain(reg.current_profile())
        for k in ("profile_version", "parameter_count", "parameter_summary"):
            self.assertIn(k, expl)

    def test_report_includes_efficiency(self):
        reg = get_registry()
        expl = CalibrationExplanationSkill.explain(reg.current_profile())
        self.assertIn("Algorithm Efficiency", expl["parameter_summary"])


if __name__ == "__main__":
    unittest.main()
