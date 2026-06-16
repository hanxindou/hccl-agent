# Agent 能力清单 (Agent Capabilities)

本文档列出 HCCL-Agent 当前具备的能力模块，每个模块说明其功能、输入输出、能力和局限。这是赛题要求的正式交付物之一。

---

## 能力总览

| 模块 | 类型 | 状态 | 说明 |
|------|------|------|------|
| ConfigSkill | 硬件感知 | ✅ 可用 | 集群配置加载、校验与链路参数提取 |
| TopologySkill | 拓扑感知 | ✅ 可用 | 基于节点数推断拓扑类型 |
| TopologyGraph | 拓扑建模 | ✅ 可用 | 加权图模型，支持路径计算 |
| AlgorithmSkill | 算法选择 | ✅ 可用 | 多粒度消息大小算法筛选 |
| Simulator | 性能模拟 | ✅ 可用 | 通信性能估算（latency/bandwidth/score） |
| PerformanceModel | 性能评分 | ✅ 可用 | 综合评分模型 |
| OptimizationSkill | 优化排序 | ✅ 可用 | 候选算法评估与排名 |
| StrategySkill | 策略生成 | ✅ 可用 | 通信路径步骤生成 |
| FaultInjector | 可靠性 | ✅ 可用 | 故障注入与重传统计 |
| ExperimentLogger | 日志追踪 | ✅ 可用 | 结构化实验日志与聚合 |
| ReportGenerator | 报告生成 | ✅ 可用 | Markdown 性能报告自动生成 |
| HCCLAgent | Agent 编排 | ✅ 可用 | 全流程编排与决策解释 |

---

## 1. 硬件感知能力 (Hardware Awareness)

### ConfigSkill

- **功能**: 加载 `config/cluster.json`，校验必需字段，提取链路参数
- **输入**: 配置文件路径（可选）
- **输出**: 标准化集群配置 dict
- **能力**:
  - 支持 HCCS / RoCE / PCIe 多链路类型
  - 自动提取主链路带宽/延迟到顶层字段
  - 缺失字段填充默认值
  - 按链路类型查询参数
- **局限**: 当前为静态配置文件，尚未对接 HCOMM `hcclGetTopology` 实时探测

### TopologySkill

- **功能**: 根据节点数推断拓扑类型
- **输入**: `nodes` (int)
- **输出**: 拓扑名称字符串 (Full Mesh / Ring / Fat Tree)
- **能力**: 规则: ≤8→Full Mesh, ≤64→Ring, >64→Fat Tree
- **局限**: 基于简单规则，未构建实际链路图

### TopologyGraph

- **功能**: 构建加权有向图，支持路径计算
- **输入**: 节点数、链路参数
- **输出**: 图对象，支持最短延迟路径、最大带宽路径计算
- **能力**:
  - 构建 Full Mesh / Ring / Fat-Tree 标准拓扑
  - 边属性：链路类型、带宽、延迟、误码率、健康状态
  - Dijkstra 最短路径（延迟最小）
  - 最大瓶颈带宽路径
  - 故障链路标记
- **局限**: Fat-Tree 为简化模型，未建模多层交换机

---

## 2. 算法生成能力 (Algorithm Generation)

### AlgorithmSkill

- **功能**: 根据消息大小、节点数、原语类型选择候选算法
- **输入**: `nodes`, `message_size_mb`, `primitive`
- **输出**: 候选算法名称列表
- **支持的算法**:
  - **Butterfly** (递归加倍): log2(N) 步，适合 ≤64KB 小数据
  - **PairWise**: N-1 步逐对交换，适合极小数据
  - **Ring AllReduce**: 2(N-1) 步环，适合中大数据
  - **NHR** (非均匀环): 适合异构带宽场景
  - **Mesh** (全互联): 适合单机 Full Mesh
  - **Fat-Tree** (分层): 适合多机多卡
- **消息粒度**: ≤64KB / ≤1MB / ≤512MB / ≤1GB / >1GB 五级
- **局限**: 选择基于规则而非 ML 模型；尚未实现代码自动生成

### StrategySkill

- **功能**: 根据最优算法生成通信步骤
- **输入**: `algorithm`, `nodes`
- **输出**: 通信步骤文本列表
- **能力**:
  - Ring: 生成动态环形路径
  - Butterfly: 基于 bit-flip 的动态递归加倍配对
  - 多余节点自动挂载
- **局限**: 文本描述，非可执行通信调度代码

---

## 3. 性能评估能力 (Performance Evaluation)

### Simulator

- **功能**: 估算算法在指定拓扑下的延迟、带宽、综合评分
- **输入**: algorithm, topology, nodes, message_size_mb, primitive, bandwidth_gbps, latency_ms
- **输出**: {latency_ms, bandwidth_gb_s, score}
- **能力**:
  - 6 种算法的独立性能模型
  - 拓扑因子调整（Full Mesh 低延迟 / Fat-Tree 额外开销）
  - 原语类型因子（AllGather 0.9x / ReduceScatter 0.95x）
  - 使用 cluster.json 链路参数
- **局限**: 公式为近似模型，未基于真实 HCCL profiling 数据校准

### PerformanceModel

- **功能**: 综合评分 = bandwidth * 0.7 - latency * 0.3
- **局限**: 权重未经实验校准，未纳入正确性、可靠性维度

### OptimizationSkill

- **功能**: 遍历候选算法，模拟评估，按 score 排名
- **输出**: best_algorithm, best_result, ranking
- **局限**: 仅比较 score，未记录完整评估日志（日志由 ExperimentLogger 单独完成）

---

## 4. 可靠性能力 (Reliability)

### FaultInjector

- **功能**: 故障注入模拟与可靠性统计
- **故障类型**: link_down / timeout / corruption / congestion
- **能力**:
  - 指定链路故障/恢复
  - 随机链路故障注入
  - 基于 BER 的数据损坏模拟
  - 拥塞带宽削减
  - 传输模拟（含重传统计）
  - 可靠性报告生成（重传率 vs 0.1% 目标）
- **局限**: 当前为统计模型，未实现真实的超时重传协议栈

---

## 5. 可追溯性能力 (Traceability)

### ExperimentLogger

- **功能**: 每次 Agent 运行记录为 JSON-lines 日志
- **输出**:
  - `logs/runs.jsonl`: 每次运行的完整参数和结果
  - `logs/summary.json`: 聚合统计（按原语、算法、拓扑）
- **能力**: 进程安全追加写入，自动聚合更新

### ReportGenerator (`scripts/generate_report.py`)

- **功能**: 从实验日志生成 Markdown 性能报告
- **输出**: `logs/performance_report.md`
- **包含**:
  - 算法性能对比表
  - 按原语/拓扑/消息大小的分析
  - 最近运行记录

---

## 6. Agent 编排能力 (Orchestration)

### HCCLAgent

- **功能**: 串联所有 Skill，完成从配置加载到策略输出的全流程
- **输入**: nodes, message_size, primitive
- **输出**: 包含 cluster, primitive, topology, candidate_algorithms, algorithm, reason, result, ranking, strategy 的完整字典
- **能力**:
  - Primitive 校验（AllReduce / AllGather / ReduceScatter）
  - 拓扑推断
  - 算法选择 → 模拟评估 → 排名 → 策略生成 → 日志记录
  - 推荐理由生成（中文）

---

## 未来能力规划

| 能力 | 优先级 | 说明 |
|------|--------|------|
| C/C++ 代码生成 | P0 | 通过 LLM Agent 生成 HCCL 插件代码 |
| HCOMM 接口对接 | P0 | 调用 hcclGetTopology / hcclAllReduce 等 |
| 实机 Profiling 集成 | P1 | 对接 msprof 或模拟器采集真实指标 |
| 自适应分块调度 | P1 | 根据 UB 容量动态调整 chunk size |
| 稀疏通信 | P2 | 梯度稀疏化 + 量化压缩 |
| 通算重叠 | P2 | 计算通信流水线并发建模 |
| 动态拓扑自适应 | P2 | 节点热插拔时算法自动重构 |
