# G3：赛事交付收口、复现强化与演示准备

## 0. 本计划的结论、范围与阶段基线

### 0.1 阶段结论

G2-F 完成的是：

- direct API 工程就绪；
- 模拟器正确性、性能、规模与可靠性验收；
- Agent backend 接入；
- 三后端隔离；
- 最终 evidence 审计；
- 真实设备验收边界冻结。

G3 不继续扩展 G2-F checkpoint，也不创建 G2-F-8。

G3 的目标是把当前项目从：

```text
功能和证据基本完整的研发仓库
```

推进为：

```text
可提交、可理解、可复现、可审计、可演示的正式竞赛作品
```

G3 统一阶段名称为：

```text
COMPETITION DELIVERY READINESS
```

G3 不等同于：

```text
REAL-DEVICE ACCEPTANCE
```

真实 Ascend NPU direct API 验收仍保持独立，不得通过打包、文档、模拟器或演示材料替代。

### 0.2 计划文件

本计划文件为：

```text
docs/plans/g3-competition-delivery-readiness.md
```

G2-F 原计划：

```text
docs/plans/g2-f-direct-api-real-device-readiness.md
```

在 G3 中作为只读技术基线，不再追加新的研发 checkpoint，也不得为配合 G3 修改其历史结论。

### 0.3 赛题依据

G3 的赛事要求来源以仓库中受控保存的正式赛题文件为准，重点包括：

- 核心目标；
- 通信原语与算法要求；
- 硬件与拓扑适配要求；
- 关键技术要求；
- 开发约束；
- 技术实现路径；
- 参赛作品要求；
- 评判标准；
- 模拟器验证要求；
- Agent 工程与 Prompt 要求；
- 演示材料要求。

赛题材料标有保密或限制扩散标记。

因此 G3 必须区分：

```text
INTERNAL_REFERENCE
SUBMISSION_ARTIFACT
PUBLIC_RELEASE_ARTIFACT
```

赛题原始文件默认属于：

```text
INTERNAL_REFERENCE
```

未经用户明确确认，不得：

- 将赛题原文件复制到最终公开仓库；
- 将赛题原文件放入公开 release；
- 将包含联系方式、密级页眉或内部标识的页面放入演示材料；
- 将赛题文件完整内容复制到公开文档；
- 通过最终压缩包重新分发赛题附件。

允许在项目计划和审计矩阵中：

- 使用简短的要求摘要；
- 记录章节或页码；
- 建立需求 ID；
- 说明项目如何满足或尚未满足要求。

### 0.4 G3 启动前置条件

G3-A 只能在以下条件满足后开始：

- G2-F-7 已通过 PR 合并进入 `main`；
- 本地 `main` 与 `origin/main` 已同步；
- G2-F-7 commit 已成为 `main` 的祖先；
- 工作区除当前 G3 计划文档外无其他修改；
- G2-F-7 最终 evidence SHA256 有效；
- G2-F-7 报告中的状态语义没有被后续修改；
- `AGENTS.md` 已在 `main` 中生效。

本计划编写时已知的 G2-F-7 本地完成 commit 为：

```text
6febd801e356f071eade70f4423410fce1a1614c
```

但 G3-A 不得仅依赖该历史报告。

执行 G3-A 前只允许进行一次轻量确认：

```text
git branch --show-current
git status --short
git merge-base --is-ancestor 6febd801e356f071eade70f4423410fce1a1614c main
```

预期：

```text
main
```

且工作区除本计划文件外无其他修改。

除非实际发现矛盾，不得重新审计全部旧 PR、逐个旧 commit 或重复运行全部历史 benchmark。

### 0.5 G2-F 冻结状态

G3 必须继承以下状态：

```text
G2-F-7: COMPLETED
Agent Backend Integration: COMPLETED
Three-backend Isolation: COMPLETED
Final Audit: COMPLETED
G2-F Readiness: COMPLETED
Competition Simulator Track: COMPLETED
G2-F Real-device Acceptance: HARDWARE_BLOCKED
G2-F Overall: PARTIAL
```

G3 不得把：

```text
G2-F Overall: PARTIAL
```

改写成：

```text
G2-F Overall: COMPLETED
```

除非未来获得真实 Ascend NPU，并完成已冻结的 direct API real-device acceptance。

### 0.6 G3 目标

G3 必须形成以下能力：

1. 赛题要求与项目资产之间的一对一映射；
2. 代码包、文档、Agent、模拟器、evidence 和演示材料的统一清单；
3. 明确的缺口、风险、优先级和后续负责人；
4. 快速复现与完整复现入口；
5. 可独立构建的提交包；
6. 面向评委的算法、正确性、性能、可靠性和 Agent 报告；
7. Prompt、Skills、Agent 生成链和 Git/evidence 的追溯关系；
8. 可信且不越界的图表与演示；
9. 干净环境冷启动验证；
10. 最终 release candidate 和 SHA256；
11. 真实设备缺失及恢复条件说明。

### 0.7 G3 非目标

G3 默认不负责：

- 新增第四种或第五种 collective；
- 从零设计新的通信框架；
- 大规模重写现有 Agent；
- 大规模重写 simulator；
- 重写 CPU_SIM ABI；
- 重写 HCCL-VM runner；
- 改变 direct adapter ABI；
- 修改 G2-E 或 G2-F 历史 evidence；
- 执行真实 ACL/HCCL runtime；
- 创建真实 communicator；
- 执行真实 NPU collective；
- 运行 MPI real-device launcher；
- 运行真实 `msprof`；
- 伪造真实 NPU 性能；
- 为改善展示效果修改原始实验结果；
- 为达到赛题目标而隐藏未达成项；
- 自动上传作品；
- 自动发布公开 release；
- 自动创建 Git tag；
- 自动提交报名系统。

G3-A 审计发现严重功能缺口时，必须先记录缺口，再决定是否增加独立修复 checkpoint。

不得在 G3-A 中未经计划扩展直接修复大型功能缺口。

---

## 1. 统一架构、验证轨道与真实性边界

### 1.1 三种执行后端

项目必须继续保持三种执行后端：

```text
CPU_SIM
ASCEND_HCCL_VM
ASCEND_HCCL_DIRECT
```

其最终语义为：

| 后端                 | 当前用途                                | 可以证明                                 | 不可以证明                       |
| -------------------- | --------------------------------------- | ---------------------------------------- | -------------------------------- |
| `CPU_SIM`            | 项目自有 CPU collective 执行与回归      | 数据布局、项目 ABI、CPU 结果与普通回归   | 官方 HCCL runtime、NPU 性能      |
| `ASCEND_HCCL_VM`     | 官方 `hccl_test` subprocess 验证路径    | G2-E 固定 checker 和 subprocess 合约     | in-process direct API、真实 NPU  |
| `ASCEND_HCCL_DIRECT` | build/link/diagnose/lifecycle readiness | 官方 ABI、链接、符号、guard 与控制面就绪 | 当前不能证明真实 collective 成功 |

默认 backend 必须继续为：

```text
CPU_SIM
```

所有 backend 的 fallback policy 必须继续为：

```text
NONE
```

### 1.2 模拟器验收轨道

```text
SIMULATOR_ACCEPTANCE
```

是验证轨道，不是第四个执行 backend。

它可以证明：

- 三原语模拟正确性；
- 独立 host reference；
- dtype/op/rank/message 覆盖；
- topology 模型；
- algorithm comparison；
- simulated p50/p95；
- simulated scale；
- simulated fault/recovery；
- logical 1 GB；
- logical 72h；
- simulator profiling；
- parameter provenance；
- sensitivity analysis。

它不可以证明：

- 真实 NPU 性能；
- 真实 HCCS/RoCE/PCIe 带宽；
- 真实 8→1024 卡扩展；
- 真实 90% 加速效率；
- 真实 100 ms 故障切换；
- 真实重传率；
- 真实 72 小时压测；
- 真实 BERT/LLaMA 训练吞吐；
- 真实 `msprof`；
- 真实零 CPU 介入；
- 真实 UB/HBM 行为。

### 1.3 结果标签

G3 中任何指标、表格、图表、报告和演示都必须携带来源标签。

允许的标签至少包括：

```text
CPU_EXECUTED
HCCL_VM_EXECUTED
SIMULATED_ONLY
DIRECT_READINESS_ONLY
REAL_DEVICE_NOT_EXECUTED
```

未来真实设备结果才允许：

```text
REAL_DEVICE_MEASURED
```

当前 G3 不得生成：

```text
REAL_DEVICE_MEASURED
REAL_DEVICE_PASS
direct_hccl_api_call=true
real_ascend_npu_validated=true
measured_on_real_npu=true
performance_claim_type=REAL_MEASURED
```

### 1.4 数值和结论边界

G3 不得为了宣传目的修改或重新解释 G2-F 的原始结果。

尤其是模拟规模结果只能描述为：

```text
在指定 simulator model、topology、parameter set 和 workload 假设下的预测结果
```

不得仅凭 logical 1024 ranks 覆盖宣称：

```text
真实支持 1024 卡
```

不得仅凭 logical 72h 声称：

```text
完成真实 72 小时稳定性压测
```

不得仅凭 simulated failover time 声称：

```text
真实集群 100 ms 内完成故障切换
```

不得仅凭通信 trace 声称：

```text
完成真实 BERT/LLaMA 训练
```

### 1.5 证据等级

每项赛事要求必须使用以下证据等级之一：

```text
E0_NONE
E1_DOCUMENTED
E2_STATIC_VERIFIED
E3_HOST_EXECUTED
E4_OFFICIAL_VM_EXECUTED
E5_SIMULATOR_VALIDATED
E6_REAL_DEVICE_MEASURED
```

含义：

| 等级                      | 含义                                            |
| ------------------------- | ----------------------------------------------- |
| `E0_NONE`                 | 没有可用实现或证据                              |
| `E1_DOCUMENTED`           | 只有设计、计划或说明                            |
| `E2_STATIC_VERIFIED`      | 已完成源码、ABI、build、link、symbol 或静态审计 |
| `E3_HOST_EXECUTED`        | 已在 CPU/host 环境执行并通过                    |
| `E4_OFFICIAL_VM_EXECUTED` | 已通过官方 HCCL-VM 固定合约执行                 |
| `E5_SIMULATOR_VALIDATED`  | 已通过项目 simulator 验收                       |
| `E6_REAL_DEVICE_MEASURED` | 已在真实 Ascend NPU 执行并有完整证据            |

当前不得将任何项目要求标为 `E6_REAL_DEVICE_MEASURED`。

### 1.6 真实性冲突处理

同一能力存在多个证据等级时：

- 必须分别列出；
- 不得只保留最高看起来最有利的结果；
- 不得把不同轨道数据合并成一个性能值；
- 不得让低等级证据继承高等级名称；
- 最终结论采用最保守且可证明的表述。

例如：

```text
Direct adapter build/link: E2_STATIC_VERIFIED
Lifecycle state machine: E3_HOST_EXECUTED
Collective correctness: E5_SIMULATOR_VALIDATED
Real NPU collective: E0_NONE / HARDWARE_BLOCKED
```

---

## 2. G3 统一状态语义

### 2.1 Checkpoint 状态

G3 checkpoint 只允许使用：

```text
NOT_STARTED
IN_PROGRESS
COMPLETED
PARTIAL
ENV_BLOCKED
HARDWARE_BLOCKED
USER_ACTION_REQUIRED
FAIL
```

### 2.2 赛事要求状态

每项赛题要求只允许使用：

```text
SATISFIED
PARTIALLY_SATISFIED
MISSING
UNVERIFIED
HARDWARE_BLOCKED
NOT_APPLICABLE
```

含义：

| 状态                  | 含义                                           |
| --------------------- | ---------------------------------------------- |
| `SATISFIED`           | 有明确实现、测试和可追溯证据                   |
| `PARTIALLY_SATISFIED` | 已覆盖一部分，但范围、证据或交付形式不完整     |
| `MISSING`             | 仓库中没有对应实现或交付件                     |
| `UNVERIFIED`          | 可能存在，但当前无法确认可构建、可运行或可追溯 |
| `HARDWARE_BLOCKED`    | 仅因真实设备或受控硬件环境缺失无法完成         |
| `NOT_APPLICABLE`      | 经赛题文本和项目范围确认确实不适用             |

不得将以下问题标为 `HARDWARE_BLOCKED`：

- 文档缺失；
- 脚本缺失；
- `.so` 不可复现；
- Prompt 记录缺失；
- 测试缺失；
- 报告缺失；
- 路径失效；
- evidence SHA256 失败；
- 代码包不可构建；
- Agent 工程不可独立运行；
- 模拟器配置不完整；
- 演示材料缺失。

### 2.3 风险等级

每个缺口必须使用：

```text
BLOCKER
HIGH
MEDIUM
LOW
INFO
```

定义：

| 风险      | 含义                                                               |
| --------- | ------------------------------------------------------------------ |
| `BLOCKER` | 不处理会导致作品无法提交、无法构建、严重违反赛题约束或产生虚假声明 |
| `HIGH`    | 会显著影响正确性、工程化、复现、性能或 Agent 评分                  |
| `MEDIUM`  | 不阻塞提交，但会降低完整性、清晰度或展示质量                       |
| `LOW`     | 体验、格式、可读性或次要增强                                       |
| `INFO`    | 已满足，或仅用于记录事实和限制                                     |

### 2.4 解决归属

每个缺口必须指定后续归属：

```text
G3-B
G3-C
G3-D
G3-E
G3-F
G3-G
REAL_DEVICE_FUTURE
USER_ACTION
NO_ACTION
```

不得只写“后续处理”而不指定 checkpoint。

---

## 3. G3 统一 Git 与执行规则

### 3.1 Checkpoint 流程

G3 继续采用：

```text
一个 checkpoint
→ 一个功能分支
→ 一个本地 commit
→ 人工审计
→ push
→ PR
→ merge
→ 同步 main
→ 下一 checkpoint
```

不得使用一个分支完成 G3-A 至 G3-G。

不得创建一个包含全部 G3 工作的超大 commit。

### 3.2 分支命名

建议：

```text
codex/g3-a-delivery-gap-audit
codex/g3-b-reproducible-submission
codex/g3-c-technical-reports
codex/g3-d-agent-prompt-delivery
codex/g3-e-visualization-innovation
codex/g3-f-demo-video-preparation
codex/g3-g-release-candidate
```

### 3.3 允许的 Git 操作

在用户明确授权的 checkpoint 中允许：

```text
git branch --show-current
git status --short
git diff
git diff --check
git add
git commit
git show
```

用户另行授权后才允许：

```text
git push
PR merge
tag
release
```

不得自动执行：

```text
git reset --hard
git clean -fd
git rebase
git commit --amend
git push --force
git filter-branch
git filter-repo
```

### 3.4 历史与 evidence 保护

不得修改：

- G2-D evidence；
- G2-E evidence；
- G2-F-1 至 G2-F-7 evidence；
- 已发布或已合并的历史 commit；
- 历史 benchmark raw records；
- 历史 SHA256SUMS；
- 旧测试结果以使其看起来更好。

G3 可以：

- 读取旧 evidence；
- 验证旧 SHA256；
- 建立 inventory；
- 生成汇总；
- 生成图表；
- 记录已知错误或局限；
- 引用历史 commit。

G3 不得覆盖旧 evidence。

---

## 4. G3 统一环境与官方目录保护

### 4.1 项目路径

Windows 项目路径：

```text
F:\projects\hccl-agent
```

WSL 项目路径：

```text
/mnt/f/projects/hccl-agent
```

### 4.2 官方环境

冻结环境：

```text
CANN=/home/workspace/Ascend/cann-9.1.0
HCOMM=/home/workspace/hcomm
HCCL=/home/workspace/hccl
```

冻结官方版本：

```text
HCOMM competition/campus-2026
c8a3dc68a37315aa1e908a971fa706abe612f6ee

HCCL competition/campus-2026
2c87cc1937bab23b8574ef24017c03572d3340e2
```

### 4.3 官方仓库保护

官方仓库只允许只读检查：

```text
git -c safe.directory=/home/workspace/hcomm -C /home/workspace/hcomm ...
git -c safe.directory=/home/workspace/hccl -C /home/workspace/hccl ...
```

不得：

- checkout；
- reset；
- commit；
- clean；
- rebuild；
- 修改 remote；
- 写入源码；
- 写入 evidence；
- 设置全局 `safe.directory=*`。

HCOMM/HCCL branch、commit 和 tracked worktree clean 只需在每个 checkpoint 最终审计时检查一次。

### 4.4 依赖规则

G3 默认不得：

- 安装新系统包；
- 使用 `sudo`；
- 升级 Python；
- 升级 CMake；
- 升级编译器；
- 升级 CANN；
- 下载新 SDK；
- 修改驱动或固件。

确需新增工具时必须：

1. 先记录缺口；
2. 优先使用标准库或仓库现有依赖；
3. 说明许可证；
4. 说明可选性；
5. 获得用户明确授权。

---

## 5. G3 统一交付物分类

所有最终资产必须属于以下分类之一：

```text
SOURCE_CODE
NATIVE_PLUGIN
BUILD_CONFIGURATION
TEST_TOOL
BENCHMARK_TOOL
FAULT_INJECTION_TOOL
AGENT_ENGINEERING
PROMPT_AND_SKILLS
SIMULATOR
CONFIGURATION
EVIDENCE
TECHNICAL_REPORT
DEMO_MATERIAL
RELEASE_METADATA
INTERNAL_REFERENCE
```

每个交付物必须记录：

- artifact id；
- category；
- repository path；
- required by competition；
- generated by Agent；
- build status；
- run status；
- evidence status；
- license；
- confidentiality；
- submission inclusion；
- public release inclusion；
- known limitations；
- owning G3 checkpoint。

---

## 6. G3 统一安全、隐私与发布规则

最终提交包和公开 release 不得包含：

- API key；
- access token；
- Cookie；
- SSH private key；
- `.env` 私密内容；
- 用户账号；
- 个人电话号码；
- 个人地址；
- IDE 认证缓存；
- Codex 登录信息；
- 校园 token；
- 代理凭据；
- 未授权官方二进制；
- 未授权赛题原文件；
- Windows 用户绝对路径；
- WSL 用户 home 绝对路径；
- 临时构建缓存；
- 大量无用途中间日志；
- `.git`；
- `.venv`；
- `__pycache__`；
- crash dump；
- core dump。

内部 evidence 中确需保存环境路径时，最终公开报告应进行最小化或规范化处理，不得影响证据可追溯性。

不得删除有意义的限制说明来改善展示效果。

---

## 7. G3 统一 evidence 规则

### 7.1 新 evidence 与旧 evidence

G3 evidence 必须与 G2 evidence 分开。

建议路径：

```text
experiments/submission/evidence/
```

每个 checkpoint 使用：

```text
experiments/submission/evidence/g3_<checkpoint>_<timestamp>/
```

例如：

```text
experiments/submission/evidence/g3_a_<timestamp>/
```

### 7.2 Evidence 最低字段

每个 G3 evidence 至少记录：

```text
checkpoint
checkpoint_status
project_commit
baseline_commit
source_documents
generated_artifacts
tests
warnings
known_limitations
old_evidence_modified=false
real_device_api_executed=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
SHA256SUMS
```

### 7.3 可复现性

每个自动生成文档、矩阵、图表、manifest 或压缩包必须满足：

- 输入路径明确；
- 生成脚本可定位；
- 命令可复现；
- 输出可验证；
- 数字可追溯到 evidence；
- 不依赖未记录的人工修改；
- 不依赖当前开发机的隐藏状态。

### 7.4 失败处理

Evidence 生成失败时：

- 保留原始错误；
- 不提交半成品权威 evidence；
- 不生成虚假的 `COMPLETED`；
- 可将调试输出留在临时目录；
- 最终只保留一份权威 evidence。

---

## 8. G3 Checkpoint 总览

| Checkpoint | 名称                                    | 主要输出                                                     | 初始状态      |
| ---------- | --------------------------------------- | ------------------------------------------------------------ | ------------- |
| G3-A       | 赛事要求与交付差距审计                  | requirement matrix、inventory、risk register、claim boundary | `NOT_STARTED` |
| G3-B       | 一键复现与交付包构建                    | quick/full reproduce、package、release manifest              | `NOT_STARTED` |
| G3-C       | 技术文档与正式报告体系                  | 算法、正确性、性能、可靠性、模拟器、direct appendix          | `NOT_STARTED` |
| G3-D       | Agent Skills、Prompt 与生成过程专项交付 | Skills、Prompt、generation trace、Agent manual               | `NOT_STARTED` |
| G3-E       | 图表、算法创新主线与结果解释            | figures、tables、innovation narrative                        | `NOT_STARTED` |
| G3-F       | 演示程序、分镜与视频准备                | demo mode、script、storyboard、voice-over                    | `NOT_STARTED` |
| G3-G       | 冷启动复现、合规审计与发布候选          | clean-room audit、submission archive、release candidate      | `NOT_STARTED` |

G3-A 完成前，G3-B 至 G3-G 的具体范围仅为初步方向。

G3-A 可以调整后续 checkpoint 的优先级和任务拆分，但不得取消赛题明确要求的交付物。

---

# 9. G3-A：赛事要求与交付差距审计

## 9.1 目标

G3-A 必须对以下内容进行一次完整但只读优先的审计：

```text
赛题要求
→ 仓库实现
→ 测试
→ evidence
→ 文档
→ 交付形式
→ 当前状态
→ 证据等级
→ 缺口
→ 风险
→ 后续 checkpoint
```

G3-A 的核心输出不是新功能，而是：

```text
一份事实准确、可机器解析、可人工审阅的赛事交付差距基线
```

完成后必须能回答：

1. 赛题明确要求提交什么；
2. 仓库目前实际拥有什么；
3. 哪些已满足；
4. 哪些只完成了研发验证但尚未形成交付件；
5. 哪些是模拟器证明；
6. 哪些只是静态 readiness；
7. 哪些真实设备要求仍被阻塞；
8. 哪些材料缺失；
9. 哪些存在严重合规风险；
10. 后续 G3-B 至 G3-G 应按什么顺序处理。

## 9.2 G3-A 非目标

G3-A 不负责：

- 实现大型新功能；
- 重写 C/C++ 算法；
- 增加 collective；
- 完成最终打包；
- 编写全部正式报告；
- 生成最终视频；
- 生成最终图表；
- 修改历史 evidence；
- 执行完整 G2-F-5/F6 benchmark；
- 运行真实设备 API；
- 自动发布；
- 自动上传；
- 将所有发现的缺口立即修复。

允许进行的修复仅限于审计本身需要的轻量问题，例如：

- 审计脚本解析错误；
- 新增审计 schema；
- 新增只读 inventory 工具；
- 修复本 checkpoint 新增文档中的链接；
- 修复审计输出自身不一致。

发现业务缺口时必须记录，不得借 G3-A 擅自扩大范围。

## 9.3 前置条件

开始前确认：

```text
current branch=main
G2-F-7 commit is ancestor of main
workspace clean except G3 plan
```

然后创建：

```text
codex/g3-a-delivery-gap-audit
```

允许将本 G3 计划文档纳入 G3-A commit。

## 9.4 审计来源优先级

来源优先级由高到低为：

1. 正式赛题文件；
2. G2-F-7 final evidence；
3. G2-F-1 至 G2-F-6 final evidence；
4. G2-E final evidence；
5. 当前 `main` 源码与构建配置；
6. 当前自动化测试；
7. 当前项目正式文档；
8. Git commit 和 Agent/Codex 日志；
9. 历史路线图或旧状态文档；
10. 用户人工说明。

当来源冲突时：

- 不得静默选择更有利的版本；
- 必须记录冲突；
- 以当前可执行代码和可验证 evidence 为事实基准；
- 将旧文档标记为 stale 或 conflicting；
- 不修改旧 evidence。

用户人工报告可用于定位信息，但不能独立替代仓库和 evidence 验证。

## 9.5 赛题要求清单

G3-A 至少审计以下赛题要求类别。

### A. 通信原语

至少核查：

```text
AllReduce
AllGather
ReduceScatter
```

并记录：

- Python simulator 实现；
- CPU_SIM C/C++ 实现；
- direct adapter readiness；
- HCCL-VM 支持范围；
- dtype；
- op；
- rank；
- message size；
- tests；
- evidence；
- 最终提交接口。

Broadcast 和 AlltoAll 不作为当前项目承诺的必选范围，但必须根据赛题“至少三种”的措辞记录为：

```text
NOT_SELECTED_OPTIONAL_PRIMITIVE
```

不得写成项目缺陷，除非最终参赛规则明确要求全部五种。

### B. 硬件与拓扑

至少核查：

- Full Mesh；
- Ring；
- hierarchical / Fat-Tree；
- heterogeneous topology；
- asymmetric links；
- HCCS；
- RoCE；
- PCIe；
- small message ≤64 KB；
- large message ≥1 GB；
- dynamic topology；
- node/rank change；
- NUMA/HBM/UB 表达；
- topology source；
- simulator assumptions；
- real-hardware detection status。

必须区分：

```text
SIMULATOR_CONFIGURED
STATIC_READINESS
REAL_HARDWARE_DETECTED
```

当前不得出现：

```text
REAL_HARDWARE_DETECTED
```

### C. 算法创新

至少核查：

- Ring；
- NHR；
- Mesh；
- Butterfly；
- PairWise，如项目中存在；
- hierarchical/Fat-Tree；
- dynamic routing；
- chunking；
- adaptive algorithm selection；
- sparse communication，如项目中存在；
- quantization/compression，如项目中存在；
- reflection/replanning；
- algorithm generation trace；
- 与固定 baseline 的比较；
- 是否有可清晰表述的主创新闭环。

对只存在名称但没有可执行调度、模型、测试或 evidence 的算法，不得标记为 `SATISFIED`。

### D. 软硬协同

至少核查：

- CANN/HCOMM API 合约；
- C/C++ direct adapter；
- official library link；
- device/context/stream/communicator 生命周期；
- device buffer 契约；
- HCCS/RoCE/PCIe profile；
- computation/communication overlap；
- in-network reduction；
- UB/HBM reuse；
- zero CPU intervention；
- direct runtime execution。

必须分别标记：

```text
DESIGNED
STATIC_VERIFIED
HOST_HARNESS_VERIFIED
SIMULATED
REAL_DEVICE_VERIFIED
```

当前不得将以下内容标记为真实验证：

- 随路归约；
- 零 CPU 介入；
- UB 复用；
- HBM 行为；
- 计算通信重叠；
- 实际设备利用率。

### E. 可靠性

至少核查：

- health monitoring；
- link degradation；
- link down；
- timeout；
- retry；
- checksum/CRC；
- route failover；
- no-alternate-path failure；
- node/rank removal；
- node/rank recovery；
- simulated 100 ms threshold；
- simulated retry rate；
- logical 72h；
- correctness after recovery；
- real-device reliability status。

模拟结果必须继续使用：

```text
SIMULATED_ONLY
```

### F. 可扩展性

至少核查：

```text
8
16
32
64
128
256
512
1024 ranks
```

并记录：

- analytical complexity；
- simulator scale；
- memory boundedness；
- simulated latency；
- simulated bandwidth；
- bottleneck；
- claimed speedup；
- claimed efficiency；
- real-device status。

如果没有完整 compute workload model，不得将 communication scaling 解释为训练线性加速比。

### G. 精度与正确性

至少核查：

- FP16；
- BF16；
- FP32；
- INT32；
- SUM；
- MAX；
- MIN；
- independent host reference；
- exact-representable dataset；
- random stress dataset；
- absolute/relative error；
- NaN/Inf；
- output hash；
- rank ordering；
- logical large-message correctness；
- CPU_SIM cross-validation。

必须明确：

- 哪些数据满足零误差；
- 哪些采用 dtype-aware tolerance；
- 是否真正满足赛题 `≤1e-6`；
- 不能用宽松 stress threshold 替代严格精度结论。

### H. C/C++ 和插件合规

这是 G3-A 的最高优先级专项审计。

至少回答：

1. 项目最终准备提交的 `.so` 是哪个；
2. `.so` 是否由仓库当前源码可重复构建；
3. `.so` 是否只依赖允许的库；
4. 是否有匹配的公开头文件；
5. 是否有 CMake 构建入口；
6. 导出符号是什么；
7. 三原语的核心逻辑位于哪里；
8. Python 是否只是控制面、Agent 和 simulator；
9. C/C++ 是否承担赛题要求的算法插件角色；
10. 当前 `.so` 是 CPU_SIM、direct adapter，还是两者之一；
11. 是否存在将 CPU_SIM `.so` 误标为官方 HCCL direct plugin 的风险；
12. direct linked artifact 是否适合放入最终交付包；
13. CANN 官方库是否允许随包分发；
14. 无 NPU 环境中评委能否构建并理解插件；
15. 赛题文档中的接口名称与当前项目 ABI 是否一致；
16. 需要在 G3-B 前补什么兼容说明或包装层。

任何结论必须引用：

- 源文件；
- CMake target；
- binary hash；
- exported symbol；
- test；
- evidence。

不得仅根据文件名或 target 名判断合规。

### I. Agent 技术要求

至少核查：

- Agent 独立工程入口；
- environment setup；
- dependencies；
- Skills 清单；
- planning；
- topology；
- algorithm generation；
- selection；
- execution；
- evaluation；
- reflection；
- replanning；
- reliability；
- reporting；
- backend selection；
- evidence audit；
- Prompt 文件；
- Prompt version；
- Prompt input/output schema；
- Agent run log；
- generated code trace；
- commit mapping；
- reproducibility；
- human intervention disclosure；
- unavailable historical prompts。

不得事后伪造不存在的原始 Prompt。

缺失内容必须标记：

```text
HISTORICAL_RECORD_UNAVAILABLE
```

或：

```text
MISSING
```

### J. 模拟器交付

至少核查：

- simulator source；
- standalone entry；
- topology configuration；
- hardware parameter configuration；
- parameter provenance；
- validation flow；
- correctness flow；
- performance model；
- scale flow；
- fault injection；
- logical 1 GB；
- logical 72h；
- workload trace；
- profiling trace；
- seeds；
- deterministic replay；
- raw logs；
- summaries；
- SHA256；
- limitations；
- real-device calibration status。

必须确认评委是否能够：

```text
读取配置
→ 运行代表用例
→ 得到结果
→ 验证日志
→ 对照 evidence
```

### K. 测试与工具

至少核查：

- CTest；
- Python test suite；
- primitive tests；
- dtype tests；
- 8-rank scenario；
- 64-rank scenario；
- logical 1024-rank scenario；
- benchmark runner；
- stress tool；
- fault injection tool；
- evidence verifier；
- Windows/WSL import；
- direct build/link audit；
- no-device diagnose；
- lifecycle harness；
- quick test；
- full test；
- clean-environment test。

必须区分：

```text
真实 8/64 设备测试
```

与：

```text
模拟 8/64 ranks 测试
```

### L. 技术文档

至少核查是否已有或需要新增：

- 顶层 README；
- quick start；
- environment guide；
- architecture overview；
- algorithm design report；
- topology report；
- correctness report；
- performance report；
- scale report；
- reliability report；
- simulator manual；
- direct readiness appendix；
- Agent architecture；
- Skills；
- Prompt engineering；
- generation trace；
- known limitations；
- real-device resume guide；
- submission inventory；
- license notice；
- reproduction guide。

旧文档存在但内容过时，应标记：

```text
STALE
```

而不是当作已满足。

### M. 参赛代码包

至少核查：

- `.so`；
- headers；
- CMake；
- source；
- Agent source；
- Prompt；
- simulator；
- configurations；
- tests；
- benchmark；
- fault injection；
- logs；
- reports；
- evidence；
- demo；
- manifest；
- SHA256；
- license；
- excluded files；
- archive size；
- forbidden data；
- clean extraction；
- buildability。

G3-A 不生成最终压缩包，但必须确认当前仓库距离可打包状态的缺口。

### N. 性能与可靠性报告

至少核查当前 evidence 是否足够支撑：

- latency；
- bandwidth；
- p50/p95；
- algorithm comparison；
- baseline；
- scale；
- sensitivity；
- bottleneck；
- profiling；
- fault detection；
- failover；
- retry；
- logical 72h；
- workload trace；
- limitations。

如没有真实数据，报告计划必须明确标记：

```text
SIMULATOR PERFORMANCE REPORT
```

### O. 演示材料

至少核查：

- 5 分钟演示视频是否存在；
- demo script；
- demo CLI；
- deterministic demo config；
- fallback recording；
- storyboard；
- narration；
- captions；
- architecture diagram；
- algorithm animation；
- simulator operation；
- Agent generation process；
- performance chart；
- reliability demo；
- claim boundary slide；
- final status slide。

缺失视频不得标记为 `HARDWARE_BLOCKED`。

### P. 合规、许可证与保密

至少核查：

- 项目许可证；
- 第三方依赖；
- copied code；
- official source usage；
- official binary redistribution；
- HCOMM/HCCL reference；
- CANN redistributability；
- confidential competition file；
- secrets；
- personal paths；
- credentials；
- generated code provenance；
- Agent logs 中的私密信息；
- public/private submission boundary。

G3-A 不负责最终法律结论，但必须列出：

```text
LICENSE_REVIEW_REQUIRED
REDISTRIBUTION_REVIEW_REQUIRED
CONFIDENTIALITY_REVIEW_REQUIRED
```

等人工确认项。

## 9.6 审计方法

G3-A 应采用以下顺序。

### 第一步：赛题 requirement inventory

从正式赛题文件建立规范化 requirement ID，例如：

```text
REQ-PRIM-001
REQ-TOPO-001
REQ-INNOV-001
REQ-CPP-001
REQ-AGENT-001
REQ-SIM-001
REQ-PACKAGE-001
REQ-DOC-001
REQ-DEMO-001
```

每条 requirement 至少包含：

```text
requirement_id
source_document
source_section
source_page
requirement_summary
requirement_level
deliverable_category
acceptance_expectation
hardware_dependency
confidentiality
```

`requirement_summary` 使用项目自己的简要概括，不长篇复制赛题原文。

### 第二步：仓库 artifact inventory

扫描并分类：

- project-owned source；
- official reference；
- generated artifacts；
- build outputs；
- tests；
- evidence；
- docs；
- prompts；
- logs；
- configs；
- third-party files；
- obsolete files；
- untracked or ignored deliverables。

必须记录 project-owned 与 official/third-party 边界。

### 第三步：要求—资产映射

每个 requirement 必须关联：

```text
implementation_paths
test_paths
evidence_paths
documentation_paths
agent_trace_paths
```

不存在时使用空数组，不得用推测路径补齐。

### 第四步：可构建和可运行性判定

G3-A 以轻量验证为主。

允许：

- import checks；
- schema checks；
- manifest checks；
- `git ls-files`；
- CMake target inventory；
- test inventory；
- ELF metadata inventory；
- SHA256 verification；
- quick static validation；
- existing final evidence parsing。

默认不运行：

- G2-F-5 完整矩阵；
- G2-F-6 完整矩阵；
- logical 72h；
- large benchmark；
- HCCL-VM actual suite；
- real-device API；
- `msprof`；
- MPI。

如果某资产只有执行后才能判断，应标记 `UNVERIFIED`，并分配到 G3-B 或 G3-G。

### 第五步：状态和证据等级

为每条 requirement 设置：

```text
status
evidence_level
confidence
```

`confidence` 只允许：

```text
HIGH
MEDIUM
LOW
```

### 第六步：缺口和风险

每条非 `SATISFIED` requirement 必须记录：

```text
gap_summary
risk_level
impact
recommended_action
owner_checkpoint
user_action_required
hardware_blocked
```

### 第七步：交付优先级

按以下顺序排列后续工作：

1. 真实性或合规 `BLOCKER`；
2. `.so` / C/C++ / build / package `BLOCKER`；
3. 一键复现 `HIGH`；
4. 正确性和证据完整性 `HIGH`；
5. Agent/Prompt 可追溯性 `HIGH`；
6. 技术报告 `HIGH`；
7. 性能和创新叙事 `HIGH`；
8. 图表与演示 `MEDIUM`；
9. 发布体验 `MEDIUM/LOW`。

## 9.7 允许修改的范围

允许新增或修改：

```text
docs/plans/g3-competition-delivery-readiness.md
docs/submission/
tools/submission_audit/
scripts/submission_audit/
tests/submission_audit/
experiments/submission/evidence/g3_a_<timestamp>/
```

具体路径可以按仓库现有结构调整。

允许对现有文档做极小范围链接修复，但不得在 G3-A 中大规模重写正式报告。

不得修改：

- collective 实现；
- algorithm implementation；
- simulator model；
- performance formula；
- CPU_SIM ABI；
- direct ABI；
- G2-E runner；
- G2-F evidence；
- HCOMM/HCCL/CANN。

## 9.8 G3-A 文档输出

至少生成：

```text
docs/submission/competition_requirement_matrix.md
docs/submission/deliverable_inventory.md
docs/submission/claim_boundary_matrix.md
docs/submission/g3_a_gap_report.md
docs/submission/g3_priority_roadmap.md
```

### competition_requirement_matrix.md

至少包含：

- requirement ID；
- requirement summary；
- mandatory/recommended；
- implementation；
- test；
- evidence；
- status；
- evidence level；
- risk；
- owner checkpoint。

### deliverable_inventory.md

至少包含：

- artifact；
- category；
- current path；
- expected submission path；
- build/run status；
- inclusion decision；
- license/confidentiality；
- missing dependencies；
- owner checkpoint。

### claim_boundary_matrix.md

至少包含：

- claim；
- allowed wording；
- prohibited wording；
- source backend/track；
- evidence level；
- report location；
- demo usage；
- known limitations。

重点包含：

```text
1024 ranks
1 GB
72h
100 ms
retry rate
BERT/LLaMA
HCCS/RoCE/PCIe
direct API
NPU performance
msprof
zero CPU intervention
```

### g3_a_gap_report.md

至少包含：

- executive summary；
- satisfied requirements；
- partial requirements；
- blockers；
- high risks；
- medium/low gaps；
- C/C++ plugin compliance findings；
- Agent/Prompt trace findings；
- simulator deliverability findings；
- performance claim findings；
- confidentiality/license findings；
- recommended G3-B to G3-G order。

### g3_priority_roadmap.md

必须将每个 gap 映射到：

```text
G3-B
G3-C
G3-D
G3-E
G3-F
G3-G
REAL_DEVICE_FUTURE
USER_ACTION
```

不得在没有依据的情况下给出固定日期或工期承诺。

## 9.9 机器可读输出

至少生成：

```text
requirement_matrix.json
deliverable_inventory.json
claim_boundary_matrix.json
risk_register.json
source_inventory.json
roadmap_assignment.json
```

每个 JSON 必须：

- schema 明确；
- UTF-8；
- key 稳定；
- path 使用仓库相对路径；
- 不包含用户本机秘密；
- 与 Markdown 汇总一致；
- 可通过测试解析。

## 9.10 关键专项审计结论

G3-A 最终必须明确给出以下结论，不得使用模糊语言。

### 1. C/C++ 插件合规状态

必须为以下之一：

```text
SATISFIED
PARTIALLY_SATISFIED
MISSING
UNVERIFIED
```

并解释：

- 最终 `.so`；
- CMake；
- headers；
- exported symbols；
- core logic location；
- Agent generation trace；
- simulator/direct distinction；
- next action。

### 2. Agent 全流程可复现状态

必须为以下之一：

```text
SATISFIED
PARTIALLY_SATISFIED
MISSING
UNVERIFIED
```

并解释：

- Skills；
- Prompt；
- run logs；
- generation trace；
- commit mapping；
- missing historical records；
- independent execution entry。

### 3. 模拟器交付状态

必须为以下之一：

```text
SATISFIED
PARTIALLY_SATISFIED
MISSING
UNVERIFIED
```

并解释：

- config；
- parameters；
- workflow；
- logs；
- deterministic replay；
- correctness；
- performance；
- reliability；
- limitations；
- package readiness。

### 4. 性能竞争力状态

必须分别判断：

```text
SIMULATOR_EVIDENCE_COMPLETENESS
PERFORMANCE_TARGET_ACHIEVEMENT
REAL_DEVICE_PERFORMANCE
```

不得用单一“性能已完成”概括三者。

### 5. 参赛包就绪状态

必须分别判断：

```text
SOURCE_READY
BUILD_READY
TEST_READY
DOCUMENT_READY
AGENT_READY
SIMULATOR_READY
DEMO_READY
RELEASE_READY
```

## 9.11 测试要求

至少新增或运行以下 G3-A focused tests：

1. requirement schema；
2. requirement ID uniqueness；
3. requirement source presence；
4. artifact path validation；
5. no fabricated path；
6. evidence path existence；
7. evidence SHA256 reference；
8. status enum；
9. evidence level enum；
10. risk enum；
11. owner checkpoint enum；
12. Markdown/JSON count consistency；
13. claim allowed/prohibited wording；
14. no `REAL_DEVICE_PASS`；
15. no false `measured_on_real_npu=true`；
16. no false `direct_hccl_api_call=true`；
17. no public inclusion of confidential source by default；
18. repository-relative paths；
19. UTF-8 parsing；
20. final evidence SHA256。

普通回归只需覆盖与审计工具直接相关的轻量测试。

除非 G3-A 修改了通用模块，不要求重跑完整 574-test Python suite。

如果修改了通用 registry、report 或 evidence parser，则必须运行受影响的 focused regression。

不得通过新增无理由 skip 获得通过。

## 9.12 G3-A Evidence

只保留一份权威 evidence：

```text
experiments/submission/evidence/g3_a_<timestamp>/
```

至少包含：

```text
README.md
manifest.json
result.json
requirement_matrix.json
deliverable_inventory.json
claim_boundary_matrix.json
risk_register.json
source_inventory.json
roadmap_assignment.json
audit_summary.json
regression.json
SHA256SUMS
```

Evidence 必须记录：

```text
checkpoint=G3-A
checkpoint_status=COMPLETED
audit_type=COMPETITION_DELIVERY_GAP_AUDIT
g2_f_baseline_status=FROZEN
old_evidence_modified=false
real_device_api_executed=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
measured_on_real_npu=false
```

还必须记录：

- baseline commit；
- project commit；
- source documents；
- source confidentiality；
- scanned paths；
- excluded paths；
- requirement counts；
- status counts；
- risk counts；
- evidence level counts；
- missing artifact count；
- blocker count；
- owner checkpoint distribution；
- generated documents；
- focused tests；
- known limitations；
- HCOMM/HCCL branch、commit 和 clean 状态；
- evidence SHA256。

不得在 evidence 中包含完整赛题原文件内容。

## 9.13 完成条件

只有以下条件全部满足时，G3-A 才可标记 `COMPLETED`：

- 正式赛题要求已建立 requirement inventory；
- requirement ID 稳定且无重复；
- 至少覆盖代码、插件、Agent、Prompt、模拟器、测试、报告、视频和发布；
- 每条 requirement 均有明确状态；
- 每条非满足项均有 gap、risk 和 owner checkpoint；
- C/C++ 插件合规专项结论明确；
- `.so`、headers 和 CMake 交付状态明确；
- 三原语覆盖状态明确；
- 8/64/1024 ranks 的真实性边界明确；
- Agent Skills/Prompt/log/trace 状态明确；
- simulator config/workflow/log 状态明确；
- performance target 与 evidence completeness 分开判断；
- reliability、100 ms、retry 和 logical 72h 边界明确；
- 5 分钟视频和演示材料状态明确；
- confidentiality、license 和 redistribution 风险明确；
- Markdown 与 JSON 一致；
- focused tests 通过；
- G2-E/G2-F old evidence 未修改；
- G3-A evidence SHA256 全部通过；
- HCOMM/HCCL tracked worktree clean；
- 工作区 clean；
- 未 push、未 merge；
- 未开始 G3-B。

最终状态必须为：

```text
G3-A: COMPLETED
Competition Requirement Inventory: COMPLETED
Deliverable Inventory: COMPLETED
Claim Boundary Audit: COMPLETED
Gap and Risk Register: COMPLETED
G3 Delivery Readiness: PARTIAL
Real-device Acceptance: HARDWARE_BLOCKED
```

G3 Delivery Readiness 在 G3-G 完成前保持：

```text
PARTIAL
```

## 9.14 阻塞与失败分类

### ENV_BLOCKED

适用于：

- 正式赛题文件无法读取；
- G2-F final evidence 缺失；
- evidence SHA256 无法验证；
- 仓库关键目录不可访问；
- Python 审计工具无法运行；
- Git metadata 无法读取；
- HCOMM/HCCL 冻结状态无法审计。

必须保留原始错误和恢复建议。

### USER_ACTION_REQUIRED

适用于：

- 需要用户确认赛题文件是否可随包分发；
- 需要用户确认最终报名平台格式；
- 需要用户确认团队信息；
- 需要用户确认许可证或版权声明；
- 需要用户提供缺失的原始 Prompt 或 Agent 日志；
- 需要用户决定是否公开 release；
- 需要用户决定最终提交哪些官方或第三方资产。

### HARDWARE_BLOCKED

只适用于：

- 真实 NPU collective；
- 真实 HCCS/RoCE/PCIe；
- 真实 8/64/1024 device scale；
- 真实 failover；
- 真实 72h；
- 真实 `msprof`；
- 真实 BERT/LLaMA 训练；
- 真实 direct API acceptance。

硬件缺失不影响 G3-A 审计完成。

### FAIL

适用于：

- requirement inventory 明显遗漏；
- 路径或 evidence 被伪造；
- Markdown 与 JSON 不一致；
- 将模拟结果写成实机；
- 将 static readiness 写成 runtime pass；
- old evidence 被修改；
- audit script 输出不确定；
- 状态或风险分类错误；
- C/C++ 合规问题被隐藏；
- confidential source 被错误列入公开交付；
- 前置条件满足但实现不能通过。

不得把审计缺陷标记为 `HARDWARE_BLOCKED`。

## 9.15 建议 commit 与停止边界

建议分支：

```text
codex/g3-a-delivery-gap-audit
```

建议 commit：

```text
G3-A audit competition delivery gaps
```

完成本地 commit 后必须停止。

不得：

- push；
- merge；
- 开始 G3-B；
- 创建最终压缩包；
- 发布 release；
- 创建 tag；
- 重写正式报告；
- 执行真实设备步骤。

回滚使用该项目 commit 的：

```text
git revert
```

不得重写历史或删除 G2 evidence。

# 10. G3-B：原生插件交付规范化、可复现构建与提交包 Staging

## 10.1 目标

G3-B 在 G3-A 差距审计基础上，完成以下四项工程交付：

1. 冻结项目最终原生产物的身份、命名、ABI、导出符号和真实性边界；
2. 建立不依赖隐藏开发状态的可复现构建与安装流程；
3. 建立 submission-level 的统一环境检查、quick 和 full 复现入口；
4. 建立可审计但尚未正式发布的提交包 staging、manifest、排除规则和 SHA256。

本 checkpoint 的目标状态是：

```text
NATIVE DELIVERY NORMALIZATION
REPRODUCIBLE BUILD
SUBMISSION REPRODUCTION ENTRY
SUBMISSION STAGING
```

本 checkpoint 不是：

```text
REAL-DEVICE DIRECT API ACCEPTANCE
FINAL RELEASE
PUBLIC RELEASE
FINAL COMPETITION SUBMISSION
```

G3-B 只能建立提交候选结构和复现基础，不能因为生成了 `.so`、staging 目录或 manifest 就宣称完整参赛作品已经发布。

---

## 10.2 G3-A 审计基线

G3-B 必须以 G3-A 最终审计结果为事实基线。

当前已确认：

```text
C/C++ Plugin Compliance: PARTIALLY_SATISFIED
Agent/Prompt Reproducibility: PARTIALLY_SATISFIED
Simulator Delivery: PARTIALLY_SATISFIED
Simulator Evidence Completeness: SATISFIED
Performance Target Achievement: PARTIALLY_SATISFIED
Real-device Performance: HARDWARE_BLOCKED
```

G3-B 重点处理以下风险：

```text
RISK-CO-001
RISK-CPP-001
RISK-CPP-002
RISK-CPP-004
RISK-CPP-005
RISK-CPP-006
RISK-AGENT-001
RISK-SIM-001
RISK-SIM-006
RISK-TEST-002
RISK-TEST-003
RISK-TEST-004
RISK-DOC-001
RISK-PACKAGE-001
RISK-PACKAGE-003
RISK-PACKAGE-004
```

G3-B 不负责解决以下风险：

```text
Agent Prompt/Skills/version/provenance      -> G3-D
正式算法、正确性、性能、可靠性报告          -> G3-C
算法创新叙事和正式图表                       -> G3-E
视频、分镜、旁白和字幕                       -> G3-F
最终许可证、SBOM、隐私、clean archive 审计   -> G3-G / USER_ACTION
真实 NPU 验收                                -> REAL_DEVICE_FUTURE
```

---

## 10.3 执行前状态与额度控制

进入本 checkpoint 前，用户已经人工确认：

- G3-A 已通过 PR 合并进入 `main`；
- 本地 `main` 与 `origin/main` 已同步；
- G3-A commit 已成为 `main` 的祖先；
- G3-A 最终 evidence SHA256 有效；
- 工作区除尚未提交的 G3-B 计划细化外无其他修改；
- G2-E、G2-F 和 G3-A 旧 evidence 未被修改。

执行开始时只允许进行一次轻量确认：

```text
git branch --show-current
git status --short
```

只需确认：

- 当前分支为 `main`；
- 除 G3-B 计划细化外没有其他未提交修改。

除非实际出现：

- 文件缺失；
- CMake target 漂移；
- G3-A 路径失效；
- evidence SHA256 失败；
- 构建结果与审计结论矛盾；

否则不得重复审计完整 Git 历史、旧 PR 或全部旧 checkpoint。

HCOMM/HCCL branch、commit 和 tracked worktree clean 只在最终审计时检查一次。

建议分支：

```text
codex/g3-b-reproducible-submission
```

---

## 10.4 G3-B 非目标

G3-B 不负责：

- 执行真实 ACL/HCCL runtime；
- 初始化真实 device/context/stream；
- 创建真实 communicator；
- 分配真实 NPU device memory；
- 执行真实 HcclAllReduce、HcclAllGather 或 HcclReduceScatter；
- 执行 `hccl_test`、MPI 或 `msprof`；
- 将 CPU_SIM ABI 替换成官方 ABI；
- 将 direct readiness 伪装成实机插件；
- 将两个不同 ABI 强行合并为一个不可审计接口；
- 重写三原语核心算法；
- 重写 simulator performance model；
- 重跑 G2-F-5/F6 完整实验矩阵；
- 重写 G2-F 或 G3-A evidence；
- 编写全部正式技术报告；
- 建立历史 Agent 生成 trace；
- 生成最终视频；
- 选择项目许可证；
- 决定正式赛题文件是否可公开；
- 决定官方 CANN/HCOMM/HCCL 二进制的再分发权；
- 创建最终 release archive；
- 创建 Git tag；
- 发布 GitHub Release；
- 上传报名平台。

发现上述缺口时必须保留给对应 checkpoint 或 `USER_ACTION`。

---

## 10.5 原生产物双轨交付原则

G3-B 必须冻结两个彼此独立的原生交付轨道。

### 10.5.1 CPU_SIM 原生插件

现有：

```text
libhccl_plugin.so
```

只能定义为：

```text
PROJECT-OWNED CPU_SIM C/C++ COLLECTIVE PLUGIN
```

它可以证明：

- 项目自有 C ABI；
- C/C++ 三原语实现；
- Ring、Mesh、Butterfly、NHR、Fat-Tree 等项目算法入口；
- host memory 上的数据正确性；
- 无 NPU 环境下可构建；
- 无 CANN SDK 环境下可运行；
- CTest 和 Python bridge 回归；
- 项目插件发现入口；
- 仅依赖允许的 host system library。

它不能证明：

- 官方 HCCL direct runtime 已执行；
- 与官方 HCCL plugin loader ABI 完全一致；
- 真实 NPU collective；
- 真实 HCCS/RoCE/PCIe 通信；
- 真实 NPU 性能；
- 官方 HCOMM topology probe；
- 零 CPU 介入；
- 真实 device memory；
- `REAL_DEVICE_PASS`。

CPU_SIM 产物不得使用以下名称：

```text
official_hccl_plugin
real_hccl_plugin
ascend_runtime_plugin
npu_validated_plugin
```

建议最终文件名继续保持：

```text
libhccl_plugin.so
```

但在 manifest、README、目录名和报告中必须固定显示：

```text
artifact_role=CPU_SIM_REFERENCE_PLUGIN
execution_environment=HOST_CPU
official_runtime_execution=false
real_device_validated=false
```

### 10.5.2 ASCEND_HCCL_DIRECT readiness 交付

现有 direct adapter 只能定义为：

```text
OFFICIAL-ABI DIRECT READINESS ADAPTER
```

当前能力包括：

- 官方头文件签名静态冻结；
- direct C ABI；
- capacity contract；
- lifecycle state machine；
- resource ownership；
- failure injection；
- no-device preflight；
- build/link/symbol audit；
- host-only lifecycle test。

它不能定义为：

```text
可执行的真实 NPU collective plugin
```

G3-B 可以将 direct adapter 规范化为可安装的 source/readiness package，但不得新增当前环境可到达的真实 runtime 调用路径。

允许最终交付：

```text
direct/include/hccl_direct_adapter.h
direct/src/hccl_direct_adapter.cpp
direct ABI manifest
direct build instructions
direct lifecycle contract
direct no-device diagnose
direct link audit source
direct readiness evidence references
```

允许生成项目自己的 shared readiness artifact，例如：

```text
libhccl_direct_adapter.so
```

但只有同时满足以下条件时才允许：

1. 它继续只暴露项目自有 direct control-plane C ABI；
2. 默认不调用任何 ACL/HCCL runtime；
3. 无设备执行请求仍在 runtime 边界前拒绝；
4. 其名称、SONAME、README 和 manifest 明确包含 `direct_adapter` 或 `readiness`；
5. 不导出或冒充 CPU_SIM collective ABI；
6. 不被描述为官方 collective plugin；
7. 不设置 `direct_hccl_api_call=true`；
8. 不设置 `real_ascend_npu_validated=true`。

如果没有必要生成 shared readiness artifact，可以继续保留：

```text
libhccl_direct_adapter.a
```

但必须在 staging manifest 中说明其是：

```text
STATIC BUILD/LIFECYCLE READINESS ARTIFACT
```

不得为满足“必须有 `.so`”的表面要求，将 static readiness archive 简单改名为 `.so`。

---

## 10.6 最终插件 ABI 决策

G3-B 必须生成：

```text
docs/submission/native_plugin_abi_decision.md
```

该文档必须明确回答：

1. 最终可执行 `.so` 是哪个；
2. 它的角色是什么；
3. 它的 ABI 是项目本地 ABI还是官方 ABI；
4. 它导出哪些符号；
5. 它依赖哪些库；
6. 它在哪种环境可执行；
7. 它如何构建；
8. 它通过哪些测试；
9. 它不能证明什么；
10. direct readiness 产物是什么；
11. 两条轨道为何不能合并；
12. 评委如何分别验证两条轨道；
13. 未来真实设备如何恢复 direct acceptance。

必须采用以下决策状态之一：

```text
CPU_SIM_PLUGIN_SELECTED_FOR_HOST_REPRODUCTION
OFFICIAL_COMPATIBLE_WRAPPER_STATICALLY_VERIFIED
OFFICIAL_PLUGIN_ABI_UNVERIFIED
USER_ACTION_REQUIRED
```

如果没有可靠的正式接口材料证明当前项目 ABI 就是赛题要求的官方插件 ABI，则必须选择：

```text
CPU_SIM_PLUGIN_SELECTED_FOR_HOST_REPRODUCTION
OFFICIAL_PLUGIN_ABI_UNVERIFIED
```

不得为提高合规状态而推断或虚构官方 loader ABI。

### 10.6.1 ABI manifest

必须生成机器可读：

```text
native_plugin_abi_manifest.json
```

至少记录：

```text
artifact_name
artifact_role
language
source_paths
public_headers
abi_namespace
abi_version
exported_symbols
required_symbols
forbidden_symbols
soname
dependencies
build_target
build_mode
runtime_mode
official_abi_status
cpu_simulated
direct_readiness
real_device_validated
```

### 10.6.2 导出符号

CPU_SIM `.so` 至少应审计：

- communicator lifecycle；
- rank selection；
- topology query/free；
- AllReduce；
- AllGather；
- ReduceScatter；
- plugin version；
- plugin algorithm inventory；
- 计划允许的算法级入口。

不得依赖：

- 编译器偶然导出的内部 static symbol；
- 未记录的 C++ mangled symbol；
- 全局默认导出策略作为唯一 ABI 控制；
- 不稳定的测试辅助符号。

建议使用：

- 明确的 visibility；
- 导出宏；
- version script 或平台等价机制；
- 稳定 allowlist。

现有导出符号数量可作为基线，但 G3-B 不得只验证数量，必须验证精确名称和角色。

### 10.6.3 ABI 隔离

必须证明：

```text
CPU_SIM ABI != DIRECT CONTROL-PLANE ABI != OFFICIAL HCCL ABI
```

至少检查：

- CPU*SIM 不导出 `hccl_direct*\*`；
- direct adapter 不导出 CPU_SIM `hccl*` 兼容符号；
- Python CPU_SIM bridge 不加载 direct adapter；
- direct backend 不加载 CPU_SIM `.so` 执行 direct collective；
- direct source 使用官方 `Hccl*` 类型只用于签名冻结和未来边界；
- 两类结果写入不同的 manifest 和 evidence 字段。

---

## 10.7 CMake 规范化

G3-B 必须将原生构建整理成明确的三种模式。

### 10.7.1 默认 host 模式

```text
HCCL_BACKEND=CPU_SIM
HCCL_ENABLE_ASCEND_HCCL_DIRECT=OFF
```

要求：

- 不需要 CANN；
- 不检查 CANN root；
- 不链接 `libhccl.so`；
- 不链接 `libhcomm.so`；
- 不链接 `libacl_rt.so`；
- 可构建 `libhccl_plugin.so`；
- 可构建并运行 CPU_SIM CTest；
- 可执行 install；
- 安装目录可移植；
- 不写入源码目录。

### 10.7.2 Direct readiness 模式

```text
HCCL_ENABLE_ASCEND_HCCL_DIRECT=ON
HCCL_CANN_ROOT=<explicit canonical root>
```

要求：

- 只搜索指定 root；
- 不使用系统默认同名库；
- 校验 CANN version；
- 校验 official headers；
- 校验 library canonical realpath；
- 校验 official symbols；
- 构建 direct adapter；
- 构建非执行 link-audit artifact；
- 运行 host-only lifecycle test；
- 不运行 link-audit executable；
- 不调用 runtime；
- 不执行 collective。

### 10.7.3 Submission install 模式

必须提供稳定 install 规则，建议支持：

```text
cmake --install <build-dir> --prefix <stage>/native
```

至少安装：

```text
native/lib/libhccl_plugin.so
native/include/hccl_comm.h
native/include/hccl_algorithms.h
native/cmake/
native/README.md
native/ABI_MANIFEST.json
```

direct readiness source可以安装或复制到：

```text
native/direct/include/
native/direct/src/
native/direct/cmake/
native/direct/README.md
native/direct/ABI_MANIFEST.json
```

不得把官方 CANN/HCOMM/HCCL DSO 安装到 staging。

### 10.7.4 CMake target 命名

建议冻结：

```text
hccl_plugin
hccl_cpu_sim_tests
hccl_direct_adapter
hccl_direct_link_audit
hccl_direct_lifecycle_tests
submission_native_install
```

具体 target 可按现有结构调整，但必须避免：

- `hccl_plugin` 在不同 flag 下静默变成完全不同 ABI；
- `ASCEND_CANN` 名称暗示已经真实执行；
- 一个 target 同时承担 CPU_SIM 和 direct readiness；
- 默认 build 无意链接 CANN；
- install 规则复制官方 DSO。

### 10.7.5 禁止不透明的 ASCEND_CANN stub

如果现有：

```text
HCCL_BACKEND=ASCEND_CANN
```

仍只是 `STUB_UNVERIFIED`，G3-B 必须采取以下方式之一：

1. 保留但明确标记 deprecated/readiness-only；
2. 重命名为不会暗示真实执行的 build mode；
3. 从 submission quick path 中排除；
4. 在配置时输出清晰 warning；
5. 在文档中说明它不是 real-device backend。

不得让评委通过该 flag 得到“已启用真实 CANN collective”的错误印象。

---

## 10.8 可复现构建

G3-B 必须提供无隐藏状态的构建流程。

### 10.8.1 干净构建目录

所有构建必须发生在：

```text
build/
dist/
tmp/
```

或用户指定的外部目录。

不得依赖：

- 已存在的 `hcccl/build`；
- 开发机旧 object；
- 开发机旧 `.so`；
- 未记录环境变量；
- `.venv` 中未冻结包；
- 用户 home 下的私有文件；
- IDE task cache。

### 10.8.2 双构建验证

CPU_SIM release artifact 至少执行两次独立干净构建：

```text
build-a
build-b
```

两次必须使用：

- 相同 source commit；
- 相同 compiler；
- 相同 CMake version；
- 相同 build type；
- 相同 normalized environment；
- 相同 build options。

至少比较：

```text
binary SHA256
SONAME
ELF NEEDED
exported symbol set
file type
architecture
installed headers SHA256
ABI manifest
CTest result
```

理想状态：

```text
BIT_FOR_BIT_REPRODUCIBLE=true
```

如果二进制 SHA256 不一致，必须分析：

- build-id；
- embedded path；
- timestamp；
- debug section；
- archive ordering；
- compiler nondeterminism。

不得只记录“可以再次编译”就宣称 bit-for-bit reproducible。

如果经过合理修复仍不能获得相同 SHA256，可以将状态设置为：

```text
FUNCTIONALLY_REPRODUCIBLE
BIT_FOR_BIT_REPRODUCIBLE=false
```

但必须：

- 记录差异原因；
- 确认 ABI、ELF、依赖和测试一致；
- 将其列为 G3-G release 风险；
- 不伪造相同 hash。

### 10.8.3 Build metadata

必须记录：

```text
compiler
compiler_version
cmake_version
generator
build_type
source_commit
source_date_epoch
build_options
target_architecture
host_os
linker
linker_version
binary_sha256
header_sha256
```

不得记录敏感用户路径到公开 manifest。

路径应规范化为：

```text
<repo>
<build>
<cann-root>
```

---

## 10.9 依赖政策

### 10.9.1 CPU_SIM 依赖

CPU_SIM `.so` 必须完成：

```text
readelf -d
ldd
nm -D
file
```

审计。

目标是只依赖允许的基础系统库。

如果发现新增依赖，必须：

- 记录名称；
- 记录用途；
- 记录许可证；
- 记录 staging 是否需要；
- 更新依赖 inventory；
- 不得静默引入。

### 10.9.2 Direct readiness 依赖

direct build/link audit 可以引用本地冻结：

```text
libhccl.so
libhcomm.so
libacl_rt.so
```

但 staging 默认只能包含：

- 项目 source；
- 项目 header；
- 项目 manifest；
- 构建说明；
- 官方 DSO 的名称、版本、hash 和用户本地路径占位符；
- 恢复说明。

不得默认复制：

```text
libhccl.so
libhcomm.so
libacl_rt.so
libruntime.so
HCOMM source
HCCL source
CANN SDK files
```

### 10.9.3 再分发状态

在用户完成正式审查前，必须固定：

```text
official_asset_redistribution=NOT_AUTHORIZED
official_binaries_included=false
official_source_included=false
```

若用户未来提供正式授权，必须由独立 checkpoint 更新，不得在 G3-B 中自行推断授权。

---

## 10.10 统一 submission CLI

G3-B 必须建立单一、可测试的 submission-level CLI。

建议入口：

```text
python -m tools.submission_cli
```

或仓库现有结构中的等价入口。

至少支持：

```text
check
build
quick
full
stage
verify
describe
clean-generated
```

### 10.10.1 `check`

只读检查：

- Python version；
- CMake；
- compiler；
- make/ninja；
- platform；
- repository root；
- required source files；
- configuration files；
- old evidence paths；
- optional CANN root；
- official asset exclusion；
- writable build/stage directory。

输出必须区分：

```text
REQUIRED
OPTIONAL
REAL_DEVICE_ONLY
USER_ACTION_REQUIRED
```

没有 CANN 或 NPU 时，默认 CPU_SIM quick path 不能失败。

### 10.10.2 `build`

默认只构建 CPU_SIM：

```text
python -m tools.submission_cli build
```

必须：

- 使用干净或显式 build 目录；
- 构建 release `.so`；
- 构建 tests；
- 执行 install；
- 生成 build manifest；
- 不调用 direct runtime。

direct readiness build 必须显式：

```text
python -m tools.submission_cli build --direct-readiness --cann-root <path>
```

且只能执行计划允许的静态、链接和 host lifecycle 步骤。

### 10.10.3 `quick`

Quick 模式目标是让评委在较短时间内确认项目基本可用。

至少包含：

1. 环境检查；
2. CPU_SIM clean build；
3. CPU_SIM CTest 代表集或全部 11 项；
4. 三原语各一个确定性用例；
5. FP32 基本正确性；
6. 一个 FP16/BF16 代表用例；
7. 一个 8-rank simulator 场景；
8. 一个 topology/algorithm comparison 场景；
9. 一个 fault-recovery 场景；
10. 一个 no-alternate-path 预期失败场景；
11. 关键 G2-F-5/F6 evidence SHA256 验证；
12. 生成简短 result summary。

Quick 模式不得：

- 重跑完整 56 点性能矩阵；
- 重跑全部 1,580 iteration；
- 重新生成 logical 72h 权威 evidence；
- 执行完整 HCCL-VM suite；
- 执行真实 direct API；
- 改写旧 evidence。

### 10.10.4 `full`

Full 模式用于 submission staging 验证。

至少包含：

1. 完整环境检查；
2. CPU_SIM 两次干净构建；
3. install 验证；
4. ELF、symbol、dependency 和 ABI audit；
5. CPU_SIM 全部 CTest；
6. Python 全量或 submission-relevant 全量回归；
7. direct build/link readiness audit，如 CANN root 可用；
8. direct lifecycle host-only CTest；
9. G2-E/G2-F/G3-A evidence SHA256；
10. simulator deterministic representative replay；
11. quick command 回归；
12. staging manifest；
13. inclusion/exclusion audit；
14. staging verify；
15. final summary。

Full 模式默认不重新生成 G2-F-5/F6 权威 evidence。

可提供单独 opt-in：

```text
--regenerate-expensive-simulator-evidence
```

但 G3-B 默认不得执行该选项。

### 10.10.5 `stage`

生成 staging 目录，但不生成正式 release。

建议路径：

```text
dist/submission-staging/
```

必须支持：

```text
--output <path>
--clean-output
--include-selected-evidence
--exclude-controlled-docs
--exclude-official-assets
```

`stage` 默认必须：

```text
exclude_controlled_competition_doc=true
exclude_official_cann_binaries=true
exclude_official_hcomm_hccl_source=true
exclude_private_logs=true
```

### 10.10.6 `verify`

必须验证：

- manifest schema；
- 所有 included 文件存在；
- 所有文件 SHA256；
- 未包含 excluded path；
- `.so` ELF 类型；
- `.so` dependencies；
- public headers；
- CMake；
- quick/full scripts；
- relative links；
- evidence references；
- controlled asset exclusion；
- no forbidden truth claims；
- staging root 不含绝对用户路径。

### 10.10.7 `describe`

输出：

- 三后端；
- simulator validation track；
- native artifact identity；
- quick/full 功能；
- 当前限制；
- real-device blocked reason；
- staging inclusion policy。

该命令只读，不执行构建或测试。

### 10.10.8 `clean-generated`

只能删除 CLI 自己创建且位于明确 generated root 下的目录。

必须拒绝：

- 删除源码；
- 删除旧 evidence；
- 删除 `.git`；
- 删除用户未标记为 generated 的目录；
- 跟随 symlink 删除外部路径；
- 等价于执行 `git clean -fd`。

---

## 10.11 拓扑和配置注入接口

G3-A 指出异构设备和非对称链路目前属于 simulator configured，缺少统一提交级注入入口。

G3-B 不重写 topology model，但必须使 submission CLI 可以显式接收：

```text
--cluster-config
--topology-config
--hardware-profile
--seed
--message-size
--rank-size
--primitive
--algorithm
```

要求：

- 使用仓库相对或用户显式路径；
- 校验 schema；
- 记录配置 SHA256；
- 不依赖修改源码；
- quick 使用冻结默认配置；
- full 可以读取受控配置矩阵；
- 配置中的拓扑来源必须保持 `SIMULATOR_CONFIG`；
- 不得标记为真实自动探测。

必须提供至少以下示例配置：

```text
configs/submission/full_mesh_8.json
configs/submission/ring_8.json
configs/submission/fat_tree_64.json
configs/submission/heterogeneous_asymmetric.json
configs/submission/logical_1024.json
configs/submission/fault_recovery.json
```

具体结构可复用现有配置，不得复制一套语义漂移的新格式。

---

## 10.12 Staging 目录结构

建议 staging 结构：

```text
submission-staging/
├── README.md
├── QUICKSTART.md
├── MANIFEST.json
├── SHA256SUMS
├── STATUS.json
├── CLAIM_BOUNDARIES.md
├── EXCLUDED_ASSETS.json
├── native/
│   ├── README.md
│   ├── ABI_MANIFEST.json
│   ├── lib/
│   │   └── libhccl_plugin.so
│   ├── include/
│   │   ├── hccl_comm.h
│   │   └── hccl_algorithms.h
│   ├── source/
│   ├── cmake/
│   ├── tests/
│   └── direct/
│       ├── README.md
│       ├── ABI_MANIFEST.json
│       ├── include/
│       ├── source/
│       └── build-readiness/
├── agent/
│   ├── README.md
│   ├── source/
│   └── PLACEHOLDER_G3_D.md
├── simulator/
│   ├── README.md
│   ├── source/
│   ├── tools/
│   └── configs/
├── tools/
│   ├── submission_cli/
│   ├── benchmark/
│   └── fault_injection/
├── tests/
│   ├── native/
│   └── python/
├── evidence/
│   ├── README.md
│   ├── inventory.json
│   ├── simulator_correctness/
│   ├── simulator_performance_reliability/
│   ├── direct_readiness/
│   └── final_audit/
├── reports/
│   └── PLACEHOLDER_G3_C.md
├── demo/
│   └── PLACEHOLDER_G3_F.md
└── release/
    ├── BUILD_MANIFEST.json
    ├── DEPENDENCY_MANIFEST.json
    └── USER_ACTION_REQUIRED.json
```

实际目录可根据仓库结构精简，但必须保持：

- native、Agent、simulator、evidence、reports、demo 分区；
- CPU_SIM 和 direct readiness 分区；
- source 和 generated binary 可追溯；
- 未完成 G3-C/D/F 时不得伪造正式材料；
- placeholder 必须清晰标记为未完成，不得冒充交付物。

---

## 10.13 Inclusion manifest

必须生成：

```text
submission_inclusion_manifest.json
```

每个条目至少包含：

```text
artifact_id
source_path
staging_path
category
artifact_role
include
required
generated
source_commit
sha256
size_bytes
license_status
confidentiality
redistribution_status
execution_status
evidence_level
claim_label
owner_checkpoint
known_limitations
```

### 10.13.1 默认包含

至少考虑包含：

- project source；
- CPU_SIM `.so`；
- public headers；
- CMake；
- native tests；
- Agent source和顶层入口；
- simulator source；
- simulator configs；
- selected tests；
- benchmark tools；
- fault injection tools；
- selected final evidence；
- G3-A matrices；
- quick/full CLI；
- build and staging manifests；
- claim boundaries；
- known limitations。

### 10.13.2 默认排除

必须默认排除：

```text
.git/
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.idea/
.vscode/ private workspace settings
node_modules/
temporary build directories
crash/core dumps
private logs
.env
API keys
tokens
cookies
SSH keys
proxy credentials
absolute-user-path reports
official CANN binaries
official HCOMM/HCCL source
controlled competition DOCX
superseded intermediate evidence
unbounded raw logs not selected for submission
```

### 10.13.3 条件包含

以下资产只能条件包含：

```text
controlled competition DOCX
official source excerpts
official binaries
historical Agent logs
Prompt call logs
team information
license
copyright notice
large raw evidence
```

在用户未确认前，状态必须为：

```text
include=false
decision=USER_ACTION_REQUIRED
```

---

## 10.14 Evidence 选择与大小控制

G3-B 不得无差别复制全部历史 evidence。

必须建立：

```text
evidence_selection_policy.json
```

每项旧 evidence 指定：

```text
INCLUDE_FULL
INCLUDE_SUMMARY_ONLY
REFERENCE_ONLY
EXCLUDE_SUPERSEDED
USER_ACTION_REQUIRED
```

至少保留：

- G2-F-5 correctness 权威 summary；
- G2-F-6 performance/reliability 权威 summary；
- G2-F-7 final audit；
- G3-A final audit；
- direct build/link/lifecycle readiness 关键 summary；
- SHA256SUMS；
- evidence inventory。

大型 raw JSONL 是否完整纳入 staging，必须根据：

- 文件大小；
- 平台大小限制；
- 评委复现需求；
- 是否可由脚本重新生成；
- 是否含私密路径；

进行决策。

G3-B 可以生成 staging-size report，但最终平台约束由用户确认，G3-G 再完成最终 archive 审计。

---

## 10.15 顶层复现文档

G3-B 至少生成或更新：

```text
README.md
docs/submission/reproduction_guide.md
docs/submission/native_plugin_abi_decision.md
docs/submission/submission_staging_guide.md
docs/submission/dependency_and_redistribution_boundary.md
```

### 10.15.1 README 最低内容

必须明确：

- 项目目标；
- 三种 backend；
- simulator validation track；
- 默认 CPU_SIM；
- `.so` 的准确身份；
- direct readiness 的准确身份；
- 无 NPU 也可完成哪些步骤；
- quick 命令；
- full 命令；
- stage 命令；
- verify 命令；
- 真实设备尚未执行；
- 报告、evidence 和 claim boundary 位置。

### 10.15.2 Quick start

必须控制在少量命令内，例如：

```text
python -m tools.submission_cli check
python -m tools.submission_cli quick
python -m tools.submission_cli stage
python -m tools.submission_cli verify --stage <path>
```

具体命令以实际实现为准，但不得要求评委先人工复制 `.so`、修改源码或编辑绝对路径。

### 10.15.3 Direct readiness 文档

必须说明：

- 需要本地合法 CANN 9.1.0；
- SDK 不随包分发；
- CANN root 必须显式指定；
- 只执行 build/link/lifecycle readiness；
- 不执行真实 runtime；
- 没有 NPU 时返回 `NO_DEVICE_EXPECTED`；
- 真实验收仍为 `HARDWARE_BLOCKED`。

---

## 10.16 Preliminary forbidden-data audit

最终 secrets、license 和隐私审计属于 G3-G，但 G3-B staging 必须执行最低限度防线。

至少检查：

- 常见 API key 格式；
- access token；
- private key header；
- `.env`；
- Cookie；
- password 字段；
- Windows 用户目录；
- WSL home path；
- `/home/workspace` 是否不必要暴露；
- ignored private logs；
- official binary extensions；
- controlled DOCX；
- symlink escaping staging root。

该审计只可标记：

```text
PRELIMINARY_FORBIDDEN_DATA_SCAN
```

不得替代 G3-G 的最终合规审计。

---

## 10.17 Claim boundary 固化

staging 中必须生成：

```text
CLAIM_BOUNDARIES.md
claim_boundaries.json
```

至少固化以下声明：

### CPU_SIM 插件

允许：

```text
项目自有 CPU_SIM C/C++ collective plugin 可在 host 环境构建和测试。
```

禁止：

```text
已完成官方 HCCL direct plugin 实机验收。
```

### Direct adapter

允许：

```text
官方 ABI、build/link、guard 和 lifecycle readiness 已完成静态或 host 验证。
```

禁止：

```text
已执行真实 HCCL collective。
```

### 1024 ranks

允许：

```text
在指定 simulator model 下完成 logical 1024-rank 预测。
```

禁止：

```text
真实支持 1024 卡。
```

### Logical 1 GB

允许：

```text
采用有界物化和分析记账验证 logical 1 GB。
```

禁止：

```text
真实 NPU 已传输 1 GB collective。
```

### Logical 72h

允许：

```text
完成事件驱动 logical 72h simulation。
```

禁止：

```text
完成真实 72 小时压测。
```

### 100 ms failover

允许：

```text
模拟场景达到模型化 100 ms 阈值。
```

禁止：

```text
真实集群 100 ms 内切换。
```

staging verifier 必须扫描关键 manifest、README 和 summary，防止出现受禁止措辞。

---

## 10.18 测试要求

G3-B 至少新增或运行以下测试。

### 10.18.1 Native build

1. CPU_SIM default configure；
2. CPU_SIM default build；
3. CPU_SIM install；
4. CPU_SIM `.so` file type；
5. CPU_SIM SONAME；
6. CPU_SIM exact symbol allowlist；
7. CPU_SIM forbidden symbol list；
8. CPU_SIM dependency audit；
9. CPU_SIM CTest 11/11；
10. installed headers compile test；
11. installed package consumer compile test；
12. two-clean-build comparison；
13. no CANN dependency in default mode；
14. source tree unchanged after external build。

### 10.18.2 Direct readiness

15. feature flag default OFF；
16. explicit CANN root required；
17. canonical CANN root only；
18. official header signature assertions；
19. direct adapter build；
20. direct link-audit ELF inspection；
21. link-audit executable not run；
22. host-only lifecycle CTest；
23. no-device preflight；
24. `runtime_api_calls=[]`；
25. no actual ACL/HCCL call expression in reachable path；
26. official DSO not copied to staging；
27. direct ABI and CPU_SIM ABI isolation。

### 10.18.3 Submission CLI

28. `check` success without CANN；
29. `build` success；
30. `quick` deterministic success；
31. `full` success；
32. `stage` creates expected structure；
33. `verify` validates SHA256；
34. `describe` is read-only；
35. `clean-generated` cannot escape generated root；
36. invalid path rejection；
37. symlink escape rejection；
38. unknown command rejection；
39. exit code contract；
40. JSON output schema；
41. Windows import safety；
42. WSL/Linux execution safety。

### 10.18.4 Staging

43. inclusion manifest schema；
44. all included paths exist；
45. no fabricated path；
46. no duplicate staging path；
47. no official binaries；
48. no official source tree；
49. controlled DOCX excluded by default；
50. private logs excluded；
51. old evidence remains immutable；
52. selected evidence SHA256 valid；
53. no absolute user paths；
54. artifact role labels；
55. claim boundary scan；
56. placeholder status correctness；
57. staging size report；
58. staging manifest and filesystem consistency。

### 10.18.5 Regression

59. CPU_SIM Python bridge；
60. top-level Agent CPU_SIM entry；
61. backend default remains CPU_SIM；
62. fallback remains NONE；
63. simulator representative replay；
64. G2-E/G2-F/G3-A evidence SHA256；
65. G3-A requirement/deliverable/claim matrix paths；
66. final HCOMM/HCCL tracked worktree clean。

不得：

- 删除或弱化旧测试；
- 增加无理由 skip；
- 用预生成旧 `.so` 代替 clean build；
- 跳过 symbol/dependency 检查；
- 执行真实 runtime；
- 修改旧 evidence；
- 为获取相同 hash 直接复制第一次构建产物作为第二次构建结果。

---

## 10.19 G3-B Evidence

只保留一份权威最终 evidence：

```text
experiments/submission/evidence/g3_b_<timestamp>/
```

至少包含：

```text
README.md
manifest.json
result.json
native_artifact_inventory.json
native_plugin_abi_manifest.json
direct_readiness_abi_manifest.json
build_environment.json
build_commands.json
reproducible_build_audit.json
elf_dependency_audit.json
symbol_inventory.json
install_audit.json
submission_cli_contract.json
quick_run_summary.json
full_run_summary.json
staging_manifest.json
staging_tree.json
staging_size_report.json
evidence_selection_policy.json
excluded_assets.json
forbidden_data_scan.json
claim_boundary_audit.json
regression.json
SHA256SUMS
```

Evidence 必须记录：

```text
checkpoint=G3-B
checkpoint_status=COMPLETED
native_delivery_normalization=COMPLETED
cpu_sim_submission_plugin=COMPLETED
direct_readiness_package=COMPLETED
reproducible_build_status=<BIT_FOR_BIT_REPRODUCIBLE|FUNCTIONALLY_REPRODUCIBLE>
submission_cli=COMPLETED
submission_staging=COMPLETED
final_release_created=false
public_release_created=false
official_binaries_included=false
official_source_included=false
controlled_competition_doc_included=false
old_evidence_modified=false
real_device_api_executed=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
measured_on_real_npu=false
runtime_api_calls=[]
```

还必须记录：

- baseline commit；
- project commit；
- CPU_SIM `.so` SHA256；
- CPU_SIM `.so` SONAME；
- exact exported symbols；
- exact dependencies；
- public header SHA256；
- CMake options；
- install tree；
- build-a/build-b comparison；
- direct artifact type；
- direct official-library references；
- direct no-device status；
- quick/full commands；
- quick/full exit status；
- staging root；
- staging file count；
- staging total size；
- inclusion/exclusion counts；
- selected evidence；
- USER_ACTION_REQUIRED；
- known limitations；
- HCOMM/HCCL branch、commit 和 clean 状态；
- evidence SHA256。

Evidence 不得包含：

```text
REAL_DEVICE_PASS
official_direct_plugin_validated=true
direct_hccl_api_call=true
real_ascend_npu_validated=true
measured_on_real_npu=true
runtime_initialized=true
communicator_created=true
collective_executed_on_real_device=true
```

---

## 10.20 USER_ACTION_REQUIRED

G3-B 必须保留以下人工决策，不能自行代替用户决定。

### UA-B-001：项目许可证

当前仓库缺少最终许可证或版权确认。

G3-B 可以：

- 生成许可证需求说明；
- 在 manifest 中标记缺失；
- 保留 staging placeholder；
- 阻止将 staging 标记为 release-ready。

G3-B 不得：

- 自行选择 MIT、Apache-2.0 或其他许可证；
- 代表团队确认版权；
- 伪造 copyright owner。

### UA-B-002：官方资产再分发

用户必须确认：

- CANN DSO 是否可分发；
- HCOMM/HCCL source 是否可分发；
- 官方 headers 是否可随包复制；
- 是否只能提供安装说明和 hash。

在确认前默认：

```text
EXCLUDE
```

### UA-B-003：赛题文件边界

用户必须确认受控赛题 DOCX 是否允许：

- 提交给赛事平台；
- 放入团队内部包；
- 放入公开 release。

在确认前默认：

```text
submission inclusion=USER_ACTION_REQUIRED
public release inclusion=false
```

### UA-B-004：平台格式和大小

用户必须确认：

- ZIP、7z 或其他格式；
- 最大文件大小；
- 单文件限制；
- 必须目录结构；
- 是否要求预编译 `.so`；
- 是否允许外部下载依赖；
- 是否要求团队字段。

G3-B 只生成 staging，不创建最终平台 archive。

---

## 10.21 完成条件

只有以下条件全部满足时，G3-B 才可标记 `COMPLETED`：

- G3-A 基线已读取且未修改；
- CPU_SIM `.so` 身份冻结；
- direct readiness 产物身份冻结；
- 两套 ABI 明确隔离；
- native plugin ABI decision 完成；
- CPU_SIM `.so` 可从 clean source 重建；
- `.so` exact symbol audit 通过；
- `.so` dependency audit 通过；
- public headers 与实现一致；
- CMake default CPU_SIM build 不依赖 CANN；
- CMake install 路径通过；
- external consumer compile test 通过；
- direct readiness build/link/lifecycle audit 通过；
- direct runtime 边界保持关闭；
- official DSO 未被复制；
- quick CLI 通过；
- full CLI 通过；
- simulator representative replay 通过；
- topology/config 注入入口可用；
- staging 目录生成成功；
- inclusion/exclusion manifest 完整；
- selected evidence SHA256 通过；
- controlled DOCX 默认排除；
- private logs 默认排除；
- official source/binary 默认排除；
- preliminary forbidden-data scan 通过；
- claim boundary audit 通过；
- G2-E/G2-F/G3-A old evidence 未修改；
- G3-B evidence SHA256 全部通过；
- HCOMM/HCCL tracked worktree clean；
- 工作区 clean；
- 未 push；
- 未 merge；
- 未开始 G3-C；
- 未创建最终 release archive；
- 未执行真实设备 API。

最终状态必须为：

```text
G3-B: COMPLETED
Native Delivery Normalization: COMPLETED
CPU_SIM Submission Plugin: COMPLETED
Direct Readiness Package: COMPLETED
Reproducible Build: COMPLETED
Submission CLI: COMPLETED
Submission Staging: COMPLETED
C/C++ Plugin Compliance: PARTIALLY_SATISFIED
Submission Release Readiness: PARTIAL
G3 Delivery Readiness: PARTIAL
Real-device Acceptance: HARDWARE_BLOCKED
```

### 10.21.1 C/C++ 合规状态升级规则

只有以下条件全部满足时，才允许将：

```text
C/C++ Plugin Compliance
```

从：

```text
PARTIALLY_SATISFIED
```

升级为：

```text
SATISFIED
```

条件：

1. 赛题要求的正式插件 ABI 有可引用的权威来源；
2. 项目最终 `.so` 精确实现该 ABI；
3. 所有 required entry points 均存在；
4. C/C++ 承担核心 collective 算法角色；
5. `.so` 可重复构建；
6. dependencies 符合赛题政策；
7. headers、CMake 和 tests 完整；
8. 不依赖将 CPU_SIM 冒充 real direct plugin；
9. 真实性措辞通过 claim audit。

如果无法证明官方 ABI，G3-B 仍可以完成，但必须保留：

```text
C/C++ Plugin Compliance: PARTIALLY_SATISFIED
```

不得通过修改状态定义强行升级。

### 10.21.2 Release readiness

即使 G3-B 全部通过，以下内容尚未完成：

- 项目许可证；
- G3-C 正式报告；
- G3-D Agent/Prompt trace；
- G3-E 图表和创新叙事；
- G3-F 演示视频；
- G3-G 最终 secrets/license/clean extraction/archive audit；
- 平台格式和大小确认。

因此：

```text
Submission Release Readiness
```

必须保持：

```text
PARTIAL
```

---

## 10.22 阻塞与失败分类

### ENV_BLOCKED

适用于：

- compiler 缺失；
- CMake 缺失；
- Python 环境无法导入；
- CPU_SIM 无法 clean build；
- install 目录不可写；
- CANN root 在 explicit direct readiness 模式下缺失；
- CANN version 或 official headers 漂移；
- G3-A/G2 evidence 无法读取；
- staging 文件系统不支持所需操作。

必须保留：

- 原始命令；
- exit code；
- stderr；
- 恢复建议。

### USER_ACTION_REQUIRED

适用于：

- 项目许可证；
- 团队版权；
- 官方资产再分发；
- 赛题 DOCX inclusion；
- 平台格式；
- 平台大小；
- 公开 release 决策。

这些人工决策不影响 CPU_SIM build、quick/full CLI 和内部 staging 的工程完成，但会阻止：

```text
Submission Release Readiness: COMPLETED
```

### HARDWARE_BLOCKED

只适用于：

- 真实 NPU；
- 真实 device/context/stream；
- 真实 communicator；
- 真实 collective；
- 真实 topology detection；
- 真实 performance；
- 真实 failover；
- 真实 `msprof`；
- direct real-device acceptance。

硬件缺失不影响 G3-B 完成。

### FAIL

适用于：

- CPU_SIM `.so` 无法从 clean source 构建；
- install 规则失效；
- public header 与实现不一致；
- required symbol 缺失；
- forbidden symbol 泄漏；
- 不允许的依赖被引入；
- CPU_SIM 与 direct ABI 混淆；
- direct guard 被绕过；
- official DSO 被复制进 staging；
- controlled DOCX 被默认打包；
- staging 含私密日志或 secret；
- quick/full 入口不稳定；
- staging manifest 与文件系统不一致；
- SHA256 失败；
- 旧 evidence 被修改；
- 模拟结果被写成实机；
- 为获得相同 hash 复用第一次构建产物；
- 前置环境满足但实现不能通过。

不得将代码、构建、打包、manifest 或文档缺陷标记为 `HARDWARE_BLOCKED`。

---

## 10.23 建议 commit 与停止边界

建议分支：

```text
codex/g3-b-reproducible-submission
```

建议 commit：

```text
G3-B normalize native delivery and reproducible submission staging
```

完成本地 commit 后必须停止。

不得：

- push；
- merge；
- 开始 G3-C；
- 创建最终 ZIP/7z；
- 创建 release；
- 创建 tag；
- 上传平台；
- 修改 G2/G3-A evidence；
- 执行真实 ACL/HCCL API；
- 将 staging 描述为正式提交完成。

回滚使用：

```text
git revert
```

不得重写历史、删除旧 evidence 或修改官方仓库。

# 11. G3-B2：赛前算法强化、模拟性能优化与最终代码冻结

## 11.1 阶段目标

G3-B2 位于 G3-B 和 G3-C 之间。

其目标是将当前项目从：

```text
具备稳定构建、正确性验证、模拟器 evidence 和提交工程底座
```

提升为：

```text
具有明确算法调度语义、拓扑感知优化闭环、可比较性能改进、
完整 Agent 优化 trace 和最终冻结代码基线的竞赛实现
```

G3-B2 重点解决以下问题：

1. 多种算法虽然已有名称和入口，但调度阶段、peer、chunk 和路径差异不够明确；
2. C/C++ collective 实现与 Agent、拓扑模型和 simulator 之间的调度语义尚未完全贯通；
3. 层次化、异构、非对称链路和动态故障场景仍有进一步优化空间；
4. 性能 evidence 完整，但算法优化收益和消融实验不够集中；
5. 缺少一条新的、真实、可重放、可审计的 Agent 算法优化全过程；
6. 正式报告尚未建立在最终代码冻结版本之上。

G3-B2 不追求在无真实 NPU 条件下“完全满足全部实机指标”，而是要求：

```text
当前环境中能够实现和验证的核心算法、Agent、模拟器和工程能力
达到正式参赛前可冻结的最高可信状态
```

---

## 11.2 阶段位置与后续关系

G3-B2 调整后的阶段顺序为：

```text
G3-A 赛事差距审计
→ G3-B 原生交付与可复现构建
→ G3-B2 算法强化与最终代码冻结
→ G3-C 正式技术报告
→ G3-D Agent/Prompt 专项交付
→ G3-E 图表与创新叙事
→ G3-F 演示与视频
→ G3-G 最终发布审计
```

在 G3-B2-F 最终代码冻结完成前，不应执行正式 G3-C。

G3-C 当前计划仅视为：

```text
PROVISIONAL REPORT PLAN
```

G3-B2 完成后，G3-C 必须更新：

- final source commit；
- final simulator evidence；
- final algorithm matrix；
- final benchmark evidence；
- final claim boundary；
- final Agent optimization trace；
- final plugin SHA256。

---

## 11.3 G3-B2 基线状态

G3-B2 必须继承以下状态：

```text
G3-A: COMPLETED
G3-B: COMPLETED

Native Delivery Normalization: COMPLETED
CPU_SIM Submission Plugin: COMPLETED
Direct Readiness Package: COMPLETED
Reproducible Build: BIT_FOR_BIT_REPRODUCIBLE
Submission CLI: COMPLETED
Submission Staging: COMPLETED

C/C++ Plugin Compliance: PARTIALLY_SATISFIED
Performance Target Achievement: PARTIALLY_SATISFIED
G3 Delivery Readiness: PARTIAL
Real-device Acceptance: HARDWARE_BLOCKED
```

原生产物基线继续保持：

```text
libhccl_plugin.so
  role=CPU_SIM_REFERENCE_PLUGIN
  ABI=project-local C ABI
  runtime=HOST_CPU
  official_plugin_abi=UNVERIFIED

libhccl_direct_adapter.a
  role=STATIC_BUILD_LIFECYCLE_READINESS_ARTIFACT
  runtime_api_calls=[]
```

G3-B2 默认不得修改：

- CPU_SIM 对外 collective ABI；
- direct control-plane ABI；
- CPU_SIM 与 direct 的隔离边界；
- default backend=`CPU_SIM`；
- fallback policy=`NONE`；
- 官方资产默认排除规则。

---

## 11.4 总体执行策略

G3-B2 不是一个单次大提交。

必须拆成六个顺序执行、顺序合并的子 checkpoint：

| Checkpoint | 名称                                | 核心输出                                        |
| ---------- | ----------------------------------- | ----------------------------------------------- |
| G3-B2-A    | 优化基线与 Agent trace 合约         | 冻结场景、基线结果、Prompt/trace schema         |
| G3-B2-B    | Collective Schedule IR 与 Ring 调度 | 统一 IR、Ring 三原语、C/Python parity           |
| G3-B2-C    | 分层异构拓扑感知优化                | NHR、Fat-Tree、权重路由、chunk 选择             |
| G3-B2-D    | 动态重规划、内存约束与流水重叠      | fault replan、bounded memory、simulated overlap |
| G3-B2-E    | Agent 优化闭环、消融与性能验收      | Agent proposal→benchmark→reflection→selection   |
| G3-B2-F    | 全量回归、最终代码与 evidence 冻结  | final baseline、submission integration、freeze  |

每个子 checkpoint 必须采用：

```text
独立分支
→ 独立本地 commit
→ 人工检查
→ push
→ PR
→ merge
→ 同步 main
→ 下一个子 checkpoint
```

不得使用一个 `/goal` 一次完成 G3-B2-A 至 G3-B2-F。

---

## 11.5 G3-B2 非目标

G3-B2 不负责：

- 新增 Broadcast 或 AlltoAll 作为参赛核心原语；
- 实现 FP8、INT4、稀疏梯度或量化压缩；
- 修改官方 HCOMM、HCCL 或 CANN；
- 推断未知的官方 plugin-loader ABI；
- 将 direct adapter 改写成未经验证的真实插件；
- 调用 ACL/HCCL runtime；
- 初始化真实 device/context/stream；
- 创建真实 communicator；
- 执行真实 collective；
- 运行 MPI、`hccl_test` 或 `msprof`；
- 声称真实 8→1024 卡线性加速；
- 声称真实训练加速比达到 90%；
- 声称真实 BERT/LLaMA 吞吐；
- 声称真实 100 ms failover；
- 声称真实 72 小时长稳；
- 声称真实零 CPU 介入；
- 声称真实 UB/HBM 复用；
- 通过修改硬件常量制造性能提升；
- 为展示效果删除较差结果；
- 重写已经稳定的正确性 reference；
- 修改 G2、G3-A 或 G3-B 历史 evidence；
- 编写正式 G3-C 报告；
- 制作视频或最终 release。

稀疏通信、压缩和超低精度只保留为：

```text
FUTURE_OPTIONAL_DIRECTION
```

不得在 G3-B2 中无边界扩展。

---

## 11.6 真实性边界

G3-B2 允许的结果标签：

```text
CPU_EXECUTED
SIMULATED_ONLY
AGENT_GENERATED_PROPOSAL
AGENT_SELECTED_SCHEDULE
DIRECT_READINESS_ONLY
REAL_DEVICE_NOT_EXECUTED
```

禁止生成：

```text
REAL_DEVICE_MEASURED
REAL_DEVICE_PASS
NPU_UTILIZATION_MEASURED
HCCS_BANDWIDTH_MEASURED
ROCE_BANDWIDTH_MEASURED
MSPROF_EXECUTED
REAL_TRAINING_SPEEDUP
ZERO_CPU_INTERVENTION_VERIFIED
UB_REUSE_VERIFIED
```

通信流水和内存优化只能称为：

```text
SIMULATED_PIPELINE_MODEL
BOUNDED_MEMORY_SCHEDULE
```

动态拓扑只能称为：

```text
SIMULATED_DYNAMIC_TOPOLOGY_REPLAN
```

---

# 11.7 G3-B2-A：优化基线、场景冻结与 Agent Trace 合约

## 11.7.1 目标

在任何算法、cost model 或 selector 修改前，建立不可变优化基线。

必须生成：

```text
experiments/optimization/evidence/g3_b2_a_baseline_<timestamp>/
```

该 evidence 后续不得修改。

## 11.7.2 Baseline commit

记录：

```text
baseline_commit=<G3_B_MERGED_MAIN_COMMIT>
baseline_plugin_sha256
baseline_parameter_set_sha256
baseline_config_sha256
baseline_selector_version
baseline_simulator_version
baseline_seed
```

基线必须来自合并后的 G3-B `main`，不得使用开发分支上的临时状态。

## 11.7.3 参数冻结

以下参数在 G3-B2 期间默认冻结：

- HCCS/RoCE/PCIe bandwidth；
- latency；
- BER；
- congestion coefficients；
- topology factors；
- retry coefficients；
- simulator timing formulas；
- dtype conversion rules；
- correctness tolerance；
- benchmark seed；
- baseline scenario definitions；
- p50/p95 aggregation方式。

生成：

```text
experiments/optimization/g3_b2_parameter_freeze.json
```

至少包含每个参数的：

```text
name
value
unit
source
source_path
sha256
mutable=false
```

不得通过改变参数改善优化结果。

若发现参数存在真实 bug：

1. 停止当前优化；
2. 记录 bug；
3. 单独修复；
4. 重新生成 baseline；
5. 旧 baseline 标记 `INVALIDATED_BY_BUGFIX`；
6. 不得把旧、新 baseline 混合比较。

## 11.7.4 基准场景合同

G3-B2-A 必须建立固定 benchmark contract：

```text
configs/optimization/g3_b2_benchmark_matrix.json
```

至少覆盖以下场景类别：

| 类别          | 最低覆盖                                  |
| ------------- | ----------------------------------------- |
| 小消息        | ≤64 KB                                    |
| 中消息        | 1–16 MB                                   |
| 大消息        | 128 MB                                    |
| Logical large | logical ≥1 GB                             |
| 单机拓扑      | Full Mesh 8 ranks                         |
| 环形拓扑      | Ring 8/16 ranks                           |
| 分层拓扑      | Fat-Tree 64 ranks                         |
| 异构拓扑      | asymmetric 16/64 ranks                    |
| 规模          | 8/16/64/1024 ranks                        |
| 原语          | AllReduce、AllGather、ReduceScatter       |
| 故障          | degradation、link down、no alternate path |
| dtype         | FP32、FP16、BF16                          |

基准矩阵应控制在可重复执行的规模，建议：

```text
12–20 个性能场景
3–6 个可靠性场景
```

每个场景必须记录：

```text
scenario_id
primitive
algorithm_baseline
topology
rank_size
message_size
dtype
reduce_op
seed
iteration_count
warmup_count
metric_set
weight
```

不得在看到优化结果后删除不利场景。

## 11.7.5 Baseline 输出

至少记录：

- correctness；
- p50 latency；
- p95 latency；
- effective bandwidth；
- phase count；
- modeled transferred bytes；
- critical path；
- link utilization；
- congestion events；
- peak materialized bytes；
- fault recovery status；
- selector decision；
- algorithm ranking；
- output hash。

## 11.7.6 Agent trace 合约

G3-B2-A 必须先建立新的权威 trace 结构：

```text
agent/evidence/g3_b2/
├── README.md
├── trace_manifest.json
├── prompt_registry.json
├── human_intervention.json
├── runs/
├── proposals/
├── evaluations/
├── reflections/
└── commit_mapping.json
```

每次 Agent 优化至少记录：

```text
run_id
timestamp
development_agent
runtime_agent
prompt_id
prompt_version
input_schema_version
output_schema_version
baseline_commit
input_config_sha256
proposal_sha256
human_decision
changed_files
tests
benchmark_result
reflection
selected
result_commit
```

必须明确区分：

```text
development_agent=Codex
runtime_agent=hccl-agent
human_reviewer=user
```

不得把 Codex、项目 Agent 和人工工作混为同一个主体。

## 11.7.7 Prompt 注册

新增版本化 Prompt，例如：

```text
prompts/g3_b2/
├── schedule_generation_v1.md
├── topology_optimization_v1.md
├── benchmark_evaluation_v1.md
├── reflection_v1.md
└── replanning_v1.md
```

每个 Prompt 必须包含：

- ID；
- version；
- purpose；
- input schema；
- output schema；
- guard；
- prohibited claims；
- validation requirements。

G3-B2-A 不修改算法。

## 11.7.8 分支与 commit

建议分支：

```text
codex/g3-b2-a-baseline-trace
```

建议 commit：

```text
G3-B2-A freeze optimization baseline and agent trace contract
```

---

# 11.8 G3-B2-B：Collective Schedule IR 与 Ring 三原语调度

## 11.8.1 目标

建立统一、确定性、可序列化的 collective schedule 中间表示：

```text
Collective Schedule IR
```

将当前算法表达从：

```text
algorithm name + direct host result calculation
```

提升为：

```text
algorithm
→ phases
→ transfers
→ chunks
→ reduce actions
→ barriers
→ paths
→ output ownership
```

## 11.8.2 Schedule IR schema

至少包含：

```text
schema_version
schedule_id
primitive
algorithm
rank_size
message_size_bytes
dtype
reduce_op
topology_hash
hardware_profile_hash
chunk_size_bytes
chunk_count
phases
dependencies
memory_plan
failure_policy
estimated_metrics
schedule_hash
```

每个 phase 至少包含：

```text
phase_id
phase_type
transfers
reductions
barrier
depends_on
```

每个 transfer 至少包含：

```text
src_rank
dst_rank
chunk_id
element_offset
element_count
route
link_type
operation
```

Schedule 必须使用 canonical JSON 序列化并生成稳定 SHA256。

## 11.8.3 Schedule invariants

必须验证：

1. rank 范围合法；
2. chunk 范围合法；
3. phase dependency 无环；
4. 每个必要 chunk 都被覆盖；
5. 不存在非法重复 writer；
6. reduce 参与 rank 完整；
7. AllGather 输出 rank ordering 正确；
8. ReduceScatter ownership 正确；
9. AllReduce 每个 rank 获得完整结果；
10. barrier 和 phase 顺序确定；
11. 相同输入生成相同 schedule hash；
12. 不支持的组合明确返回结构化错误。

## 11.8.4 Ring schedule

必须至少实现：

```text
Ring AllReduce
Ring AllGather
Ring ReduceScatter
```

Ring AllReduce 必须表现为明确的：

```text
ReduceScatter stages
+
AllGather stages
```

不能只调用统一 reduction reference 后返回结果。

必须记录并验证：

- phase count；
- chunk owner；
- left/right peer；
- per-phase transfer；
- final coverage；
- rank rotation；
- N=2、4、8、16、64；
- 非整除 message/chunk 边界。

## 11.8.5 C/C++ 调度实现

建议新增或复用等价结构：

```text
hcccl/src/hccl_schedule.c
hcccl/src/hccl_schedule_ring.c
hcccl/include/internal/hccl_schedule_internal.h
hcccl/tests/test_schedule_ring.c
```

要求：

- 现有 public collective ABI 默认不变；
- schedule 为内部实现；
- 不增加未经批准的 public exported symbol；
- 现有 19-symbol allowlist 默认保持；
- C collective 函数必须通过对应 schedule 路径执行 host 模拟语义；
- reference kernel 只用于结果校验，不再是所有算法唯一调度实现。

## 11.8.6 Python Schedule IR

建议新增或复用等价模块：

```text
schedule/
├── schema.py
├── ir.py
├── validators.py
├── canonical.py
└── generators/
    └── ring.py
```

不得复制形成不一致的第二套语义。

## 11.8.7 C/Python parity

必须提供 test-only schedule dump 或等价方式，比较：

- primitive；
- phase count；
- peer；
- chunk ownership；
- transferred bytes；
- schedule hash 或规范化内容。

若 C 与 Python 不能生成完全相同的 JSON，至少必须通过结构 parity 和 invariant parity。

test-only 工具不得成为新增 public plugin ABI。

## 11.8.8 分支与 commit

建议分支：

```text
codex/g3-b2-b-collective-schedule-ir
```

建议 commit：

```text
G3-B2-B add collective schedule IR and ring primitive schedules
```

---

# 11.9 G3-B2-C：分层、异构与拓扑感知算法优化

## 11.9.1 主创新方向

G3-B2 的主创新方向冻结为：

```text
拓扑感知的分层非均匀集合通信调度
```

英文工作名称可使用：

```text
Topology-Aware Hierarchical Non-Uniform Collective Scheduling
```

不得同时再建立多个互不相关的“主创新”。

## 11.9.2 支持算法矩阵

最低支持范围：

| Algorithm             | AllReduce | AllGather   | ReduceScatter        |
| --------------------- | --------- | ----------- | -------------------- |
| Ring                  | REQUIRED  | REQUIRED    | REQUIRED             |
| Butterfly             | REQUIRED  | REQUIRED    | OPTIONAL/UNSUPPORTED |
| Mesh                  | REQUIRED  | OPTIONAL    | REQUIRED             |
| NHR                   | REQUIRED  | UNSUPPORTED | UNSUPPORTED          |
| Fat-Tree/Hierarchical | REQUIRED  | OPTIONAL    | OPTIONAL             |

未实现的组合必须返回：

```text
UNSUPPORTED_ALGORITHM_PRIMITIVE_PAIR
```

不得静默 fallback。

## 11.9.3 Butterfly

必须形成明确 recursive-doubling schedule：

- `log2(N)` phase；
- partner calculation；
- power-of-two 条件；
- 非 power-of-two 时明确拒绝或使用有记录的独立策略；
- AllReduce 与 AllGather transfer/reduction 差异；
- deterministic peer order。

不得把 Butterfly 仅实现为不同名称的 Ring。

## 11.9.4 NHR

NHR 至少必须：

- 读取链路权重；
- 对非对称链路进行 rank ordering；
- 避免将主要流量集中到最慢链路；
- 输出 non-uniform ring order；
- 输出每段估计代价；
- 对比普通 Ring；
- 记录拓扑假设；
- 在对称拓扑下退化为可解释的普通环或等价顺序。

链路权重建议由以下项组成：

```text
latency_cost
+ transfer_bytes / effective_bandwidth
+ congestion_penalty
+ reliability_penalty
```

权重公式和常量必须来自冻结模型，不得为单一场景人工调参。

## 11.9.5 Fat-Tree/Hierarchical

至少实现清晰的分层 AllReduce：

```text
intra-group reduce/reduce-scatter
→ inter-group leader collective
→ intra-group distribute/allgather
```

必须明确：

- group 划分来源；
- leader 选择；
- intra/inter link；
- phase dependency；
- cross-node traffic；
- group size；
- oversubscription；
- fallback condition；
- no valid hierarchy condition。

不得通过 rank ID 整除关系无依据推断真实节点；必须读取 topology/node metadata。

## 11.9.6 Mesh

Mesh 调度必须：

- 显式表达 peer transfer；
- 检测共享链路冲突；
- 控制并行 fan-out；
- 支持分块；
- 避免所有 rank 在同一 phase 无约束全发；
- 在 Full Mesh 和非 Full Mesh 上使用不同约束。

## 11.9.7 Chunk 自适应

Chunk 候选必须来自有限、版本化集合，例如：

```text
64 KB
256 KB
1 MB
4 MB
16 MB
```

实际集合应结合现有 memory budget 冻结。

选择输入：

- message size；
- rank size；
- topology depth；
- link bandwidth；
- link latency；
- concurrency；
- memory limit。

选择输出：

```text
chunk_size
chunk_count
pipeline_depth
selection_reason
candidate_scores
```

不得使用无界搜索或针对最终 benchmark 单独硬编码。

## 11.9.8 拥塞模型

Schedule cost 至少考虑：

- 同一链路并发传输；
- oversubscribed parent edge；
- cross-group traffic；
- concurrent transfer count；
- queue delay；
- critical path。

必须保留：

```text
base_link_time
congestion_penalty
final_link_time
```

以便后续报告消融。

## 11.9.9 Selector 集成

Agent/selector 必须基于显式候选 schedule，而不是只返回算法名称。

输出至少包含：

```text
selected_algorithm
selected_schedule_hash
selection_reason
candidate_algorithms
candidate_schedule_hashes
candidate_scores
rejected_reasons
```

fallback 必须继续为：

```text
NONE
```

## 11.9.10 分支与 commit

建议分支：

```text
codex/g3-b2-c-topology-aware-hierarchical
```

建议 commit：

```text
G3-B2-C add topology-aware hierarchical collective optimization
```

---

# 11.10 G3-B2-D：动态重规划、有界内存与模拟流水重叠

## 11.10.1 动态重规划

当 topology event 发生时，系统必须：

1. 标记受影响链路或 rank；
2. 使旧 schedule 失效；
3. 保存旧 schedule hash；
4. 重新生成候选 schedule；
5. 验证新 schedule invariants；
6. 重新执行 correctness gate；
7. 输出新 schedule hash；
8. 记录 replan latency；
9. 无路径时返回明确失败。

事件至少覆盖：

```text
LINK_DEGRADED
LINK_DOWN
LINK_RECOVERED
RANK_REMOVED
RANK_RECOVERED
NO_ALTERNATE_PATH
```

`RANK_RECOVERED` 可以只在 simulator/control-plane 中支持，不得声称真实训练不中断。

## 11.10.2 Replan trace

至少记录：

```text
event_id
event_type
old_topology_hash
new_topology_hash
old_schedule_hash
new_schedule_hash
affected_links
candidate_count
selected_algorithm
replan_reason
simulated_replan_time_ms
correctness_after_replan
final_status
```

## 11.10.3 有界内存

每个 schedule 必须输出：

```text
logical_message_bytes
materialized_bytes
chunk_buffer_bytes
temporary_buffer_bytes
peak_materialized_bytes
memory_budget_bytes
within_budget
```

对于 logical ≥1 GB：

- 不得实际无界物化；
- 必须继续使用 bounded materialization；
- schedule chunk 必须满足 memory budget；
- 报告 logical 与 physical materialization 的差异。

## 11.10.4 Pipeline 模型

增加两个明确模式：

```text
NO_OVERLAP
SIMULATED_PIPELINED_OVERLAP
```

流水模型至少包含：

```text
pipeline_depth
fill_time
steady_state_time
drain_time
communication_slots
modeled_compute_slots
overlap_ratio
critical_path
```

该模型只能用于 simulator。

不得增加以下声明：

```text
真实 Ascend stream overlap
真实计算核并行
真实 UB/HBM reuse
真实零 CPU 介入
```

## 11.10.5 可靠性约束

动态重规划后必须重新进行：

- output correctness；
- output hash；
- rank ordering；
- no duplicate transfer；
- no missing chunk；
- route validity；
- bounded memory。

若无替代路径，应返回：

```text
EXPECTED_NO_PATH_FAILURE
```

不得用 fallback 到未记录算法掩盖失败。

## 11.10.6 分支与 commit

建议分支：

```text
codex/g3-b2-d-replan-memory-pipeline
```

建议 commit：

```text
G3-B2-D add dynamic schedule replanning and bounded pipeline model
```

---

# 11.11 G3-B2-E：Agent 优化闭环、消融实验与性能验收

## 11.11.1 目标

建立一条新的、权威的、可重放的 Agent 优化流程：

```text
输入 topology/workload
→ Agent 分析
→ 候选 schedule 生成
→ correctness gate
→ benchmark
→ evaluation
→ reflection
→ replanning
→ final selection
→ commit mapping
```

该流程不得补写或伪造历史记录。

## 11.11.2 Agent 输入

至少包含：

```text
primitive
message_size
rank_size
dtype
reduce_op
topology
hardware_profile
memory_budget
reliability_state
optimization_objective
baseline_schedule
```

## 11.11.3 Agent 输出

必须是结构化 proposal：

```text
proposal_id
algorithm
schedule_parameters
chunk_size
pipeline_depth
routing_policy
expected_benefit
expected_risk
unsupported_conditions
required_tests
```

不得只输出自然语言推荐。

## 11.11.4 优化目标

使用多目标评分，至少包含：

```text
p50 latency
p95 latency
effective bandwidth
peak memory
congestion penalty
reliability penalty
correctness gate
```

正确性必须是硬门槛：

```text
correctness_gate=false
→ candidate rejected
```

不得通过性能分数覆盖正确性失败。

## 11.11.5 消融实验

至少比较：

```text
A0: 固定 Ring baseline
A1: G3-B 原 selector
A2: Schedule IR only
A3: + topology weighting
A4: + adaptive chunking
A5: + congestion-aware scheduling
A6: + dynamic replan
A7: + simulated pipeline overlap
```

每个阶段必须使用相同：

- parameter hash；
- benchmark matrix；
- seed；
- iteration；
- warmup；
- correctness规则。

## 11.11.6 结果报告

必须完整报告：

```text
wins
ties
losses
```

不得只显示获胜场景。

每个场景至少记录：

```text
baseline
candidate
absolute_difference
relative_difference
p50
p95
bandwidth
memory
phase_count
schedule_hash
correctness
```

## 11.11.7 默认性能验收门槛

在不修改冻结性能参数的前提下，默认要求：

1. 全部 correctness gate 通过；
2. 目标场景加权模拟时间几何均值改善不少于 8%；
3. 分层/异构重点场景中至少 4 个改善不少于 10%；
4. 不超过 2 个场景回退超过 5%；
5. 任一关键正确性或可靠性场景不得回退；
6. logical 1024-rank 代表场景不得回退超过 3%；
7. peak materialized memory 不得突破预算；
8. no-path 语义保持正确；
9. p50 改善不能以严重恶化 p95 为代价；
10. 改善必须来自 schedule/selection/chunk/replan，而非模型常量变化。

这些门槛是 G3-B2 内部工程验收门槛，不等价于赛题的真实 90% 训练加速目标。

## 11.11.8 未达到门槛时

不得反复调整 benchmark 或参数。

应：

- 保留完整结果；
- 识别失败原因；
- 最多进行两轮有依据的算法修正；
- 仍未达到时将对应项标记 `PARTIAL`；
- 选择无正确性回退且综合最稳定的实现；
- 不伪造优化成功。

## 11.11.9 Agent trace 输出

必须冻结：

```text
agent/evidence/g3_b2/runs/
agent/evidence/g3_b2/proposals/
agent/evidence/g3_b2/evaluations/
agent/evidence/g3_b2/reflections/
agent/evidence/g3_b2/commit_mapping.json
```

至少包含一条完整成功或真实失败的优化链。

## 11.11.10 分支与 commit

建议分支：

```text
codex/g3-b2-e-agent-optimization-audit
```

建议 commit：

```text
G3-B2-E complete agent optimization loop and ablation audit
```

---

# 11.12 G3-B2-F：全量回归、最终代码冻结与 Submission 集成

## 11.12.1 目标

完成 G3-B2 最终审计，选择唯一 final algorithm baseline，并冻结供 G3-C 使用的代码和 evidence。

## 11.12.2 最终冻结内容

必须生成：

```text
docs/submission/g3_b2_final_code_baseline.md
experiments/optimization/g3_b2_final_baseline.json
```

至少记录：

```text
final_source_commit
final_algorithm_version
final_schedule_schema_version
final_selector_version
final_simulator_version
final_parameter_set_sha256
final_benchmark_matrix_sha256
final_plugin_sha256
final_public_abi_version
final_exported_symbols
final_evidence_path
```

## 11.12.3 ABI 规则

默认要求：

```text
CPU_SIM public ABI unchanged
19-symbol export allowlist unchanged
```

如果确需修改 public ABI：

1. 必须提前停止；
2. 单独提交 ABI change proposal；
3. 获得用户批准；
4. 提升 ABI version；
5. 更新 G3-B manifest；
6. 重跑双构建；
7. 更新 consumer tests；
8. 更新 claim boundary。

不得在 G3-B2-F 隐式修改 ABI。

## 11.12.4 全量回归

至少运行：

- G3-B submission `check`；
- `quick`；
- `full`；
- CPU_SIM 双 clean build；
- CTest；
- Python全量或 submission-relevant 全量；
- installed header consumer；
- installed CMake consumer；
- ABI/symbol/dependency audit；
- schedule invariant suite；
- C/Python parity；
- three primitives；
- FP32/FP16/BF16；
- fault replan；
- bounded memory；
- benchmark contract；
- ablation；
- staging；
- staging verify；
- previous evidence SHA256。

不得重写旧 evidence。

## 11.12.5 Final benchmark evidence

只保留一份权威 final evidence：

```text
experiments/optimization/evidence/g3_b2_f_final_<timestamp>/
```

至少包含：

```text
README.md
manifest.json
result.json
baseline_reference.json
parameter_freeze.json
benchmark_contract.json
algorithm_support_matrix.json
schedule_schema.json
schedule_inventory.json
schedule_invariant_audit.json
c_python_parity_audit.json
correctness_summary.json
performance_summary.json
scale_summary.json
memory_summary.json
pipeline_summary.json
reliability_summary.json
replan_trace.jsonl
ablation_summary.json
wins_ties_losses.json
agent_trace_inventory.json
human_intervention.json
commit_mapping.json
submission_regression.json
claim_boundary_audit.json
SHA256SUMS
```

## 11.12.6 Submission CLI 集成

G3-B2-F 必须更新 G3-B submission workflow，使：

```text
python -m tools.submission_cli quick
```

至少增加轻量：

- schedule invariant；
- representative schedule trace；
- Agent selector output；
- topology-aware comparison。

`full` 增加：

- final benchmark contract；
- C/Python parity；
- bounded-memory audit；
- G3-B2 final evidence validation。

不得让 quick 变成长时间完整 benchmark。

## 11.12.7 Staging 集成

staging 至少新增：

```text
algorithm/
├── schedule_schema.json
├── algorithm_support_matrix.json
├── examples/
└── README.md

agent/evidence/g3_b2/
optimization/
├── baseline_summary.json
├── final_summary.json
├── ablation_summary.json
└── claim_boundaries.md
```

不得包含：

- 临时优化目录；
- 未选中的大量中间 build；
- 私密 Codex原始缓存；
- 未脱敏日志；
- 官方二进制；
- 受控赛题文件。

## 11.12.8 分支与 commit

建议分支：

```text
codex/g3-b2-f-final-code-freeze
```

建议 commit：

```text
G3-B2-F freeze optimized algorithm baseline and final evidence
```

---

# 11.13 建议代码结构

具体路径应优先复用现有模块，避免重复体系。

若仓库没有适合结构，可参考：

```text
schedule/
├── schema.py
├── ir.py
├── canonical.py
├── validators.py
├── cost.py
├── executor.py
└── generators/
    ├── ring.py
    ├── butterfly.py
    ├── mesh.py
    ├── nhr.py
    └── hierarchical.py

hcccl/
├── include/internal/
│   └── hccl_schedule_internal.h
├── src/
│   ├── hccl_schedule.c
│   ├── hccl_schedule_ring.c
│   ├── hccl_schedule_butterfly.c
│   ├── hccl_schedule_mesh.c
│   ├── hccl_schedule_nhr.c
│   └── hccl_schedule_hierarchical.c
├── tools/
│   └── hccl_schedule_dump.c
└── tests/
    ├── test_schedule_ring.c
    ├── test_schedule_butterfly.c
    ├── test_schedule_hierarchical.c
    └── test_schedule_invariants.c

skills/
└── schedule_optimization_skill.py

tools/
└── optimization_cli/
```

不得为了符合建议结构大规模移动现有稳定代码。

---

# 11.14 测试要求

## 11.14.1 Schedule schema

1. schema version；
2. canonical serialization；
3. stable schedule hash；
4. invalid rank rejection；
5. invalid chunk rejection；
6. cyclic dependency rejection；
7. missing chunk detection；
8. duplicate writer detection；
9. output ownership；
10. deterministic replay。

## 11.14.2 Ring

11. AllReduce phase count；
12. AllGather phase count；
13. ReduceScatter phase count；
14. rank rotation；
15. chunk ownership；
16. non-divisible count；
17. rank 2/4/8/16/64；
18. three dtype representative cases。

## 11.14.3 Other algorithms

19. Butterfly partner；
20. Butterfly power-of-two boundary；
21. Mesh conflict control；
22. NHR weighted order；
23. NHR symmetric fallback；
24. Fat-Tree group partition；
25. leader selection；
26. inter/intra phases；
27. unsupported pair rejection。

## 11.14.4 Topology and cost

28. asymmetric link weighting；
29. congestion penalty；
30. oversubscription；
31. critical path；
32. chunk candidate search；
33. memory-budget rejection；
34. parameter hash unchanged。

## 11.14.5 Dynamic replan

35. degradation replan；
36. link-down replan；
37. recovery replan；
38. rank removal；
39. no alternate path；
40. schedule hash change；
41. correctness after replan；
42. bounded memory after replan。

## 11.14.6 Agent

43. Prompt version；
44. input schema；
45. proposal schema；
46. correctness hard gate；
47. evaluation；
48. reflection；
49. replanning；
50. commit mapping；
51. human intervention disclosure；
52. trace sanitization。

## 11.14.7 Performance and regression

53. benchmark contract immutable；
54. baseline source commit；
55. p50/p95 separation；
56. wins/ties/losses completeness；
57. ablation completeness；
58. no hidden parameter changes；
59. CPU_SIM CTest；
60. Python regression；
61. native ABI unchanged；
62. bit-for-bit rebuild；
63. G3-B quick/full；
64. staging verify；
65. old evidence SHA256；
66. HCOMM/HCCL tracked clean。

不得通过新增无理由 skip 通过测试。

---

# 11.15 文档输出

G3-B2 至少新增：

```text
docs/optimization/g3_b2_baseline.md
docs/optimization/collective_schedule_ir.md
docs/optimization/algorithm_support_matrix.md
docs/optimization/topology_aware_hierarchical_design.md
docs/optimization/chunk_and_pipeline_design.md
docs/optimization/dynamic_replanning_design.md
docs/optimization/g3_b2_ablation_report.md
docs/optimization/g3_b2_final_code_baseline.md
docs/optimization/g3_b2_known_limitations.md
```

这些是工程和优化文档，不是 G3-C 最终正式报告。

---

# 11.16 Requirement 增量评估

不得修改 G3-A 历史 requirement matrix。

G3-B2-F 必须生成：

```text
docs/submission/g3_b2_requirement_delta.json
```

可能改善的要求包括：

```text
REQ-INNOV-001
REQ-INNOV-002
REQ-INNOV-005
REQ-SCALE-002
REQ-TOPO-005
REQ-REL-003
REQ-AGENT-005
REQ-AGENT-006
REQ-AGENT-007
```

状态只能根据实际 evidence 建议更新。

以下要求仍不能因模拟优化自动变为满足：

```text
真实硬件探测
真实零 CPU 介入
真实 UB/HBM 复用
真实训练 90% 加速
真实 msprof
真实故障切换
真实 72h
官方 loader ABI
```

---

# 11.17 G3-B2 最终 Evidence

G3-B2-F final evidence 必须记录：

```text
checkpoint=G3-B2
checkpoint_status=COMPLETED|PARTIAL

schedule_ir=COMPLETED
ring_three_primitive_schedule=COMPLETED
topology_aware_optimization=COMPLETED
hierarchical_schedule=COMPLETED
dynamic_replanning=COMPLETED
bounded_memory_schedule=COMPLETED
simulated_pipeline_model=COMPLETED
agent_optimization_trace=COMPLETED
final_code_freeze=COMPLETED

performance_target_achievement=PARTIALLY_SATISFIED
c_cpp_plugin_compliance=PARTIALLY_SATISFIED
real_device_acceptance=HARDWARE_BLOCKED
g3_delivery_readiness=PARTIAL

real_device_api_executed=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
measured_on_real_npu=false
msprof_executed=false
real_model_executed=false
runtime_api_calls=[]
old_evidence_modified=false
parameter_set_modified=false
```

如果参数发生获批 bugfix，则：

```text
parameter_set_modified=true
baseline_regenerated=true
old_baseline_invalidated=true
```

---

# 11.18 完成条件

只有以下条件全部满足时，G3-B2 才可标记 `COMPLETED`：

- 优化 baseline 已冻结；
- benchmark contract 已冻结；
- parameter set 未被隐式修改；
- Agent trace schema 已建立；
- Prompt 已版本化；
- Schedule IR 已完成；
- canonical schedule hash 可用；
- schedule invariants 全部通过；
- Ring 三原语具有明确不同调度；
- 至少 Butterfly、NHR、Fat-Tree 中两个具有独立调度；
- C/Python schedule parity 通过；
- Agent selector 输出 schedule 而非仅算法名称；
- 非对称拓扑权重生效；
- chunk 自适应生效；
- 拥塞代价可追溯；
- dynamic replan 生效；
- no-path 语义保持；
- bounded-memory audit 通过；
- simulated pipeline 明确标记；
- correctness 无回退；
- 完整 wins/ties/losses 已输出；
- 消融实验完整；
- 默认性能验收门槛达到，或真实记录为 `PARTIAL`；
- 至少一条完整 Agent 优化 trace 可重放；
- 人工干预已披露；
- commit mapping 完整；
- CPU_SIM public ABI 未意外变化；
- G3-B quick/full 通过；
- 双构建可复现；
- staging verify 通过；
- 所有旧 evidence 未修改；
- G3-B2 final evidence SHA256 通过；
- HCOMM/HCCL tracked clean；
- 工作区 clean；
- 未执行真实设备 API；
- 未开始正式 G3-C；
- 未创建 release。

最终状态应为：

```text
G3-B2: COMPLETED
Optimization Baseline: COMPLETED
Collective Schedule IR: COMPLETED
Ring Three-Primitive Scheduling: COMPLETED
Topology-Aware Hierarchical Optimization: COMPLETED
Dynamic Schedule Replanning: COMPLETED
Bounded-Memory Scheduling: COMPLETED
Simulated Pipeline Model: COMPLETED
Agent Optimization Trace: COMPLETED
Ablation and Benchmark Audit: COMPLETED
Final Code Baseline: FROZEN

Performance Target Achievement: PARTIALLY_SATISFIED
C/C++ Plugin Compliance: PARTIALLY_SATISFIED
Submission Release Readiness: PARTIAL
G3 Delivery Readiness: PARTIAL
Real-device Acceptance: HARDWARE_BLOCKED
```

---

# 11.19 阻塞与失败分类

## ENV_BLOCKED

适用于：

- baseline 无法运行；
- C/C++ build 失败；
- schedule parity 工具不可运行；
- benchmark evidence 不可读取；
- submission CLI 失效；
- Python/CMake 环境损坏。

## USER_ACTION_REQUIRED

适用于：

- 是否批准 public ABI 变化；
- 是否允许改变冻结 parameter set；
- 是否接受未达到默认性能门槛的 final candidate；
- 是否扩展 G3-B2 时间；
- 是否增加稀疏/压缩可选功能。

## HARDWARE_BLOCKED

只适用于：

- 真实 NPU；
- 真实 HCCS/RoCE/PCIe；
- 真实 communicator；
- 真实 collective；
- 真实训练；
- 真实 msprof；
- 真实 failover；
- 真实 72h；
- 真实 direct acceptance。

## FAIL

适用于：

- baseline 在优化后被覆盖；
- benchmark 场景被事后删除；
- 参数被隐式修改；
- schedule 不能保证正确性；
- 不同算法仍使用同一伪调度；
- C/Python 语义漂移；
- 性能数据选择性报告；
- p50/p95 混淆；
- no-path 被隐式 fallback；
- Agent trace 被事后伪造；
- 人工介入未披露；
- ABI 意外变化；
- staging 或 evidence SHA256 失败；
- 模拟结果被写成实机；
- 旧 evidence 被修改。

不得将算法、测试或性能失败错误标记为 `HARDWARE_BLOCKED`。

---

# 11.20 停止边界与代码冻结

G3-B2-F commit 合并进入 `main` 后，项目进入：

```text
FINAL ALGORITHM CODE FREEZE
```

此后除以下情况外不得修改：

- 阻塞性 correctness bug；
- 构建失败；
- 安全或隐私问题；
- 报告发现的数据追溯错误；
- 平台明确要求的兼容修复。

默认冻结：

- algorithm schedule；
- topology semantics；
- cost model；
- parameter set；
- selector；
- chunk policy；
- pipeline model；
- benchmark matrix；
- correctness threshold；
- performance evidence；
- plugin ABI。

任何冻结后修改必须：

1. 单独 issue/记录；
2. 说明影响；
3. 重跑受影响 evidence；
4. 更新 G3-C ledger；
5. 更新 claim boundary；
6. 不得静默修改。

G3-B2-F 完成并合并后，下一阶段才是：

```text
G3-C：证据驱动的正式技术报告体系
```
