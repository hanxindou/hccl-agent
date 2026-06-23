"""Tests for PlanningSkill — task decomposition."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.planning_skill import PlanningSkill


class TestPlanningSkill(unittest.TestCase):

    def test_create_plan_returns_list(self):
        plan = PlanningSkill.create_plan(8, 128, "AllReduce")
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)

    def test_contains_at_least_6_steps(self):
        plan = PlanningSkill.create_plan(16, 256, "AllReduce")
        self.assertGreaterEqual(len(plan), 6)

    def test_step_numbers_ordered(self):
        plan = PlanningSkill.create_plan(8, 128, "AllGather")
        for i, item in enumerate(plan):
            self.assertEqual(item["step"], i + 1)

    def test_task_names_non_empty(self):
        plan = PlanningSkill.create_plan(8, 128, "ReduceScatter")
        for item in plan:
            self.assertTrue(item["task"])
            self.assertIsInstance(item["task"], str)

    def test_allreduce_has_execute_step(self):
        plan = PlanningSkill.create_plan(8, 128, "AllReduce")
        tasks = " ".join(item["task"] for item in plan)
        self.assertIn("AllReduce", tasks)

    def test_allgather_has_execute_step(self):
        plan = PlanningSkill.create_plan(8, 128, "AllGather")
        tasks = " ".join(item["task"] for item in plan)
        self.assertIn("AllGather", tasks)

    def test_reducescatter_has_execute_step(self):
        plan = PlanningSkill.create_plan(8, 128, "ReduceScatter")
        tasks = " ".join(item["task"] for item in plan)
        self.assertIn("ReduceScatter", tasks)

    def test_evaluate_and_reflect_steps_present(self):
        plan = PlanningSkill.create_plan(8, 128, "AllReduce")
        tasks = " ".join(item["task"] for item in plan)
        self.assertIn("Evaluate", tasks)
        self.assertIn("Reflect", tasks)
        self.assertIn("Record experience", tasks)


if __name__ == "__main__":
    unittest.main()
