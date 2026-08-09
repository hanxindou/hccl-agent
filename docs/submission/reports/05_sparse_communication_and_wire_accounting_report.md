# Sparse Communication and Wire Accounting Report

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `LOSSLESS_SPARSE_HOST_EXECUTED + SIMULATED_ONLY`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R05, G3-B2, G3-B3, G3-C`


## Purpose

正式说明 lossless sparsity-aware payload transform、byte accounting、break-even 与 dense fallback。

## Scope

该能力不是 Top-K、lossy gradient sparsification 或 quantization。Codec 使用 canonical ordered index/value representation、index width、metadata 与 reconstruction hash。

## Validation Identity

Codec 与 reconstruction 为 host-executed；break-even 和 wire cost 是模型结果。`modeled_wire_bytes != physically measured NIC bytes`。

## Source Evidence

- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/sparse_benchmark.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/sparse_break_even.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/dense_fallback_audit.json`
- `feature_completion/sparse.py`、`hcccl/src/internal/sparse_codec.c`

## Methodology

Selector 比较 dense total cost 与 sparse total cost；sparse cost 包括 detection、index、value、metadata、encode/decode equivalent cost。它不是单一 sparsity threshold。

## Results

### Modeled break-even

| DType | Logical bytes | Modeled break-even sparsity |
|---|---:|---:|
| BF16 | 1048576 | 0.6800 <!-- metric:g3b3.sparse.break_even.bf16_1048576 --> |
| BF16 | 1073741824 | 0.6800 <!-- metric:g3b3.sparse.break_even.bf16_1073741824 --> |
| BF16 | 134217728 | 0.6800 <!-- metric:g3b3.sparse.break_even.bf16_134217728 --> |
| BF16 | 16777216 | 0.6800 <!-- metric:g3b3.sparse.break_even.bf16_16777216 --> |
| BF16 | 65536 | 0.5200 <!-- metric:g3b3.sparse.break_even.bf16_65536 --> |
| FP16 | 1048576 | 0.6800 <!-- metric:g3b3.sparse.break_even.fp16_1048576 --> |
| FP16 | 1073741824 | 0.6800 <!-- metric:g3b3.sparse.break_even.fp16_1073741824 --> |
| FP16 | 134217728 | 0.6800 <!-- metric:g3b3.sparse.break_even.fp16_134217728 --> |
| FP16 | 16777216 | 0.6800 <!-- metric:g3b3.sparse.break_even.fp16_16777216 --> |
| FP16 | 65536 | 0.5200 <!-- metric:g3b3.sparse.break_even.fp16_65536 --> |
| FP32 | 1048576 | 0.5100 <!-- metric:g3b3.sparse.break_even.fp32_1048576 --> |
| FP32 | 1073741824 | 0.5100 <!-- metric:g3b3.sparse.break_even.fp32_1073741824 --> |
| FP32 | 134217728 | 0.5100 <!-- metric:g3b3.sparse.break_even.fp32_134217728 --> |
| FP32 | 16777216 | 0.5100 <!-- metric:g3b3.sparse.break_even.fp32_16777216 --> |
| FP32 | 65536 | 0.3500 <!-- metric:g3b3.sparse.break_even.fp32_65536 --> |

### Byte identities

`logical_bytes` 是 dense logical payload；`value_bytes + index_bytes + metadata_bytes = modeled_wire_bytes`。`compression_ratio` 与 `wire_reduction_percent` 分开定义；90% sparsity 不等于 90% wire reduction。

Dense fallback audit 保留 11 <!-- metric:g3b3.sparse.dense_fallback_case_count --> 个不利场景。Sparse chart-data 同时包含 selected sparse 与 dense fallback rows，不只呈现 wins。

## Interpretation

当前模型在不同 dtype/message size 上给出不同 break-even。结果只能说明 modeled payload/cost crossover；不能推导相同幅度的物理网络 byte reduction 或实机 acceleration。

## Claim Boundaries

- `modeled_wire_bytes` 不是 NIC counter。
- bounded sparse materialization 不是等量真实网络传输。
- host encode/decode time 不是 NPU kernel time。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

运行 `python -m tools.report_cli verify` 验证每个 sparse row 的 source pointer、SHA 与 chart derivation。

## Artifact References

- `docs/submission/report_chart_data/sparse_break_even.json`
- `docs/submission/report_chart_data/sparse_wire_bytes.json`
