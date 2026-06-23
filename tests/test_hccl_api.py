"""Tests for HCCL Compatibility Layer — HcclComm + primitives."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from plugin.hccl_api import (
    HCCL_SUCCESS, HcclComm, HcclCommInitClusterInfo,
    HcclAllReduce, HcclAllGather, HcclReduceScatter,
)


_SAMPLE_CLUSTER = {
    "nodes": 8, "topology": "Full Mesh",
    "bandwidth_gbps": 100, "latency_ms": 0.002,
}


class TestHcclApi(unittest.TestCase):

    def test_comm_init(self):
        rc, comm = HcclCommInitClusterInfo(_SAMPLE_CLUSTER, rank=0)
        self.assertEqual(rc, HCCL_SUCCESS)
        self.assertEqual(comm.rank, 0)
        self.assertEqual(comm.rank_size, 8)
        self.assertEqual(comm.topology, "Full Mesh")

    def test_allreduce(self):
        _, comm = HcclCommInitClusterInfo(_SAMPLE_CLUSTER, 0)
        r = HcclAllReduce(None, None, 1, "FP32", "SUM", comm)
        self.assertEqual(r["status"], "SUCCESS")
        self.assertEqual(r["primitive"], "AllReduce")
        self.assertIn("latency", r)
        self.assertIn("bandwidth", r)
        self.assertIn("score", r)

    def test_allgather(self):
        _, comm = HcclCommInitClusterInfo(_SAMPLE_CLUSTER, 0)
        r = HcclAllGather(None, None, 1, "FP32", comm)
        self.assertEqual(r["status"], "SUCCESS")
        self.assertEqual(r["primitive"], "AllGather")

    def test_reducescatter(self):
        _, comm = HcclCommInitClusterInfo(_SAMPLE_CLUSTER, 0)
        r = HcclReduceScatter(None, None, 1, "FP32", "SUM", comm)
        self.assertEqual(r["status"], "SUCCESS")
        self.assertEqual(r["primitive"], "ReduceScatter")

    def test_allreduce_different_algorithm(self):
        _, comm = HcclCommInitClusterInfo(_SAMPLE_CLUSTER, 0)
        r = HcclAllReduce(None, None, 1, "FP32", "SUM", comm, algorithm="Butterfly")
        self.assertIn("latency", r)

    def test_score_in_range(self):
        _, comm = HcclCommInitClusterInfo(_SAMPLE_CLUSTER, 0)
        for prim_func in [
            lambda c: HcclAllReduce(None, None, 1, "FP32", "SUM", c),
            lambda c: HcclAllGather(None, None, 1, "FP32", c),
            lambda c: HcclReduceScatter(None, None, 1, "FP32", "SUM", c),
        ]:
            r = prim_func(comm)
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)


if __name__ == "__main__":
    unittest.main()
