"""End-to-end: Topology → Selection → Explanation."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from hardware.profile import HardwareProfile
from skills.algorithm_selector import AlgorithmSelector
from skills.topology_reasoning_skill import TopologyReasoningSkill
from agent.explanation_skill import ExplanationSkill


class TestDecisionTraceFlow(unittest.TestCase):

    def test_full_flow_topology_to_explanation(self):
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        profile = HardwareProfile.tier_medium()

        topo = TopologyReasoningSkill.analyze(g)
        sel = AlgorithmSelector().select_algorithm("AllReduce", g, profile)

        trace = ExplanationSkill.generate_decision_trace(
            topo, sel["candidates"], sel["algorithm"], sel.get("reason", ""),
        )
        self.assertIn("decision_trace", trace)
        self.assertGreater(len(trace["decision_trace"]), 0)
        self.assertIn(trace["selected_algorithm"], [
            c["algorithm"] for c in sel["candidates"]
        ])

    def test_explanation_includes_topology_info(self):
        g, _ = TopologyGraphBuilder.build(16, num_gpus_per_node=8, mode="MULTI_NODE")
        profile = HardwareProfile.tier_medium()
        topo = TopologyReasoningSkill.analyze(g)
        sel = AlgorithmSelector().select_algorithm("AllReduce", g, profile)
        trace = ExplanationSkill.generate_decision_trace(
            topo, sel["candidates"], sel["algorithm"],
        )
        joined = " ".join(trace["decision_trace"])
        self.assertIn(str(topo["node_count"]), joined)


if __name__ == "__main__":
    unittest.main()
