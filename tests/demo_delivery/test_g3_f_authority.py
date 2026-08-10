from __future__ import annotations

from tools.demo_delivery.authority import AUTHORITY_ROOTS, validate_authority
from tools.demo_delivery.common import DELIVERY_ROOT, read_json


def test_g3_f_authority_contract_passes() -> None:
    result = validate_authority()
    assert result["status"] == "PASS", result["errors"]
    assert result["sentinel"] == "G3_F_DEMO_AUTHORITY_OK"
    assert result["authority_root_count"] == len(AUTHORITY_ROOTS)


def test_required_candidates_are_offline_keyless_and_no_npu() -> None:
    inventory = read_json(DELIVERY_ROOT / "demo_candidate_inventory.json")
    required = [row for row in inventory["candidates"] if row["status"] == "REQUIRED"]
    assert {row["demo_step_id"] for row in required} == {
        "DEMO-CPU-SIM", "DEMO-AGENT-REPLAY", "DEMO-VISUAL-VERIFY",
    }
    assert all(not row["network_required"] for row in required)
    assert all(not row["api_key_required"] for row in required)
    assert all(not row["hardware_required"] for row in required)
    assert any(row["truth_identity"] == "LIVE_DEMO_CPU_SIM" for row in required)


def test_final_binary_and_media_tooling_are_honest() -> None:
    production = read_json(DELIVERY_ROOT / "video_production_contract.json")
    environment = read_json(DELIVERY_ROOT / "recording_environment_contract.json")
    assert production["mandatory_deliverable"] == "VALIDATED_PRODUCTION_PACKAGE"
    assert production["final_video_binary_status"] == "USER_ACTION_REQUIRED"
    assert all(not row["installation_attempted"] for row in environment["media_tooling"].values())
    assert environment["mandatory_environment"] == {
        "offline": True,
        "api_keys": False,
        "npu": False,
        "acl_hccl_runtime": False,
        "mpi": False,
    }
