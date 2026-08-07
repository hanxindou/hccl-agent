import dataclasses
import json
import random
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from algorithm.ring_schedule import generate_ring_schedule
from feature_completion.sparse import (
    DTYPE_BYTES,
    attach_payload_transform,
    decide_sparse,
    decode_bytes,
    decode_values,
    encode_bytes,
    encode_values,
    index_width,
    pack_values,
    sparse_collective,
    streaming_accounting,
    unpack_values,
)


def quantized(values, dtype):
    return unpack_values(pack_values(values, dtype), dtype)


@pytest.mark.parametrize("dtype", ["FP32", "FP16", "BF16"])
@pytest.mark.parametrize("ratio", [0.0, 0.25, 0.5, 0.75, 0.9, 1.0])
def test_codec_is_lossless_after_source_dtype_quantization(dtype, ratio):
    count = 256
    zero_count = round(count * ratio)
    values = [0.0] * zero_count + [float(index % 13 - 6) / 4.0 for index in range(count - zero_count)]
    random.Random(20260807).shuffle(values)
    payload = encode_values(values, dtype)
    assert decode_values(payload) == quantized(values, dtype)
    assert payload.nonzero_count == sum(value != 0.0 for value in quantized(values, dtype))
    assert list(payload.indices) == sorted(payload.indices)
    assert payload.wire_bytes == payload.index_bytes + payload.value_bytes + payload.metadata_bytes


def test_positive_and_negative_zero_are_implicit_but_nan_and_infinity_are_values():
    payload = encode_values([0.0, -0.0, float("inf"), float("-inf"), float("nan")], "FP32")
    assert payload.indices == (2, 3, 4)
    decoded = decode_values(payload)
    assert decoded[0] == 0.0 and decoded[1] == 0.0
    assert decoded[2] == float("inf") and decoded[3] == float("-inf")
    assert decoded[4] != decoded[4]


def test_empty_single_nonzero_and_index_width_boundaries():
    empty = encode_bytes(b"", "FP32")
    assert empty.logical_element_count == 0
    assert empty.nonzero_count == 0
    assert decode_bytes(empty) == b""
    single = encode_values([0.0] * 31 + [7.0], "FP32")
    assert single.indices == (31,)
    assert decode_values(single)[31] == 7.0
    assert index_width(65535) == 2
    assert index_width(65536) == 4
    assert index_width(4294967296) == 8


def test_duplicate_unordered_and_out_of_range_indices_are_rejected():
    payload = encode_values([0.0, 1.0, 0.0, 2.0], "FP32")
    duplicate = dataclasses.replace(payload, indices=(1, 1))
    unordered = dataclasses.replace(payload, indices=(3, 1))
    out_of_range = dataclasses.replace(payload, indices=(1, 4))
    for invalid in (duplicate, unordered, out_of_range):
        with pytest.raises(ValueError, match="ordered|range"):
            decode_bytes(invalid)


def test_cost_based_eligibility_and_explicit_dense_fallback():
    dense = encode_values([float(index + 1) for index in range(256)], "FP32")
    sparse = encode_values([1.0] + [0.0] * 255, "FP32")
    dense_decision = decide_sparse(dense)
    sparse_decision = decide_sparse(sparse)
    assert dense_decision.selected_mode == "DENSE"
    assert dense_decision.fallback_reason == "LOW_SPARSITY"
    assert sparse_decision.selected_mode == "SPARSE_INDEX_VALUE"
    assert sparse_decision.estimated_sparse_total_cost < sparse_decision.estimated_dense_total_cost
    memory_fallback = decide_sparse(sparse, memory_limit_bytes=1)
    assert memory_fallback.selected_mode == "DENSE"
    assert memory_fallback.fallback_reason == "MEMORY_LIMIT"


def test_schedule_ir_v2_records_sparse_and_dense_decisions():
    v1 = generate_ring_schedule("AllReduce", 4, 4096)
    sparse_payload = encode_values([1.0] + [0.0] * 1023, "FP32")
    sparse_schedule = attach_payload_transform(v1, sparse_payload, decide_sparse(sparse_payload))
    assert sparse_schedule["schema_version"] == "g3-b3-schedule-ir-v2"
    assert sparse_schedule["payload_transform"]["mode"] == "SPARSE_INDEX_VALUE"
    assert sparse_schedule["payload_transform"]["fallback_reason"] is None

    dense_payload = encode_values([float(index + 1) for index in range(1024)], "FP32")
    dense_schedule = attach_payload_transform(v1, dense_payload, decide_sparse(dense_payload))
    assert dense_schedule["payload_transform"]["mode"] == "DENSE"
    assert dense_schedule["payload_transform"]["fallback_reason"] == "LOW_SPARSITY"


def make_rank_inputs(ranks, count, sparsity, *, reduce_scatter=False):
    width = count * ranks if reduce_scatter else count
    rows = []
    for rank in range(ranks):
        values = []
        for index in range(width):
            marker = (index * 17 + rank * 11) % 100
            values.append(0.0 if marker < round(sparsity * 100) else float((rank + 1) * ((index % 7) - 3)))
        rows.append(values)
    return rows


def dense_reference(primitive, inputs, dtype, reduce_op):
    rows = [quantized(values, dtype) for values in inputs]
    ranks = len(rows)
    if primitive == "AllGather":
        gathered = [value for row in rows for value in row]
        return [gathered[:] for _ in rows]
    reduced = []
    for index in range(len(rows[0])):
        column = [row[index] for row in rows]
        value = sum(column) if reduce_op == "SUM" else (max(column) if reduce_op == "MAX" else min(column))
        reduced.append(quantized([value], dtype)[0])
    if primitive == "AllReduce":
        return [reduced[:] for _ in rows]
    count = len(reduced) // ranks
    return [reduced[rank * count : (rank + 1) * count] for rank in range(ranks)]


@pytest.mark.parametrize("dtype", ["FP32", "FP16", "BF16"])
@pytest.mark.parametrize("reduce_op", ["SUM", "MAX", "MIN"])
@pytest.mark.parametrize("ranks", [2, 4, 8, 16])
def test_sparse_allreduce_union_semantics(dtype, reduce_op, ranks):
    inputs = make_rank_inputs(ranks, 32, 0.75)
    result = sparse_collective("AllReduce", inputs, dtype=dtype, reduce_op=reduce_op)
    assert result["outputs"] == dense_reference("AllReduce", inputs, dtype, reduce_op)
    assert result["correctness_gate"] is True


@pytest.mark.parametrize("dtype", ["FP32", "FP16", "BF16"])
@pytest.mark.parametrize("ranks", [2, 4, 8, 16])
def test_sparse_allgather_preserves_rank_order_and_boundaries(dtype, ranks):
    inputs = make_rank_inputs(ranks, 16, 0.9)
    result = sparse_collective("AllGather", inputs, dtype=dtype, reduce_op=None)
    assert result["outputs"] == dense_reference("AllGather", inputs, dtype, None)


@pytest.mark.parametrize("dtype", ["FP32", "FP16", "BF16"])
@pytest.mark.parametrize("reduce_op", ["SUM", "MAX", "MIN"])
@pytest.mark.parametrize("ranks", [2, 4, 8, 16])
def test_sparse_reducescatter_preserves_owner_and_segment_mapping(dtype, reduce_op, ranks):
    inputs = make_rank_inputs(ranks, 8, 0.75, reduce_scatter=True)
    result = sparse_collective("ReduceScatter", inputs, dtype=dtype, reduce_op=reduce_op)
    assert result["outputs"] == dense_reference("ReduceScatter", inputs, dtype, reduce_op)


def test_max_min_include_implicit_zero_for_negative_and_positive_inputs():
    inputs = [[-5.0, 0.0, 7.0], [0.0, -2.0, 0.0]]
    maximum = sparse_collective("AllReduce", inputs, dtype="FP32", reduce_op="MAX")
    minimum = sparse_collective("AllReduce", inputs, dtype="FP32", reduce_op="MIN")
    assert maximum["outputs"][0] == [0.0, 0.0, 7.0]
    assert minimum["outputs"][0] == [-5.0, -2.0, 0.0]


def test_representative_64_rank_case_is_deterministic():
    inputs = make_rank_inputs(64, 4, 0.9)
    first = sparse_collective("AllReduce", inputs, dtype="FP32", reduce_op="SUM")
    second = sparse_collective("AllReduce", inputs, dtype="FP32", reduce_op="SUM")
    assert first["outputs"] == second["outputs"]
    assert [dataclasses.asdict(row) for row in first["decisions"]] == [dataclasses.asdict(row) for row in second["decisions"]]


def test_logical_one_gib_accounting_is_bounded_without_tensor_materialization():
    logical_elements = 1024**3 // DTYPE_BYTES["FP32"]
    accounting = streaming_accounting(
        logical_elements,
        logical_elements // 10,
        "FP32",
        chunk_elements=1024 * 1024,
    )
    assert accounting["logical_bytes"] == 1024**3
    assert accounting["full_logical_tensor_materialized"] is False
    assert accounting["peak_materialized_bytes"] < 64 * 1024 * 1024
    assert accounting["wire_bytes"] < accounting["logical_bytes"]


def test_frozen_profiles_remain_available_to_sparse_tests():
    profiles = json.loads((ROOT / "configs/feature_completion/g3_b3_data_profiles.json").read_text(encoding="utf-8"))
    assert {row["profile_id"] for row in profiles["profiles"]} == {"S00", "S25", "S50", "S75", "S90", "S100"}
