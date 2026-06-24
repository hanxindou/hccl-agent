"""Tests for CalibrationProfile."""
import os, sys, unittest
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
        p.to_json("/tmp/_test_calib.json")
        p2 = CalibrationProfile.from_json("/tmp/_test_calib.json")
        self.assertEqual(p2.description, "test")
        os.unlink("/tmp/_test_calib.json")


if __name__ == "__main__":
    unittest.main()
