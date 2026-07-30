"""G2-E multi-primitive argv and external-execution gate tests."""

import unittest

from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_runner import HcclVmRunner, OfficialCollectiveRequest


class TestHcclVmMultiPrimitiveCommands(unittest.TestCase):

    def setUp(self):
        self.runner = HcclVmRunner(
            HcclVmConfig(backend="ASCEND_HCCL_VM")
        )

    def test_allgather_argv_uses_aggregate_output_bytes_without_reduce_op(self):
        plan = self.runner.dry_run(OfficialCollectiveRequest(
            primitive="AllGather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        ))
        argv = plan["hccl_test_argv"]
        self.assertEqual(argv[5], (
            "/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/"
            "all_gather_test"
        ))
        self.assertEqual(argv[6:12], ["-b", "64", "-e", "64", "-d", "int32"])
        self.assertNotIn("-o", argv)
        self.assertEqual(plan["registry"]["input_bytes_per_rank"], 32)
        self.assertEqual(plan["registry"]["output_bytes_per_rank"], 64)

    def test_allgather_rejects_explicit_reduce_option(self):
        with self.assertRaisesRegex(ValueError, "does not accept reduce_op"):
            self.runner.dry_run(OfficialCollectiveRequest(
                primitive="AllGather",
                rank_count=2,
                dtype="int32",
                reduce_op="sum",
                elements=8,
            ))

    def test_reducescatter_verify_remains_closed_until_its_checkpoint(self):
        with self.assertRaisesRegex(ValueError, "later G2-E checkpoint"):
            self.runner.verify(OfficialCollectiveRequest(
                primitive="ReduceScatter",
                rank_count=2,
                dtype="int32",
                reduce_op="sum",
                elements=8,
            ))


if __name__ == "__main__":
    unittest.main()
