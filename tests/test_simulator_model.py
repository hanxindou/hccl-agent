"""Tests for Simulator with algorithm efficiency + contention model."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from simulator.simulator import Simulator


class TestSimulatorModel(unittest.TestCase):

    def setUp(self):
        self.sim = Simulator()

    # ---- score range ----

    def test_all_scores_in_0_to_100(self):
        """Every algorithm/topology combination must score in [0, 100]."""
        algorithms = [
            "Ring AllReduce", "Butterfly", "Mesh",
            "NHR", "Fat-Tree", "PairWise",
        ]
        topologies = ["Full Mesh", "Ring", "Fat Tree"]
        for algo in algorithms:
            for topo in topologies:
                res = self.sim.evaluate(algo, topo, 8, 128)
                self.assertGreaterEqual(res["score"], 0.0,
                    f"{algo} on {topo} score < 0")
                self.assertLessEqual(res["score"], 100.0,
                    f"{algo} on {topo} score > 100")

    # ---- algorithm efficiency: Ring > Mesh bandwidth ----

    def test_ring_has_higher_bandwidth_than_mesh(self):
        """Ring (eff=0.95) should have more bandwidth than Mesh (eff=0.80)."""
        res_ring = self.sim.evaluate("Ring AllReduce", "Ring", 8, 128)
        res_mesh = self.sim.evaluate("Mesh", "Full Mesh", 8, 128)
        self.assertGreater(
            res_ring["bandwidth"], res_mesh["bandwidth"],
        )

    # ---- contention: Mesh gets worse with more nodes ----

    def test_mesh_latency_increases_with_nodes(self):
        """Full Mesh latency should grow with node count (contention)."""
        lat_8  = self.sim.evaluate("Mesh", "Full Mesh", 8,  128)["latency"]
        lat_16 = self.sim.evaluate("Mesh", "Full Mesh", 16, 128)["latency"]
        lat_32 = self.sim.evaluate("Mesh", "Full Mesh", 32, 128)["latency"]
        self.assertLess(lat_8, lat_16)
        self.assertLess(lat_16, lat_32)

    # ---- Ring vs Mesh at scale ----

    def test_ring_beats_mesh_at_all_scales(self):
        """Ring AllReduce beats Mesh at both 4 and 32 nodes because
        Ring has higher algorithm efficiency and no link contention."""
        for N in [4, 32]:
            mesh_score = self.sim.evaluate(
                "Mesh", "Full Mesh", N, 128,
            )["score"]
            ring_score = self.sim.evaluate(
                "Ring AllReduce", "Full Mesh", N, 128,
            )["score"]
            self.assertGreater(ring_score, mesh_score,
                f"Ring {ring_score} should beat Mesh {mesh_score} at {N} nodes")

    # ---- Mesh bandwidth collapses at scale ----

    def test_mesh_bandwidth_collapses_at_scale(self):
        """Mesh bandwidth drops sharply from 4 to 32 nodes due to
        link sharing contention."""
        bw_4 = self.sim.evaluate("Mesh", "Full Mesh", 4,  128)["bandwidth"]
        bw_32 = self.sim.evaluate("Mesh", "Full Mesh", 32, 128)["bandwidth"]
        ratio = bw_32 / bw_4
        self.assertLess(ratio, 0.5,
            f"Mesh bw should drop >50% from 4→32 nodes, got {ratio:.2f}")

    # ---- 8 / 16 / 32 scaling ----

    def test_ring_scaling_8_16_32(self):
        s8  = self.sim.evaluate("Ring AllReduce", "Ring", 8,  128)["score"]
        s16 = self.sim.evaluate("Ring AllReduce", "Ring", 16, 128)["score"]
        s32 = self.sim.evaluate("Ring AllReduce", "Ring", 32, 128)["score"]
        # Ring has no contention, so latency grows linearly with steps.
        # Score should decrease but not collapse.
        self.assertGreater(s8, s16)
        self.assertGreater(s16, s32)
        self.assertGreater(s32, 0.0)

    # ---- Fat Tree contention ----

    def test_fat_tree_contention_increases_latency(self):
        lat_8  = self.sim.evaluate("Fat-Tree", "Fat Tree", 8,  128)["latency"]
        lat_64 = self.sim.evaluate("Fat-Tree", "Fat Tree", 64, 128)["latency"]
        self.assertLess(lat_8, lat_64)

    # ---- algorithm bandwidth differentiation ----

    def test_algorithms_produce_distinct_bandwidth(self):
        """Each algorithm produces a different bandwidth value."""
        results = {}
        for algo in ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"]:
            results[algo] = self.sim.evaluate(
                algo, "Ring", 8, 128,
            )["bandwidth"]

        # All bandwidths must be distinct.
        bw_values = list(results.values())
        self.assertEqual(len(bw_values), len(set(bw_values)),
            f"Bandwidth values are not distinct: {results}")

        # Mesh has the lowest bandwidth (lowest efficiency + contention).
        self.assertLess(results["Mesh"], results["Butterfly"])
        self.assertLess(results["Mesh"], results["Ring AllReduce"])

        # Ring and NHR have the highest bandwidth (high efficiency, no contention).
        self.assertGreater(results["NHR"], results["Butterfly"])
        self.assertGreater(results["Ring AllReduce"], results["Butterfly"])


if __name__ == "__main__":
    unittest.main()
