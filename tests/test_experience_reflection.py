"""Tests: experience consistency in reflection."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.reflection_skill import ReflectionSkill


class TestExperienceReflection(unittest.TestCase):

    def test_experience_consistency_present(self):
        skill = ReflectionSkill()
        candidates = [{"algorithm": "NHR", "score": 90}]
        r = skill.reflect(80, 0.3, "Ring AllReduce", candidate_scores=candidates)
        ec = r.get("experience_consistency")
        self.assertIsNotNone(ec)
        self.assertFalse(ec["matched"])

    def test_experience_consistency_matched(self):
        skill = ReflectionSkill()
        candidates = [{"algorithm": "NHR", "score": 90}]
        r = skill.reflect(90, 0.2, "NHR", candidate_scores=candidates)
        self.assertTrue(r["experience_consistency"]["matched"])


if __name__ == "__main__":
    unittest.main()
