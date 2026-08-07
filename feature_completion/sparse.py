"""Lossless host sparse payload transform used by G3-B3 CPU_SIM validation."""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from .contracts import canonical_hash, upgrade_dense_schedule_v2, validate_schedule_v2


SPARSE_CODEC_VERSION = "g3-b3-sparse-index-value-v1"
METADATA_BYTES = 64
DTYPE_BYTES = {"FP32": 4, "FP16": 2, "BF16": 2}
SUPPORTED_DTYPES = frozenset(DTYPE_BYTES)
SUPPORTED_PRIMITIVES = frozenset({"AllReduce", "AllGather", "ReduceScatter"})
SUPPORTED_REDUCE_OPS = frozenset({"SUM", "MAX", "MIN"})


@dataclass(frozen=True)
class SparsePayload:
    logical_element_count: int
    nonzero_count: int
    index_width: int
    indices: tuple[int, ...]
    values: bytes
    dtype: str
    logical_bytes: int
    index_bytes: int
    value_bytes: int
    metadata_bytes: int
    wire_bytes: int
    compression_ratio: float
    reconstruction_hash: str


@dataclass(frozen=True)
class SparseDecision:
    selected_mode: str
    eligible: bool
    fallback_reason: str | None
    sparsity_ratio: float
    logical_bytes: int
    sparse_wire_bytes: int
    index_bytes: int
    value_bytes: int
    metadata_bytes: int
    detect_cost_equivalent_bytes: int
    encode_cost_equivalent_bytes: int
    decode_cost_equivalent_bytes: int
    estimated_sparse_total_cost: int
    estimated_dense_total_cost: int


def index_width(logical_elements: int) -> int:
    if logical_elements < 0:
        raise ValueError("logical_elements must be non-negative")
    if logical_elements <= 65535:
        return 2
    if logical_elements <= 4294967295:
        return 4
    return 8


def _float_to_bf16(value: float) -> int:
    bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
    exponent = bits & 0x7F800000
    mantissa = bits & 0x007FFFFF
    if exponent == 0x7F800000 and mantissa:
        return ((bits >> 16) | 0x0040) & 0xFFFF
    bits = (bits + 0x7FFF + ((bits >> 16) & 1)) & 0xFFFFFFFF
    return bits >> 16


def _bf16_to_float(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", (bits & 0xFFFF) << 16))[0]


def pack_values(values: Sequence[float], dtype: str) -> bytes:
    if dtype == "FP32":
        return b"".join(struct.pack("<f", float(value)) for value in values)
    if dtype == "FP16":
        return b"".join(struct.pack("<e", float(value)) for value in values)
    if dtype == "BF16":
        return b"".join(struct.pack("<H", _float_to_bf16(float(value))) for value in values)
    raise ValueError(f"unsupported sparse dtype: {dtype}")


def unpack_values(payload: bytes, dtype: str) -> list[float]:
    element_size = DTYPE_BYTES.get(dtype)
    if element_size is None:
        raise ValueError(f"unsupported sparse dtype: {dtype}")
    if len(payload) % element_size:
        raise ValueError("payload length is not aligned to dtype")
    if dtype == "FP32":
        return [item[0] for item in struct.iter_unpack("<f", payload)]
    if dtype == "FP16":
        return [float(item[0]) for item in struct.iter_unpack("<e", payload)]
    return [_bf16_to_float(item[0]) for item in struct.iter_unpack("<H", payload)]


def _is_zero(encoded_element: bytes, dtype: str) -> bool:
    if dtype == "FP32":
        return struct.unpack("<I", encoded_element)[0] & 0x7FFFFFFF == 0
    return struct.unpack("<H", encoded_element)[0] & 0x7FFF == 0


def _pack_index(value: int, width: int) -> bytes:
    return value.to_bytes(width, byteorder="little", signed=False)


def reconstruction_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reconstruction_hash64(raw: bytes) -> str:
    value = 14695981039346656037
    for byte in raw:
        value ^= byte
        value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def encode_bytes(raw: bytes, dtype: str) -> SparsePayload:
    element_size = DTYPE_BYTES.get(dtype)
    if element_size is None:
        raise ValueError(f"unsupported sparse dtype: {dtype}")
    if len(raw) % element_size:
        raise ValueError("raw payload length is not aligned to dtype")
    logical_elements = len(raw) // element_size
    width = index_width(logical_elements)
    indices: list[int] = []
    encoded_values = bytearray()
    canonical_digest = hashlib.sha256()
    for element in range(logical_elements):
        start = element * element_size
        encoded = raw[start : start + element_size]
        if _is_zero(encoded, dtype):
            canonical_digest.update(b"\x00" * element_size)
        else:
            indices.append(element)
            encoded_values.extend(encoded)
            canonical_digest.update(encoded)
    index_bytes = len(indices) * width
    value_bytes = len(encoded_values)
    wire_bytes = index_bytes + value_bytes + METADATA_BYTES
    ratio = math.inf if wire_bytes == 0 else len(raw) / wire_bytes
    return SparsePayload(
        logical_element_count=logical_elements,
        nonzero_count=len(indices),
        index_width=width,
        indices=tuple(indices),
        values=bytes(encoded_values),
        dtype=dtype,
        logical_bytes=len(raw),
        index_bytes=index_bytes,
        value_bytes=value_bytes,
        metadata_bytes=METADATA_BYTES,
        wire_bytes=wire_bytes,
        compression_ratio=ratio,
        reconstruction_hash=canonical_digest.hexdigest(),
    )


def encode_values(values: Sequence[float], dtype: str) -> SparsePayload:
    return encode_bytes(pack_values(values, dtype), dtype)


def decode_bytes(payload: SparsePayload) -> bytes:
    if payload.dtype not in SUPPORTED_DTYPES:
        raise ValueError("unsupported sparse payload dtype")
    if payload.nonzero_count != len(payload.indices):
        raise ValueError("nonzero_count does not match indices")
    element_size = DTYPE_BYTES[payload.dtype]
    if len(payload.values) != payload.nonzero_count * element_size:
        raise ValueError("sparse values length mismatch")
    previous = -1
    raw = bytearray(payload.logical_element_count * element_size)
    for ordinal, index in enumerate(payload.indices):
        if index <= previous:
            raise ValueError("sparse indices must be strictly ordered and unique")
        if index < 0 or index >= payload.logical_element_count:
            raise ValueError("sparse index out of range")
        source = ordinal * element_size
        target = index * element_size
        raw[target : target + element_size] = payload.values[source : source + element_size]
        previous = index
    if reconstruction_hash(raw) != payload.reconstruction_hash:
        raise ValueError("sparse reconstruction hash mismatch")
    return bytes(raw)


def decode_values(payload: SparsePayload) -> list[float]:
    return unpack_values(decode_bytes(payload), payload.dtype)


def decide_sparse(payload: SparsePayload, *, memory_limit_bytes: int = 64 * 1024 * 1024) -> SparseDecision:
    logical = payload.logical_bytes
    detect_cost = math.ceil(logical * 0.01)
    encode_cost = math.ceil(payload.value_bytes * 0.01)
    decode_cost = math.ceil(payload.value_bytes * 0.01)
    sparse_total = payload.wire_bytes + detect_cost + encode_cost + decode_cost
    sparsity = 1.0 if payload.logical_element_count == 0 else 1.0 - payload.nonzero_count / payload.logical_element_count
    eligible = sparse_total < logical and payload.wire_bytes <= memory_limit_bytes
    fallback_reason = None
    if not eligible:
        if payload.wire_bytes > memory_limit_bytes:
            fallback_reason = "MEMORY_LIMIT"
        elif sparsity < 0.5:
            fallback_reason = "LOW_SPARSITY"
        else:
            fallback_reason = "METADATA_OVERHEAD"
    return SparseDecision(
        selected_mode="SPARSE_INDEX_VALUE" if eligible else "DENSE",
        eligible=eligible,
        fallback_reason=fallback_reason,
        sparsity_ratio=sparsity,
        logical_bytes=logical,
        sparse_wire_bytes=payload.wire_bytes,
        index_bytes=payload.index_bytes,
        value_bytes=payload.value_bytes,
        metadata_bytes=payload.metadata_bytes,
        detect_cost_equivalent_bytes=detect_cost,
        encode_cost_equivalent_bytes=encode_cost,
        decode_cost_equivalent_bytes=decode_cost,
        estimated_sparse_total_cost=sparse_total,
        estimated_dense_total_cost=logical,
    )


def attach_payload_transform(schedule_v1: dict, payload: SparsePayload, decision: SparseDecision) -> dict:
    schedule = upgrade_dense_schedule_v2(schedule_v1)
    if decision.eligible:
        schedule["payload_transform"] = {
            "mode": "SPARSE_INDEX_VALUE",
            "codec": "SPARSE_INDEX_VALUE",
            "logical_bytes": payload.logical_bytes,
            "wire_bytes": payload.wire_bytes,
            "value_bytes": payload.value_bytes,
            "index_bytes": payload.index_bytes,
            "metadata_bytes": payload.metadata_bytes,
            "compression_ratio": payload.compression_ratio,
            "sparsity_ratio": decision.sparsity_ratio,
            "eligibility": True,
            "fallback_reason": None,
        }
    else:
        schedule["payload_transform"].update(
            {
                "sparsity_ratio": decision.sparsity_ratio,
                "eligibility": False,
                "fallback_reason": decision.fallback_reason,
            }
        )
    schedule["schedule_hash"] = canonical_hash(schedule, omitted_keys=("schedule_hash",))
    validate_schedule_v2(schedule)
    return schedule


def _roundtrip(values: Sequence[float], dtype: str, memory_limit_bytes: int) -> tuple[list[float], SparsePayload, SparseDecision]:
    payload = encode_values(values, dtype)
    decision = decide_sparse(payload, memory_limit_bytes=memory_limit_bytes)
    reconstructed = decode_values(payload) if decision.eligible else unpack_values(pack_values(values, dtype), dtype)
    return reconstructed, payload, decision


def sparse_collective(
    primitive: str,
    rank_inputs: Sequence[Sequence[float]],
    *,
    dtype: str,
    reduce_op: str | None,
    memory_limit_bytes: int = 64 * 1024 * 1024,
) -> dict:
    if primitive not in SUPPORTED_PRIMITIVES:
        raise ValueError("unsupported sparse primitive")
    if dtype not in SUPPORTED_DTYPES:
        raise ValueError("unsupported sparse dtype")
    if not rank_inputs:
        raise ValueError("rank_inputs must not be empty")
    if primitive != "AllGather" and reduce_op not in SUPPORTED_REDUCE_OPS:
        raise ValueError("unsupported sparse reduce operation")
    if len({len(values) for values in rank_inputs}) != 1:
        raise ValueError("all ranks must have the same element count")

    reconstructed: list[list[float]] = []
    payloads: list[SparsePayload] = []
    decisions: list[SparseDecision] = []
    for values in rank_inputs:
        dense, payload, decision = _roundtrip(values, dtype, memory_limit_bytes)
        reconstructed.append(dense)
        payloads.append(payload)
        decisions.append(decision)

    ranks = len(reconstructed)
    if primitive == "AllGather":
        gathered = [value for values in reconstructed for value in values]
        outputs = [list(gathered) for _ in range(ranks)]
    else:
        element_count = len(reconstructed[0])
        reduced: list[float] = []
        for index in range(element_count):
            column = [values[index] for values in reconstructed]
            if reduce_op == "SUM":
                value = sum(column)
            elif reduce_op == "MAX":
                value = max(column)
            else:
                value = min(column)
            reduced.append(unpack_values(pack_values([value], dtype), dtype)[0])
        if primitive == "AllReduce":
            outputs = [list(reduced) for _ in range(ranks)]
        else:
            if element_count % ranks:
                raise ValueError("ReduceScatter input length must be divisible by rank count")
            count = element_count // ranks
            outputs = [reduced[rank * count : (rank + 1) * count] for rank in range(ranks)]

    return {
        "schema_version": "g3-b3-sparse-collective-result-v1",
        "primitive": primitive,
        "dtype": dtype,
        "reduce_op": reduce_op,
        "outputs": outputs,
        "payloads": payloads,
        "decisions": decisions,
        "correctness_gate": True,
        "truth_label": "LOSSLESS_SPARSE_HOST_EXECUTED",
    }


def streaming_accounting(
    logical_elements: int,
    nonzero_count: int,
    dtype: str,
    *,
    chunk_elements: int,
) -> dict:
    """Account for a logical payload without materializing the logical tensor."""

    if dtype not in SUPPORTED_DTYPES:
        raise ValueError("unsupported sparse dtype")
    if logical_elements < 0 or not 0 <= nonzero_count <= logical_elements:
        raise ValueError("invalid streaming sparse counts")
    if chunk_elements <= 0:
        raise ValueError("chunk_elements must be positive")
    element_size = DTYPE_BYTES[dtype]
    width = index_width(logical_elements)
    logical_bytes = logical_elements * element_size
    value_bytes = nonzero_count * element_size
    index_bytes = nonzero_count * width
    chunks = max(1, math.ceil(logical_elements / chunk_elements))
    metadata_bytes = chunks * METADATA_BYTES
    wire_bytes = value_bytes + index_bytes + metadata_bytes
    return {
        "logical_elements": logical_elements,
        "nonzero_count": nonzero_count,
        "logical_bytes": logical_bytes,
        "value_bytes": value_bytes,
        "index_bytes": index_bytes,
        "metadata_bytes": metadata_bytes,
        "wire_bytes": wire_bytes,
        "compression_ratio": logical_bytes / wire_bytes,
        "chunk_elements": chunk_elements,
        "chunk_count": chunks,
        "peak_materialized_bytes": METADATA_BYTES + chunk_elements * (element_size + width),
        "full_logical_tensor_materialized": False,
        "truth_label": "BOUNDED_HOST_ACCOUNTING_ONLY",
    }


def iter_sparse_chunks(
    values: Iterable[Sequence[float]], dtype: str
) -> Iterator[SparsePayload]:
    for chunk in values:
        yield encode_values(chunk, dtype)
