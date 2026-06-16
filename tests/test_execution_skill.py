"""Tests for ExecutionSkill — Agent-facing execution wrapper."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.execution_skill import ExecutionSkill


class TestExecutionSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.skill = ExecutionSkill()

    def test_execute_ring_allreduce_success(self):
        result = self.skill.execute(
            "Ring AllReduce", [1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["result"],
            [10.0, 10.0, 10.0, 10.0],
        )

    def test_execute_not_implemented(self):
        result = self.skill.execute("Mesh", [1.0, 2.0])
        self.assertEqual(result["status"], "not_implemented")

    def test_execute_butterfly_success(self):
        result = self.skill.execute(
            "Butterfly", [1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [10.0, 10.0, 10.0, 10.0])

    def test_execute_unknown_algorithm(self):
        result = self.skill.execute("BogusAlgo", [1.0])
        self.assertEqual(result["status"], "unknown_algorithm")

    def test_execute_preserves_algorithm_name(self):
        result = self.skill.execute("Ring AllReduce", [1.0, 2.0])
        self.assertEqual(result["algorithm"], "Ring AllReduce")

    def test_execute_empty_input(self):
        result = self.skill.execute("Ring AllReduce", [])
        self.assertEqual(result["status"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
