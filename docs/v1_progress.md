# HCCL Agent V1 执行进度

版本：v1.0  
计划文件：`docs/v1_execution_plan.md`  
项目路径：`F:\projects\hccl-agent`  
Codex 环境：Windows Native  
Linux 验证方式：Docker Desktop Linux 容器  
状态：NOT_STARTED

---

## 1. V1 总体状态

| Stage | 名称                                | 状态        | Commit |
| ----- | ----------------------------------- | ----------- | ------ |
| V1-A  | 事实与文档基线修正                  | NOT_STARTED | -      |
| V1-B  | Collective 多元素与 rank 连续性加固 | NOT_STARTED | -      |
| V1-C  | 确定性随机化 correctness            | NOT_STARTED | -      |
| V1-D  | Docker Linux `.so` 验证             | NOT_STARTED | -      |
| V1-E  | Linux CI 与最终材料收敛             | NOT_STARTED | -      |

允许的阶段状态：

```text
NOT_STARTED
IN_PROGRESS
COMPLETED
PARTIAL
BLOCKED
ENV_BLOCKED
SKIPPED
```

---

## 2. 开始基线

开始时间：待填写  
当前分支：待填写  
开始 HEAD：待填写  
远端基线：待填写

### Git 检查

```text
git status --short：
待执行

git status -sb：
待执行

git log -10 --oneline：
待执行
```

### 开始条件

- [ ] 当前目录为 `F:\projects\hccl-agent`
- [ ] Codex 使用 Windows Native 环境
- [ ] 未使用 WSL Codex
- [ ] 工作区干净
- [ ] 无其他活动线程修改同一仓库
- [ ] `docs/v1_execution_plan.md` 已提交
- [ ] `docs/v1_progress.md` 已提交
- [ ] 未发现密钥或凭据
- [ ] 未发现仓库内构建产物

---

# 3. Stage V1-A：事实与文档基线修正

开始时间：  
结束时间：  
状态：NOT_STARTED

## 3.1 修改文件

- 待填写

## 3.2 核验事实

### H1 commit

```text
实际 H1 commit：
待填写
```

### 阶段时间记录

```text
是否存在重叠：
待填写

处理说明：
待填写
```

### Linux 待办路径

```text
旧路径：
待填写

新路径：
待填写
```

### AllReduce 当前限制

```text
V1-B 前状态：
待填写
```

### ReduceScatter 2-rank 当前限制

```text
V1-B 前状态：
待填写
```

### FP16/BF16 精度口径

```text
赛题原文：
待填写

当前 CPU tolerance：
FP16：
BF16：

结论：
待填写
```

## 3.3 验收结果

- `git diff --check`：
- 是否仅修改文档：
- 是否保留所有未验证边界：
- 是否修改运行逻辑：

## 3.4 遇到的问题

- 无，或待填写

## 3.5 降级状态

- 无，或待填写

## 3.6 用户待办

- 无，或待填写

## 3.7 本地提交

```text
commit：
message：
```

## 3.8 未验证边界

- Linux `.so` 仍未验证；
- CANN/HCOMM 仍未接入；
- Ascend 实机仍未验证；
- 本阶段不产生新的运行能力。

---

# 4. Stage V1-B：Collective 多元素与 rank 连续性加固

开始时间：  
结束时间：  
状态：NOT_STARTED

## 4.1 修改文件

- 待填写

## 4.2 最终数据契约

### AllReduce

```text
send[N][C] -> recv[N][C]

send index:
send[src_rank * C + element]

recv index:
recv[dst_rank * C + element]

语义:
recv[dst_rank][element]
=
REDUCE(send[src_rank][element] for all src_rank)
```

实际实现是否符合：待填写

### ReduceScatter

```text
send[N][N][C] -> recv[N][C]

send index:
send[(src_rank * N + dst_rank) * C + element]

recv index:
recv[dst_rank * C + element]

语义:
recv[dst_rank][element]
=
REDUCE(
    send[src_rank][dst_rank][element]
    for all src_rank
)
```

实际实现是否符合：待填写

## 4.3 覆盖矩阵

### AllReduce FP32

| Rank | count=1 | count=3 | count=17 | count=256 |
| ---: | ------- | ------- | -------- | --------- |
|    1 | -       | -       | -        | -         |
|    2 | -       | -       | -        | -         |
|    4 | -       | -       | -        | -         |
|    8 | -       | -       | -        | -         |
|   16 | -       | -       | -        | -         |

ReduceOp：

| ReduceOp | 状态 |
| -------- | ---- |
| SUM      | -    |
| PROD     | -    |
| MAX      | -    |
| MIN      | -    |

### FP16/BF16

| DType | Rank 覆盖 | Count 覆盖 | ReduceOp | 状态 |
| ----- | --------- | ---------- | -------- | ---- |
| FP16  | -         | -          | -        | -    |
| BF16  | -         | -          | -        | -    |

### ReduceScatter rank 连续性

| Rank | 状态 |
| ---: | ---- |
|    1 | -    |
|    2 | -    |
|    4 | -    |
|    8 | -    |
|   16 | -    |

## 4.4 Windows 验收结果

```text
Build directory：
待填写

CMake：
待填写

Build：
待填写

CTest：
待填写

定向 Python：
待填写

完整 Python：
待填写

实际 DLL：
待填写

DLL_LOAD_OK：
待填写

C4819：
待填写

git diff --check：
待填写
```

## 4.5 回归情况

- AllReduce：
- AllGather：
- ReduceScatter：
- FP32：
- FP16：
- BF16：
- SUM/PROD/MAX/MIN：
- B1 动态库加载：
- G1 backend 配置：

## 4.6 遇到的问题

- 无，或待填写

## 4.7 修复轮次

| 问题   | 第一次处理 | 第二次处理 | 最终状态 |
| ------ | ---------- | ---------- | -------- |
| 待填写 | -          | -          | -        |

## 4.8 降级状态

- 无，或待填写

## 4.9 用户待办

- 无，或待填写

## 4.10 本地提交

```text
commit：
message：
```

## 4.11 未验证边界

- 当前仍为单进程 CPU_SIM；
- 不代表真实多卡集合通信；
- FP16/BF16 仍为 CPU 软件模拟；
- Linux 将在 V1-D 验证；
- CANN/HCOMM/Ascend 不属于本阶段。

---

# 5. Stage V1-C：确定性随机化 Correctness

开始时间：  
结束时间：  
状态：NOT_STARTED

## 5.1 修改文件

- 待填写

## 5.2 测试配置

### 固定 seed

```text
-
-
-
```

### Case 数量

```text
每个 seed：
总 case：
```

### 参数空间

```text
Primitive：
Rank：
Count：
DType：
ReduceOp：
```

## 5.3 覆盖结果

| 能力          | 是否覆盖 | 证据 |
| ------------- | -------- | ---- |
| AllReduce     | -        | -    |
| AllGather     | -        | -    |
| ReduceScatter | -        | -    |
| rank=1        | -        | -    |
| rank=2        | -        | -    |
| rank=4        | -        | -    |
| rank=8        | -        | -    |
| rank=16       | -        | -    |
| count>1       | -        | -    |
| FP32          | -        | -    |
| FP16          | -        | -    |
| BF16          | -        | -    |
| SUM           | -        | -    |
| PROD          | -        | -    |
| MAX           | -        | -    |
| MIN           | -        | -    |

## 5.4 可复现性

```text
第一次运行：
待填写

第二次运行：
待填写

结果是否一致：
待填写

失败复现参数支持：
待填写
```

## 5.5 验收结果

```text
随机定向 suite：
待填写

Correctness 定向 suite：
待填写

CTest：
待填写

完整 Python：
待填写

测试时长：
待填写

git diff --check：
待填写
```

## 5.6 失败样例

```text
无，或填写：

seed：
case_index：
primitive：
rank：
count：
dtype：
reduce_op：
expected：
actual：
修复：
```

## 5.7 修复轮次

| 问题   | 第一次处理 | 第二次处理 | 最终状态 |
| ------ | ---------- | ---------- | -------- |
| 待填写 | -          | -          | -        |

## 5.8 降级状态

- 无，或待填写

## 5.9 用户待办

- 无，或待填写

## 5.10 本地提交

```text
commit：
message：
```

## 5.11 未验证边界

- 随机化测试不是形式化证明；
- 仍然只验证 CPU_SIM；
- 不代表真实并发、多进程或硬件通信行为。

---

# 6. Stage V1-D：Docker Linux `.so` 验证

开始时间：  
结束时间：  
状态：NOT_STARTED

## 6.1 Docker 前置检查

```text
docker version：
待填写

docker info：
待填写

Docker Engine 状态：
待填写
```

## 6.2 修改文件

- 待填写

## 6.3 Docker 环境

```text
基础镜像：
待填写

Linux 发行版：
待填写

Compiler：
待填写

CMake：
待填写

Python：
待填写
```

## 6.4 Linux 构建结果

```text
Docker container exit code：
待填写

Linux build directory：
待填写

CMake：
待填写

Build：
待填写

实际 .so 路径：
待填写

.so 文件存在：
待填写
```

## 6.5 Linux 测试结果

```text
CTest：
待填写

ctypes 加载：
待填写

实际 HCCL_PLUGIN_PATH：
待填写

定向 Python：
待填写

完整 Python：
待填写

LINUX_CPU_SIM_VALIDATION_OK：
待填写
```

## 6.6 Windows 回归结果

Linux 相关修复后重新执行：

```text
Windows CMake：
待填写

Windows Build：
待填写

Windows CTest：
待填写

Windows完整 Python：
待填写
```

## 6.7 Docker 阻塞记录

若 Docker 可用：

```text
不适用
```

若 Docker 不可用：

```text
状态：ENV_BLOCKED

首次错误：
待填写

低风险复查：
待填写

停止原因：
待填写

生成的验证脚本：
待填写

用户待办：
待填写
```

## 6.8 修复轮次

| 问题   | 第一次处理 | 第二次处理 | 最终状态 |
| ------ | ---------- | ---------- | -------- |
| 待填写 | -          | -          | -        |

## 6.9 状态结论

选择其一：

```text
LINUX_DOCKER_VERIFIED
ENV_BLOCKED
PARTIAL
```

## 6.10 本地提交

```text
commit：
message：
```

## 6.11 未验证边界

- Docker Linux CPU_SIM 不代表 Ascend；
- Docker `.so` 不代表真实 HCCL/HCOMM；
- 不包含多设备实机验证；
- 不包含 msprof。

---

# 7. Stage V1-E：Linux CI 与最终材料收敛

开始时间：  
结束时间：  
状态：NOT_STARTED

## 7.1 修改文件

- 待填写

## 7.2 GitHub Actions 配置

```text
Workflow：
待填写

触发条件：
待填写

Python：
待填写

Compiler：
待填写

CMake：
待填写

是否复用 Linux validation script：
待填写
```

## 7.3 CI 当前状态

选择其一：

```text
CI_CONFIGURED_UNRUN
CI_REMOTE_VERIFIED
ENV_BLOCKED
```

说明：

```text
待填写
```

未执行 `git push` 时不得填写 `CI_REMOTE_VERIFIED`。

## 7.4 最终 Windows 验收

```text
Build directory：
待填写

CMake Release：
待填写

Build：
待填写

CTest：
待填写

定向 Python：
待填写

完整 Python：
待填写

实际 DLL：
待填写

ASCEND_CANN 缺 SDK 快速失败：
待填写

C4819：
待填写
```

## 7.5 最终 Linux 验收

```text
Docker：
待填写

CMake：
待填写

Build：
待填写

CTest：
待填写

ctypes 加载：
待填写

完整 Python：
待填写

实际 .so：
待填写
```

Docker 被阻塞时应明确填写 `ENV_BLOCKED`，不得填写通过。

## 7.6 最终文档

| 文件                                   | 状态 |
| -------------------------------------- | ---- |
| `docs/v1_progress.md`                  | -    |
| `docs/v1_validation_report.md`         | -    |
| `docs/correctness_matrix.md`           | -    |
| `docs/competition_readiness_report.md` | -    |
| `docs/user_actions.md`                 | -    |
| `README.MD`                            | -    |

## 7.7 构建产物检查

```text
.dll：
.lib：
.exe：
.obj：
.pdb：
.so：
build/：
CMakeFiles/：
__pycache__/：
密钥：
```

## 7.8 本地提交

```text
commit：
message：
```

---

# 8. V1 最终总结

完成时间：  
总体状态：NOT_STARTED

## 8.1 阶段与提交

| Stage | 状态 | Commit | Message |
| ----- | ---- | ------ | ------- |
| V1-A  | -    | -      | -       |
| V1-B  | -    | -      | -       |
| V1-C  | -    | -      | -       |
| V1-D  | -    | -      | -       |
| V1-E  | -    | -      | -       |

## 8.2 最终能力

### Collective correctness

```text
AllReduce 多元素：
待填写

ReduceScatter 2-rank：
待填写

AllGather：
待填写

FP32 ReduceOps：
待填写

FP16：
待填写

BF16：
待填写
```

### 随机化验证

```text
Seed 数：
待填写

Case 数：
待填写

覆盖 Primitive：
待填写

覆盖 Rank：
待填写

覆盖 Count：
待填写

连续运行一致：
待填写
```

### Windows

```text
CMake：
待填写

CTest：
待填写

定向 Python：
待填写

完整 Python：
待填写
```

### Linux

```text
状态：
待填写

Docker：
待填写

.so：
待填写

CTest：
待填写

Python：
待填写
```

### CI

```text
状态：
待填写
```

## 8.3 仍未验证边界

- CANN SDK；
- HCOMM/HCCL 真实链接；
- Ascend 实机；
- 真实多设备通信；
- msprof；
- 实机 FP16/BF16 精度；
- 实机性能；
- 实机可靠性；
- E2 Agent 生成 C collective；
- D2/F2 实机校准。

## 8.4 用户仍需执行

- 待填写

## 8.5 最终 Git 状态

```text
git status --short：
待填写

git status -sb：
待填写

当前 HEAD：
待填写

相对 origin/main：
待填写

是否执行 git push：
NO
```

---

# 9. Goal 停止记录

停止原因：

```text
V1 完成
或
触发整体停止条件
```

说明：

```text
待填写
```

不得自行进入：

```text
G2
E2
D2
F2
```
