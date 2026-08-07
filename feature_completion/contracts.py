"""Versioned G3-B3 contracts without changing the frozen G3-B2 v1 semantics."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from algorithm.schedule_ir import validate_schedule as validate_schedule_v1


SCHEDULE_IR_VERSION = "g3-b3-schedule-ir-v2"
AGENT_PROPOSAL_VERSION = "g3-b3-agent-proposal-v2"
PAYLOAD_MODES = {"DENSE", "SPARSE_INDEX_VALUE"}
CHECKSUM_TYPES = {"NONE", "CRC32", "CRC32_PLUS_PARITY"}
FAILURE_CLASSES = {
    "CRC_MISMATCH",
    "LOGICAL_TIMEOUT",
    "TRANSIENT_TRANSFER_FAILURE",
    "INVALID_ARGUMENT",
    "INVALID_RANK",
    "INVALID_BUFFER",
    "UNSUPPORTED_DTYPE",
    "UNSUPPORTED_PRIMITIVE",
    "RETRY_EXHAUSTED",
    "NO_ALTERNATE_PATH",
    "UNRECOVERABLE_INTEGRITY_FAILURE",
}


def canonical_hash(value: Any, *, omitted_keys: tuple[str, ...] = ()) -> str:
    """Return a deterministic SHA256 for JSON-compatible contract data."""

    payload = copy.deepcopy(value)
    if isinstance(payload, dict):
        for key in omitted_keys:
            payload.pop(key, None)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_fields(value: dict[str, Any], required: set[str], subject: str) -> None:
    missing = sorted(required - value.keys())
    if missing:
        raise ValueError(f"{subject} missing required fields: {missing}")


def upgrade_dense_schedule_v2(schedule_v1: dict[str, Any]) -> dict[str, Any]:
    """Create a dense v2 schedule while leaving the supplied v1 schedule untouched."""

    validate_schedule_v1(schedule_v1)
    schedule = copy.deepcopy(schedule_v1)
    schedule["schema_version"] = SCHEDULE_IR_VERSION
    logical_bytes = schedule["message_size_bytes"]
    schedule["payload_transform"] = {
        "mode": "DENSE",
        "codec": "NONE",
        "logical_bytes": logical_bytes,
        "wire_bytes": logical_bytes,
        "value_bytes": logical_bytes,
        "index_bytes": 0,
        "metadata_bytes": 0,
        "compression_ratio": 1.0,
        "sparsity_ratio": 0.0,
        "eligibility": False,
        "fallback_reason": "CONTRACT_BASELINE",
    }
    schedule["integrity_policy"] = {
        "checksum_type": "NONE",
        "sequence_enabled": True,
        "chunk_id_enabled": True,
        "attempt_tracking": True,
        "verify_before_accept": False,
    }
    schedule["transport_policy"] = {
        "timeout_enabled": False,
        "logical_timeout_ticks": 0,
        "max_retries": 0,
        "retry_backoff_policy": "NONE",
        "retryable_error_classes": [],
        "terminal_error_classes": ["NO_ALTERNATE_PATH"],
    }
    schedule["flow_control_policy"] = {
        "enabled": False,
        "credit_window": 1,
        "max_inflight_chunks": 1,
        "high_watermark": 1,
        "low_watermark": 0,
    }
    schedule["schedule_hash"] = canonical_hash(schedule, omitted_keys=("schedule_hash",))
    validate_schedule_v2(schedule)
    return schedule


def validate_schedule_v2(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the v2 extension and its cross-field accounting invariants."""

    required = {
        "schema_version",
        "schedule_id",
        "primitive",
        "algorithm",
        "rank_size",
        "message_size_bytes",
        "dtype",
        "reduce_op",
        "topology_hash",
        "hardware_profile_hash",
        "chunk_size_bytes",
        "chunk_count",
        "phases",
        "dependencies",
        "memory_plan",
        "failure_policy",
        "estimated_metrics",
        "payload_transform",
        "integrity_policy",
        "transport_policy",
        "flow_control_policy",
        "schedule_hash",
    }
    _require_fields(schedule, required, "schedule v2")
    if schedule["schema_version"] != SCHEDULE_IR_VERSION:
        raise ValueError("schedule v2 schema_version mismatch")

    transform = schedule["payload_transform"]
    _require_fields(
        transform,
        {
            "mode",
            "codec",
            "logical_bytes",
            "wire_bytes",
            "value_bytes",
            "index_bytes",
            "metadata_bytes",
            "compression_ratio",
            "sparsity_ratio",
            "eligibility",
            "fallback_reason",
        },
        "payload_transform",
    )
    if transform["mode"] not in PAYLOAD_MODES:
        raise ValueError("unsupported payload transform mode")
    if transform["logical_bytes"] != schedule["message_size_bytes"]:
        raise ValueError("payload logical_bytes must match schedule message_size_bytes")
    byte_fields = ("logical_bytes", "wire_bytes", "value_bytes", "index_bytes", "metadata_bytes")
    if any(not isinstance(transform[key], int) or transform[key] < 0 for key in byte_fields):
        raise ValueError("payload byte accounting must use non-negative integers")
    if transform["wire_bytes"] != transform["value_bytes"] + transform["index_bytes"] + transform["metadata_bytes"]:
        raise ValueError("payload wire byte accounting mismatch")
    if not 0.0 <= float(transform["sparsity_ratio"]) <= 1.0:
        raise ValueError("sparsity_ratio must be in [0, 1]")
    expected_ratio = (
        float("inf")
        if transform["wire_bytes"] == 0
        else transform["logical_bytes"] / transform["wire_bytes"]
    )
    if expected_ratio != float("inf") and abs(float(transform["compression_ratio"]) - expected_ratio) > 1e-12:
        raise ValueError("compression_ratio does not match byte accounting")
    if transform["mode"] == "DENSE":
        if transform["codec"] != "NONE" or transform["index_bytes"] != 0:
            raise ValueError("dense payload must use codec NONE and zero index bytes")
        if transform["wire_bytes"] != transform["logical_bytes"]:
            raise ValueError("dense wire bytes must equal logical bytes")
    elif transform["codec"] != "SPARSE_INDEX_VALUE":
        raise ValueError("sparse payload must use SPARSE_INDEX_VALUE")

    integrity = schedule["integrity_policy"]
    _require_fields(
        integrity,
        {"checksum_type", "sequence_enabled", "chunk_id_enabled", "attempt_tracking", "verify_before_accept"},
        "integrity_policy",
    )
    if integrity["checksum_type"] not in CHECKSUM_TYPES:
        raise ValueError("unsupported checksum_type")

    transport = schedule["transport_policy"]
    _require_fields(
        transport,
        {
            "timeout_enabled",
            "logical_timeout_ticks",
            "max_retries",
            "retry_backoff_policy",
            "retryable_error_classes",
            "terminal_error_classes",
        },
        "transport_policy",
    )
    if transport["logical_timeout_ticks"] < 0 or transport["max_retries"] < 0:
        raise ValueError("timeout ticks and max_retries must be non-negative")
    classified = set(transport["retryable_error_classes"]) | set(transport["terminal_error_classes"])
    if not classified <= FAILURE_CLASSES:
        raise ValueError("transport policy contains an unknown failure class")

    flow = schedule["flow_control_policy"]
    _require_fields(
        flow,
        {"enabled", "credit_window", "max_inflight_chunks", "high_watermark", "low_watermark"},
        "flow_control_policy",
    )
    if not (
        0 <= flow["low_watermark"]
        <= flow["high_watermark"]
        <= flow["credit_window"]
        and 1 <= flow["max_inflight_chunks"] <= flow["credit_window"]
    ):
        raise ValueError("invalid flow-control bounds")

    expected_hash = canonical_hash(schedule, omitted_keys=("schedule_hash",))
    if schedule["schedule_hash"] != expected_hash:
        raise ValueError("schedule v2 canonical hash mismatch")
    return [
        {"invariant": "v2_required_fields", "passed": True},
        {"invariant": "payload_accounting", "passed": True},
        {"invariant": "integrity_policy", "passed": True},
        {"invariant": "transport_policy", "passed": True},
        {"invariant": "flow_control_policy", "passed": True},
        {"invariant": "canonical_hash", "passed": True},
    ]


def validate_agent_proposal_v2(proposal: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the data-aware proposal envelope frozen by G3-B3-A."""

    required = {
        "schema_version",
        "proposal_id",
        "schedule_algorithm",
        "payload_mode",
        "sparse_codec",
        "data_profile",
        "sparsity_ratio",
        "logical_bytes",
        "estimated_wire_bytes",
        "metadata_overhead",
        "estimated_compression_ratio",
        "encode_cost",
        "decode_cost",
        "chunk_size",
        "pipeline_depth",
        "credit_window",
        "integrity_policy",
        "retry_policy",
        "flow_control_policy",
        "dense_fallback_condition",
        "fallback_conditions",
        "correctness_plan",
        "validation_plan",
        "expected_benefit",
        "expected_risk",
        "proposal_hash",
    }
    _require_fields(proposal, required, "agent proposal v2")
    if proposal["schema_version"] != AGENT_PROPOSAL_VERSION:
        raise ValueError("agent proposal v2 schema_version mismatch")
    if proposal["payload_mode"] not in PAYLOAD_MODES:
        raise ValueError("agent proposal contains unsupported payload mode")
    if not 0.0 <= float(proposal["sparsity_ratio"]) <= 1.0:
        raise ValueError("agent proposal sparsity_ratio must be in [0, 1]")
    if proposal["logical_bytes"] <= 0 or proposal["estimated_wire_bytes"] < 0:
        raise ValueError("agent proposal byte counts are invalid")
    if proposal["chunk_size"] <= 0 or proposal["pipeline_depth"] <= 0 or proposal["credit_window"] <= 0:
        raise ValueError("agent proposal execution bounds must be positive")
    expected = canonical_hash(proposal, omitted_keys=("proposal_hash",))
    if proposal["proposal_hash"] != expected:
        raise ValueError("agent proposal v2 canonical hash mismatch")
    return [
        {"invariant": "proposal_required_fields", "passed": True},
        {"invariant": "proposal_payload_mode", "passed": True},
        {"invariant": "proposal_execution_bounds", "passed": True},
        {"invariant": "proposal_canonical_hash", "passed": True},
    ]
