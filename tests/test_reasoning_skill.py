"""Tests for ReasoningSkill — mock-only, no real API calls."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.reasoning_skill import ReasoningSkill


class FakeLLMClient:
    """A fake LLMClient that returns canned responses."""

    def __init__(self, response_text=None):
        self.response_text = response_text or ""
        self.calls = []

    def ask(self, prompt, system_prompt=None):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        return self.response_text


class TestReasoningSkill(unittest.TestCase):

    def test_analyze_parses_recommendation(self):
        fake = FakeLLMClient(
            "Recommendation: Ring AllReduce\n"
            "Reasoning: Ring provides balanced bandwidth and latency."
        )
        skill = ReasoningSkill(client=fake)
        result = skill.analyze(
            nodes=8, message_size=128, topology="Full Mesh",
            candidate_algorithms=["Ring AllReduce", "Butterfly", "Mesh"],
        )
        self.assertEqual(result["recommendation"], "Ring AllReduce")
        self.assertIn("balanced", result["reasoning"])

    def test_analyze_prompt_includes_nodes(self):
        fake = FakeLLMClient("Recommendation: Mesh\nReasoning: good.")
        skill = ReasoningSkill(client=fake)
        skill.analyze(
            nodes=16, message_size=500, topology="Ring",
            candidate_algorithms=["Mesh", "Ring AllReduce"],
        )
        prompt = fake.calls[0]["prompt"]
        self.assertIn("16", prompt)
        self.assertIn("500", prompt)
        self.assertIn("Ring", prompt)

    def test_analyze_prompt_includes_candidates(self):
        fake = FakeLLMClient("Recommendation: Mesh\nReasoning: ok.")
        skill = ReasoningSkill(client=fake)
        skill.analyze(
            nodes=8, message_size=128, topology="Full Mesh",
            candidate_algorithms=["Mesh", "NHR"],
        )
        prompt = fake.calls[0]["prompt"]
        self.assertIn("- Mesh", prompt)
        self.assertIn("- NHR", prompt)

    def test_analyze_empty_response(self):
        fake = FakeLLMClient("")
        skill = ReasoningSkill(client=fake)
        result = skill.analyze(
            nodes=4, message_size=1, topology="Full Mesh",
            candidate_algorithms=["Butterfly"],
        )
        self.assertEqual(result["recommendation"], "")
        self.assertEqual(result["reasoning"], "")

    def test_analyze_unformatted_response(self):
        """LLM returns free-form text without labeled sections."""
        fake = FakeLLMClient(
            "I think Ring AllReduce is best because it scales well."
        )
        skill = ReasoningSkill(client=fake)
        result = skill.analyze(
            nodes=8, message_size=128, topology="Full Mesh",
            candidate_algorithms=["Ring AllReduce", "Mesh"],
        )
        # Fallback: whole response becomes reasoning.
        self.assertTrue(len(result["reasoning"]) > 0)

    def test_analyze_exception_from_client(self):
        class FailingClient:
            def ask(self, prompt, system_prompt=None):
                raise RuntimeError("API down")
        skill = ReasoningSkill(client=FailingClient())
        with self.assertRaises(RuntimeError):
            skill.analyze(
                nodes=8, message_size=128, topology="Full Mesh",
                candidate_algorithms=["Ring AllReduce"],
            )


if __name__ == "__main__":
    unittest.main()
