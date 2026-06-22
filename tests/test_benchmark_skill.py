"""Tests for BenchmarkSkill — execution timing."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.benchmark_skill import BenchmarkSkill


class FakeExecutionSkill:
    def execute(self, algorithm, input_data):
        return {"algorithm": algorithm, "status": "success", "result": [sum(input_data)] * len(input_data)}


class TestBenchmarkSkill(unittest.TestCase):

    def test_execution_time_positive(self):
        skill = BenchmarkSkill(FakeExecutionSkill())
        r = skill.benchmark_execution("Ring AllReduce", [1.0, 2.0, 3.0, 4.0])
        self.assertGreater(r["execution_time_ms"], 0)

    def test_execution_result_present(self):
        skill = BenchmarkSkill(FakeExecutionSkill())
        r = skill.benchmark_execution("Butterfly", [1.0, 2.0])
        self.assertIsNotNone(r["execution_result"])
        self.assertEqual(r["execution_result"]["status"], "success")

    def test_no_execution_skill_returns_default(self):
        skill = BenchmarkSkill()  # no execution skill set
        r = skill.benchmark_execution("Mesh", [1.0])
        self.assertEqual(r["execution_time_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
