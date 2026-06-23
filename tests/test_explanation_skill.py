"""Tests for ExplanationSkill — decision trace generation."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.explanation_skill import ExplanationSkill


class TestExplanationSkill(unittest.TestCase):

    def test_generates_decision_trace(self):
        topo = {"topology_type": "FatTree", "node_count": 32, "dominant_link": "RoCE"}
        candidates = [
            {"algorithm": "Ring AllReduce", "score": 82, "latency": 0.5, "bandwidth": 10},
            {"algorithm": "Butterfly", "score": 86, "latency": 0.3, "bandwidth": 9},
            {"algorithm": "Fat-Tree", "score": 93, "latency": 0.2, "bandwidth": 11},
        ]
        r = ExplanationSkill.generate_decision_trace(
            topo, candidates, "Fat-Tree", "Best latency and bandwidth.",
        )
        self.assertIn("summary", r)
        self.assertIn("decision_trace", r)
        self.assertIn("rejected_candidates", r)
        self.assertGreater(len(r["decision_trace"]), 0)

    def test_rejected_candidates_exclude_selected(self):
        topo = {"topology_type": "FullMesh", "node_count": 8, "dominant_link": "HCCS"}
        candidates = [
            {"algorithm": "Mesh", "score": 80, "latency": 0.1, "bandwidth": 12},
            {"algorithm": "Ring AllReduce", "score": 85, "latency": 0.3, "bandwidth": 10},
        ]
        r = ExplanationSkill.generate_decision_trace(topo, candidates, "Ring AllReduce")
        rejected = {c["algorithm"] for c in r["rejected_candidates"]}
        self.assertIn("Mesh", rejected)
        self.assertNotIn("Ring AllReduce", rejected)

    def test_decision_trace_has_six_steps(self):
        topo = {"topology_type": "SingleNode", "node_count": 4, "dominant_link": "HCCS"}
        candidates = [{"algorithm": "Ring AllReduce", "score": 90, "latency": 0.01, "bandwidth": 12}]
        ref = {"status": "good", "need_replan": False}
        r = ExplanationSkill.generate_decision_trace(
            topo, candidates, "Ring AllReduce", "ok", ref,
        )
        self.assertGreaterEqual(len(r["decision_trace"]), 5)

    def test_summary_contains_topology_type(self):
        topo = {"topology_type": "MultiNode FatTree", "node_count": 64, "dominant_link": "RoCE"}
        candidates = [{"algorithm": "Fat-Tree", "score": 88, "latency": 0.5, "bandwidth": 9}]
        r = ExplanationSkill.generate_decision_trace(topo, candidates, "Fat-Tree")
        self.assertIn("MultiNode FatTree", r["summary"])


if __name__ == "__main__":
    unittest.main()
