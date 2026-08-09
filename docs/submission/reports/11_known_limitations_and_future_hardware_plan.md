# Known Limitations and Future Hardware Plan

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `REAL_DEVICE_NOT_EXECUTED`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R11, G3-B2, G3-B3, G3-C`


## Purpose

集中列出未解除限制，并定义未来 hardware acceptance，而不在 G3-C 执行。

## Scope

当前限制：no real Ascend NPU、ACL runtime、communicator、collective、official loader ABI、HCCS/RoCE/PCIe measurement、sparse physical bytes/speedup、hardware CRC/parity、transport retry、NIC/HCCL backpressure、msprof、BERT/LLaMA training、90% training scale、real failover timing、real 72h stress、zero-CPU verification、UB/HBM reuse verification。

## Validation Identity

上述均为 `REAL_DEVICE_NOT_EXECUTED` / `HARDWARE_BLOCKED`，不能由报告升级。

## Source Evidence

- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/result.json`
- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/claim_boundary_audit.json`
- `docs/submission/risk_register.json`

## Methodology

限制按 truth identity 与 hardware dependency 汇总。INT8=DEFERRED_BY_PRECISION_GATE <!-- metric:g3b3.gates.int8_quantization -->；PairWise=SKIPPED_BY_VALUE_GATE <!-- metric:g3b3.gates.pairwise -->。

## Results

### Future Hardware Acceptance Plan — NOT EXECUTED IN G3-C

1. Detect a supported Ascend environment and CANN version.
2. Verify official libraries and redistribution boundary.
3. Initialize runtime and select device.
4. Create context and stream.
5. Bootstrap communicator.
6. Allocate device buffers.
7. Validate AllReduce correctness.
8. Validate AllGather correctness.
9. Validate ReduceScatter correctness.
10. Cover FP32/FP16/BF16 and representative message sizes.
11. Discover topology and record provenance.
12. Run real performance benchmarks.
13. Measure sparse physical-wire behavior.
14. Run msprof and capture counters.
15. Validate fault/retry behavior where supported.
16. Run long-duration stress.
17. Audit cleanup, leaks, CPU intervention, and memory reuse.
18. Freeze a new REAL_DEVICE evidence family only after all gates pass.

## Interpretation

该计划是未来用户授权下的硬件验收步骤，不是当前完成声明。

## Claim Boundaries

- `HARDWARE_BLOCKED` 只用于缺失硬件/runtime 验收。
- 报告/ledger/verifier bug 必须是 FAIL 或 ENV_BLOCKED。
- G3-C 不重新开放 Final Feature Freeze。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

当前只运行 report verifier；hardware plan 标记为 NOT EXECUTED IN G3-C。

## Artifact References

- `docs/submission/g3_c_requirement_delta.json`
- `docs/submission/report_claim_ledger.json`
