# SIMULATOR Performance and Scale Report

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `SIMULATED_ONLY`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R06, G3-B2, G3-B3, G3-C`


## Purpose

报告 G3-B2 frozen scheduling/performance evidence，并显式保持 simulator identity。

## Scope

包含 A0–A7、冻结 performance scenarios、p50/p95、decimal GB/s、algorithm/topology selection、logical scale 与 pipeline caveat。

## Validation Identity

全部性能数据为 `SIMULATED_ONLY`；`profiling_source=SIMULATOR_TRACE`，`msprof_executed=false`，`real_model_executed=false`。

## Source Evidence

- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/performance_summary.json`
- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/wins_ties_losses.json`
- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/ablation_summary.json`
- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/scale_summary.json`

## Methodology

Baseline 为 frozen fixed Ring。优化栈依次表达 legacy selector、Schedule IR、topology weighting、adaptive chunking、congestion-aware scheduling、dynamic replan 与 simulator-modeled pipeline overlap。

## Results

冻结 scenario 数为 18 <!-- metric:g3b2.performance.scenario_count -->。相对 fixed Ring：wins=18 <!-- metric:g3b2.outcomes.wins -->、ties=0 <!-- metric:g3b2.outcomes.ties -->、losses=0 <!-- metric:g3b2.outcomes.losses -->。Weighted simulated collective-time improvement 为 45.59% percent <!-- metric:g3b2.performance.weighted_geomean_improvement_percent -->；冻结 raw value 为 45.59283008。

Logical scale 中 P17 p50=615552.984 us <!-- metric:g3b2.scale.p17.p50 -->，P18 p50=343972.849 us <!-- metric:g3b2.scale.p18.p50 -->；二者均为 1024 logical ranks，不是 physical devices。

A7 的 `SIMULATED_PIPELINED_OVERLAP` 调整 exposed critical path；它不证明真实 stream overlap。

## Interpretation

这些数字比较冻结 simulator model 内的 scheduling stack 与 fixed Ring baseline。它们不是 real HCCL、NPU、training throughput 或 end-to-end model speedup。

## Claim Boundaries

- `TRAINING_LINEAR_SPEEDUP_NOT_VERIFIED=true`。
- 90% training scale target 未验证。
- BERT/LLaMA 未执行，`training_throughput=null`。
- logical large messages 使用 bounded materialization，不等同真实传输。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

G3-C 不重跑 benchmark；使用 `python -m tools.report_cli verify` 回溯 frozen G3-B2 SHA 与 ledger。

## Artifact References

- `docs/submission/report_chart_data/g3_b2_latency_comparison.json`
- `docs/submission/report_chart_data/g3_b2_ablation.json`
