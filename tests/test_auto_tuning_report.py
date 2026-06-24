"""Tests: Auto-Tuning Report in generated output."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.hccl_agent import HCCLAgent
from agent.report_generator import ReportGenerator


class TestAutoTuningReport(unittest.TestCase):

    def test_report_contains_auto_tuning_section(self):
        agent = HCCLAgent()
        output = agent.run(nodes=4, message_size=64, primitive="AllReduce")
        report = ReportGenerator.generate_report(
            {"algorithm": output["algorithm"],
             "latency": output["best_result"]["latency"],
             "bandwidth": output["best_result"]["bandwidth"],
             "score": output["best_result"]["score"],
             "auto_tuning": output["auto_tuning"]},
            {"grade": "GOOD", "recommendation": "ok"},
        )
        self.assertIn("Auto-Tuning Report", report)


if __name__ == "__main__":
    unittest.main()
