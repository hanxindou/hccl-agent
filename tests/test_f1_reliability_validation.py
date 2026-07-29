"""Tests for the F1 deterministic reliability validation flow."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from simulator.fault_injector import FaultInjector
from simulator.reliability_validation import ReliabilityValidationFlow
from topology.graph_builder import TopologyGraphBuilder


class TestF1ReliabilityValidation(unittest.TestCase):

    def test_fixed_seed_reproduces_fault_sequence(self):
        first = ReliabilityValidationFlow(seed=1234).run()
        second = ReliabilityValidationFlow(seed=1234).run()

        self.assertEqual(first["event_sequence"], second["event_sequence"])
        self.assertEqual(first["crc32"], second["crc32"])
        self.assertEqual(first["retry_count"], second["retry_count"])
        self.assertEqual(
            first["model_failover_time_ms"],
            second["model_failover_time_ms"],
        )

    def test_crc32_detects_simulated_payload_corruption(self):
        payload = b"reference payload"
        corrupted = b"reference payloae"

        self.assertNotEqual(
            FaultInjector.compute_crc32(payload),
            FaultInjector.compute_crc32(corrupted),
        )
        self.assertTrue(FaultInjector.detect_corruption(payload, corrupted))

    def test_fault_injector_updates_communication_graph_edges(self):
        graph, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        injector = FaultInjector(seed=7)

        event = injector.inject_link_failure(graph, 0, 1)
        result = injector.simulate_transmission(graph, 0, 1, num_packets=8)

        self.assertEqual(event.model_time_ms, 0)
        self.assertFalse(result["success"])
        self.assertEqual(result["packets_lost"], 8)
        self.assertEqual(injector.get_reliability_report()["dropped_packets"], 8)

    def test_retry_and_failover_statistics_are_reported(self):
        result = ReliabilityValidationFlow(seed=20260729, max_retry=3).run()

        self.assertEqual(result["injection_count"], 4)
        self.assertGreaterEqual(result["detection_count"], 4)
        self.assertGreaterEqual(result["retry_count"], 2)
        self.assertEqual(result["recovered_count"], 1)
        self.assertTrue(result["failover"]["found"])
        self.assertGreater(result["model_failover_time_ms"], 0.0)
        self.assertEqual(result["model_status"], "CPU_SIMULATED / RELIABILITY_MODEL")
        self.assertIn("wall-clock", result["wall_clock_note"])

    def test_markdown_report_is_generated(self):
        flow = ReliabilityValidationFlow(seed=42)
        result = flow.run()

        with tempfile.TemporaryDirectory() as temp_dir:
            path = flow.write_markdown_report(
                os.path.join(temp_dir, "reliability_report.md"),
                result,
            )
            text = path.read_text(encoding="utf-8")

        self.assertIn("Reliability Simulation Report", text)
        self.assertIn("CPU_SIMULATED / RELIABILITY_MODEL", text)
        self.assertIn("link_down", text)
        self.assertIn("Corruption detected: `True`", text)
        self.assertIn("not a hardware failover SLA", text)


if __name__ == "__main__":
    unittest.main()
