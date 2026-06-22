"""Tests for DecisionSkill — LLM-based algorithm selection."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.decision_skill import DecisionSkill


class FakeClient:
    def __init__(self, response=""): self.response = response
    def ask(self, prompt, system_prompt=None): return self.response


class TestDecisionSkill(unittest.TestCase):

    def setUp(self):
        self.candidates = [
            {"algorithm": "Ring AllReduce", "score": 92.1, "latency": 0.15, "bandwidth": 11.8},
            {"algorithm": "Butterfly",      "score": 88.5, "latency": 0.08, "bandwidth": 10.2},
        ]

    def test_parse_algorithm_and_reason(self):
        skill = DecisionSkill(client=FakeClient(
            "Algorithm: Ring AllReduce\nReason: Best balance of latency and bandwidth."))
        r = skill.choose_algorithm(8, 128, "Full Mesh", "AllReduce", self.candidates)
        self.assertEqual(r["algorithm"], "Ring AllReduce")
        self.assertIn("balance", r["reason"])

    def test_missing_algorithm_returns_none(self):
        skill = DecisionSkill(client=FakeClient("Just some text without label."))
        r = skill.choose_algorithm(8, 128, "Full Mesh", "AllReduce", self.candidates)
        self.assertIsNone(r)

    def test_empty_response_returns_none(self):
        skill = DecisionSkill(client=FakeClient(""))
        r = skill.choose_algorithm(8, 128, "Full Mesh", "AllReduce", self.candidates)
        self.assertIsNone(r)

    def test_api_exception_returns_none(self):
        class BadClient:
            def ask(self, *a, **kw): raise RuntimeError("API down")
        skill = DecisionSkill(client=BadClient())
        r = skill.choose_algorithm(8, 128, "Full Mesh", "AllReduce", self.candidates)
        self.assertIsNone(r)

    def test_case_insensitive_algorithm(self):
        skill = DecisionSkill(client=FakeClient("ALGORITHM: Butterfly\nreason: ok"))
        r = skill.choose_algorithm(8, 128, "Full Mesh", "AllReduce", self.candidates)
        self.assertEqual(r["algorithm"], "Butterfly")


if __name__ == "__main__":
    unittest.main()
