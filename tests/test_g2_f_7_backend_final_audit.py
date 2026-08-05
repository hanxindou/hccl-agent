"""G2-F-7 backend registry, isolation, evidence, and status contracts."""

import ast
import sys
import unittest
from pathlib import Path

from agent.backend_control import BackendControlPlane
from agent.final_audit import build_final_audit, verify_sha256sums
from agent.hccl_agent import HCCLAgent
from agent.report_generator import ReportGenerator
from main import _config_from_args, parse_args
from plugin.backend_registry import DEFAULT_BACKEND, EXECUTION_BACKENDS, registry_payload
from plugin.hccl_vm_backend import Backend, normalize_backend


ROOT = Path(__file__).resolve().parents[1]


class TestG2F7BackendFinalAudit(unittest.TestCase):
    def setUp(self):
        self.control = BackendControlPlane()

    def test_registry_has_three_execution_backends_and_one_track(self):
        registry = registry_payload()
        self.assertEqual(DEFAULT_BACKEND, "CPU_SIM")
        self.assertEqual([item["name"] for item in registry["execution_backends"]], list(EXECUTION_BACKENDS))
        self.assertEqual(registry["fallback_policy"], "NONE")
        self.assertEqual(registry["validation_tracks"][0]["name"], "SIMULATOR_ACCEPTANCE")
        self.assertEqual(normalize_backend("ASCEND_HCCL_DIRECT"), Backend.ASCEND_HCCL_DIRECT.value)

    def test_default_cpu_selection_has_no_silent_import_or_fallback(self):
        sys.modules.pop("plugin.direct_api_backend", None)
        sys.modules.pop("plugin.hccl_vm_runner", None)
        selected = self.control.select()
        self.assertEqual(selected["selected_backend"], "CPU_SIM")
        self.assertEqual(selected["fallback_policy"], "NONE")
        self.assertNotIn("plugin.direct_api_backend", sys.modules)
        self.assertNotIn("plugin.hccl_vm_runner", sys.modules)

    def test_explicit_vm_and_direct_remain_isolated(self):
        sys.modules.pop("plugin.direct_api_backend", None)
        sys.modules.pop("plugin.hccl_vm_runner", None)
        vm = self.control.select("ASCEND_HCCL_VM")
        self.assertEqual(vm["execution_mode"], "subprocess_hccl_test")
        self.assertNotIn("plugin.direct_api_backend", sys.modules)
        direct = self.control.select("ASCEND_HCCL_DIRECT", request_kind="execute")
        self.assertEqual(direct["status"], "NO_DEVICE_EXPECTED")
        self.assertEqual(direct["runtime_api_calls"], [])
        self.assertFalse(direct["direct_hccl_api_call"])
        self.assertNotIn("plugin.hccl_vm_runner", sys.modules)

    def test_unknown_backend_and_simulator_track_are_explicit(self):
        with self.assertRaisesRegex(ValueError, "Unknown backend"):
            self.control.select("unknown")
        track = self.control.simulator_acceptance()
        self.assertEqual(track["validation_track"], "SIMULATOR_ACCEPTANCE")
        self.assertEqual(track["performance_claim_type"], "SIMULATED_ONLY")
        self.assertFalse(track["direct_hccl_api_call"])

    def test_cli_and_agent_expose_explicit_direct_readiness(self):
        args = parse_args([
            "--backend", "ASCEND_HCCL_DIRECT", "--nodes", "2",
            "--message-size", "1",
        ])
        self.assertEqual(_config_from_args(args).backend, "ASCEND_HCCL_DIRECT")
        agent = HCCLAgent()
        self.assertEqual(agent.list_backends()["default_backend"], "CPU_SIM")
        direct = agent.select_backend("ASCEND_HCCL_DIRECT", request_kind="execute")
        self.assertEqual(direct["status"], "NO_DEVICE_EXPECTED")

    def test_main_has_no_eager_hccl_vm_runner_or_direct_import(self):
        tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
        imported = set()
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
        self.assertNotIn("plugin.hccl_vm_runner", imported)
        self.assertNotIn("plugin.direct_api_backend", imported)

    def test_existing_evidence_inventory_and_status_aggregation(self):
        audit = build_final_audit(ROOT)
        self.assertEqual(len(audit["evidence_inventory"]), 7)
        self.assertTrue(all(item["verified"] for item in audit["evidence_inventory"]))
        self.assertEqual(audit["status_aggregation"]["g2_f_readiness"], "COMPLETED")
        self.assertEqual(audit["status_aggregation"]["competition_simulator_track"], "COMPLETED")
        self.assertEqual(audit["status_aggregation"]["g2_f_real_device_acceptance"], "HARDWARE_BLOCKED")
        self.assertEqual(audit["status_aggregation"]["g2_f_overall"], "PARTIAL")

    def test_report_has_separate_backend_and_track_sections(self):
        audit = build_final_audit(ROOT)
        report = ReportGenerator.generate_backend_isolation_report(audit)
        for heading in ("CPU_SIM Summary", "ASCEND_HCCL_VM Summary", "ASCEND_HCCL_DIRECT Readiness Summary", "SIMULATOR_ACCEPTANCE Summary", "Final Status Summary", "Known Limitations", "Real-device Resume Conditions"):
            self.assertIn(heading, report)
        self.assertNotIn("REAL_DEVICE_PASS", report)

    def test_sha256_verifier_rejects_invalid_manifest(self):
        evidence = ROOT / "experiments/simulator/evidence/g2_f_6_simulator_20260804T020000Z"
        verification = verify_sha256sums(evidence)
        self.assertTrue(verification["verified"])
        self.assertGreater(verification["entry_count"], 10)


if __name__ == "__main__":
    unittest.main()
