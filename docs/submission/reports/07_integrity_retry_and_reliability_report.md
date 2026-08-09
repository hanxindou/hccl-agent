# Integrity, Retry and Reliability Report

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `540d530e2982403376a229e8c7767902820b3199`<br>
Evidence Snapshot: `G3-B2 99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483`; `G3-B3 45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754`<br>
Execution Identity: `HOST_INTEGRITY_VALIDATED + HOST_RETRY_VALIDATED + SIMULATED_ONLY`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `R07, G3-B2, G3-B3, G3-C`


## Purpose

把 host integrity、host retry 与 simulator reliability 分层报告。

## Scope

Layer 1：CRC32、sequence/chunk identity、corruption detection。Layer 2：logical timeout、bounded retry、attempt accounting、retry exhaustion、failure classification。Layer 3：link degradation/down、dynamic replan、no-path、logical long-running scenarios 与 backpressure model。

## Validation Identity

CRC 为 `HOST_INTEGRITY_VALIDATED`；timeout/retry 为 `HOST_RETRY_VALIDATED`；flow/backpressure 与 large-scale fault 为 `SIMULATED_ONLY`/`SIMULATED_BACKPRESSURE`。

## Source Evidence

- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/crc_audit.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/retry_audit.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/timeout_audit.json`
- `experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/flow_control_audit.json`
- `experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/reliability_summary.json`

## Methodology

CRC 在 accept 前验证 payload；retry policy 只对 retryable classes 重试并受 max attempts 约束。Invalid input/no-path 等 non-retryable/terminal 状态不盲目重试。Timeout 使用 deterministic logical ticks，无 wall-clock sleep。

## Results

CRC known-vector 数=4 <!-- metric:g3b3.integrity.crc_vector_count -->，C/Python parity=true <!-- metric:g3b3.integrity.crc_c_python_parity -->。Retry case 数=3 <!-- metric:g3b3.retry.case_count -->。Timeout recovery attempt count=2 <!-- metric:g3b3.retry.timeout_recovered_attempt_count -->，terminal attempt count=3 <!-- metric:g3b3.retry.timeout_terminal_attempt_count -->，wall-clock sleep=false <!-- metric:g3b3.retry.timeout_wall_clock_sleep -->。

| Case | Blocked producer events | Truth |
|---|---:|---|
| normal_load | 0 <!-- metric:g3b3.flow.normal_load.blocked_producer_events --> | SIMULATED_BACKPRESSURE |
| recovery | 1 <!-- metric:g3b3.flow.recovery.blocked_producer_events --> | SIMULATED_BACKPRESSURE |
| sustained_congestion | 15 <!-- metric:g3b3.flow.sustained_congestion.blocked_producer_events --> | SIMULATED_BACKPRESSURE |
| temporary_congestion | 2 <!-- metric:g3b3.flow.temporary_congestion.blocked_producer_events --> | SIMULATED_BACKPRESSURE |

`EXPECTED_NO_PATH_FAILURE` 是正确的 terminal semantics。历史 100ms/72h 若被引用，只能解释为 simulated recovery time 与 logical event-simulation duration。

## Interpretation

Host CRC/retry 验证软件语义；flow-control 验证模型中的 credit conservation、bounded inflight、producer blocking、eventual drain 与 no-deadlock。

## Claim Boundaries

- host CRC 不是 hardware/NIC/HCCL CRC。
- logical timeout/retry 不是 real transport retransmission。
- simulated backpressure 不是 NIC/HCCL backpressure。
- 没有真实 failover timing 或 72h stress。

## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

运行 feature-completion reliability tests，或用 report verifier 只读复核冻结 evidence。

## Artifact References

- `docs/submission/report_chart_data/crc_retry_cases.json`
- `docs/submission/report_chart_data/backpressure_behavior.json`
