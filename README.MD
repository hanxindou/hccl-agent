# HCCL-Agent: Distributed Communication Algorithm Optimization

面向 **2026年中国研究生人工智能大赛—华为赛题「基于 CANN 的分布式通信算法设计与优化」** 的 Agent 工程。

## 项目目标

依托智能 Agent 技术，完成 HCCL 集合通信算法（AllReduce / AllGather / ReduceScatter）的全流程设计与代码开发，实现高性能、高可靠、低延迟的分布式通信能力，深度适配昇腾 NPU 集群的高速硬件链路（HCCS / RoCE / PCIe）。

## 当前阶段

**自主执行 H1 前置阶段已完成至 G1** — 当前系统是 **Python Agent + 数学/可靠性模拟器 + Windows CPU_SIM C 插件原型 + CANN/Ascend 适配准备层**。

已验证和未验证边界：

- Python Agent 主流程可进行规则候选选择、模拟评分、Prompt 记录和实验日志记录。
- C 插件当前是 CPU 模拟实现，不是 CANN/HCOMM/Ascend 实机实现。
- C 层已覆盖 AllReduce、AllGather、ReduceScatter 的 CPU_SIM 数据正确性基线；Broadcast 仍为未支持边界。
- FP32 SUM/PROD/MAX/MIN、FP16 和 BF16 CPU 软件模拟已通过 Windows DLL、CTest 和 Python 回归验证。
- Agent 代码开发闭环当前为 `OFFLINE_TEMPLATE` 最小演示，不调用真实外部 LLM。
- 拓扑/成本/可靠性结果来自 `ANALYTICAL_MODEL` 或 `RELIABILITY_MODEL`，不能直接作为真实 HCCL 性能或可靠性结论。
- Linux `.so`、真实多设备通信、CANN/HCOMM 链接、Ascend 实机正确性、msprof 和硬件可靠性仍未验证。

H1 交付汇总见：

```text
docs/competition_readiness_report.md
```

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
│   ├── test_agent.py               # Agent 主流程测试
│   └── ...                         # Python 单元测试
├── hcccl/
│   ├── CMakeLists.txt              # CPU 模拟 C 插件构建
│   ├── include/                    # HCCL-like 接口声明
│   ├── src/                        # CPU 模拟通信器和 AllReduce 算法
│   └── tests/                      # C 测试程序
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

### Windows C 插件验证

```cmd
set BUILD_DIR=F:\build\hccl-agent-hcccl-a1
cmake -S hcccl -B "%BUILD_DIR%" -G "Visual Studio 17 2022" -A x64
cmake --build "%BUILD_DIR%" --config Release
ctest --test-dir "%BUILD_DIR%" -C Release --output-on-failure
```

Windows 默认 CMake 配置应生成 `hccl_plugin.dll` 和 `hccl_plugin.lib`，并通过 CTest 发现 6 个 C 测试程序。

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
- [x] Python 单元测试覆盖
- [x] CPU 模拟 C 插件构建
- [x] 有限 FP32/SUM AllReduce CPU 模拟测试
- [ ] 完整 C AllGather / ReduceScatter 数据实现
- [ ] FP16 / BF16 / 通用 ReduceOp
- [ ] CANN/HCOMM/Ascend 实机验证

## 开发路线

### P0（已完成本次迭代）

- [x] 修复 Python 原型主流程
- [x] 补齐 README 和 Prompt 初版
- [x] 基础单元测试
- [x] 模拟器日志格式
- [x] primitive 全链路传递

### P0（当前优先）

- [ ] 收敛文档事实、项目树和跨平台验证基线
- [ ] 闭合标准 C wrapper 与 Python 调用边界
- [ ] 实现 AllGather / ReduceScatter CPU 数据正确性
- [ ] 建立 FP32 正确性基准和后续 FP16/BF16 计划

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
