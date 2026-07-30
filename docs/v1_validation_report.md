# HCCL Agent V1 Validation Report

生成时间：2026-07-30 08:42:39 +08:00

## 1. V1 目标

V1 目标是在不接入真实 CANN SDK、HCOMM、Ascend 实机或外部 LLM API 的前提下，完成 Windows CPU_SIM correctness hardening，并通过 GitHub Actions Linux CPU_SIM 验证 Linux `.so`、CTest 和 Python correctness。

## 2. 开始 Git 基线

```text
开始目录：F:\projects\hccl-agent
开始 HEAD：865df5b docs: add V1 Linux and correctness plan
开始状态：git status --short 无输出
分支：main...origin/main [ahead 1]
```

## 3. AllReduce 多元素数据契约

```text
send[N][C] -> recv[N][C]
send index = send[src_rank * C + element]
recv index = recv[dst_rank * C + element]
recv[dst_rank][element] = REDUCE(send[src_rank][element] for src_rank in 0..N-1)
```

状态：`CPU_SIMULATED`, `REFERENCE_VERIFIED`, `WINDOWS_VERIFIED`。

## 4. ReduceScatter 2-rank 数据契约

```text
send[N][N][C] -> recv[N][C]
send index = send[(src_rank * N + dst_rank) * C + element]
recv index = recv[dst_rank * C + element]
recv[dst_rank][element] = REDUCE(send[src_rank][dst_rank][element] for src_rank in 0..N-1)
```

状态：2-rank 正确长度 buffer 已验证；旧 legacy 标量 `NOT_SUPPORTED` 例外已移除。

## 5. 覆盖矩阵

- AllReduce FP32：rank 1/2/4/8/16；count 1/3/17/256；SUM/PROD/MAX/MIN。
- AllReduce FP16/BF16：rank 2/4；count 1/3/17；SUM；既有 dtype ReduceOp 回归保留。
- ReduceScatter：rank 1/2/4/8/16；SUM/PROD/MAX/MIN 回归。
- AllGather：rank 1/2/4/8/16 相关回归，含 rank=2。

## 6. 固定 seed 随机测试

```text
Seeds：20260730, 424242, 13371337
每个 seed：20 cases
总 case：60
Primitive：AllReduce, AllGather, ReduceScatter
Rank：1, 2, 4, 8, 16
Count：1, 2, 3, 7, 17, 32, 64
DType：FP32, FP16, BF16
ReduceOp：SUM, PROD, MAX, MIN
```

两次连续运行均通过。随机测试是三个固定 seed 的 60 个确定性抽样 case，不是完整笛卡尔积穷举，也不是形式化证明。

## 7. Windows 构建和测试

```text
Build directory：F:\build\hccl-agent-v1-final
CMake：PASS，Visual Studio 17 2022 x64，HCCL_BACKEND=CPU_SIM
Build：PASS，Release
DLL：F:\build\hccl-agent-v1-final\Release\hccl_plugin.dll
CTest：PASS，11/11
定向 Python：PASS，66 tests OK
完整 Python：PASS，461 tests OK
C4819：未出现
ASCEND_CANN 缺 SDK：PASS，配置阶段快速失败并提示缺 HCCL header/library 与 SDK root
```

## 8. Docker Linux 构建和测试

状态：`ENV_BLOCKED`。

```text
docker version/info：升级权限低风险复查通过，Docker Desktop 4.79.0，Engine 29.5.3，OSType linux
docker build：FAILED
原因：拉取 ubuntu:22.04 metadata 时，auth.docker.io anonymous token 获取超时
Linux CMake：未执行
Linux build：未执行
Linux CTest：未执行
Linux Python：未执行
LINUX_CPU_SIM_VALIDATION_OK：未出现
```

本地 Docker 状态仍为 `ENV_BLOCKED`。该本地阻塞原因是 `auth.docker.io` token timeout；由于 GitHub Actions Linux CPU_SIM 验证已经通过，本地 Docker 阻塞不再阻塞 V1。

## 9. Linux `.so` 实际路径

GitHub Actions Linux CPU_SIM 实际验证路径：

```text
/tmp/hccl-agent-linux-review/libhccl_plugin.so
```

状态：`LINUX_CI_VERIFIED`。该 `.so` 来自 Linux runner 的 CPU_SIM 构建，不代表 Ascend 或真实 HCCL/HCOMM。

## 10. CI 配置状态

状态：`CI_REMOTE_VERIFIED`。

```text
Workflow：
.github/workflows/linux-cpu-sim.yml

Event：
pull_request

Job：
linux-cpu-sim

Result：
PASS

Python：
3.10.20

CMake：
3.31.6

Compiler：
GCC 11.4.0

Backend：
CPU_SIM

CTest：
11/11 passed

Targeted Python：
66 tests OK

Full Python：
461 tests OK

LINUX_CPU_SIM_VALIDATION_OK：
observed

Checkout warning：
已通过升级 GitHub Actions runtime 和移除孤立 third_party/cann-hccl gitlink 解决。
```

Linux 状态记录为 `LINUX_CI_VERIFIED`，不得写成 `LINUX_DOCKER_VERIFIED`。

## 11. 未验证边界

- CANN SDK 未安装；
- HCOMM/HCCL 真实链接未验证；
- Ascend 实机未验证；
- 真实多进程、多设备集合通信未验证；
- msprof 未验证；
- FP16/BF16 硬件混合精度未验证；
- GitHub Actions Linux CPU_SIM 不代表 Ascend；
- CPU_SIM 不代表真实 HCCL/HCOMM；
- 随机化测试不是形式化证明；
- 未声明真实性能或实机可靠性结论。

## 12. 用户后续操作

见 `docs/user_actions.md`：

- `UA-V1-001`：Linux CPU_SIM 已由 GitHub Actions 验证，本地 Docker/Linux 复现可选；
- `UA-002`：准备 CANN/HCOMM/Ascend 实机验证；
- `UA-003`：FP16/BF16 Ascend 实机误差验证；
- `UA-005`：D1 模型实机校准；
- `UA-006`：F1 真实可靠性验收。

## 13. V1 阶段 commit

| Stage | Commit  | Message                                        |
| ----- | ------- | ---------------------------------------------- |
| V1-A  | eeda43d | docs: correct V1 baseline evidence             |
| V1-B  | 7691922 | feat: harden collective buffer correctness     |
| V1-C  | 9652b83 | test: add deterministic randomized correctness |
| V1-D  | f7e96f8 | chore: add Linux CPU_SIM validation tooling    |
| V1-E  | a0ee8f2 | ci: add Linux CPU_SIM validation               |
| CI 修复 | 0bfed12 | ci: update GitHub Actions runtimes             |
| CI 修复 | 280eb8e | fix: remove orphan CANN HCCL submodule entry   |

## 14. 最终 Git 状态

```text
git status --short：
 M docs/competition_readiness_report.md
 M docs/correctness_matrix.md
 M docs/user_actions.md
 M docs/v1_progress.md
 M docs/v1_validation_report.md
git status -sb：## v1-linux-correctness...origin/v1-linux-correctness
当前 HEAD：280eb8e fix: remove orphan CANN HCCL submodule entry
是否执行 git push：NO
随机测试覆盖所列参数空间中的 60 个确定性抽样 case，不代表所有参数组合的完整笛卡尔积穷举。
```

是否执行 `git push`：NO。
