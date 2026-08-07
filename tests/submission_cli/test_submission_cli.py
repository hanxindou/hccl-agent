from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.submission_cli import core


class SubmissionCliContractTests(unittest.TestCase):
    def test_parser_exposes_required_commands(self):
        parser = core.build_parser()
        for command in ("check", "build", "quick", "full", "stage", "verify", "describe", "clean-generated"):
            with self.subTest(command=command):
                self.assertEqual(parser.parse_args([command]).command, command)

    def test_unknown_command_has_exit_code_two(self):
        with self.assertRaises(SystemExit) as caught:
            core.build_parser().parse_args(["unknown"])
        self.assertEqual(caught.exception.code, 2)

    def test_describe_is_truthful_and_read_only(self):
        before = {path: path.stat().st_mtime_ns for path in (core.ROOT / "tools/submission_cli").glob("*.py")}
        result = core.describe_command()
        after = {path: path.stat().st_mtime_ns for path in before}
        self.assertEqual(before, after)
        self.assertEqual(result["default_backend"], "CPU_SIM")
        self.assertEqual(result["fallback_policy"], "NONE")
        self.assertIn("readiness", result["direct_artifact"].lower())

    def test_native_manifest_schema_and_exact_exports(self):
        manifest = json.loads(core.NATIVE_MANIFEST.read_text(encoding="utf-8"))
        required = {"artifact_name", "artifact_role", "language", "source_paths", "public_headers", "abi_namespace", "abi_version", "exported_symbols", "required_symbols", "forbidden_symbols", "soname", "dependencies", "build_target", "build_mode", "runtime_mode", "official_abi_status", "cpu_simulated", "direct_readiness", "real_device_validated"}
        self.assertTrue(required.issubset(manifest))
        self.assertEqual(len(manifest["exported_symbols"]), 19)
        self.assertEqual(manifest["artifact_role"], "CPU_SIM_REFERENCE_PLUGIN")
        self.assertFalse(manifest["direct_readiness"])

    def test_direct_manifest_is_isolated(self):
        direct = json.loads(core.DIRECT_MANIFEST.read_text(encoding="utf-8"))
        cpu = json.loads(core.NATIVE_MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(direct["direct_readiness"])
        self.assertEqual(direct["runtime_api_calls"], [])
        self.assertFalse(direct["direct_hccl_api_call"])
        self.assertFalse(set(cpu["required_symbols"]) & set(direct["forbidden_symbols"]) == set())

    def test_all_submission_configs_validate(self):
        for path in sorted((core.ROOT / "configs/submission").glob("*.json")):
            with self.subTest(path=path.name):
                result = core._load_config(str(path), submission_schema=True)
                self.assertEqual(result["payload"]["topology_source"], "SIMULATOR_CONFIG")
                self.assertEqual(len(result["sha256"]), 64)

    def test_invalid_topology_config_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
            with self.assertRaises(core.SubmissionError):
                core._load_config(str(path), submission_schema=True)

    def test_generated_target_rejects_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(core.SubmissionError):
                core._assert_generated_target(Path(temp))

    def test_generated_target_rejects_broad_roots(self):
        for path in (core.ROOT, core.ROOT / "build", core.ROOT / "dist"):
            with self.subTest(path=path):
                with self.assertRaises(core.SubmissionError):
                    core._assert_generated_target(path)

    def test_prepare_generated_refuses_unmarked_clean(self):
        target = core.ROOT / "dist/submission-test-unmarked"
        target.mkdir(parents=True, exist_ok=True)
        (target / "user.txt").write_text("user", encoding="utf-8")
        try:
            with self.assertRaises(core.SubmissionError):
                core._prepare_generated(target, clean=True)
        finally:
            (target / "user.txt").unlink()
            target.rmdir()

    def test_clean_generated_refuses_symlink_escape_contract(self):
        with mock.patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(core.SubmissionError):
                core._assert_generated_target(core.DEFAULT_STAGE)

    def test_old_evidence_integrity_selection(self):
        result = core.verify_old_evidence(["g2_f_5", "g2_f_6", "g3_a"])
        self.assertEqual([item["status"] for item in result], ["PASS", "PASS", "PASS"])

    def test_claim_audit_rejects_forbidden_true_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "STATUS.json").write_text('{"direct_hccl_api_call": true}', encoding="utf-8")
            self.assertEqual(core._claim_boundary_audit(root)["status"], "FAIL")

    def test_forbidden_scan_rejects_controlled_docx(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "competition.docx").write_bytes(b"x")
            self.assertEqual(core._scan_stage(root)["status"], "FAIL")

    def test_forbidden_scan_accepts_truthful_plain_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("No real device API was executed.", encoding="utf-8")
            self.assertEqual(core._scan_stage(root)["status"], "PASS")

    def test_stage_requires_both_exclusion_flags(self):
        args = argparse.Namespace(output="dist/submission-test", clean_output=True, include_selected_evidence=False, exclude_controlled_docs=False, exclude_official_assets=True)
        with self.assertRaises(core.SubmissionError):
            core.stage_command(args)

    def test_full_rejects_expensive_regeneration_before_execution(self):
        args = argparse.Namespace(regenerate_expensive_simulator_evidence=True)
        with self.assertRaises(core.SubmissionError):
            core.full_command(args)

    def test_direct_build_requires_explicit_root(self):
        args = argparse.Namespace(direct_readiness=True, cann_root=None, name="unused")
        with mock.patch.object(core, "check_environment", return_value={"status": "PASS"}):
            with self.assertRaises(core.SubmissionError):
                core.build_command(args)

    def test_simulator_replay_is_deterministic(self):
        args = argparse.Namespace(cluster_config=None, topology_config="configs/submission/full_mesh_8.json", hardware_profile="tier_medium", seed=20260806, message_size=1024, rank_size=8, primitive="AllReduce", algorithm="Ring AllReduce")
        first = core._simulator_replay(args)
        second = core._simulator_replay(args)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "PASS")
        self.assertEqual(first["no_alternate_path"]["status"], "EXPECTED_NO_PATH_FAILURE")


if __name__ == "__main__":
    unittest.main()
