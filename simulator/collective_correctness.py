"""Simulator-only collective correctness acceptance primitives.

This module deliberately has no dependency on the direct adapter, ACL, HCCL,
or the analytical performance simulator.  The simulator path and its host
reference use separate traversal code so their numerical comparison is a real
data-semantic check rather than a shape-only assertion.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import struct
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


DTYPE_BYTES = {"FP32": 4, "FP16": 2, "BF16": 2, "INT32": 4}
REDUCE_OPS = {"SUM", "MAX", "MIN"}
TOPOLOGIES = ("FULL_MESH", "RING", "FAT_TREE", "HETEROGENEOUS")
MAX_MATERIALIZED_ELEMENTS = 32
MAX_LOGICAL_ELEMENTS = 2**63 - 1
HOST_REFERENCE_REVISION = "independent canonical traversal v1"
STRESS_TOLERANCES = {
    "FP32": {"absolute": 1e-6, "relative": 1e-6},
    "FP16": {"absolute": 1e-3, "relative": 1e-3},
    "BF16": {"absolute": 1e-2, "relative": 1e-2},
    "INT32": {"absolute": 0.0, "relative": 0.0},
}


@dataclass(frozen=True)
class Case:
    primitive: str
    dtype: str
    op: str | None
    ranks: int
    topology: str
    message_label: str
    logical_message_bytes: int
    seed: int


def _fp32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _fp16(value: float) -> float:
    return struct.unpack("<e", struct.pack("<e", float(value)))[0]


def _bf16(value: float) -> float:
    bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
    exponent = bits & 0x7F800000
    mantissa = bits & 0x007FFFFF
    if exponent == 0x7F800000 and mantissa:
        return struct.unpack("<f", struct.pack("<I", bits | 0x00400000))[0]
    rounded = (bits + 0x7FFF + ((bits >> 16) & 1)) & 0xFFFFFFFF
    return struct.unpack("<f", struct.pack("<I", (rounded >> 16) << 16))[0]


def quantize(value: float | int, dtype: str) -> float | int:
    if dtype == "INT32":
        integer = int(value)
        if integer < -(2**31) or integer > 2**31 - 1:
            raise OverflowError("INT32 input is out of range")
        return integer
    if dtype == "FP32":
        return _fp32(float(value))
    if dtype == "FP16":
        return _fp16(float(value))
    if dtype == "BF16":
        return _bf16(float(value))
    raise ValueError(f"unsupported dtype: {dtype}")


def _reduce(values: Iterable[float | int], op: str, dtype: str) -> float | int:
    items = list(values)
    if not items or op not in REDUCE_OPS:
        raise ValueError("reduce requires values and a supported op")
    if op == "MAX":
        return quantize(max(items), dtype)
    if op == "MIN":
        return quantize(min(items), dtype)
    total: float | int = 0
    for value in items:
        total = quantize(total + value, dtype)
    return total


def _validate_rank_matrix(matrix: list[list[float | int]], ranks: int, count: int) -> None:
    if ranks <= 1 or len(matrix) != ranks or count <= 0 or any(len(row) != count for row in matrix):
        raise ValueError("rank matrix shape is invalid")


def validate_rank_ids(rank_ids: Sequence[int], rank_size: int) -> None:
    """Require one ascending, unique input for every rank in the collective."""
    if rank_size <= 1 or list(rank_ids) != list(range(rank_size)):
        raise ValueError("rank ids must be unique, complete, and ascending")


def _checked_product(left: int, right: int) -> int:
    if left < 0 or right < 0 or (right and left > MAX_LOGICAL_ELEMENTS // right):
        raise OverflowError("collective element count overflows logical contract")
    return left * right


def host_allreduce(send: list[list[float | int]], op: str, dtype: str) -> list[list[float | int]]:
    """Independent reference: transpose by element then reduce canonical ranks."""
    ranks, count = len(send), len(send[0]) if send else 0
    _validate_rank_matrix(send, ranks, count)
    reduced = [_reduce((send[rank][element] for rank in range(ranks)), op, dtype) for element in range(count)]
    return [reduced.copy() for _ in range(ranks)]


def host_allgather(send: list[list[float | int]], dtype: str) -> list[list[float | int]]:
    ranks, count = len(send), len(send[0]) if send else 0
    _validate_rank_matrix(send, ranks, count)
    canonical = [quantize(value, dtype) for rank in range(ranks) for value in send[rank]]
    return [canonical.copy() for _ in range(ranks)]


def host_reducescatter(send: list[list[float | int]], op: str, dtype: str) -> list[list[float | int]]:
    ranks, total = len(send), len(send[0]) if send else 0
    if ranks <= 1 or total == 0 or total % ranks or any(len(row) != total for row in send):
        raise ValueError("reducescatter matrix shape is invalid")
    recv_count = total // ranks
    flat = [_reduce((send[src][index] for src in range(ranks)), op, dtype) for index in range(total)]
    return [flat[rank * recv_count:(rank + 1) * recv_count] for rank in range(ranks)]


def simulate_allreduce(send: list[list[float | int]], op: str, dtype: str, topology: str) -> list[list[float | int]]:
    """Simulator algorithm: rank-local accumulators then topology-neutral broadcast."""
    if topology not in TOPOLOGIES:
        raise ValueError("unknown topology")
    ranks, count = len(send), len(send[0]) if send else 0
    _validate_rank_matrix(send, ranks, count)
    accumulators = [quantize(send[0][index], dtype) for index in range(count)]
    for source_rank in range(1, ranks):
        for index, accumulator in enumerate(accumulators):
            accumulators[index] = _reduce((accumulator, quantize(send[source_rank][index], dtype)), op, dtype)
    return [[quantize(value, dtype) for value in accumulators] for _destination_rank in range(ranks)]


def simulate_allgather(send: list[list[float | int]], dtype: str, topology: str) -> list[list[float | int]]:
    if topology not in TOPOLOGIES:
        raise ValueError("unknown topology")
    ranks, count = len(send), len(send[0]) if send else 0
    _validate_rank_matrix(send, ranks, count)
    outputs: list[list[float | int]] = []
    for _destination_rank in range(ranks):
        gathered: list[float | int] = []
        for source_rank in range(ranks):
            gathered.extend(quantize(send[source_rank][index], dtype) for index in range(count))
        outputs.append(gathered)
    return outputs


def simulate_reducescatter(send: list[list[float | int]], op: str, dtype: str, topology: str) -> list[list[float | int]]:
    if topology not in TOPOLOGIES:
        raise ValueError("unknown topology")
    ranks, total = len(send), len(send[0]) if send else 0
    if ranks <= 1 or total == 0 or total % ranks or any(len(row) != total for row in send):
        raise ValueError("reducescatter matrix shape is invalid")
    recv_count = total // ranks
    outputs: list[list[float | int]] = [[] for _ in range(ranks)]
    for destination_rank in range(ranks):
        for element in range(recv_count):
            global_index = destination_rank * recv_count + element
            outputs[destination_rank].append(_reduce((quantize(send[source_rank][global_index], dtype) for source_rank in range(ranks)), op, dtype))
    return outputs


def _logical_count(case: Case) -> int:
    if case.logical_message_bytes <= 0:
        raise ValueError("logical message bytes must be positive")
    bytes_per_element = DTYPE_BYTES[case.dtype]
    count = max(1, case.logical_message_bytes // bytes_per_element)
    if count > MAX_LOGICAL_ELEMENTS:
        raise OverflowError("logical message element count overflows contract")
    return count


def _validate_case_contract(case: Case) -> None:
    if case.primitive not in {"AllReduce", "AllGather", "ReduceScatter"}:
        raise ValueError("unknown primitive")
    if case.dtype not in DTYPE_BYTES or case.ranks <= 1 or case.topology not in TOPOLOGIES:
        raise ValueError("invalid case contract")
    if case.op not in ({None} if case.primitive == "AllGather" else REDUCE_OPS):
        raise ValueError("invalid case contract")
    count = _logical_count(case)
    input_count = _checked_product(count, case.ranks if case.primitive == "ReduceScatter" else 1)
    output_count = _checked_product(count, case.ranks if case.primitive == "AllGather" else 1)
    _checked_product(input_count, DTYPE_BYTES[case.dtype])
    _checked_product(output_count, DTYPE_BYTES[case.dtype])


def _materialized_count(case: Case) -> int:
    return min(_logical_count(case), MAX_MATERIALIZED_ELEMENTS)


def _values(case: Case, count: int, exact: bool) -> list[list[float | int]]:
    generator = random.Random(case.seed)
    multiplier = case.ranks if case.primitive == "ReduceScatter" else 1
    rows: list[list[float | int]] = []
    for rank in range(case.ranks):
        row = []
        for index in range(count * multiplier):
            if exact:
                value: float | int = ((rank * 3 + index * 5) % 7) - 3
            elif case.dtype == "INT32":
                value = generator.randint(-1000, 1000)
            else:
                value = generator.uniform(-0.5, 0.5)
            row.append(quantize(value, case.dtype))
        rows.append(row)
    return rows


def _flatten(value: list[list[float | int]]) -> list[float | int]:
    return [element for row in value for element in row]


def _metrics(actual: list[list[float | int]], expected: list[list[float | int]], dtype: str) -> dict[str, Any]:
    left, right = _flatten(actual), _flatten(expected)
    if len(left) != len(right):
        raise AssertionError("output element count differs")
    max_abs = max_rel = 0.0
    has_nan_inf = False
    for observed, reference in zip(left, right):
        if isinstance(observed, float) and (math.isnan(observed) or math.isinf(observed) or math.isnan(float(reference)) or math.isinf(float(reference))):
            has_nan_inf = True
            if observed != reference:
                raise AssertionError("NaN/Inf mismatch")
            continue
        difference = abs(float(observed) - float(reference))
        max_abs = max(max_abs, difference)
        max_rel = max(max_rel, difference / max(abs(float(reference)), 1e-30))
    exact = dtype == "INT32" or max_abs == 0.0
    payload = json.dumps(actual, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {"element_count": len(left), "max_abs_error": max_abs, "max_rel_error": max_rel,
            "has_nan_or_inf": has_nan_inf, "exact_match": exact,
            "output_hash": hashlib.sha256(payload).hexdigest()}


def run_case(case: Case, exact: bool) -> dict[str, Any]:
    _validate_case_contract(case)
    count = _materialized_count(case)
    send = _values(case, count, exact)
    if case.primitive == "AllReduce":
        actual, expected = simulate_allreduce(send, case.op or "", case.dtype, case.topology), host_allreduce(send, case.op or "", case.dtype)
    elif case.primitive == "AllGather":
        actual, expected = simulate_allgather(send, case.dtype, case.topology), host_allgather(send, case.dtype)
    else:
        actual, expected = simulate_reducescatter(send, case.op or "", case.dtype, case.topology), host_reducescatter(send, case.op or "", case.dtype)
    metrics = _metrics(actual, expected, case.dtype)
    if not metrics["exact_match"]:
        raise AssertionError("simulator result differs from independent host reference")
    logical_count = _logical_count(case)
    input_count = logical_count * (case.ranks if case.primitive == "ReduceScatter" else 1)
    output_count = logical_count * case.ranks if case.primitive == "AllGather" else logical_count
    materialized_input_count = count * (case.ranks if case.primitive == "ReduceScatter" else 1)
    materialized_output_count = count * case.ranks if case.primitive == "AllGather" else count
    bytes_per_element = DTYPE_BYTES[case.dtype]
    tolerance = STRESS_TOLERANCES[case.dtype]
    metrics["absolute_tolerance"] = 0.0 if exact else tolerance["absolute"]
    metrics["relative_tolerance"] = 0.0 if exact else tolerance["relative"]
    metrics["within_dtype_tolerance"] = (
        metrics["max_abs_error"] <= metrics["absolute_tolerance"]
        and metrics["max_rel_error"] <= metrics["relative_tolerance"]
    )
    metrics["competition_strict_1e6_pass"] = metrics["max_abs_error"] <= 1e-6
    return {"primitive": case.primitive, "dtype": case.dtype, "reduce_op": case.op,
            "rank_size": case.ranks, "rank_ids": list(range(case.ranks)), "topology": case.topology,
            "message_label": case.message_label, "seed": case.seed,
            "input_elements_per_rank": input_count, "output_elements_per_rank": output_count,
            "input_bytes_per_rank": input_count * bytes_per_element,
            "output_bytes_per_rank": output_count * bytes_per_element,
            "logical_message_bytes": case.logical_message_bytes,
            "materialized_input_bytes_per_rank": materialized_input_count * bytes_per_element,
            "materialized_output_bytes_per_rank": materialized_output_count * bytes_per_element,
            "materialized_message_bytes": count * bytes_per_element, "chunk_bytes": count * bytes_per_element,
            "chunk_count": max(1, (logical_count + count - 1) // count),
            "full_or_sampled_validation": "full" if logical_count == count else "sampled_streaming",
            "rank_order": "ascending rank id", "input_generation_rule": "seeded exact integers [-3, 3]" if exact else "seeded dtype-aware random stress values",
            "host_reference": HOST_REFERENCE_REVISION, "simulator_config": {"max_materialized_elements": MAX_MATERIALIZED_ELEMENTS, "topology_changes_values": False},
            "dataset": "exact" if exact else "random_stress", **metrics}


def representative_cases() -> list[Case]:
    sizes = (("1_element", 4), ("1KB", 1024), ("64KB", 64 * 1024), ("1MB", 1024 * 1024), ("16MB", 16 * 1024 * 1024), ("logical_1GB", 1024 * 1024 * 1024))
    cases: list[Case] = []
    seed = 20260804
    for primitive in ("AllReduce", "ReduceScatter"):
        index = 0
        for dtype in ("FP32", "FP16", "BF16", "INT32"):
            for op in ("SUM", "MAX", "MIN"):
                label, size = sizes[index % len(sizes)]
                cases.append(Case(primitive, dtype, op, (2, 4, 8, 16, 64)[index % 5], TOPOLOGIES[index % 4], label, size, seed + index))
                index += 1
    for index, dtype in enumerate(("FP32", "FP16", "BF16", "INT32")):
        label, size = sizes[index]
        cases.append(Case("AllGather", dtype, None, (2, 4, 8, 16)[index], TOPOLOGIES[index], label, size, seed + 100 + index))
    cases.append(Case("AllGather", "FP32", None, 64, "RING", "logical_1GB", 1024 * 1024 * 1024, seed + 200))
    return cases


def bf16_boundary_audit() -> dict[str, Any]:
    values = [0.0, -0.0, 2.0**-133, -2.0**-133, 3.38953139e38, -3.38953139e38]
    encoded = [quantize(value, "BF16") for value in values]
    return {"rounding": "round-to-nearest-even via FP32 upper 16 bits", "inputs": values,
            "outputs": encoded, "pass": all(math.isfinite(float(value)) for value in encoded)}
