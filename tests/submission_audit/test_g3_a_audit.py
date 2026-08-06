"""Focused G3-A schema, truthfulness, path, and output contracts."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from tools.submission_audit.g3_a_audit import (
    EVIDENCE_LEVELS,
    OWNERS,
    RISKS,
    ROOT,
    SOURCE_DOC,
    STATUSES,
    _all_reference_paths,
    _audit_summary,
    _counts,
    build_audit_data,
    validate_audit_data,
    verify_old_evidence,
    verify_sha256sums,
    write_docs,
)


class TestG3ACompetitionDeliveryAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_audit_data()

    def test_01_requirement_schema(self):
        validate_audit_data(self.data)
        required = {
            "requirement_id", "source_document", "source_section", "source_page",
            "requirement_summary", "requirement_level", "deliverable_category",
            "acceptance_expectation", "hardware_dependency", "confidentiality",
            "status", "evidence_level", "confidence", "gap_summary", "risk_level",
            "owner_checkpoint", "user_action_required", "hardware_blocked",
        }
        self.assertTrue(all(required <= item.keys() for item in self.data["requirements"]))

    def test_02_requirement_id_uniqueness(self):
        ids = [item["requirement_id"] for item in self.data["requirements"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_03_requirement_source_presence(self):
        self.assertTrue((ROOT / SOURCE_DOC).is_file())
        self.assertTrue(all(item["source_document"] == SOURCE_DOC for item in self.data["requirements"]))
        self.assertTrue(all(item["source_section"] and item["source_page"] for item in self.data["requirements"]))

    def test_04_artifact_path_validation(self):
        for item in self.data["deliverables"]:
            if item["current_path"]:
                self.assertTrue((ROOT / item["current_path"]).exists(), item["artifact_id"])

    def test_05_no_fabricated_requirement_path(self):
        for path in _all_reference_paths(self.data["requirements"]):
            self.assertTrue((ROOT / path).exists(), path)

    def test_06_evidence_path_existence(self):
        paths = [path for item in self.data["requirements"] for path in item["evidence_paths"]]
        self.assertGreater(len(paths), 20)
        self.assertTrue(all((ROOT / path).exists() for path in paths))

    def test_07_old_evidence_sha256_references(self):
        verified = verify_old_evidence()
        self.assertEqual(len(verified), 8)
        self.assertTrue(all(item["verified"] and item["entry_count"] > 0 for item in verified))

    def test_08_status_enum(self):
        self.assertTrue(all(item["status"] in STATUSES for item in self.data["requirements"]))

    def test_09_evidence_level_enum(self):
        levels = {item["evidence_level"] for item in self.data["requirements"]}
        self.assertTrue(levels <= EVIDENCE_LEVELS)
        self.assertNotIn("E6_REAL_DEVICE_MEASURED", levels)

    def test_10_risk_enum(self):
        self.assertTrue(all(item["risk_level"] in RISKS for item in self.data["risks"]))

    def test_11_owner_checkpoint_enum(self):
        self.assertTrue(all(item["owner_checkpoint"] in OWNERS for item in self.data["risks"]))
        self.assertEqual(len(self.data["risks"]), len(self.data["roadmap"]))

    def test_12_markdown_json_count_consistency(self):
        counts = _counts(self.data)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_docs(self.data, output)
            self.assertIn(f"Total requirements: {counts['requirement_count']}", (output / "competition_requirement_matrix.md").read_text(encoding="utf-8"))
            self.assertIn(f"Total deliverables: {counts['deliverable_count']}", (output / "deliverable_inventory.md").read_text(encoding="utf-8"))
            self.assertIn(f"Total claims: {counts['claim_count']}", (output / "claim_boundary_matrix.md").read_text(encoding="utf-8"))
            self.assertEqual(len(json.loads((output / "requirement_matrix.json").read_text(encoding="utf-8"))["requirements"]), counts["requirement_count"])
            self.assertEqual(len(json.loads((output / "deliverable_inventory.json").read_text(encoding="utf-8"))["deliverables"]), counts["deliverable_count"])
            self.assertEqual(len(json.loads((output / "claim_boundary_matrix.json").read_text(encoding="utf-8"))["claims"]), counts["claim_count"])

    def test_13_claim_allowed_and_prohibited_wording(self):
        claims = self.data["claims"]
        topics = {item["claim"] for item in claims}
        required = {"1024 ranks", "1 GB", "72h", "100 ms failover", "retry rate", "BERT/LLaMA", "HCCS/RoCE/PCIe", "direct API", "NPU performance", "msprof", "zero CPU intervention"}
        self.assertTrue(required <= topics)
        self.assertTrue(all(item["allowed_wording"] and item["prohibited_wording"] for item in claims))

    def test_14_no_real_device_pass(self):
        payload = json.dumps(self.data, ensure_ascii=False)
        self.assertNotIn("REAL_DEVICE_PASS", payload)

    def test_15_no_false_measured_on_real_npu(self):
        truth = _audit_summary(self.data)["truthfulness"]
        self.assertIs(truth["measured_on_real_npu"], False)
        self.assertNotIn('"measured_on_real_npu": true', json.dumps(self.data))

    def test_16_no_false_direct_hccl_api_call(self):
        truth = _audit_summary(self.data)["truthfulness"]
        self.assertIs(truth["direct_hccl_api_call"], False)
        self.assertNotIn('"direct_hccl_api_call": true', json.dumps(self.data))

    def test_17_confidential_source_not_public_by_default(self):
        source = next(item for item in self.data["deliverables"] if item["artifact_id"] == "ART-INTERNAL-001")
        self.assertEqual(source["confidentiality"], "INTERNAL_REFERENCE")
        self.assertEqual(source["public_release_inclusion"], "EXCLUDE")
        self.assertIn("EXCLUDE", source["inclusion_decision"])

    def test_18_repository_relative_paths(self):
        paths = list(_all_reference_paths(self.data["requirements"]))
        paths += [item["current_path"] for item in self.data["deliverables"] if item["current_path"]]
        paths += [path for item in self.data["claims"] for path in item["evidence_paths"]]
        for path in paths:
            pure = PurePosixPath(path)
            self.assertFalse(pure.is_absolute(), path)
            self.assertNotIn("..", pure.parts, path)
            self.assertNotIn("\\", path, path)

    def test_19_utf8_parsing_and_scope_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_docs(self.data, output)
            for path in output.iterdir():
                path.read_text(encoding="utf-8")
        categories = {item["deliverable_category"] for item in self.data["requirements"]}
        self.assertTrue({"SOURCE_CODE", "NATIVE_PLUGIN", "AGENT_ENGINEERING", "PROMPT_AND_SKILLS", "SIMULATOR", "TEST_TOOL", "TECHNICAL_REPORT", "DEMO_MATERIAL", "RELEASE_METADATA"} <= categories)

    def test_20_final_evidence_sha256_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            payload = evidence / "result.json"
            payload.write_text('{"checkpoint":"G3-A"}\n', encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            sums = evidence / "SHA256SUMS"
            sums.write_text(f"{digest}  result.json\n", encoding="utf-8")
            sums_digest = hashlib.sha256(sums.read_bytes()).hexdigest()
            (evidence / "EVIDENCE_SHA256").write_text(f"{sums_digest}  SHA256SUMS\n", encoding="utf-8")
            verified = verify_sha256sums(evidence)
            self.assertEqual(verified["sha256sums_sha256"], sums_digest)


if __name__ == "__main__":
    unittest.main()
