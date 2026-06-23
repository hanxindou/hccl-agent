"""Tests: Planning output drives HCCL API (updated for Batch24 plan)."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.planning_skill import PlanningSkill


class TestPlanningHcclIntegration(unittest.TestCase):

    def test_plan_contains_candidate_algorithms(self):
        plan = PlanningSkill.create_plan(8, 128, "AllReduce")
        step1 = plan[0]
        self.assertIn("candidate_algorithms", step1)
        self.assertIsInstance(step1["candidate_algorithms"], list)

    def test_plan_step4_has_primitive(self):
        plan = PlanningSkill.create_plan(8, 128, "AllGather")
        step4 = plan[3]  # 0-indexed step 4
        self.assertIn("primitive", step4)
        self.assertEqual(step4["primitive"], "AllGather")

    def test_allreduce_candidates_include_ring(self):
        plan = PlanningSkill.create_plan(8, 128, "AllReduce")
        self.assertIn("Ring AllReduce", plan[0]["candidate_algorithms"])

    def test_reducescatter_candidates_includes_ring(self):
        plan = PlanningSkill.create_plan(8, 128, "ReduceScatter")
        self.assertIn("Ring AllReduce", plan[0]["candidate_algorithms"])

    def test_plan_has_eight_steps(self):
        for prim in ["AllReduce", "AllGather", "ReduceScatter"]:
            plan = PlanningSkill.create_plan(16, 256, prim)
            self.assertGreaterEqual(len(plan), 8)


if __name__ == "__main__":
    unittest.main()
