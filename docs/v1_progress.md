# HCCL Agent V1 执行进度

版本：v1.0  
计划文件：`docs/v1_execution_plan.md`  
项目路径：`F:\projects\hccl-agent`  
Codex 环境：Windows Native  
Linux 验证方式：Docker Desktop Linux 容器  
状态：IN_PROGRESS

---

## 1. V1 总体状态

| Stage | 名称                                | 状态        | Commit |
| ----- | ----------------------------------- | ----------- | ------ |
| V1-A  | 事实与文档基线修正                  | COMPLETED | eeda43d |
| V1-B  | Collective 多元素与 rank 连续性加固 | COMPLETED | -      |
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

开始时间：2026-07-30 08:07:11 +08:00
当前分支：main
开始 HEAD：865df5b72928aba07dd5ad783435c4449caed603
远端基线：origin/main；本地 `main` ahead 1

### Git 检查

```text
git status --short：
无输出

git status -sb：
## main...origin/main [ahead 1]

git log -10 --oneline：
865df5b docs: add V1 Linux and correctness plan
ede07dc docs: complete autonomous competition readiness audit
bfe23ea chore: prepare G1 CANN integration layer
45cc247 feat: add F1 reliability validation flow
17f09a5 feat: converge D1 topology and cost models
de501ad feat: add E1 autonomous code development loop
d7c45f6 feat: add C3 numeric correctness baseline
4109491 feat: complete C2 ReduceScatter correctness
d054a9a docs: add autonomous competition goal plan
d604308 feat: complete C1 AllGather correctness
```

### 开始条件

- [x] 当前目录为 `F:\projects\hccl-agent`
- [x] Codex 使用 Windows Native 环境
- [x] 未使用 WSL Codex
- [x] 工作区干净
- [x] 无其他活动线程修改同一仓库
- [x] `docs/v1_execution_plan.md` 已提交
- [x] `docs/v1_progress.md` 已提交
- [x] 未发现密钥或凭据
- [x] 未发现仓库内构建产物

---

# 3. Stage V1-A：事实与文档基线修正

开始时间：2026-07-30 08:07:11 +08:00
结束时间：2026-07-30 08:07:11 +08:00
状态：COMPLETED

## 3.1 修改文件

- `docs/autonomous_progress.md`
- `docs/competition_readiness_report.md`
- `docs/correctness_matrix.md`
- `docs/user_actions.md`
- `docs/v1_progress.md`

## 3.2 核验事实

### H1 commit

```text
实际 H1 commit：
ede07dc docs: complete autonomous competition readiness audit
```

### 阶段时间记录

```text
是否存在重叠：
存在 C3-B 与 E1 记录时间重叠。

处理说明：
未臆造新时间；在 `docs/autonomous_progress.md` H1 记录中补充说明：时间来自自主执行记录，部分阶段准备或记录可能重叠，commit 与测试结果为主要阶段证据。
```

### Linux 待办路径

```text
旧路径：
/tmp/hccl-agent-hcccl-c2

新路径：
/tmp/hccl-agent-linux-review
```

### AllReduce 当前限制

```text
V1-B 前状态：
AllReduce 当前主要证明 `count=1` 标量路径；多元素 `count>1` 留给 V1-B 验证。
```

### ReduceScatter 2-rank 当前限制

```text
V1-B 前状态：
ReduceScatter 2-rank legacy 标量形状当前返回 `HCCL_ERR_NOT_SUPPORTED`；V1-B 将改为统一 `[N][N][C] -> [N][C]` 契约。
```

### FP16/BF16 精度口径

```text
赛题原文：
FP16/BF16/FP32 混精度通信，误差 <= 1e-6，无精度溢出/下溢。

当前 CPU tolerance：
FP16：1e-3
BF16：2e-2

结论：
`REQUIRES_COMPETITION_CLARIFICATION`。当前不能断言赛题 `1e-6` 一定适用于 FP16/BF16 最终量化输出；CPU 软件模拟 tolerance 仅用于本地回归，不代表 Ascend 硬件混合精度达标。
```

## 3.3 验收结果

- `git diff --check`：待提交前执行
- 是否仅修改文档：是
- 是否保留所有未验证边界：是
- 是否修改运行逻辑：否

## 3.4 遇到的问题

- PowerShell 默认编码会导致中文文档和赛题 `.docx` 抽取乱码；已改用 UTF-8 输出重新读取。

## 3.5 降级状态

- 无

## 3.6 用户待办

- Linux `.so`、CANN/HCOMM、Ascend 实机和赛题 FP16/BF16 最终误差口径仍需用户或赛事环境确认。

## 3.7 本地提交

```text
commit：
eeda43d
message：docs: correct V1 baseline evidence
```

## 3.8 未验证边界

- Linux `.so` 仍未验证；
- CANN/HCOMM 仍未接入；
- Ascend 实机仍未验证；
- 本阶段不产生新的运行能力。

---

# 4. Stage V1-B：Collective 多元素与 rank 连续性加固

开始时间：2026-07-30 08:20:53 +08:00
结束时间：2026-07-30 08:20:53 +08:00
状态：COMPLETED

## 4.1 修改文件

- `hcccl/src/hccl_algorithms.c`
- `hcccl/src/hccl_comm.c`
- `hcccl/tests/test_api_wrappers.c`
- `hcccl/tests/test_allgather.c`
- `hcccl/tests/test_reduce_ops.c`
- `hcccl/tests/test_reducescatter.c`
- `plugin/execution_engine.py`
- `plugin/hccl_api.py`
- `tests/test_allgather.py`
- `tests/test_dtype_emulation.py`
- `tests/test_plugin_bridge.py`
- `tests/test_reduce_ops.py`
- `tests/test_reducescatter.py`
- `docs/competition_readiness_report.md`
- `docs/correctness_matrix.md`
- `docs/v1_progress.md`

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

实际实现是否符合：是。C/Python CPU_SIM AllReduce 使用 `send[src_rank * C + element]` 输入并向每个目标 rank 返回相同逐元素归约结果；当前算法名共享统一 CPU_SIM reference kernel，不声称独立真实通信调度。

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

实际实现是否符合：是。`N=2` 已使用与 1/4/8/16 相同的 `[N][N][C] -> [N][C]` 契约验证。

## 4.3 覆盖矩阵

### AllReduce FP32

| Rank | count=1 | count=3 | count=17 | count=256 |
| ---: | ------- | ------- | -------- | --------- |
|    1 | PASS    | PASS    | PASS     | PASS      |
|    2 | PASS    | PASS    | PASS     | PASS      |
|    4 | PASS    | PASS    | PASS     | PASS      |
|    8 | PASS    | PASS    | PASS     | PASS      |
|   16 | PASS    | PASS    | PASS     | PASS      |

ReduceOp：

| ReduceOp | 状态 |
| -------- | ---- |
| SUM      | PASS |
| PROD     | PASS |
| MAX      | PASS |
| MIN      | PASS |

### FP16/BF16

| DType | Rank 覆盖 | Count 覆盖 | ReduceOp | 状态 |
| ----- | --------- | ---------- | -------- | ---- |
| FP16  | 2, 4      | 1, 3, 17   | SUM; existing SUM/PROD/MAX/MIN scalar regression retained | PASS |
| BF16  | 2, 4      | 1, 3, 17   | SUM; existing SUM/PROD/MAX/MIN scalar regression retained | PASS |

### ReduceScatter rank 连续性

| Rank | 状态 |
| ---: | ---- |
|    1 | PASS |
|    2 | PASS |
|    4 | PASS |
|    8 | PASS |
|   16 | PASS |

## 4.4 Windows 验收结果

```text
Build directory：
F:\build\hccl-agent-v1b

CMake：
PASS，Visual Studio 17 2022 x64，`-DHCCL_BACKEND=CPU_SIM`

Build：
PASS，Release，生成 `F:\build\hccl-agent-v1b\Release\hccl_plugin.dll`

CTest：
PASS，11/11

定向 Python：
PASS，`tests.test_reduce_ops tests.test_reducescatter tests.test_allgather tests.test_dtype_emulation tests.test_hccl_api tests.test_execution_engine -q`，65 tests OK

完整 Python：
PASS，`python -m unittest discover tests -q`，460 tests OK

实际 DLL：
F:\build\hccl-agent-v1b\Release\hccl_plugin.dll

DLL_LOAD_OK：
PASS

C4819：
未出现

git diff --check：
待提交前执行
```

## 4.5 回归情况

- AllReduce：多元素 `count>1` 已验证，FP32 覆盖 ranks 1/2/4/8/16 与 counts 1/3/17/256。
- AllGather：既有回归保持通过，并补充 rank=2。
- ReduceScatter：2-rank 正确长度 buffer 已验证，1/4/8/16 回归保持通过。
- FP32：SUM/PROD/MAX/MIN 通过。
- FP16：CPU 软件模拟 SUM 多元素覆盖 rank 2/4、count 1/3/17，既有 dtype 回归通过。
- BF16：CPU 软件模拟 SUM 多元素覆盖 rank 2/4、count 1/3/17，既有 dtype 回归通过。
- SUM/PROD/MAX/MIN：FP32 多元素通过；FP16/BF16 既有 ReduceOp 回归保持通过。
- B1 动态库加载：`HCCL_PLUGIN_PATH` 指向 V1-B DLL，Python ctypes 加载通过。
- G1 backend 配置：未修改 ASCEND_CANN 路径；V1-E 将复验缺 SDK 快速失败。

## 4.6 遇到的问题

- Python FP32 reference 初始使用 Python double，PROD 在较大 rank/count 下与 C float 结果存在差异。
- Python FP32 reference 初始未将 overflow 转为有符号 Inf。

## 4.7 修复轮次

| 问题   | 第一次处理 | 第二次处理 | 最终状态 |
| ------ | ---------- | ---------- | -------- |
| FP32 reference 未模拟 C float rounding | 改为每步 `_float32` 截断 | 补充 overflow 到有符号 Inf | PASS |

## 4.8 降级状态

- 无

## 4.9 用户待办

- Linux `.so`、CANN/HCOMM、Ascend 实机仍待 V1-D/V1-E 或用户环境验证。

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
