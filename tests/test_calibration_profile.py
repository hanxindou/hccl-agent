"""Tests for CalibrationProfile."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from calibration.calibration_profile import CalibrationProfile


class TestCalibrationProfile(unittest.TestCase):

    def test_default_has_efficiency(self):
        p = CalibrationProfile()
        self.assertIn("Ring AllReduce", p.algorithm_efficiency)

    def test_to_dict(self):
        d = CalibrationProfile(version="v2").to_dict()
        self.assertEqual(d["version"], "v2")

    def test_roundtrip_json(self):
        p = CalibrationProfile(description="test")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "_test_calib.json")
            p.to_json(path)
            p2 = CalibrationProfile.from_json(path)
            self.assertEqual(p2.description, "test")


if __name__ == "__main__":
    unittest.main()
