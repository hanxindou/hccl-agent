from __future__ import annotations

import pytest

from tools.reporting.evidence_reader import CLAIM_LEDGER, DATA_LEDGER, read_json
from tools.reporting.schemas import CLAIM_FIELDS, PROHIBITED_TRUTH_LABELS, TRUTH_LABELS, USER_ACTIONS


@pytest.fixture(scope="module")
def claims() -> dict:
    return read_json(CLAIM_LEDGER)


def test_claim_schema_and_count(claims: dict) -> None:
    assert claims["schema_version"] == "g3-c-report-claim-ledger-v1"
    assert claims["claim_count"] == len(claims["claims"])
    assert claims["claim_count"] >= 20


def test_claim_ids_are_unique(claims: dict) -> None:
    ids = [row["claim_id"] for row in claims["claims"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("field", CLAIM_FIELDS)
def test_every_claim_has_required_field(claims: dict, field: str) -> None:
    assert all(field in row for row in claims["claims"]), field


def test_claim_truth_labels_are_allowlisted(claims: dict) -> None:
    labels = {row["truth_label"] for row in claims["claims"]}
    assert labels <= TRUTH_LABELS
    assert not labels & PROHIBITED_TRUTH_LABELS


def test_claim_metric_references_exist(claims: dict) -> None:
    metric_ids = {row["metric_id"] for row in read_json(DATA_LEDGER)["metrics"]}
    for claim in claims["claims"]:
        assert set(claim["metric_refs"]) <= metric_ids, claim["claim_id"]


def test_claim_evidence_references_are_repo_relative(claims: dict) -> None:
    for claim in claims["claims"]:
        assert claim["evidence_refs"]
        assert all(not ref.startswith(("/", "\\")) and ":\\" not in ref for ref in claim["evidence_refs"])


def test_hardware_dependent_claims_are_bounded(claims: dict) -> None:
    rows = [row for row in claims["claims"] if row["hardware_dependency"]]
    assert rows
    assert all(row["truth_label"] in {"SIMULATED_ONLY", "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED"} for row in rows)


def test_user_action_inventory_is_exact() -> None:
    ids = [row["id"] for row in USER_ACTIONS]
    assert ids == ["UA-B-001", "UA-B-002", "UA-B-003", "UA-B-004", "UA-C-001", "UA-C-002", "UA-C-003"]
    assert all(row["status"] == "USER_ACTION_REQUIRED" for row in USER_ACTIONS)
