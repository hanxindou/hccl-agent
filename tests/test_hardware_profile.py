"""Tests for HardwareProfile abstraction layer."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hardware.profile import HardwareProfile


class TestHardwareProfile(unittest.TestCase):

    def test_tier_high_has_hccs(self):
        p = HardwareProfile.tier_high()
        self.assertEqual(p.device_type, "high-tier")
        props = p.get_link_properties("HCCS")
        self.assertIn("bandwidth_gbps", props)

    def test_tiers_have_different_bandwidth(self):
        bw_high = HardwareProfile.tier_high().get_link_properties("HCCS")["bandwidth_gbps"]
        bw_low = HardwareProfile.tier_low().get_link_properties("HCCS")["bandwidth_gbps"]
        self.assertGreater(bw_high, bw_low)

    def test_json_roundtrip(self):
        p = HardwareProfile.tier_medium()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.close()
            p.to_json(f.name)
            p2 = HardwareProfile.from_json(f.name)
            self.assertEqual(p.device_type, p2.device_type)
            os.unlink(f.name)

    def test_unknown_link_returns_default(self):
        p = HardwareProfile.tier_medium()
        props = p.get_link_properties("InfiniBand")
        self.assertIn("bandwidth_gbps", props)

    def test_custom_profile(self):
        p = HardwareProfile(device_type="custom", link_types={
            "HCCS": {"bandwidth_gbps": 300, "latency_ms": 0.0005},
        })
        self.assertEqual(p.get_link_properties("HCCS")["bandwidth_gbps"], 300)

    def test_all_link_types_present(self):
        for tier in [HardwareProfile.tier_high(),
                     HardwareProfile.tier_medium(),
                     HardwareProfile.tier_low()]:
            for lt in ["HCCS", "RoCE", "PCIe"]:
                self.assertIn("bandwidth_gbps", tier.get_link_properties(lt))


if __name__ == "__main__":
    unittest.main()
