"""Tests for KnowledgeExtractionSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.knowledge_extraction_skill import KnowledgeExtractionSkill


class TestKnowledgeExtraction(unittest.TestCase):

    def test_generate_lesson(self):
        lesson = KnowledgeExtractionSkill.generate_lesson({
            "algorithm": "NHR", "score": 90, "nodes": 32, "topology": "Fat Tree",
        })
        self.assertIn("NHR", lesson)
        self.assertIn("excellent", lesson)

    def test_generate_lesson_below_average(self):
        lesson = KnowledgeExtractionSkill.generate_lesson({
            "algorithm": "Mesh", "score": 30, "nodes": 64, "topology": "Ring",
        })
        self.assertIn("below-average", lesson)


if __name__ == "__main__":
    unittest.main()
