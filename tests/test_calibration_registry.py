"""Tests for CalibrationRegistry."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from calibration.calibration_registry import get_registry, CalibrationRegistry


class TestCalibrationRegistry(unittest.TestCase):

    def test_list_profiles(self):
        reg = CalibrationRegistry()
        profiles = reg.list_profiles()
        self.assertGreaterEqual(len(profiles), 1)

    def test_current_profile(self):
        reg = CalibrationRegistry()
        cp = reg.current_profile()
        self.assertIsNotNone(cp)

    def test_default_is_competition_v1(self):
        reg = CalibrationRegistry()
        self.assertIn("competition_v1", reg.list_profiles())


if __name__ == "__main__":
    unittest.main()
