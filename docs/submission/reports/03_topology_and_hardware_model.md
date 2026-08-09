# Topology and Hardware Model

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `SIMULATED_ONLY`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R03, G3-B2, G3-B3, G3-C`


## Purpose

说明 topology/hardware model 的输入来源、适用范围与 calibration 边界。

## Scope

覆盖 Full Mesh、Ring、Fat-Tree、Hierarchical、Heterogeneous、Asymmetric links、Dynamic topology 与 No-path。

## Validation Identity

`topology_source=SIMULATOR_CONFIG`，`hardware_calibrated=false`。HCCS、RoCE、PCIe 的 bandwidth、latency 与 fault probability 若来自配置，provenance 为 `PROJECT_CONFIG` 或 `EXPLICIT_ASSUMPTION`；派生结果为 `DERIVED_ANALYTICAL`。当前没有 `REAL_MEASUREMENT`。

## Source Evidence

- `topology/`、`hardware/`、`configs/submission/`
- `configs/optimization/g3_b2_benchmark_matrix.json`
- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/scale_summary.json`

## Methodology

Topology model 显式表示 node、link、group、capacity、latency 与 availability。Selector 只在通过 schedule invariants 的候选中进行成本比较；No-path 返回明确失败语义，而不是隐式 fallback。

## Results

| Topology | Modeled purpose | Provenance | Boundary |
|---|---|---|---|
| Full Mesh | dense-connectivity candidate | PROJECT_CONFIG | not discovered hardware |
| Ring | cyclic path and fixed-Ring baseline | PROJECT_CONFIG | not physical ring measurement |
| Fat-Tree/Hierarchical | group/uplink-aware schedule | PROJECT_CONFIG + DERIVED_ANALYTICAL | no fabric counter |
| Heterogeneous/Asymmetric | unequal link cost and failure paths | EXPLICIT_ASSUMPTION | no live topology probe |
| Dynamic/No-path | replan and expected failure semantics | SIMULATED_ONLY | no hardware failover timing |

## Interpretation

Topology-aware selection 说明模型如何响应结构差异；它不等同于自动检测真实大规模集群拓扑。

## Claim Boundaries

- logical rank count 不是设备数量。
- configured link rate 不是 HCCS/RoCE/PCIe 实测带宽。
- expected no-path failure 是正确语义，不是硬件 reliability 验收。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

使用 simulator config 与固定 seed 进行 replay；G3-C 不重新 benchmark。

## Artifact References

- `configs/submission`
- `docs/submission/reports/08_simulator_user_manual.md`
