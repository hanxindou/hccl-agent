# Simulator User Manual

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `SIMULATED_ONLY`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R08, G3-B2, G3-B3, G3-C`


## Purpose

提供 Final Feature Freeze 后的正式 simulator 使用入口。

## Scope

涵盖 prerequisites、layout、backend/config、topology/hardware、primitive/algorithm、Schedule IR、dense/sparse、fault/reliability、seed、replay、quick/full、evidence、SHA 与限制。

## Validation Identity

Simulator commands 运行 project host/simulator code；不会操作真实 NIC、ACL runtime 或 HCCL communicator。Direct compile/link source is not executed by simulator CLI.

## Source Evidence

- `tools/submission_cli/`、`simulator/`、`configs/submission/`
- `configs/feature_completion/`
- `docs/submission/reproduction_guide.md`

## Methodology

### Prerequisites and layout

使用仓库现有 Python 环境；C/C++ 构建需要 WSL/CMake toolchain。G3-C 不安装依赖。核心目录为 `algorithm/`、`simulator/`、`feature_completion/`、`configs/`、`tools/` 与 `experiments/`。

### Backend and config

```text
python -m tools.submission_cli check
python -m tools.submission_cli describe
```

默认 backend 是 CPU_SIM，fallback 为 NONE。Topology config 指定 simulator topology/source/rank；hardware profile 提供 project assumptions。

### Replay and acceptance

```text
python -m tools.submission_cli quick --topology-config configs/submission/full_mesh_8.json
python -m tools.submission_cli verify --stage dist/submission-staging
```

`quick` 是 host/simulator acceptance；`full` 会执行 frozen host build/regression/staging，不代表 device acceptance。G3-C 本身不重跑 performance benchmark。

### Sparse mode

Data profile 提供 sparsity pattern；selector 比较 dense/sparse modeled cost，可能选择 dense fallback。输出区分 logical/value/index/metadata/modeled wire bytes。

### Reliability mode

Corruption、logical timeout、retry 与 flow-control tests 是 host/model tests，不会注入真实 NIC fault。

### Evidence and SHA

```text
certutil -hashfile <evidence>\SHA256SUMS SHA256
python -m tools.report_cli verify
```

## Results

Report CLI 的 `build` 只读取 frozen evidence；`verify` 检查 source SHA、JSON pointer、rounding、truth、claims、links 与 chart derivation；`describe` 是 read-only。

## Interpretation

Simulator 适合确定性 replay、schedule/cost comparison 与 failure semantics；不等同真实通信 fabric。

## Claim Boundaries

- logical rank/message 不等同 physical device/transfer。
- simulator bandwidth/latency 不是 measured hardware counters。
- Direct artifact 不由 simulator CLI 执行。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

按上述命令复现；不得把输出升级为 REAL_DEVICE evidence。

## Artifact References

- `docs/submission/report_data_ledger.json`
- `docs/submission/reports/report_source_index.md`
