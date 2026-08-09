from __future__ import annotations

import json
from pathlib import Path

from tools.visualization.authority import CANDIDATE_STATUSES, TRUTH_IDENTITIES, validate_authority
from tools.visualization.common import sha256_file


ROOT = Path(__file__).resolve().parents[2]
VISUALIZATION = ROOT / "docs/submission/visualization"


def _json(name: str):
    return json.loads((VISUALIZATION / name).read_text(encoding="utf-8"))


def test_visualization_authority_inventory_validates_without_assets():
    result = validate_authority()
    assert result["status"] == "PASS", result["errors"]
    assert result["sentinel"] == "G3_E_VISUALIZATION_AUTHORITY_OK"
    assert result["chart_data_count"] == 16
    assert result["metric_count"] == 1082
    assert result["claim_count"] == 21
    assert result["final_assets_built"] is False
    assert result["benchmark_rerun"] is False
    assert result["runtime_api_calls"] == []


def test_all_chart_data_hashes_and_metric_sources_are_registered():
    inventory = _json("chart_data_inventory.json")
    assert inventory["chart_data_count"] == len(inventory["artifacts"]) == 16
    assert {row["source_path"] for row in inventory["artifacts"]} == {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "docs/submission/report_chart_data").glob("*.json")
    }
    for row in inventory["artifacts"]:
        assert sha256_file(ROOT / row["source_path"]) == row["source_sha256"]
        assert row["metric_count"] == len(row["metric_ids"])
        assert row["allowed_visualizations"]
        assert row["forbidden_interpretations"]


def test_candidate_contract_records_rejections_and_truth_boundaries():
    contract = _json("visualization_contract.json")
    candidates = _json("chart_candidate_inventory.json")
    assert set(contract["truth_identities"]) == set(TRUTH_IDENTITIES)
    assert set(contract["candidate_statuses"]) == set(CANDIDATE_STATUSES)
    assert candidates["candidate_count"] == 13
    assert all(row["status"] in CANDIDATE_STATUSES for row in candidates["candidates"])
    assert all(row["claim_refs"] and row["truth_identity"] and row["limitations"] for row in candidates["candidates"])
    direct = next(row for row in candidates["candidates"] if row["figure_id"] == "FIG-10")
    assert {"DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED"} <= set(direct["truth_identity"])


def test_renderer_and_story_contract_are_offline_and_claim_safe():
    contract = _json("visualization_contract.json")
    story = _json("story_contract.json")
    assert contract["renderer_decision"] == {
        "mandatory": "Python stdlib deterministic self-contained SVG",
        "canonical_asset": "SVG",
        "png": "OPTIONAL_NON_CANONICAL_ONLY_IF_DETERMINISTIC",
        "external_dependency_required": False,
        "network_required": False,
        "browser_service_required": False,
    }
    assert not any(contract["mandatory_offline_boundary"].values())
    assert story["strongest_evidence_boundary"] == {
        "raw": 45.59283008,
        "canonical_display": "45.59%",
        "truth_identity": "SIMULATED_ONLY",
        "wins": 18,
        "ties": 0,
        "losses": 0,
        "authoritative_source": "docs/submission/report_data_ledger.json",
    }
    assert story["real_device_acceptance"] == "HARDWARE_BLOCKED"
