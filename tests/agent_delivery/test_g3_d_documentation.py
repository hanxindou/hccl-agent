from __future__ import annotations

import json
from pathlib import Path

from tools.agent_delivery.documentation import REQUIRED_DOCUMENTS, validate_documentation


ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "docs/submission/agent_delivery"


def test_submission_documentation_and_provenance_mapping_validate():
    result = validate_documentation()
    assert result["status"] == "PASS", result["errors"]
    assert result["document_count"] == len(REQUIRED_DOCUMENTS)
    assert result["sentinels"] == ["PROVENANCE_OK", "CLAIM_BOUNDARIES_OK"]


def test_human_intervention_and_unavailable_history_are_disclosed():
    disclosure = json.loads((DELIVERY / "human_intervention_disclosure.json").read_text(encoding="utf-8"))
    assert disclosure["g3_b2"]["status"] == "HUMAN_INTERVENTION"
    assert disclosure["g3_b2"]["records"]
    assert disclosure["g3_b3"]["status"] == "HISTORICAL_TRACE_UNAVAILABLE"
    assert disclosure["g3_b3"]["records"] == []
    assert disclosure["hidden_chain_of_thought_included"] is False


def test_mapping_resolves_claims_and_keeps_unresolved_history_explicit():
    mapping = json.loads((DELIVERY / "source_commit_evidence_claim_mapping.json").read_text(encoding="utf-8"))
    claims = {row["claim_id"] for row in json.loads((ROOT / "docs/submission/report_claim_ledger.json").read_text(encoding="utf-8"))["claims"]}
    claim_edges = [row for row in mapping["relationships"] if row["to_type"] == "G3_C_CLAIM"]
    unavailable = [row for row in mapping["relationships"] if row["provenance"] == "HISTORICAL_TRACE_UNAVAILABLE"]
    assert claim_edges and all(row["to_id"] in claims for row in claim_edges)
    assert unavailable
    assert all(row["confidence"] in {"UNAVAILABLE", "HIGH"} for row in unavailable)


def test_docs_use_offline_agent_assisted_language_and_no_absolute_paths():
    combined = "\n".join((DELIVERY / name).read_text(encoding="utf-8") for name in REQUIRED_DOCUMENTS)
    assert "Agent-assisted" in combined
    assert "OFFLINE_REPLAY" in combined
    assert "HISTORICAL_TRACE_UNAVAILABLE" in combined
    assert "runtime_api_calls=[]" in combined
    assert "F:\\" not in combined
    assert "/mnt/" not in combined

