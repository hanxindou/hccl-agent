import json
import unittest
from pathlib import Path

from tools.visualization.common import OUTPUT_ROOT, sha256_file
from tools.visualization.render import build_charts, validate_charts


class G3EChartSuiteTests(unittest.TestCase):
    def test_chart_suite_is_complete_and_valid(self):
        result = build_charts()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["sentinel"], "G3_E_CHART_SUITE_OK")
        self.assertEqual((result["asset_count"], result["main_figure_count"], result["supporting_figure_count"]), (13, 10, 3))
        self.assertFalse(result["png_generated"])
        self.assertFalse(result["benchmark_rerun"])
        self.assertEqual(result["runtime_api_calls"], [])

    def test_repeated_build_is_byte_deterministic(self):
        build_charts()
        registry = json.loads((OUTPUT_ROOT / "chart_registry.json").read_text(encoding="utf-8"))
        root = Path(__file__).parents[2]
        first = {row["figure_id"]: sha256_file(root / row["asset_path"]) for row in registry["figures"]}
        build_charts()
        second = {row["figure_id"]: sha256_file(root / row["asset_path"]) for row in registry["figures"]}
        self.assertEqual(first, second)

    def test_registry_contains_portable_relative_paths(self):
        result = validate_charts()
        self.assertEqual(result["status"], "PASS", result["errors"])
        registry_text = (OUTPUT_ROOT / "chart_registry.json").read_text(encoding="utf-8")
        self.assertNotIn("F:\\\\", registry_text)
        self.assertNotIn("C:\\\\", registry_text)
        self.assertNotIn("file://", registry_text)


if __name__ == "__main__":
    unittest.main()
