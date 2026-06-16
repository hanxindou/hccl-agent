"""End-to-end test: Execution → Evaluation → Report."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.hccl_agent import HCCLAgent


class TestExecutionReportFlow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.agent = HCCLAgent()

    def test_full_flow_ring_allreduce_4_ranks(self):
        result = self.agent.generate_execution_report(
            algorithm="Ring AllReduce",
            input_data=[1.0, 2.0, 3.0, 4.0],
        )

        # Execution
        self.assertIn("execution", result)
        self.assertEqual(result["execution"]["status"], "success")
        self.assertEqual(
            result["execution"]["result"],
            [10.0, 10.0, 10.0, 10.0],
        )

        # Evaluation
        self.assertIn("evaluation", result)
        self.assertIn("grade", result["evaluation"])
        self.assertIn("recommendation", result["evaluation"])

        # Report
        self.assertIn("report", result)
        self.assertIn("Execution Report", result["report"])
        self.assertIn("Ring AllReduce", result["report"])

    def test_full_flow_butterfly_success(self):
        result = self.agent.generate_execution_report(
            algorithm="Butterfly",
            input_data=[1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["execution"]["status"], "success")
        self.assertEqual(result["execution"]["result"], [10.0] * 4)
        self.assertIn("evaluation", result)
        self.assertIn("report", result)

    def test_full_flow_nhr_success(self):
        result = self.agent.generate_execution_report(
            algorithm="NHR", input_data=[1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["execution"]["status"], "success")
        self.assertEqual(result["execution"]["result"], [10.0] * 4)
        self.assertIn("report", result)

    def test_full_flow_mesh_success(self):
        result = self.agent.generate_execution_report(
            algorithm="Mesh", input_data=[1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["execution"]["status"], "success")
        self.assertEqual(result["execution"]["result"], [10.0] * 4)

    def test_full_flow_fattree_success(self):
        result = self.agent.generate_execution_report(
            algorithm="Fat-Tree", input_data=[1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["execution"]["status"], "success")
        self.assertEqual(result["execution"]["result"], [10.0] * 4)

    def test_full_flow_not_implemented(self):
        result = self.agent.generate_execution_report(
            algorithm="PairWise",
            input_data=[1.0, 2.0],
        )
        self.assertEqual(result["execution"]["status"], "not_implemented")
        # Evaluation still runs (on the simulated score).
        self.assertIn("evaluation", result)
        self.assertIn("report", result)

    def test_flow_preserves_input_data(self):
        data = [5.0, 15.0, 25.0, 35.0]
        result = self.agent.generate_execution_report(
            algorithm="Ring AllReduce",
            input_data=data,
        )
        expected_sum = sum(data)
        self.assertEqual(
            result["execution"]["result"],
            [expected_sum] * len(data),
        )

    def test_report_printable(self):
        """Print a sample report for visual verification."""
        result = self.agent.generate_execution_report(
            algorithm="Ring AllReduce",
            input_data=[1.0, 2.0, 3.0, 4.0],
        )
        print()
        print(result["report"])
        print(f"Execution status: {result['execution']['status']}")
        print(f"Evaluation grade: {result['evaluation']['grade']}")

        self.assertTrue(len(result["report"]) > 0)


if __name__ == "__main__":
    unittest.main()
