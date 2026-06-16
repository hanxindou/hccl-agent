"""Tests for ReportGenerator — text report formatting."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.report_generator import ReportGenerator


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.gen = ReportGenerator()

    def test_generates_report_with_all_fields(self):
        exec_result = {
            "algorithm": "Ring AllReduce",
            "latency": 22.4,
            "bandwidth": 96.0,
            "score": 60.48,
        }
        eval_result = {
            "grade": "GOOD",
            "recommendation": "Keep current algorithm.",
        }
        report = self.gen.generate_report(exec_result, eval_result)
        self.assertIn("Execution Report", report)
        self.assertIn("Ring AllReduce", report)
        self.assertIn("22.4", report)
        self.assertIn("96.0", report)
        self.assertIn("60.48", report)
        self.assertIn("GOOD", report)
        self.assertIn("Keep current algorithm.", report)

    def test_report_has_expected_sections(self):
        report = self.gen.generate_report(
            {"algorithm": "Mesh", "latency": 0, "bandwidth": 0, "score": 0},
            {"grade": "POOR", "recommendation": "Replace."},
        )
        self.assertIn("Algorithm:", report)
        self.assertIn("Latency:", report)
        self.assertIn("Bandwidth:", report)
        self.assertIn("Score:", report)
        self.assertIn("Evaluation:", report)
        self.assertIn("Recommendation:", report)

    def test_report_with_missing_keys(self):
        report = self.gen.generate_report({}, {})
        self.assertIn("Unknown", report)
        self.assertIn("N/A", report)


if __name__ == "__main__":
    unittest.main()
