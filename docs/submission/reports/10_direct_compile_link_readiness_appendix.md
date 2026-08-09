# Direct Compile/Link Readiness Appendix

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `DIRECT_COMPILE_LINK_ONLY + REAL_DEVICE_NOT_EXECUTED`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R10, G3-B2, G3-B3, G3-C`


## Purpose

说明 Direct 从 signature/symbol/link readiness 演进到 actual official API call-expression source readiness 的边界。

## Scope

覆盖 runtime init、device、context、stream、memory、communicator、AllReduce/AllGather/ReduceScatter、sync 与 reverse cleanup；只描述冻结 source/audit 中存在的 lifecycle。

## Validation Identity

`DIRECT_COMPILE_LINK_ONLY`。`loaded=false`、`executed=false`、`real_device_api_executed=false`、`direct_hccl_api_call=false`、`runtime_api_calls=[]`。

## Source Evidence

- `hcccl/direct/src/hccl_direct_runtime_source.cpp`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/official_api_call_expression_audit.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/direct_compile_link_audit.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/cpu_sim_isolation_audit.json`

## Methodology

Target default OFF，要求 explicit frozen CANN root；构建独立 shared inspection artifact，不链接进 CPU_SIM，不注册为 CTest executable，不由 report/submission CLI 加载执行。Verifier 只检查 source call syntax、compile/link result 与 ELF dependencies。

## Results

冻结 audit 的 official call-expression count 为 17 <!-- metric:g3b3.direct.official_call_expression_count -->。API inventory：aclInit, aclrtSetDevice, aclrtCreateContext, aclrtCreateStream, aclrtMalloc, aclrtMemcpy, HcclCommInitClusterInfo, HcclAllReduce, HcclAllGather, HcclReduceScatter, aclrtSynchronizeStream, HcclCommDestroy, aclrtFree, aclrtDestroyStream, aclrtDestroyContext, aclrtResetDevice, aclFinalize。

Runtime execution=false <!-- metric:g3b3.direct.runtime_execution -->。Direct artifact 可以链接 official libraries；CPU_SIM `libhccl_plugin.so` 仍保持隔离。

## Interpretation

Direct Production Source Readiness: `COMPLETED`。Real-device Acceptance: `HARDWARE_BLOCKED`。

## Claim Boundaries

- actual call expression present != runtime API executed。
- symbol/declaration/static_assert/link dependency 分别弱于 actual call expression；actual call expression 仍弱于 reachable runtime execution。
- G3-C 不执行 source artifact。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

只运行 `python -m tools.report_cli verify`；不得加载 Direct artifact。

## Artifact References

- `docs/feature_completion/direct_compile_only_runtime_source.md`
- `docs/submission/report_claim_ledger.json`
