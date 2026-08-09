import dataclasses
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from algorithm.ring_schedule import generate_ring_schedule
from feature_completion.reliability import (
    FailureClass,
    FailureReason,
    Fault,
    IntegrityConfig,
    IntegrityMetadata,
    attach_reliability_policy,
    crc32,
    execute_transfer,
    verify_chunked,
)
from feature_completion.sparse import attach_payload_transform, decide_sparse, encode_values


IDENTITY = IntegrityMetadata(transfer_id=7, sequence_id=2, chunk_id=2)
PAYLOAD = b"integrity-payload"


def run(fault, *, max_retries=3, fault_until_attempt=0):
    return execute_transfer(
        PAYLOAD,
        IDENTITY,
        IntegrityConfig(
            max_retries=max_retries,
            logical_timeout_ticks=8,
            retry_backoff_ticks=1,
            fault=fault,
            fault_until_attempt=fault_until_attempt,
            corruption_offset=3,
        ),
    )


def test_crc32_known_vectors_and_non_aligned_payloads():
    assert crc32(b"") == 0
    assert crc32(b"123456789") == 0xCBF43926
    assert crc32(b"a") == 0xE8B7BE43
    assert crc32(bytes(range(7))) == 0xAD5809F9


def test_clean_transfer_has_identity_crc_and_no_retry():
    result = run(Fault.NONE)
    assert result.result_code == "HCCL_SUCCESS"
    assert result.output == PAYLOAD
    assert result.metadata.payload_length == len(PAYLOAD)
    assert result.metadata.crc32 == crc32(PAYLOAD)
    assert result.attempt_count == 1
    assert result.retransmitted_bytes == 0
    assert result.trace[0]["attempt"] == 0


@pytest.mark.parametrize("fault", [Fault.BIT_FLIP, Fault.BYTE_FLIP, Fault.CRC_TAMPER])
def test_corruption_is_detected_then_recovers_with_one_retry(fault):
    result = run(fault)
    assert result.result_code == "HCCL_SUCCESS"
    assert result.output == PAYLOAD
    assert result.corruption_detected is True
    assert result.recovered is True
    assert result.attempt_count == 2
    assert result.retransmitted_bytes == len(PAYLOAD)
    assert result.trace[0]["failure_reason"] == FailureReason.CRC_MISMATCH.value


def test_repeated_corruption_exhausts_exact_retry_budget():
    result = run(Fault.BIT_FLIP, max_retries=3, fault_until_attempt=3)
    assert result.result_code == "HCCL_ERR_CRC_MISMATCH"
    assert result.classification == FailureClass.TERMINAL
    assert result.failure_reason == FailureReason.RETRY_EXHAUSTED
    assert result.attempt_count == 4
    assert result.retransmitted_bytes == len(PAYLOAD) * 3
    assert result.output is None


def test_logical_timeout_recovery_and_terminal_exhaustion_use_no_sleep():
    recovered = run(Fault.LOGICAL_TIMEOUT, max_retries=2, fault_until_attempt=0)
    assert recovered.result_code == "HCCL_SUCCESS"
    assert recovered.timed_out is True
    assert recovered.recovered is True
    assert recovered.attempt_count == 2
    assert recovered.trace[0]["completion_tick"] > recovered.trace[0]["deadline_tick"]

    terminal = run(Fault.LOGICAL_TIMEOUT, max_retries=2, fault_until_attempt=2)
    assert terminal.result_code == "HCCL_ERR_TIMEOUT"
    assert terminal.failure_reason == FailureReason.RETRY_EXHAUSTED
    assert terminal.attempt_count == 3


def test_transient_transfer_is_retryable():
    result = run(Fault.TRANSIENT_TRANSFER, max_retries=2)
    assert result.result_code == "HCCL_SUCCESS"
    assert result.recovered is True
    assert result.trace[0]["classification"] == FailureClass.RETRYABLE.value
    assert result.trace[0]["failure_reason"] == FailureReason.TRANSIENT_TRANSFER_FAILURE.value


def test_invalid_input_and_no_path_do_not_blindly_retry():
    invalid = run(Fault.INVALID_INPUT, fault_until_attempt=3)
    assert invalid.classification == FailureClass.NON_RETRYABLE
    assert invalid.failure_reason == FailureReason.INVALID_ARGUMENT
    assert invalid.attempt_count == 0
    assert invalid.retransmitted_bytes == 0

    no_path = run(Fault.NO_ALTERNATE_PATH, fault_until_attempt=3)
    assert no_path.classification == FailureClass.TERMINAL
    assert no_path.failure_reason == FailureReason.NO_ALTERNATE_PATH
    assert no_path.attempt_count == 0
    assert no_path.retransmitted_bytes == 0


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        (Fault.DUPLICATE_SEQUENCE, FailureReason.DUPLICATE_SEQUENCE),
        (Fault.MISSING_CHUNK, FailureReason.MISSING_CHUNK),
        (Fault.REORDERED_SEQUENCE, FailureReason.REORDERED_SEQUENCE),
    ],
)
def test_sequence_errors_are_terminal(fault, reason):
    result = run(fault)
    assert result.result_code == "HCCL_ERR_COMM_FAILURE"
    assert result.classification == FailureClass.TERMINAL
    assert result.failure_reason == reason
    assert result.sequence_valid is False
    assert result.attempt_count == 1


def test_attempt_count_never_exceeds_configured_bound():
    for retries in range(5):
        result = run(Fault.BIT_FLIP, max_retries=retries, fault_until_attempt=10)
        assert result.attempt_count <= retries + 1


def test_chunked_large_payload_is_bounded_and_deterministic():
    payload = bytes(range(256)) * 8193
    first = verify_chunked(payload, chunk_bytes=1024 * 1024, transfer_id=9)
    second = verify_chunked(payload, chunk_bytes=1024 * 1024, transfer_id=9)
    assert first["passed"] is True
    assert len(first["chunks"]) == 3
    assert first["peak_materialized_bytes"] == 1024 * 1024
    assert [row.metadata.crc32 for row in first["chunks"]] == [row.metadata.crc32 for row in second["chunks"]]


def test_schedule_ir_v2_carries_integrity_identity_and_retry_policy():
    v1 = generate_ring_schedule("AllReduce", 4, 4096)
    payload = encode_values([1.0] + [0.0] * 1023, "FP32")
    sparse_v2 = attach_payload_transform(v1, payload, decide_sparse(payload))
    schedule = attach_reliability_policy(sparse_v2)
    metadata = [
        transfer["integrity_metadata"]
        for phase in schedule["phases"]
        for transfer in phase["transfers"]
    ]
    assert schedule["integrity_policy"]["checksum_type"] == "CRC32"
    assert schedule["transport_policy"]["max_retries"] == 3
    assert [row["sequence_id"] for row in metadata] == list(range(len(metadata)))
    assert all(row["attempt"] == 0 and row["payload_length"] > 0 for row in metadata)


def test_invalid_retry_bounds_are_rejected():
    with pytest.raises(ValueError, match="bounds"):
        execute_transfer(PAYLOAD, IDENTITY, dataclasses.replace(IntegrityConfig(), logical_timeout_ticks=0))
