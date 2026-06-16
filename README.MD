# HCCL-Agent: Distributed Communication Algorithm Optimization

面向 **2026年中国研究生人工智能大赛—华为赛题「基于 CANN 的分布式通信算法设计与优化」** 的 Agent 工程。

## 项目目标

依托智能 Agent 技术，完成 HCCL 集合通信算法（AllReduce / AllGather / ReduceScatter）的全流程设计与代码开发，实现高性能、高可靠、低延迟的分布式通信能力，深度适配昇腾 NPU 集群的高速硬件链路（HCCS / RoCE / PCIe）。

## 当前阶段

**Python 概念原型** — 具备最小可运行的 Agent → Skills → Simulator 闭环。后续将逐步过渡到 C/C++ HCCL 插件工程。

## 目录结构

```
.
├── README.MD                       # 本文件
├── main.py                         # CLI 入口（支持交互式和非交互式）
├── agent/
│   ├── hccl_agent.py               # Agent 编排核心
│   └── experiment_logger.py        # 结构化实验日志
├── skills/
│   ├── algorithm_skill.py          # 算法选择
│   ├── topology_skill.py           # 拓扑推断
│   ├── config_skill.py             # 配置加载与校验
│   ├── optimization_skill.py       # 优化评估与排名
│   ├── strategy_skill.py           # 通信策略生成
│   └── performance_model.py        # 性能评分模型
├── simulator/
│   └── simulator.py                # 通信性能模拟器
├── config/
│   └── cluster.json                # 静态集群配置
├── prompts/
│   └── algorithm_prompt.txt        # Prompt 文件（Agent 引导词）
├── tests/
│   └── test_agent.py               # 单元测试
├── docs/
│   ├── project_documentation.md    # 详细项目文档
│   ├── gap_analysis.md             # 差距分析
│   ├── competition_analysis.md     # 赛题分析
│   └── 2026年中国研究生人工智能大赛--华为赛题.docx  # 原始赛题
└── logs/
    ├── runs.jsonl                  # 每次运行记录
    └── summary.json                # 聚合统计
```

## 环境要求

- Python 3.8+
- 无外部依赖（仅使用标准库）

## 快速开始

### 非交互式运行（推荐，可复现）

```bash
# 8 节点、128 MB 消息、AllReduce 原语
python3 main.py --nodes 8 --message-size 128 --primitive AllReduce

# 64 节点、2 GB 消息、AllGather 原语
python3 main.py --nodes 64 --message-size 2048 --primitive AllGather

# 小数据块 30KB 场景（0.03 MB）
python3 main.py --nodes 8 --message-size 0.03 --primitive ReduceScatter
```

### 交互式运行

```bash
python3 main.py
# 按提示输入 nodes、message_size（单位 MB）
```

### 运行测试

```bash
python3 -m unittest tests/test_agent.py -v
```

## 架构

```
main.py (CLI)
  └─> HCCLAgent.run(nodes, message_size, primitive)
        ├─> ConfigSkill.load_cluster_info()        # 加载 & 校验配置
        ├─> TopologySkill.analyze(nodes)            # 推断拓扑
        ├─> AlgorithmSkill.choose_algorithms()      # 选择候选算法
        ├─> OptimizationSkill.optimize()            # 评估 & 排序
        │     └─> Simulator.evaluate()              # 性能模拟
        │           └─> PerformanceModel.calculate_score()
        ├─> StrategySkill.generate()                # 生成通信步骤
        └─> ExperimentLogger.log_run()              # 持久化日志
```

## 已实现功能

- [x] 静态集群配置加载与校验
- [x] 基于节点数的拓扑推断（Full Mesh / Ring / Fat Tree）
- [x] 多粒度消息大小算法选择（≤64KB → ≥1GB）
- [x] 三种集合通信原语识别（AllReduce / AllGather / ReduceScatter）
- [x] primitive 感知的算法选择和性能模拟
- [x] 使用 cluster.json 带宽/延迟配置的模拟器
- [x] Butterfly 动态配对（非硬编码）
- [x] 候选算法评分排序
- [x] 通信策略文本生成
- [x] 结构化实验日志（JSON-lines + summary）
- [x] CLI 非交互式运行入口
- [x] 最小单元测试覆盖

## 开发路线

### P0（已完成本次迭代）

- [x] 修复 Python 原型主流程
- [x] 补齐 README 和 Prompt 初版
- [x] 基础单元测试
- [x] 模拟器日志格式
- [x] primitive 全链路传递

### P0（待完成）

- [ ] 建立 C/C++ HCCL 插件目录和 CMake 骨架
- [ ] Agent 能力清单文档
- [ ] 模拟器配置说明文档

### P1（高优先级）

- [ ] 实现 AllReduce / AllGather / ReduceScatter 基线模拟与测试
- [ ] 扩展 topology 数据结构为链路图
- [ ] 扩展 cluster.json 为多节点、多链路、多设备配置
- [ ] 性能报告生成脚本
- [ ] 故障注入模拟

### P2（可选优化）

- [ ] NHR 非均匀环、动态分块 Ring、分块 Mesh
- [ ] 稀疏通信、量化压缩
- [ ] 通信计算重叠建模
- [ ] 动态拓扑自适应
- [ ] 可视化性能报告

## 实验日志

每次 Agent 运行会记录到 `logs/runs.jsonl`（每行一条 JSON 记录），聚合统计在 `logs/summary.json`。
