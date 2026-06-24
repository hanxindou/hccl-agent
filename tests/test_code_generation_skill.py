"""Tests for CodeGenerationSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.code_generation_skill import CodeGenerationSkill


class TestCodeGenerationSkill(unittest.TestCase):

    def setUp(self):
        self.topo = {"topology_type": "FatTree", "node_count": 32, "dominant_link": "RoCE"}

    def test_hccl_config_has_keys(self):
        cfg = CodeGenerationSkill.generate_hccl_config("AllReduce", "Ring AllReduce", self.topo)
        for k in ("algorithm", "chunk_size_mb", "pipeline_depth", "communication_pattern"):
            self.assertIn(k, cfg)

    def test_execution_plan_ring(self):
        plan = CodeGenerationSkill.generate_execution_plan("Ring AllReduce", "AllReduce")
        self.assertIn("phase1", plan)
        self.assertIn("phase2", plan)

    def test_execution_plan_butterfly(self):
        plan = CodeGenerationSkill.generate_execution_plan("Butterfly", "AllReduce")
        self.assertGreater(len(plan), 0)

    def test_algorithm_skeleton_contains_class(self):
        skel = CodeGenerationSkill.generate_algorithm_skeleton("Ring AllReduce", "AllReduce")
        self.assertIn("class", skel)

    def test_optimization_notes_non_empty(self):
        notes = CodeGenerationSkill.generate_optimization_notes("NHR", self.topo)
        self.assertGreater(len(notes), 2)

    def test_all_algorithms_generate_config(self):
        for algo in ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"]:
            cfg = CodeGenerationSkill.generate_hccl_config("AllReduce", algo, self.topo)
            self.assertIn("communication_pattern", cfg)


if __name__ == "__main__":
    unittest.main()
