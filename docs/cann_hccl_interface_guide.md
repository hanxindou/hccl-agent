# HCCL Agent 项目接口参考与仿真实现指南

## Stage G1 CANN/Ascend 适配准备

当前项目支持两个明确隔离的后端配置：

| 后端 | CMake 参数 | 当前状态 | SDK 要求 | 验证边界 |
|------|------------|----------|----------|----------|
| CPU_SIM | `-DHCCL_BACKEND=CPU_SIM` | 默认可构建 | 不需要 CANN | Windows DLL、CTest、Python 回归 |
| ASCEND_CANN | `-DHCCL_BACKEND=ASCEND_CANN` | `STUB_UNVERIFIED` 适配边界 | 需要真实 CANN/HCCL SDK | 当前环境未验证，缺 SDK 时快速失败 |

G1 不接入真实 HCOMM 运行时，不使用 Stub 库冒充 CANN，也不生成虚假 msprof 结果。`ASCEND_CANN` 模式只准备条件编译、头文件/库探测和用户实机验收入口；默认 `CPU_SIM` 路径必须继续不依赖 SDK。

### 目标 CANN 版本和组件

目标版本以赛题最终通知为准，当前准备项按 CANN 8.0+ 组织。用户需要提供：

| 组件 | 用途 | 典型线索 |
|------|------|----------|
| HCCL/HCOMM 头文件 | 标准接口声明 | `hccl/hccl.h`、`hccl.h`、`hccl_types.h` |
| HCCL 运行库 | 链接真实通信库 | `libhccl.so` 或平台等价库 |
| 环境初始化脚本 | 设置 SDK 路径和运行库路径 | `set_env.sh` 或 CANN 安装文档指定脚本 |
| Profiling 工具 | 性能和可靠性证据 | `msprof` 或当前 CANN 版本等价工具 |
| 设备工具 | 设备状态采集 | `npu-smi` |

可能的安装目录包括：

```text
/usr/local/Ascend/ascend-toolkit/latest
/usr/local/Ascend/latest
```

也可以通过以下变量显式传入：

```text
HCCL_CANN_ROOT
ASCEND_HOME_PATH
ASCEND_HOME
CANN_HOME
```

### CMake 使用方式

CPU_SIM 默认构建：

```powershell
cmake -S hcccl -B C:\tmp\hccl-agent-hcccl-g1 -DHCCL_BACKEND=CPU_SIM
cmake --build C:\tmp\hccl-agent-hcccl-g1 --config Release
ctest --test-dir C:\tmp\hccl-agent-hcccl-g1 -C Release --output-on-failure
```

ASCEND_CANN 探测构建：

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
cmake -S hcccl -B /tmp/hccl-agent-hcccl-cann \
  -DHCCL_BACKEND=ASCEND_CANN \
  -DHCCL_CANN_ROOT="$ASCEND_HOME_PATH"
```

如果 SDK 缺失，配置阶段必须失败，并指出缺少 HCCL 头文件、库或环境变量。该失败是预期行为，不应通过 Stub 库绕过。

### 标准接口映射表

| 标准能力 | 当前 CPU_SIM 状态 | ASCEND_CANN 准备状态 | 真实验收要求 |
|----------|-------------------|----------------------|--------------|
| Communicator | 项目自有 `HcclComm` 句柄模拟 | 待映射真实 HCOMM/HCCL communicator | 初始化、rank、rank size 与标准一致 |
| AllReduce | FP32/FP16/BF16 CPU_SIM 数据路径 | 待实机 wrapper 对齐 | 与 HCCL reference 数值一致 |
| AllGather | FP32/FP16/BF16 CPU_SIM 数据路径 | 待实机 wrapper 对齐 | 各 rank 扁平 buffer 一致 |
| ReduceScatter | FP32/FP16/BF16 CPU_SIM 数据路径 | 待实机 wrapper 对齐 | scatter 分片与 reference 一致 |
| Broadcast | wrapper 仍为未实现边界 | 待后续阶段 | 不得伪造成功 |
| ReduceOp | SUM/PROD/MAX/MIN CPU_SIM | 待实机 op 枚举映射 | 枚举值、错误码和 dtype 行为一致 |
| Stream | 当前不执行真实 device stream | 待 Ascend stream 绑定 | 需要真实运行时验证 |
| 错误码 | 项目自定义兼容码 | 待与 HCCL 标准错误码校正 | 参数错误、未支持、运行时错误可区分 |

### 实机测试命令模板

单机正确性：

```bash
export HCCL_PLUGIN_PATH=/path/to/libhccl_plugin.so
unset DEEPSEEK_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY
python -m unittest tests.test_hccl_api tests.test_execution_engine -q
python -m unittest tests.test_allgather tests.test_reducescatter tests.test_dtype_emulation -q
```

FP16/BF16 误差采集：

```bash
python -m unittest tests.test_dtype_emulation -q
```

Profiling 模板：

```bash
msprof --application="./path/to/correctness_or_benchmark" --output="./msprof_output"
```

baseline 对比方法：

1. 使用相同 rank、dtype、op、count 和 message size。
2. 分别运行项目 wrapper 与官方 HCCL reference。
3. 记录最大绝对误差、最大相对误差、NaN/Inf/overflow 行为。
4. 记录 latency、bandwidth、错误码和 profiling 摘要。
5. 将结果标注为真实硬件测量，不与 CPU_SIM 数学模型混写。

## Batch A1 接口与验证边界

当前项目的 `hcccl/` 目录提供的是 CPU 模拟基线和 HCCL-like 接口声明，不声明已经完成真实 CANN/HCOMM ABI 兼容。Windows CPU 模式、Linux CPU 模式和 Ascend/CANN 模式必须分开记录：

| 模式 | 当前状态 | 说明 |
|------|----------|------|
| Windows CPU | 已验证 | 默认 CMake 构建 DLL/import lib，CTest 运行 11 个 C 测试 |
| Linux CPU | 待环境验证 | 应使用外部 `/tmp` 构建目录生成 `.so` 并运行 CTest |
| Ascend/CANN | 未接入 | 需要 CANN 8.0+、HCOMM 头库和硬件或官方模拟器 |

当前 C 数据路径覆盖 AllReduce、AllGather、ReduceScatter 的 CPU_SIM 正确性基线，并已覆盖 FP32 SUM/PROD/MAX/MIN 与 FP16/BF16 软件模拟。Broadcast 仍不得伪造成功，真实 CANN/HCOMM 适配仍未验证。

## 1. 文档目的

本文档用于记录 HCCL（Huawei Collective Communication Library）在本项目中的关键接口、数据结构以及后续仿真实现方案。

本项目不依赖真实昇腾 NPU 环境，而是采用：

```text
Agent
 ↓
HCCL Compatibility Layer
 ↓
Simulator
 ↓
Performance Evaluation
```

方式完成赛题要求。

因此本文档重点关注：

* HCCL 标准接口
* 通信域管理
* 集合通信原语
* Agent 项目中的映射关系

而不关注底层驱动实现。

---

# 2. HCCL 源码位置

当前源码目录：

```text
third_party/
└── cann-hccl/
```

关键目录：

```text
cann-hccl/

├── inc/
│   └── hccl/
│       ├── hccl.h
│       └── hccl_types.h

├── src/
│   └── domain/
│       └── collective_communication/

├── docs/

└── test/
```

其中：

```text
hccl.h
```

定义标准接口。

```text
hccl_types.h
```

定义数据类型和通信对象。

---

# 3. HCCL 基本概念

## 3.1 Rank

Rank 表示一个通信参与者。

例如：

```text
8卡训练
```

对应：

```text
Rank0
Rank1
Rank2
Rank3
Rank4
Rank5
Rank6
Rank7
```

每个 Rank 对应一个 NPU。

在模拟器中：

```python
rank_id
```

即可表示。

---

## 3.2 Communicator

HCCL 使用 Communicator 表示通信域。

源码定义：

```cpp
typedef void *HcclComm;
```

说明：

```text
HcclComm 本质是通信上下文句柄
```

在本项目中计划映射为：

```python
class HcclComm:
    rank
    rank_size
    topology
```

---

# 4. 返回值

源码定义：

```cpp
typedef enum {
    HCCL_SUCCESS = 0,
    HCCL_E_PARA,
    HCCL_E_PTR,
    HCCL_E_MEMORY,
    HCCL_E_INTERNAL,
    ...
} HcclResult;
```

常用返回值：

| 返回值             | 含义   |
| --------------- | ---- |
| HCCL_SUCCESS    | 成功   |
| HCCL_E_PARA     | 参数错误 |
| HCCL_E_PTR      | 空指针  |
| HCCL_E_MEMORY   | 内存不足 |
| HCCL_E_INTERNAL | 内部错误 |
| HCCL_E_TIMEOUT  | 超时   |

仿真环境中仅需实现：

```text
SUCCESS
PARA_ERROR
INTERNAL_ERROR
```

即可。

---

# 5. 数据类型

源码定义：

```cpp
HCCL_DATA_TYPE_INT8
HCCL_DATA_TYPE_INT16
HCCL_DATA_TYPE_INT32
HCCL_DATA_TYPE_INT64

HCCL_DATA_TYPE_FP16
HCCL_DATA_TYPE_FP32
HCCL_DATA_TYPE_FP64
```

推荐映射：

| HCCL  | Python     |
| ----- | ---------- |
| INT8  | np.int8    |
| INT16 | np.int16   |
| INT32 | np.int32   |
| INT64 | np.int64   |
| FP16  | np.float16 |
| FP32  | np.float32 |
| FP64  | np.float64 |

---

# 6. Reduction 操作

源码定义：

```cpp
HCCL_REDUCE_SUM
HCCL_REDUCE_PROD
HCCL_REDUCE_MAX
HCCL_REDUCE_MIN
```

对应：

| 操作   | 说明  |
| ---- | --- |
| SUM  | 求和  |
| PROD | 连乘  |
| MAX  | 最大值 |
| MIN  | 最小值 |

比赛中主要使用：

```text
SUM
```

即可。

---

# 7. 通信域初始化接口

## HcclCommInitClusterInfo

源码：

```cpp
HcclResult HcclCommInitClusterInfo(
    const char *clusterInfo,
    uint32_t rank,
    HcclComm *comm
);
```

作用：

```text
根据集群配置初始化通信域
```

参数：

| 参数          | 说明     |
| ----------- | ------ |
| clusterInfo | 集群配置文件 |
| rank        | 当前节点编号 |
| comm        | 输出通信域  |

项目映射：

```python
cluster.json
 ↓
HcclComm
```

这是后续所有通信操作的入口。

---

# 8. AllReduce

## 接口

```cpp
HcclAllReduce(
    sendBuf,
    recvBuf,
    count,
    dataType,
    op,
    comm,
    stream
)
```

作用：

```text
所有节点参与归约
归约结果同步给所有节点
```

示例：

Rank0:

```text
[1]
```

Rank1:

```text
[2]
```

Rank2:

```text
[3]
```

Rank3:

```text
[4]
```

SUM 后：

```text
[10]
```

所有 Rank 都获得：

```text
[10]
```

---

## 项目实现

调用：

```python
Simulator.evaluate(
    primitive="AllReduce"
)
```

支持算法：

```text
Ring
Butterfly
Mesh
NHR
FatTree
```

---

# 9. AllGather

## 接口

```cpp
HcclAllGather(
    sendBuf,
    recvBuf,
    sendCount,
    dataType,
    comm,
    stream
)
```

作用：

```text
收集所有 Rank 数据
然后同步给所有 Rank
```

示例：

Rank0:

```text
[A]
```

Rank1:

```text
[B]
```

Rank2:

```text
[C]
```

结果：

```text
[A B C]
```

每个 Rank 都拥有完整数据。

---

## 应用场景

```text
Embedding同步
模型参数同步
梯度聚合前准备
```

---

# 10. ReduceScatter

## 接口

```cpp
HcclReduceScatter(
    sendBuf,
    recvBuf,
    recvCount,
    dataType,
    op,
    comm,
    stream
)
```

作用：

```text
先 Reduce
再 Scatter
```

示例：

先求和：

```text
[10,20,30,40]
```

然后切分：

```text
Rank0 -> [10]
Rank1 -> [20]
Rank2 -> [30]
Rank3 -> [40]
```

---

## 深度学习中的意义

AllReduce 常分解为：

```text
ReduceScatter
+
AllGather
```

因此该原语非常重要。

---

# 11. 当前赛题最低实现要求

根据赛题要求，必须支持：

```text
HcclCommInitClusterInfo
HcclAllReduce
HcclAllGather
HcclReduceScatter
```

这是项目后续开发重点。

---

# 12. Agent 与 HCCL 的关系

目标架构：

```text
Agent
 ↓
Planning
 ↓
Reasoning
 ↓
Algorithm Selection
 ↓
HCCL API
 ↓
Simulator
 ↓
Performance Report
```

示例：

```text
Agent选择 Ring
 ↓
调用 HcclAllReduce
 ↓
Simulator执行
 ↓
输出延迟与带宽
 ↓
生成报告
```

---

# 13. 后续开发路线

Phase 1

```text
实现 HCCL Compatibility Layer
```

接口：

```text
HcclCommInitClusterInfo
HcclAllReduce
HcclAllGather
HcclReduceScatter
```

---

Phase 2

```text
拓扑自动发现
```

支持：

```text
Ring
Mesh
FatTree
```

---

Phase 3

```text
Agent自动选择算法
```

支持：

```text
Ring
Butterfly
Mesh
NHR
FatTree
```

---

Phase 4

```text
故障注入
动态重规划
```

结合：

```text
Reflection
Replanning
```

能力完成完整闭环。

---

# 14. 项目最终展示链路

```text
Cluster Config
        ↓
Topology Discovery
        ↓
Algorithm Selection
        ↓
HcclAllReduce
        ↓
Simulator
        ↓
Benchmark
        ↓
Report
        ↓
Reflection
        ↓
Replanning
```

该链路同时满足：

* HCCL 标准接口
* Agent 自动规划
* 模拟器验证
* Prompt 工程展示

四项赛题核心要求。
