# HCCL Agent 自主目标执行计划

版本：v1.0  
适用阶段：Batch C1 完成之后  
执行环境：Windows Native、Conda Python 3.10、Visual Studio 2022、CMake  
项目路径：`F:\projects\hccl-agent`

---

## 1. 总目标

在当前缺少 Ascend 实机、CANN SDK 和真实 HCOMM 运行环境的条件下，将 HCCL Agent 推进为一个最大程度符合赛题要求、具备明确正确性证据、可重复构建测试、可展示 Agent 开发过程的参赛工程。

本计划不以“一次运行完成整个项目”为硬性要求，而以以下结果为目标：

1. 优先完成赛题硬性能力；
2. 尽可能完成能够在 Windows CPU 环境验证的功能；
3. 无法完成的实机能力转化为明确的适配层、测试脚本和用户操作手册；
4. 不因单个环境、依赖或外部服务问题停止所有开发；
5. 不浪费大量额度反复处理同一个问题；
6. 不伪造真实通信、真实性能或实机验证结果；
7. 每个稳定阶段形成独立、本地、可回退的 Git 提交；
8. 最终形成可用于参赛展示、答辩和后续实机迁移的完整工程证据。

本计划不能保证获奖，但所有任务排序均以提高赛题匹配度、工程可信度和答辩展示价值为主要依据。

---

## 2. 当前稳定基线

以下阶段已经完成：

### Batch A1

- Windows 默认 DLL 构建；
- Windows 导入库生成；
- CTest 注册；
- MSVC UTF-8 编译配置；
- 跨平台临时路径；
- generated code 语法修复；
- Windows/Linux 基础构建说明；
- 41 个既有 C 测试用例通过。

### Batch B1

- `hcclAllReduce`、`hcclAllGather`、`hcclReduceScatter`、`hcclBroadcast` 标准 wrapper 符号闭合；
- `hcclAllReduce` 复用 CPU Ring；
- 其他三个尚未实现的 wrapper 返回 `HCCL_ERR_NOT_SUPPORTED`；
- 支持 `library_path > HCCL_PLUGIN_PATH > 默认候选路径`；
- Windows DLL 真实加载；
- 四个 wrapper 导出符号检查通过；
- CTest 7/7 通过；
- 定向 Python 测试 49/49 通过；
- 完整 Python 回归 399/399 通过。

### Batch C1

- Ring AllGather FP32 CPU 数据路径；
- Butterfly AllGather FP32 CPU 数据路径；
- `hcclAllGather` 默认接入 Ring；
- CPU_SIM 数据布局：

```text
send[N][C] -> recv[N][N][C]
```

- 输出按源 rank 顺序拼接；
- CTest 8/8 通过；
- 定向 Python 测试 35/35 通过；
- 完整 Python 回归 415/415 通过。

当前仍未验证：

- Linux `.so`；
- CANN SDK；
- HCOMM；
- Ascend 实机；
- msprof；
- 真实多进程、多设备通信；
- 真实 HCCL 性能。

---

## 3. 需求来源与优先级

自主执行时按以下优先级解释需求：

1. 赛题原始 DOCX；
2. 本文件 `docs/autonomous_goal_plan.md`；
3. `docs/roadmap_v2.md`；
4. `docs/project_audit.md`；
5. 当前已通过测试的代码行为；
6. 其他历史文档。

若不同来源冲突：

- 优先遵守赛题原文；
- 不破坏当前已验证的稳定功能；
- 在 `docs/autonomous_progress.md` 中记录冲突；
- 采用最小、可验证、可回退的处理方式；
- 不因文档冲突无限等待用户确认。

---

## 4. 自主执行顺序

本轮自主执行顺序为：

```text
C2：ReduceScatter CPU 正确性
  ↓
C3-A：FP32 ReduceOp 与统一 reference
  ↓
C3-B：FP16/BF16 CPU 软件模拟
  ↓
E1：Agent 代码生成—编译—测试—修复最小闭环
  ↓
D1：拓扑与成本模型收敛
  ↓
F1：可靠性模拟验证闭环
  ↓
G1：CANN/Ascend 适配准备
  ↓
H1：最终集成、审计和比赛材料收敛
```

调整 E1 到 D1 之前的原因：

- 三种 primitive 完成后，应尽快补足赛题对 Agent 自动开发过程的要求；
- 当前项目已有较多 Agent 模块，但缺少真实的代码生成、编译、测试和修复证据；
- E1 对比赛答辩价值高于继续增加未校准的模拟指标。

除非发生明确依赖阻塞，不得随意改变上述顺序。

---

## 5. 全局执行原则

### 5.1 正确性优先

优先级为：

```text
数据正确性
> 接口闭合
> 可重复测试
> Agent 过程证据
> 模型可信度
> 性能优化
> 展示效果
```

不得为了提高模拟性能数字而牺牲数据正确性或测试覆盖。

### 5.2 不得伪造成功

统一使用以下能力状态：

| 状态              | 含义                                      |
| ----------------- | ----------------------------------------- |
| `IMPLEMENTED`     | 已实现并通过对应环境的真实测试            |
| `CPU_SIMULATED`   | 使用 CPU 单进程或共享内存模拟，结果已验证 |
| `EMULATED`        | 使用软件模拟硬件数据类型或行为            |
| `STUB_UNVERIFIED` | 尚未实现或无法验证，必须返回明确错误      |
| `ENV_BLOCKED`     | 因 SDK、硬件、权限、网络或外部依赖阻塞    |

规则：

- `STUB_UNVERIFIED` 不得返回成功；
- `ENV_BLOCKED` 不得写成已经验证；
- 模拟性能不得冒充 Ascend 实机性能；
- 软件 FP16/BF16 不得冒充硬件混合精度；
- Windows DLL 结果不得写成 Linux `.so` 已验证；
- CPU wrapper 不得写成真实 HCOMM/HCCL 已接入。

### 5.3 有限尝试规则

为控制额度和执行时间：

1. 同一个编译或测试错误最多进行两轮针对性修复；
2. 同一个依赖问题最多尝试一种官方方案和一种低风险替代方案；
3. 同一个外部仓库最多优先阅读 3—5 个高价值文件；
4. 外部代码无法快速、安全集成时，只记录设计思想和来源；
5. 不进行长时间无目标搜索；
6. 不连续重构多个模块来解决一个局部问题；
7. 不为一个非 P0 问题阻塞后续所有可执行任务；
8. 两轮修复仍失败时，将问题记录为阻塞项并采取降级方案。

### 5.4 降级而不中断

遇到无法解决的问题时：

1. 保留错误输出和最小复现命令；
2. 写入 `docs/user_actions.md`；
3. 明确：
   - 阻塞原因；
   - 已尝试方案；
   - 用户需要执行的操作；
   - 需要的文件、SDK、权限或硬件；
   - 验证成功的预期输出；
4. 对受阻功能标记 `ENV_BLOCKED` 或 `STUB_UNVERIFIED`；
5. 继续执行不依赖该功能的后续任务。

不得因以下问题停止全部工作：

- WSL 不可用；
- CANN SDK 不存在；
- Ascend 设备不存在；
- 没有 DeepSeek Key；
- 网络搜索失败；
- 单个可选依赖无法安装；
- 某个非核心优化无法通过。

### 5.5 保护当前稳定基线

每个阶段必须保证：

- 既有 CTest 不回归；
- 既有 Python完整回归不出现 failure 或 error；
- 不破坏 A1 的 Windows构建基线；
- 不破坏 B1 的动态库路径解析；
- 不破坏 C1 的 AllGather 数据正确性；
- 不修改与当前阶段无关的 Agent、Simulator 或通信算法。

---

## 6. Git 自主执行规则

### 6.1 开始条件

开始自主执行前必须运行：

```cmd
git status --short
git log -3 --oneline
```

要求工作区干净。

若工作区不干净：

- 立即停止；
- 不执行 `git reset --hard`；
- 不删除、覆盖或恢复用户文件；
- 只报告当前变更。

### 6.2 阶段提交

每个阶段只有在满足阶段验收闸门后，才允许创建本地提交。

允许：

```text
git add <本阶段明确修改的文件>
git commit
```

禁止：

```text
git add .
git push
git push --force
git reset --hard
git rebase
git clean -fd
```

不得提交：

- DLL、LIB、EXE、OBJ；
- 外部构建目录；
- API Key；
- 用户凭据；
- 下载缓存；
- 大型第三方仓库；
- 临时测试数据；
- 自动生成但未纳入交付要求的日志。

推荐提交信息：

```text
feat: complete C2 ReduceScatter correctness
feat: add C3 numeric correctness baseline
feat: add E1 autonomous code development loop
feat: converge D1 topology and cost models
feat: add F1 reliability validation flow
chore: prepare G1 CANN integration layer
docs: complete autonomous competition readiness audit
```

### 6.3 阶段失败

阶段未通过完整验收时：

- 不创建“完成”提交；
- 不将失败功能标记为完成；
- 可以回退本阶段未提交的局部修改，但不得影响此前提交；
- 记录失败原因；
- 继续执行与失败项无依赖关系的后续阶段。

---

## 7. 网络搜索与成熟项目借鉴

允许搜索 GitHub、官方文档和公开论文，但必须以减少重复造轮子为目的。

### 7.1 搜索优先级

1. Huawei Ascend、CANN、HCCL、HCOMM 官方代码和文档；
2. NVIDIA NCCL、nccl-tests；
3. ASTRA-sim；
4. SimAI；
5. 其他具有明确 License、活跃维护和可验证来源的集合通信项目；
6. 相关论文的官方代码仓库。

### 7.2 搜索预算

每个阶段：

- 最多进行 3 组高价值搜索；
- 最多重点阅读 3—5 个文件；
- 优先查接口、测试、数据布局、模型公式和工程组织；
- 不完整克隆大型仓库；
- 不为非核心细节进行大范围搜索。

### 7.3 借鉴要求

每次有效借鉴写入：

```text
docs/research_notes.md
```

至少记录：

- 项目或论文名称；
- 仓库或官方页面；
- commit、tag 或访问日期；
- 参考文件路径；
- License；
- 借鉴内容；
- 是否直接复制代码；
- 与当前项目的差异；
- 为什么适合或不适合直接集成。

不得：

- 复制来源不明代码；
- 复制许可证不兼容代码；
- 删除原作者版权声明；
- 将大型第三方实现直接塞入本项目；
- 因外部实现结构不同而整体推翻现有稳定架构。

---

# 8. Stage C2：ReduceScatter CPU 数据正确性

优先级：P0

## 8.1 目标

完成第三种核心集合通信原语的 FP32 CPU 数据正确性，使项目具备：

1. AllReduce；
2. AllGather；
3. ReduceScatter。

这三种 primitive 均应具有真实 CPU 数据输出和独立 reference checker。

## 8.2 建议 CPU_SIM 数据契约

设：

```text
N = rank 数
C = 每个目标 rank 最终接收的元素数量
```

建议输入：

```text
send[N][N][C]
```

含义：

```text
send[src_rank][dst_rank][element]
```

建议输出：

```text
recv[N][C]
```

正确性关系：

```text
recv[dst_rank][element]
=
SUM(send[src_rank][dst_rank][element]
    for src_rank in 0..N-1)
```

即：

1. 对所有源 rank 的同一目标分片进行 Reduce；
2. 将第 `dst_rank` 个结果分片交给对应目标 rank。

若当前 B1 ABI 无法安全表达该布局：

- 不得擅自破坏公共 ABI；
- 采用最小兼容调整；
- 在代码和文档中记录 CPU_SIM 语义；
- 不得静默采用其他布局。

## 8.3 最低实现要求

- FP32；
- SUM；
- `count >= 1`；
- 1、4、8、16 rank；
- `count = 1` 和 `count > 1`；
- 每个源 rank、目标 rank和元素使用可区分数据；
- 标准 `hcclReduceScatter` wrapper 接入真实数据实现；
- 至少实现当前 roadmap 指定的 Mesh 路径；
- 若实现第二种算法路径成本较低，可以增加，但不得拖延核心正确性；
- Python reference 必须独立于 C 实现；
- 实际 Windows DLL 集成测试；
- CTest 和完整 Python 回归。

## 8.4 非目标

- FP16/BF16；
- PROD/MAX/MIN；
- 真实多进程；
- 真实设备通信；
- 性能优化；
- CANN/HCOMM。

## 8.5 阶段闸门

必须满足：

- ReduceScatter C 正确性测试通过；
- Python reference 一致；
- AllReduce、AllGather、ReduceScatter 全部通过；
- CTest 全部通过；
- 完整 Python回归为 0 failures、0 errors；
- 实际加载本轮 DLL；
- 不修改 B1 的通用路径解析；
- 不破坏 C1 数据布局。

通过后创建本地提交：

```text
feat: complete C2 ReduceScatter correctness
```

---

# 9. Stage C3-A：FP32 ReduceOp 与统一正确性基准

优先级：P0

## 9.1 目标

先建立 FP32 的完整 reduce operation 正确性基线。

优先支持：

```text
SUM
PROD
MAX
MIN
```

适用范围：

- AllReduce；
- ReduceScatter。

AllGather 不具有 ReduceOp，不得机械地为 AllGather 增加 `op` 参数。

## 9.2 要求

- 每个 ReduceOp 使用独立 Python reference；
- 覆盖正数、负数、零、小数；
- 覆盖容易暴露初始化错误的数据；
- MAX/MIN 不得错误地用零初始化；
- PROD 覆盖零和负数；
- 检查 NaN、Inf 和溢出行为；
- 明确错误码；
- 保持 B1 ABI；
- 保持 C1/C2 数据正确性；
- 生成统一 capability matrix。

建议新增或更新：

```text
docs/correctness_matrix.md
```

记录：

| Primitive | DType | ReduceOp | 状态 | 环境 | 测试证据 |
| --------- | ----- | -------- | ---- | ---- | -------- |

## 9.3 阶段闸门

- FP32 SUM/PROD/MAX/MIN reference 全部通过；
- AllReduce 和 ReduceScatter 覆盖对应 ReduceOp；
- AllGather 回归不受影响；
- CTest 全部通过；
- 完整 Python 回归为 0 failures、0 errors；
- capability matrix 与代码一致。

---

# 10. Stage C3-B：FP16/BF16 CPU 软件模拟

优先级：P0/P1

## 10.1 目标

在无 Ascend 硬件时，建立明确标记的软件精度模拟：

```text
CPU_EMULATED_FP16
CPU_EMULATED_BF16
```

该实现用于：

- 验证数据转换；
- 验证累加策略；
- 建立 reference checker；
- 为后续 Ascend 实机迁移准备测试样例。

## 10.2 实现原则

优先策略：

1. 输入按 FP16/BF16 格式量化；
2. CPU 内部转换为 FP32；
3. 使用 FP32 累加；
4. 根据接口约定转换输出；
5. 与独立 reference 比较。

允许：

- FP16 使用标准半精度转换；
- BF16 使用 `uint16_t` 位表示；
- 软件实现舍入；
- 使用明确的 tolerance。

不得：

- 将 FP16/BF16 软件模拟描述为 Ascend 混合精度；
- 为满足报告数字而伪造误差；
- 对所有 dtype 强制使用同一个误差阈值；
- 将无法达到的精度要求写成已经满足。

## 10.3 数值测试

至少覆盖：

- 正数；
- 负数；
- 零；
- 小数；
- 较大值；
- 较小值；
- NaN；
- 正负 Inf；
- 舍入边界；
- 溢出或下溢场景。

记录：

- 最大绝对误差；
- 最大相对误差；
- 不同 dtype 的 tolerance；
- 不可比较场景；
- 与真实硬件验证的差距。

## 10.4 降级方案

若 FP16/BF16 在两轮实现后仍无法稳定通过：

- 保留 FP32 完整实现；
- 将对应 dtype 标记为 `EMULATED_PARTIAL` 或 `STUB_UNVERIFIED`；
- 不返回伪造成功；
- 在 `docs/user_actions.md` 中记录实机验证需求；
- 继续执行 E1。

## 10.5 C3 总闸门

- FP32 ReduceOp 基线完成；
- FP16/BF16 至少有明确、可测试的软件模拟或明确跳过；
- 正确性矩阵完成；
- CTest 全部通过；
- 完整 Python 回归为 0 failures、0 errors；
- 不破坏三种 primitive 的 FP32 正确性。

C3-A 和 C3-B 均达到相应标准后，创建本地提交：

```text
feat: add C3 numeric correctness baseline
```

若 C3-B 只部分完成，提交信息和文档必须明确使用 `partial` 或 `emulated`，不得写成完整混合精度支持。

---

# 11. Stage E1：Agent 自动代码开发最小闭环

优先级：P1

## 11.1 目标

让 Agent 真实完成一个受控、可复现的小型开发闭环：

```text
读取任务
→ 生成文件
→ 写入隔离工作区
→ 配置/编译
→ 运行测试
→ 读取错误
→ 最多两轮修复
→ 保存过程记录
```

## 11.2 默认模式

默认使用：

```text
OFFLINE_TEMPLATE
```

没有 API Key 时不得阻塞。

可选模式：

```text
EXTERNAL_LLM
```

只有用户明确提供 Key 并人工触发时才允许使用。

自主 Goal 执行期间：

- 不调用真实 DeepSeek；
- 不发送仓库代码到外部服务；
- 不依赖网络 LLM 完成验收。

## 11.3 生成目标

只选择低风险、可验证目标，例如：

- 一个独立 C 测试文件；
- 一个隔离的算法辅助函数；
- 一个 reference checker；
- 一个小型生成示例。

不得让 Agent 自动重写：

- `hcccl/src/hccl_algorithms.c` 主体；
- Git 配置；
- 用户文档；
- CMake 根结构；
- 多个核心模块。

## 11.4 安全要求

- 使用 `tempfile.TemporaryDirectory()`；
- 不使用固定 `/tmp`；
- 不直接写入生产目录；
- 限制可写目录；
- 限制命令白名单；
- 设置执行超时；
- 最多两轮修复；
- 保存 stdout、stderr、exit code；
- 不执行任意 Shell 文本；
- 不执行网络命令；
- 不执行 Git push；
- 不读取 API Key。

## 11.5 过程证据

生成：

```text
docs/agent_development_demo.md
```

记录：

- 输入需求；
- 生成计划；
- 生成文件；
- 第一次编译命令；
- 错误输出；
- 修复理由；
- 第二次结果；
- 测试结果；
- 工作区路径策略；
- 模板模式与真实 LLM 模式的区别。

## 11.6 阶段闸门

- 无 Key 模板模式可运行；
- 从干净临时目录执行；
- 至少完成一次成功编译和测试；
- 至少有一个可控失败—修复演示，或有确定性模拟失败；
- 最多两轮修复；
- 所有过程有日志；
- 完整 Python回归通过；
- 不影响三种 primitive。

通过后创建本地提交：

```text
feat: add E1 autonomous code development loop
```

---

# 12. Stage D1：拓扑与成本模型收敛

优先级：P1

## 12.1 目标

减少平行模型，让拓扑、message size、链路和节点规模真实参与性能估算。

本阶段输出仍是：

```text
CPU_SIMULATED / ANALYTICAL_MODEL
```

不得冒充实机性能。

## 12.2 主要任务

1. 确认唯一主拓扑模型；
2. 处理 `skills/topology_graph.py` 与 `topology/graph_builder.py` 的重复；
3. 让 `Simulator.evaluate()` 主要依赖统一 graph/cost model；
4. 让 message size 明确影响：
   - latency；
   - bandwidth；
   - transfer volume；
   - algorithm steps；
5. 区分：
   - HCCS；
   - PCIe；
   - RoCE；
6. 增加：
   - 8 rank；
   - 64 rank；
   - 128 rank；
   - 256 rank；
   - 1024 rank；
7. 记录参数来源；
8. 输出相对排序和模型假设。

## 12.3 外部借鉴

优先参考：

- HCCL/HCOMM 官方接口和算法结构；
- nccl-tests 的 collective 测试组织；
- ASTRA-sim 的 workload/network/system 分层；
- SimAI 的 analytical communication model。

只借鉴模型结构和验证方法，不整体复制架构。

## 12.4 模型要求

至少采用可解释的近似：

```text
latency
=
startup_cost
+ communication_steps * per_step_latency
+ transferred_bytes / effective_bandwidth
+ contention_penalty
```

每个参数应有：

- 名称；
- 单位；
- 默认值；
- 来源；
- 适用拓扑；
- 是否校准；
- 可信度。

不得继续只使用与 message size 弱相关或无关的固定 score。

## 12.5 阶段闸门

- 唯一主拓扑模型明确；
- message size 改变会导致合理的 latency/bandwidth 变化；
- 链路类型影响结果；
- 节点规模影响结果；
- 8—1024 rank 场景可运行；
- 参数来源写入文档；
- 固定输入输出可复现；
- 现有 correctness 测试全部通过；
- 完整 Python回归通过。

通过后创建本地提交：

```text
feat: converge D1 topology and cost models
```

---

# 13. Stage F1：可靠性模拟验证闭环

优先级：P1

## 13.1 目标

在 CPU/模拟器环境中建立可重复的可靠性验证：

- link down；
- timeout；
- corruption；
- congestion；
- CRC32；
- retry；
- failover；
- 统计报告。

## 13.2 要求

- 固定随机 seed；
- 相同输入得到相同故障序列；
- CRC32 对真实 payload 或明确模拟 payload 计算；
- 记录重试次数；
- 记录成功、失败、丢弃；
- 记录 failover 模拟时间；
- 区分模型时间与真实 wall-clock；
- 输出可靠性报告。

不得写成：

- 真实 100ms 切换已经满足；
- 实机重传率已经达到 0.1%；
- 真实硬件 CRC 已验证。

应写成：

```text
模拟器在给定模型和固定 seed 下的统计结果
```

## 13.3 报告

生成：

```text
docs/reliability_report.md
```

至少包含：

- 模型说明；
- 故障类型；
- seed；
- 测试规模；
- 注入次数；
- 检测次数；
- 重试次数；
- 恢复次数；
- 模拟 failover 时间；
- 失败案例；
- 与赛题真实验收的差距。

## 13.4 阶段闸门

- 固定 seed 可复现；
- CRC/reference 能检测 corruption；
- retry 统计正确；
- failover 路径可测试；
- 报告自动生成；
- 可靠性测试通过；
- correctness 和完整回归不退化。

通过后创建本地提交：

```text
feat: add F1 reliability validation flow
```

---

# 14. Stage G1：CANN/Ascend 适配准备

优先级：P1；获得实机后升级为 P0。

## 14.1 目标

在没有 SDK 和设备时，完成不依赖实机的适配准备：

```text
CPU_SIM
ASCEND_CANN
```

两种模式必须明确隔离。

## 14.2 CMake 要求

建议提供：

```text
-DHCCL_BACKEND=CPU_SIM
-DHCCL_BACKEND=ASCEND_CANN
```

或等价的明确选项。

要求：

- 默认模式为 `CPU_SIM`；
- 无 SDK 时 CPU 模式正常构建；
- 选择 `ASCEND_CANN` 且 SDK 缺失时快速失败；
- 错误信息说明缺少的头文件、库和环境变量；
- 不自动下载 SDK；
- 不假装链接成功；
- 不用 Stub 库冒充 CANN；
- 不覆盖 CPU_SIM 路径。

## 14.3 接口准备

生成或更新：

```text
docs/cann_hccl_interface_guide.md
docs/user_actions.md
```

至少说明：

- 目标 CANN 版本；
- 需要的 SDK 组件；
- 可能的安装目录；
- 环境初始化脚本；
- CMake 参数；
- HCOMM/HCCL 头文件；
- 需要链接的库；
- 单机正确性测试；
- FP16/BF16 测试；
- msprof 命令模板；
- baseline 对比方法；
- 需要用户反馈的输出。

## 14.4 可接受占位

允许创建明确的适配接口和条件编译占位，但必须：

- 标记 `STUB_UNVERIFIED`；
- 在无 SDK 时不参与默认构建；
- 不返回伪造成功；
- 不生成虚假 msprof 结果；
- 不声称真实 HCOMM 已接入。

## 14.5 阶段闸门

- CPU_SIM 完整构建和测试继续通过；
- ASCEND_CANN 选项存在；
- 缺少 SDK 时错误清楚；
- 接口映射表完成；
- 用户操作手册完成；
- 实机测试命令模板完成；
- Linux/CANN/Ascend 状态仍明确标记为未验证。

通过后创建本地提交：

```text
chore: prepare G1 CANN integration layer
```

---

# 15. Stage H1：最终集成、审计和比赛材料收敛

优先级：P0/P1

## 15.1 目标

对自主执行结果进行最终集成，不再新增大功能。

## 15.2 全量验收

执行：

- Windows Release CMake；
- 完整 CTest；
- 定向 correctness suite；
- 完整 Python unittest；
- Agent 自动开发 demo；
- 模拟器场景；
- 可靠性场景；
- CPU_SIM CMake；
- ASCEND_CANN 缺失环境检测；
- Git 修改和构建产物检查。

## 15.3 最终文档

更新或生成：

```text
README.MD
docs/project_documentation.md
docs/project_audit.md
docs/roadmap_v2.md
docs/autonomous_progress.md
docs/correctness_matrix.md
docs/agent_development_demo.md
docs/research_notes.md
docs/reliability_report.md
docs/user_actions.md
docs/competition_readiness_report.md
```

## 15.4 比赛准备度报告

`docs/competition_readiness_report.md` 至少包含：

1. 当前架构；
2. 三种 primitive；
3. dtype/ReduceOp 支持矩阵；
4. CPU_SIM 说明；
5. Agent 开发闭环；
6. 拓扑和成本模型；
7. 可靠性模型；
8. Windows动态验证；
9. Linux/CANN/Ascend 未验证项；
10. 与赛题逐项映射；
11. 可演示内容；
12. 用户后续操作；
13. 风险和剩余 P0；
14. 不得宣称的能力。

## 15.5 最终闸门

- 三种 primitive FP32 正确性通过；
- CTest 全部通过；
- 完整 Python回归无 failure/error；
- Agent 最小闭环可复现；
- 模型参数和来源明确；
- 可靠性模拟可复现；
- CANN适配准备完成；
- 所有模拟和未验证能力标记准确；
- 工作区无构建产物；
- 所有阶段有本地提交或明确未完成记录。

通过后创建本地提交：

```text
docs: complete autonomous competition readiness audit
```

不得执行 `git push`。

---

# 16. 用户操作记录格式

无法自动完成的事项统一写入：

```text
docs/user_actions.md
```

每项按以下格式：

````markdown
## UA-001：操作名称

状态：待用户执行  
阻塞阶段：G1  
优先级：P0/P1/P2

### 原因

说明为什么 Codex 无法完成。

### 用户需要准备

- SDK：
- 硬件：
- 权限：
- 网络：
- 文件：

### 操作步骤

1. ...
2. ...
3. ...

### 执行命令

```bash
...
```
````

### 预期输出

```text
...
```

### 反馈内容

用户需要将以下结果反馈：

- 命令输出；
- 错误日志；
- 版本信息；
- 生成文件；
- 性能数据。

### 当前降级状态

说明当前项目使用的 CPU_SIM、EMULATED 或 STUB 方案。

````

---

# 17. 自主进度记录

创建：

```text
docs/autonomous_progress.md
````

每完成或跳过一个阶段追加：

```markdown
## Stage 名称

开始时间：  
结束时间：  
状态：COMPLETED / PARTIAL / BLOCKED / SKIPPED

### 修改文件

- ...

### 验收结果

- CMake：
- CTest：
- 定向 Python：
- 完整 Python：
- DLL/SO：

### 外部参考

- ...

### 遇到的问题

- ...

### 降级方案

- ...

### 用户待办

- ...

### 本地提交

- commit：
- message：

### 未验证边界

- ...
```

不得删除历史阶段记录。

---

# 18. 停止条件

出现以下情况时停止当前阶段，但不一定停止整个 Goal：

- 两轮针对性修复后仍无法通过；
- 需要用户凭据；
- 需要管理员权限；
- 需要下载受限 SDK；
- 需要真实 Ascend 设备；
- 需要访问不可用的校园内网；
- 修改将破坏已完成 primitive；
- 需要改变公共 ABI 且没有可靠依据；
- 外部 License 不允许使用；
- 完整回归出现无法隔离的失败。

出现以下情况时停止整个 Goal：

- 工作区开始时不干净；
- 发现用户文件可能被覆盖；
- 需要执行破坏性 Git 命令；
- 发现密钥或凭据可能泄露；
- 当前修改无法安全隔离；
- 多个稳定阶段发生严重回归；
- 项目路径或仓库不匹配。

停止后只报告事实，不执行破坏性恢复。

---

# 19. 最终成功标准

本次自主 Goal 达到以下条件时视为成功：

- AllReduce、AllGather、ReduceScatter 具备 FP32 CPU 正确性；
- 三种 primitive 具有 C 和 Python reference 证据；
- FP32 ReduceOp 支持矩阵明确；
- FP16/BF16 有软件模拟或明确未完成说明；
- Windows DLL、CTest 和 Python完整回归持续通过；
- Agent 具备最小生成—编译—测试—修复闭环；
- 模拟器能够反映 message size、链路类型和节点规模；
- 可靠性场景固定 seed 可复现；
- CANN/Ascend 条件编译和用户操作手册完成；
- 外部借鉴和 License 有记录；
- 所有真实、模拟、仿真、占位和阻塞状态区分明确；
- 无法完成的问题有可执行的用户操作步骤；
- 每个稳定阶段有本地 Git 提交；
- 未执行 Git push；
- 没有伪造任何实机、性能或精度结果。

完成本计划后停止，不自行开启新的大型功能方向。
