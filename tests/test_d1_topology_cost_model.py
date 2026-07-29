"""Stage D1 topology/cost-model convergence tests."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from cost_model.engine import CostModelEngine
from simulator.simulator import Simulator
from topology.graph_builder import TopologyGraphBuilder


class TestD1TopologyCostModel(unittest.TestCase):

    def test_message_size_changes_latency_and_transfer_volume(self):
        sim = Simulator()
        small = sim.evaluate("Ring AllReduce", "Fat Tree", 64, 1)
        large = sim.evaluate("Ring AllReduce", "Fat Tree", 64, 1024)

        self.assertGreater(large["latency"], small["latency"])
        self.assertGreater(large["transferred_bytes"], small["transferred_bytes"])
        self.assertGreater(large["communication_steps"], 0)
        self.assertEqual(large["model_type"], "ANALYTICAL_MODEL")

    def test_link_type_affects_result(self):
        sim = Simulator()
        hccs = sim.evaluate("Ring AllReduce", "Full Mesh", 8, 128)
        mixed = sim.evaluate("Ring AllReduce", "Mixed", 64, 128)

        self.assertIn("HCCS", hccs["link_types"])
        self.assertIn("RoCE", mixed["link_types"])
        self.assertIn("PCIe", mixed["link_types"])
        self.assertNotEqual(hccs["latency"], mixed["latency"])
        self.assertNotEqual(hccs["bandwidth"], mixed["bandwidth"])

    def test_required_rank_scales_run(self):
        sim = Simulator()
        latencies = []
        for ranks in [8, 64, 128, 256, 1024]:
            with self.subTest(ranks=ranks):
                result = sim.evaluate("Ring AllReduce", "Fat Tree", ranks, 256)
                self.assertGreater(result["latency"], 0.0)
                self.assertGreater(result["bandwidth"], 0.0)
                self.assertGreater(result["score"], 0.0)
                self.assertLessEqual(result["score"], 100.0)
                latencies.append(result["latency"])

        self.assertEqual(latencies, sorted(latencies))

    def test_parameter_sources_are_recorded(self):
        g, _ = TopologyGraphBuilder.build(64, num_gpus_per_node=8, mode="MULTI_NODE")
        result = CostModelEngine().estimate_collective(
            g, 256, "Ring AllReduce", "AllReduce",
        )
        sources = result["parameter_sources"]

        for key in [
            "startup_cost_ms",
            "bandwidth_gbps",
            "latency_ms",
            "contention_penalty",
        ]:
            self.assertIn(key, sources)
            self.assertIn("unit", sources[key])
            self.assertIn("source", sources[key])
            self.assertIn("calibrated", sources[key])

        self.assertIn("ANALYTICAL_MODEL", result["model_type"])
        self.assertGreater(result["edge_count"], 0)


if __name__ == "__main__":
    unittest.main()
