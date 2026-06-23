# HCCL Agent 项目接口参考与仿真实现指南

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
