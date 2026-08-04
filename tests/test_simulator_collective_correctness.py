"""G2-F-5 simulator correctness contracts independent of CPU_SIM."""

import unittest

from simulator.collective_correctness import (
    Case, bf16_boundary_audit, host_allgather, host_allreduce, host_reducescatter,
    representative_cases, run_case, simulate_allgather, simulate_allreduce, simulate_reducescatter,
    validate_rank_ids,
)


class TestSimulatorCollectiveCorrectness(unittest.TestCase):
    def test_three_primitives_match_independent_references(self):
        cases = [
            Case("AllReduce", "INT32", "SUM", 4, "RING", "1_element", 4, 1),
            Case("AllGather", "FP16", None, 4, "FULL_MESH", "1KB", 1024, 2),
            Case("ReduceScatter", "BF16", "MAX", 4, "FAT_TREE", "1KB", 1024, 3),
        ]
        for case in cases:
            result = run_case(case, exact=True)
            self.assertTrue(result["exact_match"])
            self.assertEqual(result["max_abs_error"], 0.0)

    def test_representative_matrix_covers_required_values(self):
        cases = representative_cases()
        self.assertEqual({case.dtype for case in cases}, {"FP32", "FP16", "BF16", "INT32"})
        self.assertTrue({2, 4, 8, 16, 64}.issubset({case.ranks for case in cases}))
        self.assertEqual({"SUM", "MAX", "MIN"}, {case.op for case in cases if case.op})
        self.assertEqual({"FULL_MESH", "RING", "FAT_TREE", "HETEROGENEOUS"}, {case.topology for case in cases})
        self.assertTrue(any(case.message_label == "logical_1GB" for case in cases))

    def test_rank_order_and_shape_validation(self):
        self.assertEqual(simulate_allgather([[1], [2]], "INT32", "RING"), [[1, 2], [1, 2]])
        self.assertEqual(host_allgather([[1], [2]], "INT32"), [[1, 2], [1, 2]])
        with self.assertRaises(ValueError):
            simulate_allreduce([[1], [2, 3]], "SUM", "INT32", "RING")
        with self.assertRaises(ValueError):
            host_reducescatter([[1, 2], [3]], "SUM", "INT32")

    def test_invalid_rank_ids_and_case_contracts_are_rejected(self):
        for rank_ids in ([0], [0, 0], [1, 0], [0, 2]):
            with self.assertRaises(ValueError):
                validate_rank_ids(rank_ids, 2)
        with self.assertRaises(ValueError):
            run_case(Case("AllGather", "FP32", "SUM", 2, "RING", "1KB", 1024, 1), exact=True)
        with self.assertRaises(ValueError):
            run_case(Case("AllReduce", "FP32", "SUM", 1, "RING", "1KB", 1024, 1), exact=True)
        with self.assertRaises(ValueError):
            run_case(Case("AllReduce", "FP32", "SUM", 2, "RING", "empty", 0, 1), exact=True)

    def test_capacity_overflow_is_rejected(self):
        with self.assertRaises(OverflowError):
            run_case(Case("ReduceScatter", "INT32", "SUM", 64, "RING", "overflow", 2**63, 1), exact=True)

    def test_topology_does_not_change_values(self):
        send = [[1, -2], [3, 4], [5, -6], [7, 8]]
        outputs = [simulate_allreduce(send, "SUM", "INT32", topology) for topology in ("FULL_MESH", "RING", "FAT_TREE", "HETEROGENEOUS")]
        self.assertTrue(all(output == host_allreduce(send, "SUM", "INT32") for output in outputs))
        self.assertEqual(simulate_reducescatter([[1, 2, 3, 4], [5, 6, 7, 8]], "MIN", "INT32", "RING"), host_reducescatter([[1, 2, 3, 4], [5, 6, 7, 8]], "MIN", "INT32"))

    def test_bf16_boundaries_are_recorded(self):
        self.assertTrue(bf16_boundary_audit()["pass"])


if __name__ == "__main__":
    unittest.main()
