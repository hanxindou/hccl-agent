"""Tests for CaseRetrievalSkill."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from knowledge.knowledge_base import KnowledgeBase
from skills.case_retrieval_skill import CaseRetrievalSkill


class TestCaseRetrieval(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.tmp.close()
        self.kb = KnowledgeBase(path=self.tmp.name)
        self.kb.add_case({"primitive": "AllReduce", "topology": "Full Mesh",
                          "nodes": 8, "algorithm": "Mesh", "score": 88})
        self.skill = CaseRetrievalSkill(self.kb)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_retrieve_returns_cases(self):
        r = self.skill.retrieve("AllReduce", "Full Mesh", 8)
        self.assertGreater(r["count"], 0)
        self.assertIsNotNone(r["best_practice"])


if __name__ == "__main__":
    unittest.main()
