"""End-to-end: AlgorithmSelector → CodeGenerationSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from hardware.profile import HardwareProfile
from skills.algorithm_selector import AlgorithmSelector
from skills.topology_reasoning_skill import TopologyReasoningSkill
from agent.code_generation_skill import CodeGenerationSkill


class TestCodeGenerationFlow(unittest.TestCase):

    def test_selector_to_code_generation(self):
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        profile = HardwareProfile.tier_medium()
        topo = TopologyReasoningSkill.analyze(g)
        sel = AlgorithmSelector().select_algorithm("AllReduce", g, profile)

        cfg = CodeGenerationSkill.generate_hccl_config("AllReduce", sel["algorithm"], topo)
        self.assertEqual(cfg["algorithm"], sel["algorithm"])
        self.assertIn("communication_pattern", cfg)

    def test_full_chain_produces_all_artifacts(self):
        g, _ = TopologyGraphBuilder.build(16, num_gpus_per_node=8, mode="MULTI_NODE")
        profile = HardwareProfile.tier_medium()
        topo = TopologyReasoningSkill.analyze(g)
        sel = AlgorithmSelector().select_algorithm("AllReduce", g, profile)

        cg = CodeGenerationSkill()
        cfg = cg.generate_hccl_config("AllReduce", sel["algorithm"], topo)
        plan = cg.generate_execution_plan(sel["algorithm"], "AllReduce")
        skel = cg.generate_algorithm_skeleton(sel["algorithm"], "AllReduce")
        notes = cg.generate_optimization_notes(sel["algorithm"], topo)

        self.assertIn("algorithm", cfg)
        self.assertGreater(len(plan), 0)
        self.assertIn("class", skel)
        self.assertGreater(len(notes), 0)


if __name__ == "__main__":
    unittest.main()
