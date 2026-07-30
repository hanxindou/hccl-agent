# HCCL Agent V1：Linux 交付与 Correctness Hardening 执行计划

版本：v1.0  
计划日期：2026-07-30  
项目路径：`F:\projects\hccl-agent`  
Codex 运行环境：Windows Native  
Linux 验证环境：优先使用 Docker Desktop Linux 容器  
前置里程碑：C2—H1 已完成

---

## 1. V1 总目标

在不依赖 CANN SDK、Ascend 实机、HCOMM、msprof 或外部 LLM API 的条件下，将当前 Windows CPU_SIM 原型推进为：

> Windows/Linux 双平台可构建、三种核心 primitive 支持多元素 buffer、关键 rank 规模连续、具备固定 seed 随机化 reference 验证和 Linux CI 配置的正确性基线。

V1 重点解决当前已经明确存在的工程缺口：

1. Linux `libhccl_plugin.so` 尚未实际构建和加载验证；
2. AllReduce 当前文档只证明 `count=1` 标量路径；
3. ReduceScatter 仍存在 2-rank legacy `NOT_SUPPORTED` 例外；
4. correctness 主要依赖固定样例，缺少确定性随机测试；
5. H1 进度、用户待办和准备度文档存在少量事实未同步；
6. Linux 后续回归尚未纳入自动化 CI。

V1 不追求新增更多 Agent Skill、拓扑模型、可靠性模型或模拟性能数字。

---

## 2. 当前稳定基线

开始执行前，应通过 Git 和文档核验以下基线。

### 2.1 预期阶段提交

```text
4109491 feat: complete C2 ReduceScatter correctness
d7c45f6 feat: add C3 numeric correctness baseline
de501ad feat: add E1 autonomous code development loop
17f09a5 feat: converge D1 topology and cost models
45cc247 feat: add F1 reliability validation flow
bfe23ea chore: prepare G1 CANN integration layer
ede07dc docs: complete autonomous competition readiness audit
```

以上 commit ID 仅作为预期事实，执行前必须以当前仓库中的 `git log` 为准。

### 2.2 当前已验证能力

- Windows Native；
- Visual Studio 2022 x64；
- Release 构建；
- `HCCL_BACKEND=CPU_SIM`；
- Windows `hccl_plugin.dll`；
- CTest 11/11；
- Python 完整回归 454 tests；
- AllReduce、AllGather、ReduceScatter CPU_SIM；
- FP32 SUM/PROD/MAX/MIN；
- FP16/BF16 CPU 软件模拟；
- Agent E1 离线模板闭环；
- D1 analytical model；
- F1 fixed-seed reliability model；
- G1 CANN/Ascend 条件编译准备。

### 2.3 当前未验证边界

- Linux `libhccl_plugin.so`；
- Linux CTest；
- Linux Python ctypes 加载；
- CANN/HCOMM 真实编译与链接；
- Ascend 实机；
- 真实多进程、多设备通信；
- msprof；
- 实机 FP16/BF16 误差；
- 实机性能与可靠性。

---

## 3. 需求优先级

发生要求冲突时，按以下顺序处理：

1. 赛题原始文档  
   `docs/2026年中国研究生人工智能大赛--华为赛题.docx`
2. 本文件  
   `docs/v1_execution_plan.md`
3. `docs/competition_readiness_report.md`
4. `docs/correctness_matrix.md`
5. `docs/roadmap_v2.md`
6. `docs/project_audit.md`
7. 当前已经通过测试的代码行为
8. 其他历史文档

若赛题原文与当前 CPU_SIM 数据契约冲突：

- 不得静默修改；
- 在 `docs/v1_progress.md` 中记录；
- 采用最小兼容方案；
- 公共 ABI 无法安全兼容时停止对应子任务；
- 不阻塞其他无关 V1 阶段。

---

## 4. V1 阶段顺序

严格按以下顺序执行：

```text
V1-A：事实与文档基线修正
  ↓
V1-B：Collective 多元素和 rank 连续性加固
  ↓
V1-C：确定性随机化 correctness
  ↓
V1-D：Docker Linux .so 构建与加载验证
  ↓
V1-E：Linux CI、最终回归和材料收敛
```

除非存在明确依赖阻塞，不得随意调整顺序。

Docker 不可用时：

```text
V1-A → V1-B → V1-C 正常完成
V1-D 标记 ENV_BLOCKED
V1-E 仍生成验证脚本和 CI 配置
```

Docker 环境问题不得阻塞 Windows correctness 工作。

---

## 5. 全局执行原则

### 5.1 正确性优先级

```text
数据正确性
> 内存安全
> ABI 兼容
> 跨平台构建
> 可重复测试
> 文档证据
> 执行速度
> 展示效果
```

### 5.2 不得伪造成功

统一使用以下状态：

| 状态                    | 含义                                   |
| ----------------------- | -------------------------------------- |
| `IMPLEMENTED`           | 对应代码已实现并通过目标环境测试       |
| `CPU_SIMULATED`         | 单进程 CPU buffer 数据路径已验证       |
| `CPU_EMULATED_FP16`     | FP16 软件编码和 FP32 内部计算已验证    |
| `CPU_EMULATED_BF16`     | BF16 软件编码和 FP32 内部计算已验证    |
| `REFERENCE_VERIFIED`    | 与独立 reference 比较通过              |
| `WINDOWS_VERIFIED`      | 已在 Windows DLL 环境验证              |
| `LINUX_DOCKER_VERIFIED` | 已在 Docker Linux 环境实际验证         |
| `CI_CONFIGURED_UNRUN`   | CI 文件已创建，但未在远端 Actions 运行 |
| `ENV_BLOCKED`           | 受 Docker、网络或系统环境阻塞          |
| `STUB_UNVERIFIED`       | 尚未实现，必须返回明确错误             |
| `NOT_SUPPORTED`         | 当前明确不支持                         |

规则：

- Docker 未运行时不得写成 Linux 已验证；
- 创建 GitHub Actions 文件不等同于 CI 已运行；
- Windows DLL 不等同于 Linux `.so`；
- Docker Linux CPU_SIM 不等同于 Ascend；
- FP16/BF16 软件模拟不等同于硬件混合精度；
- 随机化测试不等同于形式化证明；
- 不得将 CPU_SIM latency/bandwidth 作为实机性能。

### 5.3 有限尝试规则

1. 同一编译或测试问题最多两轮针对性修复；
2. 同一 Docker 问题最多：
   - 一次正常尝试；
   - 一次低风险修复；
3. Docker 镜像或依赖下载失败后，不得反复重试；
4. 不允许花费大量时间修复 WSL、代理或 Docker Desktop 本身；
5. 不允许切换 Codex 到 WSL 环境；
6. 不允许操作旧 WSL 仓库；
7. 同一随机测试失败必须先输出 seed 和 case 参数，再进行修复；
8. 不通过删除、跳过或放宽测试掩盖错误；
9. 完整回归失败时不得继续扩大修改范围。

### 5.4 最小修改原则

V1 不重新设计：

- B1 动态库发现优先级；
- E1 Agent 开发闭环；
- D1 拓扑与成本模型；
- F1 可靠性模型；
- G1 CANN backend 结构；
- Agent 主编排架构；
- 公共 API，除非确有必要且向后兼容。

不增加：

- Broadcast；
- 新 Agent Skill；
- 新性能评分体系；
- 新拓扑类型；
- 新可靠性故障类型；
- 真实外部 LLM 调用；
- CANN Stub 成功路径。

---

## 6. 工作区与 Git 规则

### 6.1 开始前检查

必须执行：

```cmd
git status --short
git status -sb
git log -10 --oneline
```

要求：

- `git status --short` 无输出；
- 当前目录为 `F:\projects\hccl-agent`；
- 当前分支明确；
- 不存在其他线程产生的修改。

若工作区不干净：

- 停止整个 V1；
- 不删除；
- 不恢复；
- 不覆盖；
- 不执行 `git reset --hard`；
- 只报告文件列表。

### 6.2 本地阶段提交授权

V1 允许 Codex在每个阶段通过验收后创建独立本地提交。

每次提交前必须执行：

```cmd
git status --short
git diff --name-only
git diff --stat
git diff --check
```

然后使用精确文件列表暂存。

禁止：

```text
git add .
git add -A
```

暂存后必须执行：

```cmd
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
```

只有以下条件同时满足时才能提交：

- 暂存区只包含当前阶段文件；
- `git diff --cached --check` 无输出；
- 当前阶段所有闸门通过；
- 无二进制、缓存、密钥和构建产物；
- 没有无关修改。

### 6.3 禁止操作

```text
git push
git push --force
git reset --hard
git rebase
git clean
git checkout -- .
git restore .
```

不得提交：

- `.dll`
- `.lib`
- `.exe`
- `.obj`
- `.pdb`
- `.so`
- CMake 构建目录
- Docker layer/cache
- Python cache
- API Key
- 凭据
- 大型日志
- 临时随机测试数据

### 6.4 建议提交信息

```text
docs: correct V1 baseline evidence
feat: harden collective buffer correctness
test: add deterministic randomized correctness
test: validate Linux CPU_SIM backend
ci: add Linux CPU_SIM validation
docs: complete V1 delivery audit
```

若某阶段只部分完成，提交信息不得包含 `complete`。

---

## 7. 进度文件

创建：

```text
docs/v1_progress.md
```

每个阶段追加：

```markdown
## Stage V1-X：阶段名称

开始时间：  
结束时间：  
状态：COMPLETED / PARTIAL / BLOCKED / SKIPPED

### 修改文件

- ...

### 数据契约

- ...

### 验收结果

- Windows CMake：
- Windows CTest：
- 定向 Python：
- 完整 Python：
- Docker：
- Linux CMake：
- Linux CTest：
- Linux Python：

### 遇到的问题

- ...

### 修复轮次

- ...

### 降级状态

- ...

### 用户待办

- ...

### 本地提交

- commit：
- message：

### 未验证边界

- ...
```

不得删除此前阶段记录。

---

# 8. Stage V1-A：事实与文档基线修正

优先级：P0  
预计类型：纯文档和事实同步  
不得修改运行逻辑。

## 8.1 目标

消除当前 H1 材料中的已知事实不一致。

## 8.2 必须检查和修正

### A. H1 commit

检查：

```text
docs/autonomous_progress.md
```

若 H1 仍写着：

```text
commit：待创建
```

应根据 Git 历史更新为实际 H1 commit。

预期为：

```text
ede07dc docs: complete autonomous competition readiness audit
```

必须以实际 `git log` 为准。

### B. 阶段时间重叠

当前记录可能存在：

```text
C3-B：21:43—22:10
E1：22:00—22:10
```

不得凭空修改时间。

处理方式：

- 若无法从日志证明准确时间，在 `docs/autonomous_progress.md` 中增加说明：
  - 时间来自自主执行记录；
  - 部分阶段准备或记录存在重叠；
  - commit 和测试结果是主要阶段证据。
- 不伪造新的精确时间。

### C. Linux 待办路径

将 `docs/user_actions.md` 中类似：

```text
/tmp/hccl-agent-hcccl-c2
```

改为阶段无关名称，例如：

```text
/tmp/hccl-agent-linux-review
```

### D. AllReduce 当前限制

在 V1-B 完成前，文档必须准确保留当前事实：

```text
AllReduce 当前主要证明 count=1 标量路径。
```

V1-B 完成后再更新为多元素已验证。

### E. ReduceScatter 2-rank 例外

文档必须准确记录：

```text
2-rank legacy 标量场景当前返回 NOT_SUPPORTED。
```

V1-B 完成后再删除此限制。

### F. FP16/BF16 精度口径

检查赛题原文和当前文档中：

```text
误差 <= 1e-6
FP16 tolerance = 1e-3
BF16 tolerance = 2e-2
```

之间的关系。

要求：

- 不得自行断言赛题的 `1e-6` 一定适用于 FP16/BF16 最终量化输出；
- 若赛题原文不能明确解释，文档中必须标记为：
  `REQUIRES_COMPETITION_CLARIFICATION`；
- 保留当前 CPU 软件模拟 tolerance；
- 不得把 CPU tolerance 描述为已经满足 Ascend 最终精度要求。

## 8.3 主要修改文件

可能包括：

```text
docs/autonomous_progress.md
docs/competition_readiness_report.md
docs/correctness_matrix.md
docs/user_actions.md
docs/v1_progress.md
```

## 8.4 验收闸门

- 只修改文档；
- 所有 commit ID 与 Git 历史一致；
- 未验证边界没有被删除；
- `git diff --check` 无输出；
- 不修改运行代码；
- Windows 当前基线无需重复完整构建，但不得声称新代码验证。

通过后创建本地提交：

```text
docs: correct V1 baseline evidence
```

---

# 9. Stage V1-B：Collective 多元素与 rank 连续性加固

优先级：P0

## 9.1 目标

完成：

1. AllReduce 多元素 buffer；
2. ReduceScatter 2-rank 正确性；
3. FP32、FP16、BF16 路径回归；
4. SUM、PROD、MAX、MIN 回归；
5. Windows DLL 实际加载验证。

## 9.2 AllReduce CPU_SIM 数据契约

设：

```text
N = rank 数
C = 每个 rank 的元素数量
```

输入：

```text
send[N][C]
```

扁平长度：

```text
N * C
```

输出：

```text
recv[N][C]
```

扁平长度：

```text
N * C
```

语义：

```text
recv[dst_rank][element]
=
REDUCE(
    send[src_rank][element]
    for src_rank in 0..N-1
)
```

AllReduce 后每个目标 rank 应获得相同的归约结果。

扁平索引：

```text
send[src_rank * C + element]
recv[dst_rank * C + element]
```

不得只计算元素 0。

## 9.3 AllReduce 最低覆盖

rank：

```text
1, 2, 4, 8, 16
```

count：

```text
1, 3, 17, 256
```

FP32 ReduceOp：

```text
SUM
PROD
MAX
MIN
```

dtype：

```text
FP32
FP16
BF16
```

最低要求：

- FP32 覆盖全部 rank、count、ReduceOp；
- FP16/BF16 至少覆盖：
  - rank 2、4、8；
  - count 1、3、17；
  - SUM；
- FP16/BF16 其他 ReduceOp 若当前实现已支持，应回归验证；
- 不得通过跳过现有路径维持通过。

## 9.4 算法路径

检查当前已经存在的：

```text
Ring
Butterfly
Mesh
NHR
Fat-Tree
hcclAllReduce wrapper
```

要求：

- 每个当前声明支持 AllReduce 的 CPU_SIM 路径不得继续只处理第一个元素；
- 公共 helper 可以复用；
- 不复制五份相同 dtype/reduce 逻辑；
- 算法特有调度可以保留；
- wrapper 默认路径必须支持多元素；
- 不得因 count 扩展破坏 `count=1`。

若某个算法名称只有性能模拟意义，而数据实现实际共用统一 reference kernel：

- 可以继续共用；
- 文档必须准确描述；
- 不得伪造每个算法都具有独立通信调度实现。

## 9.5 ReduceScatter 2-rank 数据契约

沿用已有契约：

```text
send[N][N][C] -> recv[N][C]
```

扁平长度：

```text
input  = N * N * C
output = N * C
```

语义：

```text
recv[dst_rank][element]
=
REDUCE(
    send[src_rank][dst_rank][element]
    for src_rank in 0..N-1
)
```

扁平索引：

```text
send[(src_rank * N + dst_rank) * C + element]
recv[dst_rank * C + element]
```

要求：

- N=2 必须使用与 N=4/8/16 相同契约；
- 删除或改写仅因旧标量形状而返回 `NOT_SUPPORTED` 的特殊分支；
- 不允许为了通过测试读取短 buffer；
- 更新旧测试，使其提供正确长度的输入和输出；
- 不破坏 N=1/4/8/16。

## 9.6 数值安全要求

### FP32

- SUM 使用明确的 FP32 行为；
- PROD 避免错误 identity；
- MAX 初值不能为 0；
- MIN 初值不能为 0；
- NaN/Inf 行为保持既有测试结论；
- overflow 允许产生 Inf，但必须有测试。

### FP16/BF16

- 输入按现有 16-bit 编码解析；
- 内部 FP32 计算；
- 输出重新编码；
- 不改变既有 tolerance；
- 不宣称硬件等价。

## 9.7 建议修改文件

根据实际结构确定，可能包括：

```text
hcccl/include/hccl_algorithms.h
hcccl/src/hccl_algorithms.c
hcccl/src/hccl_comm.c
hcccl/tests/test_ring.c
hcccl/tests/test_butterfly.c
hcccl/tests/test_mesh.c
hcccl/tests/test_nhr.c
hcccl/tests/test_fattree.c
hcccl/tests/test_reduce_ops.c
hcccl/tests/test_reducescatter.c
hcccl/tests/test_dtype_emulation.c
plugin/execution_engine.py
plugin/hccl_api.py
plugin/hccl_bridge.py
tests/test_reduce_ops.py
tests/test_reducescatter.py
tests/test_dtype_emulation.py
tests/test_hccl_api.py
docs/correctness_matrix.md
docs/v1_progress.md
```

不得为了匹配此列表而修改无关文件。

## 9.8 Windows 验收

使用全新构建目录：

```cmd
set BUILD_DIR=F:\build\hccl-agent-v1b

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

cmake -S hcccl -B "%BUILD_DIR%" ^
  -G "Visual Studio 17 2022" ^
  -A x64 ^
  -DHCCL_BACKEND=CPU_SIM

cmake --build "%BUILD_DIR%" --config Release

ctest --test-dir "%BUILD_DIR%" ^
  -C Release ^
  --output-on-failure

set HCCL_PLUGIN_PATH=%BUILD_DIR%\Release\hccl_plugin.dll
set DEEPSEEK_API_KEY=
set OPENAI_API_KEY=
set ANTHROPIC_API_KEY=

python -m unittest ^
  tests.test_reduce_ops ^
  tests.test_reducescatter ^
  tests.test_dtype_emulation ^
  tests.test_hccl_api ^
  tests.test_execution_engine ^
  -q

python -m unittest discover tests -q
```

## 9.9 阶段闸门

必须满足：

- Windows Release CMake 通过；
- Windows Release Build 通过；
- CTest 全部通过，数量不得少于 11；
- 完整 Python 回归 0 failures、0 errors；
- 测试数量不得低于 H1 的 454，除非有明确、合理且记录完整的测试合并；
- AllReduce `count > 1` reference 通过；
- ReduceScatter 2-rank reference 通过；
- AllReduce、AllGather、ReduceScatter 既有测试全部通过；
- 实际加载本轮 DLL；
- 不出现新的 C4819；
- `git diff --check` 无输出；
- 文档矩阵更新为实际状态。

通过后创建本地提交：

```text
feat: harden collective buffer correctness
```

---

# 10. Stage V1-C：确定性随机化 Correctness

优先级：P0/P1

## 10.1 目标

建立可重复、可定位、运行时间受控的随机化 correctness suite。

这不是无边界 fuzz。

## 10.2 测试原则

- 固定 seed；
- 每次失败打印完整复现参数；
- Python reference 独立于 C 实现；
- 不调用生产 C helper 计算 reference；
- 不依赖网络；
- 不依赖 NumPy，除非 NumPy 已经是项目固定依赖；
- 测试总时间应可接受；
- 不产生随机 flaky failure。

## 10.3 建议测试文件

```text
tests/test_randomized_collective_correctness.py
```

必要时新增：

```text
hcccl/tests/test_randomized_correctness.c
```

C 随机测试不是强制项；Python 通过实际 DLL 调用是核心要求。

## 10.4 固定 seed

至少使用：

```text
20260730
20260801
9102026
```

允许增加不超过 5 个 seed。

每个 seed 建议生成：

```text
10—20 个 case
```

总 case 数控制在：

```text
30—100
```

不得无限生成。

## 10.5 随机参数空间

primitive：

```text
AllReduce
AllGather
ReduceScatter
```

rank：

```text
1
2
4
8
16
```

count：

```text
1
2
3
7
17
32
64
```

dtype：

```text
FP32
FP16
BF16
```

ReduceOp：

```text
SUM
PROD
MAX
MIN
```

AllGather 不使用 ReduceOp。

## 10.6 数据生成规则

常规随机数据：

```text
[-4.0, 4.0]
```

PROD：

- 使用更窄范围，例如 `[-1.5, 1.5]`；
- 控制 count 和 rank，避免所有 case 都溢出；
- 另设确定性 overflow 测试。

必须包含：

- 正数；
- 负数；
- 零；
- 小数；
- 重复值；
- 极小值；
- 边界舍入值。

NaN、Inf 和 overflow：

- 使用独立确定性 case；
- 不随机混入所有普通 case；
- 明确比较规则。

## 10.7 Reference 要求

### FP32

Python reference 必须明确模拟 FP32 边界。

可使用：

- `ctypes.c_float`；
- `struct.pack/unpack`；
- 项目已有独立 Python float32 helper。

不得直接调用生产 DLL 获取“reference”。

### FP16/BF16

允许复用项目独立的 Python encode/decode reference helper，但：

- 不得调用 C 实现；
- helper 必须在测试侧或明确的 reference 模块；
- 输出按现有 tolerance 比较。

### 比较规则

FP32：

```text
普通有限值：最大绝对误差按当前 correctness 规则
NaN：isnan 比较
Inf：符号一致
```

FP16：

```text
tolerance = 1e-3
```

BF16：

```text
tolerance = 2e-2
```

上述 tolerance 仅适用于 CPU 软件模拟。

## 10.8 失败输出

每个失败必须输出：

```text
seed
case_index
primitive
rank_count
count
dtype
reduce_op
input摘要
expected
actual
最大绝对误差
```

失败 case 应能通过一个单独参数重新运行。

建议支持环境变量或命令行过滤，例如：

```text
HCCL_RANDOM_SEED
HCCL_RANDOM_CASE
```

不是强制项，但应优先实现。

## 10.9 测试时长

- 定向随机 suite 建议不超过 60 秒；
- 完整 Python 回归不得因随机测试无限增长；
- 不运行百万级元素；
- 不进行多线程 fuzz；
- 不进行长时间压力测试。

## 10.10 验收命令

```cmd
set HCCL_PLUGIN_PATH=F:\build\hccl-agent-v1b\Release\hccl_plugin.dll

python -m unittest ^
  tests.test_randomized_collective_correctness ^
  -v

python -m unittest ^
  tests.test_reduce_ops ^
  tests.test_reducescatter ^
  tests.test_allgather ^
  tests.test_dtype_emulation ^
  tests.test_randomized_collective_correctness ^
  -q

python -m unittest discover tests -q
```

并重新运行：

```cmd
ctest --test-dir F:\build\hccl-agent-v1b ^
  -C Release ^
  --output-on-failure
```

## 10.11 阶段闸门

- 至少 3 个固定 seed；
- 至少 30 个随机 case；
- 三种 primitive 均覆盖；
- rank=2 必须被覆盖；
- count>1 必须被覆盖；
- FP32、FP16、BF16 均有覆盖；
- SUM/PROD/MAX/MIN 均有覆盖；
- 失败信息具备复现参数；
- 连续运行两次结果一致；
- CTest 全部通过；
- 完整 Python 回归 0 failures、0 errors；
- 不删除既有确定性测试；
- `git diff --check` 无输出。

通过后创建本地提交：

```text
test: add deterministic randomized correctness
```

---

# 11. Stage V1-D：Docker Linux `.so` 验证

优先级：P0/P1  
环境依赖：Docker Desktop  
Codex 仍运行在 Windows Native。

## 11.1 目标

在 Docker Linux 容器中实际完成：

```text
GCC/CMake
→ libhccl_plugin.so
→ CTest
→ Python ctypes 加载
→ 定向 correctness
→ 完整 Python 回归
```

不得切换 Codex 到 WSL 环境。

## 11.2 Docker 前置检查

先执行：

```cmd
docker version
docker info
```

### Docker 可用

继续 Linux 实测。

### Docker 不可用

最多执行一次低风险复查。

不得：

- 调试 WSL 内核；
- 修改 `.wslconfig`；
- 修改代理；
- 安装 Docker；
- 重启系统；
- 操作旧 WSL 仓库；
- 反复重试 Docker daemon。

将 V1-D 标记：

```text
ENV_BLOCKED
```

然后：

- 生成 Linux 验证脚本；
- 生成 Linux CI；
- 更新 `docs/user_actions.md`；
- 继续 V1-E；
- 不声明 Linux 已验证。

## 11.3 建议新增文件

```text
scripts/validate_linux_cpu_sim.sh
docker/linux-cpu-sim.Dockerfile
```

如项目已有适合的容器结构，应优先复用，不强制新增重复目录。

## 11.4 Linux 验证脚本要求

`scripts/validate_linux_cpu_sim.sh` 必须：

- 使用 `set -euo pipefail`；
- 接受可选构建目录；
- 默认使用容器内 `/tmp/hccl-agent-linux-review`；
- 使用 `HCCL_BACKEND=CPU_SIM`；
- 使用 Release 构建；
- 运行 CTest；
- 自动找到实际 `.so`；
- 设置 `HCCL_PLUGIN_PATH`；
- 清空外部 LLM API Key；
- 运行定向 Python；
- 运行完整 Python；
- 打印版本和最终摘要；
- 不执行 Git；
- 不写入仓库构建目录。

建议逻辑：

```bash
#!/usr/bin/env bash
set -euo pipefail

BUILD_DIR="${1:-/tmp/hccl-agent-linux-review}"

rm -rf "$BUILD_DIR"

python3 --version
cmake --version
cc --version

cmake -S hcccl -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DHCCL_BACKEND=CPU_SIM

cmake --build "$BUILD_DIR" -j

ctest --test-dir "$BUILD_DIR" --output-on-failure

PLUGIN_PATH="$(find "$BUILD_DIR" -type f -name 'libhccl_plugin.so' -print -quit)"

if [[ -z "$PLUGIN_PATH" ]]; then
  echo "libhccl_plugin.so not found" >&2
  exit 1
fi

export HCCL_PLUGIN_PATH="$PLUGIN_PATH"
unset DEEPSEEK_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY || true

python3 -m unittest \
  tests.test_reduce_ops \
  tests.test_reducescatter \
  tests.test_allgather \
  tests.test_dtype_emulation \
  tests.test_randomized_collective_correctness \
  tests.test_hccl_api \
  tests.test_execution_engine \
  -q

python3 -m unittest discover tests -q

echo "LINUX_CPU_SIM_VALIDATION_OK"
echo "HCCL_PLUGIN_PATH=$HCCL_PLUGIN_PATH"
```

Codex应根据项目实际依赖调整，不得机械复制导致错误。

## 11.5 Dockerfile 要求

建议基础镜像：

```text
ubuntu:22.04
```

最低安装：

```text
build-essential
cmake
python3
python3-pip
```

仅在项目需要时安装额外依赖。

要求：

- 不写入任何 API Key；
- 不复制本地构建产物；
- 不运行 WSL 特定命令；
- 不使用来源不明镜像；
- 不上传镜像；
- 不将整个 Git 历史作为必要依赖；
- 尽量利用 Docker layer 缓存。

## 11.6 Docker 执行

Codex根据当前 Shell 使用正确的 bind mount 语法。

目标行为：

```text
Windows 仓库
→ bind mount 到 /workspace
→ 容器内执行 bash scripts/validate_linux_cpu_sim.sh
```

不得在仓库目录生成 Linux build 目录。

## 11.7 Linux 验收标准

只有实际满足以下条件，才能标记：

```text
LINUX_DOCKER_VERIFIED
```

要求：

- Docker container exit code 0；
- Linux CMake 配置通过；
- GCC/Clang 编译通过；
- `libhccl_plugin.so` 实际存在；
- CTest 全部通过；
- Python 实际通过 ctypes 加载该 `.so`；
- 定向 correctness 通过；
- 完整 Python 0 failures、0 errors；
- 无 Windows DLL 被误加载；
- 不依赖 Windows路径；
- 不出现路径硬编码；
- 不出现只在 MSVC 下可用的代码。

## 11.8 若 Linux 暴露跨平台问题

允许修复：

- MSVC/GCC 条件编译；
- 符号导出；
- include；
- 路径；
- CMake；
- 标准 C 兼容；
- 动态库名称；
- 测试路径。

不允许顺带重构算法。

每个问题最多两轮修复。

修复后必须重新运行：

- Windows CMake；
- Windows CTest；
- Windows完整 Python；
- Docker Linux全流程。

确保修复 Linux 不破坏 Windows。

## 11.9 阶段闸门

### Docker 成功路径

- Linux全流程通过；
- Windows完整回归再次通过；
- 文档更新为 `LINUX_DOCKER_VERIFIED`；
- 保存关键文本摘要，不提交大型日志；
- `git diff --check` 无输出。

本地提交：

```text
test: validate Linux CPU_SIM backend
```

### Docker 阻塞路径

- 状态为 `ENV_BLOCKED`；
- `docs/user_actions.md` 有明确操作；
- Linux脚本可供用户或 CI 执行；
- 不得创建声称 Linux 已验证的提交。

允许创建：

```text
chore: add Linux CPU_SIM validation tooling
```

---

# 12. Stage V1-E：Linux CI 与最终材料收敛

优先级：P1

## 12.1 目标

建立可重复的 Linux CI 配置，并完成 V1 最终审计。

## 12.2 GitHub Actions

建议新增：

```text
.github/workflows/linux-cpu-sim.yml
```

触发条件建议：

```text
pull_request
workflow_dispatch
```

是否启用 `push` 触发应根据项目当前 CI 结构决定，避免重复消耗 Actions。

CI 应执行：

```text
checkout
安装 Python 3.10
安装 CMake/GCC
安装项目 Python 依赖
CPU_SIM Release 构建
CTest
设置 HCCL_PLUGIN_PATH
定向 correctness
完整 Python unittest
```

要求：

- 不使用真实 API Key；
- 不调用外部 LLM；
- 不下载 CANN；
- 不声称验证 Ascend；
- 不提交构建产物；
- 路径从构建输出动态确定；
- 与 `scripts/validate_linux_cpu_sim.sh` 尽量复用。

## 12.3 CI 状态标记

在未执行 `git push` 的情况下，只能标记：

```text
CI_CONFIGURED_UNRUN
```

不得写成：

```text
GitHub Actions passed
```

只有用户后续 push 并提供 Actions 结果后才能更新状态。

## 12.4 最终文档

更新或生成：

```text
docs/v1_progress.md
docs/v1_validation_report.md
docs/correctness_matrix.md
docs/competition_readiness_report.md
docs/user_actions.md
README.MD
```

必要时在：

```text
docs/autonomous_progress.md
```

顶部或末尾增加：

```text
后续 V1 Linux 与 correctness hardening 进度见 docs/v1_progress.md。
```

不得把完整 V1 日志再次复制进旧文件。

## 12.5 V1 Validation Report

创建：

```text
docs/v1_validation_report.md
```

至少包含：

1. V1 目标；
2. 开始 Git 基线；
3. AllReduce 多元素数据契约；
4. ReduceScatter 2-rank 数据契约；
5. rank/count/dtype/ReduceOp 覆盖矩阵；
6. 固定 seed 随机测试；
7. Windows构建和测试；
8. Docker Linux构建和测试；
9. Linux `.so` 实际路径；
10. CI 配置状态；
11. 未验证的 CANN/HCOMM/Ascend 边界；
12. 用户后续操作；
13. V1 各阶段 commit；
14. 最终 Git 状态。

## 12.6 最终全量 Windows 验收

使用全新目录：

```cmd
set BUILD_DIR=F:\build\hccl-agent-v1-final

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

cmake -S hcccl -B "%BUILD_DIR%" ^
  -G "Visual Studio 17 2022" ^
  -A x64 ^
  -DHCCL_BACKEND=CPU_SIM

cmake --build "%BUILD_DIR%" --config Release

ctest --test-dir "%BUILD_DIR%" ^
  -C Release ^
  --output-on-failure

set HCCL_PLUGIN_PATH=%BUILD_DIR%\Release\hccl_plugin.dll
set DEEPSEEK_API_KEY=
set OPENAI_API_KEY=
set ANTHROPIC_API_KEY=

python -m unittest ^
  tests.test_reduce_ops ^
  tests.test_reducescatter ^
  tests.test_allgather ^
  tests.test_dtype_emulation ^
  tests.test_randomized_collective_correctness ^
  tests.test_hccl_api ^
  tests.test_execution_engine ^
  -q

python -m unittest discover tests -q
```

## 12.7 ASCEND_CANN 缺失环境回归

继续验证：

- `CPU_SIM` 默认或显式配置正常；
- `ASCEND_CANN` 缺 SDK 时快速失败；
- 错误信息仍清楚；
- V1 不得破坏 G1。

不得下载或伪造 SDK。

## 12.8 最终 Git 检查

执行：

```cmd
git status --short
git diff --check
git log --oneline --decorate -15
```

检查已跟踪二进制：

```cmd
git ls-files
```

确认没有新增：

```text
.dll
.lib
.exe
.obj
.pdb
.so
build/
CMakeFiles/
__pycache__/
API Key
```

## 12.9 最终闸门

V1 成功必须满足：

### 必须项

- AllReduce `count > 1` 已验证；
- ReduceScatter 2-rank 已验证；
- 1/2/4/8/16 rank 具有确定性测试证据；
- FP32 SUM/PROD/MAX/MIN 通过；
- FP16/BF16 CPU 软件模拟回归通过；
- 至少 3 个固定 seed；
- 至少 30 个随机 case；
- Windows全新 Release 构建通过；
- Windows CTest 全部通过；
- Windows完整 Python 0 failures、0 errors；
- 完整测试数量不低于 H1 基线；
- G1 缺 SDK 快速失败行为保持；
- 工作区最终干净；
- 未执行 Git push。

### Linux 分支

以下二者满足其一：

#### A. 完成

- Docker Linux CMake通过；
- `libhccl_plugin.so` 实际生成；
- Linux CTest通过；
- Linux Python实际加载 `.so`；
- Linux完整回归通过；
- 状态标记 `LINUX_DOCKER_VERIFIED`。

#### B. 环境阻塞

- Docker问题按有限尝试停止；
- 状态标记 `ENV_BLOCKED`；
- Linux验证脚本完成；
- Linux CI 配置完成；
- 用户待办明确；
- 未伪造 Linux验证结果。

## 12.10 最终提交

若 CI 和文档共同完成：

```text
ci: add Linux CPU_SIM validation
```

最终审计可单独提交：

```text
docs: complete V1 delivery audit
```

完成后停止，不执行 `git push`。

---

# 13. 用户操作与阻塞记录

更新：

```text
docs/user_actions.md
```

## Docker 阻塞项格式

````markdown
## UA-V1-001：启动 Docker Desktop 并执行 Linux CPU_SIM 验证

状态：待用户执行  
优先级：P0/P1  
阻塞阶段：V1-D

### 原因

说明 `docker version` 或 `docker info` 的实际错误。

### 已尝试

1. 正常检查；
2. 一次低风险复查。

### 用户操作

1. 启动 Docker Desktop；
2. 等待 Engine 正常；
3. 在 Windows终端执行：

```cmd
docker version
docker info
```
````

4. 重新运行：

```cmd
docker build ...
docker run ...
```

### 预期输出

- Client 和 Server 均可见；
- 容器 exit code 0；
- `LINUX_CPU_SIM_VALIDATION_OK`。

### 当前状态

`ENV_BLOCKED`，不得宣称 Linux已验证。

````

不得要求用户修复 WSL Codex。

---

# 14. 整体停止条件

出现以下情况时停止当前子阶段：

- 两轮针对性修复仍失败；
- 需要改变公共 ABI 且无法保持兼容；
- Docker daemon 不可用；
- Docker镜像下载持续失败；
- Windows完整回归失败且无法隔离；
- 随机测试暴露内存安全问题；
- 需要管理员权限；
- 需要用户凭据；
- 需要真实 CANN/Ascend 环境。

出现以下情况时停止整个 V1：

- 开始时工作区不干净；
- 当前目录不是目标仓库；
- 存在其他活动 Codex线程同时修改同一仓库；
- 用户文件可能被覆盖；
- 需要破坏性 Git 命令；
- 检测到密钥可能泄露；
- V1 修改导致多个稳定阶段严重回归；
- 无法区分用户修改和 Codex修改。

停止时：

- 不删除；
- 不恢复；
- 不覆盖；
- 不执行 `git reset --hard`；
- 保留现场；
- 报告事实和下一步。

---

# 15. 非目标

V1 不负责：

- 真实 CANN/HCOMM 接入；
- Ascend 实机；
- msprof；
- 实机性能优化；
- 实机 FP16/BF16 误差；
- 实机可靠性；
- Broadcast；
- 外部真实 LLM Agent；
- E2 C 代码生成；
- D2 实机模型校准；
- F2 真实故障注入；
- 新增 Agent Skill；
- 重写模拟器；
- 重构整个 C 插件。

这些任务留给后续：

```text
G2：Real CANN/HCOMM Minimal Integration
E2：Agent-Generated C Collective Candidate
D2/F2：实机性能与可靠性校准
````

---

# 16. 最终报告要求

Goal 完成后必须报告：

1. V1-A—V1-E 状态；
2. 每个阶段 commit；
3. AllReduce 多元素状态；
4. ReduceScatter 2-rank 状态；
5. rank/count/dtype/ReduceOp 覆盖；
6. 随机 seed 和 case 数量；
7. Windows CMake/CTest/Python 结果；
8. Docker状态；
9. Linux CMake/CTest/Python结果；
10. 实际 `.so` 路径；
11. GitHub Actions状态；
12. CANN/HCOMM/Ascend 未验证边界；
13. 用户仍需执行的操作；
14. 最终 `git status --short`；
15. 是否执行过 `git push`。

完成后停止，不自行进入 G2、E2、D2 或 F2。
