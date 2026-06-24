"""Tests for bottleneck detection."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.optimization_proposal_skill import OptimizationProposalSkill


class TestBottleneckDetection(unittest.TestCase):

    def test_high_latency_bottleneck(self):
        r = {"algorithm": "Ring", "score": 80, "latency": 5.0, "bandwidth": 10}
        p = OptimizationProposalSkill.generate_proposal(
            r, [{"algorithm": "Ring", "score": 80}], {"node_count": 8},
        )
        types = [b["type"] for b in p["detected_bottlenecks"]]
        self.assertIn("Latency", types)

    def test_low_bandwidth_bottleneck(self):
        r = {"algorithm": "Mesh", "score": 60, "latency": 0.1, "bandwidth": 2.0}
        p = OptimizationProposalSkill.generate_proposal(
            r, [{"algorithm": "Mesh", "score": 60}], {"node_count": 8},
        )
        types = [b["type"] for b in p["detected_bottlenecks"]]
        self.assertIn("Bandwidth", types)

    def test_no_bottlenecks(self):
        r = {"algorithm": "NHR", "score": 95, "latency": 0.01, "bandwidth": 12}
        p = OptimizationProposalSkill.generate_proposal(
            r, [{"algorithm": "NHR", "score": 95}], {"node_count": 4},
        )
        types = [b["type"] for b in p["detected_bottlenecks"]]
        self.assertIn("None", types)


if __name__ == "__main__":
    unittest.main()
