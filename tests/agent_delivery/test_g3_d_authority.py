from __future__ import annotations

import json
from pathlib import Path

from tools.agent_delivery.authority import PROVENANCE_VOCABULARY, validate_authority_artifacts


ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "docs/submission/agent_delivery"


def test_authority_inventory_and_frozen_hashes_are_valid():
    result = validate_authority_artifacts()
    assert result["status"] == "PASS", result["errors"]
    assert result["sentinel"] == "G3_D_AUTHORITY_INVENTORY_OK"
    assert result["g3_b2"]["status"] == "PASS"
    assert result["g3_b3"]["status"] == "PASS"


def test_delivery_contract_preserves_offline_freeze_and_claim_boundaries():
    contract = json.loads((DELIVERY / "delivery_contract.json").read_text(encoding="utf-8"))
    assert set(contract["provenance_vocabulary"]) == set(PROVENANCE_VOCABULARY)
    assert contract["mandatory_path"]["identity"] == "OFFLINE_REPLAY"
    assert contract["mandatory_path"]["api_keys_required"] == []
    assert contract["mandatory_path"]["network_required"] is False
    assert contract["claim_language_authority"] == "docs/submission/report_claim_ledger.json"
    assert contract["feature_freeze"]["status"] == "FROZEN"
    assert contract["hardware_boundary"]["real_device_acceptance"] == "HARDWARE_BLOCKED"
    assert contract["hardware_boundary"]["runtime_api_calls"] == []


def test_inventory_is_complete_file_level_and_excludes_local_logs_as_authority():
    inventory = json.loads((DELIVERY / "authority_inventory.json").read_text(encoding="utf-8"))
    assert inventory["ignored_logs_are_authority"] is False
    paths = {row["path"] for row in inventory["tracked_file_inventory"]}
    assert "agent/hccl_agent.py" in paths
    assert "agent/g3_b2_optimization_loop.py" in paths
    assert "agent/g3_b3_feature_loop.py" in paths
    assert "prompts/algorithm_prompt.txt" in paths
    assert all(not path.startswith("logs/") for path in paths)

