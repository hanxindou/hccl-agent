"""G2-E-2 strict primitive registry and request tests."""

import unittest
from unittest import mock

from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_registry import (
    PRIMITIVE_REGISTRY,
    build_hccl_test_argv,
    normalize_primitive,
    resolve_collective_request,
    resolve_hccl_test_path,
)
from plugin.hccl_vm_runner import HcclVmRunner, OfficialCollectiveRequest


class TestHcclVmRegistry(unittest.TestCase):

    def test_registry_is_immutable_and_has_only_three_primitives(self):
        self.assertEqual(
            tuple(PRIMITIVE_REGISTRY),
            ("AllReduce", "AllGather", "ReduceScatter"),
        )
        with self.assertRaises(TypeError):
            PRIMITIVE_REGISTRY["Other"] = object()

    def test_aliases_normalize_only_from_whitelist(self):
        cases = {
            " AllReduce ": "AllReduce",
            "all_reduce": "AllReduce",
            "all-reduce": "AllReduce",
            "ALLGATHER": "AllGather",
            "reduce_scatter": "ReduceScatter",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(
                    normalize_primitive(value).canonical_name,
                    expected,
                )
        for value in ("all.reduce", "all reduce", "AllToAll", ""):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Unsupported"):
                    normalize_primitive(value)

    def test_resolved_contracts_preserve_distinct_byte_semantics(self):
        all_reduce = resolve_collective_request(
            primitive="AllReduce",
            rank_count=2,
            dtype="int32",
            reduce_op="sum",
            elements=16,
        )
        all_gather = resolve_collective_request(
            primitive="AllGather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        )
        reduce_scatter = resolve_collective_request(
            primitive="ReduceScatter",
            rank_count=2,
            dtype="int32",
            reduce_op="sum",
            elements=8,
        )
        self.assertEqual(
            (all_reduce.input_bytes_per_rank, all_reduce.output_bytes_per_rank),
            (64, 64),
        )
        self.assertEqual(
            (all_gather.input_bytes_per_rank, all_gather.output_bytes_per_rank),
            (32, 64),
        )
        self.assertEqual(
            (
                reduce_scatter.input_bytes_per_rank,
                reduce_scatter.output_bytes_per_rank,
            ),
            (64, 32),
        )
        self.assertEqual(
            {all_reduce.hccl_test_bytes, all_gather.hccl_test_bytes,
             reduce_scatter.hccl_test_bytes},
            {64},
        )

    def test_reduce_option_contract_is_strict(self):
        with self.assertRaisesRegex(ValueError, "requires an explicit"):
            resolve_collective_request(
                primitive="AllReduce",
                rank_count=2,
                dtype="int32",
                reduce_op=None,
                elements=16,
            )
        with self.assertRaisesRegex(ValueError, "does not accept"):
            resolve_collective_request(
                primitive="AllGather",
                rank_count=2,
                dtype="int32",
                reduce_op="sum",
                elements=8,
            )
        with self.assertRaisesRegex(ValueError, "reduce_op=sum"):
            resolve_collective_request(
                primitive="ReduceScatter",
                rank_count=2,
                dtype="int32",
                reduce_op="max",
                elements=8,
            )

    def test_command_builder_uses_only_registry_executable(self):
        contract = resolve_collective_request(
            primitive="all-gather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        )
        argv = build_hccl_test_argv(contract, "/opt/cann/tools/hccl_test/bin")
        self.assertIn("/opt/cann/tools/hccl_test/bin/all_gather_test", argv)
        self.assertNotIn("-o", argv)
        self.assertEqual(
            resolve_hccl_test_path("/opt/cann/tools/hccl_test/bin/../bin", contract),
            "/opt/cann/tools/hccl_test/bin/all_gather_test",
        )
        with self.assertRaises(TypeError):
            OfficialCollectiveRequest(executable="/tmp/anything")

    def test_non_allreduce_verify_is_rejected_before_environment_probe(self):
        request = OfficialCollectiveRequest(
            primitive="AllGather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        )
        runner = HcclVmRunner(HcclVmConfig(backend="ASCEND_HCCL_VM"))
        with mock.patch("plugin.hccl_vm_runner.HcclVmEnvironment") as env:
            with self.assertRaisesRegex(ValueError, "dry-run only"):
                runner.verify(request)
        env.assert_not_called()

    def test_dry_run_uses_resolved_allgather_contract(self):
        request = OfficialCollectiveRequest(
            primitive="AllGather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        )
        plan = HcclVmRunner(
            HcclVmConfig(backend="ASCEND_HCCL_VM")
        ).dry_run(request)
        self.assertIn("all_gather_test -b 64 -e 64", plan[
            "interactive_commands"
        ][1])
        self.assertNotIn(" -o ", plan["interactive_commands"][1])
        self.assertIn(
            "CheckerV3 stage SemanticCheck=success",
            plan["success_requirements"],
        )
        self.assertNotIn(
            "reduceType=SUM",
            plan["success_requirements"],
        )
        self.assertEqual(
            plan["evidence_directory_pattern"].split("/")[-1],
            "g2_e_allgather_<timestamp>",
        )


if __name__ == "__main__":
    unittest.main()
