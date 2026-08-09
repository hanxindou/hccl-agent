import unittest

from tools.visualization.finalize import old_authority_immutability, portability_and_secret_audit, visual_integrity_audit
from tools.agent_delivery.finalize import _allowed_change


class G3EFinalizationTests(unittest.TestCase):
    def test_old_authority_matches_origin_main(self):
        result = old_authority_immutability()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertFalse(result["old_authority_modified"])
        self.assertGreater(result["files_checked"], 20)

    def test_assets_are_portable_and_secret_free(self):
        portability, secrets = portability_and_secret_audit()
        self.assertEqual(portability["status"], "PASS", portability["findings"])
        self.assertEqual(portability["sentinel"], "G3_E_ASSET_PORTABILITY_OK")
        self.assertEqual(secrets["status"], "PASS", secrets["findings"])

    def test_visual_integrity(self):
        result = visual_integrity_audit()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["figure_count"], 13)
        self.assertEqual(result["misleading_encoding_findings"], [])

    def test_g3_d_freeze_guard_allows_only_g3_e_delivery_paths(self):
        self.assertTrue(_allowed_change("docs/submission/visualization/chart_registry.json"))
        self.assertTrue(_allowed_change("tools/visualization/render.py"))
        self.assertTrue(_allowed_change("experiments/submission/evidence/g3_e_example/result.json"))
        self.assertFalse(_allowed_change("algorithm/schedule_ir.py"))
        self.assertFalse(_allowed_change("hcccl/src/hccl_algorithms.c"))


if __name__ == "__main__":
    unittest.main()
