# HCCL Agent 用户待办

## UA-001：Linux .so 验证

状态：待用户执行
阻塞阶段：C2/G1
优先级：P1

### 原因

本轮自主执行按当前限制未访问 WSL/Linux。Windows DLL 已验证，但不能等同于 Linux `.so`。

### 用户需要准备

- Linux 或 WSL2 环境
- CMake 与 C 编译器
- Python 3.10

### 操作步骤

1. 在 Linux 项目目录进入当前仓库。
2. 使用独立构建目录构建 CPU_SIM 插件。
3. 指向实际生成的 `.so` 运行 CTest 和 Python 回归。

### 执行命令

```bash
BUILD_DIR=/tmp/hccl-agent-hcccl-c2
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
3. 在 G1 后执行 ASCEND_CANN 模式构建和正确性测试。

### 执行命令

```bash
which npu-smi || true
npu-smi info
python3 -c "import os; print(os.environ.get('ASCEND_HOME_PATH'))"
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
