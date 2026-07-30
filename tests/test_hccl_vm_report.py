"""Tests for G2-D official validation reports and evidence archives."""

import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent.report_generator import ReportGenerator
from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_evidence import archive_official_evidence
from plugin.hccl_vm_runner import OfficialAllReduceRequest, OfficialRunOutcome


class TestHcclVmEvidence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.config = HcclVmConfig(
            backend="ASCEND_HCCL_VM",
            evidence_root=self.temp_dir.name,
        )
        self.request = OfficialAllReduceRequest()
        self.result = {
            "backend": "ASCEND_HCCL_VM",
            "execution_mode": "subprocess_hccl_test",
            "primitive": "AllReduce",
            "rank_count": 2,
            "dtype": "int32",
            "reduce_op": "sum",
            "elements": 16,
            "byte_count": 64,
            "test_exit_code": 0,
            "checker_exit_code": 0,
            "vm_exit_code": 0,
            "outer_exit_code": 0,
            "checker_success": True,
            "metadata_match": True,
            "warning_103_count": 1,
            "op_summaries": [{
                "op_index": 0,
                "collective_type": "AllReduce",
                "rank_count": 2,
                "data_type": "INT32",
                "element_count": 16,
                "reduce_type": "SUM",
            }],
            "vm_normal_shutdown": True,
            "failure_reasons": [],
            "passed": True,
            "status": "PASS_WITH_WARNING",
        }
        self.outcome = OfficialRunOutcome(
            diagnosis={
                "status": "OK",
                "missing_items": [],
                "hcomm": {"commit": "c8a3dc68"},
                "hccl": {"commit": "2c87cc19"},
            },
            plan={"topology": "topology.yaml", "mock_comm": "112"},
            result=self.result,
            raw_log="\n".join([
                "noise",
                "__HCCL_AGENT_TEST_EXIT_CODE=0",
                "Opsummary,opIndex=0,collectiveType=AllReduce,"
                "rankCount=2,dataType=INT32,elementCount=16,"
                "reduceType=SUM,",
                "Checker Success",
                "ErrorCode: 103 warning",
                "Shell exited. Host shutting down.",
            ]),
            duration_seconds=1.25,
            timed_out=False,
        )

    def test_archive_contains_required_files_and_valid_hashes(self):
        archive = archive_official_evidence(
            self.outcome,
            self.request,
            self.config,
            command="python3 main.py verify-official",
            generated_at=datetime(
                2026, 7, 30, 12, 0, tzinfo=timezone.utc
            ),
        )
        expected = {
            "manifest.json",
            "command.txt",
            "result.json",
            "concise.log",
            "raw.log.gz",
            "report.txt",
            "README.md",
            "SHA256SUMS",
        }
        self.assertEqual(
            {path.name for path in archive.directory.iterdir()},
            expected,
        )
        checksum_lines = (
            archive.directory / "SHA256SUMS"
        ).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(checksum_lines), len(expected) - 1)
        for line in checksum_lines:
            digest, name = line.split("  ", 1)
            payload = (archive.directory / name).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), digest)
        self.assertEqual(
            gzip.decompress(
                (archive.directory / "raw.log.gz").read_bytes()
            ).decode("utf-8"),
            self.outcome.raw_log,
        )

    def test_manifest_and_result_preserve_validation_boundaries(self):
        archive = archive_official_evidence(
            self.outcome,
            self.request,
            self.config,
            command="python3 main.py verify-official",
        )
        manifest = json.loads(
            (archive.directory / "manifest.json").read_text(encoding="utf-8")
        )
        result = json.loads(
            (archive.directory / "result.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            manifest["validation_class"],
            "OFFICIAL_HCCL_VM_SIMULATOR",
        )
        self.assertFalse(manifest["direct_hccl_api_call"])
        self.assertFalse(manifest["real_ascend_npu_validated"])
        self.assertEqual(result["status"], "PASS_WITH_WARNING")
        self.assertEqual(result["warning_103_count"], 1)
        self.assertTrue(result["checker_success"])

    def test_report_does_not_claim_direct_api_or_real_npu(self):
        report = ReportGenerator.generate_official_validation_report(
            self.outcome.to_public_dict()
        )
        self.assertIn("OFFICIAL_HCCL_VM_SIMULATOR", report)
        self.assertIn("subprocess-driven official hccl_test", report)
        self.assertIn("Direct HCCL API Call: No", report)
        self.assertIn("Real Ascend NPU Validated: No", report)
        self.assertIn("Status: PASS_WITH_WARNING", report)
        self.assertIn("ErrorCode 103 Warnings: 1", report)

    def test_failed_result_remains_failed_in_report_and_archive(self):
        failed = dict(self.result)
        failed.update({
            "status": "FAIL",
            "passed": False,
            "checker_success": False,
            "outer_exit_code": 1,
            "failure_reasons": ["Checker Success was not observed"],
        })
        outcome = OfficialRunOutcome(
            diagnosis=self.outcome.diagnosis,
            plan=self.outcome.plan,
            result=failed,
            raw_log="checker failed",
            duration_seconds=0.5,
            timed_out=False,
        )
        archive = archive_official_evidence(
            outcome,
            self.request,
            self.config,
            command="python3 main.py verify-official",
        )
        result = json.loads(
            (archive.directory / "result.json").read_text(encoding="utf-8")
        )
        report = (
            archive.directory / "report.txt"
        ).read_text(encoding="utf-8")
        self.assertFalse(result["passed"])
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("Passed: False", report)
        self.assertIn("Checker Success was not observed", report)


if __name__ == "__main__":
    unittest.main()
