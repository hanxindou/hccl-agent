# Stage D1 拓扑与成本模型说明

更新时间：2026-07-29

## 结论

D1 后的主拓扑模型为：

```text
topology.graph_builder.CommunicationGraph
```

`skills/topology_graph.py` 保留为 legacy skill-level 图模型和历史测试兼容入口，不再作为 `Simulator` 和 `CostModelEngine` 的主路径。

当前性能输出状态：

```text
CPU_SIMULATED / ANALYTICAL_MODEL
```

不得描述为真实 HCCL、CANN、HCOMM 或 Ascend 实机性能。

## 统一公式

```text
latency
= startup_cost
+ communication_steps * per_step_latency
+ transferred_bytes / effective_bandwidth
+ contention_penalty
```

## 参数来源

| 参数 | 单位 | 默认值 | 来源 | 适用拓扑 | 是否校准 | 可信度 |
| ---- | ---- | ------ | ---- | -------- | -------- | ------ |
| `startup_cost_ms` | ms | `0.003` | 项目分析模型默认值 | 全部 | 否 | low |
| `bandwidth_gbps` | Gbps | `HardwareProfile.link_types` | `hardware/profile.py` 相对 tier | HCCS/RoCE/PCIe | 否 | medium |
| `latency_ms` | ms | `HardwareProfile.link_types` | `hardware/profile.py` 相对 tier | HCCS/RoCE/PCIe | 否 | medium |
| `contention_penalty` | ms | 由规模、链路混合、算法推导 | D1 analytical model | 全部 | 否 | low |

## 链路类型

| Link | 当前含义 | 来源 |
| ---- | -------- | ---- |
| HCCS | 单机 NPU 间高带宽低延迟相对模型 | `HardwareProfile.tier_medium()` |
| RoCE | 多机 leader 间网络相对模型 | `HardwareProfile.tier_medium()` |
| PCIe | 异构/回退链路相对模型 | `HardwareProfile.tier_medium()` |

## 规模场景

D1 验证覆盖：

```text
8, 64, 128, 256, 1024 rank
```

验证内容：

- message size 增大时 latency 和 `transferred_bytes` 增大；
- 链路类型改变时 latency/bandwidth 改变；
- 节点规模增大时 Ring AllReduce latency 单调上升；
- 输出包含 `model_type`、`communication_steps`、`transferred_bytes`、`link_types`、`parameter_sources`。

## 模型假设

- 所有数值是相对排序和趋势分析，不是实机 profiling。
- 带宽、延迟和 contention 参数尚未用 Ascend 实机校准。
- 多机拓扑由 `TopologyGraphBuilder` 生成 HCCS/RoCE 混合图。
- 异构拓扑会引入 PCIe 回退链路。
- 算法步骤是可解释近似，不等同于真实 HCCL 内核调度。

## 未验证边界

- Linux `.so` 未验证。
- CANN SDK 未接入。
- HCOMM 标准运行时未接入。
- Ascend 实机 latency、bandwidth、msprof 数据未验证。
