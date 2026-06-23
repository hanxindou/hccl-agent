"""Tests for benchmark report generation."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.benchmark_suite_skill import BenchmarkSuiteSkill


class TestBenchmarkReports(unittest.TestCase):

    def setUp(self):
        self.suite = BenchmarkSuiteSkill()

    def test_generate_scenario_report(self):
        result = {
            "scenario": {"name": "test", "nodes": 8, "topology": "Full Mesh",
                         "primitive": "AllReduce", "message_size_mb": 128},
            "algorithm": "Ring AllReduce", "score": 92.0,
            "latency": 0.01, "bandwidth": 12.0,
            "reflection": {"status": "good", "need_replan": False},
            "decision_trace": {"decision_trace": ["[1] Topology: FullMesh"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            report = self.suite.generate_scenario_report(result, output_dir=tmp)
            self.assertIn("Scenario Information", report)
            self.assertIn("test", report)
            self.assertTrue(os.path.exists(os.path.join(tmp, "test.md")))

    def test_generate_summary(self):
        results = [
            {"scenario": {"name": "s1"}, "algorithm": "Ring AllReduce",
             "score": 90, "latency": 0.1, "bandwidth": 10,
             "reflection": {"decision_quality": {"recommendation": "Near-optimal"}}},
            {"scenario": {"name": "s2"}, "algorithm": "Butterfly",
             "score": 85, "latency": 0.2, "bandwidth": 9,
             "reflection": {"decision_quality": None}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            summary = self.suite.generate_summary(results, output_dir=tmp)
            self.assertIn("s1", summary)
            self.assertIn("Ring AllReduce", summary)
            self.assertIn("s2", summary)
            self.assertTrue(os.path.exists(os.path.join(tmp, "benchmark_summary.md")))


if __name__ == "__main__":
    unittest.main()
