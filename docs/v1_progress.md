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
| V1-B  | Collective 多元素与 rank 连续性加固 | COMPLETED | 7691922 |
| V1-C  | 确定性随机化 correctness            | COMPLETED | 9652b83 |
| V1-D  | Docker Linux `.so` 验证             | ENV_BLOCKED | f7e96f8 |
| V1-E  | Linux CI 与最终材料收敛             | COMPLETED | -      |

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
7691922
message：feat: harden collective buffer correctness
```

## 4.11 未验证边界

- 当前仍为单进程 CPU_SIM；
- 不代表真实多卡集合通信；
- FP16/BF16 仍为 CPU 软件模拟；
- Linux 将在 V1-D 验证；
- CANN/HCOMM/Ascend 不属于本阶段。

---

# 5. Stage V1-C：确定性随机化 Correctness

开始时间：2026-07-30 08:33:31 +08:00
结束时间：2026-07-30 08:33:31 +08:00
状态：COMPLETED

## 5.1 修改文件

- `tests/test_randomized_collective_correctness.py`
- `docs/correctness_matrix.md`
- `docs/v1_progress.md`

## 5.2 测试配置

### 固定 seed

```text
20260730
424242
13371337
```

### Case 数量

```text
每个 seed：
20
总 case：
60
```

### 参数空间

```text
Primitive：
AllReduce, AllGather, ReduceScatter
Rank：
1, 2, 4, 8, 16
Count：
1, 2, 3, 7, 17, 32, 64
DType：
FP32, FP16, BF16
ReduceOp：
SUM, PROD, MAX, MIN；AllGather 为 N/A
```

## 5.3 覆盖结果

| 能力          | 是否覆盖 | 证据 |
| ------------- | -------- | ---- |
| AllReduce     | 是       | randomized cases |
| AllGather     | 是       | randomized cases |
| ReduceScatter | 是       | randomized cases |
| rank=1        | 是       | randomized cases |
| rank=2        | 是       | randomized cases |
| rank=4        | 是       | randomized cases |
| rank=8        | 是       | randomized cases |
| rank=16       | 是       | randomized cases |
| count>1       | 是       | counts 2/3/7/17/32/64 |
| FP32          | 是       | randomized cases |
| FP16          | 是       | randomized cases |
| BF16          | 是       | randomized cases |
| SUM           | 是       | randomized cases |
| PROD          | 是       | randomized cases |
| MAX           | 是       | randomized cases |
| MIN           | 是       | randomized cases |

## 5.4 可复现性

```text
第一次运行：
PASS，`python -m unittest tests.test_randomized_collective_correctness -v`，60 cases，Ran 1 test in 12.902s，OK

第二次运行：
PASS，`python -m unittest tests.test_randomized_collective_correctness -v`，60 cases，Ran 1 test in 13.007s，OK

结果是否一致：
是

失败复现参数支持：
支持 `HCCL_RANDOM_SEED` 和 `HCCL_RANDOM_CASE`
```

## 5.5 验收结果

```text
随机定向 suite：
PASS，seeds 20260730/424242/13371337，60 cases

Correctness 定向 suite：
PASS，`tests.test_reduce_ops tests.test_reducescatter tests.test_allgather tests.test_dtype_emulation tests.test_randomized_collective_correctness -q`，35 tests OK

CTest：
PASS，`ctest --test-dir F:\build\hccl-agent-v1b -C Release --output-on-failure`，11/11

完整 Python：
PASS，`python -m unittest discover tests -q`，461 tests OK

测试时长：
随机 suite 单次约 13 秒；完整 Python 14.617 秒

git diff --check：
待提交前执行
```

## 5.6 失败样例

```text
无最终失败。中间定位信息：

seed：20260730
case_index：15
primitive：AllGather
rank：16
count：64
dtype：FP32
reduce_op：N/A
expected：未失败；该 case 运行时间超出随机 suite 目标
actual：未失败；被手动停止后收紧随机生成规则
修复：保留 count=64 覆盖，但避免将大 rank 的 AllGather/ReduceScatter 随机 case 变成慢速压力测试
```

## 5.7 修复轮次

| 问题   | 第一次处理 | 第二次处理 | 最终状态 |
| ------ | ---------- | ---------- | -------- |
| 随机 suite 生成 AllGather rank=16 count=64 导致运行时间超目标 | 限制大 rank AllGather/ReduceScatter 随机 count，同时保留 count=64 覆盖 | 不需要 | PASS |

## 5.8 降级状态

- 无

## 5.9 用户待办

- Linux `.so`、CANN/HCOMM、Ascend 实机仍待 V1-D/V1-E 或用户环境验证。

## 5.10 本地提交

```text
commit：
9652b83
message：test: add deterministic randomized correctness
```

## 5.11 未验证边界

- 随机化测试不是形式化证明；
- 仍然只验证 CPU_SIM；
- 不代表真实并发、多进程或硬件通信行为。

---

# 6. Stage V1-D：Docker Linux `.so` 验证

开始时间：2026-07-30 08:38:05 +08:00
结束时间：2026-07-30 08:38:05 +08:00
状态：ENV_BLOCKED

## 6.1 Docker 前置检查

```text
docker version：
正常检查：Client 29.5.3 可见，但 sandbox 内访问 `C:\Users\86159\.docker\config.json` 和 docker pipe 被拒绝。
低风险复查：PASS，Client/Server 29.5.3，Docker Desktop 4.79.0，context `desktop-linux`。

docker info：
正常检查：permission denied while trying to connect to docker API。
低风险复查：PASS，OSType linux, Architecture x86_64, Docker Root Dir `/var/lib/docker`。

Docker Engine 状态：
可用，但镜像 metadata 下载失败，V1-D 按有限尝试规则停止 Docker 执行。
```

## 6.2 修改文件

- `.dockerignore`
- `docker/linux-cpu-sim.Dockerfile`
- `scripts/validate_linux_cpu_sim.sh`
- `docs/user_actions.md`
- `docs/v1_progress.md`

## 6.3 Docker 环境

```text
基础镜像：
ubuntu:22.04

Linux 发行版：
未进入容器，镜像下载阻塞

Compiler：
未验证

CMake：
未验证

Python：
未验证
```

## 6.4 Linux 构建结果

```text
Docker container exit code：
未执行容器；Docker build exit code 1

Linux build directory：
/tmp/hccl-agent-linux-review（脚本默认值，未执行）

CMake：
ENV_BLOCKED

Build：
ENV_BLOCKED

实际 .so 路径：
未生成

.so 文件存在：
未验证
```

## 6.5 Linux 测试结果

```text
CTest：
ENV_BLOCKED

ctypes 加载：
ENV_BLOCKED

实际 HCCL_PLUGIN_PATH：
未设置 Linux `.so`

定向 Python：
ENV_BLOCKED

完整 Python：
ENV_BLOCKED

LINUX_CPU_SIM_VALIDATION_OK：
未出现
```

## 6.6 Windows 回归结果

Linux 相关修复后重新执行：

```text
Windows CMake：
V1-B/V1-C 已通过，V1-D 未做 Linux 代码修复，无需额外 Windows 重建

Windows Build：
V1-B/V1-C 已通过

Windows CTest：
V1-C 复跑 11/11 PASS

Windows完整 Python：
V1-C 完整 Python 461 tests OK
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
`docker version` / `docker info` 在 sandbox 内无法访问 Docker config 和 docker pipe。

低风险复查：
使用升级权限复查 `docker version; docker info` 通过；随后 `docker build` 拉取 `ubuntu:22.04` metadata 失败，`auth.docker.io` token 获取超时。

停止原因：
Docker 镜像 metadata 下载失败；根据有限尝试规则不反复重试、不修复 Docker Desktop、WSL、代理或系统环境。

生成的验证脚本：
`scripts/validate_linux_cpu_sim.sh`

用户待办：
见 `docs/user_actions.md` 的 `UA-V1-001`。
```

## 6.8 修复轮次

| 问题   | 第一次处理 | 第二次处理 | 最终状态 |
| ------ | ---------- | ---------- | -------- |
| Docker access / image metadata download | 正常检查失败后做一次低风险复查 | 镜像下载失败后停止重试 | ENV_BLOCKED |

## 6.9 状态结论

选择其一：

```text
LINUX_DOCKER_VERIFIED
ENV_BLOCKED
PARTIAL
```
选择：`ENV_BLOCKED`

## 6.10 本地提交

```text
commit：
f7e96f8
message：chore: add Linux CPU_SIM validation tooling
```

## 6.11 未验证边界

- Docker Linux CPU_SIM 不代表 Ascend；
- Docker `.so` 不代表真实 HCCL/HCOMM；
- 不包含多设备实机验证；
- 不包含 msprof。

---

# 7. Stage V1-E：Linux CI 与最终材料收敛

开始时间：2026-07-30 08:42:39 +08:00
结束时间：2026-07-30 08:42:39 +08:00
状态：COMPLETED

## 7.1 修改文件

- `.github/workflows/linux-cpu-sim.yml`
- `README.MD`
- `docs/competition_readiness_report.md`
- `docs/v1_progress.md`
- `docs/v1_validation_report.md`

## 7.2 GitHub Actions 配置

```text
Workflow：
.github/workflows/linux-cpu-sim.yml

触发条件：
pull_request, workflow_dispatch

Python：
3.10

Compiler：
ubuntu-22.04 runner `build-essential`

CMake：
system package

是否复用 Linux validation script：
是，`bash scripts/validate_linux_cpu_sim.sh /tmp/hccl-agent-linux-review`
```

## 7.3 CI 当前状态

选择其一：

```text
CI_CONFIGURED_UNRUN
```

说明：

```text
Workflow 已创建但未执行 git push；远端 GitHub Actions 未运行。
```

未执行 `git push` 时不得填写 `CI_REMOTE_VERIFIED`。

## 7.4 最终 Windows 验收

```text
Build directory：
F:\build\hccl-agent-v1-final

CMake Release：
PASS，Visual Studio 17 2022 x64，`-DHCCL_BACKEND=CPU_SIM`

Build：
PASS，Release，生成 `F:\build\hccl-agent-v1-final\Release\hccl_plugin.dll`

CTest：
PASS，11/11

定向 Python：
PASS，66 tests OK

完整 Python：
PASS，461 tests OK

实际 DLL：
F:\build\hccl-agent-v1-final\Release\hccl_plugin.dll

ASCEND_CANN 缺 SDK 快速失败：
PASS，配置阶段失败并提示缺 HCCL header/library、`HCCL_CANN_ROOT` 或 `ASCEND_HOME_PATH`/`CANN_HOME`

C4819：
未出现
```

## 7.5 最终 Linux 验收

```text
Docker：
ENV_BLOCKED，Docker Desktop engine 可用，但 `docker build` 拉取 `ubuntu:22.04` metadata 时访问 `auth.docker.io` 超时

CMake：
未执行

Build：
未执行

CTest：
未执行

ctypes 加载：
未执行

完整 Python：
未执行

实际 .so：
未生成
```

Docker 被阻塞时应明确填写 `ENV_BLOCKED`，不得填写通过。

## 7.6 最终文档

| 文件                                   | 状态 |
| -------------------------------------- | ---- |
| `docs/v1_progress.md`                  | UPDATED |
| `docs/v1_validation_report.md`         | CREATED |
| `docs/correctness_matrix.md`           | UPDATED |
| `docs/competition_readiness_report.md` | UPDATED |
| `docs/user_actions.md`                 | UPDATED |
| `README.MD`                            | UPDATED |

## 7.7 构建产物检查

```text
.dll：
未新增跟踪
.lib：
未新增跟踪
.exe：
未新增跟踪
.obj：
未新增跟踪
.pdb：
未新增跟踪
.so：
未新增跟踪
build/：
未新增跟踪
CMakeFiles/：
未新增跟踪
__pycache__/：
未新增跟踪
密钥：
未发现真实凭据；扫描命中仅为文档/测试占位示例
```

## 7.8 本地提交

```text
commit：
待本阶段提交
message：ci: add Linux CPU_SIM validation
```

---

# 8. V1 最终总结

完成时间：2026-07-30 08:42:39 +08:00
总体状态：COMPLETED_WITH_ENV_BLOCKED_LINUX

## 8.1 阶段与提交

| Stage | 状态 | Commit | Message |
| ----- | ---- | ------ | ------- |
| V1-A  | COMPLETED | eeda43d | docs: correct V1 baseline evidence |
| V1-B  | COMPLETED | 7691922 | feat: harden collective buffer correctness |
| V1-C  | COMPLETED | 9652b83 | test: add deterministic randomized correctness |
| V1-D  | ENV_BLOCKED | f7e96f8 | chore: add Linux CPU_SIM validation tooling |
| V1-E  | COMPLETED | 待本阶段提交 | ci: add Linux CPU_SIM validation |

## 8.2 最终能力

### Collective correctness

```text
AllReduce 多元素：
WINDOWS_VERIFIED，FP32 ranks 1/2/4/8/16 and counts 1/3/17/256

ReduceScatter 2-rank：
WINDOWS_VERIFIED，正确长度 `[N][N][C] -> [N][C]` buffer

AllGather：
WINDOWS_VERIFIED，含 rank=2 回归

FP32 ReduceOps：
SUM/PROD/MAX/MIN PASS

FP16：
CPU_EMULATED_FP16，Windows regression PASS

BF16：
CPU_EMULATED_BF16，Windows regression PASS
```

### 随机化验证

```text
Seed 数：
3

Case 数：
60

覆盖 Primitive：
AllReduce, AllGather, ReduceScatter

覆盖 Rank：
1, 2, 4, 8, 16

覆盖 Count：
1, 2, 3, 7, 17, 32, 64

连续运行一致：
是，两次随机 suite 均 OK
```

### Windows

```text
CMake：
PASS

CTest：
PASS，11/11

定向 Python：
PASS，66 tests OK

完整 Python：
PASS，461 tests OK
```

### Linux

```text
状态：
ENV_BLOCKED

Docker：
Engine 可用；Docker build 拉取 `ubuntu:22.04` metadata 失败

.so：
未生成

CTest：
未执行

Python：
未执行
```

### CI

```text
状态：
CI_CONFIGURED_UNRUN
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

- 执行 `UA-V1-001`：在可拉取 `ubuntu:22.04` 的 Docker/Linux 环境运行 Linux CPU_SIM 验证。
- 执行 CANN/HCOMM/Ascend 实机验证和 FP16/BF16 实机误差验证。
- push 后观察 `.github/workflows/linux-cpu-sim.yml` 的远端 Actions 结果。

## 8.5 最终 Git 状态

```text
git status --short：
待最终提交后复查

git status -sb：
待最终提交后复查

当前 HEAD：
待最终提交后复查

相对 origin/main：
待最终提交后复查

是否执行 git push：
NO
```

---

# 9. Goal 停止记录

停止原因：

```text
V1 完成；Linux Docker 验证为 ENV_BLOCKED
```

说明：

```text
Docker image metadata 下载失败后按有限尝试规则停止 V1-D，不声明 Linux 已验证；V1-E 仍完成 Linux 脚本、CI 配置和最终审计。
```

不得自行进入：

```text
G2
E2
D2
F2
```
