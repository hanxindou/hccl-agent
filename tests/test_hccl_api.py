"""Tests for HCCL Compatibility Layer — HcclComm + primitives."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from plugin.hccl_api import (
    HCCL_SUCCESS, HcclComm, HcclCommInitClusterInfo,
    HcclAllReduce, HcclAllGather, HcclReduceScatter,
    HcclAllGatherReference, HcclAllGatherCpuData,
    HcclReduceScatterReference, HcclReduceScatterCpuData,
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

    def test_allgather_reference_layout(self):
        send_data = [[0.0, 1.0], [10.0, 11.0], [20.0, 21.0], [30.0, 31.0]]
        expected = [[0.0, 1.0, 10.0, 11.0, 20.0, 21.0, 30.0, 31.0]] * 4
        self.assertEqual(HcclAllGatherReference(send_data), expected)

    def test_allgather_cpu_data_uses_explicit_data_entry(self):
        send_data = [[float(rank * 10 + elem) for elem in range(2)]
                     for rank in range(4)]
        result = HcclAllGatherCpuData(send_data, algorithm="Wrapper")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], HcclAllGatherReference(send_data))

    def test_reducescatter_reference_layout(self):
        send_data = [
            [[1.0, 2.0], [10.0, 20.0]],
            [[3.0, 4.0], [30.0, 40.0]],
        ]
        self.assertEqual(
            HcclReduceScatterReference(send_data),
            [[4.0, 6.0], [40.0, 60.0]],
        )

    def test_reducescatter_cpu_data_uses_explicit_data_entry(self):
        send_data = [
            [
                [float(src * 1000 + dst * 100 + elem + 1)
                 for elem in range(2)]
                for dst in range(4)
            ]
            for src in range(4)
        ]
        result = HcclReduceScatterCpuData(send_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], HcclReduceScatterReference(send_data))


if __name__ == "__main__":
    unittest.main()
