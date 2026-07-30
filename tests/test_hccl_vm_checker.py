"""G2-D-4 strict Checker and process-result parser tests."""

import unittest

from plugin.hccl_vm_checker import parse_official_result
from plugin.hccl_vm_runner import OfficialAllReduceRequest


SUCCESS_LOG = """
__HCCL_AGENT_HCCL_CONFIG_EXIT_CODE=0
__HCCL_AGENT_MOCK_EXIT_CODE=0
__HCCL_AGENT_TEST_EXIT_CODE=0
[info] Op summary, opIndex=0, collectiveType=AllReduce, rankCount=2,
dataType=INT32, elementCount=16, reduceType=SUM, opGroupSize=2
[info] CheckerV3 stage finished, stage=GenGraph, status=success
[info] CheckerV3 stage finished, stage=SingleTaskCheck, status=success
[info] CheckerV3 stage finished, stage=MemConflict, status=success
[info] CheckerV3 stage finished, stage=SemanticCheck, status=success
[info] op[0] Checker Success
__HCCL_AGENT_CHECKER_EXIT_CODE=0
[info] Shell exited. Host shutting down.
__HCCL_AGENT_VM_EXIT_CODE=0
"""


class TestHcclVmChecker(unittest.TestCase):

    def setUp(self):
        self.request = OfficialAllReduceRequest()

    def parse(self, log, outer_exit_code=0):
        return parse_official_result(
            log,
            outer_exit_code=outer_exit_code,
            request=self.request,
        )

    def test_clean_success_is_pass_clean(self):
        result = self.parse(SUCCESS_LOG)
        self.assertTrue(result.passed)
        self.assertEqual(result.status, "PASS_CLEAN")
        self.assertTrue(result.metadata_match)
        self.assertEqual(result.checker_success_count, 1)
        self.assertTrue(result.vm_normal_shutdown)

    def test_warning_103_is_recorded_as_pass_with_warning(self):
        log = (
            SUCCESS_LOG
            + "\n[warning][ErrorCode: 103] Found CCU post/local-post tasks "
            "that were never consumed by any Wait task\n"
            + "[warning][ErrorCode: 103] second warning\n"
        )
        result = self.parse(log)
        self.assertTrue(result.passed)
        self.assertEqual(result.status, "PASS_WITH_WARNING")
        self.assertEqual(result.warning_103_count, 2)
        self.assertEqual(len(result.warning_summaries), 2)
        self.assertTrue(result.warning_regression)

    def test_wrapped_metadata_tokens_are_parsed(self):
        wrapped = SUCCESS_LOG.replace(
            "collectiveType",
            "collectiveTyp\ne",
        ).replace("rankCount", "rank\nCount")
        result = self.parse(wrapped)
        self.assertTrue(result.metadata_match)

    def test_missing_metadata_cannot_pass(self):
        result = self.parse(SUCCESS_LOG.replace("Op summary", "No summary"))
        self.assertFalse(result.passed)
        self.assertIn(
            "checker metadata",
            " ".join(result.failure_reasons),
        )

    def test_mismatched_metadata_cannot_pass(self):
        result = self.parse(SUCCESS_LOG.replace("rankCount=2", "rankCount=4"))
        self.assertFalse(result.metadata_match)
        self.assertFalse(result.passed)

    def test_test_exit_code_must_be_captured_and_zero(self):
        for log in (
            SUCCESS_LOG.replace(
                "__HCCL_AGENT_TEST_EXIT_CODE=0",
                "__HCCL_AGENT_TEST_EXIT_CODE=7",
            ),
            SUCCESS_LOG.replace(
                "__HCCL_AGENT_TEST_EXIT_CODE=0\n",
                "",
            ),
        ):
            with self.subTest(log=log[:50]):
                result = self.parse(log)
                self.assertFalse(result.passed)

    def test_each_fatal_signal_forces_failure(self):
        for signal in (
            "Segmentation fault",
            "MPI_ABORT",
            "undefined symbol: hcclFoo",
            "fatal failure",
            "Checker Failed",
        ):
            with self.subTest(signal=signal):
                result = self.parse(SUCCESS_LOG + "\n" + signal)
                self.assertFalse(result.passed)
                self.assertTrue(result.fatal_signals)

    def test_missing_or_failed_required_stage_cannot_pass(self):
        missing = self.parse(SUCCESS_LOG.replace(
            "[info] CheckerV3 stage finished, stage=SemanticCheck, status=success\n",
            "",
        ))
        failed = self.parse(SUCCESS_LOG.replace(
            "stage=MemConflict, status=success",
            "stage=MemConflict, status=failed",
        ))
        self.assertFalse(missing.passed)
        self.assertIn("SemanticCheck", " ".join(missing.stage_failures))
        self.assertFalse(failed.passed)
        self.assertIn("MemConflict", " ".join(failed.stage_failures))

    def test_missing_resolved_contract_cannot_pass(self):
        result = parse_official_result(SUCCESS_LOG, outer_exit_code=0)
        self.assertFalse(result.passed)
        self.assertTrue(any(
            "resolved collective contract" in reason
            for reason in result.failure_reasons
        ))

    def test_vm_shutdown_marker_and_outer_exit_must_be_zero(self):
        missing_shutdown = SUCCESS_LOG.replace(
            "Shell exited. Host shutting down.",
            "",
        )
        self.assertFalse(
            self.parse(missing_shutdown).passed
        )
        self.assertFalse(
            self.parse(SUCCESS_LOG, outer_exit_code=9).passed
        )

    def test_result_dictionary_is_structured(self):
        result = self.parse(SUCCESS_LOG).to_dict()
        self.assertEqual(result["backend"], "ASCEND_HCCL_VM")
        self.assertEqual(
            result["execution_mode"],
            "subprocess_hccl_test",
        )
        self.assertEqual(result["byte_count"], 64)
        self.assertEqual(result["op_summaries"][0]["rank_count"], 2)


if __name__ == "__main__":
    unittest.main()
