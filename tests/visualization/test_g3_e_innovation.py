import json
import unittest

from tools.visualization.common import OUTPUT_ROOT
from tools.visualization.innovation import build_innovation_map, validate_innovation_map


class G3EInnovationMapTests(unittest.TestCase):
    def test_innovation_map_resolves_all_authorities(self):
        result = build_innovation_map()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["sentinel"], "G3_E_INNOVATION_MAPPING_OK")
        self.assertEqual(result["innovation_count"], 5)
        self.assertGreater(result["claim_reference_count"], 0)
        self.assertGreater(result["metric_reference_count"], 0)
        self.assertEqual(result["trace_reference_count"], 2)
        self.assertFalse(result["benchmark_rerun"])
        self.assertEqual(result["runtime_api_calls"], [])

    def test_every_innovation_discloses_truth_and_limitations(self):
        result = validate_innovation_map()
        self.assertEqual(result["status"], "PASS", result["errors"])
        payload = json.loads((OUTPUT_ROOT / "innovation_map.json").read_text(encoding="utf-8"))
        for row in payload["innovations"]:
            self.assertTrue(row["truth_identity"])
            self.assertTrue(row["limitations"])
            self.assertTrue(row["source_records"])
            self.assertTrue(all(record["commit"] for record in row["source_records"]))


if __name__ == "__main__":
    unittest.main()
