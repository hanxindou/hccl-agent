# HCCL Agent 用户待办

## UA-001：Linux .so 验证

状态：待用户执行
阻塞阶段：V1-D
优先级：P1

### 原因

本轮 V1 执行优先使用 Windows Docker Desktop 的 Linux 容器验证。若 Docker 不可用，则保持 `ENV_BLOCKED`；Windows DLL 已验证不能等同于 Linux `.so`。

### 用户需要准备

- Docker Desktop Linux 容器，或用户自行准备的 Linux 环境
- CMake 与 C 编译器
- Python 3.10

### 操作步骤

1. 在 Linux 容器或 Linux 项目目录进入当前仓库。
2. 使用独立构建目录构建 CPU_SIM 插件。
3. 指向实际生成的 `.so` 运行 CTest 和 Python 回归。

### 执行命令

```bash
BUILD_DIR=/tmp/hccl-agent-linux-review
rm -rf "$BUILD_DIR"
cmake -S hcccl -B "$BUILD_DIR"
cmake --build "$BUILD_DIR"
ctest --test-dir "$BUILD_DIR" --output-on-failure
export HCCL_PLUGIN_PATH="$BUILD_DIR/libhccl_plugin.so"
unset DEEPSEEK_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY
python -m unittest tests.test_reducescatter tests.test_execution_engine tests.test_hccl_api -q
python -m unittest discover tests -q
```

### 预期输出

```text
CTest 100% tests passed
Python unittest 0 failures, 0 errors
```

### 反馈内容

- CMake/CTest 完整输出
- 实际 `.so` 路径
- Python 测试输出

### 当前降级状态

Windows `hccl_plugin.dll` 已验证；Linux `.so` 标记为未验证。

## UA-002：CANN/HCOMM/Ascend 实机验证准备

状态：待用户执行
阻塞阶段：G1/H1
优先级：P0

### 原因

当前环境缺少 CANN SDK、HCOMM 运行环境、Ascend NPU 和 msprof，无法完成赛题要求的实机验证。

### 用户需要准备

- CANN 8.0 或赛题指定版本 SDK
- Ascend 910B/910C 或赛题允许的模拟器环境
- HCOMM/HCCL 头文件与库
- msprof 或对应 profiling 工具
- 管理员/驱动安装权限

### 操作步骤

1. 安装并初始化 CANN 环境。
2. 提供 SDK 路径、版本信息和环境初始化命令输出。
3. 使用 `-DHCCL_BACKEND=ASCEND_CANN` 和真实 SDK 根目录执行配置。
4. 运行单机正确性、FP16/BF16 正确性和 profiling 模板。

### 执行命令

```bash
which npu-smi || true
npu-smi info
python3 -c "import os; print(os.environ.get('ASCEND_HOME_PATH'))"
source /usr/local/Ascend/ascend-toolkit/set_env.sh
cmake -S hcccl -B /tmp/hccl-agent-hcccl-cann \
  -DHCCL_BACKEND=ASCEND_CANN \
  -DHCCL_CANN_ROOT="$ASCEND_HOME_PATH"
cmake --build /tmp/hccl-agent-hcccl-cann
ctest --test-dir /tmp/hccl-agent-hcccl-cann --output-on-failure
```

### 预期输出

```text
CANN/Ascend 环境变量可见
npu-smi 能列出设备或模拟器状态
```

### 反馈内容

- CANN 版本
- SDK 安装路径
- HCOMM/HCCL 头文件和库路径
- `npu-smi info` 输出
- msprof 可用性
- `ASCEND_CANN` 配置、构建和 CTest 输出
- 单机 AllReduce、AllGather、ReduceScatter、FP16/BF16 正确性输出

### 当前降级状态

项目当前为 `CPU_SIMULATED`，不得宣称真实 CANN/HCOMM 或 Ascend 已验证。

## UA-003：FP16/BF16 Ascend 实机误差验证

状态：待用户执行
阻塞阶段：G1/H1
优先级：P0

### 原因

C3-B 已完成 FP16/BF16 CPU 软件模拟，但该结果不能代表 Ascend 混合精度硬件行为或赛题最终精度结论。

### 用户需要准备

- Ascend 设备或赛题允许的 Ascend 模拟环境
- CANN/HCCL 运行环境
- 实机可执行的 AllReduce、AllGather、ReduceScatter correctness case

### 反馈内容

- FP16/BF16 最大绝对误差
- FP16/BF16 最大相对误差
- NaN、Inf、overflow 行为
- CANN/HCCL 版本和设备型号

## UA-004：Stage E1 用户待办

状态：无新增用户操作
阻塞阶段：无
优先级：P2

### 原因

E1 使用 `OFFLINE_TEMPLATE` 离线模式，不需要用户提供 API Key、网络权限、管理员权限、SDK 或硬件。

### 后续说明

若未来人工启用 `EXTERNAL_LLM` 模式，必须由用户显式提供凭据并确认允许调用外部模型；自主 Goal 不启用该模式。

## UA-005：D1 模型实机校准

状态：待用户执行
阻塞阶段：G1/H1
优先级：P1

### 原因

D1 输出为 `CPU_SIMULATED / ANALYTICAL_MODEL`。参数来自项目相对 tier，尚未用 Ascend、CANN/HCCL 或 msprof 校准。

### 用户需要准备

- Ascend 实机或赛题允许的模拟环境
- CANN/HCCL 运行时
- 不同 message size、rank scale 和 link type 的 profiling 数据

### 反馈内容

- 8/64/128/256/1024 rank 的 latency 和 bandwidth
- HCCS/RoCE/PCIe 或等效链路实测参数
- msprof 或同等 profiling 摘要

## UA-006：F1 真实可靠性验收

状态：待用户执行
阻塞阶段：H1/比赛最终验收
优先级：P1

### 原因

F1 当前结果来自 `CPU_SIMULATED / RELIABILITY_MODEL`。固定 seed、CRC32、retry 和 failover 统计可复现，但不能证明真实 Ascend/HCCL 链路故障、硬件 CRC、重传或故障切换时间。

### 用户需要准备

- Ascend 设备或赛题认可的可靠性测试环境
- CANN/HCCL 运行时和故障注入权限
- 可观察链路状态、错误计数和 profiling 的工具

### 反馈内容

- link down、timeout、corruption、congestion 的实机注入方式
- 真实检测次数、重试次数、恢复次数和失败案例
- 实测 failover 时间分布
- 硬件 CRC 或等效校验路径
- 长时间可靠性压测摘要
