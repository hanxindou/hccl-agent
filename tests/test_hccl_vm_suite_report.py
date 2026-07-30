"""G2-E-6 suite CLI and evidence-summary tests."""

import hashlib
import io
import json
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

from main import _g2_e_suite_requests, parse_args
from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_evidence import (
    EvidenceArchive,
    archive_g2_e_suite_evidence,
)


class TestHcclVmSuiteReport(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.config = HcclVmConfig(
            backend="ASCEND_HCCL_VM",
            evidence_root=self.temp_dir.name,
        )

    def _entry(self, request, *, passed=True):
        primitive_dir = Path(self.temp_dir.name) / request.resolve().canonical_primitive
        primitive_dir.mkdir()
        archive = EvidenceArchive(
            directory=primitive_dir,
            checksums={},
            checksum_file_sha256=(
                "a" * 64 if passed else "b" * 64
            ),
        )
        return {
            "request": request,
            "archive": archive,
            "result": {
                "passed": passed,
                "status": "PASS_WITH_WARNING" if passed else "FAIL",
                "checker_success_count": 2 if passed else 0,
                "warning_103_count": 4,
                "warning_regression": False,
            },
        }

    def test_suite_cli_is_mutually_exclusive_with_primitive(self):
        args = parse_args(["verify-official", "--suite", "g2-e"])
        self.assertEqual(args.suite, "g2-e")
        self.assertIsNone(args.primitive)
        with self.assertRaises(SystemExit):
            with mock.patch("sys.stderr", new=io.StringIO()):
                parse_args([
                    "verify-official", "--suite", "g2-e",
                    "--primitive", "AllReduce",
                ])

    def test_suite_archive_references_all_primitives_and_hashes(self):
        entries = [self._entry(request) for request in _g2_e_suite_requests()]
        archive = archive_g2_e_suite_evidence(
            entries,
            self.config,
            command="python main.py verify-official --suite g2-e",
            generated_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
        )
        self.assertTrue(archive.summary["passed"])
        self.assertEqual(archive.summary["status"], "COMPLETED")
        self.assertTrue(archive.summary["environment_consistent"])
        self.assertEqual(
            [entry["primitive"] for entry in archive.summary["primitive_results"]],
            ["AllReduce", "AllGather", "ReduceScatter"],
        )
        self.assertEqual(
            {path.name for path in archive.directory.iterdir()},
            {"README.md", "summary.json", "manifest.json", "SHA256SUMS"},
        )
        summary = json.loads((archive.directory / "summary.json").read_text())
        self.assertFalse(summary["direct_hccl_api_call"])
        self.assertFalse(summary["real_ascend_npu_validated"])
        for line in (archive.directory / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            self.assertEqual(
                hashlib.sha256((archive.directory / name).read_bytes()).hexdigest(),
                digest,
            )

    def test_suite_is_not_completed_when_any_primitive_fails(self):
        entries = [
            self._entry(request, passed=request.primitive != "AllGather")
            for request in _g2_e_suite_requests()
        ]
        archive = archive_g2_e_suite_evidence(
            entries,
            self.config,
            command="python main.py verify-official --suite g2-e",
        )
        self.assertFalse(archive.summary["passed"])
        self.assertEqual(archive.summary["status"], "INCOMPLETE")

    def test_environment_mismatch_is_blocked(self):
        entries = [self._entry(request) for request in _g2_e_suite_requests()]
        entries[1]["outcome"] = type("Outcome", (), {
            "diagnosis": {"hcomm": {"commit": "different"}},
        })()
        archive = archive_g2_e_suite_evidence(
            entries,
            self.config,
            command="python main.py verify-official --suite g2-e",
        )
        self.assertFalse(archive.summary["passed"])
        self.assertEqual(
            archive.summary["status"],
            "ENV_BLOCKED_ENVIRONMENT_MISMATCH",
        )


if __name__ == "__main__":
    unittest.main()
