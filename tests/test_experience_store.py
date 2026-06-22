"""Tests for ExperienceStore — save, load, query, aggregate."""
import os, sys, unittest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.experience_store import ExperienceStore


class TestExperienceStore(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.tmp.close()
        self.store = ExperienceStore(path=self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_save_and_load(self):
        self.store.save({"nodes": 8, "algorithm": "Mesh", "score": 92.1,
                         "topology": "Full Mesh", "primitive": "AllReduce",
                         "message_size": 128, "execution_time_ms": 0.25})
        records = self.store.load_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["algorithm"], "Mesh")

    def test_load_empty(self):
        self.assertEqual(len(self.store.load_all()), 0)

    def test_query_similar_match(self):
        self.store.save({"nodes": 8, "topology": "Full Mesh", "primitive": "AllReduce",
                         "algorithm": "Mesh", "score": 90, "execution_time_ms": 0.2})
        self.store.save({"nodes": 8, "topology": "Ring", "primitive": "AllReduce",
                         "algorithm": "Ring AllReduce", "score": 80, "execution_time_ms": 0.3})
        results = self.store.query_similar(nodes=8, topology="Full Mesh",
                                           primitive="AllReduce")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["algorithm"], "Mesh")

    def test_query_similar_no_match_topology(self):
        self.store.save({"nodes": 8, "topology": "Full Mesh", "primitive": "AllReduce",
                         "algorithm": "Mesh", "score": 90, "execution_time_ms": 0.2})
        results = self.store.query_similar(nodes=8, topology="Ring",
                                           primitive="AllReduce")
        self.assertEqual(len(results), 0)

    def test_aggregate_statistics(self):
        records = [
            {"algorithm": "Mesh", "score": 90, "execution_time_ms": 0.2},
            {"algorithm": "Mesh", "score": 92, "execution_time_ms": 0.3},
            {"algorithm": "Ring AllReduce", "score": 80, "execution_time_ms": 0.5},
        ]
        stats = self.store.aggregate_statistics(records)
        self.assertIn("Mesh", stats)
        self.assertEqual(stats["Mesh"]["count"], 2)
        self.assertEqual(stats["Mesh"]["avg_score"], 91.0)
        self.assertIn("Ring AllReduce", stats)
        self.assertEqual(stats["Ring AllReduce"]["count"], 1)

    def test_aggregate_empty(self):
        self.assertEqual(self.store.aggregate_statistics([]), {})

    def test_save_adds_timestamp(self):
        self.store.save({"nodes": 4})
        self.assertIn("timestamp", self.store.load_all()[0])


if __name__ == "__main__":
    unittest.main()
