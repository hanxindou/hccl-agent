import json
import zipfile
from pathlib import Path

import pytest

from tools.release_audit.finalize import FINAL_EVIDENCE_FILES, _inspect_infos, old_authority_immutability, verify_final_evidence


def _final_evidence_root() -> Path:
    roots = sorted(Path("experiments/submission/evidence").glob("g3_g_*"))
    assert len(roots) == 1
    return roots[0]


def test_final_evidence_exact_coverage_and_sentinel():
    root = _final_evidence_root()
    assert {path.name for path in root.iterdir() if path.is_file()} == FINAL_EVIDENCE_FILES
    result = verify_final_evidence(root)
    assert result["status"] == "PASS"
    assert result["sentinel"] == "G3_G_SOFTWARE_RELEASE_READY"


def test_dual_status_and_hardware_boundary_are_preserved():
    result = json.loads((_final_evidence_root() / "result.json").read_text(encoding="utf-8"))
    assert result["software_release_readiness"] == "COMPLETED"
    assert result["final_competition_submission_authorization"] == "USER_ACTION_REQUIRED"
    assert result["real_device_acceptance"] == "HARDWARE_BLOCKED"
    assert result["real_device_api_executed"] is False
    assert result["runtime_api_calls"] == []
    assert result["git_tag_created"] is result["github_release_created"] is result["competition_submission_performed"] is False
    gate = json.loads(Path("docs/submission/release/user_action_release_gate.json").read_text(encoding="utf-8"))
    assert gate["software_release_readiness"] == "COMPLETED"
    assert gate["final_competition_submission_authorization"] == "USER_ACTION_REQUIRED"


def test_old_authority_remains_immutable():
    result = old_authority_immutability()
    assert result["status"] == "PASS"
    assert result["old_authority_modified"] is False


def test_archive_metadata_rejects_traversal():
    info = zipfile.ZipInfo("../escape.txt")
    info.create_system = 3
    info.external_attr = (0o100644 << 16)
    assert any("unsafe path" in error for error in _inspect_infos([info]))
