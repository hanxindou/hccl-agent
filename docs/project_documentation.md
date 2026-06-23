# 项目概述

当前项目是一个面向 HCCL 通信优化赛题的 Agent 工程。它用 Agent + Skills + Simulator 的方式，根据节点数、消息大小、集群配置和性能模型，选择候选通信算法、模拟性能得分、输出通信策略，并记录可复现的实验日志。

项目已从早期 Python 原型逐步扩展：新增了 C/C++ HCCL 插件骨架（接口声明真实，实现为桩）、拓扑图模型（加权有向图 + 路径计算）、故障注入模拟器、AgentPromptEngine、结构化日志与性能报告生成器。

# 项目整体架构

当前架构由 8 类模块组成：

1. **入口层**：main.py，CLI 参数解析 + 交互式输入。
2. **Agent 编排层**：agent/hccl_agent.py，串联配置加载 → 拓扑推断 → 拓扑图构建 → 算法选择 → 模拟评估 → 策略生成 → Prompt 记录 → 日志持久化。
3. **Skills 层**：skills/ 下 7 个模块，覆盖算法选择、拓扑推断、拓扑图建模、配置加载与校验、优化排序、性能评分、策略生成。
4. **模拟器层**：simulator/ 下 simulator.py（性能模拟）和 fault_injector.py（故障注入）。
5. **配置层**：config/cluster.json 存储 HCCS/RoCE/PCIe 链路参数、NUMA、HBM、UB 等昇腾关键参数。
6. **Prompt 层**：prompts/algorithm_prompt.txt（5 类 Prompt 模板），agent/prompt_engine.py（模板填充与调用日志）。
7. **C/C++ 插件骨架**：hcccl/ 目录，包含接口声明（真实 HCOMM API）、算法桩、CMakeLists.txt。
8. **工具与日志**：scripts/generate_report.py（性能报告生成），scripts/integration_test.sh（集成测试），logs/ 目录（实验日志 + Prompt 调用记录）。

逻辑调用关系：

```text
main.py
  -> HCCLAgent.run(nodes, message_size, primitive)
      -> ConfigSkill.load_cluster_info()
      -> TopologySkill.analyze(nodes) -> topology string
      -> _build_topology_graph(nodes, topology, cluster_info) -> TopologyGraph
      -> AlgorithmSkill.choose_algorithms(nodes, message_size, primitive)
      -> OptimizationSkill.optimize(simulator, cluster_info, candidates, ...)
          -> Simulator.evaluate(algorithm, topology, nodes, message_size,
                                primitive, bandwidth_gbps, latency_ms)
              -> PerformanceModel.calculate_score(latency, bandwidth)
      -> StrategySkill.generate(best_algorithm, nodes, primitive)
      -> AgentPromptEngine.build_algorithm_selection_prompt(params)
      -> ExperimentLogger.log_run(output)
      -> return output
```

# 项目执行流程

1. 用户运行 `main.py --nodes 8 --message-size 128 --primitive AllReduce`（或交互式输入）。
2. HCCLAgent 加载 `config/cluster.json`，校验并提取链路参数。
3. TopologySkill 根据节点数推断拓扑类型（Full Mesh / Ring / Fat Tree）。
4. HCCLAgent 构建 TopologyGraph（加权有向图），将图摘要写入输出。
5. AlgorithmSkill 根据消息大小五级粒度、节点数、原语类型选择候选算法。
6. OptimizationSkill 遍历候选算法，调用 Simulator 评估每个算法。
7. Simulator 使用 config 中的 bandwidth_gbps 和 latency_ms，结合算法步数模型、拓扑因子、原语因子计算 latency/bandwidth/score。
8. OptimizationSkill 选出 best_algorithm 并生成 ranking。
9. StrategySkill 根据 best_algorithm、nodes、primitive 生成通信步骤文本（区分 AllReduce 两阶段环、AllGather 单阶段、ReduceScatter 分片）。
10. AgentPromptEngine 填充算法选择 Prompt 模板，记录到 `logs/prompt_calls.jsonl`。
11. ExperimentLogger 记录完整运行到 `logs/runs.jsonl`，更新 `logs/summary.json`。
12. main.py 打印全部输出字段。

# 项目目录说明

```text
.
├── .gitignore
├── README.MD
├── main.py
├── agent/
│   ├── hccl_agent.py               # Agent 编排核心
│   ├── experiment_logger.py        # 结构化实验日志
│   └── prompt_engine.py            # Prompt 模板填充与日志
├── skills/
│   ├── algorithm_skill.py          # 算法选择（5级消息粒度 + primitive感知）
│   ├── config_skill.py             # 配置加载、校验、链路查询
│   ├── optimization_skill.py       # 候选算法评估与排名
│   ├── performance_model.py        # 综合评分模型
│   ├── strategy_skill.py           # 通信策略生成（primitive感知）
│   ├── topology_graph.py           # 加权图模型（路径计算）
│   └── topology_skill.py           # 拓扑类型推断
├── simulator/
│   ├── simulator.py                # 通信性能模拟器
│   └── fault_injector.py           # 故障注入与可靠性统计
├── hcccl/                          # C/C++ HCCL 插件骨架
│   ├── CMakeLists.txt
│   ├── README.md
│   ├── include/
│   │   ├── hccl_comm.h             # HCCL 接口声明（真实 HCOMM API）
│   │   └── hccl_algorithms.h       # 算法入口声明
│   ├── src/
│   │   ├── hccl_comm.c             # 通信器桩实现
│   │   └── hccl_algorithms.c       # 算法桩实现
│   └── tests/                      # 预留 C 测试目录
├── scripts/
│   ├── generate_report.py          # Markdown 性能报告生成
│   └── integration_test.sh         # 集成测试脚本
├── config/
│   └── cluster.json                # 扩展集群配置（HCCS/RoCE/PCIe等）
├── prompts/
│   └── algorithm_prompt.txt        # 5类Prompt模板
├── tests/
│   └── test_agent.py               # 47个单元测试
├── docs/
│   ├── project_documentation.md    # 本文件
│   ├── gap_analysis.md
│   ├── competition_analysis.md
│   ├── agent_capabilities.md       # Agent 能力清单
│   ├── simulator_guide.md          # 模拟器说明文档
│   └── 赛题.docx
└── logs/
    ├── runs.jsonl                  # 实验运行日志
    ├── summary.json                # 聚合统计
    ├── prompt_calls.jsonl          # Prompt 调用记录
    └── performance_report.md       # 性能报告
```

# 文件说明概要

（各文件详细说明见最初版本的项目文档，以下仅列出本次迭代变更）

## 新增文件（第二批 + 第三批）

- **`.gitignore`**：排除 `__pycache__/`、`logs/`、`*.pyc`、构建产物、IDE 配置。
- **`agent/experiment_logger.py`**：每次 Agent 运行追加 JSON-lines 记录，自动更新聚合统计。
- **`agent/prompt_engine.py`**：加载 Prompt 模板，填充 `{placeholders}`，记录到 `logs/prompt_calls.jsonl`。
- **`skills/topology_graph.py`**：加权有向图模型，支持 Full Mesh / Ring / Fat-Tree 构建，Dijkstra 最短延迟路径、最大瓶颈带宽路径、故障链路避让。
- **`simulator/fault_injector.py`**：4 种故障注入（link_down / timeout / corruption / congestion），基于 BER 的传输模拟，可靠性报告（重传率 ≤ 0.1% 目标）。
- **`scripts/generate_report.py`**：从 `logs/runs.jsonl` 生成 Markdown 性能报告（算法对比、原语分析、拓扑分布、消息大小分析）。
- **`scripts/integration_test.sh`**：11 个场景批量运行，自动校验输出结构完整性。
- **`hcccl/` 目录**：C/C++ HCCL 插件骨架（6 个文件），接口声明基于真实 HCOMM API，实现为桩。
- **`docs/agent_capabilities.md`**：赛题正式 Agent 能力清单（6 大类 12 个模块）。
- **`docs/simulator_guide.md`**：模拟器配置说明、性能模型公式、验证流程。

## 修改文件（三批迭代汇总）

- **`agent/hccl_agent.py`**：集成 TopologyGraph 构建、AgentPromptEngine 调用、primitive 全链路传递、拓扑图摘要输出。
- **`skills/algorithm_skill.py`**：五级消息粒度（≤64KB → ≥1GB），nodes 参与判断，primitive 影响候选（AllGather 增加 Butterfly，ReduceScatter 增加 Ring）。
- **`skills/config_skill.py`**：基于模块路径的绝对路径解析、必需字段校验、默认值填充、`get_link_by_type()` 链路查询、bandwidth_gbps/latency_ms 自动提取。
- **`skills/optimization_skill.py`**：primitive 参数透传，从 cluster_info 提取 bandwidth_gbps/latency_ms 传入 Simulator。
- **`skills/strategy_skill.py`**：Butterfly 动态 bit-flip 配对（非硬编码），primitive 感知（AllReduce 两阶段环 / AllGather 单阶段 / ReduceScatter 分片），Mesh 策略生成。
- **`simulator/simulator.py`**：使用 config 带宽/延迟参数，primitive 感知因子，6 种算法独立模型（含新增 PairWise/NHR/Fat-Tree），拓扑因子调整。
- **`config/cluster.json`**：新增 `links[]`（HCCS/RoCE/PCIe + BER）、`numa`、`hbm`、`ub` 字段，算法列表扩展。
- **`tests/test_agent.py`**：从 3 个扩展到 47 个测试，覆盖 7 个测试类。
- **`prompts/algorithm_prompt.txt`**：5 类 Prompt 模板（算法选择/代码生成/测试生成/性能分析/可靠性机制）。
- **`README.MD`**：完整项目介绍、架构图、快速开始、开发路线。

# 参数说明

## nodes
含义：节点或卡数量。
当前用途：AlgorithmSkill、Simulator、StrategySkill、TopologySkill、TopologyGraph 均使用。
风险：与 config/cluster.json 中 nodes 字段无一致性校验（runtime_cluster_info 覆盖）。

## message_size
含义：消息大小，main.py 单位为 MB，支持浮点数（如 0.03 = 30KB）。
当前用途：AlgorithmSkill 五级粒度判断，Simulator 计算 latency/bandwidth。
风险：赛题要求覆盖 <=64KB 和 >=1GB，当前已支持。

## primitive
含义：集合通信原语。
当前取值：AllReduce、AllGather、ReduceScatter。
当前用途：全链路透传 —— AlgorithmSkill 候选调整、Simulator 原语因子、StrategySkill 阶段描述、AgentPromptEngine 模板填充、输出和日志记录。

## topology
含义：集群拓扑，TopologySkill 推断 + TopologyGraph 建模。
当前用途：Simulator 拓扑因子、StrategySkill 策略选择、Agent 输出。

## algorithm
含义：通信算法名称，当前 6 种：Ring AllReduce、Butterfly、PairWise、NHR、Mesh、Fat-Tree。

# 当前已实现功能（汇总三批迭代）

1. 静态集群配置加载、校验与链路参数查询（HCCS/RoCE/PCIe + BER/NUMA/HBM/UB）。
2. 五级消息粒度算法选择（≤64KB / ≤1MB / ≤512MB / ≤1GB / >1GB），nodes 和 primitive 参与判断。
3. 三种集合通信原语全链路支持（AllReduce / AllGather / ReduceScatter）。
4. 拓扑推断（Full Mesh / Ring / Fat Tree） + 拓扑图建模（加权有向图，Dijkstra 路径计算）。
5. 6 种算法性能模拟（使用 config 带宽/延迟，primitive 感知，拓扑因子）。
6. Butterfly 动态配对（bit-flip），primitive 感知的通信策略生成。
7. 故障注入模拟（4 种故障类型，BER 传输模拟，可靠性报告）。
8. 结构化实验日志（JSON-lines + summary），Prompt 调用记录。
9. Markdown 性能报告自动生成。
10. CLI 非交互式运行入口，集成测试脚本（11 场景）。
11. 47 个单元测试（7 个测试类）。
12. C/C++ HCCL 插件骨架（接口声明真实，实现为桩，需 CANN SDK 编译）。
13. Agent 能力清单文档 + 模拟器说明文档。
14. README + Prompt 初版。

# 后续开发计划

## P0（部分完成）

- [x] C/C++ 插件 CPU 模拟编译 — 通信基础设施可在普通 Linux 上编译和测试，零 CANN 依赖
- [ ] 获取 CANN 8.0 SDK，在实机上编译并替换为 HCOMM 驱动调用
- [ ] 实现至少一种原语的真实通信逻辑（如 Ring AllReduce）

## P1

- [ ] 对接 HCOMM 真实拓扑探测
- [ ] 将 PrompEngine 接入 LLM API，实现真正的 Agent 代码生成
- [ ] 实机性能校准

# 本次迭代记录

## 2026-06-13（第一批）：primitive 全链路 + 算法粒度 + 日志 + README

（详见之前迭代记录）

## 2026-06-14（第二批）：拓扑图 + 故障注入 + 文档 + 报告生成

（详见之前迭代记录）

## 2026-06-14（第三批）：C/C++ 骨架 + TopologyGraph + PromptEngine + 集成测试

新增文件：
1. hcccl/ 目录（6 个文件）：C/C++ HCCL 插件骨架
2. agent/prompt_engine.py：Prompt 模板填充与调用日志
3. scripts/integration_test.sh：11 场景集成测试

修改文件：
1. agent/hccl_agent.py：集成 TopologyGraph 构建、PromptEngine 调用、primitive 传入 StrategySkill
2. skills/strategy_skill.py：primitive 感知的三阶段策略生成（AllReduce 两阶段环 / AllGather / ReduceScatter / Mesh）
3. tests/test_agent.py：更新 ring 测试以匹配新策略格式，新增 2 个 primitive 策略测试

新增函数：
1. HCCLAgent._build_topology_graph()
2. StrategySkill._generate_ring() / _generate_butterfly() / _generate_mesh() / _generate_generic()
3. AgentPromptEngine 全部方法

测试结果：47 单元测试全部通过，11 集成场景全部通过。


## 2026-06-14（第四批）：CPU 模拟通信基础设施 — hcclCommInit / hcclCommDestroy / hcclGetTopology

修改文件：
1. `hcccl/src/hccl_comm.c`：实现三个通信基础设施函数（不再返回 NOT_SUPPORTED）
2. `hcccl/CMakeLists.txt`：移除 CANN SDK 依赖，新增 `test_topology` 可执行文件目标

新增文件：
1. `hcccl/tests/test_topology.c`：9 个测试用例，验证 communicator 生命周期和 Full Mesh 拓扑生成

新增内部结构体：
1. `hcclCommInternal`（定义在 .c 文件中，不暴露）：
   - `num_devices`（int32_t）：通信器内的设备/卡数量
   - `device_ids`（int32_t*）：设备 ID 数组，长度等于 num_devices
   - 作用：hcclCommInit 分配并填充该结构体，通过 `void*`（hcclComm_t）返回给调用者；
     hcclCommDestroy 释放它；hcclGetTopology 读取 num_devices 生成正确规模的模拟拓扑

新增 / 修改函数实现：
1. **hcclCommInit(comm, num_devices, device_ids)**：
   - 参数校验（NULL 指针、num_devices≤0 → HCCL_ERR_INVALID_ARG）
   - malloc hcclCommInternal + malloc device_ids 数组
   - memcpy device_ids，*comm = ctx
   - 返回 HCCL_SUCCESS
   - 不依赖任何 CANN/HCOMM API，纯 CPU 内存分配

2. **hcclCommDestroy(comm)**：
   - NULL 检查 → HCCL_ERR_INVALID_ARG
   - free(ctx->device_ids)，free(ctx)
   - 返回 HCCL_SUCCESS

3. **hcclGetTopology(comm, topo)**：
   - 参数校验
   - 生成模拟 Full Mesh：N 设备 → N*(N-1) 条有向链路（无自环）
   - 每条链路：link_type="HCCS"，bandwidth_gbps=100，latency_us=1，ber=1e-12，healthy=1
   - 分配 hcclTopology_t + hcclLinkInfo_t 数组
   - 返回 HCCL_SUCCESS

编译命令：
```bash
cd hcccl && mkdir -p build && cd build
cmake ..
make
# 产物：libhccl_plugin.so（共享库）+ test_topology（测试可执行文件）
```

运行测试命令：
```bash
cd hcccl/build
./test_topology
# 预期输出：9 run, 9 passed, 0 failed
```

验证无 CANN 依赖：
```bash
ldd hcccl/build/libhccl_plugin.so
# 输出应仅含 linux-vdso、libc、ld-linux，无任何 Ascend/CANN 库
```

测试结果：9/9 C 测试通过，libhccl_plugin.so 仅依赖 libc。


## 2026-06-14（第五批）：Ring AllReduce CPU 模拟版

### 目标

在 CPU 模拟框架上实现 Ring AllReduce 算法，验证 ReduceScatter + AllGather 两阶段环形通信逻辑，不依赖 Ascend SDK / CANN / MPI / 线程。

### Ring AllReduce 原理

Ring AllReduce 将 N 个 rank 排列成单向环，在 2×(N−1) 步内完成全局归约：

**Phase 1 — Reduce (N-1 步):**
每个 rank 维护两个 buffer：
-  — 累加器，最终收敛到全局和
-  — 传递给下一个 rank 的值

每步：rank i 将 forward[i] 发送给 (i+1)%N，从 (i-1+N)%N 接收值存入 forward[i] 并累加到 partial[i]。关键性质：每个原始值在环上恰好传播一圈后回到原点，不会重复累加。

**Phase 2 — AllGather (N-1 步):**
将 Phase 1 结束后的 partial 复制到 forward 作为起点，再执行 N-1 步循环（只替换不累加），确保所有 rank 得到一致结果。

### 为什么采用 CPU 模拟实现

- 赛题要求 Agent 完成算法设计，CPU 模拟是验证算法逻辑正确性的最快路径
- 无需昇腾硬件或 CANN SDK，可在任何 Linux 机器上编译运行
- 算法逻辑（环形数据流、双 buffer 设计）与真实 HCCL 实现一致，仅数据搬运方式不同

### 当前限制

- 仅支持  数据类型，其他返回 
- 仅支持  ReduceOp，其他返回 
- 仅支持 count == 1（每个 rank 一个 float），多元素返回 
- 最多支持 64 个 rank（栈上 buffer 限制）
- 不涉及真实网络传输、RDMA、流水线等

### 新增文件

1.  — 6 个测试用例：
   - 4 rank [1,2,3,4] → 期望 10
   - 8 rank [1..8] → 期望 36
   - 非法数据类型 → 
   - 非法 ReduceOp → 
   - NULL send_buf / recv_buf → 

### 修改文件

1.  — 新增  声明（CPU simulation helper 区域）
2.  — 扩展 （+current_rank / rank_values / rank_results / calls_received），更新 （+calloc 模拟 buffer）和 （+释放），实现 
3.  — 替换  桩为 CPU 实现（参数校验 → 存储输入 → 两阶段环形模拟 → 返回结果），其他算法保持桩不变
4.  — 新增  目标

### 编译命令

```bash
cd hcccl && mkdir -p build && cd build
cmake .. && make
# 产物：libhccl_plugin.so + test_topology + test_ring
```

### 运行测试命令

```bash
cd hcccl/build
./test_topology   # 通信基础设施测试（9 项）
./test_ring       # Ring AllReduce 测试（6 项）
```

### 预期输出结果

```
./test_ring
 4 ranks [1,2,3,4] → all get 10                     PASS
 8 ranks [1..8] → all get 36                        PASS
 FP16 data type → HCCL_ERR_NOT_SUPPORTED            PASS
 PROD ReduceOp → HCCL_ERR_NOT_SUPPORTED             PASS
 NULL send_buf → HCCL_ERR_INVALID_ARG               PASS
 NULL recv_buf → HCCL_ERR_INVALID_ARG               PASS
 Results: 6 run, 6 passed, 0 failed
```

测试结果：15/15 C 测试通过（9 topology + 6 ring），libhccl_plugin.so 仅依赖 libc。


## 2026-06-14（第六批）：Plugin Bridge — Python ↔ libhccl_plugin.so 闭环

### 设计目标

建立 Python Agent 与 C 动态库之间的第一条真实调用链路：

```
Agent (Python)
    │
    ▼
Plugin Bridge (ctypes)
    │
    ▼
libhccl_plugin.so (C)
    │
    ▼
hcclPluginGetVersion() / hcclPluginGetAlgorithms()
```

通过 ctypes 加载已编译的 `.so` 文件，调用其中已有的插件发现函数，使 Python 层可以读取 C 层的版本号和算法能力列表。

### ctypes 工作原理

`ctypes` 是 Python 标准库模块，用于加载 C 动态库并调用其中的函数，无需编写 C 扩展或使用 Cython。

关键步骤：
1. `ctypes.CDLL(path)` 加载 `.so` 文件，返回库对象
2. 为每个 C 函数设置 `argtypes`（参数类型列表）和 `restype`（返回类型）
3. `c_char_p` 类型自动将 C 的 `const char*` 转换为 Python `bytes`，再 `.decode("utf-8")` 得到 `str`

示例：
```python
lib = ctypes.CDLL("libhccl_plugin.so")
lib.hcclPluginGetVersion.argtypes = []
lib.hcclPluginGetVersion.restype = ctypes.c_char_p
version = lib.hcclPluginGetVersion().decode("utf-8")
# → "0.1.0-prototype"
```

### 新增文件

1. **`plugin/hccl_bridge.py`** — `HCCLBridge` 类：
   - `load_library()` — idempotent 加载，设置 argtypes/restype
   - `get_version()` → str — 调用 `hcclPluginGetVersion()`
   - `get_algorithms()` → str — 调用 `hcclPluginGetAlgorithms()`
   - `_find_library()` — 自动定位 `hcccl/build/libhccl_plugin.so`
   - 文件不存在时抛出 `FileNotFoundError` 并附带编译指引

2. **`agent/plugin_capability.py`** — 轻量辅助模块：
   - `parse_algorithm_list(raw)` — 将 "RingAllReduce,Butterfly,..." 拆分为 Python list
   - `map_algorithm_name(name)` — 将紧凑名（"RingAllReduce"）映射为可读名（"Ring AllReduce"）

3. **`tests/test_plugin_bridge.py`** — 10 个测试用例：
   - 库加载成功 / 文件不存在抛出异常
   - 版本号非空 / 类型正确
   - 算法列表包含 RingAllReduce / 非空
   - 算法字符串解析 / 空字符串处理
   - 算法名称映射 / 未知名称透传
   - 打印能力清单（人工检查）

### 编译步骤

```bash
# 1. 编译 C 动态库（如果尚未编译）
cd hcccl && mkdir -p build && cd build
cmake .. && make
# 产物：libhccl_plugin.so

# 2. 无需额外步骤 — Python 端通过 ctypes 直接加载
```

### 测试步骤

```bash
# C 测试（确保动态库正常）
cd hcccl/build
./test_topology
./test_ring

# Python 桥接测试
cd ../..
python3 -m unittest tests.test_plugin_bridge -v
```

### 测试预期结果

```
$ python3 -m unittest tests.test_plugin_bridge -v
test_get_algorithms_contains_ring ... ok
test_get_algorithms_non_empty ...... ok
test_get_version_non_empty ......... ok
test_get_version_returns_str ....... ok
test_load_library_succeeds ......... ok
test_map_algorithm_name ............ ok
test_missing_library_raises ........ ok
test_parse_algorithm_list .......... ok
test_parse_empty_string ............ ok
test_print_capabilities ............ ok

Plugin Version:
  0.1.0-prototype

Algorithms (raw):
  RingAllReduce,Butterfly,Mesh,NHR,FatTree

Algorithms (parsed):
  - Ring AllReduce
  - Butterfly
  - Mesh
  - NHR
  - Fat-Tree

Ran 10 tests in 0.001s
OK
```

### 当前项目架构图

```
┌─────────────────────────────────────────────────┐
│  main.py  (CLI: --nodes --message-size ...)      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  agent/hccl_agent.py  (Orchestration)            │
│    ├─ ConfigSkill      ├─ OptimizationSkill      │
│    ├─ TopologySkill    ├─ StrategySkill          │
│    ├─ AlgorithmSkill   ├─ ExperimentLogger       │
│    └─ TopologyGraph    └─ AgentPromptEngine      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  plugin/hccl_bridge.py  (ctypes bridge)          │
│    ├─ get_version()                              │
│    └─ get_algorithms()                           │
└──────────────────┬──────────────────────────────┘
                   │  ctypes.CDLL
┌──────────────────▼──────────────────────────────┐
│  hcccl/build/libhccl_plugin.so  (C shared lib)   │
│    ├─ hcclPluginGetVersion()                     │
│    ├─ hcclPluginGetAlgorithms()                  │
│    ├─ hcclCommInit / hcclCommDestroy             │
│    ├─ hcclGetTopology / hcclSetRank              │
│    └─ ring_allreduce  (CPU-simulated)            │
└─────────────────────────────────────────────────┘
```

测试结果：57 Python + 15 C = 72 测试全部通过。


## 2026-06-14（第七批）：Agent ↔ Plugin 集成 — 能力发现

### 目标

让 Agent 首次真正使用 Plugin，形成完整的能力发现闭环：

```
Agent
  │
  ▼
PluginManager
  │
  ▼
HCCLBridge (ctypes)
  │
  ▼
libhccl_plugin.so
  │
  ▼
hcclPluginGetVersion() / hcclPluginGetAlgorithms()
```

### PluginManager 设计

`agent/plugin_manager.py` — `PluginManager` 类：

- 持有 `HCCLBridge` 实例
- `discover()` 方法组合 bridge + capability 解析，返回结构化 dict：
  ```python
  {
      "version": "0.1.0-prototype",
      "algorithms": ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"],
      "raw_algorithms": "RingAllReduce,Butterfly,Mesh,NHR,FatTree",
      "library_path": "/.../libhccl_plugin.so",
  }
  ```

### Agent 与 Plugin 交互流程

1. `HCCLAgent.__init__()` → 创建 `PluginManager` 实例
2. `HCCLAgent.run()` → 调用 `plugin_manager.discover()` 获取插件能力
3. 结果写入 `output["plugin"]`，与 Simulator 结果并列输出
4. 不破坏现有逻辑：Simulator、StrategySkill、Logger 等全部保持不变

### 修改文件

1. **`agent/plugin_manager.py`** — 新文件。`PluginManager` 类封装 bridge + 解析
2. **`agent/hccl_agent.py`** — 3 处最小改动：
   - 新增 `from agent.plugin_manager import PluginManager`
   - `__init__` 中新增 `self.plugin_manager = PluginManager()`
   - `run()` 中新增 `plugin_info = self.plugin_manager.discover()` 并写入 `output["plugin"]`
3. **`tests/test_plugin_manager.py`** — 新文件。8 个测试用例

### 测试命令

```bash
python3 -m unittest tests/test_plugin_manager -v
```

### 测试结果

```
$ python3 -m unittest tests.test_plugin_manager -v
test_discover_algorithms_non_empty ... ok
test_discover_contains_ring_allreduce ... ok
test_discover_library_path ........... ok
test_discover_raw_algorithms ......... ok
test_discover_returns_dict ........... ok
test_discover_version_non_empty ...... ok
test_manager_initializes ............. ok
test_print_capability_report ......... ok

Plugin Version:
  0.1.0-prototype

Supported Algorithms:
  - Ring AllReduce
  - Butterfly
  - Mesh
  - NHR
  - Fat-Tree

Ran 8 tests in 0.001s
OK
```

### 当前架构图

```
┌─────────────────────────────────────────────────┐
│  main.py  (CLI: --nodes --message-size ...)      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  agent/hccl_agent.py  (Orchestration)            │
│    ├─ ConfigSkill       ├─ OptimizationSkill     │
│    ├─ TopologySkill     ├─ StrategySkill         │
│    ├─ AlgorithmSkill    ├─ ExperimentLogger      │
│    ├─ TopologyGraph     ├─ AgentPromptEngine     │
│    └─ PluginManager ───────────────────┐         │
└────────────────────────────────────────┼─────────┘
                                         │
┌────────────────────────────────────────▼─────────┐
│  agent/plugin_manager.py  (Capability discovery)  │
│    ├─ HCCLBridge.load_library()                  │
│    └─ plugin_capability.parse / map              │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│  plugin/hccl_bridge.py  (ctypes wrapper)          │
│    ├─ get_version()     → const char*             │
│    └─ get_algorithms()  → const char*             │
└────────────────────┬─────────────────────────────┘
                     │  ctypes.CDLL
┌────────────────────▼─────────────────────────────┐
│  hcccl/build/libhccl_plugin.so  (C shared lib)    │
│    ├─ hcclPluginGetVersion()                     │
│    ├─ hcclPluginGetAlgorithms()                  │
│    ├─ hcclCommInit / hcclCommDestroy             │
│    ├─ hcclGetTopology / hcclSetRank              │
│    └─ ring_allreduce  (CPU-simulated)            │
└──────────────────────────────────────────────────┘
```

测试结果：65 Python + 15 C = 80 测试全部通过。


## 2026-06-14（第八批）：Agent Execution Framework — 首次真正执行 Ring AllReduce

### 目标

让 Agent 第一次真正执行插件中的算法，形成从决策到计算的完整闭环：

```
Agent
  │
  ├── PluginManager  (能力发现)
  ├── AlgorithmSkill (算法选择)
  │
  └── ExecutionSkill ──→ ExecutionEngine ──→ PluginBridge
                                                 │
                                          libhccl_plugin.so
                                                 │
                                          ring_allreduce()
                                                 │
                                          [10, 10, 10, 10]
```

### Execution Engine 设计

`plugin/execution_engine.py` — `ExecutionEngine` 类：

- 通过 ctypes 加载 `libhccl_plugin.so`，绑定 4 个 C 函数：
  - `hcclCommInit` — 创建 communicator
  - `hcclCommDestroy` — 销毁 communicator
  - `hcclSetRank` — 设置当前 rank
  - `ring_allreduce` — 执行 Ring AllReduce
- `execute_algorithm(name, data)` 方法：
  - 将 Agent 算法名映射到内部 key
  - 仅 `ring` 已实现；Butterfly/Mesh/NHR/Fat-Tree 返回 `not_implemented`
  - 未知算法返回 `unknown_algorithm`
  - 空输入返回 `invalid_input`
- Ring AllReduce 执行流程（两阶段）：
  1. 创建 N-rank communicator
  2. Pass 1：逐个 rank 调用 `ring_allreduce` 提交输入值
  3. Pass 2：逐个 rank 调用 `ring_allreduce` 获取归约结果
  4. 销毁 communicator，返回结果列表

### Agent 执行流程

1. `HCCLAgent.__init__()` → 创建 `ExecutionSkill` 实例
2. `HCCLAgent.run_execution_demo(algorithm, input_data)` → 调用 `execution_skill.execute()`
3. 与 `run()` 完全独立，不破坏现有 Simulator 逻辑

### 新增文件

1. **`plugin/execution_engine.py`** — `ExecutionEngine`：ctypes 绑定 + 两阶段执行
2. **`agent/execution_skill.py`** — `ExecutionSkill`：Agent 侧薄封装
3. **`tests/test_execution_engine.py`** — 8 个测试用例：
   - 4 rank [1,2,3,4] → [10,10,10,10]
   - 8 rank [1..8] → [36]*8
   - Butterfly/Mesh/NHR/Fat-Tree → not_implemented
   - unknown algorithm → unknown_algorithm
   - empty input → invalid_input
4. **`tests/test_execution_skill.py`** — 5 个测试用例

### 修改文件

1. **`agent/hccl_agent.py`** — 3 处最小改动：
   - import ExecutionSkill
   - `__init__` 中创建 `self.execution_skill`
   - 新增 `run_execution_demo()` 方法（与 `run()` 独立）

### 测试命令

```bash
python3 -m unittest tests/test_execution_engine -v
python3 -m unittest tests/test_execution_skill -v
```

### 测试结果

```
test_ring_allreduce_4_ranks ..... ok
test_ring_allreduce_8_ranks ..... ok
test_butterfly_not_implemented .. ok
test_mesh_not_implemented ....... ok
test_nhr_not_implemented ........ ok
test_fat_tree_not_implemented ... ok
test_unknown_algorithm .......... ok
test_empty_input ................ ok
Ran 8 tests ... OK

test_execute_ring_allreduce_success ... ok
test_execute_not_implemented .......... ok
test_execute_unknown_algorithm ........ ok
test_execute_preserves_algorithm_name . ok
test_execute_empty_input .............. ok
Ran 5 tests ... OK
```

### 当前项目架构图

```
┌─────────────────────────────────────────────────────────┐
│  main.py  (CLI: --nodes --message-size ...)              │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  agent/hccl_agent.py  (Orchestration)                    │
│    ├─ ConfigSkill         ├─ OptimizationSkill           │
│    ├─ TopologySkill       ├─ StrategySkill               │
│    ├─ AlgorithmSkill      ├─ ExperimentLogger            │
│    ├─ TopologyGraph       ├─ AgentPromptEngine           │
│    ├─ PluginManager       └─ ExecutionSkill ───────┐     │
│    └─ run_execution_demo()                         │     │
└────────────────────────────────────────────────────┼─────┘
                                                     │
┌────────────────────────────────────────────────────▼─────┐
│  agent/execution_skill.py                                │
│    └─ ExecutionSkill.execute(algorithm, data)            │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  plugin/execution_engine.py                              │
│    ├─ ctypes bindings:                                   │
│    │    hcclCommInit / hcclCommDestroy                   │
│    │    hcclSetRank / ring_allreduce                     │
│    └─ execute_algorithm(name, data)                      │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  plugin/hccl_bridge.py  (plugin discovery)               │
└────────────────────────┬─────────────────────────────────┘
                         │  ctypes.CDLL
┌────────────────────────▼─────────────────────────────────┐
│  hcccl/build/libhccl_plugin.so  (C shared library)        │
│    ├─ hcclPluginGetVersion / hcclPluginGetAlgorithms     │
│    ├─ hcclCommInit / hcclCommDestroy / hcclSetRank       │
│    ├─ hcclGetTopology / hcclFreeTopology                 │
│    └─ ring_allreduce  ← 首次真正执行 ✓                   │
└──────────────────────────────────────────────────────────┘
```

测试结果：78 Python + 15 C = 93 测试全部通过。


## 2026-06-14（第九批）：Self Evaluation Framework — 自动评价与报告生成

### 目标

让 Agent 在执行算法后自动评价性能并生成可读报告，形成完整闭环：

```
Agent
  │
  ├── ExecutionSkill  → 执行算法
  ├── EvaluationSkill → 评价性能
  └── ReportGenerator → 生成报告
```

### EvaluationSkill 设计

`agent/evaluation_skill.py` — `EvaluationSkill` 类：

基于 score 的四级评分制：

| score 范围 | Grade | Recommendation |
|-----------|-------|----------------|
| >= 70 | EXCELLENT | Current algorithm performs very well. |
| 50 – 70 | GOOD | Keep current algorithm. |
| 30 – 50 | FAIR | Consider trying another algorithm. |
| < 30 | POOR | Strongly recommend algorithm replacement. |

输入：Simulator 输出的 performance dict（含 `score` 字段）
输出：`{"grade": "GOOD", "recommendation": "..."}`

### ReportGenerator 设计

`agent/report_generator.py` — `ReportGenerator` 类：

将 execution result 和 evaluation result 格式化为多行文本报告，包含 6 个段落：
Algorithm / Latency / Bandwidth / Score / Evaluation / Recommendation

### Agent 执行→评价→报告流程

`HCCLAgent.generate_execution_report(algorithm, input_data)`:

1. **Execution**: 调用 `execution_skill.execute()` → C plugin 执行
2. **Simulation**: 调用 `simulator.evaluate()` → 获取 latency/bandwidth/score
3. **Evaluation**: 调用 `evaluation_skill.evaluate()` → 评级
4. **Report**: 调用 `report_generator.generate_report()` → 文本报告

与 `run()` 和 `run_execution_demo()` 完全独立，不破坏兼容性。

### 新增文件

1. **`agent/evaluation_skill.py`** — `EvaluationSkill`：4 级评分制
2. **`agent/report_generator.py`** — `ReportGenerator`：文本报告格式化
3. **`logs/sample_execution_report.txt`** — 示例输出
4. **`tests/test_evaluation_skill.py`** — 10 个测试：EXCELLENT/GOOD/FAIR/POOR + 边界值 + 缺失字段
5. **`tests/test_report_generator.py`** — 3 个测试：关键字段存在、完整内容、缺失处理
6. **`tests/test_execution_report_flow.py`** — 4 个测试：完整 Execution→Evaluation→Report 链路

### 修改文件

1. **`agent/hccl_agent.py`** — 3 处最小改动：
   - import EvaluationSkill / ReportGenerator
   - `__init__` 中创建实例
   - 新增 `generate_execution_report()`

### 测试命令

```bash
python3 -m unittest tests/test_evaluation_skill -v
python3 -m unittest tests/test_report_generator -v
python3 -m unittest tests/test_execution_report_flow -v
```

### 测试结果

```
test_evaluation_skill   — 10 tests ... OK
test_report_generator   —  3 tests ... OK
test_execution_report_flow — 4 tests ... OK
```

### 示例输出

```
Execution Report
=================

Algorithm:
  Ring AllReduce

Latency:
  0.012 ms

Bandwidth:
  12.5 GB/s

Score:
  8.75

Evaluation:
  POOR

Recommendation:
  Strongly recommend algorithm replacement.
```

### 当前项目架构图

```
┌──────────────────────────────────────────────────────────────────┐
│  main.py  (CLI)                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│  agent/hccl_agent.py                                             │
│    ├─ run()                     ├─ run_execution_demo()          │
│    └─ generate_execution_report()  ← NEW                        │
│         │                              │                         │
│         ▼                              ▼                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐       │
│  │ ExecutionSkill│  │EvaluationSkill│  │ ReportGenerator  │       │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘       │
│         │                             (NEW)          (NEW)       │
└─────────┼───────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────┐
│  plugin/execution_engine.py  (ctypes)                            │
└─────────┬───────────────────────────────────────────────────────┘
          │  ctypes.CDLL
┌─────────▼───────────────────────────────────────────────────────┐
│  hcccl/build/libhccl_plugin.so                                   │
│    └─ ring_allreduce()  (CPU-simulated)                          │
└──────────────────────────────────────────────────────────────────┘
```

测试结果：95 Python + 15 C = 110 测试全部通过。


## 2026-06-14（第十批）：DeepSeek Reasoning Layer — LLM 推理能力接入

### 目标

让 Agent 首次具备真实大模型推理能力。DeepSeek 作为增强层分析候选算法，但**不替代**现有规则系统。

```
Agent
  │
  ├── AlgorithmSkill  (规则选择 → candidates)
  ├── ReasoningSkill  (DeepSeek 分析 → recommendation + reasoning)
  └── OptimizationSkill (Simulator 排名 → best_algorithm)
```

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/llm_client.py` | DeepSeek OpenAI-compatible API 客户端。仅依赖 `urllib`（标准库），零第三方依赖。`ask(prompt)` → `str` |
| `agent/reasoning_skill.py` | 封装 LLMClient，构造算法分析 Prompt，解析回复中的 Recommendation / Reasoning |
| `tests/test_llm_client.py` | 7 个测试：成功/空Key/空choices/HTTP错误/URL错误/system prompt/env fallback |
| `tests/test_reasoning_skill.py` | 6 个测试：解析推荐/参数传递/空响应/自由格式/客户端异常 |
| `docs/deepseek_setup.md` | DeepSeek API Key 配置指南 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/hccl_agent.py` | 3 处：import ReasoningSkill → `__init__` 创建实例 → `run()` 中 try/except 调用 → `output["reasoning"]` |

### 类图

```
LLMClient                          ReasoningSkill
├── ask(prompt, system_prompt)     ├── analyze(nodes, msg_size,
│   → str                          │           topology, candidates)
│                                  │   → {"recommendation": "...",
└── uses urllib.request            │       "reasoning": "..."}
    + DEEPSEEK_API_KEY env var     │
                                   └── uses LLMClient
                                       + structured prompt template
```

### 调用链路

```
HCCLAgent.run()
  │
  ├── candidate_algorithms = AlgorithmSkill.choose_algorithms(...)
  │
  ├── try:
  │     reasoning_result = ReasoningSkill.analyze(
  │         nodes, message_size, topology, candidate_algorithms
  │     )
  │   except:  # API key unset or network down
  │     reasoning_result = None    ← graceful degradation
  │
  ├── best_algorithm, ... = OptimizationSkill.optimize(...)
  │
  └── output["reasoning"] = reasoning_result
```

### Prompt 设计

```
System: You are an expert in distributed collective-communication
        algorithms for Ascend NPU clusters.

User:   Analyse the following HCCL communication scenario...
        Nodes: {nodes}
        Message Size: {message_size} MB
        Topology: {topology}
        Candidate algorithms:
        - Ring AllReduce
        - Butterfly
        - Mesh
        Please recommend the best algorithm and explain why.

Model:  Recommendation: Ring AllReduce
        Reasoning: Ring provides balanced bandwidth and latency...
```

### 环境变量配置

```bash
export DEEPSEEK_API_KEY=sk-your-key-here
```

未设置时 Agent 静默跳过 LLM 推理，规则系统照常工作。

### 测试结果

```
test_llm_client:       7 tests PASS (mock)
test_reasoning_skill:  6 tests PASS (mock)
Existing tests:       95 tests PASS (unchanged)
Total:               108 Python + 15 C = 123 tests PASS
```

### 示例输入输出

```python
>>> agent = HCCLAgent()
>>> out = agent.run(nodes=8, message_size=128, primitive="AllReduce")
>>> print(out["reasoning"])
{
    "recommendation": "Ring AllReduce",
    "reasoning": "Ring provides the best balance of bandwidth and latency..."
}
# None if DEEPSEEK_API_KEY not set.
```

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 通信基础设施 | ✅ |
| C Ring AllReduce (CPU) | ✅ |
| Python ↔ C Bridge | ✅ |
| Plugin 能力发现 | ✅ |
| Agent 执行 Ring AllReduce | ✅ |
| **Agent 自动评价与报告** | **✅ 本轮完成** |
| Butterfly / Mesh / NHR / Fat-Tree | ⬜ 未实现 |
| 真实 CANN / HCOMM 对接 | ⬜ 待 SDK |
| LLM Agent 代码生成 | ⬜ 待后续 |

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 通信基础设施 (comm/topology) | ✅ 完成 |
| C Ring AllReduce (CPU 模拟) | ✅ 完成 |
| Python ↔ C Bridge (ctypes) | ✅ 完成 |
| Plugin 能力发现 | ✅ 完成 |
| **Agent 执行 Ring AllReduce** | **✅ 本轮完成** |
| Butterfly / Mesh / NHR / Fat-Tree | ⬜ 未实现 |
| 真实 CANN / HCOMM 对接 | ⬜ 待 SDK |
| LLM Agent 代码生成 | ⬜ 待后续 |



## 2026-06-14（第十一批）：Performance Model Refactor — 标准化评分与竞争模型

### 修改原因

旧模型 `score = bandwidth * 0.7 - latency * 0.3` 存在三个严重缺陷：
1. latency(ms) 与 bandwidth(GB/s) 单位不同，score 无固定范围
2. 所有算法带宽完全相同，无法区分
3. Mesh 因 O(1) 步数永远获胜，不符合真实场景

### PerformanceModel 新设计

标准化 0~100 评分体系：

```
bandwidth_score = min(bandwidth_gb_s / theoretical_max * 100, 100)
latency_score   = max(0, 100 - latency_ms * 1000)
final_score     = bandwidth_score * 0.4 + latency_score * 0.6
```

- 带宽以链路理论上限为满分基准
- 延迟每 0.001ms 扣 1 分（penalty=1000），0.1ms 以上归零
- 延迟权重 0.6 > 带宽权重 0.4，优先奖励低延迟

### Algorithm Efficiency 模型

不同算法对链路带宽的利用效率不同：

| 算法 | Efficiency | 原因 |
|------|-----------|------|
| NHR | 0.92 | 非均匀环优化 |
| Ring AllReduce | 0.90 | 流水线环，带宽利用率高 |
| Fat-Tree | 0.88 | 层级开销 |
| Mesh | 0.88 | 高并发但 O(N²) 链路使用 |
| Butterfly | 0.85 | 递归加倍，对带宽要求低 |
| PairWise | 0.82 | 逐对交换，效率最低 |

带宽计算：
```
effective_bw = link_bw * algo_efficiency * primitive_factor * bw_contention
```

### Contention Model

**延迟竞争（算法感知）**：
- Mesh: `latency *= 1 + nodes * 0.15`（N-1 并发发送导致 NIC 队列深度）
- Fat-Tree: `latency *= 1 + nodes * 0.04`（仅跨机架层有竞争）
- Ring / Butterfly / NHR: 无竞争（串行化通信）

**带宽竞争（Mesh 专有）**：
- Mesh: `bw /= 1 + (nodes-1) * 0.12`（每个链路被 N-1 个对等方共享）
- Fat-Tree: `bw /= 1 + (nodes-1) * 0.04`（仅跨机架层）
- Ring / Butterfly / NHR: 无竞争

**Mesh 有效步数**：
- `steps = 1 + nodes * 0.15`（1 个逻辑轮次 + 队列深度开销）

### 修改文件

| 文件 | 改动 |
|------|------|
| `skills/performance_model.py` | 重写评分公式：0-100 范围，双维度标准化 |
| `simulator/simulator.py` | 新增 ALGORITHM_EFFICIENCY / BW_CONTENTION_COEFF / MESH_EFFECTIVE_STEPS_COEFF；带宽和延迟竞争模型；默认 link_lat 从 2000us 改为 2us（HCCS） |
| `tests/test_performance_model.py` | **新文件**。8 测试：范围检查、满分/零分/带宽差异/延迟差异/边界条件 |
| `tests/test_simulator_model.py` | **新文件**。10 测试：0-100 范围、Ring vs Mesh、Mesh 带宽崩溃、扩展退化、效率差异、Fat Tree 竞争 |

### 测试结果

```
test_performance_model:  8 tests PASS
test_simulator_model:   10 tests PASS
Existing tests:        106 tests PASS (unchanged)
Total:                 124 Python + 15 C = 139 tests PASS
```

### 典型输出对比

| 场景 | 旧 score | 新 score | 说明 |
|------|---------|---------|------|
| Ring 4 nodes Full Mesh | ~8.75 | 88.80 | 标准化范围 |
| Mesh 4 nodes Full Mesh | ~8.75 | 82.81 | Ring 效率更高 |
| Mesh 32 nodes Full Mesh | ~8.75 | 27.09 | 带宽崩溃 |
| Ring 32 nodes Full Mesh | ~8.75 | 36.00 | 延迟退化但带宽稳定 |

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 通信基础设施 | ✅ |
| C Ring AllReduce (CPU) | ✅ |
| Python ↔ C Bridge | ✅ |
| Plugin 能力发现 | ✅ |
| Agent 执行 Ring AllReduce | ✅ |
| Agent 自动评价与报告 | ✅ |
| DeepSeek LLM 推理 | ✅ |
| **标准化性能评分体系** | **✅ 本轮完成** |
| Butterfly / Mesh / NHR / Fat-Tree | ⬜ 未实现 |
| 真实 CANN / HCOMM 对接 | ⬜ 待 SDK |



## 2026-06-14（第十二批）：Butterfly AllReduce CPU 实现 — Recursive Doubling

### 目标

让 Butterfly 从 "可发现但不可执行" 升级为完整可执行算法，Agent 推荐 Butterfly 后能真正运行。

### Butterfly 原理 — Recursive Doubling

log₂(N) 步内完成全局归约。每步 rank i 与 partner = i XOR 2^step 交换累加值：

```
N=8 示例:

Step 0 (distance=1):  0<->1  2<->3  4<->5  6<->7
Step 1 (distance=2):  0<->2  1<->3  4<->6  5<->7
Step 2 (distance=4):  0<->4  1<->5  2<->6  3<->7
```

每步 snapshot 机制避免原地更新的重复累加。log₂(N) 步后所有 rank 持有全局和。

### 修改文件

| 文件 | 改动 |
|------|------|
| `hcccl/src/hccl_algorithms.c` | 替换 `butterfly_allreduce()` 桩为真实实现（参数校验 → 存储输入 → log₂(N) 步 pairwise exchange → 返回结果） |
| `hcccl/tests/test_butterfly.c` | **新文件**。6 个测试：4 rank/8 rank/NULL args/FP16/PROD |
| `hcccl/CMakeLists.txt` | 新增 `test_butterfly` 目标 |
| `plugin/execution_engine.py` | 新增 `butterfly_allreduce` ctypes 绑定 + `_execute_butterfly()` + `_IMPLEMENTED` 增加 "butterfly" |
| `tests/test_execution_engine.py` | Butterfly 从 not_implemented → success（+2 测试） |
| `tests/test_execution_skill.py` | 新增 `test_execute_butterfly_success` |
| `tests/test_execution_report_flow.py` | 新增 `test_full_flow_butterfly_success` |

### Agent 执行链路变化

```
Before:  Butterfly → "not_implemented"
After:   Butterfly → butterfly_allreduce() → [sum, sum, ...]
```

### 测试结果

```
C:  test_topology  9/9
    test_ring       6/6
    test_butterfly  6/6  ← NEW
    Total C:       21/21

Python:  127 tests PASS (+3 new, existing updated)
Total:   148 tests PASS
```

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 通信基础设施 | ✅ |
| C Ring AllReduce (CPU) | ✅ |
| **C Butterfly AllReduce (CPU)** | **✅ 本轮完成** |
| Python ↔ C Bridge | ✅ |
| Plugin 能力发现 + 执行 | ✅ (Ring + Butterfly) |
| Agent 自动评价与报告 | ✅ |
| DeepSeek LLM 推理 | ✅ |
| 标准化 0–100 性能评分 | ✅ |
| Mesh / NHR / Fat-Tree | ⬜ 未实现 |
| 真实 CANN / HCOMM | ⬜ 待 SDK |



## 2026-06-14（第十三批）：NHR AllReduce CPU 实现 — Hierarchical Ring

### NHR 原理 — 三阶段层级环

```
16 ranks 示例 (group_size=4):

Phase 1 — Group Local Reduce:
  Group0: [0,1,2,3] → leader 0 持有组内和
  Group1: [4,5,6,7] → leader 4 持有组内和
  Group2: [8,9,10,11] → leader 8 持有组内和
  Group3: [12,13,14,15] → leader 12 持有组内和

Phase 2 — Leader Ring Reduce:
  leader 0 → 4 → 8 → 12 → 0  (环)
  → 所有 leader 持有全局和

Phase 3 — Group Broadcast:
  每个 leader 将全局和广播给组内成员
  → 所有 16 个 rank 获得相同结果
```

### 修改文件

| 文件 | 改动 |
|------|------|
| `hcccl/src/hccl_algorithms.c` | 替换 `nhr_allreduce()` 桩：三阶段层级环实现（NHR_GROUP_SIZE=4） |
| `hcccl/tests/test_nhr.c` | **新文件**。7 测试：4/8/16 rank + NULL/FP16/PROD |
| `hcccl/CMakeLists.txt` | 新增 `test_nhr` 目标 |
| `plugin/execution_engine.py` | ctypes 绑定 + `_execute_nhr()` + `_IMPLEMENTED` 增加 nhr |
| `simulator/simulator.py` | NHR 效率系数 0.92→0.93 |
| `tests/test_execution_engine.py` | +3 NHR 测试，移除旧 not_implemented |
| `tests/test_execution_skill.py` | +1 NHR 成功测试 |
| `tests/test_execution_report_flow.py` | +1 NHR 端到端测试 |

### 测试结果

```
C:  topology 9 + ring 6 + butterfly 6 + nhr 7 = 28 PASS
Python: 131 PASS (+4 new NHR tests)
Total:  159 PASS
```

### Agent 执行链路

```
Ring      ✅ → ring_allreduce()
Butterfly ✅ → butterfly_allreduce()
NHR       ✅ → nhr_allreduce()     ← NEW
Mesh      ⬜ → not_implemented
Fat-Tree  ⬜ → not_implemented
```

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 通信基础设施 | ✅ |
| **C 可执行算法: Ring / Butterfly / NHR** | **✅ 3/5 完成** |
| Python ↔ C Bridge | ✅ |
| Plugin 执行 | ✅ (3 algorithms) |
| Agent 自动评价与报告 | ✅ |
| DeepSeek LLM 推理 | ✅ |
| 标准化 0–100 评分 | ✅ |
| Mesh / Fat-Tree | ⬜ 未实现 |
| 真实 CANN / HCOMM | ⬜ 待 SDK |


## 2026-06-14（第十四批）：Mesh AllReduce CPU 实现 — 全互联归约

### Mesh 原理

Full Mesh 拓扑中所有节点直接互联。AllReduce 只需一步：
1. 收集所有 rank 的输入 → 计算全局和
2. 将全局和写入所有 rank → 完成

CPU 模拟实现：
```
global_sum = Σ rank_values[0..N-1]
rank_results[i] = global_sum  (for all i)
```

### 修改文件

| 文件 | 改动 |
|------|------|
| `hcccl/src/hccl_algorithms.c` | 替换 `mesh_allreduce()` 桩 |
| `hcccl/tests/test_mesh.c` | **新文件**。6 测试 |
| `hcccl/CMakeLists.txt` | 新增 `test_mesh` |
| `plugin/execution_engine.py` | ctypes 绑定 + `_execute_mesh()` + mesh 加入 `_IMPLEMENTED` |
| `tests/test_execution_engine.py` | +2 Mesh 测试，移除 not_implemented |
| `tests/test_execution_skill.py` | +1 Mesh 测试 |
| `tests/test_execution_report_flow.py` | +1 Mesh 端到端 |

### 测试结果

```
C:  topology 9 + ring 6 + butterfly 6 + nhr 7 + mesh 6 = 34 PASS
Python: 134 PASS
Total:  168 PASS
```

### Agent 执行链路

```
Ring      ✅   Butterfly ✅   NHR  ✅   Mesh ✅
Fat-Tree  ⬜
```

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 基础设施 | ✅ |
| **可执行算法** | **✅ 4/5 (Ring + Butterfly + NHR + Mesh)** |
| Python ↔ C Bridge | ✅ |
| Agent 评价/报告/推理 | ✅ |
| Fat-Tree | ⬜ |
| 真实 CANN / HCOMM | ⬜ 待 SDK |



## 2026-06-14（第十五批）：Fat-Tree AllReduce CPU 实现 — 树形聚合

### Fat-Tree 原理 — 三阶段树形聚合

```
16 ranks, group_size=4:

Phase 1 — Leaf:        Phase 2 — Core:       Phase 3 — Broadcast:
G0:[0,1,2,3]→L0=10    L0+L1+L2+L3           L0→G0, L1→G1,
G1:[4,5,6,7]→L1=26    = 136 (global sum)    L2→G2, L3→G3
G2:[8,9,10,11]→L2=42                         → all 16 ranks = 136
G3:[12,13,14,15]→L3=58
```

CPU 模拟：组内求和 → 组间求和 → 广播。FT_GROUP_SIZE=4。

### 修改文件

| 文件 | 改动 |
|------|------|
| `hcccl/src/hccl_algorithms.c` | 替换 `fattree_allreduce()` 桩 |
| `hcccl/tests/test_fattree.c` | **新文件**。7 测试 |
| `hcccl/CMakeLists.txt` | 新增 `test_fattree` |
| `plugin/execution_engine.py` | ctypes 绑定 + `_execute_fattree()` |
| `simulator/simulator.py` | Fat-Tree 效率 0.88→0.95 |
| `tests/test_execution_engine.py` | +2 Fat-Tree 测试 |
| `tests/test_execution_skill.py` | +1 Fat-Tree 测试 |
| `tests/test_execution_report_flow.py` | +1 Fat-Tree 测试 |

### 测试结果

```
C:  41/41  (9+6+6+7+6+7)
Python: 137/137
Total:  178 PASS
```

### Agent 执行链路 — 全部 5 个算法可执行

```
Ring      ✅   Butterfly ✅   NHR  ✅   Mesh ✅   Fat-Tree ✅
```

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 基础设施 | ✅ |
| **可执行算法** | **✅ 5/5 全部完成** |
| Python ↔ C Bridge | ✅ |
| Agent 评价/报告/推理 | ✅ |
| 真实 CANN / HCOMM | ⬜ 待 SDK |


## 2026-06-14（第十六批）：LLM Decision Engine + Execution Benchmark

### 目标

将 LLM 从 Commentator 升级为 Decision Maker，并增加真实执行计时。

### 架构变化

```
Before:                                  After:
AlgorithmSkill                           AlgorithmSkill
  ↓                                        ↓
Simulator.evaluate()                     Simulator.evaluate()
  ↓                                        ↓
OptimizationSkill (max score)            OptimizationSkill (ranking)
  ↓                                        ↓
ReasoningSkill (解释)                     DecisionSkill (LLM 选择)
  ↓                                        ↓
                                          ExecutionSkill + BenchmarkSkill
                                            ↓
                                          EvaluationSkill + ReportGenerator
                                          
LLM 从"旁白"升级为"决策者"
```

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/decision_skill.py` | LLM 算法选择：构造候选算法 Prompt → 调用 DeepSeek → 解析 Algorithm/Reason → 失败回退 None |
| `agent/benchmark_skill.py` | 执行计时：`time.perf_counter()` 测量 `ExecutionSkill.execute()` 耗时 |
| `tests/test_decision_skill.py` | 5 测试：正常解析/缺失字段/空返回/API异常/大小写 |
| `tests/test_benchmark_skill.py` | 3 测试：耗时>0/结果正确/无execution_skill |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/hccl_agent.py` | 集成 DecisionSkill（选择或回退）+ BenchmarkSkill（计时执行）+ `chosen_algorithm` 替换 `best_algorithm` + 输出新增 `llm_decision`/`benchmark` |
| `agent/report_generator.py` | 新增 Predicted Score + Actual Execution Time 段落 |
| `tests/test_execution_report_flow.py` | 验证 benchmark 字段 + 报告含计时 |
| `tests/test_report_generator.py` | +1 benchmark 报告测试 |

### 测试结果

```
C:      41/41 (unchanged)
Python: 146/146 (+9 new: 5 decision + 3 benchmark + 1 report)
Total:  187 PASS
```

### 当前项目阶段评估

| 层次 | 状态 |
|------|------|
| C 基础设施 + 5/5 算法 | ✅ |
| Python ↔ C Bridge | ✅ |
| Plugin 执行 + 能力发现 | ✅ |
| Agent 自动评价与报告 | ✅ |
| **LLM 决策引擎** | **✅ 本轮完成** |
| **执行 Benchmark** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |

## 2026-06-14（第十七批）：Experience Memory & Historical Learning

### 目标

让 Agent 从历史运行中学习，LLM 决策时同时参考当前模拟结果和历史统计数据。

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/experience_store.py` | `save()` → JSONL，`query_similar()` → 相似场景，`aggregate_statistics()` → 按算法统计 |
| `tests/test_experience_store.py` | 7 测试：save/load/query/match/aggregate/empty/timestamp |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/hccl_agent.py` | init ExperienceStore → query historical → 传入 DecisionSkill → auto-save |
| `agent/decision_skill.py` | `historical_stats` 参数 → Prompt 增加 Historical Performance 段落 |
| `agent/report_generator.py` | `historical_stats` → 报告增加 Historical Performance 段落 |

### 测试结果

```
Python: 153/153 (+7)
C:      41/41
Total:  194 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 基础设施 + 5/5 算法 | ✅ |
| Python ↔ C Bridge | ✅ |
| LLM 决策引擎 + Benchmark | ✅ |
| **Experience Memory** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |

## 2026-06-14（第十八批）：Adaptive Policy Engine — 历史经验驱动决策

### 目标

将历史经验从"展示参考"升级为"驱动决策"。

### PolicyEngine 设计

```
simulation_score × 0.7 + win_rate × 100 × 0.3 = final_score
```

`calculate_win_rates(historical_stats)` → 按算法出现频率计算 win rate
`rank_algorithms(sim_scores, win_rates)` → 融合排序（降序）

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/policy_engine.py` | PolicyEngine 类 |
| `tests/test_policy_engine.py` | 9 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/experience_store.py` | 新增 `get_win_rate_summary()` |
| `agent/decision_skill.py` | `choose_algorithm()` 新增 `win_rates` → Prompt 增加 Win Rate 段落 |
| `agent/hccl_agent.py` | import PolicyEngine → `rank_algorithms()` → 传入 DecisionSkill → `output["policy_ranking"]` |
| `agent/report_generator.py` | 新增 Policy Ranking 段落 |

### Agent 调用链路图

```
run()
  ├── Simulator → candidate_results
  ├── ExperienceStore.query_similar() → records
  ├── ExperienceStore.aggregate_statistics() → historical_stats
  ├── ExperienceStore.get_win_rate_summary() → win_rates
  ├── PolicyEngine.rank_algorithms(sim, win_rates) → policy_ranking
  ├── DecisionSkill.choose_algorithm(..., win_rates, historical_stats) → chosen
  ├── ExecutionSkill + BenchmarkSkill
  └── ExperienceStore.save()
```

### 测试结果

```
C:      41/41
Python: 162/162 (+9)
Total:  203 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Python Bridge + 执行 | ✅ |
| LLM 决策 + Benchmark | ✅ |
| Experience Memory | ✅ |
| **Adaptive Policy Engine** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |

## 2026-06-14（第十九批）：Self Reflection Engine — 执行后反思与重规划

### 目标

形成 Plan → Execute → Reflect 闭环。

### ReflectionSkill 设计

| 条件 | Status | Need Replan |
|------|--------|-------------|
| exec_time < 1ms | good | False |
| 1ms ≤ exec_time < 5ms | warning | False |
| exec_time ≥ 5ms | poor | True |

额外检测：误差比 > 0.5 → `prediction_deviation = True`

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/reflection_skill.py` | ReflectionSkill 类 |
| `tests/test_reflection_skill.py` | 11 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/hccl_agent.py` | import ReflectionSkill → init → reflect() → `output["reflection"]` |
| `agent/report_generator.py` | 新增 Reflection 段落（Status / Message / Need Replan） |

### Agent 调用链路图

```
run()
  ├── AlgorithmSkill → Simulator → OptimizationSkill
  ├── PolicyEngine.rank_algorithms()
  ├── DecisionSkill (LLM)
  ├── ExecutionSkill + BenchmarkSkill
  ├── ReflectionSkill.reflect()     ← NEW
  └── ExperienceStore.save()
  
  Plan → Execute → Reflect 闭环完成
```

### 测试结果

```
C:      41/41
Python: 172/172 (+10)
Total:  213 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Python Bridge + 执行 | ✅ |
| LLM 决策 + Benchmark | ✅ |
| Experience Memory + Policy | ✅ |
| **Self Reflection** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |

## 2026-06-14（第二十批）：Replanning Engine — 自动重规划

### 目标

Reflection 发现问题后自动触发 RePlan，形成 Plan→Execute→Reflect→RePlan 闭环。

### ReplanningSkill 设计

`choose_alternative(current, ranking)` → 返回 ranking 中第一个不等于 current 的算法。无替代时返回 current。最多重规划一次。

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/replanning_skill.py` | ReplanningSkill 类 |
| `tests/test_replanning_skill.py` | 8 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/hccl_agent.py` | Reflection → need_replan → ReplanningSkill → 再次执行 → `output["replanned"]` |
| `agent/report_generator.py` | 新增 Replanning 段落（Triggered / Original / Replanned） |

### Agent 调用链路图

```
DecisionSkill → Execution → Benchmark → Reflection
                                              │
                                    need_replan? ──No──→ done
                                              │
                                             Yes
                                              │
                                    ReplanningSkill.choose_alternative()
                                              │
                                    Execution + Benchmark (replanned)
                                              │
                                    done  (max 1 replan)
```

### 测试结果

```
C:      41/41
Python: 180/180 (+8)
Total:  221 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Python Bridge + 执行 | ✅ |
| LLM 决策 + Benchmark | ✅ |
| Experience + Policy + Reflection | ✅ |
| **Auto Replanning** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |

## 2026-06-14（第二十一批）：Task Decomposition & Multi-Step Planning

### 目标

新增 Planning Layer，将优化目标分解为有序可执行子任务。

### Plan 结构（8 步骤）

1. Analyze topology
2. Simulate candidate algorithms
3. Rank algorithms by predicted performance
4. Select best algorithm via policy engine
5. Execute [primitive] on chosen algorithm
6. Evaluate execution performance
7. Reflect on result and replan if needed
8. Record experience for future learning

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/planning_skill.py` | PlanningSkill 类 |
| `tests/test_planning_skill.py` | 8 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/hccl_agent.py` | init → `create_plan()` → `output["plan"]` |
| `agent/report_generator.py` | 新增 Planning 段落 |

### 测试结果

```
C:      41/41
Python: 188/188 (+8)
Total:  229 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Python Bridge + 执行 | ✅ |
| LLM 决策 + Benchmark | ✅ |
| Experience + Policy + Reflection + Replan | ✅ |
| **Multi-Step Planning** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |


## 2026-06-14（第二十二批）：HCCL Compatibility Layer

### 目标

新增 HCCL 标准接口兼容层，使 Agent 通过 `HcclAllReduce` / `HcclAllGather` / `HcclReduceScatter` 调用 Simulator，形成标准 HCCL 接口 + 模拟验证闭环。

### 新增文件

| 文件 | 说明 |
|------|------|
| `plugin/hccl_api.py` | HcclComm + HcclCommInitClusterInfo + 3 个集体通信函数 |
| `tests/test_hccl_api.py` | 6 测试：init/allreduce/allgather/reducescatter/algorithm/score range |
| `tests/test_execution_hccl_flow.py` | 3 测试：simulate_collective → HCCL API → Simulator 调用链 |
| `tests/test_planning_hccl_integration.py` | 5 测试：plan 含 primitive/algorithm 字段 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `simulator/simulator.py` | 新增 `simulate_collective()` — 统一 HCCL 调用入口 |
| `agent/planning_skill.py` | 新增 `_DEFAULT_ALGORITHM` 映射 + 步骤 5 含 primitive/algorithm |
| `agent/report_generator.py` | 新增 HCCL Compatibility Report 段落 |

### 执行链路

```
Cluster Config → Planning (primitive selection)
    → HcclAllReduce / HcclAllGather / HcclReduceScatter
    → Simulator.simulate_collective()
    → Evaluation → Reflection → Replanning → Report
```

### 测试结果

```
C:      41/41
Python: 202/202 (+14 new)
Total:  243 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Python Bridge + 执行 | ✅ |
| LLM 决策 + Benchmark | ✅ |
| Experience + Policy + Reflection + Replan | ✅ |
| Multi-Step Planning | ✅ |
| **HCCL Compatibility Layer** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |

## 2026-06-14（第二十三批）：Graph-Based Communication Engine

### Overview

Batch23 引入 graph-based 通信建模，替换 flat bandwidth/latency 模拟。
新增 Hardware Abstraction Layer、Topology Graph Builder、Cost Model Engine。

## 2026-06-14（第二十四批）：Topology-Aware Algorithm Selection

### 目标

将固定算法映射升级为图拓扑感知的算法自动选择。Agent 现在分析拓扑图，在图模拟器上评估候选算法，自动选出最优。

### 新增文件

| 文件 | 说明 |
|------|------|
| `skills/algorithm_selector.py` | AlgorithmSelector — 图模拟 → 排序 → 选择 |
| `skills/topology_reasoning_skill.py` | TopologyReasoningSkill — 提取图结构属性 |
| `tests/test_algorithm_selector.py` | 5 测试 |
| `tests/test_topology_reasoning.py` | 5 测试 |
| `tests/test_algorithm_selection_flow.py` | 2 测试 |
| `tests/test_algorithm_reflection.py` | 3 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/planning_skill.py` | 重构：候选算法 + 图模拟选择替代固定映射 |
| `agent/report_generator.py` | 新增 Algorithm Selection Report 段落 |
| `tests/test_planning_hccl_integration.py` | 适配新 plan 结构 |

### Algorithm Selection Report（示例）

```
Algorithm Selection Report:
---------------------------
  Candidates: Ring AllReduce, Butterfly, Mesh, NHR, Fat-Tree
    Ring AllReduce       score=78.3
    Butterfly            score=85.2
    Mesh                 score=64.1
    NHR                  score=82.0
    Fat-Tree             score=71.5
  Selected:  Butterfly
  Reason:    Selected Butterfly — score=85.2...
```

### 测试结果

```
C:      41/41
Python: 239/239 (+15 new)
Total:  280 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Graph-Based Comm Engine | ✅ |
| Hardware Abstraction | ✅ |
| HCCL Compatibility | ✅ |
| **Topology-Aware Algorithm Selection** | **✅ 本轮完成** |

## 2026-06-14（第二十五批）：Explainable Decision Engine

### 目标

新增完整决策可解释性：Decision Trace、Candidate Ranking、Selection Justification、Reflection-based Quality Analysis。

### Decision Trace 结构（6 步）

```
[1] Topology: FatTree  Nodes: 32  Dominant Link: RoCE
[2] Candidates: Ring, Butterfly, Fat-Tree
[3] Simulation: Ring=82  Butterfly=86  Fat-Tree=93
[4] Cost: latency=0.2ms  bandwidth=11GB/s
[5] Selected: Fat-Tree
     Reason: Highest score among 3 candidates
[6] Reflection: status=good  need_replan=False
```

### 新增文件

| 文件 | 说明 |
|------|------|
| `agent/explanation_skill.py` | generate_decision_trace() |
| `tests/test_explanation_skill.py` | 4 测试 |
| `tests/test_decision_trace_flow.py` | 2 测试 |
| `tests/test_reflection_decision_quality.py` | 3 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `skills/algorithm_selector.py` | 新增 ranking + candidate_scores |
| `skills/topology_reasoning_skill.py` | 新增 topology_summary() |
| `agent/reflection_skill.py` | 新增 decision_quality 分析 |
| `agent/report_generator.py` | 新增 Decision Trace + Reflection on Decision 段落 |
| `agent/hccl_agent.py` | 集成 ExplanationSkill → output["decision_trace"] |

### 测试结果

```
C:      41/41
Python: 248/248 (+9 new)
Total:  289 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Graph Engine + HW Abstraction | ✅ |
| Topology-Aware Selection | ✅ |
| **Explainable Decision Engine** | **✅ 本轮完成** |

## Milestone M1: Scenario Benchmark Suite

### Benchmark Motivation

构建 5 个标准集群场景，自动运行 Agent 全流程并生成可复现报告，用于比赛演示、答辩展示和实验验证。

### Benchmark Scenarios

| # | Scenario | Nodes | Topology | Primitive | Msg Size | Selected | Score |
|---|----------|-------|----------|-----------|----------|----------|-------|
| 1 | single_node_8gpu | 8 | Full Mesh | AllReduce | 128 MB | Butterfly | 90.4 |
| 2 | dual_node_16gpu | 16 | Hierarchical | AllReduce | 256 MB | NHR | 61.2 |
| 3 | fattree_32gpu | 32 | Fat Tree | AllReduce | 512 MB | NHR | 37.2 |
| 4 | hierarchical_64gpu | 64 | Hierarchical | Broadcast | 1024 MB | Fat-Tree | 36.0 |
| 5 | heterogeneous_cluster | 24 | Heterogeneous | AllReduce | 256 MB | NHR | 42.0 |

### Benchmark Pipeline

```
Scenario JSON → Agent.run() → Algorithm Selection → Decision Trace
    → Reflection → Per-scenario Markdown Report → Summary Table
```

### 新增文件

| 文件 | 说明 |
|------|------|
| `experiments/scenarios/` (5 JSON) | 标准场景配置 |
| `experiments/benchmark_runner.py` | 批量执行 + 报告生成 |
| `experiments/reports/` (6 MD) | 5 场景报告 + 1 汇总表 |
| `skills/benchmark_suite_skill.py` | BenchmarkSuiteSkill |
| `tests/test_benchmark_runner.py` | 4 测试 |
| `tests/test_benchmark_reports.py` | 2 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `agent/hccl_agent.py` | SUPPORTED_PRIMITIVES 增加 Broadcast |
| `tests/test_agent.py` | 不支持的 primitive 改用 AlltoAll |

### 测试结果

```
C:      41/41
Python: 254/254 (+6 new)
Total:  295 PASS
5 scenarios: all executed successfully
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Graph Engine + Topology Selection | ✅ |
| Explainable Decision + Reflection | ✅ |
| **Scenario Benchmark Suite** | **✅ M1 完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |

## 2026-06-14（Batch26）：Performance Model Calibration & Validation

### Overview

Batch26 introduces calibrated performance scoring with smooth latency decay,
score breakdown, scaling validation, and decision optimality checks.

### Key Enhancements

**(1) Smooth Latency Decay Model**
- Old: `max(0, 100 - latency * LATENCY_PENALTY)` — hard cutoff at 0
- New: `100 / (1 + latency_ms / LATENCY_SCALE)` — smooth decay, never hits zero
- LATENCY_SCALE=30 (configurable): 30ms → lat_score=50

**(2) Score Breakdown**
- `calculate_score_breakdown()` returns bandwidth_score, latency_score, bw_weighted, lat_weighted
- Backward-compatible: `calculate_score()` unchanged

**(3) Scaling Validation** (`analysis/scaling_analysis.py`)
- 4→128 nodes: scores decrease monotonically, latency decays smoothly

**(4) Algorithm & Topology Sensitivity** (2 analysis scripts)

**(5) Decision Validation Layer** (`skills/decision_validation_skill.py`)
- Validates selected algorithm is truly optimal; confidence levels

### 新增文件

| 文件 | 说明 |
|------|------|
| `skills/decision_validation_skill.py` | DecisionValidationSkill |
| `analysis/scaling_analysis.py` | 4→128 节点扩展分析 |
| `analysis/algorithm_sensitivity.py` | 5 算法比较 |
| `analysis/topology_sensitivity.py` | 5 拓扑比较 |
| `tests/test_performance_calibration.py` | 6 测试 |
| `tests/test_score_breakdown.py` | 3 测试 |
| `tests/test_decision_validation.py` | 4 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `skills/performance_model.py` | 重构：smooth decay + breakdown |
| `agent/report_generator.py` | Score Breakdown 段落 |
| `tests/test_performance_model.py` | 适配新模型 |

### 测试结果

```
C:      41/41
Python: 267/267 (+13 new)
Total:  308 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| Graph Engine + Topology Selection | ✅ |
| Explainable Decision | ✅ |
| Benchmark Suite (M1) | ✅ |
| **Calibrated Performance Model** | **✅ 本轮完成** |
| 真实 CANN / HCOMM | ⬜ 待 SDK |


| 真实 CANN / HCOMM | ⬜ 待 SDK |



### Key Enhancements

**(1) Hardware Abstraction Layer** (`hardware/profile.py`)
- `HardwareProfile` — 可配置链路行为模型（HCCS/RoCE/PCIe）
- 三级预设（high/medium/low），不硬编码真实 Ascend 数值
- `from_json()` / `to_json()` / `get_link_properties()`

**(2) Topology Graph Engine** (`topology/graph_builder.py`)
- `CommunicationGraph` — 加权有向图，边含 bandwidth/latency/link_type/contention_weight
- 三种模式：SINGLE_NODE（Full Mesh）、MULTI_NODE（HCCS+RoCE Fat-Tree）、HETEROGENEOUS（非对称混合链路）

**(3) Cost Model Engine** (`cost_model/engine.py`)
- `estimate_allreduce_ring()` — 环形路径遍历 + chunk 分解
- `estimate_allreduce_tree()` — log-N 树形估算
- 竞争惩罚 + 计算-通信重叠因子

### 新增文件

| 文件 | 说明 |
|------|------|
| `hardware/profile.py` | HardwareProfile 抽象层 |
| `topology/graph_builder.py` | CommunicationGraph + TopologyGraphBuilder |
| `cost_model/engine.py` | CostModelEngine |
| `tests/test_hardware_profile.py` | 6 测试 |
| `tests/test_topology_graph.py` | 6 测试 |
| `tests/test_cost_model.py` | 5 测试 |
| `tests/test_graph_simulator.py` | 5 测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `simulator/simulator.py` | 新增 `simulate_with_graph()` — 图遍历通信模拟 |
| `plugin/hccl_api.py` | `_simulate()` 支持可选的 graph + profile 参数 |
| `agent/planning_skill.py` | 新增 hardware_profile/topology_mode/graph_strategy 字段 |

### 执行链路（升级后）

```
Planning → ExecutionSkill → HCCL API
    → Topology Graph Simulator → Cost Model Engine
    → Evaluation → Reflection → Replanning → Report
```

### 测试结果

```
C:      41/41
Python: 224/224 (+22 new)
Total:  265 PASS
```

### 当前项目阶段

| 层次 | 状态 |
|------|------|
| C 5/5 算法 | ✅ |
| HCCL Compatibility Layer | ✅ |
| Agent Decision Loop | ✅ |
| **Graph-Based Comm Engine** | **✅ 本轮完成** |
| **Hardware Abstraction + Cost Model** | **✅ 本轮完成** |


