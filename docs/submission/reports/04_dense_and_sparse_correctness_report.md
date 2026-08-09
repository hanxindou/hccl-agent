# Dense and Sparse Correctness Report

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `SIMULATED_ONLY + LOSSLESS_SPARSE_HOST_EXECUTED`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R04, G3-B2, G3-B3, G3-C`


## Purpose

分别报告 dense simulator correctness 与 lossless sparse host correctness，避免混合 validation identity。

## Scope

Dense 覆盖 AllReduce、AllGather、ReduceScatter，FP32/FP16/BF16，SUM/MAX/MIN，以及冻结 rank/message/topology matrix。Sparse 覆盖 detect → encode → collective → reconstruct → validate。

## Validation Identity

- Dense G3-B2 matrix：`SIMULATED_ONLY`。
- Sparse codec/collective：`LOSSLESS_SPARSE_HOST_EXECUTED`。
- logical large message：bounded/sampled or analytically accounted；不是等量物理 materialization。

## Source Evidence

- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/correctness_summary.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/sparse_correctness.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/sparse_c_python_parity.json`
- `tests/feature_completion/test_g3_b3_sparse.py`

## Methodology

Dense reference 检查 output hash/error 与 exact/sample identity。Sparse 对每 rank 不同 sparsity pattern、implicit zero、ordered index/value、dense fallback 与 reconstruction hash 进行验证。

## Results

G3-B2 frozen dense scenarios 全部正确=true <!-- metric:g3b2.correctness.all_scenarios_correct -->。Sparse support matrix 包含 primitive 数 3 <!-- metric:g3b3.sparse.supported_primitives_count -->、dtype 数 3 <!-- metric:g3b3.sparse.supported_dtypes_count -->、reduce-op 数 3 <!-- metric:g3b3.sparse.supported_reduce_ops_count -->；sparse benchmark correctness=true 的场景数为 20 <!-- metric:g3b3.sparse.benchmark_correct_case_count -->。

| Primitive | Sparse semantics |
|---|---|
| AllReduce | index union；SUM/MAX/MIN 对 implicit zero 保持明确语义 |
| AllGather | 保留 rank order 与 rank boundary |
| ReduceScatter | reduction 后按 owner segment 进行 local index remapping |

Coverage identity 使用 `EXECUTED`、`SAMPLED`、`ANALYTICALLY_ACCOUNTED`、`NOT_APPLICABLE`、`NOT_TESTED`，不把 sampled/streamed logical message 写成 full physical materialization。

## Interpretation

Sparse correctness 证明 codec/collective host semantics 与 reconstruction；不证明真实 sparse network speedup。

## Claim Boundaries

- FP16/BF16 global `<=1e-6` 在 UA-C-001 未确认前不是正式 claim。
- host exact/hash evidence 不是 real HCCL device correctness。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

运行 `python -m pytest -q tests/feature_completion/test_g3_b3_sparse.py`，或仅运行 report verifier 核对 frozen evidence。

## Artifact References

- `docs/submission/report_chart_data/correctness_coverage.json`
- `docs/submission/report_claim_ledger.json`
