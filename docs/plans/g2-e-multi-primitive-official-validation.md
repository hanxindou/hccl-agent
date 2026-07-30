# G2-E 多原语官方 HCCL-VM 验证注册表与严格结果契约计划

## 0. 只读审查基线

本计划基于 2026-07-30 的 `main` 制定。本轮只读审查确认：

- 当前分支：`main`
- `HEAD`：`eb6623617f77fd42abe1091b5e60f04881eb01a5`
- `origin/main`：`eb6623617f77fd42abe1091b5e60f04881eb01a5`
- 工作区：审查开始时 clean
- G2-D：已由 merge commit `eb66236` 合并到 `main`
- G2-D 最终 commit `08a939c` 是当前 HEAD 的祖先
- 根目录不存在 `AGENTS.md`
- 存在并已读取 `CLAUDE.md`
- 后续不得在旧分支 `g2-hccl-vm-integration` 上实现

已读取：

- `CLAUDE.md`
- `docs/plans/g2-d-hccl-vm-backend.md`
- `docs/g2_d_validation_report.md`
- `docs/project_audit.md`
- `docs/project_documentation.md`
- `experiments/hccl_vm/evidence/g2_official_baseline/`
- `experiments/hccl_vm/evidence/g2_d_20260730T081052.668860Z/`
- `main.py`
- `config/hccl_vm.json`
- `plugin/hccl_vm_backend.py`
- `plugin/hccl_vm_env.py`
- `plugin/hccl_vm_runner.py`
- `plugin/hccl_vm_checker.py`
- `plugin/hccl_vm_evidence.py`
- `agent/report_generator.py`
- 所有 `tests/test_hccl_vm_*.py`
- `tests/test_backend_selection.py`

已通过 `wsl.exe -d Ubuntu-22.04 -- bash -lc "..."` 只读检查：

- `/home/workspace/hcomm/test/hccl_vm/README-Competition.md`
- `/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/`
- `all_reduce_test -h`
- `all_gather_test -h`
- `reduce_scatter_test -h`
- `/home/workspace/evidence/logs/` 中三份 G2-C 原始日志
- HCOMM/HCCL 当前 branch、commit 和 tracked status

root Git 检查只使用命令级精确路径：

```text
git -c safe.directory=/home/workspace/hcomm -C /home/workspace/hcomm ...
git -c safe.directory=/home/workspace/hccl -C /home/workspace/hccl ...
```

未修改全局或系统 Git 配置。官方仓库状态为：

| Repo | Branch | Commit | Tracked status |
|---|---|---|---|
| HCOMM | `competition/campus-2026` | `c8a3dc68a37315aa1e908a971fa706abe612f6ee` | clean |
| HCCL | `competition/campus-2026` | `2c87cc1937bab23b8574ef24017c03572d3340e2` | clean |

## 1. 目标、范围和非目标

### 1.1 目标

把 G2-D 中固定为 AllReduce 的 `ASCEND_HCCL_VM` 外部验证后端扩展为集中式、不可绕过的三原语白名单框架：

- `AllReduce`
- `AllGather`
- `ReduceScatter`

每个原语必须有独立的请求约束、hccl_test argv 构建、element/byte 语义、Checker metadata contract、warning 基线和 evidence schema。未知原语或无效参数必须在环境探测、WSL 启动或 HCCL-VM 启动之前失败。

### 1.2 非目标

- 不实现 AllToAll、Broadcast、Reduce、Scatter 或其他原语。
- 不扩展到 INT32 以外的数据类型。
- 不扩展到 2 ranks 以外的规模。
- 不验证真实 Ascend NPU。
- 不实现 hccl-agent 直接链接或直接调用真实 HCCL API。
- 不把 HCCL-VM 或 hccl_test 数据描述为真实硬件性能。
- 不修改 HCOMM/HCCL 已跟踪源码或 CANN 安装。
- 不替换、删除或改写 G2-C/G2-D evidence。
- 不改变 `CPU_SIM` 默认后端。
- 不在本计划阶段实现业务代码、运行官方闭环、提交或推送。

## 2. G2-D 当前架构清单

### 2.1 可直接复用

| 模块 | 可复用能力 |
|---|---|
| `plugin/hccl_vm_backend.py` | 双后端枚举、配置优先级、路径控制字符校验、精确 Git repo 路径约束 |
| `plugin/hccl_vm_env.py` | Windows/WSL transport、base64 probe、CANN/HCCL-VM/checker/MPI/tool 探测、命令级 `safe.directory` |
| `plugin/hccl_vm_runner.py` | HCCL-VM startup、PTY、分步骤 marker、总超时、stdout/stderr 合流、正常 exit |
| `plugin/hccl_vm_checker.py` | ANSI 清理、Op summary 基础解析、退出码 marker、fatal signal、warning 103、正常关闭判定 |
| `plugin/hccl_vm_evidence.py` | JSON、精简日志、gzip 原始日志、SHA256、目录冲突处理 |
| `agent/report_generator.py` | 官方模拟边界声明、结构化文本报告 |
| `main.py` | `diagnose`、`dry-run`、`verify-official` 分流和 CPU_SIM 隔离 |
| tests | Windows 导入安全、dry-run 无副作用、环境阻塞、严格失败、evidence hash 和 opt-in 实测模式 |

### 2.2 必须重构的 AllReduce 专用部分

| 当前专用点 | G2-E 需要的变化 |
|---|---|
| `OfficialAllReduceRequest` | 改为通用 request，并由 registry entry 执行原语级校验 |
| `_official_request_from_args()` | 先规范化 primitive，再处理可选 `--op`，禁止默认 SUM 泄漏到 AllGather |
| 官方 CLI 的 `--op` 默认 `sum` | 改为 `None`；AllReduce/ReduceScatter 要求显式提供，AllGather 提供即拒绝 |
| env 只探测 `all_reduce_test` | registry 驱动探测三种 executable 和各自 `ldd` |
| runner 固定 `all_reduce_test` | 仅使用 registry 中的常量 basename，按原语构建 argv |
| runner 固定 `-b/-e=byte_count` | 使用各 primitive 的 hccl_test byte semantics |
| dry-run success requirements 固定 AllReduce | 从 resolved contract 生成 |
| checker `_DefaultRequest` 固定 AllReduce | parser 必须接收 resolved contract，不允许隐式默认获得 PASS |
| checker 强制比较 `reduceType` | AllGather 忽略该字段；其他两个严格比较 SUM |
| checker 只收集 stage，不要求必需 stage 存在 | 每个目标 operation block 必须检查必需 stage |
| failure 文案写死 `all_reduce_test` | 改为 canonical primitive 和 registry executable |
| evidence schema/name 为 `g2-d-v1`/`g2_d_*` | 升级为 G2-E per-primitive schema 和 suite summary |
| report 始终输出 Reduce Operation | AllGather 输出 `N/A`，不能暗示 SUM 是成功条件 |

## 3. 官方三原语真实命令契约

### 3.1 实际 help 事实

当前三个二进制的 `-h` 输出相同，均列出：

- `-b/--minbytes`
- `-e/--maxbytes`
- `-i/--stepbytes`
- `-f/--stepfactor`
- `-n/--iters`
- `-o/--op`
- `-d/--datatype`
- `-r/--root`
- `-w/--warmup_iters`
- `-c/--check`
- `-p/--npus`
- `-m/--symmetric_memory`
- `-z/--zero_copy`
- `-s/--nslb`
- `-t/--onlydevicetime`

help 在无设备上下文中打印 `aclrtGetSocName failed`，但帮助命令退出码为 0。diagnose 不得因为该字符串单独判定失败。

### 3.2 G2-C 成功基线中的精确 hccl_test argv

共同 MPI 前缀：

```text
mpirun --allow-run-as-root --oversubscribe -np 2
```

AllReduce：

```text
/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/all_reduce_test -b 64 -e 64 -d int32 -o sum -w 0 -n 1 -c 1
```

AllGather：

```text
/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/all_gather_test -b 64 -e 64 -d int32 -w 0 -n 1 -c 1
```

ReduceScatter：

```text
/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/reduce_scatter_test -b 64 -e 64 -d int32 -o sum -w 0 -n 1 -c 1
```

冻结参数：

| 参数 | G2-E 固定值/规则 |
|---|---|
| `-b` | resolved contract 的 `hccl_test_bytes` |
| `-e` | 与 `-b` 相同，只跑一个固定 size |
| `-d` | `int32` |
| `-o` | AllReduce/ReduceScatter 为 `sum`；AllGather 不传 |
| `-w` | `0` |
| `-n` | `1` |
| `-c` | `1` |
| `-np` | `2` |
| executable | registry 中的固定 basename |

不使用 `-i`、`-f`、`-r`、`-p`、`-m`、`-z`、`-s`、`-t`。

### 3.3 element 和 byte 语义

虽然三条命令恰好都使用 `-b 64 -e 64`，但不能共享一个简单的 `elements * 4` 公式：

| Primitive | 请求 elements 语义 | Checker `elementCount` | 每 rank input | 每 rank output | hccl_test `-b/-e` |
|---|---|---:|---:|---:|---:|
| AllReduce | 每 rank 输入/输出元素 | 16 | 16 × 4 = 64 B | 16 × 4 = 64 B | 64 B |
| AllGather | 每 rank 输入元素 | 8 | 8 × 4 = 32 B | 8 × 2 × 4 = 64 B | 64 B |
| ReduceScatter | 每 rank 输出元素 | 8 | 8 × 2 × 4 = 64 B | 8 × 4 = 32 B | 64 B |

G2-C 原始日志进一步证明：

- AllReduce HCCL exchange `count[16]`，Checker `elementCount=16`
- AllGather HCCL exchange `count[8]`，Checker `elementCount=8`
- ReduceScatter HCCL exchange `count[8]`，Checker `elementCount=8`

`-b/-e` 在 AllGather 表示每 rank 聚合输出 byte size；在 ReduceScatter 表示每 rank 输入总 byte size。result/evidence 必须同时保存 `request_elements`、`element_semantics`、`input_bytes_per_rank`、`output_bytes_per_rank` 和 `hccl_test_bytes`。

### 3.4 Checker 基线

| Primitive | collectiveType | rankCount | dataType | elementCount | reduceType 处理 | Checker Success | Warning 103 |
|---|---|---:|---|---:|---|---:|---:|
| AllReduce | AllReduce | 2 | INT32 | 16 | 必须为 SUM | 2 | 4 |
| AllGather | AllGather | 2 | INT32 | 8 | 日志为 SUM，但完全忽略 | 2 | 4 |
| ReduceScatter | ReduceScatter | 2 | INT32 | 8 | 必须为 SUM | 2 | 4 |

G2-E 不要求恰好两个 opIndex。至少发现一个 Op summary；所有发现的 Op summary 都必须满足选中 primitive 的 contract；至少出现一个 `Checker Success`。

固定的 CheckerV3 必需 stage：

- `GenGraph`
- `SingleTaskCheck`
- `MemConflict`
- `SemanticCheck`

日志中还会出现 `CollectReachableTaskNodesToScanMemoryBuckets` 等辅助 stage。所有观察到的 stage 都不得为 failed；四个必需 stage 必须存在且为 success。实现时应按 Op summary 分块关联 stage，避免简单 dict 覆盖多个 operation 的结果。

G2-C check-only 日志中的 hccl_test `check_result` 可显示 `failed`，而 checker、命令退出码和 HCCL-VM 关闭均成功。G2-E 不得把该表格字段作为 PASS 信号，也不得用不带上下文的任意 `failed` 字符串覆盖严格 fatal/stage 规则；官方 CheckerV3 contract 和退出码是本阶段判定依据。

## 4. Primitive registry 设计

建议新增：

- `plugin/hccl_vm_registry.py`
- `tests/test_hccl_vm_registry.py`

registry 使用冻结 dataclass 加 `MappingProxyType` 或等价不可变结构。每个 entry 至少包含：

```text
canonical_name
aliases
executable_basename
requires_reduce_op
allowed_reduce_ops
allowed_dtypes
allowed_rank_counts
element_semantics
element_validator
dtype_size_resolver
input_bytes_resolver
output_bytes_resolver
hccl_test_bytes_resolver
command_builder
checker_contract
evidence_contract
official_baseline
warning_baseline
required_checker_stages
```

建议 alias 白名单：

| Canonical | Aliases |
|---|---|
| `AllReduce` | `allreduce`, `all_reduce`, `all-reduce` |
| `AllGather` | `allgather`, `all_gather`, `all-gather` |
| `ReduceScatter` | `reducescatter`, `reduce_scatter`, `reduce-scatter` |

规范化只做 trim、case fold 和白名单查找；不得把任意去标点后的字符串自动视为有效原语。

executable 安全规则：

1. request/CLI 不包含 executable 字段。
2. executable basename 只能来自 registry 常量。
3. basename 不得含 `/`、`\`、`..`、NUL 或 shell 控制字符。
4. 最终路径只能是 `posixpath.join(config.hccl_test_bin, spec.executable_basename)`。
5. normalize 后父目录必须仍等于配置的 `hccl_test_bin`。
6. 不新增 `--hccl-test-executable` 或等价参数。
7. `hccl_test_bin` 必须规范化后严格等于
   `<cann_path>/tools/hccl_test/bin`；`--hccl-test-bin` 只能表达该固定
   CANN 布局，不能指向 CANN 根目录外的任意目录。
8. 如果未来需要支持另一种官方 CANN 布局，必须在代码中增加显式目录
   allowlist 和独立测试，不能由 request 放宽。

每个 entry 的初始限制：

- dtype 仅 `int32`
- rank count 仅 `2`
- AllReduce elements 仅 `16`
- AllGather input elements per rank 仅 `8`
- ReduceScatter output elements per rank 仅 `8`
- reduce op 仅 `sum`
- 三者 `official_baseline=true`

## 5. 通用请求模型

建议把 `OfficialAllReduceRequest` 替换为 `OfficialCollectiveRequest`，字段为：

```text
primitive: str
rank_count: int
dtype: str
elements: int
reduce_op: str | None
```

构造分两步：

1. `normalize_primitive()` 从不可变 registry 返回 spec；未知值立即 `ValueError`。
2. `resolve_request()` 使用 spec 校验参数并产生冻结的 `ResolvedCollectiveContract`。

resolved contract 至少包含：

```text
canonical_primitive
rank_count
dtype
dtype_size_bytes
reduce_op
request_elements
element_semantics
checker_element_count
input_elements_per_rank
output_elements_per_rank
input_bytes_per_rank
output_bytes_per_rank
hccl_test_bytes
executable_basename
required_checker_stages
warning_baseline
```

原语规则：

- AllReduce：`--op` 必须显式提供且为 `sum`。
- AllGather：`--op` 只要出现即拒绝；不能静默忽略。
- ReduceScatter：`--op` 必须显式提供且为 `sum`。

官方子命令的 argparse `--op` 默认值必须从 `sum` 改为 `None`。普通 CPU_SIM `run` 路径不使用此字段，不受影响。

## 6. 命令构建和 dry-run

每个 command builder 返回 argv list，不返回未转义 shell 片段。runner 最后用 `shlex.join()` 渲染交互命令。

示例 resolved argv：

```python
[
    "mpirun",
    "--allow-run-as-root",
    "--oversubscribe",
    "-np",
    "2",
    "/configured/hccl_test/bin/all_gather_test",
    "-b",
    "64",
    "-e",
    "64",
    "-d",
    "int32",
    "-w",
    "0",
    "-n",
    "1",
    "-c",
    "1",
]
```

OpenMPI/MPICH 差异继续由已探测的 MPI implementation 决定；当前环境是 Open MPI 4.1.2，因此冻结基线包含 `--allow-run-as-root --oversubscribe`。

dry-run 必须在任何环境 probe 前完成 request resolve，并输出：

- canonical primitive 和命中的 alias
- registry entry 摘要
- request element semantics
- input/output elements 和 bytes
- hccl_test bytes
- executable basename 和最终 path
- 完整 argv list
- `shlex.join()` 后的最终交互命令
- common startup、mock-comm、checker、exit 和 cleanup plan
- per-primitive evidence 目录模式
- success requirements
- `not_executed=true`

dry-run 不调用 `subprocess.Popen`、`wsl.exe`、HCCL-VM、MPI、hccl_test 或 checker。

## 7. diagnose 和 CLI

### 7.1 diagnose

`HcclVmEnvironment` 改为 registry 驱动的 executable matrix：

```text
hccl_test.executables.AllReduce
hccl_test.executables.AllGather
hccl_test.executables.ReduceScatter
```

每项记录 path、executable、dependencies_resolved。公共环境状态和每原语状态分开：

- 单 primitive verify 只依赖公共环境和选中 primitive。
- G2-E suite/最终完成要求三项全部 OK。
- `diagnose` 顶层建议在任一 registry primitive 不可用时返回 `ENV_BLOCKED`，同时保留每项细节。

### 7.2 CLI

继续支持：

```text
python main.py diagnose --backend ASCEND_HCCL_VM
python main.py dry-run --backend ASCEND_HCCL_VM --primitive <primitive> ...
python main.py verify-official --backend ASCEND_HCCL_VM --primitive <primitive> ...
```

示例：

```text
python main.py verify-official --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16
python main.py verify-official --backend ASCEND_HCCL_VM --primitive AllGather --nodes 2 --dtype int32 --elements 8
python main.py verify-official --backend ASCEND_HCCL_VM --primitive ReduceScatter --nodes 2 --dtype int32 --op sum --elements 8
```

未知 primitive、AllGather 的 `--op`、缺失 reduce op、错误 dtype/rank/elements 必须在构造 `HcclVmEnvironment` 或调用 runner 前失败。

CPU_SIM 继续是普通 `run` 的默认后端。`ASCEND_HCCL_VM` 不自动替换 CPU_SIM。

统一 suite CLI 需要用户确认。建议在同一个 `verify-official` 下增加与 `--primitive` 互斥的 `--suite g2-e`，而不是把 `All` 注册成第四个 primitive：

```text
python main.py verify-official --backend ASCEND_HCCL_VM --suite g2-e
```

suite 顺序固定为 registry 中的 `AllReduce`、`AllGather`、`ReduceScatter`，不接受用户提供 executable 或任意 primitive list。

## 8. Checker parser 和结果判定

### 8.1 Parser

保留现有 ANSI/空白清理和 marker regex，新增：

- parser 必须接收 `ResolvedCollectiveContract`，无 contract 不允许解析为 PASS。
- Op summary 基础结构继续解析 `reduceType`，但比较逻辑由 spec 决定。
- AllGather 记录 observed `reduceType`，但不比较、不依赖。
- 按每个 Op summary 到下一个 summary/结束位置建立 `operation_results`。
- 不要求 opIndex 连续或数量等于 2。
- 至少一个 summary，且所有 summary 都匹配。
- 至少一个 Checker Success。
- 每个 operation block 的四个必需 CheckerV3 stage 必须存在且为 success。
- 任意 observed stage failed 立即失败。

### 8.2 统一成功条件

三种 primitive 都必须同时满足：

- hccl_config exit code 0
- mock-comm exit code 0
- hccl_test exit code 0
- checker command exit code 0
- 至少一个 Checker Success
- 至少一个目标 Op summary
- 所有目标 Op summary metadata 匹配
- 所有 CheckerV3 必需 stage success
- 任意 observed stage 无 failure
- HCCL-VM exit code 0
- HCCL-VM 正常关闭 marker
- 外层退出码 0
- 无 Segmentation fault
- 无 MPI_ABORT
- 无 undefined symbol
- 无 fatal failure
- postflight 无遗留 hccl-vm、MPI、checker 或选中 hccl_test 进程

任何字段缺失都不能推断成功。

### 8.3 ErrorCode 103

三原语固定基线均为：

- count：4
- normalized summary：CCU post/local-post task 未被 Wait task 消费

结果字段增加：

```text
warning_103_count
warning_summaries
warning_baseline_count
warning_regression
warning_regression_reasons
```

判定：

- count 为 0：可为 `PASS_CLEAN`。
- count 大于 0 且无其他失败：`PASS_WITH_WARNING`。
- count 或 normalized summary 相对固定基线显著变化：仍按其他条件决定 PASS/FAIL，但必须设置 `warning_regression=true` 并在报告突出显示。
- 不得把 warning 103 删除、降级为 clean 或伪装为普通 info。

建议把固定契约下 `count != 4` 或出现新的 normalized warning form 定义为 regression warning；该阈值需用户确认。

## 9. 进程、超时和清理

继续复用 marker 驱动的交互执行，但补齐：

- request 校验必须先于任何 process。
- 每一步保留 completion marker 和退出码。
- 总超时外增加 start/mock/test/checker/exit 阶段超时。
- 所有退出路径都进入 `finally` cleanup。
- 正常路径发送 `exit` 并等待正常 shutdown marker。
- 超时只终止本 runner 启动的 process/process group，不执行 broad `pkill`。
- postflight 只读检查精确进程名和本次 PID/子进程关系。
- 若发现残留，不得 PASS；结果为 `FAIL_CLEANUP` 或等价失败状态并保留 PID/command 摘要。
- concurrent 外部 HCCL-VM 会话不得被清理；若无法区分归属，标记 `ENV_BLOCKED_CONCURRENT_PROCESS`。

需要覆盖的精确名称至少包括：

- `hccl-vm`
- `mpirun` 或当前 MPI launcher
- `all_reduce_test`
- `all_gather_test`
- `reduce_scatter_test`
- checker process

## 10. Evidence 和统一报告

### 10.1 每原语 evidence

目录：

```text
experiments/hccl_vm/evidence/g2_e_allreduce_<timestamp>/
experiments/hccl_vm/evidence/g2_e_allgather_<timestamp>/
experiments/hccl_vm/evidence/g2_e_reducescatter_<timestamp>/
```

每个目录至少包含：

- `README.md`
- `command.txt`
- `manifest.json`
- `result.json`
- `concise.log`
- `raw.log.gz`
- `report.txt`
- `SHA256SUMS`

schema 建议为 `g2-e-primitive-v1`。manifest/result 必须包含：

- canonical primitive
- input alias
- resolved registry contract/version
- request element semantics
- input/output elements 和 bytes
- hccl_test bytes
- executable basename 和最终 path
- argv
- checker metadata contract
- required/observed stages
- Checker Success count
- warning 103 baseline、count、摘要和 regression
- 全部退出码
- cleanup audit
- environment、HCOMM/HCCL commits
- `execution_mode=subprocess_hccl_test`
- `direct_hccl_api_call=false`
- `real_ascend_npu_validated=false`

### 10.2 Suite summary

目录：

```text
experiments/hccl_vm/evidence/g2_e_summary_<timestamp>/
```

建议包含：

- `README.md`
- `summary.json`
- `manifest.json`
- `SHA256SUMS`

summary 不复制三份 raw log，只引用三个 per-primitive evidence 目录和它们的 `SHA256SUMS` digest。至少包含：

- 三原语状态
- 三份 metadata contract 和 observed summaries
- Checker Success 数量
- required/observed stage success
- warning 103 baseline、数量和 regression
- 全部退出码
- per-primitive evidence SHA256
- 统一环境、HCOMM/HCCL branch/commit
- cleanup 状态
- 官方模拟器边界声明

suite summary 只有在三个结果均来自同一 suite id、相同环境 commit、相同 registry version 且全部通过时才可标记完成。任一 primitive 失败或 ENV_BLOCKED 时，summary 必须保留其他原始结果并标为非完成。

## 11. 测试策略

建议新增：

- `tests/test_hccl_vm_registry.py`
- `tests/test_hccl_vm_multi_primitive_commands.py`
- `tests/test_hccl_vm_multi_primitive_checker.py`
- `tests/test_hccl_vm_suite_report.py`
- `tests/fixtures/hccl_vm/` 下精简、不可伪造结论的三原语 parser fixtures

必须覆盖：

1. registry 只含三个 canonical primitive。
2. 每个允许 alias 规范化正确。
3. 未知、近似和恶意 primitive 拒绝。
4. request/CLI 不能注入 executable/path。
5. registry basename 路径逃逸以及 CANN 根目录外的
   `hccl_test_bin` 拒绝。
6. AllGather 传 `--op` 拒绝。
7. AllReduce/ReduceScatter 未传 `--op` 拒绝。
8. 非 INT32、非 2 ranks、错误 elements 拒绝。
9. 三原语 element/input/output/hccl_test byte 计算。
10. 三种 argv 与 G2-C 基线逐 token 相同。
11. 所有动态 shell 字段经 argv + `shlex.join` 安全处理。
12. dry-run 不启动 WSL/process。
13. 三种 parser 正向 fixture。
14. collectiveType/rank/dataType/elementCount mismatch 失败。
15. reduceType mismatch 仅对 AllReduce/ReduceScatter 失败。
16. AllGather observed reduceType 改变不影响 metadata contract。
17. 缺少 Op summary 失败。
18. 多个 summary 中任一个 mismatch 失败。
19. 不依赖恰好两个 opIndex。
20. 缺少 Checker Success 失败。
21. 必需 stage 缺失或 failed 失败。
22. fatal signal 失败。
23. marker/退出码缺失或非零失败。
24. timeout 失败并进入 cleanup。
25. cleanup 残留失败。
26. warning 103 为 `PASS_WITH_WARNING`。
27. warning count/form 变化设置 regression warning。
28. per-primitive evidence schema、gzip 和 SHA256。
29. suite summary 引用、hash、环境一致性和部分失败。
30. Windows 无 WSL/CANN 导入安全。
31. CPU_SIM 仍为默认。
32. Windows 全量 Python/CTest/CLI。
33. Linux 独立 CPU_SIM 构建、CTest、全量 Python/CLI。
34. opt-in 三原语官方环境测试。

当前基线为每平台运行 507 Python tests，1 个 opt-in skipped；G2-E 不得减少现有测试或通过修改 skip 获得绿色结果。

## 12. Checkpoints

所有 checkpoint 从最新 `main` 创建新的 `codex/g2-e-multi-primitive-validation` 或用户指定分支。每个 checkpoint 单独验证和提交，不 push、不 merge。

### G2-E-1 官方命令和 Checker 契约冻结

**修改文件**

- 新增 `docs/hccl_vm_g2_e_contract.md` 或等价冻结文档
- 可新增只含必要日志片段的 `tests/fixtures/hccl_vm/`

**非目标**

- 不修改 runner/parser/CLI。
- 不启动 HCCL-VM。

**测试命令**

```powershell
python -m unittest tests.test_hccl_vm_checker tests.test_hccl_vm_runner_dry_run -q
```

**官方验证命令**

不执行官方闭环。本 checkpoint 只运行本计划第 0 节列出的 WSL help、日志 grep 和 Git metadata 只读命令。

**完成条件**

- 三条 argv、byte 语义、metadata、stage、warning 基线有原始日志行支持。
- fixture 保留真实格式但不改写结果。

**ENV_BLOCKED**

- G2-C 原始日志缺失/校验不一致。
- help 二进制缺失或无法执行。
- HCOMM/HCCL commit 漂移。

**建议 commit**

`G2-E-1 freeze official primitive contracts`

**回滚**

删除本 checkpoint 新增的 contract 文档/fixtures；不触碰原始 evidence。

### G2-E-2 Primitive registry 和通用 request

**修改文件**

- 新增 `plugin/hccl_vm_registry.py`
- 修改 `main.py`
- 修改 `plugin/hccl_vm_runner.py` 的类型入口，不改变实际 AllReduce argv
- 新增 `tests/test_hccl_vm_registry.py`
- 修改 `tests/test_backend_selection.py`

**非目标**

- 不实现 AllGather/ReduceScatter 外部执行。
- 不修改 checker PASS 逻辑。

**测试命令**

```powershell
python -m unittest tests.test_hccl_vm_registry tests.test_backend_selection tests.test_hccl_vm_runner_dry_run -q
```

**官方验证命令**

不执行官方闭环；只执行三个 primitive 的 dry-run 参数拒绝/规范化测试。

**完成条件**

- registry 不可变且不可绕过。
- 未知 primitive、任意 executable、错误 op/dtype/rank/elements 在 process 前失败。
- CPU_SIM 默认不变。

**ENV_BLOCKED**

无官方环境依赖；若单元测试不能在无 WSL/CANN Windows 环境运行，checkpoint 失败而不是 ENV_BLOCKED。

**建议 commit**

`G2-E-2 add strict primitive registry and requests`

**回滚**

移除 registry 并恢复 G2-D request adapter；CPU_SIM 文件不动。

### G2-E-3 AllReduce 迁移到 registry

**修改文件**

- 修改 `plugin/hccl_vm_runner.py`
- 修改 `plugin/hccl_vm_checker.py`
- 修改 `plugin/hccl_vm_env.py`
- 修改 `plugin/hccl_vm_evidence.py`
- 修改相关 G2-D tests

**非目标**

- 不启用 AllGather/ReduceScatter verify。
- 不改变 G2-D AllReduce 命令或成功契约。

**测试命令**

```powershell
python -m unittest tests.test_hccl_vm_registry tests.test_hccl_vm_checker tests.test_hccl_vm_runner_dry_run tests.test_hccl_vm_official_flow tests.test_hccl_vm_report -q
```

**官方验证命令**

```powershell
wsl.exe -d Ubuntu-22.04 -u root -- bash -lc "cd /mnt/f/projects/hccl-agent && python3 main.py verify-official --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
```

**完成条件**

- argv 与 G2-D/G2-C 精确一致。
- Checker、warning、退出码、正常关闭和 evidence 与 G2-D 行为兼容。
- AllReduce 结果仍为真实观测状态，不强制写死 warning。

**ENV_BLOCKED**

- diagnose 非 OK。
- 官方 branch/commit 漂移。
- 两种可靠 runner 修复路径失败。

**建议 commit**

`G2-E-3 migrate allreduce to primitive registry`

**回滚**

revert 本 checkpoint，恢复 G2-D AllReduce request/parser；不删除已生成 evidence。

### G2-E-4 AllGather builder、parser 和官方闭环

**修改文件**

- 修改 `plugin/hccl_vm_registry.py`
- 修改 `plugin/hccl_vm_runner.py`
- 修改 `plugin/hccl_vm_checker.py`
- 修改 `plugin/hccl_vm_env.py`
- 新增/修改 multi-primitive command、checker、flow tests

**非目标**

- 不把 checker 的默认 SUM 当作 AllGather reduce contract。
- 不实现其他 dtype/rank/size。

**测试命令**

```powershell
python -m unittest tests.test_hccl_vm_registry tests.test_hccl_vm_multi_primitive_commands tests.test_hccl_vm_multi_primitive_checker tests.test_hccl_vm_official_flow -q
```

**官方验证命令**

```powershell
wsl.exe -d Ubuntu-22.04 -u root -- bash -lc "cd /mnt/f/projects/hccl-agent && python3 main.py verify-official --backend ASCEND_HCCL_VM --primitive AllGather --nodes 2 --dtype int32 --elements 8"
```

**完成条件**

- argv 不含 `-o`。
- checker elementCount=8；input=32 B，output/hccl_test=64 B。
- 至少一个 Checker Success、全部 summary/stage/退出/cleanup 条件通过。
- warning 103 如存在则 `PASS_WITH_WARNING`。

**ENV_BLOCKED**

- `all_gather_test` 或依赖缺失。
- 基线 metadata 与当前输出发生无法解释的 contract 变化。
- cleanup 无法安全完成。

**建议 commit**

`G2-E-4 verify allgather through official hccl-vm`

**回滚**

revert AllGather registry entry/flow；保留 AllReduce 和原始失败 evidence。

### G2-E-5 ReduceScatter builder、parser 和官方闭环

**修改文件**

- 修改 `plugin/hccl_vm_registry.py`
- 修改 `plugin/hccl_vm_runner.py`
- 修改 `plugin/hccl_vm_checker.py`
- 修改 `plugin/hccl_vm_env.py`
- 扩展 multi-primitive command、checker、flow tests

**非目标**

- 不把 output elements 误当输入总元素。
- 不实现其他 reduce op。

**测试命令**

```powershell
python -m unittest tests.test_hccl_vm_registry tests.test_hccl_vm_multi_primitive_commands tests.test_hccl_vm_multi_primitive_checker tests.test_hccl_vm_official_flow -q
```

**官方验证命令**

```powershell
wsl.exe -d Ubuntu-22.04 -u root -- bash -lc "cd /mnt/f/projects/hccl-agent && python3 main.py verify-official --backend ASCEND_HCCL_VM --primitive ReduceScatter --nodes 2 --dtype int32 --op sum --elements 8"
```

**完成条件**

- checker elementCount=8；input/hccl_test=64 B，output=32 B。
- reduceType=SUM 严格匹配。
- 全部 summary/stage/退出/cleanup 条件通过。

**ENV_BLOCKED**

- `reduce_scatter_test` 或依赖缺失。
- 当前输出与冻结基线发生无法解释的 contract 变化。
- cleanup 无法安全完成。

**建议 commit**

`G2-E-5 verify reducescatter through official hccl-vm`

**回滚**

revert ReduceScatter entry/flow；保留前两个 primitive 和原始 evidence。

### G2-E-6 三原语 evidence 和统一报告

**修改文件**

- 修改 `plugin/hccl_vm_evidence.py`
- 修改 `agent/report_generator.py`
- 修改 `main.py` 的 suite orchestration
- 新增 `tests/test_hccl_vm_suite_report.py`
- 生成三份 per-primitive evidence 和一份 summary evidence

**非目标**

- 不复制 G2-C/G2-D raw logs。
- 不声称真实 NPU 或直接 API。

**测试命令**

```powershell
python -m unittest tests.test_hccl_vm_report tests.test_hccl_vm_suite_report -q
```

**官方验证命令**

推荐、待确认：

```powershell
wsl.exe -d Ubuntu-22.04 -u root -- bash -lc "cd /mnt/f/projects/hccl-agent && python3 main.py verify-official --backend ASCEND_HCCL_VM --suite g2-e"
```

若未批准 suite 参数，则按 G2-E-3/4/5 三条命令依次执行，并以显式 suite id 生成 summary。

**完成条件**

- 八类 per-primitive 文件齐全并通过 SHA256。
- summary 引用三份 digest，环境和 commit 一致。
- 任一 primitive 未通过时 summary 不标 COMPLETED。

**ENV_BLOCKED**

- 任一 per-primitive 结果 ENV_BLOCKED。
- 三次运行环境/commit/registry version 不一致。
- evidence 写入或校验失败。

**建议 commit**

`G2-E-6 archive multi-primitive official evidence`

**回滚**

revert writer/report/suite code；已生成 evidence 作为原始记录保留，不重写或删除。

### G2-E-7 双平台回归和最终审计

**修改文件**

- 只修改 G2-E 测试、文档、审计报告或必要后端适配
- 更新 `docs/project_documentation.md`
- 更新 `docs/project_audit.md`
- 新增 G2-E 完成报告

**非目标**

- 不扩展业务范围。
- 不修改官方源码或历史 evidence。

**测试命令**

Windows：

```powershell
python -m unittest discover -s tests -q
ctest --test-dir hcccl/build -C Release --output-on-failure
python main.py --nodes 4 --message-size 128 --primitive AllReduce
```

Linux CPU_SIM：

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && cmake -S hcccl -B /tmp/hccl-agent-g2e-cpu -DCMAKE_BUILD_TYPE=Release -DHCCL_BACKEND=CPU_SIM"
wsl.exe -d Ubuntu-22.04 -- bash -lc "cmake --build /tmp/hccl-agent-g2e-cpu --parallel"
wsl.exe -d Ubuntu-22.04 -- bash -lc "ctest --test-dir /tmp/hccl-agent-g2e-cpu --output-on-failure"
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && env HCCL_PLUGIN_PATH=/tmp/hccl-agent-g2e-cpu/libhccl_plugin.so python3 -m unittest discover -s tests -q"
```

**官方验证命令**

重新执行 G2-E-6 suite 或三条独立命令，并复核 HCOMM/HCCL status。

**完成条件**

- Windows/Linux Python 不少于当前 507 tests，现有测试不减少或弱化。
- Windows/Linux CTest 全部通过。
- CPU_SIM 默认 CLI 通过。
- 三原语官方结果全部满足严格 contract。
- HCOMM/HCCL tracked status 为空。
- 无遗留进程。
- evidence SHA256 全部通过。

**ENV_BLOCKED**

- 任一官方 primitive 无 Checker Success 或退出码非零。
- 官方源码 tracked status 非空。
- 不能安全清理进程。
- 两种可靠修复路径失败。

**建议 commit**

`G2-E-7 complete multi-primitive validation audit`

**回滚**

revert 最终文档/回归适配 commit；不删除 evidence，不回滚已通过的独立 checkpoint。

## 13. 风险和 ENV_BLOCKED 统一规则

### 13.1 主要风险

1. 三个 hccl_test 的 help 是通用模板，不能仅靠 help 推断 primitive 语义，必须以成功基线日志冻结。
2. 三种 `-b/-e` 都为 64，容易错误复用一个 byte 公式。
3. AllGather checker 打印 `reduceType=SUM`，但命令没有 `-o`，不能把默认值当 contract。
4. check-only baseline 的 hccl_test 数据表可显示 `check_result: failed`，而 CheckerV3 成功；不能使用模糊字符串判定。
5. 当前 parser 会把多 operation stage 合并到一个 dict，可能掩盖单个 operation 缺 stage。
6. 当前 env probe 只验证 `all_reduce_test`。
7. 当前 `--op=sum` 默认值使 AllGather 无法区分“未提供”和“显式提供”。
8. warning 103 数量可能随官方实现变化，需要报告 regression 但不能单独误判 FAIL。
9. HCCL-VM 交互 prompt、PTY 和多层 Windows/WSL/bash quoting 仍是脆弱边界。
10. concurrent 官方会话会使 postflight process 判断和清理归属不明确。

### 13.2 ENV_BLOCKED 分类

- `ENV_BLOCKED_WSL`
- `ENV_BLOCKED_CANN`
- `ENV_BLOCKED_HCCL_VM`
- `ENV_BLOCKED_HCCL_TEST_<PRIMITIVE>`
- `ENV_BLOCKED_CHECKER`
- `ENV_BLOCKED_MPI`
- `ENV_BLOCKED_GIT_METADATA`
- `ENV_BLOCKED_BRANCH_COMMIT`
- `ENV_BLOCKED_TIMEOUT`
- `ENV_BLOCKED_CONCURRENT_PROCESS`
- `ENV_BLOCKED_CONTRACT_DRIFT`
- `ENV_BLOCKED_EVIDENCE`

ENV_BLOCKED 必须保留 checkpoint、命令、退出码、原始错误、已尝试路径、为何不能安全继续和恢复命令。ENV_BLOCKED 不得写为 PASS。连续两种可靠修复路径失败后停止；不得下载依赖、修改官方源码、放宽全局 Git 信任或伪造结果。

## 14. 需要用户确认的设计选择

1. **AllGather `--op`**：建议严格拒绝任何显式 `--op`，不静默忽略。
2. **Suite CLI**：建议 `verify-official --suite g2-e`，与 `--primitive` 互斥；不把 `All` 注册为 primitive。
3. **Warning regression**：建议固定契约下 warning 103 count 不等于 4，或出现新 normalized form，即设置 `warning_regression=true`；它本身不导致 FAIL。
4. **Diagnose 顶层状态**：建议任一 registry primitive 不可用时顶层为 ENV_BLOCKED，但单 primitive verify 只被公共环境和自身 executable 阻塞。
5. **Stage 粒度**：建议按 operation block 要求四个必需 stage，而不是只要求整份日志中各出现一次。

## 15. 完成标准和全局回滚边界

G2-E 只有在以下条件全部有实际命令和 evidence 支持时才能标记 COMPLETED：

- registry 白名单不可绕过。
- 三种请求语义和 argv 与冻结基线一致。
- 三原语分别取得退出码 0、严格 metadata match、必需 stage success、Checker Success 和正常关闭。
- warning 103 被完整记录和分类。
- cleanup 无残留。
- per-primitive evidence 和 suite summary SHA256 通过。
- Windows/Linux CPU_SIM 和全量测试无回归。
- HCOMM/HCCL tracked status 为空。
- 文档明确区分 CPU_SIM、官方 HCCL-VM 模拟验证和真实 NPU。

全局回滚以 checkpoint commit 为单位执行 `git revert`，不得删除或重写已生成 evidence，不得修改官方目录。`CPU_SIM` 默认路径与 G2-D AllReduce 兼容性是每个 checkpoint 的回滚保护线。

## 16. 当前状态声明

本文件仅为 G2-E 可执行计划。尚未开始 G2-E 业务代码实现，尚未启动新的 HCCL-VM 官方验证，尚未生成 G2-E evidence，尚未创建 commit，也未 push 或 merge。
