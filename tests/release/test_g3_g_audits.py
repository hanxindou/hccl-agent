from __future__ import annotations

import json

from tools.release_audit.audits import C_SENTINELS, scan_secret_text, validate_audits
from tools.release_audit.common import RELEASE_ROOT


def _load(name: str) -> dict:
    return json.loads((RELEASE_ROOT / name).read_text(encoding="utf-8"))


def test_all_release_audit_classes_are_separate_and_complete() -> None:
    result = validate_audits()
    assert result["status"] == "PASS", result["errors"]
    assert result["sentinels"] == C_SENTINELS
    for name in ("dependency", "license", "copyright", "redistribution", "security", "privacy", "controlled_material", "third_party_asset"):
        assert result[f"{name}_audit"] == "COMPLETED"


def test_license_audit_does_not_claim_legal_authorization() -> None:
    license_inventory = _load("license_inventory.json")
    redistribution = _load("redistribution_audit.json")
    assert license_inventory["status"] == "COMPLETED"
    assert license_inventory["authorization"] == "USER_ACTION_REQUIRED"
    assert license_inventory["license_audit_is_legal_authorization"] is False
    assert redistribution["authorization"] == "USER_ACTION_REQUIRED"
    assert redistribution["legal_conclusion_provided"] is False


def test_controlled_material_and_official_assets_are_excluded() -> None:
    audit = _load("controlled_material_audit.json")
    assert audit["status"] == "PASS"
    assert audit["default_policy"] == "EXCLUDE_UNLESS_EXPLICITLY_AUTHORIZED"
    assert audit["controlled_item_count"] >= 1
    assert all(row["included"] is False and row["decision"] == "EXCLUDE_CONTROLLED" for row in audit["items"])
    assert audit["official_binary_included"] is False


def test_secret_scanner_redacts_synthetic_fixture() -> None:
    synthetic = "api_key=" + "sk-" + "SYNTHETIC_TEST_ONLY_12345"
    findings = scan_secret_text(synthetic, "<synthetic-fixture>")
    assert len(findings) == 1
    assert findings[0]["type"] == "CREDENTIAL_VALUE"
    assert findings[0]["secret_value_recorded"] is False
    assert findings[0]["classification"] == "POTENTIAL_SECRET"
    assert "SYNTHETIC_TEST_ONLY" not in json.dumps(findings)
    assert len(findings[0]["redacted_fingerprint"]) == 12


def test_security_privacy_and_dependency_mandatory_gates_pass() -> None:
    security = _load("security_audit.json")
    privacy = _load("privacy_audit.json")
    dependency = _load("dependency_manifest.json")
    assert security["status"] == privacy["status"] == dependency["status"] == "PASS"
    assert security["raw_secret_values_recorded"] is False
    assert security["secret_findings"] == []
    assert len(security["reviewed_documentation_placeholders"]) == 4
    assert privacy["findings"] == []
    assert all(row["disposition"] == "EXCLUDE_PRIVATE" for row in privacy["excluded_private_path_findings"])
    assert dependency["dependency_install_attempted"] is False
    assert dependency["mandatory_execution_offline"] is True


def test_release_risks_do_not_hide_software_failure_as_user_action() -> None:
    risks = _load("release_risk_register.json")
    assert risks["mandatory_software_blocker_count"] == 0
    assert any(row["blocking_scope"] == "HARDWARE_BLOCKED" for row in risks["risks"])
    assert all(row["blocking_scope"] != "MANDATORY_SOFTWARE" for row in risks["risks"])
