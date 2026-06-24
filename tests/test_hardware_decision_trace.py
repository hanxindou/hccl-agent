"""Tests: hardware info in decision trace."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.explanation_skill import ExplanationSkill


class TestHardwareDecisionTrace(unittest.TestCase):

    def test_hardware_in_trace(self):
        topo = {"topology_type": "FullMesh", "node_count": 8, "dominant_link": "HCCS"}
        hw = {"num_nodes": 1, "total_devices": 8, "numa_domains": 2, "hbm_capacity_gb": 64}
        candidates = [{"algorithm": "Ring AllReduce", "score": 90, "latency": 0.01, "bandwidth": 12}]
        r = ExplanationSkill.generate_decision_trace(
            topo, candidates, "Ring AllReduce", hardware_analysis=hw,
        )
        first = r["decision_trace"][0]
        self.assertIn("Hardware", first)
        self.assertIn("64", first)


if __name__ == "__main__":
    unittest.main()
