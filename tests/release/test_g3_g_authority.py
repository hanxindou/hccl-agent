from __future__ import annotations

import json
from pathlib import Path

from tools.release_audit.authority import AUTHORITY_ROOTS, USER_ACTION_SUBJECTS, validate_authority
from tools.release_audit.common import RELEASE_ROOT, ROOT


def test_g3_g_release_authority_contract_passes() -> None:
    result = validate_authority()
    assert result["status"] == "PASS", result
    assert result["sentinel"] == "G3_G_RELEASE_AUTHORITY_OK"
    assert result["authority_root_count"] == 6


def test_release_contract_preserves_dual_state_and_offline_boundary() -> None:
    contract = json.loads((RELEASE_ROOT / "release_contract.json").read_text(encoding="utf-8"))
    assert contract["final_authorization_boundary"] == "SOFTWARE_RELEASE_READY != FINAL_SUBMISSION_AUTHORIZED"
    assert contract["mandatory_environment"] == {
        "acl_hccl_runtime": False, "api_keys": False, "mpi": False, "npu": False, "offline": True,
    }
    assert contract["controlled_material_policy"] == "EXCLUDE_UNLESS_EXPLICITLY_AUTHORIZED"
    assert contract["license_and_redistribution_policy"] == "AUDIT_ONLY_NOT_LEGAL_AUTHORIZATION"


def test_release_inventory_has_no_unknown_mandatory_source() -> None:
    inventory = json.loads((RELEASE_ROOT / "release_inventory.json").read_text(encoding="utf-8"))
    assert inventory["unknown_source_count"] == 0
    assert inventory["tracked_file_count"] == len(inventory["entries"])
    assert all(row["source_or_generated"] == "SOURCE" for row in inventory["entries"])


def test_release_user_actions_are_inherited_and_open() -> None:
    gate = json.loads((RELEASE_ROOT / "user_action_release_gate.json").read_text(encoding="utf-8"))
    assert gate["item_count"] == len(USER_ACTION_SUBJECTS) == 26
    assert {row["id"] for row in gate["items"]} == set(USER_ACTION_SUBJECTS)
    assert all(row["status"] == "USER_ACTION_REQUIRED" for row in gate["items"])
    assert gate["final_competition_submission_authorization"] == "USER_ACTION_REQUIRED"


def test_authority_roots_are_repository_relative() -> None:
    for relative, _ in AUTHORITY_ROOTS.values():
        path = Path(relative)
        assert not path.is_absolute()
        assert (ROOT / path / "SHA256SUMS").is_file()


def test_old_authority_baseline_is_content_addressed() -> None:
    baseline = json.loads((RELEASE_ROOT / "old_authority_baseline.json").read_text(encoding="utf-8"))
    assert baseline["status"] == "PASS"
    assert baseline["file_count"] == len(baseline["records"])
    assert baseline["file_count"] >= 20
    assert all(len(row["sha256"]) == 64 for row in baseline["records"])
