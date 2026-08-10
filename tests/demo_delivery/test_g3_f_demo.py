from __future__ import annotations

from tools.demo_delivery.common import DELIVERY_ROOT, read_json
from tools.demo_delivery.demo import run_profile, validate_demo_package


def test_demo_manifest_and_fallback_contract_pass() -> None:
    result = validate_demo_package()
    assert result["status"] == "PASS", result["errors"]
    assert result["quick_step_count"] == 3
    assert result["fallback_count"] == 3
    assert result["sentinels"] == ["G3_F_OFFLINE_DEMO_OK", "G3_F_DEMO_FALLBACK_OK"]


def test_quick_demo_has_cpu_sim_replay_and_visual_verification() -> None:
    manifest = read_json(DELIVERY_ROOT / "demo_manifest.json")
    assert manifest["profiles"]["QUICK_DEMO"] == [
        "DEMO-CPU-SIM", "DEMO-AGENT-REPLAY", "DEMO-VISUAL-VERIFY",
    ]
    indexed = {row["step_id"]: row for row in manifest["steps"]}
    assert indexed["DEMO-CPU-SIM"]["truth_identity"] == "LIVE_DEMO_CPU_SIM"
    assert indexed["DEMO-AGENT-REPLAY"]["truth_identity"] == "DEMO_REPLAY"
    assert indexed["DEMO-VISUAL-VERIFY"]["truth_identity"] == "HISTORICAL_EVIDENCE"
    for step_id in manifest["profiles"]["QUICK_DEMO"]:
        row = indexed[step_id]
        assert row["network_required"] is False
        assert row["api_key_required"] is False
        assert row["hardware_required"] is False
        assert row["fallback_step"]


def test_fallback_is_deterministic_and_never_claims_live_execution() -> None:
    first = run_profile("fallback")
    second = run_profile("fallback")
    assert first["status"] == second["status"] == "PASS"
    assert first["canonical_transcript_sha256"] == second["canonical_transcript_sha256"]
    assert first["canonical_transcript"]["live_execution"] is False
    assert all(row["truth_identity"] == "PRERECORDED_DETERMINISTIC_OUTPUT" for row in first["canonical_transcript"]["steps"])
    assert first["sentinel"] == "G3_F_DEMO_FALLBACK_OK"


def test_demo_contract_excludes_benchmark_network_and_hardware() -> None:
    contract = read_json(DELIVERY_ROOT / "demo_contract.json")
    assert contract["benchmark_rerun"] is False
    assert contract["mandatory_network_dependency"] is False
    assert contract["mandatory_external_api_dependency"] is False
    assert contract["mandatory_real_device_dependency"] is False
    assert contract["failure_policy"]["fallback_never_impersonates_live"] is True
