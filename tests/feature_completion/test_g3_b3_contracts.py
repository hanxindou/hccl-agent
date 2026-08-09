import hashlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from algorithm.ring_schedule import generate_ring_schedule
from algorithm.schedule_ir import validate_schedule as validate_schedule_v1
from feature_completion.contracts import (
    AGENT_PROPOSAL_VERSION,
    SCHEDULE_IR_VERSION,
    canonical_hash,
    upgrade_dense_schedule_v2,
    validate_agent_proposal_v2,
    validate_schedule_v2,
)
from tools.g3_b3_baseline import (
    CLAIM_CONTRACT,
    DATA_PROFILES,
    PROPOSAL_SCHEMA,
    RELIABILITY_MATRIX,
    SCHEDULE_SCHEMA,
    SPARSE_MATRIX,
    proposal_audit,
    validate_g3_b2_integrity,
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v2_schemas_are_versioned_and_contain_required_policies():
    schedule = _load(SCHEDULE_SCHEMA)
    proposal = _load(PROPOSAL_SCHEMA)
    assert schedule["$id"] == SCHEDULE_IR_VERSION
    assert proposal["$id"] == AGENT_PROPOSAL_VERSION
    assert {
        "payload_transform",
        "integrity_policy",
        "transport_policy",
        "flow_control_policy",
    } <= set(schedule["required"])
    assert {
        "data_profile",
        "estimated_wire_bytes",
        "integrity_policy",
        "retry_policy",
        "flow_control_policy",
        "validation_plan",
    } <= set(proposal["required"])


def test_dense_v1_schedule_remains_valid_and_upgrades_without_mutation():
    v1 = generate_ring_schedule("AllReduce", 4, 65536)
    before = canonical_hash(v1)
    assert all(row["passed"] for row in validate_schedule_v1(v1))
    v2 = upgrade_dense_schedule_v2(v1)
    assert canonical_hash(v1) == before
    assert v1["schema_version"] == "g3-b2-schedule-ir-v1"
    assert v2["schema_version"] == SCHEDULE_IR_VERSION
    assert v2["payload_transform"]["mode"] == "DENSE"
    assert v2["payload_transform"]["wire_bytes"] == v2["message_size_bytes"]
    assert all(row["passed"] for row in validate_schedule_v2(v2))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("mode", "LOSSY_INT8", "unsupported payload transform mode"),
        ("wire_bytes", 7, "payload wire byte accounting mismatch"),
    ],
)
def test_invalid_payload_transform_is_rejected(field, value, message):
    schedule = upgrade_dense_schedule_v2(generate_ring_schedule("AllReduce", 4, 65536))
    schedule["payload_transform"][field] = value
    schedule["schedule_hash"] = canonical_hash(schedule, omitted_keys=("schedule_hash",))
    with pytest.raises(ValueError, match=message):
        validate_schedule_v2(schedule)


def test_agent_proposal_v2_contract_and_hash():
    audit = proposal_audit()
    proposal = audit["proposal"]
    assert proposal["schema_version"] == AGENT_PROPOSAL_VERSION
    assert proposal["payload_mode"] == "DENSE"
    assert all(row["passed"] for row in validate_agent_proposal_v2(proposal))
    proposal["estimated_wire_bytes"] += 1
    with pytest.raises(ValueError, match="canonical hash"):
        validate_agent_proposal_v2(proposal)


def test_sparse_profiles_and_incremental_matrices_are_frozen_and_complete():
    profiles = _load(DATA_PROFILES)
    sparse = _load(SPARSE_MATRIX)
    reliability = _load(RELIABILITY_MATRIX)
    assert profiles["frozen"] is True
    assert [row["profile_id"] for row in profiles["profiles"]] == ["S00", "S25", "S50", "S75", "S90", "S100"]
    assert [row["sparsity_ratio"] for row in profiles["profiles"]] == [0.0, 0.25, 0.5, 0.75, 0.9, 1.0]
    assert 15 <= len(sparse["scenarios"]) <= 25
    assert {row["primitive"] for row in sparse["scenarios"]} == {"AllReduce", "AllGather", "ReduceScatter"}
    assert {row["data_profile"] for row in sparse["scenarios"]} >= {"S00", "S25", "S50", "S75", "S90"}
    assert {row["topology_variant"] for row in sparse["scenarios"]} == {"full_mesh_8", "ring_16", "fat_tree_64", "asymmetric_16"}
    assert max(row["message_size_bytes"] for row in sparse["scenarios"]) >= 1024**3
    assert len(reliability["scenarios"]) == 12
    assert reliability["wall_clock_sleep_allowed"] is False
    assert len({row["scenario_id"] for row in reliability["scenarios"]}) == 12


def test_claim_contract_preserves_truth_boundary():
    claims = _load(CLAIM_CONTRACT)
    assert claims["frozen"] is True
    assert all(row["equivalent"] is False for row in claims["equivalence_prohibitions"])
    assert all(value is False for value in claims["required_false_flags"].values())
    assert claims["required_empty_fields"]["runtime_api_calls"] == []


def test_g3_b2_historical_baseline_integrity_is_still_valid():
    audit = validate_g3_b2_integrity()
    assert audit["valid"] is True
    assert audit["old_evidence_modified"] is False
    assert audit["benchmark_sha256"] == "db6519370256f3c73ca96177e599f3dabc7dcbc1c0319b5ef2b0cc53236b2bfe"
    assert audit["parameter_sha256"] == "df4dd8fd39db45c923c14ada30c1531c666e49d384be806267aeaa228285ebdf"
    assert audit["historical_performance"]["weighted_simulated_improvement_percent"] == 45.59283008


def test_g3_b3_a_authority_evidence_checksums_and_status():
    roots = sorted((ROOT / "experiments/feature_completion/evidence").glob("g3_b3_a_baseline_*"))
    assert len(roots) == 1
    evidence = roots[0]
    for line in (evidence / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == expected
    result = _load(evidence / "result.json")
    baseline = _load(evidence / "baseline.json")
    assert result["checkpoint_status"] == "COMPLETED"
    assert result["sparse_implemented"] is False
    assert result["algorithm_implementation_changed"] is False
    assert result["public_abi_changed"] is False
    assert result["runtime_api_calls"] == []
    assert baseline["freeze_status"] == "FROZEN"
    assert baseline["schedule_ir_version"] == SCHEDULE_IR_VERSION

