# Native Plugin and ABI Appendix

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `CPU_EXECUTED`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R09, G3-B2, G3-B3, G3-C`


## Purpose

记录 Final Feature Freeze 后 CPU_SIM native artifact 的 ABI、ELF、dependency 与 reproducibility 状态。

## Scope

Artifact identity 为 `libhccl_plugin.so` / `CPU_SIM_REFERENCE_PLUGIN`。

## Validation Identity

这是 project CPU_SIM ABI；不等于 Direct control-plane/readiness ABI，也不等于 official HCCL plugin-loader ABI。

## Source Evidence

- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/native_elf_audit.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/reproducible_build.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/submission_regression.json`
- `hcccl/submission/native_plugin_abi_manifest.json`

## Methodology

冻结 audit 使用 ELF/file、SONAME、dynamic exports、NEEDED、double clean build、CTest 与 installed consumer compile。

## Results

- SONAME：`libhccl_plugin.so <!-- metric:g3b3.native.soname -->`。
- Artifact SHA256：`af91e76ac5dbb693ba7263330300acdbe89b5f2b1077a31fe1b48ba2e3631309 <!-- metric:g3b3.native.artifact_sha256 -->`。
- Export count：19 <!-- metric:g3b3.native.exported_symbol_count -->。
- Dependency count：1 <!-- metric:g3b3.native.dependency_count -->；official dependencies 为空。
- Reproducibility：`BIT_FOR_BIT_REPRODUCIBLE <!-- metric:g3b3.native.reproducible_build_status -->`。
- CTest passed=14 <!-- metric:g3b3.regression.ctest_passed -->，failed=0 <!-- metric:g3b3.regression.ctest_failed -->；focused unittest passed=93 <!-- metric:g3b3.regression.python_passed -->。

## Interpretation

结果证明 project-owned CPU_SIM native delivery 可重建并保持 ABI isolation；不能证明 official loader 接受该 export set。

## Claim Boundaries

- 不写 `official plugin ABI verified`。
- CPU_SIM libc-only dependency 不代表 Direct artifact 无官方 dependency。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

运行 submission CLI full 可重新构建 host artifact；G3-C 仅复用冻结结果，不重建性能 evidence。

## Artifact References

- `hcccl/submission/native_plugin_abi_manifest.json`
- `docs/submission/native_plugin_abi_decision.md`
