# HCCL Agent 比赛准备度报告

更新时间：2026-07-30 08:42:39 +08:00

## 1. 当前架构

当前项目是 `Python Agent + CPU_SIM C 插件 + 数学/可靠性模拟器 + CANN/Ascend 适配准备层`。

```text
main.py
  -> agent/hccl_agent.py
  -> skills / simulator / plugin
  -> plugin/hccl_api.py
  -> hcccl/Release/hccl_plugin.dll
  -> hcccl/src CPU_SIM algorithms
```

实现边界：

| 层级 | 当前状态 | 说明 |
|------|----------|------|
| Python Agent | 真实工程编排 | 可执行 planning、selection、simulation、execution、evaluation、reflection、logging |
| C 插件 | `CPU_SIMULATED` | 单进程 CPU buffer 正确性基线，不是真实多卡通信 |
| ctypes bridge | Windows DLL 已验证 | `HCCL_PLUGIN_PATH` 可指向本轮构建 DLL |
| Linux CPU_SIM validation | `LINUX_CI_VERIFIED`, `CI_REMOTE_VERIFIED`; local Docker `ENV_BLOCKED` | GitHub Actions `pull_request` / `linux-cpu-sim` PASS；本地 Docker build 仍因 `auth.docker.io` token 获取超时未完成 |
| Simulator | `ANALYTICAL_MODEL` | latency/bandwidth/score 为模型趋势，不是实机 profiling |
| Reliability | `RELIABILITY_MODEL` | 固定 seed 可靠性模拟，不是硬件故障切换证明 |
| ASCEND_CANN | `STUB_UNVERIFIED` 准备边界 | 缺 SDK 时快速失败，未链接真实 CANN/HCOMM |

## 2. 三种 Primitive

| Primitive | CPU_SIM 状态 | C/Python 证据 | 未验证边界 |
|-----------|--------------|---------------|------------|
| AllReduce | 已实现；V1-B 已验证多元素 `count>1` | `hcccl/src/hccl_algorithms.c`、`tests/test_reduce_ops.py`、CTest | 真实 HCCL 多 rank 未验证 |
| AllGather | 已实现 | `hcccl/tests/test_allgather.c`、`tests/test_allgather.py` | 真实 HCCL 多 rank 未验证 |
| ReduceScatter | 已实现；V1-B 已验证 2-rank 正确长度 buffer | `hcccl/tests/test_reducescatter.c`、`tests/test_reducescatter.py` | 真实 HCCL 多 rank 未验证 |
| Broadcast | 明确未支持 | `hcccl/tests/test_api_wrappers.c` | 不得宣称已实现 |

## 3. DType / ReduceOp 支持矩阵

| 能力 | 当前状态 | 说明 |
|------|----------|------|
| FP32 | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | AllReduce、AllGather、ReduceScatter |
| FP16 | `CPU_EMULATED_FP16`, `REFERENCE_VERIFIED` | 16-bit buffer，CPU 内部转 FP32 计算 |
| BF16 | `CPU_EMULATED_BF16`, `REFERENCE_VERIFIED` | 16-bit buffer，CPU 内部转 FP32 计算 |
| SUM | 已验证 | AllReduce、ReduceScatter |
| PROD | 已验证 | AllReduce、ReduceScatter |
| MAX | 已验证 | AllReduce、ReduceScatter |
| MIN | 已验证 | AllReduce、ReduceScatter |

详细矩阵见 `docs/correctness_matrix.md`。

赛题原文要求 FP16/BF16/FP32 混精度通信误差 `<=1e-6` 且无溢出/下溢。当前 FP16 `1e-3`、BF16 `2e-2` 是 CPU 软件模拟回归 tolerance，不代表 Ascend 硬件精度或最终赛题阈值已满足；该口径标记为 `REQUIRES_COMPETITION_CLARIFICATION`。

## 4. CPU_SIM 说明

CPU_SIM 使用项目自有 C 动态库在单进程 CPU 内存上计算扁平 buffer。它用于证明接口、数据布局、dtype 编码和 reference correctness，不代表真实 HCCL/CANN 通信性能。

当前 V1 Windows 验证使用：

```text
F:\build\hccl-agent-v1-final\Release\hccl_plugin.dll
```

Linux `.so` 已由 GitHub Actions Linux CPU_SIM 验证通过：

```text
Event：pull_request
Job：linux-cpu-sim
Result：PASS
Python：3.10.20
CMake：3.31.6
Compiler：GCC 11.4.0
Backend：CPU_SIM
Linux plugin：/tmp/hccl-agent-linux-review/libhccl_plugin.so
CTest：11/11 passed
Targeted Python：66 tests OK
Full Python：461 tests OK
LINUX_CPU_SIM_VALIDATION_OK：observed
```

本地 Docker build 阶段仍因镜像 metadata 下载超时标记为 `ENV_BLOCKED`；该本地阻塞不再阻塞 V1，因为 Linux CI 已通过。Linux 状态为 `LINUX_CI_VERIFIED`，不是 `LINUX_DOCKER_VERIFIED`。

## 5. Agent 开发闭环

Stage E1 完成 `OFFLINE_TEMPLATE` 最小闭环：

```text
需求 -> 生成临时代码 -> py_compile 失败 -> 读取错误 -> 模板修复 -> 再编译 -> 自测通过
```

该闭环不调用 DeepSeek/OpenAI/Anthropic，不读取 API Key，不访问网络，不写入生产源码。它证明项目具备受控自动开发演示能力，但不代表真实 LLM 自动开发能力已经验收。

## 6. 拓扑和成本模型

D1 后主模型为 `topology.graph_builder.CommunicationGraph`，`Simulator.evaluate()` 通过统一图模型和 `CostModelEngine` 估算：

```text
latency = startup_cost
        + communication_steps * per_step_latency
        + transferred_bytes / effective_bandwidth
        + contention_penalty
```

模型已覆盖 message size、HCCS/RoCE/PCIe 链路类型和 8/64/128/256/1024 rank 规模趋势。参数来源、假设和未校准边界见 `docs/topology_cost_model.md`。

## 7. 可靠性模型

F1 可靠性验证提供固定 seed 场景：

| 故障类型 | 当前状态 |
|----------|----------|
| link_down | 可注入，可进入 health/failover 统计 |
| timeout | 可注入，可进入 retry 统计 |
| corruption | 通过 CRC32 检测模拟 payload |
| congestion | 可注入，可改变链路带宽 |

报告见 `docs/reliability_report.md`。其中 failover 时间为模型时间，wall-clock 仅为观察值，不是硬件 SLA。

## 8. Windows 动态验证

当前最近一次 V1 验证结果：

| 验证项 | 结果 |
|--------|------|
| Windows Release CMake | 通过，`F:\build\hccl-agent-v1-final`，`HCCL_BACKEND=CPU_SIM` |
| Release Build | 通过，生成 `F:\build\hccl-agent-v1-final\Release\hccl_plugin.dll`，未出现 C4819 |
| CTest | 11/11 passed |
| 定向 correctness suite | 66 tests OK |
| 完整 Python unittest | 461 tests OK |
| 固定 seed 随机 correctness | 3 seeds，60 个确定性抽样 cases，两次连续运行 OK；不是完整笛卡尔积穷举 |
| ASCEND_CANN 缺 SDK检测 | 按预期快速失败，错误说明缺头文件、库和环境变量 |
| 外部 API | API Key 已清空；无真实网络请求 |

## 9. Linux/CANN/Ascend 验证边界

- Linux `libhccl_plugin.so` 已在 GitHub Actions CPU_SIM runner 验证，路径为 `/tmp/hccl-agent-linux-review/libhccl_plugin.so`。
- 本地 Docker Linux 验证仍为 `ENV_BLOCKED`，原因是 `auth.docker.io` token timeout；本地复现可选，不再阻塞 V1。
- CANN SDK 未安装，未链接真实 HCCL/HCOMM 库。
- Ascend 设备、真实多卡 rank、stream、communicator 和 profiling 未验证。
- FP16/BF16 硬件精度、溢出、NaN/Inf 行为未验证。
- 真实可靠性故障注入、硬件 CRC、重试率和 failover 时间未验证。

## 10. 与赛题逐项映射

| 赛题相关项 | 当前状态 | 准备度 |
|------------|----------|--------|
| 至少三种集合通信原语 | CPU_SIM 已覆盖 AllReduce/AllGather/ReduceScatter | 中 |
| C/C++ 实现 | C 插件可构建和测试 | 中 |
| 基于 CANN/HCOMM | 仅完成适配准备，未接入 | 低 |
| Agent 参与算法/代码开发 | 离线最小闭环已验证 | 中 |
| 性能优化 | 有模型排序和拓扑成本模型 | 中-低 |
| 可靠性 | 有固定 seed CPU_SIM 模型 | 中-低 |
| Linux CPU_SIM 交付验证 | GitHub Actions 已验证 `.so`、CTest 和 Python correctness | 中 |
| 实机验证材料 | 模板和用户待办已准备 | 低 |

## 11. 可演示内容

- Windows 下构建 `hccl_plugin.dll` 并运行 11 个 CTest。
- 设置 `HCCL_PLUGIN_PATH` 后运行 Python correctness suite。
- 展示 AllReduce/AllGather/ReduceScatter FP32/FP16/BF16 CPU_SIM 正确性。
- 展示 E1 离线自动开发闭环。
- 展示 D1 拓扑/成本模型随 message size、link type、rank scale 变化。
- 展示 F1 固定 seed 可靠性报告。
- 展示 G1 `ASCEND_CANN` 缺 SDK 快速失败和用户实机操作手册。

## 12. 用户后续操作

用户仍需提供或执行：

- 本地 Docker/Linux `.so` 复现可选；V1 不再因此阻塞。
- CANN 8.0+ 或赛题指定版本 SDK。
- Ascend 设备或赛题认可模拟环境。
- HCCL/HCOMM 头文件、库和环境初始化脚本。
- FP16/BF16、三种 primitive 和 ReduceOp 的实机正确性结果。
- msprof 或等价 profiling 摘要。
- 真实可靠性故障注入与长时间压测结果。

详细步骤见 `docs/user_actions.md`。

## 13. 风险和剩余 P0

| 风险 | 影响 | 处理方向 |
|------|------|----------|
| 无真实 CANN/HCOMM 链接 | 不能满足最终硬性验收 | 用户提供 SDK 后执行 ASCEND_CANN 适配 |
| 无 Ascend 实机 | 性能、精度、可靠性无法最终证明 | 获取设备或官方模拟环境 |
| 本地 Docker Linux 复现阻塞 | 本机无法复现 Linux CI 结果 | 需要时由用户在网络可访问 `auth.docker.io` 的环境执行 UA-V1-001 |
| 模型性能未校准 | score 不能作为比赛性能结论 | 使用 msprof 数据校准 D1 |
| Broadcast 未实现 | 若赛题要求 Broadcast 会缺口明显 | 后续单独 Batch，不在 H1 新增 |

## 14. 不得宣称的能力

- 不得宣称已经接入真实 CANN/HCOMM。
- 不得宣称 Windows DLL 等同 Linux `.so` 或 Ascend 运行结果。
- 不得宣称本地 Docker Linux 已验证；当前 Linux 结论来自 GitHub Actions CPU_SIM。
- 不得宣称 CPU_SIM latency/bandwidth/score 是真实 HCCL 性能。
- 不得宣称 FP16/BF16 CPU 软件模拟等同 Ascend 硬件精度。
- 不得宣称 F1 模型 failover 时间满足真实硬件 SLA。
- 不得宣称真实 DeepSeek/OpenAI Agent 自动开发闭环已验收。
