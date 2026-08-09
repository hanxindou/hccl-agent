from __future__ import annotations

import json
from pathlib import Path

from tools.agent_delivery.finalize import (
    EXPECTED_EVIDENCE_FILES,
    FINAL_SENTINELS,
    USER_ACTION_REQUIRED,
    _claim_validation,
    _content_audits,
    _freeze_validation,
    verify_final_evidence,
)
from tools.agent_delivery.common import sha256_file


ROOT = Path(__file__).resolve().parents[2]


def test_final_claim_freeze_secret_and_portability_preflight_passes():
    claim = _claim_validation()
    freeze = _freeze_validation()
    secrets, paths = _content_audits()
    assert claim["status"] == "PASS", claim["errors"]
    assert freeze["status"] == "PASS", freeze["errors"]
    assert freeze["cpu_sim_contract"] == {
        "artifact_role": "CPU_SIM_REFERENCE_PLUGIN",
        "soname": "libhccl_plugin.so",
        "exported_symbol_count": 19,
    }
    assert freeze["real_device_acceptance"] == "HARDWARE_BLOCKED"
    assert freeze["runtime_api_calls"] == []
    assert secrets["status"] == "PASS", secrets["findings"]
    assert paths["status"] == "PASS", paths["findings"]


def test_existing_submission_staging_has_g3_d_delivery_coverage_contract():
    source = (ROOT / "tools/submission_cli/core.py").read_text(encoding="utf-8")
    for token in (
        '"prompts"',
        '"tools/agent_delivery"',
        '"docs/submission/agent_delivery"',
        '"tests/agent_delivery"',
        '"docs/submission/report_claim_ledger.json"',
        '"docs/submission/report_data_ledger.json"',
        '"g3_d_agent_prompt_delivery": "PASS"',
    ):
        assert token in source


def test_final_evidence_schema_and_user_actions_are_complete():
    assert len(EXPECTED_EVIDENCE_FILES) == len(set(EXPECTED_EVIDENCE_FILES))
    assert EXPECTED_EVIDENCE_FILES[-1] == "SHA256SUMS"
    assert set(FINAL_SENTINELS) == {
        "G3_D_AUTHORITY_INVENTORY_OK",
        "PROMPT_REGISTRY_OK",
        "SKILL_REGISTRY_OK",
        "TRACE_INDEX_OK",
        "OFFLINE_REPLAY_OK",
        "PROVENANCE_OK",
        "CLAIM_BOUNDARIES_OK",
        "NO_SECRETS_OK",
        "G3_D_AGENT_PROMPT_DELIVERY_OK",
    }
    assert {row["topic"] for row in USER_ACTION_REQUIRED} == {
        "license/copyright",
        "official artifact redistribution",
        "controlled competition materials",
        "submission archive format and size limits",
        "precision interpretation",
        "final submission language and template",
        "real-device acceptance",
    }


def test_final_evidence_verifier_checks_exact_hash_coverage(tmp_path):
    for name in EXPECTED_EVIDENCE_FILES:
        if name == "SHA256SUMS":
            continue
        path = tmp_path / name
        if name == "result.json":
            value = {
                "delivery_status": "G3_D_AGENT_PROMPT_DELIVERY_OK",
                "external_api_required": False,
                "real_device_api_executed": False,
                "runtime_api_calls": [],
                "sentinels": list(FINAL_SENTINELS),
            }
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
        else:
            path.write_text("{}\n" if name.endswith(".json") else "# fixture\n", encoding="utf-8")
    lines = [
        f"{sha256_file(path)}  {path.relative_to(tmp_path).as_posix()}"
        for path in sorted(tmp_path.iterdir())
    ]
    (tmp_path / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = verify_final_evidence(tmp_path)
    assert result["status"] == "PASS", result["errors"]
    (tmp_path / "README.md").write_text("tampered\n", encoding="utf-8")
    assert verify_final_evidence(tmp_path)["status"] == "FAIL"
