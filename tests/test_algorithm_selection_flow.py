"""End-to-end: Topology → Selector → Planning → Execution."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from hardware.profile import HardwareProfile
from skills.algorithm_selector import AlgorithmSelector
from skills.topology_reasoning_skill import TopologyReasoningSkill
from agent.planning_skill import PlanningSkill


class TestAlgorithmSelectionFlow(unittest.TestCase):

    def test_full_chain_topology_to_selection(self):
        g, _ = TopologyGraphBuilder.build(16, num_gpus_per_node=8, mode="MULTI_NODE")
        profile = HardwareProfile.tier_medium()

        # 1. Analyze topology.
        topo_info = TopologyReasoningSkill.analyze(g)
        self.assertGreater(topo_info["node_count"], 0)

        # 2. Select algorithm.
        selector = AlgorithmSelector()
        sel = selector.select_algorithm("AllReduce", g, profile)
        self.assertIn(sel["algorithm"], ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"])

        # 3. Generate plan.
        plan = PlanningSkill.create_plan(16, 128, "AllReduce", g, profile)
        self.assertGreater(len(plan), 0)
        step1 = plan[0]
        self.assertIn("candidate_algorithms", step1)

    def test_selection_flow_for_all_primitives(self):
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        profile = HardwareProfile.tier_medium()
        selector = AlgorithmSelector()

        for prim in ["AllReduce", "AllGather", "ReduceScatter"]:
            sel = selector.select_algorithm(prim, g, profile)
            self.assertIn("algorithm", sel)
            self.assertGreater(sel["score"], 0)


if __name__ == "__main__":
    unittest.main()
