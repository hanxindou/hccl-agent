"""End-to-end test: ExecutionSkill → HCCL API → Simulator."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from plugin.hccl_api import HcclCommInitClusterInfo, HcclAllReduce
from simulator.simulator import Simulator


class TestExecutionHcclFlow(unittest.TestCase):

    def test_simulate_collective_exists(self):
        sim = Simulator()
        r = sim.simulate_collective("AllReduce", "Ring AllReduce", "Ring", 8)
        self.assertIn("latency", r)
        self.assertIn("score", r)

    def test_hccl_api_calls_simulator(self):
        """HCCL API must delegate through Simulator.simulate_collective()."""
        cluster = {"nodes": 8, "topology": "Ring",
                   "bandwidth_gbps": 100, "latency_ms": 0.002}
        _, comm = HcclCommInitClusterInfo(cluster, 0)
        r = HcclAllReduce(None, None, 1, "FP32", "SUM", comm)
        self.assertEqual(r["status"], "SUCCESS")
        self.assertGreater(r["score"], 0)

    def test_primitive_propagates_to_result(self):
        cluster = {"nodes": 4, "topology": "Full Mesh",
                   "bandwidth_gbps": 100, "latency_ms": 0.002}
        _, comm = HcclCommInitClusterInfo(cluster, 0)
        r = HcclAllReduce(None, None, 1, "FP32", "SUM", comm)
        self.assertEqual(r["primitive"], "AllReduce")


if __name__ == "__main__":
    unittest.main()
