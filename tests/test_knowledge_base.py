"""Tests for KnowledgeBase."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from knowledge.knowledge_base import KnowledgeBase


class TestKnowledgeBase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.tmp.close()
        self.kb = KnowledgeBase(path=self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_add_and_load(self):
        self.kb.add_case({"primitive": "AllReduce", "topology": "Ring", "nodes": 8,
                          "algorithm": "Ring AllReduce", "score": 85})
        cases = self.kb.load_all()
        self.assertEqual(len(cases), 1)

    def test_get_best_practice(self):
        self.kb.add_case({"primitive": "AllReduce", "topology": "Ring", "nodes": 8,
                          "algorithm": "Mesh", "score": 70})
        self.kb.add_case({"primitive": "AllReduce", "topology": "Ring", "nodes": 8,
                          "algorithm": "NHR", "score": 90})
        bp = self.kb.get_best_practice("AllReduce", "Ring")
        self.assertEqual(bp["algorithm"], "NHR")

    def test_retrieve_cases(self):
        self.kb.add_case({"primitive": "AllReduce", "topology": "Ring", "nodes": 8,
                          "algorithm": "Ring AllReduce", "score": 80})
        cases = self.kb.retrieve_cases("AllReduce", "Ring", 10)
        self.assertGreater(len(cases), 0)

    def test_export_summary_empty(self):
        s = self.kb.export_summary()
        self.assertEqual(s["total_cases"], 0)


if __name__ == "__main__":
    unittest.main()
