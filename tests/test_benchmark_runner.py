"""Tests for benchmark scenario loading and execution."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.benchmark_suite_skill import BenchmarkSuiteSkill


class TestBenchmarkRunner(unittest.TestCase):

    def test_load_all_scenarios(self):
        scenarios = BenchmarkSuiteSkill.load_all_scenarios()
        self.assertGreaterEqual(len(scenarios), 5)

    def test_load_single_scenario(self):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "experiments", "scenarios", "scenario_01_single_node_8gpu.json",
        )
        s = BenchmarkSuiteSkill.load_scenario(path)
        self.assertEqual(s["name"], "single_node_8gpu")
        self.assertEqual(s["nodes"], 8)

    def test_scenario_keys_present(self):
        for s in BenchmarkSuiteSkill.load_all_scenarios():
            for k in ("name", "nodes", "topology", "primitive", "message_size_mb"):
                self.assertIn(k, s)

    def test_run_scenario_requires_agent(self):
        suite = BenchmarkSuiteSkill()
        s = {"name": "test", "nodes": 4, "topology": "Ring",
             "primitive": "AllReduce", "message_size_mb": 128}
        with self.assertRaises(RuntimeError):
            suite.run_scenario(s)


if __name__ == "__main__":
    unittest.main()
