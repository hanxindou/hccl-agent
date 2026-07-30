# HCCL Agent 项目审计报告

> H1 更新说明：本报告主体记录的是综合审计时的基线事实。后续自主阶段 A1/B1/C1/C2/C3/E1/D1/F1/G1 已陆续完成并创建本地提交。当前比赛准备度、Windows 验收结果和仍未验证边界以 `docs/competition_readiness_report.md`、`docs/correctness_matrix.md`、`docs/reliability_report.md` 和 `docs/user_actions.md` 为准。

审计基线：`e67a18d31e7bf7b88975a2ae2816d42945aaf290`（`e67a18d baseline-before-comprehensive-audit`）  
审计环境：Windows Native，项目路径 `F:\projects\hccl-agent`，分支 `main`。  
审计范围：赛题 DOCX、项目文档、Git 跟踪文件清单、入口调用链、Agent/Skills/Simulator/Plugin/C/test/config/script 等当前实现。  
动态验证状态：Windows Native 动态验证已执行。Conda Python 3.10 环境中运行 339 个 Python 测试，出现 17 个 error，均为已识别的 Windows/Linux 路径兼容问题；Windows MSVC/CMake 成功构建 CPU 插件及 6 个 C 测试程序，手动执行共 41 个测试用例，41 个全部通过。Linux `.so`、CANN/HCOMM 与 Ascend 实机环境尚未验证。

## 1. 执行摘要

当前项目已经不是最早期的空骨架，而是一个较完整的 **Python Agent + 规则/模型决策 + CPU 模拟 C 插件** 原型。它能够从 CLI 进入 `HCCLAgent.run()`，串联配置加载、拓扑推断、算法候选选择、模拟评分、LLM best-effort 推理、规则决策、C CPU 模拟 benchmark、反思、重规划、自动调优、知识/经验记录、Prompt 记录和报告生成等环节。

但按原始赛题验收标准判断，项目尚未达到可提交状态。赛题要求“基于 CANN 8.0+ 与 HCOMM 开源接口，采用 C/C++，至少正确实现 3 种 HCCL 核心集合通信原语，并由 Agent 完成核心算法和代码开发过程”。当前 C 层真实可计算部分集中在 **AllReduce 系列 CPU 单进程模拟**，且仅支持 FP32、SUM、`count == 1`，没有真实 Ascend/CANN/HCOMM 链接，没有多进程/多设备通信，没有 FP16/BF16 混合精度，也没有 C 层 AllGather/ReduceScatter/Broadcast 数据正确性实现。

最大工程优势是模块覆盖广、测试数量多、主流程可表达完整 Agent 工作流，并且已有 `ctypes` 到 `libhccl_plugin.so` 的 CPU 模拟闭环。最大技术缺口是赛题核心交付物仍停留在模拟与规则层：标准接口兼容性、真实 primitive 正确性、实机或高保真模拟、Agent 代码生成-编译-测试-修复闭环都未达验收级别。最大赛题风险是继续堆叠新的 Agent Skill 会稀释精力，应暂停新增“顾问类/解释类”模块，优先收敛到 HCCL/HCOMM 接口、三种 primitive、正确性测试和可追溯验证。

结论：项目原型可运行性较强，赛题验收准备度偏低。下一阶段最高优先级不是新增 Agent Skill，而是完成标准接口与三种集合通信原语的真实可验证 CPU 模拟实现，并建立与赛题原文逐项对应的正确性证据。本轮补充的 Windows Native 动态验证提高了对 CPU 原型可运行性的置信度：C 源码可由 Visual Studio 2022/MSVC 成功编译，能够生成 `hccl_plugin.dll` 和导入库，并且现有 communicator、topology 以及五类 AllReduce 的 41 个 C 测试用例全部通过。但该结果仍限定于 FP32、SUM、有限 rank 和单进程 CPU 模拟，不能证明三种 primitive、混合精度、HCOMM/CANN 兼容或 Ascend 实机性能已经完成。Python 测试暴露出的主要问题是 Linux `.so` 路径和 POSIX 临时目录被硬编码，属于跨平台工程缺陷。

## 2. 当前真实架构

```text
main.py
  |
  v
HCCLAgent.run
  |-- ConfigSkill -> config/cluster.json                         [人工配置]
  |-- TopologySkill -> Full Mesh/Ring/Fat Tree                    [规则推断]
  |-- TopologyGraph                                               [数学图模型]
  |-- HardwareReasoningSkill + NodeProfile/ResourceManager        [人工配置/模拟]
  |-- PluginManager -> HCCLBridge -> hcccl/build/libhccl_plugin.so[CPU 动态库发现]
  |-- PlanningSkill                                               [固定计划]
  |-- ExperienceStore / KnowledgeBase                             [日志经验]
  |-- AlgorithmSkill                                              [规则候选]
  |-- ReasoningSkill / DecisionSkill -> DeepSeek API              [可选 LLM, 无 Key 降级]
  |-- OptimizationSkill -> Simulator -> PerformanceModel          [数学预测]
  |-- BenchmarkSkill -> ExecutionSkill -> ExecutionEngine         [CPU 模拟执行]
  |-- ReflectionSkill / ReplanningSkill                           [规则反思]
  |-- AutoTuningSkill / OptimizationLoopSkill                     [启发式搜索]
  |-- CodeGenerationSkill                                         [伪代码/配置生成]
  |-- StrategySkill                                               [文本策略]
  |-- PromptEngine / ExperimentLogger / KnowledgeBase             [运行写入]
```

实现类型判定：

| 模块                              | 当前事实                                                                                                                                           | 实现类型                                    |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| Python Agent 主流程               | `agent/hccl_agent.py` 串联大量模块，返回完整 dict                                                                                                  | 真实实现 + 规则编排                         |
| LLM Reasoning/Decision            | `agent/llm_client.py` 读取 `DEEPSEEK_API_KEY` 并调用 DeepSeek；无 Key 抛错后主流程降级                                                             | 可选外部 API，测试为 Mock                   |
| Simulator                         | `simulator/simulator.py` 使用算法效率、步数、拓扑因子和固定权重算 latency/bandwidth/score                                                          | 数学预测                                    |
| TopologyGraph                     | `skills/topology_graph.py` / `topology/graph_builder.py` 构图和路径计算                                                                            | 数学图模型                                  |
| Hardware awareness                | `hardware/`、`skills/hardware_reasoning_skill.py` 使用静态容量/亲和度                                                                              | 人工配置 + 模拟                             |
| C 动态库                          | Linux 设计目标为 `libhccl_plugin.so`；Windows 在启用自动符号导出后可生成 `hccl_plugin.dll` 和 `hccl_plugin.lib`，但 Python loader 仍固定寻找 `.so` | CPU 模拟 + 跨平台适配不完整                 |
| C AllReduce 算法                  | Ring/Butterfly/Mesh/NHR/Fat-Tree 的现有 Windows C 测试共 32 个算法用例通过；仍只覆盖 FP32、SUM、有限 rank 和 CPU 模拟                              | 已动态验证的有限 CPU 模拟                   |
| AllGather/ReduceScatter/Broadcast | Python 兼容层只返回模拟指标；C 层相关函数多为 STUB 或无通用 wrapper 实现                                                                           | Stub/数学模型                               |
| CodeGenerationSkill               | 生成配置、执行计划和 Python 伪代码 skeleton                                                                                                        | 文本/伪代码生成，不写入生产代码             |
| Knowledge/Experience              | 写入 `logs/*.jsonl`                                                                                                                                | 真实持久化，但数据来自模拟                  |
| third_party/cann-hccl             | 历史孤立 gitlink 已在 V1 Linux CI 清理阶段移除                                                                                                     | 当前未引入第三方 CANN/HCCL 源码或 submodule |

## 3. 已实现能力矩阵

| 能力                        | 主要文件                                                     |                                       主流程调用 | 测试证据                                                 | 实现类型                       | 成熟度 | 赛题相关性 |
| --------------------------- | ------------------------------------------------------------ | -----------------------------------------------: | -------------------------------------------------------- | ------------------------------ | ------ | ---------- |
| Planning                    | `agent/planning_skill.py`                                    |                                               是 | `test_planning_skill.py`                                 | 固定计划                       | 中     | 高         |
| LLM Reasoning               | `agent/reasoning_skill.py`, `agent/llm_client.py`            |                                     是，失败降级 | `test_reasoning_skill.py`, `test_llm_client.py` Mock     | 可选外部 API                   | 低-中  | 高         |
| LLM Decision                | `agent/decision_skill.py`                                    |                                     是，失败降级 | `test_decision_skill.py`                                 | 可选外部 API                   | 低-中  | 高         |
| Execution                   | `agent/execution_skill.py`, `plugin/execution_engine.py`     |                             是，benchmark 中调用 | `test_execution_engine.py`                               | CPU 模拟                       | 中     | 高         |
| Benchmark                   | `agent/benchmark_skill.py`                                   |                                               是 | `test_benchmark_skill.py`                                | CPU 计时                       | 中     | 中         |
| Evaluation                  | `agent/evaluation_skill.py`                                  |                                     报告入口调用 | `test_evaluation_skill.py`                               | 规则评分                       | 中     | 中         |
| Reflection/Replanning       | `agent/reflection_skill.py`, `agent/replanning_skill.py`     |                                               是 | 对应测试                                                 | 规则逻辑                       | 中     | 高         |
| Experience Memory           | `agent/experience_store.py`                                  |                                               是 | `test_experience_store.py`                               | 日志经验                       | 中     | 中         |
| Policy Engine               | `agent/policy_engine.py`                                     |                                         条件调用 | `test_policy_engine.py`                                  | 规则融合                       | 中     | 中         |
| Prompt Engine/Logging       | `agent/prompt_engine.py`, `prompts/algorithm_prompt.txt`     |                                               是 | Prompt 测试                                              | 模板填充 + 日志                | 中     | 高         |
| Plugin Discovery            | `agent/plugin_manager.py`, `plugin/hccl_bridge.py`           |                                               是 | `test_plugin_bridge.py`                                  | ctypes 动态库查询              | 中     | 高         |
| Plugin Capability           | `agent/plugin_capability.py`                                 |                                               是 | `test_plugin_manager.py`                                 | 字符串映射                     | 中     | 中         |
| Plugin Bridge/Execution     | `plugin/execution_engine.py`                                 |                                               是 | `test_execution_engine.py`                               | CPU C 调用                     | 中     | 高         |
| Code Generation             | `agent/code_generation_skill.py`                             |                                               是 | `test_code_generation_skill.py`                          | 文本/伪代码                    | 低     | 高         |
| Optimization Loop           | `agent/optimization_loop_skill.py`                           |                                               是 | `test_optimization_loop.py`                              | 启发式                         | 中     | 中         |
| Auto Tuning                 | `agent/auto_tuning_skill.py`                                 |                                               是 | `test_auto_tuning_skill.py`                              | 网格搜索公式                   | 中     | 中         |
| Topology Modeling           | `skills/topology_graph.py`, `topology/graph_builder.py`      |                                          是/部分 | 多个 topology 测试                                       | 数学图模型                     | 中     | 高         |
| Dynamic Topology            | `topology/dynamic_topology.py`                               |                               未在主流程直接使用 | `test_dynamic_topology.py`                               | 可选分析模块                   | 中     | 高         |
| Hardware Awareness          | `hardware/`, `skills/hardware_reasoning_skill.py`            |                                               是 | 硬件测试                                                 | 静态模拟                       | 中     | 高         |
| Cost Model                  | `cost_model/engine.py`                                       |                               graph 模拟路径调用 | `test_cost_model.py`                                     | 数学模型                       | 中     | 高         |
| Calibration                 | `calibration/`, `analysis/calibration_report.py`             |                                 未接入主评分常量 | calibration 测试                                         | 参数容器                       | 中     | 中         |
| Fault/Health/Retry/Failover | `simulator/`                                                 | `simulate_with_failures` 可用，主 run 未默认使用 | 可靠性测试                                               | 模拟                           | 中     | 高         |
| Reporting                   | `agent/report_generator.py`, `scripts/generate_report.py`    |                                         部分入口 | 报告测试                                                 | 文本报告                       | 中     | 中         |
| Knowledge Base              | `knowledge/knowledge_base.py`                                |                                               是 | `test_knowledge_flow.py`                                 | 日志案例                       | 中     | 中         |
| Primitive 覆盖              | Python 支持 AllReduce/AllGather/ReduceScatter/Broadcast 名称 |                                               是 | `test_agent.py`                                          | 表示/模拟                      | 中     | 最高       |
| AllReduce 算法              | C 层 Ring/Butterfly/Mesh/NHR/Fat-Tree                        |                                 benchmark 可调用 | Windows MSVC 构建成功；五个算法测试程序共 32/32 用例通过 | CPU、FP32、SUM、有限 rank 模拟 | 中     | 最高       |

## 4. 赛题逐项映射

| 赛题原始要求                                             | 原文位置或表述                    | 当前实现证据                                                                                                 | 当前状态                    | 完成度 | 关键差距                                                      | 优先级 |
| -------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------- | -----: | ------------------------------------------------------------- | ------ |
| 至少 3 种核心集合通信原语                                | DOCX“通信原语与算法要求”“至少3种” | `SUPPORTED_PRIMITIVES` 支持 AllReduce/AllGather/ReduceScatter/Broadcast；`plugin/hccl_api.py` 有 Python 函数 | Python 可表示，C 未完整实现 |    30% | C 层真实 AllGather/ReduceScatter/Broadcast 缺失；无数据正确性 | P0     |
| AllReduce 正确性                                         | DOCX 评判标准                     | Windows MSVC 成功构建 Ring/Butterfly/NHR/Mesh/Fat-Tree；相关测试程序共 32/32 用例通过                        | 已动态验证的 CPU 模拟       |    45% | 仍仅覆盖 FP32/SUM、有限 rank 和单进程内存模拟，无真实设备通信 | P0     |
| FP32/BF16/FP16 混精度                                    | DOCX“精度保障”                    | C tests 明确 FP16 返回 `NOT_SUPPORTED`                                                                       | 未满足                      |     5% | BF16/FP16、误差、NaN/Inf/溢出验证缺失                         | P0     |
| CANN 8.0+ / HCOMM 接口                                   | DOCX“开发约束”                    | `hcccl/CMakeLists.txt` 明确无 CANN 依赖；README 与 CMake 描述冲突                                            | 未接入                      |    10% | 未链接 CANN/HCOMM；接口命名/签名未证实兼容真实 HCCL           | P0     |
| 单机 Full Mesh                                           | DOCX“单机多卡 FullMesh”           | `TopologyGraph.full_mesh`、C `hcclGetTopology` 模拟 Full Mesh                                                | 数学/CPU 模拟               |    45% | 无真实拓扑探测，无 HCCS 实测参数                              | P1     |
| 异构 910A2/910A3 / 非对称链路                            | DOCX“异构集群”                    | `config/cluster.json` 单 `device_type`；`topology/graph_builder.py` 有 HETEROGENEOUS 模式                    | 模拟扩展                    |    20% | 无自动探测，无真实设备差异                                    | P1     |
| 小数据 <=64KB / 大数据 >=1GB                             | DOCX“极限场景”                    | `AlgorithmSkill` 阈值覆盖                                                                                    | 规则选择                    |    40% | 只是候选选择，不证明性能和正确性                              | P1     |
| 8->1024 卡线性扩展、加速比 >=90%                         | DOCX“可扩展性”                    | 场景到 256，模拟器支持任意 nodes                                                                             | 数学外推                    |    20% | 无 1024 场景、无线性加速实证                                  | P1/P2  |
| 算法创新 NHR/分块 Mesh/动态 Butterfly/稀疏/量化/通算融合 | DOCX“算法创新”                    | NHR/Butterfly/Mesh 有规则和部分 C AllReduce；稀疏/量化/通算重叠多为 Prompt/公式                              | 部分模拟                    |    25% | 大多数不是可执行 C/HCCL 代码                                  | P1/P2  |
| 可靠性：健康检测、100ms 切换、CRC、重传率 <=0.1%         | DOCX“可靠性机制”                  | `FaultInjector`, `HealthMonitor`, `RetryPolicy`, `FailoverEngine`                                            | 模拟                        |    25% | 无真实 CRC、流控、多节点故障、长压测                          | P1     |
| Agent 完成算法设计与代码开发                             | DOCX 多处强调                     | `CodeGenerationSkill` 只生成伪代码；PromptEngine 记录模板                                                    | 部分展示                    |    25% | 无自动写入、编译、测试、修复闭环                              | P0/P1  |
| 交付代码包、.so、头文件、CMake、测试、压测、故障工具     | DOCX“参赛作品要求”                | `.so` 路径依赖既有 build；CMake/headers/tests 有；压测脚本不足                                               | 部分                        |    35% | 实机构建、标准接口、压测与提交清单不足                        | P0/P1  |
| 技术文档、性能/可靠性报告、模拟器配置日志                | DOCX“技术文档”                    | 多个 docs、experiments/reports                                                                               | 部分                        |    45% | 报告多来自模拟；缺正确性和可追溯实测                          | P1     |

扩展项说明：AlltoAll、FP8/INT4、72 小时压测、BERT/LLaMA2 端到端验证在原文中出现为典型或交付要求相关内容，但当前项目没有真实实现，应作为后续扩展或实机阶段任务，不应在当前声明完成。

## 5. 代码和架构健康度

| 问题                                           | 证据文件                                                                                      | 严重程度 | 影响                                                             | 修复建议                                                        | 优先级 | 下一阶段 |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------- | --------------------------------------------------------------- | ------ | -------- |
| README 与当前 CMake/C 源码冲突                 | `hcccl/README.md`, `hcccl/CMakeLists.txt`                                                     | 高       | 文档误导，影响评审可信度                                         | 下一阶段统一事实表述                                            | P0     | 是       |
| C 标准 wrapper 声明未见实现                    | `hcccl/include/hccl_comm.h`, `hcccl/src/*.c`                                                  | 高       | `hcclAllReduce` 等标准接口不闭合                                 | 实现 wrapper 或调整接口边界                                     | P0     | 是       |
| AllGather/ReduceScatter/Broadcast 数据实现缺失 | `hcccl/src/hccl_algorithms.c`                                                                 | 高       | 不满足至少三种 primitive                                         | 先实现 CPU 正确性版本                                           | P0     | 是       |
| 精度支持严重不足                               | C tests 对 FP16/PROD 期望 `NOT_SUPPORTED`                                                     | 高       | 不满足 FP16/BF16/FP32 混精度                                     | 增加 dtype/op 与误差测试                                        | P0     | 是       |
| 生成代码示例语法错误                           | `examples/generated_code/fat-tree.py`, `butterfly.py`, `nhr.py`                               | 中       | Code Generation 可信度低                                         | 生成合法 C/C++ 或明确为伪代码                                   | P1     | 是       |
| 主流程运行会写入 logs                          | `ExperimentLogger`, `PromptEngine`, `KnowledgeBase`, `ExperienceStore`                        | 中       | 测试和 demo 有副作用                                             | 提供 dry-run/audit 模式或临时路径注入                           | P1     | 是       |
| LLM 调用只支持 DeepSeek 且可能外网             | `agent/llm_client.py`                                                                         | 中       | 无 Key/断网时不是完整 LLM Agent                                  | 明确离线降级与可复现日志                                        | P1     | 是       |
| 高级模块平行实现较多                           | `skills/topology_graph.py`, `topology/graph_builder.py` 等                                    | 中       | 架构膨胀、主流程不一致                                           | 收敛到一套拓扑/成本模型                                         | P1     | 是       |
| 性能分数无实机校准                             | `simulator/simulator.py`, `calibration/`                                                      | 高       | 不能作为比赛性能结论                                             | 引入校准数据和参数 provenance                                   | P1     | 是       |
| 第三方 CANN/HCCL 依赖尚未引入                  | V1 已移除无 .gitmodules 配置的孤立 gitlink 后续 G2 必须核验官方来源、版本、License 和集成方式 | 中       | 难证明 HCOMM 来源/版本                                           | 记录来源、版本、引用接口                                        | P0     | 是       |
| Python loader 写死 Linux `.so` 路径            | `plugin/hccl_bridge.py`, `plugin/execution_engine.py`                                         | 高       | Windows Python 测试无法加载已生成的 DLL，多个 Agent 流程测试报错 | 支持 `.dll`/`.so` 平台检测，并允许参数或环境变量指定库路径      | P0     | 是       |
| 测试写死 POSIX `/tmp` 路径                     | `tests/test_calibration_profile.py`                                                           | 中       | Windows 原生测试产生 `FileNotFoundError`                         | 使用 `tempfile.TemporaryDirectory()` 或 `tempfile.gettempdir()` | P0     | 是       |
| Windows DLL 默认未导出符号                     | `hcccl/CMakeLists.txt`                                                                        | 高       | 默认构建生成 DLL 但不生成导入库，测试程序出现 `LNK1181`          | 为 Windows target 正式配置导出宏或 `WINDOWS_EXPORT_ALL_SYMBOLS` | P0     | 是       |
| CTest 未注册测试                               | `hcccl/CMakeLists.txt`                                                                        | 中       | `ctest` 返回 `No tests were found`，无法统一自动验收             | 增加 `enable_testing()` 与各测试目标的 `add_test()`             | P0     | 是       |
| MSVC UTF-8 编码与控制台乱码                    | `hcccl/src/*`, `hcccl/include/*`, `hcccl/tests/*`                                             | 中       | 构建出现 `C4819`，测试标题和箭头乱码                             | 核验源码编码，正式增加 MSVC `/utf-8`，避免批量无依据转码        | P1     | 是       |

## 6. 模拟器真实性审计

| 维度           | 当前评分 | 依据                                                      | 类型              |
| -------------- | -------: | --------------------------------------------------------- | ----------------- |
| 拓扑真实性     |   45/100 | 有 Full Mesh/Ring/Fat Tree/Heterogeneous 图，但非真实探测 | 数学模型/人工配置 |
| 延迟模型       |   35/100 | 步数 _ 链路延迟 _ 系数                                    | 经验常量          |
| 带宽模型       |   35/100 | 算法效率和竞争系数固定                                    | 经验常量          |
| 数据传输量模型 |   25/100 | `evaluate()` 基本不使用 message_size 影响带宽/延迟        | 数学预测不足      |
| 链路竞争       |   30/100 | Mesh/Fat-Tree 有固定系数                                  | 经验常量          |
| 并发模型       |   20/100 | 无真实并发/队列/流建模                                    | 简化模型          |
| 算法阶段模型   |   35/100 | Ring/Butterfly 等有步数，C 层 count=1                     | CPU 模拟/公式     |
| 硬件参数来源   |   25/100 | `config/cluster.json` 人工值                              | 人工配置          |
| 校准能力       |   35/100 | 有 profile 容器，未接入实测                               | 尚未实机校准      |
| 可追溯性       |   55/100 | 有 runs/prompt/summary 日志                               | 模拟日志          |
| 故障模拟       |   40/100 | 可注入 link_down/timeout/corruption/congestion            | 统计模拟          |
| 实机映射       |   10/100 | 无 CANN/HCOMM/msprof/Ascend                               | 无法验证          |

当前性能数据不能作为比赛性能结论，只能作为原型内部的相对排序参考。当前 Score 有工程调试意义，但没有客观 HCCL 对比含义。带宽和延迟不能直接与真实 HCCL 对比。在没有 Ascend 实机时，可信结论主要限于：代码路径是否可运行、规则选择是否稳定、CPU count=1 AllReduce 求和是否正确、报告链路是否可追溯。真实性能、混精度正确性、1024 卡扩展和故障恢复必须等待高保真模拟器校准或实机验证。

## 7. Agent 真实性审计

当前系统更接近“固定工作流编排器 + 规则决策器 + 数学模拟器 + 可选 LLM 解释/决策器”。它具备反思、重规划、经验学习、知识检索、自动调优和优化循环的接口，但大多是确定性规则和启发式，不是完整自动开发 Agent。

完整闭环核验：

| 环节               | 当前状态                                                 |
| ------------------ | -------------------------------------------------------- |
| 需求分析           | `PlanningSkill` 固定拆解，可用但浅                       |
| 生成算法方案       | `AlgorithmSkill`/`CodeGenerationSkill` 规则输出          |
| 生成 C/C++ 代码    | 未真实生成可编译 C/C++；示例为 Python 伪代码且有语法错误 |
| 写入文件           | 主流程不写核心代码                                       |
| 自动编译           | 无主流程编译                                             |
| 自动运行测试       | 无主流程测试                                             |
| 读取错误           | 无                                                       |
| 自动修复           | 无                                                       |
| 再编译和测试       | 无                                                       |
| 保存 Prompt 和过程 | Prompt 填充会写日志，但不是完整代码生成过程              |
| 干净环境复现       | 未验证                                                   |

因此，不能因为存在 `agent/code_generation_skill.py` 就判定赛题要求的 Agent 代码生成闭环已完成。

## 8. 当前完成度评分

| 维度                  | 分数 | 主要依据                                                                                                                             |
| --------------------- | ---: | ------------------------------------------------------------------------------------------------------------------------------------ |
| 工程架构              |   72 | 模块丰富，主流程完整，但膨胀和平行实现明显                                                                                           |
| 代码质量              |   62 | 核心 C 代码可由 MSVC 编译并通过现有测试，但 `.so`/`.dll`、`/tmp`、符号导出和编码处理缺乏跨平台抽象                                   |
| 测试质量              |   58 | Windows 实际运行 339 个 Python 测试，17 个因跨平台路径报错；6 个 C 测试程序共 41/41 用例通过，但 CTest 未注册且覆盖范围有限          |
| 文档质量              |   60 | 文档多，部分过期或互相冲突                                                                                                           |
| Agent 完整性          |   48 | 有编排和日志，LLM/生成闭环不足                                                                                                       |
| Agent 代码生成闭环    |   18 | 仅伪代码和 Prompt，无自动开发闭环                                                                                                    |
| HCCL/HCOMM 接口兼容性 |   20 | 自定义 CPU 接口，未链接 CANN/HCOMM                                                                                                   |
| primitive 覆盖        |   35 | Python 表示覆盖，C 数据实现不足                                                                                                      |
| 算法实现完整性        |   42 | 多个 AllReduce count=1 CPU 模拟，其他 primitive 缺失                                                                                 |
| 模拟器真实性          |   32 | 数学模型未校准                                                                                                                       |
| 硬件感知              |   38 | 静态建模，非自动探测                                                                                                                 |
| 可靠性                |   35 | 模拟组件存在，无真实协议/长压测                                                                                                      |
| 性能验证              |   25 | 仅模拟报告，无实机/校准                                                                                                              |
| 可复现性              |   45 | Windows CPU 构建和 C 测试已复现，但需要额外 DLL 导出参数，CTest 未注册，Python loader 仍依赖 Linux `.so`，Linux/CANN/Ascend 尚未验证 |
| 比赛交付完整性        |   28 | 缺标准接口、正确性、实机/模拟器可信证据                                                                                              |

总分：

1. 项目原型完成度：`58/100`。
2. 赛题验收准备度：`30/100`。

主要加分项：主流程完整、模块覆盖广、CPU 动态库调用存在、测试数量较多、Prompt/日志有雏形。主要扣分项：三种 primitive 未真实实现、CANN/HCOMM 未接入、混精度缺失、性能模型未校准、Agent 代码生成闭环缺失。最大不确定性：Windows CPU 模式已完成动态验证，但 Linux `.so` 构建、Python ctypes 对 Windows DLL 的调用、CANN/HCOMM 标准接口以及 Ascend 实机正确性和性能仍未验证。

## 9. 审计证据附录

全文读取文件：`README.MD`、`project_tree.txt`、赛题 DOCX、`docs/project_documentation.md`、`docs/competition_analysis.md`、`docs/gap_analysis.md`、`docs/agent_capabilities.md`、`docs/simulator_guide.md`、`docs/deepseek_setup.md`、`docs/cann_hccl_interface_guide.md`、`hcccl/README.md`、`CLAUDE.md`、核心源码/测试/配置/脚本。

缺失可选文件：`docs/design_overview.md`、`docs/developer_guide.md`、`docs/competition_requirements.md`。

部分读取文件：`experiments/reports/*`、`experiments/scenarios/*`、`analysis/*`。理由：多为自动生成报告或辅助分析，已抽样核验与主流程关系。

历史记录：third_party/cann-hccl 曾以无 .gitmodules 配置的孤立 gitlink 存在，未包含可读取源码；V1 Linux CI 清理阶段已将该无效索引项移除。

执行命令摘要：Windows 预检、`git ls-files` 受控清单、UTF-8 文档读取、DOCX XML 提取、源码/测试定向读取、Conda Python unittest、Visual Studio 2022 CMake/MSBuild 构建、CTest 检查以及 6 个 C 测试程序手动执行。未执行 `git add`、`git commit`、`git push`，未安装额外项目依赖。

动态验证：

| 项                         | 结果                                                                                                      |
| -------------------------- | --------------------------------------------------------------------------------------------------------- |
| Windows Python 环境        | Conda 环境 `hccl-agent`，解释器位于 `C:\Users\86159\anaconda3\envs\hccl-agent\python.exe`                 |
| Python unittest            | 运行 339 个测试，出现 17 个 error，未显示 assertion failure                                               |
| Python 错误分类            | 16 个与 loader 固定寻找 `hcccl/build/libhccl_plugin.so` 有关；1 个与测试写死 `/tmp/_test_calib.json` 有关 |
| LLM 测试                   | 输出为 `MagicMock` 响应，没有明确证据表明产生真实 DeepSeek 网络请求                                       |
| Windows CMake 配置         | Visual Studio 17 2022、x64、Release，配置成功                                                             |
| 默认 Windows 构建          | DLL 可生成，但未生成导入库，6 个测试目标因 `LNK1181` 无法链接                                             |
| 补充导出配置               | 使用 `CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON` 后成功生成 `hccl_plugin.dll` 和 `hccl_plugin.lib`              |
| C/C++ 构建                 | MSVC/MSBuild 构建成功，退出码 0                                                                           |
| CTest                      | 返回 `No tests were found`；退出码 0 仅表示 CTest 正常结束，不代表测试通过                                |
| communicator/topology 测试 | `test_topology.exe`：9/9 通过                                                                             |
| Ring 测试                  | `test_ring.exe`：6/6 通过                                                                                 |
| Butterfly 测试             | `test_butterfly.exe`：6/6 通过                                                                            |
| NHR 测试                   | `test_nhr.exe`：7/7 通过                                                                                  |
| Mesh 测试                  | `test_mesh.exe`：6/6 通过                                                                                 |
| Fat-Tree 测试              | `test_fattree.exe`：7/7 通过                                                                              |
| C 测试总计                 | 6 个测试程序，41 个用例，41 个通过，0 个失败                                                              |
| 已验证限制                 | FP16 和 PROD 明确返回 `NOT_SUPPORTED`；测试只证明有限 FP32/SUM CPU 模拟                                   |
| 编码状态                   | MSVC 仍出现 `C4819`，控制台 UTF-8 字符存在乱码                                                            |
| Windows Python Bridge      | 尚未验证；当前 loader 固定寻找 Linux `.so`                                                                |
| Linux/CANN/Ascend          | Linux `.so`、CANN/HCOMM 和 Ascend 实机仍未动态验证                                                        |

审计完成后的允许修改范围：仅应包含 `docs/project_audit.md` 与 `docs/roadmap_v2.md`。

## 10. 2026-07-30 G2-D 增量审计

本节覆盖基线审计后的 G2-D 事实，旧章节中的历史测试数量和“Linux `.so` 未验证”等结论不得再作为当前状态引用。

| 审计项 | 当前证据 |
|---|---|
| 默认后端 | `CPU_SIM`，Windows/Linux CLI 均实际通过 |
| 官方模拟后端 | `ASCEND_HCCL_VM`，仅显式 CLI 启用 |
| 官方闭环 | 2-rank INT32 SUM AllReduce，16 elements，外层退出码 0 |
| Checker | 两次 `Checker Success`，五个 stage success，metadata 完全匹配 |
| Warning | ErrorCode 103 共 4 条，状态为 `PASS_WITH_WARNING` |
| 致命错误 | 无 Segmentation fault、MPI_ABORT、undefined symbol、fatal failure |
| HCCL-VM | 正常关闭，无相关遗留进程 |
| Windows Python | 507 tests，OK，1 skipped |
| Linux Python | 507 tests，OK，1 skipped，使用新构建 CPU_SIM `.so` |
| Windows/Linux CTest | 各 11/11 PASS |
| 官方源码 | HCOMM/HCCL 已跟踪工作树最终均为空 |
| Evidence | `experiments/hccl_vm/evidence/g2_d_20260730T081052.668860Z` |

审计边界：CPU_SIM 是工程模拟；`ASCEND_HCCL_VM` 是 subprocess 驱动官方 hccl_test/checker 的官方模拟验证；两者都不是真实 Ascend NPU 验证，且后者不是 hccl-agent 直接 HCCL API 调用。G2-D 的完成不改变真实多设备正确性、真实性能、硬件可靠性和直接 HCOMM/HCCL 集成仍未验证的边界。详细命令、commits、SHA256 和 G2-E 入口见 `docs/g2_d_validation_report.md`。
