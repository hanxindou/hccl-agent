# 模拟器说明文档 (Simulator Guide)

本文档说明 HCCL-Agent 模拟器的配置、运行流程、性能模型和验证方法。这是赛题要求的正式交付物之一。

---

## 1. 概述

HCCL-Agent 模拟器用于在缺乏实体昇腾硬件的情况下，模拟 NPU 集群的集合通信性能。模拟器接收算法名称、拓扑、节点数、消息大小和链路参数，输出预估的延迟、带宽和综合评分。

**当前阶段**: 概念验证模型，公式基于通信复杂度估算，尚未使用真实 HCCL profiling 数据校准。

---

## 2. 配置说明

模拟器的硬件参数来自 `config/cluster.json`。

### 2.1 集群配置文件结构

```json
{
    "cluster_name": "Ascend-Test-Cluster",
    "nodes": 8,
    "topology": "Full Mesh",
    "device_type": "Ascend910A",
    "memory_gb": 64,

    "links": [
        {
            "type": "HCCS",
            "bandwidth_gbps": 100,
            "latency_ms": 0.002,
            "ber": 1e-12,
            "duplex": "full"
        },
        {
            "type": "RoCE",
            "bandwidth_gbps": 100,
            "latency_ms": 0.005,
            "ber": 1e-10
        },
        {
            "type": "PCIe",
            "bandwidth_gbps": 32,
            "latency_ms": 0.010,
            "ber": 1e-9
        }
    ],

    "numa": {
        "nodes_per_socket": 4,
        "sockets": 2
    },

    "hbm": {
        "capacity_gb": 64,
        "bandwidth_gbps": 1200
    },

    "ub": {
        "capacity_kb": 192
    },

    "available_algorithms": [
        "Ring AllReduce", "Butterfly", "PairWise",
        "NHR", "Mesh", "Fat-Tree"
    ]
}
```

### 2.2 关键参数说明

| 参数 | 单位 | 说明 |
|------|------|------|
| `links[].bandwidth_gbps` | Gbps | 链路带宽，HCCS 通常 100-400 Gbps |
| `links[].latency_ms` | ms | 链路延迟，HCCS ~2us，RoCE ~5us，PCIe ~10us |
| `links[].ber` | - | 误码率 (Bit Error Rate)，HCCS 通常 1e-12 |
| `numa.nodes_per_socket` | - | 每 socket 的 NPU 数量 |
| `hbm.capacity_gb` | GB | HBM 容量，影响 chunk 大小选择 |
| `ub.capacity_kb` | KB | 片上统一缓存，影响数据驻留策略 |

---

## 3. 性能模型

### 3.1 算法步数模型

| 算法 | 步数公式 | 每步数据量 |
|------|---------|-----------|
| Ring AllReduce | 2 × (N−1) | M / N |
| Butterfly | ⌈log₂(N)⌉ | M |
| PairWise | N−1 | M |
| NHR | 2 × (N−1) | M / N |
| Mesh | 1 | M |
| Fat-Tree | 2 × ⌈log₂(N)⌉ | M |

其中 N = 节点数, M = 消息大小。

### 3.2 延迟模型

```
latency_ms = steps × link_latency_ms × topology_factor × primitive_factor
```

| 拓扑因子 | 值 |
|---------|-----|
| Full Mesh | 1.0 |
| Ring | 1.0 |
| Fat Tree | 1.15 |
| 其他 | 1.2 |

| 原语因子 | 值 |
|---------|-----|
| AllReduce | 1.0 |
| AllGather | 0.9 |
| ReduceScatter | 0.95 |

### 3.3 带宽模型

```
effective_bandwidth_gbps = link_bandwidth_gbps × topology_factor × primitive_factor
bandwidth_gb_s = effective_bandwidth_gbps / 8.0
```

### 3.4 综合评分

```
score = bandwidth_gb_s × 0.7 − latency_ms × 0.3
```

---

## 4. 验证流程

### 4.1 单次运行

```bash
python3 main.py --nodes 8 --message-size 128 --primitive AllReduce
```

### 4.2 批量验证

```bash
# 运行多个场景
for nodes in 8 16 32 64; do
  for msg in 0.03 1 128 512 2048; do
    for prim in AllReduce AllGather ReduceScatter; do
      python3 main.py --nodes $nodes --message-size $msg --primitive $prim
    done
  done
done
```

### 4.3 生成性能报告

```bash
python3 scripts/generate_report.py
cat logs/performance_report.md
```

### 4.4 查看实验摘要

```bash
cat logs/summary.json
cat logs/runs.jsonl  # 完整记录
```

---

## 5. 验证标准

模拟器验证结果应与以下预期行为一致：

| 场景 | 预期行为 |
|------|---------|
| ≤64KB 小数据 | 选择 Butterfly 或 PairWise（低延迟优先） |
| 中数据 + Full Mesh | 倾向于 Mesh 算法（高带宽） |
| ≥1GB 大数据 + 多节点 | 选择 Fat-Tree 分层算法 |
| AllGather 原语 | Butterfly 出现在候选列表 |
| ReduceScatter 原语 | Ring AllReduce 出现在候选列表 |
| 节点数变化 | 拓扑正确推断（8→Full Mesh, 64→Ring, 128→Fat Tree） |

---

## 6. 已知局限

1. **公式为近似模型**：步数和数据量基于理论复杂度，未考虑实际实现的常数因子、流水线效率、内存墙等。
2. **未建模拥塞**：当前 topology_factor 为固定值，未模拟链路竞争和动态拥塞。
3. **未建模计算开销**：归约计算、pack/unpack 开销未纳入延迟模型。
4. **未对接真实 HCCL 基准**：尚未与昇腾实机 HCCL 性能数据进行校准。
5. **简化 Fat-Tree**：仅建模两层（机内 Mesh + 机间 Ring），未建模多层交换机。

---

## 7. 后续改进方向

- 使用真实 HCCL profiling 数据校准模型参数
- 引入链路拥塞模拟（多流竞争）
- 对接 TopologyGraph 的路径计算
- 集成 FaultInjector 的可靠性验证
- 支持异构设备（910A2/910A3 混合）
