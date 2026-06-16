import unittest
from unittest.mock import patch

from agent.hccl_agent import HCCLAgent
from main import parse_args
from skills.algorithm_skill import AlgorithmSkill
from skills.config_skill import ConfigSkill
from skills.strategy_skill import StrategySkill
from skills.topology_graph import TopologyGraph
from simulator.simulator import Simulator
from simulator.fault_injector import FaultInjector


# ======================================================================
# HCCLAgent & CLI — existing tests (kept intact)
# ======================================================================

class TestHCCLAgent(unittest.TestCase):

    def test_agent_supports_three_required_primitives(self):
        agent = HCCLAgent()
        for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
            output = agent.run(
                nodes=8,
                message_size=128,
                primitive=primitive,
            )
            self.assertEqual(output["primitive"], primitive)
            self.assertIn("algorithm", output)
            self.assertIn("result", output)

    def test_agent_rejects_unsupported_primitive(self):
        agent = HCCLAgent()
        with self.assertRaises(ValueError):
            agent.run(nodes=8, message_size=128, primitive="Broadcast")


class TestMainCli(unittest.TestCase):

    def test_parse_args_accepts_reproducible_experiment_inputs(self):
        with patch(
            "sys.argv",
            ["main.py", "--nodes", "8", "--message-size", "128",
             "--primitive", "AllGather"],
        ):
            args = parse_args()
        self.assertEqual(args.nodes, 8)
        self.assertEqual(args.message_size, 128)
        self.assertEqual(args.primitive, "AllGather")


# ======================================================================
# AlgorithmSkill — message-size granularity, nodes, primitive
# ======================================================================

class TestAlgorithmSkill(unittest.TestCase):

    def setUp(self):
        self.skill = AlgorithmSkill()

    # ---- message-size buckets ----

    def test_tiny_message_selects_butterfly_pairwise(self):
        # <= 64 KB
        candidates = self.skill.choose_algorithms(8, 0.03)
        self.assertIn("Butterfly", candidates)
        self.assertIn("PairWise", candidates)
        self.assertNotIn("Ring AllReduce", candidates)

    def test_small_message_includes_ring(self):
        # 64 KB – 1 MB
        candidates = self.skill.choose_algorithms(8, 0.5)
        self.assertIn("Butterfly", candidates)
        self.assertIn("PairWise", candidates)
        self.assertIn("Ring AllReduce", candidates)

    def test_medium_message_full_mesh_prefers_ring_mesh(self):
        # 1 – 512 MB, nodes <= 8
        candidates = self.skill.choose_algorithms(8, 128)
        self.assertIn("Ring AllReduce", candidates)
        self.assertIn("Mesh", candidates)

    def test_medium_message_many_nodes_prefers_ring_nhr(self):
        # 1 – 512 MB, nodes > 8 and <= 64
        candidates = self.skill.choose_algorithms(32, 128)
        self.assertIn("Ring AllReduce", candidates)
        self.assertIn("NHR", candidates)
        self.assertNotIn("Mesh", candidates)

    def test_large_message_many_nodes_prefers_fat_tree(self):
        # 512 MB – 1 GB, nodes > 8
        candidates = self.skill.choose_algorithms(64, 800)
        self.assertIn("Fat-Tree", candidates)
        self.assertIn("Ring AllReduce", candidates)

    def test_huge_message_prefers_fat_tree(self):
        # >= 1 GB, nodes > 8
        candidates = self.skill.choose_algorithms(128, 2048)
        self.assertIn("Fat-Tree", candidates)

    # ---- primitive-aware ----

    def test_allgather_adds_butterfly(self):
        candidates = self.skill.choose_algorithms(16, 800, "AllGather")
        self.assertIn("Butterfly", candidates)

    def test_reducescatter_adds_ring(self):
        candidates = self.skill.choose_algorithms(8, 0.03, "ReduceScatter")
        self.assertIn("Ring AllReduce", candidates)

    # ---- no duplicates ----

    def test_no_duplicate_candidates(self):
        candidates = self.skill.choose_algorithms(8, 0.5, "AllGather")
        self.assertEqual(len(candidates), len(set(candidates)))


# ======================================================================
# ConfigSkill — validation, defaults, link lookup
# ======================================================================

class TestConfigSkill(unittest.TestCase):

    def test_load_real_config(self):
        skill = ConfigSkill()
        config = skill.load_cluster_info()
        self.assertIn("cluster_name", config)
        self.assertIn("links", config)
        self.assertIn("bandwidth_gbps", config)   # normalised
        self.assertIn("latency_ms", config)        # normalised

    def test_get_link_by_type_hccs(self):
        skill = ConfigSkill()
        link = skill.get_link_by_type("HCCS")
        self.assertIsNotNone(link)
        self.assertEqual(link["type"], "HCCS")

    def test_get_link_by_type_unknown_returns_none(self):
        skill = ConfigSkill()
        link = skill.get_link_by_type("InfiniBand")
        self.assertIsNone(link)

    def test_missing_config_file_raises(self):
        skill = ConfigSkill(config_path="/nonexistent/config.json")
        with self.assertRaises(FileNotFoundError):
            skill.load_cluster_info()


# ======================================================================
# StrategySkill — Butterfly dynamic pairing
# ======================================================================

class TestStrategySkill(unittest.TestCase):

    def setUp(self):
        self.skill = StrategySkill()

    def test_butterfly_8_nodes_has_three_steps(self):
        result = self.skill.generate("Butterfly", 8)
        steps = result["steps"]
        # Exactly 3 steps for 8 nodes (log2(8) = 3)
        step_labels = [s for s in steps if s.startswith("Step")]
        self.assertEqual(len(step_labels), 3)

    def test_butterfly_4_nodes_has_two_steps(self):
        result = self.skill.generate("Butterfly", 4)
        steps = result["steps"]
        step_labels = [s for s in steps if s.startswith("Step")]
        self.assertEqual(len(step_labels), 2)

    def test_butterfly_5_nodes_has_leftover(self):
        result = self.skill.generate("Butterfly", 5)
        steps = result["steps"]
        leftovers = [s for s in steps if s.startswith("Leftover")]
        self.assertEqual(len(leftovers), 1)

    def test_butterfly_1_node(self):
        result = self.skill.generate("Butterfly", 1)
        self.assertEqual(result["steps"], ["0"])

    def test_ring_generates_two_phases_for_allreduce(self):
        result = self.skill.generate("Ring AllReduce", 4, "AllReduce")
        self.assertIn("steps", result)
        self.assertEqual(result["primitive"], "AllReduce")
        # Should describe ReduceScatter + AllGather phases.
        self.assertTrue(
            any("ReduceScatter" in s for s in result["steps"])
        )
        self.assertTrue(
            any("AllGather" in s for s in result["steps"])
        )

    def test_ring_allgather_single_phase(self):
        result = self.skill.generate("Ring AllReduce", 4, "AllGather")
        self.assertIn("steps", result)
        self.assertTrue(
            any("Gather" in s for s in result["steps"])
        )

    def test_ring_reducescatter_single_phase(self):
        result = self.skill.generate("Ring AllReduce", 4, "ReduceScatter")
        self.assertIn("steps", result)
        self.assertTrue(
            any("Reduce" in s for s in result["steps"])
        )


# ======================================================================
# Simulator — primitive-aware, config-bandwidth/latency
# ======================================================================

class TestSimulator(unittest.TestCase):

    def setUp(self):
        self.sim = Simulator()

    def test_primitive_allreduce_vs_allgather(self):
        res_ar = self.sim.evaluate(
            "Ring AllReduce", "Full Mesh", 8, 128,
            primitive="AllReduce",
        )
        res_ag = self.sim.evaluate(
            "Ring AllReduce", "Full Mesh", 8, 128,
            primitive="AllGather",
        )
        # AllGather has a different (lower) latency factor.
        self.assertNotEqual(res_ar["latency"], res_ag["latency"])

    def test_config_bandwidth_affects_result(self):
        res_default = self.sim.evaluate(
            "Ring AllReduce", "Full Mesh", 8, 128,
            bandwidth_gbps=100,
        )
        res_low_bw = self.sim.evaluate(
            "Ring AllReduce", "Full Mesh", 8, 128,
            bandwidth_gbps=50,
        )
        self.assertGreater(
            res_default["bandwidth"], res_low_bw["bandwidth"],
        )

    def test_config_latency_affects_result(self):
        res_low = self.sim.evaluate(
            "Ring AllReduce", "Full Mesh", 8, 128,
            latency_ms=0.002,
        )
        res_high = self.sim.evaluate(
            "Ring AllReduce", "Full Mesh", 8, 128,
            latency_ms=0.010,
        )
        self.assertLess(res_low["latency"], res_high["latency"])

    def test_butterfly_vs_ring_small_message(self):
        # Butterfly should have lower latency for small messages.
        res_bf = self.sim.evaluate(
            "Butterfly", "Full Mesh", 8, 0.03,
        )
        res_ring = self.sim.evaluate(
            "Ring AllReduce", "Full Mesh", 8, 0.03,
        )
        self.assertLess(res_bf["latency"], res_ring["latency"])

    def test_pairwise_algorithm(self):
        res = self.sim.evaluate(
            "PairWise", "Full Mesh", 4, 0.01,
        )
        self.assertIn("latency", res)
        self.assertIn("bandwidth", res)
        self.assertIn("score", res)

    def test_fat_tree_algorithm(self):
        res = self.sim.evaluate(
            "Fat-Tree", "Fat Tree", 128, 2048,
        )
        self.assertGreater(res["score"], 0)

    def test_unknown_algorithm_fallback(self):
        res = self.sim.evaluate(
            "UnknownAlgo", "Ring", 8, 10,
        )
        self.assertIn("score", res)


# ======================================================================
# TopologyGraph — construction, path computation
# ======================================================================

class TestTopologyGraph(unittest.TestCase):

    def test_full_mesh_construction(self):
        g = TopologyGraph.full_mesh(8)
        self.assertEqual(len(g.nodes), 8)
        # Full mesh: N*(N-1) directed edges (bidirectional)
        self.assertEqual(len(g.edges), 8 * 7)

    def test_ring_construction(self):
        g = TopologyGraph.ring(4)
        self.assertEqual(len(g.nodes), 4)
        self.assertEqual(len(g.edges), 4)  # unidirectional ring

    def test_fat_tree_construction(self):
        g = TopologyGraph.fat_tree(16)
        self.assertGreater(len(g.nodes), 0)
        self.assertGreater(len(g.edges), 0)

    def test_shortest_path_latency_full_mesh(self):
        g = TopologyGraph.full_mesh(8)
        path, latency = g.shortest_path_latency(0, 7)
        self.assertEqual(len(path), 2)  # direct link
        self.assertLess(latency, float("inf"))

    def test_shortest_path_latency_ring(self):
        g = TopologyGraph.ring(8)
        path, latency = g.shortest_path_latency(0, 6)
        self.assertIsNotNone(path)
        self.assertLess(latency, float("inf"))

    def test_max_bandwidth_path(self):
        g = TopologyGraph.full_mesh(8)
        path, bw = g.max_bandwidth_path(0, 7)
        self.assertIsNotNone(path)
        self.assertGreater(bw, 0)

    def test_unhealthy_link_avoided(self):
        g = TopologyGraph.full_mesh(8)
        g.set_link_health(0, 7, False)
        path, _ = g.shortest_path_latency(0, 7)
        # Must route through an intermediate node.
        self.assertEqual(len(path), 3)  # 0 -> X -> 7

    def test_summary(self):
        g = TopologyGraph.full_mesh(8)
        s = g.summary()
        self.assertEqual(s["num_nodes"], 8)


# ======================================================================
# FaultInjector — fault injection, transmission, reliability report
# ======================================================================

class TestFaultInjector(unittest.TestCase):

    def setUp(self):
        self.graph = TopologyGraph.full_mesh(8)
        self.injector = FaultInjector(seed=42)

    def test_inject_link_failure(self):
        event = self.injector.inject_link_failure(self.graph, 0, 1)
        self.assertEqual(event.fault_type, "link_down")
        self.assertFalse(self.graph.edges[(0, 1)].healthy)

    def test_recover_link(self):
        self.injector.inject_link_failure(self.graph, 0, 1)
        self.injector.recover_link(self.graph, 0, 1)
        self.assertTrue(self.graph.edges[(0, 1)].healthy)

    def test_recover_all_links(self):
        self.injector.inject_random_link_failure(self.graph)
        self.injector.inject_random_link_failure(self.graph)
        self.injector.recover_all_links(self.graph)
        for edge in self.graph.edges.values():
            self.assertTrue(edge.healthy)

    def test_inject_timeout(self):
        event = self.injector.inject_timeout(self.graph, 0, 1)
        self.assertEqual(event.fault_type, "timeout")
        self.assertEqual(self.injector.retransmit_count, 1)

    def test_inject_corruption(self):
        event = self.injector.inject_corruption(self.graph, 0, 1)
        self.assertEqual(event.fault_type, "corruption")
        self.assertEqual(self.injector.corrupted_packets, 1)

    def test_simulate_transmission_healthy(self):
        result = self.injector.simulate_transmission(
            self.graph, 0, 1, num_packets=1000,
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["packets_sent"], 1000)

    def test_simulate_transmission_dead_link(self):
        self.injector.inject_link_failure(self.graph, 0, 1)
        result = self.injector.simulate_transmission(
            self.graph, 0, 1, num_packets=100,
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["packets_lost"], 100)

    def test_reliability_report(self):
        self.injector.simulate_transmission(
            self.graph, 0, 1, num_packets=1000,
        )
        self.injector.inject_link_failure(self.graph, 2, 3)
        report = self.injector.get_reliability_report()
        self.assertIn("total_faults", report)
        self.assertIn("retransmission_rate", report)
        self.assertIn("retransmission_ok", report)
        self.assertGreaterEqual(report["total_packets_sent"], 1000)

    def test_inject_congestion_reduces_bandwidth(self):
        key = (0, 1)
        original_bw = self.graph.edges[key].bandwidth_gbps
        self.injector.inject_congestion(self.graph, 0, 1, bandwidth_reduction=0.5)
        self.assertLess(self.graph.edges[key].bandwidth_gbps, original_bw)


if __name__ == "__main__":
    unittest.main()
