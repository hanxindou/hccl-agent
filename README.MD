# HCCL-Agent: Distributed Communication Algorithm Optimization

面向 **2026年中国研究生人工智能大赛—华为赛题「基于 CANN 的分布式通信算法设计与优化」** 的 Agent 工程。

## 项目目标

依托智能 Agent 技术，完成 HCCL 集合通信算法（AllReduce / AllGather / ReduceScatter）的全流程设计与代码开发，实现高性能、高可靠、低延迟的分布式通信能力，深度适配昇腾 NPU 集群的高速硬件链路（HCCS / RoCE / PCIe）。

## 当前阶段

**V1 Linux 交付与 correctness hardening 已完成到本地可提交状态** — 当前系统是 **Python Agent + 数学/可靠性模拟器 + Windows CPU_SIM C 插件原型 + Linux CPU_SIM 验证工具/CI 配置 + CANN/Ascend 适配准备层**。

G3-B 已规范化两条不可混同的原生交付轨道：

- `libhccl_plugin.so` 是项目自有 `CPU_SIM_REFERENCE_PLUGIN`，在 host memory
  上执行三原语；它不是官方 HCCL loader plugin。
- `libhccl_direct_adapter.a` 是
  `STATIC BUILD/LIFECYCLE READINESS ARTIFACT`，只提供官方签名静态冻结、
  非执行 link audit 与 host lifecycle；它不执行真实 collective。

默认 backend 仍为 `CPU_SIM`，fallback 仍为 `NONE`。无 NPU/CANN 的评委路径：

```bash
python -m tools.submission_cli check
python -m tools.submission_cli quick
python -m tools.submission_cli full
python -m tools.submission_cli stage --clean-output --include-selected-evidence --exclude-controlled-docs --exclude-official-assets
python -m tools.submission_cli verify --stage dist/submission-staging
```

`SIMULATOR_ACCEPTANCE` 是独立验证轨道，不是第四个 backend。当前未执行真实
ACL/HCCL runtime、NPU communicator 或 collective；正式技术报告、Agent/Prompt
trace、图表、视频、许可证审查和最终 archive 分别留给 G3-C 至 G3-G 或
`USER_ACTION_REQUIRED`。复现、ABI、staging、依赖与真实性边界见
`docs/submission/`。

已验证和未验证边界：

- Python Agent 主流程可进行规则候选选择、模拟评分、Prompt 记录和实验日志记录。
- C 插件当前是 CPU 模拟实现，不是 CANN/HCOMM/Ascend 实机实现。
- C 层已覆盖 AllReduce、AllGather、ReduceScatter 的 CPU_SIM 数据正确性基线；Broadcast 仍为未支持边界。
- V1 已验证 AllReduce 多元素 `count>1`、ReduceScatter 2-rank 正确长度 buffer、FP32 SUM/PROD/MAX/MIN、FP16/BF16 CPU 软件模拟和固定 seed 随机 correctness。
- Agent 代码开发闭环当前为 `OFFLINE_TEMPLATE` 最小演示，不调用真实外部 LLM。
- 拓扑/成本/可靠性结果来自 `ANALYTICAL_MODEL` 或 `RELIABILITY_MODEL`，不能直接作为真实 HCCL 性能或可靠性结论。
- Linux `libhccl_plugin.so` 验证脚本和 GitHub Actions workflow 已配置，但 Docker build 因 `auth.docker.io` token 获取超时标记为 `ENV_BLOCKED`；CI 未经远端运行，仅为 `CI_CONFIGURED_UNRUN`。
- 真实多设备通信、CANN/HCOMM 链接、Ascend 实机正确性、msprof 和硬件可靠性仍未验证。

V1 交付汇总见：

```text
docs/competition_readiness_report.md
docs/v1_validation_report.md
```

## G2-F 后端与验收轨道

执行后端始终只有 `CPU_SIM`、`ASCEND_HCCL_VM` 与
`ASCEND_HCCL_DIRECT`；默认选择为 `CPU_SIM`，显式选择不可执行的后端会
返回结构化 blocked/next-action 信息，绝不静默降级。`SIMULATOR_ACCEPTANCE`
是独立验证轨道，不是第四个执行后端。

```bash
# 查看可用后端、能力与禁止的真实性声明
python3 main.py backends

# 显式 direct readiness 查询：当前仅返回 NO_DEVICE_EXPECTED，
# 不会加载官方 runtime 或调用 collective。
python3 main.py --backend ASCEND_HCCL_DIRECT --nodes 2 --message-size 1
```

G2-F-5/G2-F-6 simulator evidence 只可证明模拟正确性、模型化的拓扑/性能/
规模/可靠性；G2-F-1 至 G2-F-4 只可证明 direct readiness。它们均不构成
真实 Ascend NPU 或 direct collective 成功证据。验证某一 evidence 目录：

```bash
cd experiments/simulator/evidence/g2_f_6_simulator_20260804T020000Z
sha256sum -c SHA256SUMS
```

恢复 real-device acceptance 需要：获支持的 NPU 与 driver/device node、冻结
兼容 CANN、获批多-rank launcher/rank-table 或 root-info、至少两个 ranks、
device/context/stream/memory 权限、communicator、每 rank API/cleanup trace、
D2H independent host reference，以及专用实机 evidence。当前这些条件未满足。

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
│   ├── src/                        # CPU 模拟通信器和 collective 算法
│   └── tests/                      # C 测试程序
├── scripts/
│   └── validate_linux_cpu_sim.sh    # Linux CPU_SIM 构建/CTest/Python 验证
├── docker/
│   └── linux-cpu-sim.Dockerfile     # Docker Desktop Linux 验证镜像
├── .github/workflows/
│   └── linux-cpu-sim.yml            # Linux CPU_SIM CI 配置
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

Windows 默认 CMake 配置应生成 `hccl_plugin.dll` 和 `hccl_plugin.lib`，并通过 CTest 发现 11 个 C 测试程序。

### Linux CPU_SIM 验证

```bash
bash scripts/validate_linux_cpu_sim.sh /tmp/hccl-agent-linux-review
```

Docker Desktop 可用时：

```cmd
docker build -f docker/linux-cpu-sim.Dockerfile -t hccl-agent-linux-cpu-sim:v1 .
docker run --rm -v "%CD%:/workspace" -w /workspace hccl-agent-linux-cpu-sim:v1 bash scripts/validate_linux_cpu_sim.sh
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
- [x] Python 单元测试覆盖
- [x] CPU 模拟 C 插件构建
- [x] AllReduce / AllGather / ReduceScatter CPU_SIM 数据正确性
- [x] AllReduce 多元素 buffer 与 ReduceScatter 2-rank 正确性
- [x] FP32 SUM/PROD/MAX/MIN、FP16/BF16 CPU 软件模拟
- [x] 固定 seed 随机 correctness suite
- [x] Linux CPU_SIM 验证脚本与 CI 配置
- [ ] Linux Docker `.so` 本地实测通过
- [ ] CANN/HCOMM/Ascend 实机验证

## 开发路线

### P0（已完成本次迭代）

- [x] 修复 Python 原型主流程
- [x] 补齐 README 和 Prompt 初版
- [x] 基础单元测试
- [x] 模拟器日志格式
- [x] primitive 全链路传递

### V1（本地已完成，Linux 环境阻塞）

- [x] 收敛文档事实、项目树和跨平台验证基线
- [x] 闭合标准 C wrapper 与 Python 调用边界
- [x] 实现 AllReduce 多元素、AllGather、ReduceScatter 2-rank CPU 数据正确性
- [x] 建立 FP32/FP16/BF16 固定 seed correctness 基线
- [x] 生成 Linux `.so` 验证脚本与 Linux CI workflow
- [ ] Docker Linux `.so` 实测通过（当前 `ENV_BLOCKED`）

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
