"""Render deterministic Markdown reports and ledger-derived chart data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .evidence_reader import (
    CHART_ROOT, G3_B2_ROOT, G3_B3_ROOT, REPORT_INDEX, REPORT_ROOT, REQUIREMENT_DELTA,
    STALE_AUDIT, read_json, relative, write_json, write_text,
)
from .schemas import CHART_FILES, REPORT_FILES, USER_ACTIONS


REPORT_IDS = {
    "01_system_architecture_and_algorithm_design.md": "R01",
    "02_collective_schedule_ir_and_algorithm_evolution.md": "R02",
    "03_topology_and_hardware_model.md": "R03",
    "04_dense_and_sparse_correctness_report.md": "R04",
    "05_sparse_communication_and_wire_accounting_report.md": "R05",
    "06_simulator_performance_and_scale_report.md": "R06",
    "07_integrity_retry_and_reliability_report.md": "R07",
    "08_simulator_user_manual.md": "R08",
    "09_native_plugin_and_abi_appendix.md": "R09",
    "10_direct_compile_link_readiness_appendix.md": "R10",
    "11_known_limitations_and_future_hardware_plan.md": "R11",
}


def _index(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["metric_id"]: row for row in ledger["metrics"]}


def _metric(metrics: dict[str, dict[str, Any]], metric_id: str) -> str:
    row = metrics[metric_id]
    unit = "" if row["unit"] in {"string", "boolean", "count", "ratio", "scalar"} else f" {row['unit']}"
    return f"{row['display_value']}{unit} <!-- metric:{metric_id} -->"


def _header(title: str, report_id: str, truth: str, ledger: dict[str, Any]) -> str:
    snapshots = ledger["evidence_snapshots"]
    return f"""# {title}

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `{ledger['source_commit']}`<br>
Evidence Snapshot: `G3-B2 {snapshots['G3-B2']['sha256sums_sha256']}`; `G3-B3 {snapshots['G3-B3']['sha256sums_sha256']}`<br>
Execution Identity: `{truth}`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`<br>
Applicable Checkpoints: `{report_id}, G3-B2, G3-B3, G3-C`

"""


def _common_tail(reproduction: str, artifacts: list[str]) -> str:
    refs = "\n".join(f"- `{item}`" for item in artifacts)
    return f"""
## Known Limitations

本报告只使用冻结的 host、simulator 与 compile/link evidence。没有真实 Ascend NPU、ACL/HCCL runtime、communicator、collective、training 或 profiler 证据。

## Reproduction

{reproduction}

## Artifact References

{refs}
"""


def _report_01(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    support = [row for row in ledger["metrics"] if row["metric_group"] == "algorithm_support"]
    table = ["| Algorithm | Primitive | Status |", "|---|---|---|"]
    table.extend(f"| {row['algorithm']} | {row['primitive']} | {_metric(m, row['metric_id'])} |" for row in support)
    proposals = _metric(m, "g3b3.agent.proposal_records")
    evaluations = _metric(m, "g3b3.agent.evaluation_records")
    reflections = _metric(m, "g3b3.agent.reflection_records")
    return _header("System Architecture and Algorithm Design", "R01", "HISTORICAL_EVIDENCE + HOST_EXECUTED + SIMULATED_ONLY", ledger) + f"""
## Purpose

给出 Final Feature Freeze 后的总体架构、backend registry、三原语、算法族与 Agent decision loop。

## Scope

系统分为 Agent Control Plane、Schedule Layer、Topology Layer、Cost Model、Simulator、CPU_SIM、ASCEND_HCCL_VM、ASCEND_HCCL_DIRECT 与 Submission/Evidence Layer。`SIMULATOR_ACCEPTANCE` 是独立 validation track，不是第四个 backend。

```mermaid
flowchart LR
  A["Agent Control Plane"] --> S["Schedule IR v1/v2"]
  T["Topology + Hardware Config"] --> S
  C["Cost Model"] --> S
  S --> V["Simulator Acceptance"]
  S --> P["CPU_SIM Host Plugin"]
  S -. readiness .-> D["ASCEND_HCCL_DIRECT"]
  V --> E["Evidence + Report Ledgers"]
  P --> E
  D --> E
```

## Validation Identity

- `CPU_SIM`: project-owned host-executed reference plugin；default backend。
- `ASCEND_HCCL_VM`: official `hccl_test` subprocess contract；G3-C 不执行。
- `ASCEND_HCCL_DIRECT`: compile/link/readiness source；G3-C 不执行。
- `fallback=NONE`，不把 host 结果隐式升级为 device 结果。

## Source Evidence

- `agent/`、`algorithm/`、`topology/`、`cost_model/`、`simulator/`
- `{relative(G3_B2_ROOT / 'algorithm_support_matrix.json')}`
- `{relative(G3_B3_ROOT / 'agent_trace_inventory.json')}`

## Methodology

三原语为 AllReduce、AllGather、ReduceScatter。AllReduce 对同形输入执行 reduction 并向所有 rank 返回结果；AllGather 保留 rank 顺序与边界；ReduceScatter 先 reduction，再按 owner segment 分发。Broadcast 与 AlltoAll 不在正式支持 primitive 中。

## Results

### Algorithm support matrix

{chr(10).join(table)}

PairWise 状态为 `{m['g3b3.gates.pairwise']['value']}` <!-- metric:g3b3.gates.pairwise -->，因此不进入 implemented matrix。

### Complexity interpretation

| Family | Phase tendency | Latency sensitivity | Bandwidth sensitivity | Topology assumption | Rank/message notes |
|---|---|---|---|---|---|
| Ring | linear in rank count | higher for small messages | efficient streaming | cycle/path | broad rank support |
| Butterfly | logarithmic stages where supported | favorable | exchange-pattern dependent | power-of-two friendly | AllReduce/AllGather only |
| Mesh | low phase count on dense connectivity | favorable | link fan-out sensitive | full/near-full mesh | AllReduce/ReduceScatter |
| NHR | hierarchy-aware rounds | hierarchy dependent | cross-group sensitive | hierarchical groups | AllReduce only |
| Hierarchical/Fat-Tree | intra/inter-group phases | topology dependent | uplink sensitive | explicit groups/tree | AllReduce only |

这些是实现/IR 复杂度特征，不是实机效率测量。

### Agent decision loop

`input → candidate schedules → correctness hard gate → cost evaluation → selection → reflection → replanning`。冻结 trace 包含 proposal {proposals}、evaluation {evaluations}、reflection {reflections}。`development_agent=Codex`、`runtime_agent=hccl-agent`、`human_reviewer=user` 是不同身份。

## Interpretation

架构允许同一 Schedule/Agent 体系消费 dense、sparse、integrity 与 flow-control fields，但每条验证结果保留独立 truth identity。

## Claim Boundaries

- 不把 `SIMULATOR_ACCEPTANCE` 描述为 backend。
- 不把 PairWise 描述为已实现。
- 不把 Agent proposal/replay 描述成无人监督的真实设备调优。
""" + _common_tail("运行 `python -m tools.report_cli verify` 核对支持矩阵、claims 与引用。",
                       ["docs/submission/report_data_ledger.json", "docs/submission/report_claim_ledger.json"])


def _report_02(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    parity_count = _metric(m, "g3b2.parity.case_count")
    parity = _metric(m, "g3b2.parity.all_canonical_equal")
    schedule_hash = _metric(m, "g3b2.parity.representative_schedule_hash")
    return _header("Collective Schedule IR and Algorithm Evolution", "R02", "CPU_EXECUTED + HISTORICAL_EVIDENCE", ledger) + f"""
## Purpose

解释 G3-B2 Schedule IR v1 到 G3-B3 Schedule IR v2 的增量演化与历史兼容边界。

## Scope

IR v1 包含 phases、transfers、chunks、routes、dependencies、memory plan、failure policy 与 canonical schedule hash。IR v2 增加 payload transform、integrity policy、transport/retry policy、flow-control policy，以及 logical/wire accounting。

## Validation Identity

IR 生成与 parity 是 host/CPU evidence；基于 IR 的 latency 与 bandwidth 仍是 `SIMULATED_ONLY`。

## Source Evidence

- `algorithm/schedule_ir.py`、`hcccl/src/schedule_ir.c`
- `feature_completion/contracts.py`、`feature_completion/reliability.py`
- `{relative(G3_B2_ROOT / 'c_python_parity_audit.json')}`
- `{relative(G3_B3_ROOT / 'schedule_ir_v2_audit.json')}`

## Methodology

v2 通过复制并扩展 v1，不修改传入的 v1 document；canonical hash 排除 hash field 本身后按稳定 JSON 编码计算。v1 historical evidence remains immutable，v2 不重写 v1 history。

## Results

C/Python parity 覆盖 {parity_count} 个冻结 case，全部 canonical equal={parity}。代表性 schedule hash 为 `{schedule_hash}`。

```mermaid
flowchart TD
  V1["IR v1: phases/routes/memory/failure"] --> U["copy + versioned upgrade"]
  U --> P["payload_transform"]
  U --> I["integrity_policy"]
  U --> R["transport_policy"]
  U --> F["flow_control_policy"]
  P --> H["canonical v2 hash"]
  I --> H
  R --> H
  F --> H
```

代表性 schedule families 包括 Ring AllReduce、Butterfly、NHR、Hierarchical 与 sparse-aware v2 schedule；每个 schedule 必须先通过 invariant validation，再参与 selector/cost evaluation。

## Interpretation

IR v2 是 feature-completion contract，不是新的历史性能实验身份；G3-B2 performance 继续引用 v1 frozen evidence。

## Claim Boundaries

- canonical parity 证明序列化/语义一致性，不证明真实设备执行。
- sparse-aware schedule 的 modeled wire fields 不是物理 NIC counter。
""" + _common_tail("运行 `python -m tools.report_cli build` 后再运行 `python -m tools.report_cli verify`。",
                       ["configs/feature_completion/g3_b3_schedule_ir_v2_schema.json", "docs/submission/report_data_ledger.json"])


def _report_03(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    return _header("Topology and Hardware Model", "R03", "SIMULATED_ONLY", ledger) + f"""
## Purpose

说明 topology/hardware model 的输入来源、适用范围与 calibration 边界。

## Scope

覆盖 Full Mesh、Ring、Fat-Tree、Hierarchical、Heterogeneous、Asymmetric links、Dynamic topology 与 No-path。

## Validation Identity

`topology_source=SIMULATOR_CONFIG`，`hardware_calibrated=false`。HCCS、RoCE、PCIe 的 bandwidth、latency 与 fault probability 若来自配置，provenance 为 `PROJECT_CONFIG` 或 `EXPLICIT_ASSUMPTION`；派生结果为 `DERIVED_ANALYTICAL`。当前没有 `REAL_MEASUREMENT`。

## Source Evidence

- `topology/`、`hardware/`、`configs/submission/`
- `configs/optimization/g3_b2_benchmark_matrix.json`
- `{relative(G3_B2_ROOT / 'scale_summary.json')}`

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
""" + _common_tail("使用 simulator config 与固定 seed 进行 replay；G3-C 不重新 benchmark。",
                       ["configs/submission", "docs/submission/reports/08_simulator_user_manual.md"])


def _report_04(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    primitive_count = _metric(m, "g3b3.sparse.supported_primitives_count")
    dtype_count = _metric(m, "g3b3.sparse.supported_dtypes_count")
    op_count = _metric(m, "g3b3.sparse.supported_reduce_ops_count")
    return _header("Dense and Sparse Correctness Report", "R04", "SIMULATED_ONLY + LOSSLESS_SPARSE_HOST_EXECUTED", ledger) + f"""
## Purpose

分别报告 dense simulator correctness 与 lossless sparse host correctness，避免混合 validation identity。

## Scope

Dense 覆盖 AllReduce、AllGather、ReduceScatter，FP32/FP16/BF16，SUM/MAX/MIN，以及冻结 rank/message/topology matrix。Sparse 覆盖 detect → encode → collective → reconstruct → validate。

## Validation Identity

- Dense G3-B2 matrix：`SIMULATED_ONLY`。
- Sparse codec/collective：`LOSSLESS_SPARSE_HOST_EXECUTED`。
- logical large message：bounded/sampled or analytically accounted；不是等量物理 materialization。

## Source Evidence

- `{relative(G3_B2_ROOT / 'correctness_summary.json')}`
- `{relative(G3_B3_ROOT / 'sparse_correctness.json')}`
- `{relative(G3_B3_ROOT / 'sparse_c_python_parity.json')}`
- `tests/feature_completion/test_g3_b3_sparse.py`

## Methodology

Dense reference 检查 output hash/error 与 exact/sample identity。Sparse 对每 rank 不同 sparsity pattern、implicit zero、ordered index/value、dense fallback 与 reconstruction hash 进行验证。

## Results

G3-B2 frozen dense scenarios 全部正确={_metric(m, 'g3b2.correctness.all_scenarios_correct')}。Sparse support matrix 包含 primitive 数 {primitive_count}、dtype 数 {dtype_count}、reduce-op 数 {op_count}；sparse benchmark correctness=true 的场景数为 {_metric(m, 'g3b3.sparse.benchmark_correct_case_count')}。

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
""" + _common_tail("运行 `python -m pytest -q tests/feature_completion/test_g3_b3_sparse.py`，或仅运行 report verifier 核对 frozen evidence。",
                       ["docs/submission/report_chart_data/correctness_coverage.json", "docs/submission/report_claim_ledger.json"])


def _report_05(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    break_even = [row for row in ledger["metrics"] if row["metric_group"] == "sparse_break_even"]
    fallback = _metric(m, "g3b3.sparse.dense_fallback_case_count")
    table = ["| DType | Logical bytes | Modeled break-even sparsity |", "|---|---:|---:|"]
    table.extend(f"| {row['dtype']} | {row['logical_bytes']} | {_metric(m, row['metric_id'])} |" for row in break_even)
    return _header("Sparse Communication and Wire Accounting Report", "R05", "LOSSLESS_SPARSE_HOST_EXECUTED + SIMULATED_ONLY", ledger) + f"""
## Purpose

正式说明 lossless sparsity-aware payload transform、byte accounting、break-even 与 dense fallback。

## Scope

该能力不是 Top-K、lossy gradient sparsification 或 quantization。Codec 使用 canonical ordered index/value representation、index width、metadata 与 reconstruction hash。

## Validation Identity

Codec 与 reconstruction 为 host-executed；break-even 和 wire cost 是模型结果。`modeled_wire_bytes != physically measured NIC bytes`。

## Source Evidence

- `{relative(G3_B3_ROOT / 'sparse_benchmark.json')}`
- `{relative(G3_B3_ROOT / 'sparse_break_even.json')}`
- `{relative(G3_B3_ROOT / 'dense_fallback_audit.json')}`
- `feature_completion/sparse.py`、`hcccl/src/internal/sparse_codec.c`

## Methodology

Selector 比较 dense total cost 与 sparse total cost；sparse cost 包括 detection、index、value、metadata、encode/decode equivalent cost。它不是单一 sparsity threshold。

## Results

### Modeled break-even

{chr(10).join(table)}

### Byte identities

`logical_bytes` 是 dense logical payload；`value_bytes + index_bytes + metadata_bytes = modeled_wire_bytes`。`compression_ratio` 与 `wire_reduction_percent` 分开定义；90% sparsity 不等于 90% wire reduction。

Dense fallback audit 保留 {fallback} 个不利场景。Sparse chart-data 同时包含 selected sparse 与 dense fallback rows，不只呈现 wins。

## Interpretation

当前模型在不同 dtype/message size 上给出不同 break-even。结果只能说明 modeled payload/cost crossover；不能推导相同幅度的物理网络 byte reduction 或实机 acceleration。

## Claim Boundaries

- `modeled_wire_bytes` 不是 NIC counter。
- bounded sparse materialization 不是等量真实网络传输。
- host encode/decode time 不是 NPU kernel time。
""" + _common_tail("运行 `python -m tools.report_cli verify` 验证每个 sparse row 的 source pointer、SHA 与 chart derivation。",
                       ["docs/submission/report_chart_data/sparse_break_even.json", "docs/submission/report_chart_data/sparse_wire_bytes.json"])


def _report_06(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    return _header("SIMULATOR Performance and Scale Report", "R06", "SIMULATED_ONLY", ledger) + f"""
## Purpose

报告 G3-B2 frozen scheduling/performance evidence，并显式保持 simulator identity。

## Scope

包含 A0–A7、冻结 performance scenarios、p50/p95、decimal GB/s、algorithm/topology selection、logical scale 与 pipeline caveat。

## Validation Identity

全部性能数据为 `SIMULATED_ONLY`；`profiling_source=SIMULATOR_TRACE`，`msprof_executed=false`，`real_model_executed=false`。

## Source Evidence

- `{relative(G3_B2_ROOT / 'performance_summary.json')}`
- `{relative(G3_B2_ROOT / 'wins_ties_losses.json')}`
- `{relative(G3_B2_ROOT / 'ablation_summary.json')}`
- `{relative(G3_B2_ROOT / 'scale_summary.json')}`

## Methodology

Baseline 为 frozen fixed Ring。优化栈依次表达 legacy selector、Schedule IR、topology weighting、adaptive chunking、congestion-aware scheduling、dynamic replan 与 simulator-modeled pipeline overlap。

## Results

冻结 scenario 数为 {_metric(m, 'g3b2.performance.scenario_count')}。相对 fixed Ring：wins={_metric(m, 'g3b2.outcomes.wins')}、ties={_metric(m, 'g3b2.outcomes.ties')}、losses={_metric(m, 'g3b2.outcomes.losses')}。Weighted simulated collective-time improvement 为 {_metric(m, 'g3b2.performance.weighted_geomean_improvement_percent')}；冻结 raw value 为 {m['g3b2.performance.weighted_geomean_improvement_percent']['value']}。

Logical scale 中 P17 p50={_metric(m, 'g3b2.scale.p17.p50')}，P18 p50={_metric(m, 'g3b2.scale.p18.p50')}；二者均为 1024 logical ranks，不是 physical devices。

A7 的 `SIMULATED_PIPELINED_OVERLAP` 调整 exposed critical path；它不证明真实 stream overlap。

## Interpretation

这些数字比较冻结 simulator model 内的 scheduling stack 与 fixed Ring baseline。它们不是 real HCCL、NPU、training throughput 或 end-to-end model speedup。

## Claim Boundaries

- `TRAINING_LINEAR_SPEEDUP_NOT_VERIFIED=true`。
- 90% training scale target 未验证。
- BERT/LLaMA 未执行，`training_throughput=null`。
- logical large messages 使用 bounded materialization，不等同真实传输。
""" + _common_tail("G3-C 不重跑 benchmark；使用 `python -m tools.report_cli verify` 回溯 frozen G3-B2 SHA 与 ledger。",
                       ["docs/submission/report_chart_data/g3_b2_latency_comparison.json", "docs/submission/report_chart_data/g3_b2_ablation.json"])


def _report_07(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    flow = [row for row in ledger["metrics"] if row["metric_group"] == "backpressure" and row["metric_id"].endswith("blocked_producer_events")]
    flow_table = ["| Case | Blocked producer events | Truth |", "|---|---:|---|"]
    flow_table.extend(f"| {row['metric_id'].split('.')[2]} | {_metric(m, row['metric_id'])} | SIMULATED_BACKPRESSURE |" for row in flow)
    return _header("Integrity, Retry and Reliability Report", "R07", "HOST_INTEGRITY_VALIDATED + HOST_RETRY_VALIDATED + SIMULATED_ONLY", ledger) + f"""
## Purpose

把 host integrity、host retry 与 simulator reliability 分层报告。

## Scope

Layer 1：CRC32、sequence/chunk identity、corruption detection。Layer 2：logical timeout、bounded retry、attempt accounting、retry exhaustion、failure classification。Layer 3：link degradation/down、dynamic replan、no-path、logical long-running scenarios 与 backpressure model。

## Validation Identity

CRC 为 `HOST_INTEGRITY_VALIDATED`；timeout/retry 为 `HOST_RETRY_VALIDATED`；flow/backpressure 与 large-scale fault 为 `SIMULATED_ONLY`/`SIMULATED_BACKPRESSURE`。

## Source Evidence

- `{relative(G3_B3_ROOT / 'crc_audit.json')}`
- `{relative(G3_B3_ROOT / 'retry_audit.json')}`
- `{relative(G3_B3_ROOT / 'timeout_audit.json')}`
- `{relative(G3_B3_ROOT / 'flow_control_audit.json')}`
- `{relative(G3_B2_ROOT / 'reliability_summary.json')}`

## Methodology

CRC 在 accept 前验证 payload；retry policy 只对 retryable classes 重试并受 max attempts 约束。Invalid input/no-path 等 non-retryable/terminal 状态不盲目重试。Timeout 使用 deterministic logical ticks，无 wall-clock sleep。

## Results

CRC known-vector 数={_metric(m, 'g3b3.integrity.crc_vector_count')}，C/Python parity={_metric(m, 'g3b3.integrity.crc_c_python_parity')}。Retry case 数={_metric(m, 'g3b3.retry.case_count')}。Timeout recovery attempt count={_metric(m, 'g3b3.retry.timeout_recovered_attempt_count')}，terminal attempt count={_metric(m, 'g3b3.retry.timeout_terminal_attempt_count')}，wall-clock sleep={_metric(m, 'g3b3.retry.timeout_wall_clock_sleep')}。

{chr(10).join(flow_table)}

`EXPECTED_NO_PATH_FAILURE` 是正确的 terminal semantics。历史 100ms/72h 若被引用，只能解释为 simulated recovery time 与 logical event-simulation duration。

## Interpretation

Host CRC/retry 验证软件语义；flow-control 验证模型中的 credit conservation、bounded inflight、producer blocking、eventual drain 与 no-deadlock。

## Claim Boundaries

- host CRC 不是 hardware/NIC/HCCL CRC。
- logical timeout/retry 不是 real transport retransmission。
- simulated backpressure 不是 NIC/HCCL backpressure。
- 没有真实 failover timing 或 72h stress。
""" + _common_tail("运行 feature-completion reliability tests，或用 report verifier 只读复核冻结 evidence。",
                       ["docs/submission/report_chart_data/crc_retry_cases.json", "docs/submission/report_chart_data/backpressure_behavior.json"])


def _report_08(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    return _header("Simulator User Manual", "R08", "SIMULATED_ONLY", ledger) + """
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
certutil -hashfile <evidence>\\SHA256SUMS SHA256
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
""" + _common_tail("按上述命令复现；不得把输出升级为 REAL_DEVICE evidence。",
                       ["docs/submission/report_data_ledger.json", "docs/submission/reports/report_source_index.md"])


def _report_09(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    return _header("Native Plugin and ABI Appendix", "R09", "CPU_EXECUTED", ledger) + f"""
## Purpose

记录 Final Feature Freeze 后 CPU_SIM native artifact 的 ABI、ELF、dependency 与 reproducibility 状态。

## Scope

Artifact identity 为 `libhccl_plugin.so` / `CPU_SIM_REFERENCE_PLUGIN`。

## Validation Identity

这是 project CPU_SIM ABI；不等于 Direct control-plane/readiness ABI，也不等于 official HCCL plugin-loader ABI。

## Source Evidence

- `{relative(G3_B3_ROOT / 'native_elf_audit.json')}`
- `{relative(G3_B3_ROOT / 'reproducible_build.json')}`
- `{relative(G3_B3_ROOT / 'submission_regression.json')}`
- `hcccl/submission/native_plugin_abi_manifest.json`

## Methodology

冻结 audit 使用 ELF/file、SONAME、dynamic exports、NEEDED、double clean build、CTest 与 installed consumer compile。

## Results

- SONAME：`{_metric(m, 'g3b3.native.soname')}`。
- Artifact SHA256：`{_metric(m, 'g3b3.native.artifact_sha256')}`。
- Export count：{_metric(m, 'g3b3.native.exported_symbol_count')}。
- Dependency count：{_metric(m, 'g3b3.native.dependency_count')}；official dependencies 为空。
- Reproducibility：`{_metric(m, 'g3b3.native.reproducible_build_status')}`。
- CTest passed={_metric(m, 'g3b3.regression.ctest_passed')}，failed={_metric(m, 'g3b3.regression.ctest_failed')}；focused unittest passed={_metric(m, 'g3b3.regression.python_passed')}。

## Interpretation

结果证明 project-owned CPU_SIM native delivery 可重建并保持 ABI isolation；不能证明 official loader 接受该 export set。

## Claim Boundaries

- 不写 `official plugin ABI verified`。
- CPU_SIM libc-only dependency 不代表 Direct artifact 无官方 dependency。
""" + _common_tail("运行 submission CLI full 可重新构建 host artifact；G3-C 仅复用冻结结果，不重建性能 evidence。",
                       ["hcccl/submission/native_plugin_abi_manifest.json", "docs/submission/native_plugin_abi_decision.md"])


def _report_10(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    calls = read_json(G3_B3_ROOT / "official_api_call_expression_audit.json")["calls"]
    call_names = ", ".join(row["api"] for row in calls)
    return _header("Direct Compile/Link Readiness Appendix", "R10", "DIRECT_COMPILE_LINK_ONLY + REAL_DEVICE_NOT_EXECUTED", ledger) + f"""
## Purpose

说明 Direct 从 signature/symbol/link readiness 演进到 actual official API call-expression source readiness 的边界。

## Scope

覆盖 runtime init、device、context、stream、memory、communicator、AllReduce/AllGather/ReduceScatter、sync 与 reverse cleanup；只描述冻结 source/audit 中存在的 lifecycle。

## Validation Identity

`DIRECT_COMPILE_LINK_ONLY`。`loaded=false`、`executed=false`、`real_device_api_executed=false`、`direct_hccl_api_call=false`、`runtime_api_calls=[]`。

## Source Evidence

- `hcccl/direct/src/hccl_direct_runtime_source.cpp`
- `{relative(G3_B3_ROOT / 'official_api_call_expression_audit.json')}`
- `{relative(G3_B3_ROOT / 'direct_compile_link_audit.json')}`
- `{relative(G3_B3_ROOT / 'cpu_sim_isolation_audit.json')}`

## Methodology

Target default OFF，要求 explicit frozen CANN root；构建独立 shared inspection artifact，不链接进 CPU_SIM，不注册为 CTest executable，不由 report/submission CLI 加载执行。Verifier 只检查 source call syntax、compile/link result 与 ELF dependencies。

## Results

冻结 audit 的 official call-expression count 为 {_metric(m, 'g3b3.direct.official_call_expression_count')}。API inventory：{call_names}。

Runtime execution={_metric(m, 'g3b3.direct.runtime_execution')}。Direct artifact 可以链接 official libraries；CPU_SIM `libhccl_plugin.so` 仍保持隔离。

## Interpretation

Direct Production Source Readiness: `COMPLETED`。Real-device Acceptance: `HARDWARE_BLOCKED`。

## Claim Boundaries

- actual call expression present != runtime API executed。
- symbol/declaration/static_assert/link dependency 分别弱于 actual call expression；actual call expression 仍弱于 reachable runtime execution。
- G3-C 不执行 source artifact。
""" + _common_tail("只运行 `python -m tools.report_cli verify`；不得加载 Direct artifact。",
                       ["docs/feature_completion/direct_compile_only_runtime_source.md", "docs/submission/report_claim_ledger.json"])


def _report_11(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    m = _index(ledger)
    return _header("Known Limitations and Future Hardware Plan", "R11", "REAL_DEVICE_NOT_EXECUTED", ledger) + f"""
## Purpose

集中列出未解除限制，并定义未来 hardware acceptance，而不在 G3-C 执行。

## Scope

当前限制：no real Ascend NPU、ACL runtime、communicator、collective、official loader ABI、HCCS/RoCE/PCIe measurement、sparse physical bytes/speedup、hardware CRC/parity、transport retry、NIC/HCCL backpressure、msprof、BERT/LLaMA training、90% training scale、real failover timing、real 72h stress、zero-CPU verification、UB/HBM reuse verification。

## Validation Identity

上述均为 `REAL_DEVICE_NOT_EXECUTED` / `HARDWARE_BLOCKED`，不能由报告升级。

## Source Evidence

- `{relative(G3_B3_ROOT / 'result.json')}`
- `{relative(G3_B2_ROOT / 'claim_boundary_audit.json')}`
- `docs/submission/risk_register.json`

## Methodology

限制按 truth identity 与 hardware dependency 汇总。INT8={_metric(m, 'g3b3.gates.int8_quantization')}；PairWise={_metric(m, 'g3b3.gates.pairwise')}。

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
""" + _common_tail("当前只运行 report verifier；hardware plan 标记为 NOT EXECUTED IN G3-C。",
                       ["docs/submission/g3_c_requirement_delta.json", "docs/submission/report_claim_ledger.json"])


def _readme(ledger: dict[str, Any]) -> str:
    entries = "\n".join(f"- [{name}]({name})" for name in REPORT_FILES if name not in {"README.md", "report_source_index.md"})
    return f"""# G3-C Formal Technical Report Suite

Evidence-derived Markdown source for the frozen G3-B2 scheduling/performance family and G3-B3 feature-completion family.

- Source baseline: `{ledger['source_commit']}`
- Real-device validated: `false`
- Runtime API executed: `false`

{entries}

- [Report source index](report_source_index.md)
- [Top-level technical report index](../technical_report_index.md)
"""


def _source_index(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    rows = ["# Report Source Index", "", "| Report | Source code/config | Frozen evidence | Metric groups | Claim IDs |", "|---|---|---|---|---|"]
    mapping = {
        "R01": ("agent/; algorithm/; topology/", "algorithm_support_matrix; agent_trace_inventory", "algorithm_support, agent"),
        "R02": ("algorithm/schedule_ir.py; feature_completion/contracts.py", "c_python_parity; schedule_ir_v2_audit", "schedule_ir"),
        "R03": ("topology/; hardware/; configs/", "scale_summary", "g3_b2_scale"),
        "R04": ("simulator/; feature_completion/sparse.py", "correctness_summary; sparse_correctness", "correctness, correctness_coverage"),
        "R05": ("feature_completion/sparse.py; hcccl/src/internal/sparse_codec.c", "sparse_benchmark; sparse_break_even", "sparse, sparse_break_even"),
        "R06": ("algorithm/; simulator/", "performance_summary; wins_ties_losses; ablation", "g3_b2_performance, g3_b2_scenarios, g3_b2_ablation"),
        "R07": ("feature_completion/reliability.py; flow_control.py", "crc; retry; timeout; flow_control", "integrity, retry, backpressure"),
        "R08": ("tools/submission_cli/; simulator/", "submission_regression", "regression"),
        "R09": ("hcccl/; native ABI manifest", "native_elf; reproducible_build", "native_abi, regression"),
        "R10": ("hcccl/direct/src/hccl_direct_runtime_source.cpp", "official_api_call_expression; direct_compile_link", "direct"),
        "R11": ("risk/claim documents", "result; claim_boundary", "feature_gates"),
    }
    for filename, rid in REPORT_IDS.items():
        claim_ids = ", ".join(row["claim_id"] for row in claims["claims"] if row["report_id"] == rid) or "—"
        source, evidence, groups = mapping[rid]
        rows.append(f"| [{filename}]({filename}) | `{source}` | `{evidence}` | `{groups}` | `{claim_ids}` |")
    rows.extend(["", "All source paths are repository-relative. Numeric values resolve through `../report_data_ledger.json`; claims resolve through `../report_claim_ledger.json`."])
    return "\n".join(rows) + "\n"


def _technical_index(ledger: dict[str, Any], claims: dict[str, Any]) -> str:
    return f"""# Technical Report Index

Report Status: `FINAL_EVIDENCE_DERIVED`<br>
Source Commit: `{ledger['source_commit']}`<br>
Real-device Validated: `false`<br>
Runtime API Executed: `false`

- [Formal report suite](reports/README.md)
- [Report source index](reports/report_source_index.md)
- [Report data ledger](report_data_ledger.json) — {ledger['metric_count']} metrics
- [Report claim ledger](report_claim_ledger.json) — {claims['claim_count']} claims
- [Chart-data](report_chart_data/)
- [Stale-document audit](stale_document_audit.md)
- [G3-C requirement delta](g3_c_requirement_delta.json)

Final Feature Freeze remains in force. Performance is `SIMULATED_ONLY`; Direct is `DIRECT_COMPILE_LINK_ONLY`; real-device acceptance remains `HARDWARE_BLOCKED`.
"""


def _stale_audit() -> str:
    return """# Stale Documentation Audit

| Document / family | Classification | Rationale / replacement |
|---|---|---|
| `docs/submission/g3_b3_final_feature_baseline.md` | CURRENT FINAL FEATURE BASELINE | Current Final Feature Baseline |
| `docs/submission/g3_b2_final_code_baseline.md` | HISTORICAL | Historical optimization baseline; not current final code |
| `docs/submission/g3_a_gap_report.md` | HISTORICAL | Historical competition gap audit |
| `docs/submission/reproduction_guide.md` | CURRENT | Native/submission reproduction reference |
| older simulator guides under `docs/` | SUPERSEDED | Formal user entry is `reports/08_simulator_user_manual.md` |
| `docs/feature_completion/` | INTERNAL_REFERENCE | Engineering design detail supporting G3-B3 evidence |
| G2/G3-B interim evidence notes | HISTORICAL | Preserved; not rewritten by G3-C |

Historical documents are retained. No frozen evidence or prior baseline was deleted or regenerated.
"""


def _requirement_delta() -> dict[str, Any]:
    return {
        "schema_version": "g3-c-requirement-delta-v1",
        "baseline": "G3-A historical matrix; G3-B2 and G3-B3 frozen evidence",
        "historical_matrix_modified": False,
        "changes": [
            {"requirement": "formal technical report suite", "previous": "PARTIAL", "current": "SATISFIED", "basis": "G3-C reports and verifier"},
            {"requirement": "algorithm and Schedule IR explanation", "previous": "PARTIAL", "current": "SATISFIED", "basis": "reports R01/R02"},
            {"requirement": "simulator user manual", "previous": "PARTIAL", "current": "SATISFIED", "basis": "report R08"},
            {"requirement": "numeric traceability", "previous": "PARTIAL", "current": "SATISFIED", "basis": "report_data_ledger"},
            {"requirement": "real performance", "previous": "PARTIAL", "current": "PARTIAL", "basis": "cannot be upgraded by reporting"},
            {"requirement": "real-device acceptance", "previous": "HARDWARE_BLOCKED", "current": "HARDWARE_BLOCKED", "basis": "no authorized hardware runtime"},
            {"requirement": "official loader ABI", "previous": "PARTIAL", "current": "PARTIAL", "basis": "CPU_SIM project ABI only"},
        ],
        "user_action_required": list(USER_ACTIONS),
        "real_device_api_executed": False,
        "runtime_api_calls": [],
    }


def _chart_payload(name: str, metrics: list[dict[str, Any]], truth: str) -> dict[str, Any]:
    return {
        "schema_version": "g3-c-chart-data-v1", "chart_id": name.removesuffix(".json"),
        "truth_label": truth, "derived_from": "docs/submission/report_data_ledger.json",
        "metric_refs": [row["metric_id"] for row in metrics],
        "series": [{"metric_id": row["metric_id"], "value": row["value"], "unit": row["unit"],
                    "display_value": row["display_value"]} for row in metrics],
    }


def build_chart_data(ledger: dict[str, Any], claims: dict[str, Any]) -> dict[str, Any]:
    metrics = ledger["metrics"]
    by_group = lambda *groups: [row for row in metrics if row["metric_group"] in groups]
    mapping = {
        "correctness_coverage.json": (by_group("correctness", "correctness_coverage"), "SIMULATED_ONLY + LOSSLESS_SPARSE_HOST_EXECUTED"),
        "algorithm_support_matrix.json": (by_group("algorithm_support"), "HISTORICAL_EVIDENCE"),
        "schedule_phase_comparison.json": ([row for row in by_group("g3_b2_ablation") if row["metric_id"].endswith("phase_count")], "SIMULATED_ONLY"),
        "g3_b2_latency_comparison.json": ([row for row in by_group("g3_b2_scenarios") if "p50_us" in row["metric_id"] or "p95_us" in row["metric_id"]], "SIMULATED_ONLY"),
        "g3_b2_bandwidth_comparison.json": ([row for row in by_group("g3_b2_scenarios") if "bandwidth" in row["metric_id"]], "SIMULATED_ONLY"),
        "g3_b2_scale.json": (by_group("g3_b2_scale"), "SIMULATED_ONLY"),
        "g3_b2_ablation.json": (by_group("g3_b2_ablation"), "SIMULATED_ONLY"),
        "sparse_compression_ratio.json": ([row for row in by_group("sparse") if row["metric_id"].endswith("compression_ratio")], "LOSSLESS_SPARSE_HOST_EXECUTED"),
        "sparse_break_even.json": (by_group("sparse_break_even"), "SIMULATED_ONLY"),
        "sparse_wire_bytes.json": ([row for row in by_group("sparse") if row["metric_id"].endswith(("logical_bytes", "value_bytes", "index_bytes", "metadata_bytes", "wire_bytes"))], "LOSSLESS_SPARSE_HOST_EXECUTED"),
        "sparse_dense_fallback.json": ([row for row in by_group("sparse") if row["metric_id"].endswith(("selected_mode", "sparsity_ratio"))], "HOST_EXECUTED"),
        "crc_retry_cases.json": (by_group("integrity", "retry"), "HOST_INTEGRITY_VALIDATED + HOST_RETRY_VALIDATED"),
        "reliability_outcomes.json": (by_group("retry"), "HOST_RETRY_VALIDATED"),
        "backpressure_behavior.json": (by_group("backpressure"), "SIMULATED_BACKPRESSURE"),
        "direct_readiness_status.json": (by_group("direct"), "DIRECT_COMPILE_LINK_ONLY"),
        "claim_boundary_summary.json": ([], "REAL_DEVICE_NOT_EXECUTED"),
    }
    CHART_ROOT.mkdir(parents=True, exist_ok=True)
    for name in CHART_FILES:
        selected, truth = mapping[name]
        payload = _chart_payload(name, selected, truth)
        if name == "claim_boundary_summary.json":
            payload["claims"] = [{"claim_id": row["claim_id"], "truth_label": row["truth_label"], "status": row["status"]} for row in claims["claims"]]
        write_json(CHART_ROOT / name, payload)
    return {"status": "PASS", "chart_count": len(CHART_FILES), "charts": list(CHART_FILES)}


def render_reports(ledger: dict[str, Any], claims: dict[str, Any]) -> dict[str, Any]:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    renderers: dict[str, Callable[[dict[str, Any], dict[str, Any]], str]] = {
        "01_system_architecture_and_algorithm_design.md": _report_01,
        "02_collective_schedule_ir_and_algorithm_evolution.md": _report_02,
        "03_topology_and_hardware_model.md": _report_03,
        "04_dense_and_sparse_correctness_report.md": _report_04,
        "05_sparse_communication_and_wire_accounting_report.md": _report_05,
        "06_simulator_performance_and_scale_report.md": _report_06,
        "07_integrity_retry_and_reliability_report.md": _report_07,
        "08_simulator_user_manual.md": _report_08,
        "09_native_plugin_and_abi_appendix.md": _report_09,
        "10_direct_compile_link_readiness_appendix.md": _report_10,
        "11_known_limitations_and_future_hardware_plan.md": _report_11,
    }
    write_text(REPORT_ROOT / "README.md", _readme(ledger))
    for filename, renderer in renderers.items():
        write_text(REPORT_ROOT / filename, renderer(ledger, claims))
    write_text(REPORT_ROOT / "report_source_index.md", _source_index(ledger, claims))
    write_text(REPORT_INDEX, _technical_index(ledger, claims))
    write_text(STALE_AUDIT, _stale_audit())
    write_json(REQUIREMENT_DELTA, _requirement_delta())
    chart = build_chart_data(ledger, claims)
    return {"status": "PASS", "report_count": len(renderers), "files": list(REPORT_FILES), "chart_data": chart}
