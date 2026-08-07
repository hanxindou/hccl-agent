"""Deterministic host integrity, logical timeout, and bounded retry model."""

from __future__ import annotations

import binascii
import copy
import dataclasses
from dataclasses import dataclass
from enum import Enum

from .contracts import canonical_hash, validate_schedule_v2


INTEGRITY_VERSION = "g3-b3-host-integrity-crc32-v1"
RETRY_POLICY_VERSION = "g3-b3-bounded-retry-v1"


class Fault(str, Enum):
    NONE = "NONE"
    BIT_FLIP = "BIT_FLIP"
    BYTE_FLIP = "BYTE_FLIP"
    CRC_TAMPER = "CRC_TAMPER"
    LOGICAL_TIMEOUT = "LOGICAL_TIMEOUT"
    TRANSIENT_TRANSFER = "TRANSIENT_TRANSFER"
    DUPLICATE_SEQUENCE = "DUPLICATE_SEQUENCE"
    MISSING_CHUNK = "MISSING_CHUNK"
    REORDERED_SEQUENCE = "REORDERED_SEQUENCE"
    INVALID_INPUT = "INVALID_INPUT"
    NO_ALTERNATE_PATH = "NO_ALTERNATE_PATH"


class FailureClass(str, Enum):
    NONE = "NONE"
    RETRYABLE = "RETRYABLE"
    NON_RETRYABLE = "NON_RETRYABLE"
    TERMINAL = "TERMINAL"


class FailureReason(str, Enum):
    NONE = "NONE"
    CRC_MISMATCH = "CRC_MISMATCH"
    LOGICAL_TIMEOUT = "LOGICAL_TIMEOUT"
    TRANSIENT_TRANSFER_FAILURE = "TRANSIENT_TRANSFER_FAILURE"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    NO_ALTERNATE_PATH = "NO_ALTERNATE_PATH"
    UNRECOVERABLE_INTEGRITY_FAILURE = "UNRECOVERABLE_INTEGRITY_FAILURE"
    DUPLICATE_SEQUENCE = "DUPLICATE_SEQUENCE"
    MISSING_CHUNK = "MISSING_CHUNK"
    REORDERED_SEQUENCE = "REORDERED_SEQUENCE"


@dataclass(frozen=True)
class IntegrityMetadata:
    transfer_id: int
    sequence_id: int
    chunk_id: int
    attempt: int = 0
    payload_length: int = 0
    crc32: int = 0


@dataclass(frozen=True)
class IntegrityConfig:
    max_retries: int = 3
    logical_timeout_ticks: int = 8
    retry_backoff_ticks: int = 1
    fault: Fault = Fault.NONE
    fault_until_attempt: int = 0
    corruption_offset: int = 0
    expected_sequence_id: int = 0
    observed_sequence_id: int = 0


@dataclass(frozen=True)
class IntegrityResult:
    result_code: str
    classification: FailureClass
    failure_reason: FailureReason
    metadata: IntegrityMetadata
    attempt_count: int
    retransmitted_bytes: int
    start_tick: int
    deadline_tick: int
    completion_tick: int
    timed_out: bool
    corruption_detected: bool
    sequence_valid: bool
    recovered: bool
    output: bytes | None
    trace: tuple[dict, ...]


def crc32(payload: bytes) -> int:
    return binascii.crc32(payload) & 0xFFFFFFFF


def execute_transfer(
    source: bytes,
    identity: IntegrityMetadata,
    config: IntegrityConfig = IntegrityConfig(),
) -> IntegrityResult:
    if config.logical_timeout_ticks <= 0 or config.max_retries < 0:
        raise ValueError("invalid integrity transport bounds")
    metadata = dataclasses.replace(identity, payload_length=len(source), crc32=crc32(source))
    if config.fault == Fault.INVALID_INPUT:
        return IntegrityResult(
            "HCCL_ERR_INVALID_ARG", FailureClass.NON_RETRYABLE, FailureReason.INVALID_ARGUMENT,
            metadata, 0, 0, 0, 0, 0, False, False, True, False, None, (),
        )
    if config.fault == Fault.NO_ALTERNATE_PATH:
        return IntegrityResult(
            "HCCL_ERR_TOPOLOGY", FailureClass.TERMINAL, FailureReason.NO_ALTERNATE_PATH,
            metadata, 0, 0, 0, 0, 0, False, False, True, False, None, (),
        )

    retransmitted = 0
    ever_corruption = False
    ever_timeout = False
    trace: list[dict] = []
    final_class = FailureClass.NONE
    final_reason = FailureReason.NONE
    final_code = "HCCL_SUCCESS"
    output: bytes | None = None
    start_tick = deadline_tick = completion_tick = 0
    sequence_valid = True
    for attempt in range(config.max_retries + 1):
        applies = config.fault != Fault.NONE and attempt <= config.fault_until_attempt
        destination = bytearray(source)
        expected_crc = metadata.crc32
        start_tick = attempt * (1 + config.retry_backoff_ticks)
        deadline_tick = start_tick + config.logical_timeout_ticks
        completion_tick = start_tick + 1
        sequence_valid = True
        final_class = FailureClass.NONE
        final_reason = FailureReason.NONE
        final_code = "HCCL_SUCCESS"

        if applies and config.fault == Fault.BIT_FLIP and destination:
            destination[config.corruption_offset % len(destination)] ^= 0x01
        elif applies and config.fault == Fault.BYTE_FLIP and destination:
            destination[config.corruption_offset % len(destination)] ^= 0xFF
        elif applies and config.fault == Fault.CRC_TAMPER:
            expected_crc ^= 1
        elif applies and config.fault == Fault.LOGICAL_TIMEOUT:
            completion_tick = deadline_tick + 1
        elif applies and config.fault == Fault.TRANSIENT_TRANSFER:
            final_code = "HCCL_ERR_COMM_FAILURE"
            final_class = FailureClass.RETRYABLE
            final_reason = FailureReason.TRANSIENT_TRANSFER_FAILURE
        elif applies and config.fault in {Fault.DUPLICATE_SEQUENCE, Fault.MISSING_CHUNK, Fault.REORDERED_SEQUENCE}:
            sequence_valid = False
            final_code = "HCCL_ERR_COMM_FAILURE"
            final_class = FailureClass.TERMINAL
            final_reason = {
                Fault.DUPLICATE_SEQUENCE: FailureReason.DUPLICATE_SEQUENCE,
                Fault.MISSING_CHUNK: FailureReason.MISSING_CHUNK,
                Fault.REORDERED_SEQUENCE: FailureReason.REORDERED_SEQUENCE,
            }[config.fault]

        if final_class != FailureClass.TERMINAL:
            if applies and config.fault == Fault.TRANSIENT_TRANSFER:
                pass
            elif completion_tick > deadline_tick:
                ever_timeout = True
                final_code = "HCCL_ERR_TIMEOUT"
                final_class = FailureClass.RETRYABLE
                final_reason = FailureReason.LOGICAL_TIMEOUT
            elif crc32(destination) != expected_crc:
                ever_corruption = True
                final_code = "HCCL_ERR_CRC_MISMATCH"
                final_class = FailureClass.RETRYABLE
                final_reason = FailureReason.CRC_MISMATCH
            else:
                output = bytes(destination)
                trace.append({
                    "attempt": attempt,
                    "classification": FailureClass.NONE.value,
                    "failure_reason": FailureReason.NONE.value,
                    "start_tick": start_tick,
                    "deadline_tick": deadline_tick,
                    "completion_tick": completion_tick,
                    "crc32": metadata.crc32,
                })
                return IntegrityResult(
                    "HCCL_SUCCESS", FailureClass.NONE, FailureReason.NONE,
                    dataclasses.replace(metadata, attempt=attempt), attempt + 1,
                    retransmitted, start_tick, deadline_tick, completion_tick,
                    ever_timeout, ever_corruption, True, attempt > 0, output, tuple(trace),
                )

        trace.append({
            "attempt": attempt,
            "classification": final_class.value,
            "failure_reason": final_reason.value,
            "start_tick": start_tick,
            "deadline_tick": deadline_tick,
            "completion_tick": completion_tick,
            "crc32": metadata.crc32,
        })
        if final_class != FailureClass.RETRYABLE:
            break
        if attempt < config.max_retries:
            retransmitted += len(source)
            continue
        final_class = FailureClass.TERMINAL
        final_reason = FailureReason.RETRY_EXHAUSTED
        break

    return IntegrityResult(
        final_code, final_class, final_reason,
        dataclasses.replace(metadata, attempt=max(0, len(trace) - 1)), len(trace),
        retransmitted, start_tick, deadline_tick, completion_tick,
        ever_timeout, ever_corruption, sequence_valid, False, None, tuple(trace),
    )


def verify_chunked(
    source: bytes,
    *,
    chunk_bytes: int,
    transfer_id: int,
    config: IntegrityConfig = IntegrityConfig(),
) -> dict:
    if chunk_bytes <= 0:
        raise ValueError("chunk_bytes must be positive")
    chunks = []
    for chunk_id, offset in enumerate(range(0, max(1, len(source)), chunk_bytes)):
        payload = source[offset : offset + chunk_bytes]
        result = execute_transfer(
            payload,
            IntegrityMetadata(transfer_id, chunk_id, chunk_id),
            dataclasses.replace(config, expected_sequence_id=chunk_id, observed_sequence_id=chunk_id),
        )
        chunks.append(result)
        if result.result_code != "HCCL_SUCCESS":
            break
    return {
        "chunks": chunks,
        "passed": all(row.result_code == "HCCL_SUCCESS" for row in chunks),
        "peak_materialized_bytes": min(max(1, len(source)), chunk_bytes),
        "bounded": True,
    }


def attach_reliability_policy(
    schedule_v2: dict,
    config: IntegrityConfig = IntegrityConfig(),
) -> dict:
    """Attach versioned integrity identities and deterministic retry policy."""

    schedule = copy.deepcopy(schedule_v2)
    sequence = 0
    for phase in schedule["phases"]:
        for transfer in phase["transfers"]:
            transfer["integrity_metadata"] = {
                "transfer_id": transfer["transfer_id"],
                "sequence_id": sequence,
                "chunk_id": transfer["chunk_id"],
                "attempt": 0,
                "payload_length": transfer["length_bytes"],
                "crc32": None,
            }
            sequence += 1
    schedule["integrity_policy"] = {
        "checksum_type": "CRC32",
        "sequence_enabled": True,
        "chunk_id_enabled": True,
        "attempt_tracking": True,
        "verify_before_accept": True,
    }
    schedule["transport_policy"] = {
        "timeout_enabled": True,
        "logical_timeout_ticks": config.logical_timeout_ticks,
        "max_retries": config.max_retries,
        "retry_backoff_policy": "FIXED_LOGICAL_TICKS",
        "retryable_error_classes": [
            "CRC_MISMATCH",
            "LOGICAL_TIMEOUT",
            "TRANSIENT_TRANSFER_FAILURE",
        ],
        "terminal_error_classes": [
            "RETRY_EXHAUSTED",
            "NO_ALTERNATE_PATH",
            "UNRECOVERABLE_INTEGRITY_FAILURE",
        ],
    }
    schedule["schedule_hash"] = canonical_hash(schedule, omitted_keys=("schedule_hash",))
    validate_schedule_v2(schedule)
    return schedule
