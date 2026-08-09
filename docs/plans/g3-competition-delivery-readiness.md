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
G3-B3：赛题关键功能补齐、可靠性深化与官方接口代码化
```

# 12. G3-B3：赛题关键功能补齐、可靠性深化与官方接口代码化

## 12.1 阶段定位

G3-B3 是项目进入正式技术报告、演示和最终交付前的最后一次功能增强阶段。

阶段性质：

```text
FINAL FEATURE ENHANCEMENT
```

G3-B3 不再以提高 G3-B2 已冻结的 45.59283008% 模拟性能改善为主要目标，也不继续无边界增加算法数量。

核心目标是补齐当前仍然具有明显比赛价值、且能够在无真实 Ascend NPU 条件下真实实现和验证的代码能力：

1. Lossless sparsity-aware communication；
2. C/C++ 数据完整性校验；
3. bounded timeout/retry；
4. credit-based flow control / backpressure；
5. Agent / Schedule / Cost Model 对 sparse 与 reliability 的统一集成；
6. 官方 ACL/HCCL API 的 compile/link-only production source path；
7. 最终 Feature Freeze。

G3-B3 完成后：

```text
不得再创建 G3-B4 或其他常规功能开发阶段。
```

除阻塞性 bug、比赛平台兼容问题或真实性错误外，代码进入：

```text
FINAL FEATURE FREEZE
```

然后正式进入 G3-C。

---

# 12.2 G3-B3 目标状态

G3-B3 的目标不是：

```text
“让所有赛题项全部 SATISFIED”
```

因为以下能力仍然无法在当前环境中完成真实验收：

- 真实 Ascend NPU；
- 真实 ACL runtime；
- 真实 HCCL communicator；
- 真实 HCCL collective；
- 官方 plugin-loader 实机验收；
- 真实 HCCS/RoCE/PCIe 指标；
- 真实 sparse wire-byte；
- 真实 quantized communication；
- 真实 msprof；
- 真实 failover；
- 真实 72h；
- 真实训练吞吐；
- 真实 90% 训练加速；
- 真实 zero-CPU；
- 真实 UB/HBM reuse。

G3-B3 的目标是：

```text
在不制造任何真实硬件声明的前提下，
将当前环境能够实现和验证的赛题关键能力补到最终提交级别。
```

---

# 12.3 G3-B3 前置基线

开始前必须继承已合并的 G3-B2 Final Code Baseline。

当前权威状态：

```text
G3-B2: COMPLETED
Final Code Baseline: FROZEN

default_backend=CPU_SIM
fallback_policy=NONE

libhccl_plugin.so
  role=CPU_SIM_REFERENCE_PLUGIN

public_abi=g3-b-cpu-sim-abi-v1
SONAME=libhccl_plugin.so
export_allowlist_count=19

direct artifact
  role=STATIC BUILD/LIFECYCLE READINESS ARTIFACT

performance_target_achievement=PARTIALLY_SATISFIED
real_device_acceptance=HARDWARE_BLOCKED
```

G3-B3 必须继承：

```text
G3-B2 benchmark matrix
G3-B2 parameter freeze
G3-B2 Schedule IR v1
G3-B2 selector
G3-B2 simulator semantics
G3-B2 final evidence
```

作为不可修改历史基线。

不得修改任何：

```text
G2
G3-A
G3-B
G3-B2
```

历史 authority evidence。

---

# 12.4 冻结契约

以下 ELF/public contract 在整个 G3-B3 中继续冻结：

```text
libhccl_plugin.so identity
public ABI
SONAME
19-symbol export allowlist
CPU_SIM/direct isolation
default backend
fallback policy
```

默认不得：

- 新增 public C symbol；
- 删除 public C symbol；
- 修改现有函数签名；
- 修改 public struct 大小；
- 修改 enum 既有数值；
- 修改 SONAME；
- 将 CANN/HCCL dependency 链接入 CPU_SIM plugin；
- 改变 CPU_SIM plugin 的 host-only 身份。

内部实现允许变化：

- private C/C++ structs；
- internal helpers；
- Schedule IR；
- Agent proposal schema；
- cost-model metadata；
- simulator metadata；
- internal test-only interfaces。

---

# 12.5 Schedule Contract 版本策略

G3-B2 已冻结：

```text
g3-b2-schedule-ir-v1
```

G3-B3 不允许原地改变 v1 的语义。

必须新增：

```text
g3-b3-schedule-ir-v2
```

并保持：

```text
v1 historical evidence remains valid
v2 used only for G3-B3+
```

v2 必须向后兼容当前 dense schedule 的核心语义。

同理，Agent proposal schema 应进行版本升级，例如：

```text
g3-b3-agent-proposal-v2
```

不得静默改变 G3-B2 trace 的解释规则。

---

# 12.6 G3-B3 总体 checkpoint

G3-B3 拆分为六个内部阶段：

| Checkpoint | 名称                                          | 核心目标                                           |
| ---------- | --------------------------------------------- | -------------------------------------------------- |
| G3-B3-A    | Contract v2 与增量基线冻结                    | IR v2、Agent schema v2、新 benchmark/data profiles |
| G3-B3-B    | Lossless Sparse Integrated Path               | detector、codec、reconstruct、dense fallback       |
| G3-B3-C    | C/C++ Integrity 与 Retry                      | CRC32、sequence、corruption、timeout/retry         |
| G3-B3-D    | Wire-aware Selector、Agent 与 Backpressure    | wire cost、credit flow、Agent闭环、消融            |
| G3-B3-E    | Official API Compile/Link-only Runtime Source | 真实官方 API 调用表达式，仅编译链接                |
| G3-B3-F    | Final Validation 与 Feature Freeze            | 全量回归、新 evidence、最终冻结                    |

执行方式可采用：

```text
一个功能分支
一个 /goal
六个阶段性 commit
```

但必须严格按照 A→F 顺序执行。

---

# 12.7 G3-B3 非目标

G3-B3 明确不做：

## Collective 扩张

不新增：

```text
AlltoAll
```

不深化：

```text
Broadcast
```

Broadcast 已存在 public symbol，但不属于当前最高价值缺口。

AlltoAll 会引入新的 public/API/semantic/test/benchmark 面，当前不值得重新打开冻结接口。

---

## 算法扩张

默认不新增：

```text
PairWise
```

PairWise 仅保留 OPTIONAL gate。

只有现有 tiny-message benchmark 能证明：

```text
Ring/Butterfly candidate set 存在可量化缺口
```

时才允许作为 internal Schedule candidate 实现。

不得新增 public PairWise API。

---

## 量化压缩

默认不实现：

```text
FP8
INT4
```

BF16→INT8 只作为 OPTIONAL research path。

不得让 INT8 阻塞 G3-B3 完成。

---

## 性能调参

禁止继续围绕：

```text
45.59283008%
```

进行无边界性能优化。

不得修改 G3-B2：

- 18 个性能 benchmark；
- 4 个 reliability benchmark；
- frozen seed；
- topology；
- hardware constants；
- statistics；
- G3-B2 performance formulas。

G3-B3 新功能使用独立增量 benchmark。

---

# 12.8 真实性标签

G3-B3 允许使用：

```text
HOST_EXECUTED
CPU_EXECUTED
SIMULATED_ONLY
LOSSLESS_SPARSE_HOST_EXECUTED
HOST_INTEGRITY_VALIDATED
HOST_RETRY_VALIDATED
SIMULATED_BACKPRESSURE
DIRECT_READINESS_ONLY
DIRECT_COMPILE_LINK_ONLY
REAL_DEVICE_NOT_EXECUTED
```

不得使用：

```text
REAL_DEVICE_PASS
REAL_DEVICE_MEASURED
DIRECT_RUNTIME_EXECUTED
DIRECT_HCCL_API_EXECUTED
REAL_SPARSE_SPEEDUP
REAL_WIRE_COMPRESSION
REAL_NPU_BANDWIDTH
MSPROF_EXECUTED
ZERO_CPU_INTERVENTION_VERIFIED
UB_HBM_REUSE_VERIFIED
REAL_FAILOVER_VERIFIED
```

特别注意：

```text
源码中出现 HcclAllReduce(...)
```

不等于：

```text
direct_hccl_api_call=true
```

后者只能表示运行时真正执行过 API。

G3-B3-E 的正确标签必须是：

```text
DIRECT_COMPILE_LINK_ONLY
runtime_api_calls=[]
```

---

# 12.9 G3-B3-A：Contract v2、Sparse 基线与增量 Benchmark Freeze

## 12.9.1 目标

在任何 sparse、CRC、retry、flow-control 或 direct production source 修改之前：

1. 建立 Schedule IR v2；
2. 建立 Agent proposal v2；
3. 冻结 G3-B3 数据 profile；
4. 冻结 G3-B3 benchmark contract；
5. 生成 G3-B3 增量 baseline；
6. 保留 G3-B2 baseline 不变；
7. 建立 G3-B3 truth/claim contract。

---

# 12.9.2 G3-B2 基线不可修改

必须验证：

```text
G3-B2 benchmark SHA256
G3-B2 parameter SHA256
G3-B2 final evidence SHA256
```

仍有效。

新增 G3-B3 baseline 必须独立存放：

```text
experiments/feature_completion/evidence/
    g3_b3_a_baseline_<timestamp>/
```

不得覆盖：

```text
experiments/optimization/evidence/g3_b2_*
```

---

# 12.9.3 Schedule IR v2

建议新增字段：

```text
schema_version
payload_transform
integrity_policy
transport_policy
flow_control_policy
```

其中 `payload_transform` 至少包含：

```text
mode
codec
logical_bytes
wire_bytes
value_bytes
index_bytes
metadata_bytes
compression_ratio
sparsity_ratio
eligibility
fallback_reason
```

允许 mode：

```text
DENSE
SPARSE_INDEX_VALUE
```

初始不得加入：

```text
LOSSY_INT8
FP8
INT4
```

作为正式路径。

---

## integrity_policy

至少：

```text
checksum_type
sequence_enabled
chunk_id_enabled
attempt_tracking
verify_before_accept
```

checksum type 初始：

```text
NONE
CRC32
```

parity 可以后续加入：

```text
CRC32_PLUS_PARITY
```

但不得代替 CRC32。

---

## transport_policy

至少：

```text
timeout_enabled
logical_timeout_ticks
max_retries
retry_backoff_policy
retryable_error_classes
terminal_error_classes
```

测试不得依赖 wall-clock sleep。

使用逻辑时钟或确定性事件。

---

## flow_control_policy

至少：

```text
enabled
credit_window
max_inflight_chunks
high_watermark
low_watermark
```

不得声称真实 NIC credit flow control。

---

# 12.9.4 Agent Proposal v2

至少增加：

```text
data_profile
sparsity_ratio
payload_transform
codec
estimated_wire_bytes
metadata_overhead
encode_cost
decode_cost
dense_fallback_condition
integrity_policy
retry_policy
flow_control_policy
expected_benefit
expected_risk
validation_plan
```

Agent 必须输出：

```text
为什么 sparse
为什么 dense
为什么启用/禁用 CRC
为什么需要 retry
为什么选择 credit window
```

而不是只返回 algorithm。

---

# 12.9.5 Sparse Data Profiles

必须建立冻结 data profiles。

建议最低覆盖：

```text
S00  0% sparse
S25  25% sparse
S50  50% sparse
S75  75% sparse
S90  90% sparse
S100 100% sparse
```

可增加：

```text
clustered sparsity
random sparsity
structured sparsity
```

但第一轮不要求复杂稀疏模式。

必须固定：

```text
seed
dtype
message sizes
rank sizes
index format
zero semantics
```

---

# 12.9.6 Sparse Benchmark Matrix

建议覆盖至少：

### Message size

```text
64 KB
1 MB
16 MB
128 MB
logical 1 GiB
```

### Sparsity

```text
0%
25%
50%
75%
90%
```

### Primitive

至少：

```text
AllReduce
AllGather
ReduceScatter
```

### Topology

代表性：

```text
Full Mesh 8
Ring 16
Fat-Tree 64
Heterogeneous 16
```

不需要形成和 G3-B2 一样大的性能矩阵。

目标约：

```text
15–25 sparse representative cases
```

---

# 12.9.7 Sparse Baseline Metrics

必须记录：

```text
logical_bytes
dense_wire_bytes
sparse_wire_bytes
index_bytes
value_bytes
metadata_bytes
compression_ratio
encode_cost
decode_cost
schedule_cost
p50
p95
correctness
dense_fallback
```

其中：

```text
wire_bytes
```

必须明确为：

```text
MODELED/HOST PAYLOAD BYTES
```

不是物理 NIC measured bytes。

---

# 12.9.8 Reliability Incremental Benchmark

新增代表场景：

```text
R01 clean transfer
R02 single corruption
R03 repeated corruption
R04 retry exhaustion
R05 logical timeout
R06 non-retryable invalid input
R07 no alternate path
R08 credit exhaustion
R09 backpressure recovery
R10 duplicate sequence
R11 missing chunk
R12 reordered chunk
```

所有 fault 必须确定性重放。

---

# 12.9.9 G3-B3 Claim Contract

新增：

```text
docs/submission/g3_b3_claim_contract.json
```

至少明确：

```text
sparse_host_execution != real_sparse_network
wire_bytes_model != physical_wire_measurement
host_crc != hardware_crc
host_retry != HCCL/NIC retry
backpressure_model != NIC backpressure
compile_link_direct != runtime_direct
```

---

# 12.9.10 G3-B3-A Evidence

至少：

```text
README.md
baseline.json
schedule_ir_v2_schema.json
agent_proposal_v2_schema.json
data_profiles.json
sparse_benchmark_contract.json
reliability_benchmark_contract.json
claim_contract.json
g3_b2_baseline_integrity.json
SHA256SUMS
```

---

# 12.9.11 G3-B3-A 完成条件

- G3-B2 evidence 未变；
- Schedule IR v2 完成；
- v1仍可解析；
- Agent proposal v2 完成；
- sparse profiles 冻结；
- sparse benchmark 冻结；
- reliability benchmark 冻结；
- baseline 完成；
- claim contract 完成；
- SHA256 完成；
- 未修改算法实现；
- 未实现 sparse；
- 未修改 frozen public ABI。

建议 commit：

```text
G3-B3-A freeze feature-completion contracts and incremental baseline
```

---

# 12.10 G3-B3-B：Lossless Sparsity-Aware Collective Path

## 12.10.1 目标

实现：

```text
LOSSLESS SPARSITY-AWARE PAYLOAD TRANSFORM
```

形成完整路径：

```text
input
→ sparsity detection
→ eligibility
→ dense/sparse decision
→ index/value encode
→ Schedule IR
→ host collective execution
→ reconstruction
→ reference validation
```

不得实现孤立的 sparse helper 而不与：

```text
Schedule
selector
cost model
Agent
correctness
```

集成。

---

# 12.10.2 Sparse Codec

第一版只允许：

```text
SPARSE_INDEX_VALUE
```

建议 representation：

```text
SparsePayload
{
  logical_element_count
  nonzero_count
  index_width
  indices
  values
}
```

要求：

- deterministic encoding；
- stable ordering；
- duplicate index rejection；
- out-of-range index rejection；
- deterministic decode；
- full reconstruction；
- dtype preserved；
- no lossy transformation。

---

# 12.10.3 Index Format

内部允许根据规模选择：

```text
uint16
uint32
uint64
```

但必须：

- 明确规则；
- 可预测；
- 有测试；
- 不形成 public ABI。

例如：

```text
logical_elements <= 65535
→ uint16

otherwise
→ uint32 / uint64
```

实际规则应由实现根据当前 message/rank 范围决定并冻结。

---

# 12.10.4 Sparse Eligibility

不得使用固定：

```text
sparsity > 50% → sparse
```

这种粗糙规则。

必须基于：

```text
sparse_wire_bytes
+
metadata_bytes
+
encode_cost
+
decode_cost
```

与：

```text
dense_wire_bytes
```

进行比较。

建议判定：

```text
estimated_sparse_total_cost
<
estimated_dense_total_cost
```

才允许 sparse。

---

# 12.10.5 Dense Fallback

必须支持：

```text
DENSE_FALLBACK
```

典型原因：

```text
LOW_SPARSITY
METADATA_OVERHEAD
UNSUPPORTED_DTYPE
UNSUPPORTED_PRIMITIVE
MEMORY_LIMIT
CODEC_ERROR
CORRECTNESS_GATE
```

不得 silent fallback。

Schedule/Agent output 必须记录 fallback_reason。

---

# 12.10.6 Primitive Support

Lossless sparse 最低必须覆盖：

```text
AllReduce
AllGather
ReduceScatter
```

但允许在内部采用不同 sparse execution strategy。

必须严格验证 collective semantics。

---

# 12.10.7 Sparse AllReduce

必须回答一个关键语义问题：

不同 rank 的 nonzero indices 不一定相同。

实现必须处理：

```text
union of sparse indices
```

而不是假设所有 rank 有相同 sparsity pattern。

SUM：

```text
same index → reduce values
missing index → implicit zero
```

MAX/MIN：

必须严格处理 implicit zero 与负值场景。

不得通过只测试正值绕过语义问题。

---

# 12.10.8 Sparse AllGather

应保持：

```text
rank ordering
per-rank sparse payload boundaries
```

重建后必须等价于 dense AllGather reference。

---

# 12.10.9 Sparse ReduceScatter

必须在 reduction 后保持：

```text
owner rank
segment boundary
index remapping
```

正确。

不得把 global sparse index 直接错误地映射到 local output。

---

# 12.10.10 Dtype

正式 sparse path 最低支持：

```text
FP32
FP16
BF16
```

INT32 可根据现有 correctness architecture 决定是否纳入。

不得在这一阶段加入 INT8 lossy codec。

---

# 12.10.11 Logical Large Message

必须继续满足 bounded materialization。

logical ≥1 GiB sparse 场景不得：

```text
materialize full logical tensor
```

必须以：

```text
chunked sparse generation
streaming encode
bounded reconstruction/reference sampling
```

或现有可证明方法实现。

---

# 12.10.12 C/C++ 实现

必须有真实 CPU_SIM C/C++ sparse execution capability，而不只是 Python simulator。

原则：

```text
internal helpers only
no new exported symbols
```

可以新增类似：

```text
hcccl/src/internal/sparse_codec.c
hcccl/include/internal/sparse_codec.h
```

但优先适配仓库现有结构。

---

# 12.10.13 C/Python Parity

至少验证：

```text
nonzero_count
indices
values
logical_bytes
wire_bytes
metadata_bytes
compression_ratio
reconstruction_hash
```

一致。

---

# 12.10.14 Sparse Correctness Tests

至少包括：

1. all dense；
2. all zero；
3. single nonzero；
4. 25% sparse；
5. 50% sparse；
6. 75% sparse；
7. 90% sparse；
8. random sparse pattern；
9. per-rank different pattern；
10. duplicate index rejection；
11. unordered input canonicalization；
12. invalid index rejection；
13. empty payload；
14. non-divisible chunk；
15. multiple ranks；
16. SUM；
17. MAX；
18. MIN；
19. AllReduce；
20. AllGather；
21. ReduceScatter；
22. FP32；
23. FP16；
24. BF16；
25. dense fallback；
26. logical large message；
27. bounded memory；
28. C/Python parity。

---

# 12.10.15 Sparse Performance Acceptance

G3-B3 不要求每个 sparsity 场景都优于 dense。

正确预期：

```text
低 sparsity → dense 胜出
高 sparsity → sparse 胜出
```

必须展示 break-even。

至少输出：

```text
sparsity ratio
compression ratio
wire byte reduction
cost delta
selected mode
fallback
```

禁止只选择 sparse 获胜场景。

---

# 12.10.16 G3-B3-B Evidence

至少：

```text
sparse_codec_manifest.json
sparse_correctness.json
sparse_c_python_parity.json
sparse_benchmark.json
sparse_break_even.json
dense_fallback_audit.json
bounded_sparse_memory.json
claim_boundary_audit.json
SHA256SUMS
```

---

# 12.10.17 完成条件

必须：

```text
Lossless Sparse: COMPLETED
Dense Fallback: COMPLETED
Three-Primitive Sparse Correctness: COMPLETED
Sparse C/Python Parity: COMPLETED
Bounded Sparse Large Message: COMPLETED
```

建议 commit：

```text
G3-B3-B add lossless sparsity-aware collective transport
```

---

# 12.11 G3-B3-C：C/C++ Integrity、CRC32 与 Bounded Retry

## 12.11.1 目标

将 reliability 从：

```text
Python simulator / Schedule metadata
```

深化到：

```text
CPU_SIM C/C++ payload execution path
```

重点：

```text
chunk identity
sequence
CRC32
corruption detection
retry classification
logical timeout
bounded retry
retry exhaustion
```

---

# 12.11.2 Integrity Metadata

每个内部 transfer/chunk 至少有：

```text
transfer_id
sequence_id
chunk_id
attempt
payload_length
crc32
```

不得暴露为新 public ABI。

---

# 12.11.3 CRC32

必须实现标准、确定性的 CRC32。

最低验证：

- known vectors；
- empty payload；
- 1 byte；
- non-aligned length；
- large chunk；
- bit flip；
- byte corruption；
- wrong CRC；
- C/Python parity。

不得只调用一个 test stub 返回预设结果。

---

# 12.11.4 Corruption Injection

只允许：

```text
TEST_ONLY / HOST_SIMULATED
```

注入。

必须 deterministic。

支持：

```text
bit flip
byte flip
CRC tamper
duplicate chunk
missing chunk
reordered sequence
```

不得进入生产默认路径。

---

# 12.11.5 Failure Classification

必须明确：

```text
RETRYABLE
NON_RETRYABLE
TERMINAL
```

推荐：

### Retryable

```text
CRC_MISMATCH
LOGICAL_TIMEOUT
TRANSIENT_TRANSFER_FAILURE
```

### Non-retryable

```text
INVALID_ARGUMENT
INVALID_RANK
INVALID_BUFFER
UNSUPPORTED_DTYPE
UNSUPPORTED_PRIMITIVE
```

### Terminal

```text
RETRY_EXHAUSTED
NO_ALTERNATE_PATH
UNRECOVERABLE_INTEGRITY_FAILURE
```

---

# 12.11.6 Timeout

不得使用真实 `sleep()` 来人为制造可靠性测试。

使用：

```text
logical clock
event ticks
deterministic deadline
```

每个 transfer 记录：

```text
start_tick
deadline_tick
completion_tick
timed_out
```

---

# 12.11.7 Retry

至少：

```text
max_retries
attempt_count
retry_reason
retransmitted_bytes
terminal_reason
```

必须保证：

```text
attempt_count <= configured bound
```

不得出现 infinite retry。

---

# 12.11.8 CRC → Retry 联动

必须真实实现：

```text
payload
→ CRC
→ corruption
→ verify fail
→ classify retryable
→ retry
→ verify pass
```

以及：

```text
repeated corruption
→ retry exhaustion
→ terminal failure
```

---

# 12.11.9 No-path 与 Timeout 分离

必须保证：

```text
NO_ALTERNATE_PATH
```

不被错误解释为 timeout。

No-path 不应无意义重复 retry。

---

# 12.11.10 Parity

Parity 为 SHOULD。

仅在 CRC 完整完成后允许增加。

不得用 parity 代替 CRC。

若实现：

```text
PARITY_AUXILIARY
```

只作为：

- 辅助检测；
- 教学/算法实验；
- evidence 扩展。

不允许宣称硬件 ECC/parity。

---

# 12.11.11 C/C++ Tests

至少：

1. CRC known vector；
2. C/Python CRC parity；
3. clean transfer；
4. single corruption；
5. recover after retry；
6. repeated corruption；
7. retry exhausted；
8. logical timeout；
9. non-retryable error；
10. no-path；
11. duplicate sequence；
12. missing chunk；
13. reorder；
14. max attempt；
15. retransmitted bytes；
16. sparse payload CRC；
17. dense payload CRC；
18. logical large chunk；
19. bounded memory；
20. deterministic replay。

---

# 12.11.12 G3-B3-C Evidence

至少：

```text
integrity_manifest.json
crc_known_vectors.json
crc_c_python_parity.json
corruption_cases.json
retry_cases.json
timeout_cases.json
failure_classification.json
retry_exhaustion.json
sparse_integrity_crosscheck.json
SHA256SUMS
```

---

# 12.11.13 完成条件

```text
C/C++ CRC32: COMPLETED
Host Integrity Validation: COMPLETED
Bounded Retry: COMPLETED
Logical Timeout: COMPLETED
Failure Classification: COMPLETED
```

建议 commit：

```text
G3-B3-C add host integrity validation and bounded retry
```

---

# 12.12 G3-B3-D：Wire-aware Cost、Agent 决策与 Credit Backpressure

## 12.12.1 目标

将 Sparse、Integrity 和 Retry 真正纳入：

```text
Schedule
Cost Model
Selector
Agent
```

避免形成孤立功能。

---

# 12.12.2 Wire-aware Cost Model

现有：

```text
transferred_bytes
```

应明确拆分：

```text
logical_bytes
payload_bytes
index_bytes
metadata_bytes
wire_bytes
retransmitted_bytes
```

不得让：

```text
logical_bytes == wire_bytes
```

成为隐含假设。

---

# 12.12.3 Codec Cost

至少考虑：

```text
detect_cost
encode_cost
decode_cost
metadata_cost
```

这些都是：

```text
HOST/SIMULATOR MODEL
```

不得表示真实 Ascend codec latency。

---

# 12.12.4 Integrity Cost

记录：

```text
crc_cost
retry_probability
expected_retry_bytes
retry_penalty
```

如果使用 deterministic benchmark，原始故障与期望模型必须分开记录。

---

# 12.12.5 Flow Control

实现：

```text
credit-based bounded in-flight model
```

至少包含：

```text
credit_window
available_credit
max_inflight_chunks
high_watermark
low_watermark
blocked_producer_events
credit_return_events
```

---

# 12.12.6 Flow-control Invariants

必须保证：

```text
available_credit >= 0
inflight <= max_inflight
credits conserved
no deadlock
eventually drains
memory budget respected
```

---

# 12.12.7 Backpressure

在 consumer 处理能力不足或 queue saturation 时：

```text
producer pauses
```

而不是：

```text
无限累积 queue
```

至少模拟：

```text
normal load
temporary congestion
sustained congestion
recovery
```

---

# 12.12.8 Agent Data-aware Selection

Agent 必须根据：

```text
primitive
algorithm
topology
message size
sparsity
wire bytes
codec overhead
metadata overhead
memory
integrity policy
retry cost
flow control
```

选择：

```text
dense/sparse
algorithm
chunk size
pipeline depth
credit window
integrity policy
```

---

# 12.12.9 Agent Proposal

至少：

```text
proposal_id
schedule_algorithm
payload_mode
sparse_codec
sparsity_ratio
logical_bytes
estimated_wire_bytes
estimated_compression_ratio
chunk_size
pipeline_depth
credit_window
integrity_policy
retry_policy
fallback_conditions
correctness_plan
expected_benefit
expected_risk
```

---

# 12.12.10 Correctness Hard Gate

任何 candidate：

```text
codec correctness fail
CRC integrity fail
reconstruction fail
retry invariant fail
flow-control invariant fail
```

必须被拒绝。

性能不能覆盖正确性失败。

---

# 12.12.11 Sparse Ablation

至少：

```text
B0 dense baseline
B1 sparse codec only
B2 + wire-aware cost
B3 + Agent dense/sparse selection
B4 + CRC
B5 + retry
B6 + credit flow-control
```

不得替换或覆盖 G3-B2 的 A0–A7。

两套消融用途不同：

```text
G3-B2 A0–A7
→ communication scheduling optimization

G3-B3 B0–B6
→ feature-completion stack
```

---

# 12.12.12 Sparse Performance Gate

不得要求：

```text
all scenarios WIN
```

正确 gate：

1. correctness 100%；
2. 低稀疏度能正确 fallback dense；
3. 高稀疏度至少存在稳定 wire-byte 减少；
4. 找到 reproducible break-even；
5. metadata 计入成本；
6. sparse 不得突破 memory budget；
7. p95 不得异常失控；
8. 使用固定 benchmark/data profiles；
9. 不修改 G3-B2 parameter freeze；
10. 不选择性删除 unfavorable cases。

---

# 12.12.13 Flow Control Gate

必须：

```text
credit invariant PASS
memory invariant PASS
deadlock tests PASS
temporary congestion recovery PASS
```

---

# 12.12.14 OPTIONAL-GATE-1：PairWise

只有在：

```text
existing tiny-message candidates
```

表现出明确缺口时才允许进入。

必须先生成：

```text
pairwise_value_gate.json
```

若没有足够收益：

```text
status=SKIPPED_BY_VALUE_GATE
```

不影响 G3-B3 COMPLETED。

若实现：

- internal schedule only；
- no public symbol；
- focused benchmark；
- correctness；
- selector integration；
- support matrix update。

---

# 12.12.15 OPTIONAL-GATE-2：INT8

默认：

```text
DEFERRED_BY_PRECISION_GATE
```

只有全部满足时才允许：

- MUST 项全部完成；
- SHOULD 主体完成；
- regression stable；
- 无 unresolved correctness issue；
- precision contract 可独立定义；
- 有明显剩余执行预算。

若实现，仅允许：

```text
per-chunk symmetric INT8
```

最低记录：

```text
scale
saturation_count
max_abs_error
max_rel_error
MSE
compression_ratio
dense_fallback
```

不得声称：

```text
lossless
global ≤1e-6
real NPU speedup
```

若无法满足稳定 correctness：

```text
INT8=DEFERRED
```

不影响 G3-B3。

---

# 12.12.16 G3-B3-D Evidence

至少：

```text
wire_cost_audit.json
selector_decisions.json
agent_proposals.jsonl
agent_evaluations.jsonl
agent_reflections.jsonl
flow_control_audit.json
backpressure_cases.json
feature_ablation.json
sparse_break_even.json
pairwise_value_gate.json
int8_precision_gate.json
SHA256SUMS
```

---

# 12.12.17 完成条件

```text
Wire-aware Cost Model: COMPLETED
Sparse-aware Selector: COMPLETED
Agent Sparse/Integrity Proposal: COMPLETED
Credit Flow Control: COMPLETED
Backpressure Model: COMPLETED
Feature Ablation: COMPLETED
```

PairWise/INT8 不属于完成必要条件。

建议 commit：

```text
G3-B3-D integrate sparse reliability decisions and bounded backpressure
```

---

# 12.13 G3-B3-E：Official ACL/HCCL Compile/Link-only Production Source Path

## 12.13.1 目标

当前 direct readiness 只有：

```text
official declarations
static_assert
symbol anchors
link dependencies
host lifecycle model
```

G3-B3-E 增加真正包含官方 runtime API 调用表达式的源码路径。

该路径必须：

```text
存在真实调用表达式
可以 compile
可以 link
默认 OFF
当前环境绝不执行
```

---

# 12.13.2 身份

新的 artifact/target 必须定义为：

```text
DIRECT_COMPILE_LINK_ONLY_RUNTIME_SOURCE
```

不是：

```text
REAL_DEVICE_BACKEND
OFFICIAL_PLUGIN
REAL_RUNTIME_VALIDATED
```

---

# 12.13.3 与现有 Direct Readiness 分离

不得改变：

```text
libhccl_direct_adapter.a
```

现有角色。

新 target 独立存在，例如概念：

```text
hccl_direct_runtime_source
```

实际名称由现有 CMake 风格决定。

---

# 12.13.4 Required API Expressions

只有在 frozen official headers 中确实存在并签名确认后，才允许加入。

预期涵盖：

### Runtime initialization

```text
aclInit
aclrtSetDevice
```

### Context / Stream

```text
aclrtCreateContext
aclrtCreateStream
```

### Memory

```text
aclrtMalloc
aclrtMemcpy
```

### HCCL communicator

使用 frozen official API 中实际可用的：

```text
HcclCommInit*
```

不得凭记忆发明函数。

### Collective

必须存在三原语实际 call expression：

```text
HcclAllReduce
HcclAllGather
HcclReduceScatter
```

### Synchronization

使用 frozen headers 中实际 API。

### Cleanup

必须逆序：

```text
communicator
buffers
stream
context
device/runtime
```

具体顺序以官方 API 合约为准。

---

# 12.13.5 Source Contract

源码必须明确：

```text
THIS SOURCE IS NOT EXECUTED IN HOST-ONLY ACCEPTANCE
```

并通过 compile-time guard 防止 accidental host execution。

---

# 12.13.6 Runtime Reachability Guard

必须至少两层保护：

```text
CMake default OFF
+
runtime execution guard
```

当前 submission CLI 不能自动执行此 binary。

即使 CANN root 存在：

```text
compile/link != execute
```

---

# 12.13.7 ELF Audit

必须确认：

新 direct compile/link artifact 可以依赖：

```text
libacl_rt.so
libhccl.so
libhcomm.so
```

但：

```text
libhccl_plugin.so
```

仍只能依赖：

```text
libc.so.6
```

---

# 12.13.8 API Call-expression Audit

必须新增静态 audit，区分：

```text
DECLARATION
STATIC_ASSERT
SYMBOL_ADDRESS
ACTUAL_CALL_EXPRESSION
```

G3-B3-E 必须证明：

```text
ACTUAL_CALL_EXPRESSION=PRESENT
```

但同时：

```text
RUNTIME_EXECUTION=false
runtime_api_calls=[]
```

---

# 12.13.9 Lifecycle Error Paths

源码级必须包含：

- init fail；
- set device fail；
- context fail；
- stream fail；
- allocation fail；
- communicator fail；
- collective fail；
- synchronization fail；

以及：

```text
reverse-order cleanup
first-error preservation
no double free
```

---

# 12.13.10 No-device 环境

当前不得运行 production runtime target。

允许：

```text
compile
link
nm
readelf
ldd
objdump/static source audit
```

不允许：

```text
execute
```

---

# 12.13.11 Direct Evidence

至少：

```text
direct_runtime_source_manifest.json
official_api_call_expression_audit.json
compile_result.json
link_result.json
elf_needed.json
symbol_audit.json
execution_guard_audit.json
cleanup_path_audit.json
cpu_sim_isolation_audit.json
truth_boundary_audit.json
SHA256SUMS
```

---

# 12.13.12 完成条件

```text
Official API Call Expressions: PRESENT
Compile: PASS
Link: PASS
Execution: NOT_EXECUTED
CPU_SIM ABI Isolation: PASS
CPU_SIM Dependency Isolation: PASS
Runtime Guard: PASS
Cleanup Static Audit: PASS
```

状态只能：

```text
Direct Production Source Readiness: COMPLETED
Real-device Acceptance: HARDWARE_BLOCKED
```

不得将：

```text
C/C++ Plugin Compliance
```

自动提升为 SATISFIED。

建议 commit：

```text
G3-B3-E add compile-only official ACL HCCL runtime source path
```

---

# 12.14 G3-B3-F：Final Regression、Evidence Freeze 与 Final Feature Freeze

## 12.14.1 目标

冻结新的最终功能基线。

G3-B3-F 之后：

```text
FINAL FEATURE FREEZE
```

生效。

---

# 12.14.2 最终 baseline

生成：

```text
docs/submission/g3_b3_final_feature_baseline.md
experiments/feature_completion/g3_b3_final_baseline.json
```

至少记录：

```text
final_source_commit
public_abi_version
SONAME
exported_symbols
plugin_sha256
schedule_ir_version
agent_proposal_version
sparse_codec_version
integrity_version
retry_policy_version
flow_control_version
direct_source_version
g3_b2_benchmark_sha256
g3_b3_benchmark_sha256
g3_b2_parameter_sha256
final_evidence_path
```

---

# 12.14.3 Final Support Matrix

生成新的：

```text
feature_support_matrix.json
```

至少：

| Capability           | Status            | Truth             |
| -------------------- | ----------------- | ----------------- |
| Dense AllReduce      | COMPLETED         | HOST_EXECUTED     |
| Dense AllGather      | COMPLETED         | HOST_EXECUTED     |
| Dense ReduceScatter  | COMPLETED         | HOST_EXECUTED     |
| Sparse AllReduce     | COMPLETED         | HOST_EXECUTED     |
| Sparse AllGather     | COMPLETED         | HOST_EXECUTED     |
| Sparse ReduceScatter | COMPLETED         | HOST_EXECUTED     |
| CRC32                | COMPLETED         | HOST_EXECUTED     |
| Retry                | COMPLETED         | HOST_EXECUTED     |
| Timeout              | COMPLETED         | HOST_EXECUTED     |
| Backpressure         | COMPLETED         | HOST/SIMULATED    |
| Direct source        | COMPLETED         | COMPILE_LINK_ONLY |
| INT8                 | OPTIONAL/DEFERRED | EXPERIMENTAL      |
| PairWise             | OPTIONAL/SKIPPED  | INTERNAL          |
| Broadcast            | NOT_SELECTED      | —                 |
| AlltoAll             | NOT_SELECTED      | —                 |

---

# 12.14.4 Final Regression

必须运行：

### G3-B

```text
submission check
quick
full
```

### C/C++

- all CTest；
- CPU_SIM clean build；
- double clean build；
- bit-for-bit reproducibility；
- install；
- external consumer；
- ELF audit；
- symbols；
- dependency；
- SONAME。

### G3-B2

- Schedule IR v1 authority evidence；
- G3-B2 focused tests；
- G3-B2 final evidence SHA；
- G3-B2 benchmark unchanged。

### G3-B3

- IR v2；
- sparse；
- dense fallback；
- C/Python parity；
- CRC；
- corruption；
- retry；
- timeout；
- flow control；
- Agent；
- benchmark；
- direct compile/link；
- truth audit。

### Python

运行 submission-relevant + full repo regression。

不得新增无理由 skip。

---

# 12.14.5 Reproducibility

最终必须再次验证：

```text
libhccl_plugin.so
```

双构建：

```text
binary SHA equal
SONAME equal
NEEDED equal
19 symbols equal
headers equal
CTest equal
```

因为 G3-B3 修改了内部 C 实现。

最终 plugin SHA 可以变化，但 public contract 必须不变。

---

# 12.14.6 G3-B2 Regression Guard

必须验证：

```text
18 wins / 0 ties / 0 losses
45.59283008%
```

历史 evidence 未改变。

G3-B3 不要求重新把 sparse/reliability 特性塞入 G3-B2 的 45.59% 数字。

---

# 12.14.7 Final Sparse Result

必须报告：

```text
dense cases
sparse cases
fallback cases
break-even
compression ratios
wire-byte model
correctness
memory
```

不得只报告最好的 compression ratio。

---

# 12.14.8 Final Reliability Result

至少：

```text
clean transfer
corruption detected
retry recovered
retry exhausted
timeout recovered
timeout terminal
non-retryable rejected
sequence error
backpressure recovery
no-path
```

---

# 12.14.9 Submission CLI

更新：

```text
python -m tools.submission_cli quick
```

加入轻量：

- sparse representative case；
- CRC known-vector；
- retry recovery；
- dense fallback；
- IR v2 validation。

`full` 加入：

- sparse focused regression；
- integrity；
- flow control；
- direct compile/link-only；
- G3-B3 final evidence。

不得让 quick 执行完整 sparse benchmark。

---

# 12.14.10 Staging

新增：

```text
feature_completion/
├── sparse/
├── integrity/
├── retry/
├── flow_control/
└── direct_source/
```

其中只放：

- manifest；
- source/docs；
- representative evidence；
- final summary。

不得放：

- CANN SDK；
- official HCCL/HCOMM source；
- official DSO；
- private Codex logs；
- build cache；
- temporary benchmark dumps；
- controlled competition documents。

---

# 12.14.11 Final Evidence

唯一最终 authority evidence：

```text
experiments/feature_completion/evidence/
    g3_b3_f_final_<timestamp>/
```

至少包含：

```text
README.md
manifest.json
result.json

g3_b2_baseline_reference.json
g3_b3_baseline_reference.json

schedule_ir_v2_audit.json
agent_proposal_v2_audit.json

sparse_support_matrix.json
sparse_correctness.json
sparse_c_python_parity.json
sparse_benchmark.json
sparse_break_even.json
dense_fallback_audit.json
bounded_sparse_memory.json

integrity_manifest.json
crc_audit.json
corruption_audit.json
retry_audit.json
timeout_audit.json
failure_classification.json

flow_control_audit.json
backpressure_audit.json

agent_trace_inventory.json
feature_ablation.json

direct_runtime_source_manifest.json
official_api_call_expression_audit.json
direct_compile_link_audit.json
cpu_sim_isolation_audit.json

native_elf_audit.json
reproducible_build.json
submission_regression.json
staging_verification.json

claim_boundary_audit.json
requirement_delta.json
user_action_required.json

SHA256SUMS
```

---

# 12.15 G3-B3 Requirement Delta

不得修改 G3-A requirement matrix。

生成：

```text
docs/submission/g3_b3_requirement_delta.json
```

重点重新评估：

```text
REQ-INNOV-004
reliability CRC/integrity related requirements
retry related requirements
flow-control related requirements
Agent algorithm generation related requirements
direct interface readiness related requirements
```

可能升级：

```text
MISSING → PARTIALLY_SATISFIED
PARTIALLY_SATISFIED → SATISFIED
```

只能以实际 evidence 为准。

真实设备相关仍：

```text
HARDWARE_BLOCKED
```

---

# 12.16 G3-B3 性能结论规则

G3-B3 必须维护两套独立性能结论。

## G3-B2 Scheduling Performance

保持：

```text
18 wins
0 ties
0 losses
weighted simulated improvement=45.59283008%
```

身份：

```text
SIMULATED_ONLY
```

---

## G3-B3 Sparse Payload Result

使用独立指标：

```text
wire-byte model reduction
compression ratio
break-even sparsity
encode/decode overhead
modeled communication benefit
```

不得把：

```text
50% fewer modeled wire bytes
```

直接写成：

```text
50% faster
```

除非 cost-model benchmark 确实得到该性能结果。

---

# 12.17 OPTIONAL INT8 精度规则

若 INT8 gate 未开启：

```text
INT8 Status:
DEFERRED_BY_PRECISION_GATE
```

这是正常完成状态。

若开启：

必须使用独立实验身份：

```text
EXPERIMENTAL_LOSSY_INT8
```

不得纳入 lossless sparse correctness 结论。

必须报告：

```text
quantization scale
saturation
max_abs_error
max_rel_error
MSE
compression ratio
fallback
```

任何精度失败必须自动退回 dense/non-quantized path。

---

# 12.18 Documentation

G3-B3 至少新增：

```text
docs/feature_completion/
├── g3_b3_overview.md
├── schedule_ir_v2.md
├── lossless_sparse_design.md
├── sparse_collective_semantics.md
├── integrity_crc_retry_design.md
├── flow_control_design.md
├── agent_sparse_decision.md
├── direct_compile_only_runtime_source.md
├── g3_b3_ablation.md
├── g3_b3_known_limitations.md
└── g3_b3_final_feature_baseline.md
```

这些仍属于工程文档。

正式比赛报告由 G3-C 生成。

---

# 12.19 Test Requirements

至少覆盖以下类别。

## Contract

1. IR v1 historical compatibility；
2. IR v2 schema；
3. v2 canonical hash；
4. proposal v2 schema；
5. dense v2 compatibility；
6. invalid transform rejection。

## Sparse

7. all dense；
8. all zero；
9. 25% sparse；
10. 50% sparse；
11. 75% sparse；
12. 90% sparse；
13. single nonzero；
14. random sparsity；
15. different rank patterns；
16. duplicate index；
17. invalid index；
18. ordered canonical encoding；
19. encode/decode；
20. C/Python parity；
21. dense fallback；
22. break-even；
23. logical large；
24. bounded memory。

## Sparse Collectives

25. sparse AllReduce SUM；
26. sparse AllReduce MAX；
27. sparse AllReduce MIN；
28. sparse AllGather；
29. sparse ReduceScatter；
30. FP32；
31. FP16；
32. BF16；
33. ranks 2/4/8/16；
34. representative 64-rank simulated case。

## Integrity

35. CRC known vector；
36. empty CRC；
37. C/Python CRC；
38. bit corruption；
39. byte corruption；
40. CRC tamper；
41. missing chunk；
42. duplicate chunk；
43. reorder；
44. sequence validation。

## Retry

45. clean no retry；
46. one retry；
47. recovery；
48. repeated failure；
49. retry exhaustion；
50. logical timeout；
51. timeout recovery；
52. non-retryable no retry；
53. no-path no blind retry；
54. attempt bound；
55. retransmitted byte accounting。

## Flow control

56. credit conservation；
57. no negative credit；
58. max inflight；
59. queue saturation；
60. producer blocking；
61. credit return；
62. recovery；
63. no deadlock；
64. bounded memory；
65. fairness/basic starvation guard。

## Agent / Selector

66. sparse candidate generation；
67. dense fallback；
68. wire cost；
69. integrity proposal；
70. retry proposal；
71. credit proposal；
72. correctness hard gate；
73. deterministic selection；
74. reflection/replanning trace。

## Direct

75. default OFF；
76. official headers；
77. actual API call expression；
78. collective call expressions；
79. compile；
80. link；
81. not executed；
82. CPU_SIM dependency isolation；
83. export allowlist unchanged；
84. cleanup-path audit。

## Regression

85. CPU_SIM CTest；
86. Python submission regression；
87. full Python regression；
88. G3-B quick；
89. G3-B full；
90. bit-for-bit native rebuild；
91. G3-B2 evidence SHA；
92. G3-B3 evidence SHA；
93. staging verify；
94. HCOMM tracked clean；
95. HCCL tracked clean。

数量可以因实际测试组织变化，但上述语义必须有覆盖。

---

# 12.20 USER_ACTION_REQUIRED

继承：

```text
UA-B-001 project license/copyright
UA-B-002 official asset redistribution
UA-B-003 controlled competition material
UA-B-004 platform archive/size
```

新增：

## UA-B3-001

```text
INT8 precision interpretation
```

仅当 Optional INT8 被考虑时需要。

不阻塞 MUST 范围。

---

# 12.21 失败与状态分类

## FAIL

用于：

- sparse reconstruction错误；
- collective语义错误；
- CRC误检/漏检；
- retry无界；
- timeout错误；
- flow-control deadlock；
- credit泄漏；
- C/Python parity失败；
- G3-B2 regression；
- ABI变化；
- export变化；
- CPU_SIM引入official dependency；
- evidence SHA失败；
- claim boundary失败。

---

## PARTIAL

用于：

- Sparse主体完成但某非核心 topology 未覆盖；
- Backpressure部分完成；
- Direct source只能部分覆盖官方 lifecycle；
- optional能力未达到目标。

---

## ENV_BLOCKED

用于：

- compiler/CMake不可用；-必要 frozen SDK header 不可读取；-文件系统或环境损坏。

---

## HARDWARE_BLOCKED

只用于真实硬件：

- NPU；
- ACL runtime；
- HCCL communicator；
- collective；
- real network；
- msprof；
- real failover；
- real training。

不得用 HARDWARE_BLOCKED 掩盖代码 bug。

---

# 12.22 G3-B3 最终完成条件

G3-B3 只有以下全部满足才可：

```text
G3-B3: COMPLETED
```

必须：

- G3-B3-A baseline frozen；
- Schedule IR v2；
- Agent proposal v2；
- G3-B2 v1 evidence保持有效；
- lossless sparse detector；
- sparse index/value codec；
- reconstruction；
- dense fallback；
- three primitive sparse correctness；
- sparse C/Python parity；
- bounded sparse large-message；
- wire-byte accounting；
- sparse break-even；
- C/C++ CRC32；
- corruption detection；
- sequence/chunk identity；
- bounded retry；
- logical timeout；
- retry exhaustion；
- failure classification；
- wire-aware cost；
- sparse-aware selector；
- Agent sparse proposal；
- Agent correctness hard gate；
- credit-based flow control；
- bounded inflight；
- no-deadlock test；
- feature ablation；
- direct official API actual call expressions；
- direct compile；
- direct link；
- direct execution disabled；
- CPU_SIM ABI不变；
- SONAME不变；
- 19-symbol allowlist不变；
- CPU_SIM dependency isolation；
- G3-B quick/full通过；
- native双构建 bit-for-bit；
- final evidence完整；
- staging verify；-旧 evidence未修改；-工作区 clean；
- HCOMM/HCCL tracked clean；-未执行真实设备。

PairWise 和 INT8 不属于完成必要条件。

---

# 12.23 G3-B3 最终状态

成功后：

```text
G3-B3: COMPLETED

Schedule IR v2: COMPLETED
Lossless Sparse Communication: COMPLETED
Sparse Three-Primitive Correctness: COMPLETED
Dense Fallback: COMPLETED
Sparse Wire Accounting: COMPLETED

C/C++ CRC32 Integrity: COMPLETED
Bounded Timeout/Retry: COMPLETED
Failure Classification: COMPLETED

Credit Flow Control: COMPLETED
Backpressure Model: COMPLETED

Sparse-aware Selector: COMPLETED
Agent Feature Proposal Loop: COMPLETED
Feature Ablation: COMPLETED

Direct Compile/Link-only Runtime Source: COMPLETED

CPU_SIM Public ABI: FROZEN
SONAME: FROZEN
19-symbol Export Allowlist: FROZEN

Final Feature Baseline: FROZEN
```

仍保持：

```text
C/C++ Plugin Compliance: PARTIALLY_SATISFIED
Competition Performance Target: PARTIALLY_SATISFIED
Submission Release Readiness: PARTIAL
G3 Delivery Readiness: PARTIAL
Real-device Acceptance: HARDWARE_BLOCKED
```

---

# 12.24 Final Feature Freeze

G3-B3-F 合并进入 `main` 后：

```text
FINAL FEATURE FREEZE
```

正式生效。

冻结：

```text
collective primitives
algorithm families
Schedule IR semantics
sparse codec
integrity semantics
retry semantics
flow-control semantics
selector
cost model
Agent proposal contract
simulator model
benchmark contracts
public ABI
direct source structure
```

之后不得新增：

- collective；-算法；
- sparse codec；
- compression codec；
- reliability机制；
- direct功能；
- performance model。

---

# 12.25 Freeze 后允许修改

只允许：

### BLOCKING_BUGFIX

- correctness bug；
- build failure；
- staging failure；
- security/privacy；
- evidence traceability bug。

### DOCUMENTATION

- report；-图表；
- README；
- explanation；
- comments。

### PLATFORM_COMPATIBILITY

-比赛平台目录；

- archive format；
- packaging；
- non-semantic launcher fixes。

任何涉及：

```text
algorithm
schedule
performance formula
benchmark
correctness semantic
```

的修改都必须重新开放 freeze，并重新生成受影响 evidence。

---

# 12.26 Branch 与 Commit

建议单一分支：

```text
codex/g3-b3-final-feature-completion
```

建议六个阶段性 commit：

```text
G3-B3-A freeze feature-completion contracts and incremental baseline

G3-B3-B add lossless sparsity-aware collective transport

G3-B3-C add host integrity validation and bounded retry

G3-B3-D integrate sparse reliability decisions and bounded backpressure

G3-B3-E add compile-only official ACL HCCL runtime source path

G3-B3-F freeze final competition feature baseline and evidence
```

完成 G3-B3-F commit 后必须停止。

不得：

```text
push
merge
start G3-C
start G3-D
create release
create tag
upload competition platform
```

由用户检查后再进行 PR/merge。

---

# 12.27 Final Evidence 状态字段

最终 `result.json` 至少记录：

```text
checkpoint=G3-B3
checkpoint_status=COMPLETED

final_feature_freeze=FROZEN

schedule_ir_v2=COMPLETED

lossless_sparse=COMPLETED
sparse_allreduce=COMPLETED
sparse_allgather=COMPLETED
sparse_reducescatter=COMPLETED
dense_fallback=COMPLETED

crc32_integrity=COMPLETED
bounded_retry=COMPLETED
logical_timeout=COMPLETED
failure_classification=COMPLETED

credit_flow_control=COMPLETED
backpressure_model=COMPLETED

agent_sparse_selection=COMPLETED
feature_ablation=COMPLETED

direct_compile_link_source=COMPLETED
direct_runtime_execution=false

pairwise=<SKIPPED_BY_VALUE_GATE|OPTIONAL_COMPLETED>
int8=<DEFERRED_BY_PRECISION_GATE|EXPERIMENTAL_COMPLETED>

public_abi_changed=false
soname_changed=false
export_allowlist_changed=false

old_evidence_modified=false
g3_b2_baseline_modified=false

real_device_api_executed=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
measured_on_real_npu=false
real_training_acceleration=false
msprof_executed=false
runtime_api_calls=[]

c_cpp_plugin_compliance=PARTIALLY_SATISFIED
competition_performance_target=PARTIALLY_SATISFIED
submission_release_readiness=PARTIAL
g3_delivery_readiness=PARTIAL
real_device_acceptance=HARDWARE_BLOCKED
```

---

# 12.28 最终汇报要求

Codex最终汇报至少包含：

1. G3-B3 总体状态、分支、六个 commit 和耗时；
2. G3-B2 frozen baseline完整性；
3. IR v2 和 Agent proposal v2；
4. Sparse codec设计；
5. Sparse三原语支持；
6. dense fallback；
7. sparse break-even；
8. logical/wire/metadata bytes；
9. C/Python sparse parity；
10. CRC32；
11. corruption detection；
12. timeout/retry；
13. retry exhaustion；
14. flow control/backpressure；
15. Agent sparse/reliability决策；
16. B0–B6消融；
17. PairWise gate；
18. INT8 gate；
19. direct actual call-expression audit；
20. direct compile/link结果；
21. direct execution guard；
22. public ABI、SONAME、19 symbols；23.最终 plugin SHA；24.双构建 reproducibility；
23. CTest/Python/quick/full；
24. staging；
25. final evidence；
26. requirement delta；
27. USER_ACTION_REQUIRED；
28. HCOMM/HCCL状态；
29. git status；32.真实性边界；33.未 push、未 merge、未开始 G3-C；
30. Final Feature Baseline 是否 FROZEN。

---

# 12.29 G3-C 启动门槛

只有满足：

```text
G3-B3 merge into main
+
Final Feature Baseline=FROZEN
+
final evidence SHA PASS
+
git worktree clean
```

才允许正式执行 G3-C。

G3-C 必须以：

```text
G3-B3 merged main commit
```

作为最终 source baseline。

正式报告不得再使用 G3-B2：

```text
final code baseline
```

作为当前最终源码状态，但可以继续引用 G3-B2 的 optimization evidence 作为历史权威性能 evidence。

最终证据链应变为：

```text
G3-B2
→ scheduling / topology optimization evidence

G3-B3
→ sparse / integrity / retry / backpressure /
   direct compile-link feature evidence

G3-C
→ formal report derived from both evidence families
```

# 13. G3-C：Final Feature Freeze 后的证据驱动正式技术报告体系

## 13.1 阶段定位

G3-C 是在：

```text
G3-B2 Final Code Baseline
+
G3-B3 Final Feature Baseline
```

均完成并合并进入 `main` 后执行的正式技术报告阶段。

G3-C 的身份为：

```text
EVIDENCE-DERIVED FORMAL TECHNICAL REPORTING
```

本阶段不再开发新的通信算法、Sparse codec、可靠性机制、性能模型或 Direct runtime 能力。

其目标是将已经冻结的：

```text
source
configs
tests
benchmark contracts
G2-F evidence
G3-A audit
G3-B delivery evidence
G3-B2 optimization evidence
G3-B3 feature-completion evidence
```

转换成：

```text
评委可阅读
可复现
可追踪
数字可核验
claim 有边界
不同证据身份不混淆
```

的正式技术报告体系。

---

# 13.2 G3-C 前置条件

开始 G3-C 前必须验证：

```text
G3-B3 已 merge into main
Final Feature Baseline=FROZEN
main == origin/main
git worktree clean
G3-B2 final evidence SHA PASS
G3-B3 final evidence SHA PASS
```

执行开始时解析并记录：

```text
g3_c_source_commit=<CURRENT_MERGED_MAIN_COMMIT>
g3_b2_final_source_commit
g3_b3_final_source_commit
g3_b2_final_evidence
g3_b3_final_evidence
```

G3-C 不得依赖聊天记录中的 commit、性能数字或测试数字作为权威来源。

所有正式报告中的数字必须重新从 repository/evidence 中提取。

---

# 13.3 Final Feature Freeze 约束

G3-C 必须尊重 G3-B3-F 后的：

```text
FINAL FEATURE FREEZE
```

本阶段默认不得修改：

- collective semantics；
- algorithm families；
- Schedule IR semantics；
- Sparse codec；
- CRC/integrity semantics；
- retry semantics；
- flow-control semantics；
- topology model；
- cost model；
- selector；
- Agent proposal semantics；
- simulator formulas；
- benchmark matrix；
- benchmark seed；
- correctness tolerance；
- CPU_SIM public ABI；
- Direct source semantics。

如果在报告过程中发现：

```text
BLOCKING_CORRECTNESS_BUG
SOURCE_EVIDENCE_CONFLICT
REPORT_CANNOT_BE_MADE_TRUTHFUL_WITH_CURRENT_CODE
```

必须停止，记录问题，并由用户决定是否重新开放 Feature Freeze。

不得为了让报告数字更漂亮而修改代码或 evidence。

---

# 13.4 G3-C 非目标

G3-C 不负责：

- 新算法；
- 新 collective；
- Broadcast；
- AlltoAll；
- PairWise 实现；
- INT8 实现；
- Sparse 算法继续优化；
- CRC/retry继续扩展；
- Direct runtime执行；
- 新性能模型；
- 新硬件参数；
- 新 benchmark场景；-重新标定 HCCS/RoCE/PCIe；-重新生成 G3-B2/G3-B3 历史 benchmark；-训练 BERT/LLaMA；-调用 ACL/HCCL runtime；-真实 NPU；
  -MPI；-`hccl_test`；-`msprof`；-制作最终展示图；-制作视频；-制作最终 PDF；-创建 release/archive/tag。

最终图表美化属于 G3-E。

视频和演示属于 G3-F。

Release 与最终合规属于 G3-G。

---

# 13.5 权威证据层级

正式报告必须使用以下 source-of-truth hierarchy。

优先级从高到低：

```text
L1  G3-B3 merged main source/tests/configs
L2  G3-B3 final frozen evidence
L3  G3-B2 final frozen evidence
L4  G3-B native/reproducibility evidence
L5  G3-A requirement / claim / gap audit
L6  G2-F simulator / direct / integration evidence
L7  current engineering documentation
L8  historical documentation and notes
```

如果不同层级之间发生冲突：

### 当前代码行为

以：

```text
L1 → L2
```

为准。

### G3-B2 历史优化结果

必须继续以：

```text
G3-B2 frozen evidence
```

为准。

不得因为 G3-B3 出现新代码就修改 G3-B2 的历史实验结论。

### G2/G3-A/G3-B 历史状态

作为：

```text
HISTORICAL_EVIDENCE
```

保留。

不得覆盖。

---

# 13.6 证据身份体系

正式报告必须严格区分以下 truth / execution identities。

允许：

```text
HOST_EXECUTED
CPU_EXECUTED
SIMULATED_ONLY
LOSSLESS_SPARSE_HOST_EXECUTED
HOST_INTEGRITY_VALIDATED
HOST_RETRY_VALIDATED
SIMULATED_BACKPRESSURE
DIRECT_READINESS_ONLY
DIRECT_COMPILE_LINK_ONLY
REAL_DEVICE_NOT_EXECUTED
HISTORICAL_EVIDENCE
```

不得生成：

```text
REAL_DEVICE_MEASURED
REAL_DEVICE_PASS
DIRECT_RUNTIME_EXECUTED
REAL_HCCL_COLLECTIVE_EXECUTED
REAL_SPARSE_NETWORK_MEASURED
REAL_WIRE_BYTES_MEASURED
REAL_HARDWARE_CRC_VALIDATED
REAL_NIC_RETRY_VALIDATED
REAL_BACKPRESSURE_VALIDATED
REAL_TRAINING_SPEEDUP
NPU_UTILIZATION_MEASURED
MSPROF_EXECUTED
ZERO_CPU_INTERVENTION_VERIFIED
UB_HBM_REUSE_VERIFIED
```

---

# 13.7 两条主要证据主线

G3-C 必须明确区分两条技术证据主线。

## 13.7.1 G3-B2：调度与拓扑优化主线

用于证明：

```text
Collective Schedule IR v1
Ring / Butterfly / Mesh / NHR / Hierarchical
Topology-aware selection
Asymmetric topology handling
Adaptive chunking
Congestion-aware scheduling
Dynamic replanning
Bounded materialization
Simulated pipeline overlap
Agent optimization loop
A0–A7 ablation
```

G3-B2 的性能数字属于：

```text
SIMULATED_ONLY
```

其中最终 45.59283008% 只有在 final evidence 核验一致后才允许报告。

正式名称应类似：

```text
weighted simulated collective-time improvement
of the G3-B2 optimization stack
relative to the frozen fixed-Ring baseline
```

不得写成：

```text
45.59% real HCCL speedup
45.59% NPU speedup
45.59% training speedup
```

---

## 13.7.2 G3-B3：功能补齐主线

用于证明：

```text
Schedule IR v2
Lossless sparse payload transform
Dense fallback
Sparse break-even
Logical / payload / metadata / wire-byte accounting
CRC32
Sequence/chunk integrity
Logical timeout
Bounded retry
Failure classification
Credit/backpressure model
Agent feature proposal loop
B0–B6 feature ablation
Direct official API compile/link-only source
```

其中必须分别标记：

```text
Sparse correctness        → HOST_EXECUTED
CRC32                      → HOST_EXECUTED
Timeout/retry              → HOST_EXECUTED
Backpressure/performance   → SIMULATED_ONLY
Direct source              → DIRECT_COMPILE_LINK_ONLY
```

不得把上述能力全部笼统写成：

```text
真实通信系统已经验证
```

---

# 13.8 Machine-readable Report Data Ledger

必须建立：

```text
docs/submission/report_data_ledger.json
```

所有报告中的定量数字必须先进入 ledger，再进入 Markdown。

不得：

```text
evidence → 手工抄数字 → report
```

正确流程：

```text
evidence
→ extractor
→ report_data_ledger
→ report
→ verifier
```

---

# 13.9 Data Ledger Schema

每个 metric 至少包含：

```text
metric_id
metric_group
report_id
section_id

value
unit
display_value
rounding_rule

truth_label
execution_identity

checkpoint
feature_family
backend
track

primitive
algorithm
schedule_ir_version
topology
rank_size
message_size_bytes
dtype
reduce_op

source_path
source_json_pointer
source_sha256
source_evidence_root

extraction_method
limitations
```

---

# 13.10 G3-B3 扩展数据字段

Sparse/feature metrics 还应支持：

```text
sparsity_ratio
payload_mode
codec
logical_bytes
dense_wire_bytes
payload_bytes
value_bytes
index_bytes
metadata_bytes
modeled_wire_bytes
compression_ratio
dense_fallback
fallback_reason
encode_cost
decode_cost
break_even_status
```

Reliability metrics 支持：

```text
crc_type
corruption_type
corruption_detected
sequence_valid
attempt_count
max_retries
retransmitted_bytes
timeout_ticks
retry_status
terminal_reason
```

Flow-control metrics 支持：

```text
credit_window
max_inflight_chunks
peak_inflight_chunks
blocked_producer_events
credit_return_events
deadlock_detected
memory_budget_bytes
```

Direct metrics 支持：

```text
official_call_expression_count
compile_passed
link_passed
loaded=false
executed=false
runtime_api_calls=[]
```

---

# 13.11 Claim Ledger

必须建立：

```text
docs/submission/report_claim_ledger.json
```

每个重要结论至少记录：

```text
claim_id
report_id
claim_text
truth_label

allowed_wording
prohibited_wording

evidence_refs
metric_refs

limitations
hardware_dependency
status
```

---

# 13.12 必须建立的 Claim Boundary

至少明确以下结论：

### Logical scale

```text
1024 ranks
```

只能解释为：

```text
logical simulator scale
```

不是 1024 个真实设备。

---

### Logical large message

```text
1 GiB / 2 GiB
```

如采用 bounded materialization，只能解释为：

```text
logical message size validated under bounded host/simulator materialization
```

不是实机传输对应容量。

---

### 45.59283008%

只能解释为：

```text
G3-B2 weighted simulated collective-time improvement
```

---

### Sparse

Host sparse codec 能证明：

```text
lossless sparse semantics
reconstruction correctness
modeled payload-byte reduction
```

不能证明：

```text
physical network bytes reduced by same amount
real hardware acceleration
```

---

### CRC

Host CRC 能证明：

```text
CPU_SIM payload integrity detection
```

不能证明：

```text
hardware CRC
NIC CRC
HCCL internal CRC
```

---

### Retry

Host retry 能证明：

```text
bounded retry semantics
logical timeout handling
failure classification
```

不能证明：

```text
real HCCL transport retransmission
```

---

### Backpressure

只能：

```text
SIMULATED_BACKPRESSURE
```

---

### Direct

存在：

```text
actual official API call expressions
```

只证明 source readiness。

即使官方函数以：

```cpp
HcclAllReduce(...)
```

形式出现在源码中，也必须保持：

```text
direct_hccl_api_call=false
runtime_api_calls=[]
```

直到真实运行证据存在。

---

### INT8

必须报告：

```text
DEFERRED_BY_PRECISION_GATE
```

如果 final evidence 如此记录。

不得写成已实现量化压缩。

---

### PairWise

必须报告：

```text
SKIPPED_BY_VALUE_GATE
```

如果 final evidence 如此记录。

不得放入 implemented algorithm matrix。

---

# 13.13 正式报告目录

最终 G3-C 建议生成：

```text
docs/submission/reports/
├── README.md
├── 01_system_architecture_and_algorithm_design.md
├── 02_collective_schedule_ir_and_algorithm_evolution.md
├── 03_topology_and_hardware_model.md
├── 04_dense_and_sparse_correctness_report.md
├── 05_sparse_communication_and_wire_accounting_report.md
├── 06_simulator_performance_and_scale_report.md
├── 07_integrity_retry_and_reliability_report.md
├── 08_simulator_user_manual.md
├── 09_native_plugin_and_abi_appendix.md
├── 10_direct_compile_link_readiness_appendix.md
├── 11_known_limitations_and_future_hardware_plan.md
└── report_source_index.md
```

另生成：

```text
docs/submission/technical_report_index.md
```

作为正式报告入口。

---

# 13.14 所有报告统一头信息

每个正式报告顶部至少包含：

```text
Report Status
Source Commit
Evidence Snapshot
Execution Identity
Real-device Validated
Runtime API Executed
Applicable Checkpoints
```

例如：

```text
Report Status: FINAL_EVIDENCE_DERIVED
Source Commit: <merged-main-sha>
Real-device Validated: false
Runtime API Executed: false
```

不得写绝对本地路径。

---

# 13.15 所有报告统一章节结构

原则上每份正式报告包含：

```text
1. Purpose
2. Scope
3. Validation Identity
4. Source Evidence
5. Methodology
6. Results
7. Interpretation
8. Claim Boundaries
9. Known Limitations
10. Reproduction
11. Artifact References
```

根据报告内容可增减，但：

```text
Validation Identity
Claim Boundaries
Known Limitations
```

不得删除。

---

# 13.16 Report 01：System Architecture and Algorithm Design

文件：

```text
01_system_architecture_and_algorithm_design.md
```

必须覆盖：

## 总体架构

```text
Agent Control Plane
Schedule Layer
Topology Layer
Cost Model
Simulator
CPU_SIM
ASCEND_HCCL_VM
ASCEND_HCCL_DIRECT
Submission/Evidence Layer
```

明确：

```text
SIMULATOR_ACCEPTANCE
```

是独立验证 track，不是第四个 backend。

---

## Backend Registry

解释：

```text
CPU_SIM
ASCEND_HCCL_VM
ASCEND_HCCL_DIRECT
```

及：

```text
default backend=CPU_SIM
fallback=NONE
```

---

## 三原语

正式解释：

```text
AllReduce
AllGather
ReduceScatter
```

包括：

-输入/输出语义；
-rank布局；
-reduction语义；
-Schedule表达。

Broadcast/AlltoAll 不作为正式支持 primitive。

---

## 算法族

至少：

```text
Ring
Butterfly
Mesh
NHR
Hierarchical/Fat-Tree
```

建立正式支持矩阵。

不得把：

```text
PairWise
```

作为当前已实现算法，除非 final evidence 明确显示 OPTIONAL_COMPLETED。

---

## Algorithm Complexity

建立算法复杂度矩阵，包括：

```text
phase complexity
communication volume
latency sensitivity
bandwidth sensitivity
topology assumptions
rank constraints
message-size characteristics
```

复杂度必须来自实现和算法定义，不得杜撰实机效率。

---

## Agent Decision Loop

解释：

```text
input
→ candidate schedules
→ correctness hard gate
→ cost evaluation
→ selection
→ reflection
→ replanning
```

并区分：

```text
development_agent=Codex
runtime_agent=hccl-agent
human_reviewer=user
```

---

# 13.17 Report 02：Collective Schedule IR and Algorithm Evolution

文件：

```text
02_collective_schedule_ir_and_algorithm_evolution.md
```

这是 G3-B3 后新增的重要正式报告。

必须解释：

```text
Schedule IR v1
→ Schedule IR v2
```

---

## IR v1

说明 G3-B2：

```text
phases
transfers
chunks
routes
dependencies
memory plan
failure policy
schedule hash
```

---

## IR v2

说明 G3-B3 增加：

```text
payload transform
integrity policy
transport/retry policy
flow-control policy
logical/wire accounting
```

---

## Compatibility

明确：

```text
v1 historical evidence remains immutable
v2 does not rewrite v1 history
```

---

## Canonical Hash / C-Python Parity

必须从 evidence 提取：

```text
canonical schedule hash
C/Python parity
invariant validation
```

不得只写“经过测试”。

---

## Algorithm Schedule Examples

至少展示代表性：

```text
Ring AllReduce
Butterfly
NHR
Hierarchical
Sparse-aware schedule
```

使用 Mermaid/表格/structured pseudo-trace。

G3-C 可以生成 Mermaid 和表格，但最终专业图形留给 G3-E。

---

# 13.18 Report 03：Topology and Hardware Model

文件：

```text
03_topology_and_hardware_model.md
```

必须覆盖：

```text
Full Mesh
Ring
Fat-Tree
Hierarchical
Heterogeneous
Asymmetric links
Dynamic topology
No-path
```

---

## HCCS / RoCE / PCIe

所有：

```text
bandwidth
latency
fault probability
```

必须带 provenance。

明确：

```text
PROJECT_CONFIG
EXPLICIT_ASSUMPTION
DERIVED_ANALYTICAL
REAL_MEASUREMENT
```

当前无真实测量时不得标：

```text
REAL_MEASUREMENT
```

---

## Hardware Calibration

默认：

```text
hardware_calibrated=false
```

除非 evidence 明确证明相反。

---

## Topology Source

明确：

```text
topology_source=SIMULATOR_CONFIG
```

除非某具体 track 使用不同来源。

不得描述成：

```text
自动检测真实 1024 卡拓扑
```

---

# 13.19 Report 04：Dense and Sparse Correctness

文件：

```text
04_dense_and_sparse_correctness_report.md
```

G3-C 必须把 Dense 和 Sparse correctness 分开说明。

---

## Dense Correctness

覆盖：

```text
AllReduce
AllGather
ReduceScatter

FP32
FP16
BF16

SUM
MAX
MIN

rank coverage
message-size coverage
topology coverage
```

---

## Coverage Identity

每个 correctness 项必须分类：

```text
EXECUTED
SAMPLED
ANALYTICALLY_ACCOUNTED
NOT_APPLICABLE
NOT_TESTED
```

不得将 logical large-message 的 sampled/streamed correctness 写成 full physical materialization。

---

## Host Reference

解释：

```text
reference independence
exact cases
random/stress cases
output hash/error audit
```

---

## Sparse Correctness

必须正式解释：

```text
detect
encode
collective
reconstruct
validate
```

以及：

```text
per-rank different sparsity patterns
implicit zeros
index/value semantics
dense fallback
```

---

## Sparse 三原语

分别说明：

```text
Sparse AllReduce
Sparse AllGather
Sparse ReduceScatter
```

特别说明：

- AllReduce index union；
- SUM/MAX/MIN implicit-zero语义；
- AllGather rank boundaries；
- ReduceScatter local index remapping。

---

## Precision Boundary

必须继续保留：

```text
UA-C-001 / precision interpretation
```

若 FP16/BF16 的实际 tolerance 并非全局 `<=1e-6`，不得写成满足全局 `<=1e-6`。

---

# 13.20 Report 05：Sparse Communication and Wire Accounting

文件：

```text
05_sparse_communication_and_wire_accounting_report.md
```

这是 G3-B3 后新增的核心创新报告。

---

## Sparse Design

解释：

```text
LOSSLESS SPARSITY-AWARE PAYLOAD TRANSFORM
```

不是 Top-K、lossy gradient sparsification 或 quantization。

---

## Codec

说明：

```text
index/value representation
index width
canonical ordering
metadata
reconstruction
```

---

## Dense/Sparse Decision

必须从真实实现说明：

```text
dense cost
vs
sparse cost
```

而非简单“超过某稀疏率就启用”。

---

## Byte Accounting

必须明确区分：

```text
logical_bytes
payload_bytes
index_bytes
metadata_bytes
modeled_wire_bytes
```

必须突出：

```text
modeled_wire_bytes != physically measured NIC bytes
```

---

## Compression Ratio

只报告 evidence 中实际存在的 ratio。

不得使用：

```text
理论最高压缩率
```

作为实验结果。

---

## Break-even

必须展示：

```text
sparsity ratio
dense/sparse selected mode
modeled cost
wire-byte difference
fallback reason
```

正式回答：

> 从什么 sparsity range 开始，当前模型认为 Sparse 有收益？

若不同 message size 的 break-even 不同，必须分别报告。

---

## Dense Fallback

必须展示不利场景。

不得只报告：

```text
Sparse wins
```

---

## Large Logical Message

说明：

```text
bounded sparse materialization
```

和真实网络传输之间的区别。

---

# 13.21 Report 06：Simulator Performance and Scale

文件：

```text
06_simulator_performance_and_scale_report.md
```

报告标题必须明确包含：

```text
SIMULATOR
```

不得使用模糊标题：

```text
Performance Report
```

而让读者误以为是实机。

---

## G3-B2 Performance

正式报告：

```text
A0–A7
18 frozen performance scenarios
p50
p95
effective bandwidth
algorithm/topology selection
```

45.59283008% 只有在 ledger 与 final evidence 核对一致后才能进入报告。

---

## 18/0/0

若 final evidence 确认：

```text
18 wins
0 ties
0 losses
```

必须同时解释 baseline：

```text
fixed Ring baseline
```

以及优化栈包含哪些机制。

不得单独写：

```text
所有算法场景全面胜出
```

---

## Pipeline Caveat

如果最终 stage 包含：

```text
SIMULATED_PIPELINED_OVERLAP
```

必须单独声明：

```text
pipeline overlap is simulator-modeled
```

不能当作硬件验证。

---

## Scale

至少：

```text
8
16
64
1024 logical ranks
```

说明：

- p50；
- p95；
- bandwidth；
- trend；
- bottleneck。

---

## 90% 训练扩展目标

必须保持：

```text
TRAINING_LINEAR_SPEEDUP_NOT_VERIFIED=true
```

不得用 communication simulator scale 推导训练 scale >=90%。

---

## BERT / LLaMA

若只有 communication workload traces：

```text
real_model_executed=false
training_throughput=null
```

---

## Profiling

若没有：

```text
msprof
```

必须：

```text
profiling_source=SIMULATOR_TRACE
msprof_executed=false
```

---

# 13.22 Report 07：Integrity, Retry and Reliability

文件：

```text
07_integrity_retry_and_reliability_report.md
```

必须把 reliability 分层。

---

## Layer 1：Host Integrity

正式报告：

```text
CRC32
sequence/chunk identity
corruption detection
```

truth：

```text
HOST_INTEGRITY_VALIDATED
```

---

## Layer 2：Host Retry

正式报告：

```text
logical timeout
bounded retry
attempt accounting
retry exhaustion
failure classification
```

truth：

```text
HOST_RETRY_VALIDATED
```

---

## Layer 3：Simulator Reliability

报告：

```text
link degradation
link down
dynamic replan
no-path
large-scale fault scenarios
logical long-running scenarios
```

truth：

```text
SIMULATED_ONLY
```

---

## CRC

不得写：

```text
链路实现硬件 CRC32
```

正确表述：

```text
CPU_SIM host payload path validates CRC32 integrity semantics
```

---

## Timeout

必须写：

```text
logical timeout
```

而不是：

```text
real network timeout
```

---

## Retry

必须展示：

```text
retryable
non-retryable
terminal
```

失败分类。

---

## No-path

必须明确：

```text
EXPECTED_NO_PATH_FAILURE
```

是正确的失败语义，而不是 reliability failure。

---

## Flow Control / Backpressure

如果 final evidence 仍为模拟：

```text
SIMULATED_BACKPRESSURE
```

报告：

- credit window；
- max inflight；
- queue saturation；
- producer blocking；
- recovery；
- deadlock audit。

不得写：

```text
NIC backpressure implemented
```

---

## 100ms / 72h

若历史 evidence 包含：

```text
100ms recovery
logical 72h
```

必须分别写：

```text
simulated recovery time
logical event-simulation duration
```

---

# 13.23 Report 08：Simulator User Manual

文件：

```text
08_simulator_user_manual.md
```

该手册应成为当前正式 simulator 用户入口，并取代 stale guide。

至少包含：

```text
installation prerequisites
repository layout
backend selection
config format
topology config
hardware profile
primitive config
algorithm config
Schedule IR
dense mode
sparse mode
fault/reliability mode
seed
benchmark
replay
quick/full
evidence
SHA verification
limitations
```

---

## Sparse 使用说明

至少说明：

```text
data profile
sparsity
dense fallback
logical/wire accounting
```

---

## Reliability 使用说明

说明：

```text
corruption tests
logical timeout
retry
flow-control simulation
```

不得让用户误以为这些命令会操作真实 NIC。

---

## Direct

必须明确：

```text
Direct compile/link source is not executed by simulator CLI.
```

---

# 13.24 Report 09：Native Plugin and ABI Appendix

文件：

```text
09_native_plugin_and_abi_appendix.md
```

必须使用最终 G3-B3 freeze 后 native artifact。

记录：

```text
artifact name
identity
ABI version
SONAME
SHA256
exports
dependencies
language/toolchain
reproducibility
```

---

## ABI Truth

必须明确：

```text
CPU_SIM project ABI
!=
Direct control-plane/readiness ABI
!=
Official HCCL plugin-loader ABI
```

不得把 19 个 export 解释为：

```text
official plugin ABI verified
```

---

## Reproducibility

报告：

```text
double clean build
bit-for-bit status
CTest
consumer tests
```

数字从 G3-B3 final evidence 提取。

---

# 13.25 Report 10：Direct Compile/Link Readiness Appendix

文件：

```text
10_direct_compile_link_readiness_appendix.md
```

这是 G3-B3 后必须新增/重写的 appendix。

---

## Direct Evolution

解释：

```text
G2/G3-B:
signature / ABI / symbol / link readiness

G3-B3:
actual official API call expressions
compile/link-only production source path
```

---

## Call-expression Audit

必须报告 evidence 中实际数量。

当前 handoff 报告称：

```text
17 official ACL/HCCL call expressions
```

但正式报告必须从 G3-B3 final evidence 提取并核对，不能直接采用 handoff 文本。

---

## Runtime State

即使 call expression 存在：

```text
loaded=false
executed=false
real_device_api_executed=false
direct_hccl_api_call=false
runtime_api_calls=[]
```

---

## Lifecycle

报告源码设计：

```text
runtime init
device
context
stream
memory
communicator
collective
sync
reverse cleanup
```

只描述实际 source 中存在的部分。

不得补写不存在的 lifecycle。

---

## ELF Isolation

验证并报告：

```text
Direct artifact may link official libraries
CPU_SIM libhccl_plugin.so remains isolated
```

---

## Claim Boundary

正式结论：

```text
Direct Production Source Readiness: COMPLETED
Real-device Acceptance: HARDWARE_BLOCKED
```

---

# 13.26 Report 11：Known Limitations and Future Hardware Plan

文件：

```text
11_known_limitations_and_future_hardware_plan.md
```

必须集中列出所有仍无法解除的限制。

至少：

```text
no real Ascend NPU
no real ACL runtime execution
no real communicator
no real collective
official loader ABI not verified
no real HCCS/RoCE/PCIe measurement
no real sparse network byte measurement
no real sparse speedup
no real hardware CRC/parity
no real transport retry
no real NIC/HCCL backpressure
no msprof
no real BERT/LLaMA training
no real 90% training scale validation
no real failover timing
no real 72h stress
no zero-CPU verification
no UB/HBM reuse verification
INT8 deferred
```

---

# 13.27 Future Hardware Acceptance Plan

建立正式未来验收流程。

建议至少覆盖：

```text
1. supported Ascend environment detection
2. CANN version check
3. official library check
4. runtime initialization
5. device/context/stream
6. communicator bootstrap
7. device buffers
8. AllReduce correctness
9. AllGather correctness
10. ReduceScatter correctness
11. FP32/FP16/BF16
12. representative message sizes
13. topology discovery
14. real performance benchmark
15. sparse real-wire experiment
16. msprof
17. fault/retry acceptance where platform permits
18. long-running test
19. cleanup/leak audit
20. final REAL_DEVICE evidence freeze
```

必须注明：

```text
NOT EXECUTED IN G3-C
```

---

# 13.28 Report Source Index

生成：

```text
docs/submission/reports/report_source_index.md
```

每份报告映射到：

```text
source code
tests
configs
evidence
ledger metrics
claim IDs
```

例如：

```text
05_sparse...
  → G3-B3 final evidence
  → sparse codec source
  → sparse tests
  → report_data_ledger metric IDs
  → report_claim_ledger claim IDs
```

---

# 13.29 Report Tooling

建议新增：

```text
tools/reporting/
├── __init__.py
├── evidence_reader.py
├── ledger_builder.py
├── claim_builder.py
├── report_renderer.py
├── report_verifier.py
└── schemas.py
```

并提供统一 CLI：

```text
python -m tools.report_cli build
python -m tools.report_cli verify
python -m tools.report_cli describe
```

可选：

```text
python -m tools.report_cli extract
```

---

# 13.30 Reporting Tool 原则

优先使用：

```text
Python standard library
```

避免为 G3-C 新增第三方 dependency。

生成结果必须：

```text
deterministic
relative-path only
stable ordering
stable formatting
no local absolute paths
no current-clock dependent report content
```

除非 timestamp 是冻结 evidence 本身的一部分。

---

# 13.31 Build 行为

`build`：

```text
read frozen evidence
verify source SHA
build data ledger
build claim ledger
render Markdown reports
render chart-data
render indexes
```

不得：

```text
modify evidence
run performance benchmarks
modify source algorithms
```

---

# 13.32 Verify 行为

`verify` 至少验证：

```text
all ledger source files exist
all JSON pointers resolve
source SHA matches
report values match ledger
units match
rounding is correct
truth labels valid
claims have evidence
forbidden wording absent
links resolve
no absolute private paths
no stale final-baseline references
```

---

# 13.33 Describe 行为

`describe`：

```text
read-only
```

输出：

- source commit；
- evidence roots；
- report count；
- metric count；
- claim count；
- unresolved user actions；
- truth identities。

不得生成/修改文件。

---

# 13.34 Report Numeric Rules

所有数字必须：

1. 保存 raw value；
2. 明确单位；
3. 定义 rounding rule；
4. 报告显示值；
5. 保持 ledger 可回溯。

例如：

```text
raw=45.59283008
display=45.59%
rounding=2 decimal places
```

不得在不同报告中分别写：

```text
45.5%
45.59%
45.6%
```

而没有统一规则。

---

# 13.35 Latency / Bandwidth

必须统一：

```text
latency → us or ms
bandwidth → GB/s
```

并明确：

```text
GB/s
```

是否使用 decimal GB。

不要在表格中混用：

```text
Gbps
GB/s
```

而不解释。

---

# 13.36 Sparse Ratio

统一定义：

```text
sparsity_ratio
compression_ratio
wire_reduction_percent
```

不得混用。

例如：

```text
90% sparsity
```

不等于：

```text
90% wire reduction
```

---

# 13.37 Chart-data 输出

G3-C 不负责最终图形美化，但应提供 G3-E 的单一权威数据源。

目录：

```text
docs/submission/report_chart_data/
```

建议至少：

```text
correctness_coverage.json
algorithm_support_matrix.json
schedule_phase_comparison.json

g3_b2_latency_comparison.json
g3_b2_bandwidth_comparison.json
g3_b2_scale.json
g3_b2_ablation.json

sparse_compression_ratio.json
sparse_break_even.json
sparse_wire_bytes.json
sparse_dense_fallback.json

crc_retry_cases.json
reliability_outcomes.json
backpressure_behavior.json

direct_readiness_status.json
claim_boundary_summary.json
```

所有 chart-data 必须从 ledger 派生。

不得手工维护第二套数字。

---

# 13.38 G3-E 接口

G3-C 完成后：

```text
report_data_ledger.json
+
report_chart_data/
```

成为 G3-E 唯一数值来源。

G3-E 不得重新读取随机 benchmark 日志自行挑数字。

---

# 13.39 Stale Documentation Audit

生成：

```text
docs/submission/stale_document_audit.md
```

每个重要文档分类：

```text
CURRENT
SUPERSEDED
HISTORICAL
STALE
INTERNAL_REFERENCE
```

---

## G3-B2 Final Code Baseline

G3-B3 merge 后，应明确：

```text
G3-B2 Final Code Baseline
= HISTORICAL OPTIMIZATION BASELINE
```

不是 current final code。

---

## G3-B3 Final Feature Baseline

应：

```text
CURRENT FINAL FEATURE BASELINE
```

---

## 旧 simulator docs

若被新的：

```text
08_simulator_user_manual.md
```

取代，应：

```text
SUPERSEDED
```

不要删除历史文档。

---

# 13.40 Requirement Delta

不得修改 G3-A historical requirement matrix。

生成：

```text
docs/submission/g3_c_requirement_delta.json
```

G3-C 只评估：

```text
报告/文档/可复现性/traceability
```

带来的状态变化。

不要因为“写了报告”而把真实硬件要求升级。

---

# 13.41 G3-C 可能改善的 Requirement

若 evidence 和报告完整，可建议：

```text
documentation requirements
formal report requirements
algorithm explanation requirements
simulator manual requirements
reproducibility explanation requirements
```

由：

```text
PARTIAL
→ SATISFIED
```

---

# 13.42 不得因 G3-C 升级的 Requirement

以下不能因为写报告而升级：

```text
real performance
real training scale
real hardware topology
real failover
real 72h
msprof
zero CPU
UB/HBM reuse
official loader ABI
```

---

# 13.43 USER_ACTION_REQUIRED

继承：

```text
UA-B-001 project license/copyright
UA-B-002 official asset redistribution
UA-B-003 controlled competition material
UA-B-004 platform archive/size requirements
```

---

## UA-C-001：Precision Interpretation

确认赛事：

```text
<=1e-6
```

如何适用于：

```text
FP32
FP16
BF16
```

在用户未确认前：

```text
FP16/BF16 global <=1e-6
```

不得成为正式 claim。

---

## UA-C-002：Final Report Language

默认：

```text
Chinese body
+
English technical terminology
```

该项不阻塞 Markdown 技术报告生成。

---

## UA-C-003：Final Submission Template

待确认：

```text
page limit
cover
font
anonymous requirement
template
PDF format
```

不阻塞 G3-C Markdown source。

---

# 13.44 G3-C Test Requirements

至少覆盖：

## Ledger

1. schema validation；
2. unique metric ID；
3. valid source path；
4. valid JSON pointer；
5. source SHA；
6. unit validation；
7. rounding；
8. truth identity；
9. no unsupported truth labels。

## Claims

10. unique claim ID；
11. evidence mapping；
12. allowed wording；
13. prohibited wording；
14. real-device forbidden claims；
15. Sparse boundary；
16. CRC boundary；
17. retry boundary；
18. backpressure boundary；
19. Direct call-expression/runtime distinction；
20. INT8 deferred status；
21. PairWise gate status。

## Reports

22. all required reports exist；
23. required headings；
24. source commit；
25. evidence snapshot；
26. truth identity；
27. known limitations；
28. reproduction instructions；
29. no broken relative links；
30. no absolute user paths。

## G3-B2

31. 45.59283008 source trace；
32. 18/0/0 source trace；
33. A0–A7 source trace；
34. pipeline caveat；
35. logical 1024 caveat。

## G3-B3

36. Sparse correctness source；
37. break-even source；
38. wire-byte source；
39. dense fallback source；
40. CRC source；
41. retry source；
42. timeout source；
43. flow-control source；
44. Direct call-expression source；
45. direct runtime=false。

## Documentation

46. stale-doc audit；
47. G3-B2 historical baseline；
48. G3-B3 current baseline；
49. source index completeness；
50. chart-data derived from ledger。

## Regression / Evidence

51. G3-B2 SHA；
52. G3-B3 SHA；
53. current source commit；
54. no old evidence modification；
55. staging integration；
56. HCOMM/HCCL frozen references clean if checked；
57. worktree clean.

实际测试数量可更多。

不得新增无理由 skip。

---

# 13.45 G3-C Evidence

只生成一个最终 authority evidence：

```text
experiments/submission/evidence/
    g3_c_<timestamp>/
```

至少包含：

```text
README.md
manifest.json
result.json

source_hierarchy.json
source_commit.json
evidence_inventory.json

report_inventory.json
report_data_ledger.json
report_claim_ledger.json
report_source_index.json

numeric_traceability_audit.json
claim_boundary_audit.json
forbidden_claim_audit.json
truth_identity_audit.json

g3_b2_reporting_audit.json
g3_b3_reporting_audit.json

sparse_reporting_audit.json
reliability_reporting_audit.json
direct_reporting_audit.json

stale_document_audit.json
requirement_delta.json
user_action_required.json

report_verification.json
chart_data_verification.json
staging_verification.json
regression_summary.json

SHA256SUMS
```

---

# 13.46 Evidence 真实性字段

最终 `result.json` 至少：

```text
checkpoint=G3-C
checkpoint_status=COMPLETED

formal_report_suite=COMPLETED

system_architecture_report=COMPLETED
schedule_ir_report=COMPLETED
topology_hardware_report=COMPLETED
dense_sparse_correctness_report=COMPLETED
sparse_communication_report=COMPLETED
simulator_performance_scale_report=COMPLETED
integrity_retry_reliability_report=COMPLETED
simulator_manual=COMPLETED
native_plugin_appendix=COMPLETED
direct_compile_link_appendix=COMPLETED
limitations_hardware_plan=COMPLETED

data_ledger=COMPLETED
claim_ledger=COMPLETED
chart_data=COMPLETED
stale_document_audit=COMPLETED

final_feature_freeze_preserved=true
old_evidence_modified=false

performance_target_achievement=PARTIALLY_SATISFIED
c_cpp_plugin_compliance=PARTIALLY_SATISFIED
submission_release_readiness=PARTIAL
g3_delivery_readiness=PARTIAL
real_device_acceptance=HARDWARE_BLOCKED

real_device_api_executed=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
measured_on_real_npu=false
real_model_executed=false
msprof_executed=false
runtime_api_calls=[]
```

---

# 13.47 G3-C Completion Gate

只有以下全部满足才可：

```text
G3-C: COMPLETED
```

要求：

- G3-B3 已 merge；
- current source baseline frozen；
- G3-B2 SHA PASS；
- G3-B3 SHA PASS；
- data ledger 完整；
- claim ledger 完整；
- 所有正式 reports 完成；-所有定量数字可回溯；
  -Sparse truth boundary 完整；
  -CRC/retry truth boundary 完整；
  -backpressure truth boundary 完整；
  -Direct compile-link/runtime边界完整；
  -INT8状态真实；
  -PairWise状态真实；
  -45.59283008%有唯一来源；
  -18/0/0有唯一来源；
  -no real-device overclaim；
  -simulator manual完成；
  -stale docs audit完成；
  -chart-data完成；
  -report verify PASS；
  -staging verify PASS；
  -final evidence SHA PASS；
  -old evidence未修改；
  -Feature Freeze未重新打开；
  -worktree clean；-未执行真实设备 API；-未开始 G3-D/G3-E/G3-F。

---

# 13.48 Block Classification

## ENV_BLOCKED

仅：

```text
evidence unreadable
repository corruption
Python/report tooling environment failure
```

---

## USER_ACTION_REQUIRED

用于：

```text
precision interpretation
report language
submission template
license/copyright
redistribution
controlled competition material
archive constraints
```

---

## HARDWARE_BLOCKED

只用于：

```text
real NPU
real ACL/HCCL
real communicator
real collective
real topology
real profiler
real training
real failover
real long-running stress
```

---

## FAIL

用于：

```text
report number cannot trace to evidence
claim lacks evidence
truth label incorrect
real-device overclaim
Sparse byte model called physical measurement
Direct call-expression called runtime execution
45.59% misrepresented
broken links
ledger/report mismatch
old evidence modified
```

不得将报告或数据错误标记为 HARDWARE_BLOCKED。

---

# 13.49 Branch / Commit / Stop Boundary

建议分支：

```text
codex/g3-c-final-formal-report-suite
```

G3-C 允许一个 `/goal` 完整执行。

建议最终 commit：

```text
G3-C build final evidence-derived competition report suite
```

默认只创建一个 G3-C 本地 commit。

如果 Codex 因实现 reporting infrastructure 确实需要内部恢复点，可创建少量阶段性 commit，但不得把 G3-C 拆成多个 branch/PR。

完成后：

```text
STOP
```

不得：

```text
push
merge
start G3-D
start G3-E
start G3-F
create PDF
create release
create archive
```

---

# 13.50 G3-D / G3-E 的正式接口

G3-C 完成后向 G3-D 提供：

```text
report_claim_ledger.json
Agent-related report sections
source/evidence index
G3-B2 optimization trace references
G3-B3 feature proposal trace references
```

G3-D 不应重新发明项目能力描述。

---

G3-C 向 G3-E 提供：

```text
report_data_ledger.json
report_chart_data/
```

G3-E 不应重新运行 benchmark 或手工选择数字。

---

# 13.51 最终证据链

完成后项目正式证据链应为：

```text
G2-F
│
├── simulator / direct / integration foundations
│
G3-A
│
├── competition gap and claim audit
│
G3-B
│
├── reproducible native delivery / staging
│
G3-B2
│
├── schedule / topology / algorithm optimization
│   └── A0–A7 + frozen simulated performance
│
G3-B3
│
├── sparse / integrity / retry / backpressure
│   └── IR v2 + Direct compile-link source
│
G3-C
│
└── evidence-derived formal technical report system
```

G3-C 的职责不是制造新 evidence，而是将以上 evidence 转化成：

```text
一套一致、正式、可信、可审计的技术叙事。
```

# 14. G3-D — Agent / Prompt Reproducible Delivery

## 14.1 阶段定位

G3-D 的正式名称为：

```text
G3-D — Agent / Prompt Reproducible Delivery
```

阶段身份为：

```text
DELIVERY
REPRODUCIBILITY
PROVENANCE
SUBMISSION READINESS
```

G3-D 在 G3-C 完成并合并进入 `main` 后执行。核心目标是把当前已经存在的 Agent、Prompt、Skills、proposal/evaluation/reflection/replanning records、human intervention records、source/commit/evidence mappings，以及 G3-B2/G3-B3 frozen evidence，整理成比赛可提交、可解释、可审计、可离线复现的正式 Agent/Prompt 交付体系。

G3-D 不是新的 Agent feature development 阶段。G3-B3-F 建立的：

```text
FINAL FEATURE FREEZE
```

继续有效。

G3-D 不得重新设计 Agent，不得新增算法能力，不得重新优化 benchmark，不得修改冻结功能语义，也不得通过重放材料制造新的历史事实。

最终评审者必须能够从提交材料中直接回答：

1. Agent 由哪些当前源码模块组成；
2. 当前实际使用或冻结记录引用了哪些 Prompt；
3. 每个 Prompt 的版本、来源、hash 和输入输出 contract 是什么；
4. Agent 可以调用哪些真实存在的 Skill；
5. 哪些步骤是 Agent proposal；
6. 哪些步骤是 deterministic evaluation；
7. 哪些步骤包含 human input、approval 或 intervention；
8. 哪些 trace 是历史冻结证据；
9. 哪些记录只是 replay 或 reconstruction；
10. Prompt、Skill、Trace、Source、Commit、Evidence 与 G3-C Claim 如何映射；
11. 在没有 DeepSeek、OpenAI、Anthropic API Key 时，mandatory replay 与 verification 是否仍可完成。

---

## 14.2 当前实现与证据基线

G3-D-A 开始时必须以 merged `main` 重新验证以下盘点结论，不得只复制本计划中的描述。

### Agent entry 与模块

当前已知入口和模块包括：

```text
main.py
agent/hccl_agent.py
agent/llm_client.py
agent/prompt_engine.py
agent/g3_b2_optimization_loop.py
agent/g3_b3_feature_loop.py
agent/autonomous_development_loop.py
agent/*_skill.py
skills/*.py
```

其中：

- `HCCLAgent` 是现有综合编排入口；
- `LLMClient` 是 DeepSeek online client，缺少 Key 时会失败，由上层 best-effort 路径降级；
- `AgentPromptEngine` 读取 `prompts/algorithm_prompt.txt` 并把本机调用日志写入 ignored `logs/`；
- `g3_b2_optimization_loop.py` 是 deterministic、replayable 的 Schedule optimization chain；
- `g3_b3_feature_loop.py` 是 deterministic、replayable 的 sparse/integrity/flow feature decision chain；
- `OfflineDevelopmentLoop` 是隔离临时目录中的 `OFFLINE_TEMPLATE` 演示，不等同 G3-B2/G3-B3 historical Agent execution；
- ignored `logs/`、临时目录输出和本机私有日志不是 authority evidence。

### Prompt

当前存在：

```text
prompts/algorithm_prompt.txt
prompts/g3_b2/schedule_generation_v1.md
prompts/g3_b2/topology_optimization_v1.md
prompts/g3_b2/benchmark_evaluation_v1.md
prompts/g3_b2/reflection_v1.md
prompts/g3_b2/replanning_v1.md
```

`agent/evidence/g3_b2/prompt_registry.json` 已冻结 5 个 G3-B2 Prompt 的 `prompt_id`、`version=1.0.0`、source path 和 SHA256。G3-D 必须复用并验证该 registry。

`prompts/algorithm_prompt.txt` 的多个 section 当前没有等价的完整比赛 registry contract；必须在 G3-D 中登记 current canonical source，但不得反向伪造 historical version。

G3-B3 deterministic feature loop 当前没有独立、可证明的 historical Prompt/Response log。G3-D 必须将其 proposal/evaluation/reflection 归入 frozen deterministic trace；若无法证明 historical Prompt relationship，使用：

```text
HISTORICAL_TRACE_UNAVAILABLE
```

或：

```text
RECONSTRUCTED_FROM_FROZEN_EVIDENCE
```

不得为 G3-B3 补造 Prompt。

### Skill

当前 `agent/` 与 `skills/` 中存在 planning、reasoning、selection、execution、evaluation、reflection、replanning、explanation、benchmark、proposal、optimization、topology、hardware、knowledge 和 reporting 等模块。

当前没有统一、提交级的 Skill Registry。G3-D-B 必须先从真实 source、imports、tests 和 frozen evidence 建立 registry，不得仅按文件名把模块全部声明成已实现 Skill。

### Frozen Agent traces

G3-B2 已有：

```text
agent/evidence/g3_b2/trace_manifest.json
agent/evidence/g3_b2/prompt_registry.json
agent/evidence/g3_b2/human_intervention.json
agent/evidence/g3_b2/commit_mapping.json
agent/evidence/g3_b2/runs/
agent/evidence/g3_b2/proposals/
agent/evidence/g3_b2/evaluations/
agent/evidence/g3_b2/reflections/
```

并由 G3-B2 final evidence 的 `agent_trace_inventory.json` 逐文件 hash 锚定。

G3-B3 已有 20 条 proposal、20 条 evaluation、20 条 reflection 记录，source authority 通过 G3-B3 final `manifest.json` 指向：

```text
experiments/feature_completion/evidence/
    g3_b3_d_agent_flow_20260807T150515Z/
```

其 SHA256SUMS digest 已由 final manifest 锚定。G3-D 不得复制或修改这些 frozen records，只能以 pointer/hash 引用和归一化解释。

### 当前交付缺口

G3-D 当前需要关闭：

1. 缺统一 Agent/Prompt delivery contract；
2. 缺完整 Prompt Registry；
3. 缺提交级 Skill Registry；
4. 缺跨 G3-B2/G3-B3 的 normalized trace schema/index；
5. 缺只读取 frozen evidence 的统一 offline replay/verify 入口；
6. 缺 human/Agent/deterministic/reconstructed provenance 的统一披露；
7. 缺 Prompt→Skill→Trace→Source→Commit→Evidence→Claim 的正式映射；
8. 缺 Agent/Prompt 专项 staging 与最终 authority evidence。

这些都是交付与可复现性缺口，不授权重新打开 Agent 或通信功能开发。

---

## 14.3 Authority hierarchy

G3-D 必须使用以下权威层级，优先级从高到低。

### L1：merged main Final Feature Freeze source

```text
当前 merged main 上的 source / tests / configs
```

它定义当前实现事实、当前入口、当前 Prompt/Skill source 和 current canonical behavior。

### L2：G3-C formal reporting system

至少包括：

```text
docs/submission/report_claim_ledger.json
docs/submission/report_data_ledger.json
docs/submission/report_chart_data/
docs/submission/reports/
docs/submission/reports/report_source_index.md
experiments/submission/evidence/g3_c_20260809T000000Z/
```

其中 `docs/submission/report_claim_ledger.json` 是 G3-D 对外 claim language 和 claim boundary 的最高权威之一。

### L3：G3-B3 final feature completion evidence

权威 evidence root：

```text
experiments/feature_completion/evidence/
    g3_b3_f_final_20260807T170000Z
```

权威 `SHA256SUMS` digest：

```text
45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754
```

重点消费 Agent proposal v2、Schedule IR v2、20 proposal/evaluation/reflection inventory、implemented/deferred/skipped gate decisions、feature ablation、human/deterministic gate information where recorded，以及 source evidence pointers。

### L4：G3-B2 optimization evidence

权威 evidence root：

```text
experiments/optimization/evidence/
    g3_b2_f_final_20260807T040000Z
```

权威 `SHA256SUMS` digest：

```text
99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483
```

重点消费 Agent optimization trace、proposal、evaluation、reflection、replanning、A0-A7 ablation、human intervention、commit mapping 和 prompt registry。

### L5：G3-A requirement / gap / claim audit

重点消费：

```text
REQ-AGENT-002
REQ-AGENT-004
REQ-AGENT-005
REQ-AGENT-006
REQ-AGENT-007
REQ-DOC-005
REQ-PACKAGE-002
corresponding risks and roadmap assignments
```

G3-A 是 historical audit。G3-D 不得覆盖或修改 G3-A historical requirement matrix；只能生成 G3-D 独立 validation/result，并说明当前新增交付如何响应旧 gap。

### 冲突规则

```text
current implementation fact        → L1
external claim wording             → L2 claim ledger
G3-B3 historical feature decision  → L3
G3-B2 historical optimization      → L4
historical gap identity            → L5
```

无法按层级消解的冲突必须：

```text
STOP
status=BLOCKED_BY_AUTHORITY_CONFLICT
```

不得选择更有利的描述。

---

## 14.4 Truth / provenance vocabulary

G3-D 必须建立统一、machine-readable 的 provenance vocabulary，至少包含：

```text
AGENT_GENERATED
DETERMINISTIC_EVALUATION
HUMAN_INTERVENTION
HISTORICAL_EVIDENCE
REPLAYED_FROM_FROZEN_TRACE
RECONSTRUCTED_FROM_FROZEN_EVIDENCE
HISTORICAL_TRACE_UNAVAILABLE
OFFLINE_REPLAY
ONLINE_LLM_OPTIONAL
```

| Vocabulary | 允许含义 |
| ---------- | -------- |
| `AGENT_GENERATED` | frozen record 明确把某个 proposal/output 标识为 Agent 生成；不自动表示无人干预或 LLM 生成 |
| `DETERMINISTIC_EVALUATION` | 当前 source/test 或 frozen evidence 可确定性复算的 schema、correctness、cost、gate 或 selection |
| `HUMAN_INTERVENTION` | 有明确 actor、decision、scope 或 approval record 的人工输入/干预 |
| `HISTORICAL_EVIDENCE` | G3-D 之前已经冻结且 hash 可验证的原始仓库 evidence |
| `REPLAYED_FROM_FROZEN_TRACE` | G3-D 使用 frozen trace 输入按固定规则重放的结果；不是历史执行本身 |
| `RECONSTRUCTED_FROM_FROZEN_EVIDENCE` | 由多个 frozen artifact 组合出的解释或 normalized record；不是 original Agent log |
| `HISTORICAL_TRACE_UNAVAILABLE` | 历史 Prompt、Response、execution log 或关系无法从 authority source 证明 |
| `OFFLINE_REPLAY` | 不使用外部模型、网络或 API Key 的 mandatory deterministic replay |
| `ONLINE_LLM_OPTIONAL` | 已存在但不属于 mandatory submission path 的 online LLM 能力 |

允许新增更细 vocabulary，但必须先写入 schema/allowlist，并保持以上含义不变。

以下区分必须始终存在：

```text
historical execution
!=
G3-D replay
!=
G3-D reconstruction
```

如果缺乏原始历史 Prompt/Response/Agent execution log，必须标记 `HISTORICAL_TRACE_UNAVAILABLE` 或 `RECONSTRUCTED_FROM_FROZEN_EVIDENCE`。

不得补造历史时间戳、未保存的 Prompt/Response、hidden chain-of-thought、Agent 内部推理过程、未证明的人工决策、未证明的 source/commit relationship 或“全部代码由 Agent 自主生成”结论。

G3-D 不得输出或保存 hidden chain-of-thought。对外只允许可审计 decision record，例如：

```text
input
proposal
deterministic_evaluation
reflection_or_replanning_result
final_decision
human_intervention_status
evidence_pointer
```

---

## 14.5 Mandatory offline boundary

G3-D mandatory path 必须完全 offline。

不得要求：

```text
DEEPSEEK_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
```

不得发起真实外部模型请求，不得把 network availability 作为通过条件。

现有 DeepSeek `LLMClient` 可以继续存在，但只能登记为 `ONLINE_LLM_OPTIONAL`。G3-D 不得为了本阶段重新设计 LLM client、provider abstraction 或 Agent reasoning semantics。

submission mandatory path 必须通过 `OFFLINE_REPLAY` 完成，并满足：

1. 不实例化或调用 online LLM client；
2. 不读取或要求 API Key；
3. 不访问网络；
4. 读取 frozen trace/evidence；
5. 校验 schema、hash、source pointer；
6. 确定性重放 proposal→evaluation→reflection/replanning→final decision；
7. 输出 machine-readable canonical JSON；
8. 多次运行产生相同 canonical output/hash；
9. 不修改 frozen evidence；
10. 不把 replay 标记成 historical execution。

现有 `HCCLAgent.run()` 会包含日志写入、best-effort online reasoning 和 CPU_SIM execution orchestration，因此不得直接作为 G3-D mandatory replay contract。G3-D 应复用已有 deterministic G3-B2/G3-B3 loop、schema、validator 和 evidence reader，在其上建立最小 delivery wrapper。

---

## 14.6 G3-C Claim Ledger boundary

`docs/submission/report_claim_ledger.json` 是 G3-D 对外 claim language authority。

G3-D 不得为了 Agent 文档修改 claim ledger 来放宽 claim。若 G3-D wording 与 ledger 冲突：

```text
modify G3-D wording
```

不得修改 ledger 以迁就 G3-D。

必须继续保持：

```text
LOSSLESS_SPARSE_HOST_EXECUTED
HOST_INTEGRITY_VALIDATED
HOST_RETRY_VALIDATED
SIMULATED_BACKPRESSURE
SIMULATED_ONLY
DIRECT_COMPILE_LINK_ONLY
REAL_DEVICE_NOT_EXECUTED
```

特别禁止：

- 把 `45.59283008%` raw / `45.59%` display 写成真实 Ascend/NPU/HCCL/training 性能提升；
- 把 18 wins / 0 ties / 0 losses 写成真实 workloads 全胜；
- 把 official ACL/HCCL call expressions 写成 real-device execution；
- 把 sparse modeled wire bytes 写成物理 NIC measurement；
- 把 host CRC/retry 写成 HCCL/NIC reliability；
- 把 backpressure model 写成真实 NIC backpressure；
- 把 optional online LLM 写成 mandatory autonomous Agent；
- 无 evidence 使用 `fully autonomous`。

优先使用受 evidence 支持的描述：

```text
Agent-assisted
Agent-generated proposal
deterministically evaluated
human-governed
offline replayable
evidence-backed
```

---

## 14.7 Feature Freeze 与 hardware boundary

### Feature Freeze boundary

G3-D 禁止修改：

```text
collective algorithms
algorithm semantics
Schedule IR execution semantics
topology optimization semantics
Sparse codec semantics
CRC / integrity semantics
timeout / retry semantics
flow-control / backpressure semantics
selector behavior
performance model
simulator equations
benchmark scenarios / results
correctness thresholds
CPU_SIM public ABI
SONAME
19-symbol allowlist
Direct runtime semantics
G3-B2 frozen evidence
G3-B3 frozen evidence
G3-C factual ledgers
```

允许的实现范围只有：

```text
delivery metadata
registry/schema
read-only evidence readers
normalization
offline replay wrapper
verification
documentation
staging integration
new G3-D evidence
```

如果完成任务必须修改冻结项目：

```text
STOP
record blocker
do not reopen Final Feature Freeze
```

### Hardware boundary

G3-D 不允许执行：

```text
ACL runtime
HCCL runtime
device/context/stream
communicator
real collective
MPI
hccl_test
msprof
```

Real-device acceptance 继续为 `HARDWARE_BLOCKED`，除非未来独立取得真实硬件 evidence。

G3-D 不得产生：

```text
REAL_DEVICE_PASS
real_ascend_npu_validated=true
direct_hccl_api_call=true
real_device_api_executed=true
runtime_api_calls=[...]
```

---

## 14.8 G3-D 总体 checkpoint

G3-D 拆分为五个有序阶段：

| Checkpoint | 名称 | 核心目标 |
| ---------- | ---- | -------- |
| G3-D-A | Authority, Inventory and Delivery Contract | 冻结 authority、inventory、truth 与 delivery contract |
| G3-D-B | Prompt Registry and Skill Registry | 建立 current canonical Prompt/Skill registries |
| G3-D-C | Trace Normalization and Offline Replay | 归一化 G3-B2/G3-B3 frozen traces 并提供 deterministic offline replay |
| G3-D-D | Provenance, Human Intervention and Submission Documentation | 完成正式 Agent/Prompt 文档和 provenance/autonomy disclosure |
| G3-D-E | Final Validation, Staging and Evidence Freeze | 完成测试、staging、唯一最终 evidence 与 SHA freeze |

必须按：

```text
G3-D-A → G3-D-B → G3-D-C → G3-D-D → G3-D-E
```

顺序执行。不得在 inventory/contract 完成前创建重复实现。

---

## 14.9 G3-D-A — Authority, Inventory and Delivery Contract

### Objective

冻结 G3-D Agent/Prompt delivery contract，并完整盘点当前已有实现、tests、documentation、staging 和 historical frozen evidence。本阶段只建立交付 contract，不做 Agent feature enhancement。

### Inputs / Authority

必须读取并验证：

```text
agent/
skills/
prompts/
tools/
tests/
experiments/optimization/
experiments/feature_completion/
docs/submission/
```

以及 14.3 的 L1–L5 authority。必须验证 G3-B2/G3-B3 `SHA256SUMS` digest 与 final manifest source pointer，不得只检查目录存在。

### Implementation scope

盘点至少覆盖：

```text
Agent entry point
backend boundary
LLM boundary
prompt engine
prompt files
prompt registry
skill registry status
planning
reasoning
candidate generation
selection
evaluation
execution
reflection
replanning
explanation
benchmark integration
Schedule IR integration
feature proposal path
optimization trace
human intervention representation
commit/source mapping
replay capability
logging side effects
staging coverage
tests
```

每项必须记录：

```text
component_id
component_type
source_path
authority_level
current_status
frozen_status
entry_or_owner
inputs
outputs
side_effects
online_dependency
tests
relevant_evidence
historical_record_availability
provenance
g3_d_output_mapping
limitations
```

状态至少允许：

```text
CURRENT_IMPLEMENTED
FROZEN_HISTORICAL
PARTIAL
OPTIONAL_ONLINE
DOCUMENTATION_ONLY
HISTORICAL_TRACE_UNAVAILABLE
NOT_IN_SCOPE
```

不得把 aspirational docs、roadmap、Prompt text 或文件名当作 implemented capability。

### Expected artifacts

建议建立：

```text
docs/submission/agent_delivery/
├── delivery_contract.json
├── authority_inventory.json
└── inventory_summary.md
```

`delivery_contract.json` 至少冻结 schema versions、authority roots/hashes、provenance vocabulary、mandatory offline rule、forbidden claims、Feature Freeze boundary、hardware boundary、expected artifacts、staging destinations 和 validation sentinels。

### Tests / Acceptance criteria

至少验证：

1. inventory 中每个 source/test/evidence path 存在；
2. authority level 合法；
3. status 与 provenance vocabulary 合法；
4. G3-B2/G3-B3 SHA authority PASS；
5. G3-C claim/data ledger 可读取；
6. ignored local logs 不作为 authority；
7. roadmap-only capability 不标 implemented；
8. online/offline、side-effect 和 hardware boundary 完整；
9. required artifact mapping 完整；
10. 只使用 repository-relative paths。

预期 sentinel：

```text
G3_D_AUTHORITY_INVENTORY_OK
```

### Truth boundaries

- inventory 是 G3-D 当前盘点，不是 historical Agent log；
- source/hash 证明文件身份，不证明某次历史调用；
- `HCCLAgent` module existence 不证明所有生产代码由 Agent 生成；
- `OfflineDevelopmentLoop` 只证明受控模板演示，不证明 online LLM 自主开发；
- ignored `logs/` 不得升级成 official evidence。

### Forbidden changes

- 不修改 Agent/Skill/Prompt behavior；
- 不新增 replay engine；
- 不修改 frozen evidence 或 G3-C ledger；
- 不更新算法或 benchmark；
- contract/inventory 验证通过前不得创建后续重复实现。

### Commit boundary

本阶段只允许提交 authority、inventory、delivery contract 及其 focused tests/validator。

建议 commit：

```text
G3-D-A freeze Agent prompt delivery contract
```

### Exit criteria

- authority hierarchy frozen；
- current component inventory complete；
- historical availability逐项标记；
- G3-B2/G3-B3 authority hash validated；
- G3-C ledger authority recorded；
- offline/online boundary recorded；
- Feature Freeze/hardware boundary recorded；
- no duplicate implementation created；
- focused G3-D-A tests PASS；
- working diff limited to G3-D-A scope。

---

## 14.10 G3-D-B — Prompt Registry and Skill Registry

### Objective

建立比赛正式使用的 Prompt Registry 与 Skill Registry，并将 current canonical source、frozen historical references、tests 和 provenance 统一映射。

### Inputs / Authority

优先复用：

```text
agent/evidence/g3_b2/prompt_registry.json
agent/evidence/g3_b2/trace_manifest.json
prompts/g3_b2/*.md
prompts/algorithm_prompt.txt
agent/prompt_engine.py
agent/reasoning_skill.py
agent/g3_b2_optimization_loop.py
agent/g3_b3_feature_loop.py
agent/*_skill.py
skills/*.py
tests/
G3-B2/G3-B3 frozen evidence
G3-D-A authority_inventory.json
```

禁止无必要重新设计 G3-B2/G3-B3 已有 schema。

### Implementation scope

#### Prompt Registry

每项应尽可能记录：

```text
prompt_id
current_canonical_version
historical_version_status
purpose
source_path
source_sha256
owning_stage
owning_module
input_contract
output_contract
referenced_skills
online_offline_classification
provenance
source_commit
evidence_pointer
tests
limitations
```

规则：

1. 复用 G3-B2 的五个 frozen prompt_id/version/hash；
2. 对 `prompts/algorithm_prompt.txt` 可建立 current canonical registry entries 或 section entries，但 version 只能表示 G3-D current canonical source；
3. 若 historical prompt version 从未存在，必须设置 `historical_version_status=HISTORICAL_TRACE_UNAVAILABLE`；
4. G3-B3 deterministic proposal/evaluation 不得伪装成有 historical Prompt/Response；
5. source hash 必须基于 repository bytes；
6. Prompt 中 aspirational/overclaim wording 必须在 limitations 中披露，不能据此升级 capability claim。

#### Skill Registry

每项应尽可能记录：

```text
skill_id
name
source_path
source_sha256
purpose
inputs
outputs
deterministic_classification
side_effects
online_dependency
agent_stage
prompt_dependency
tests
frozen_evidence
status
provenance
limitations
```

classification 至少区分：

```text
DETERMINISTIC
OPTIONAL_ONLINE
HOST_EXECUTED
SIMULATOR_MODEL
DELIVERY_ONLY
```

只登记当前源码真实存在并可映射到 tests/evidence 的能力。没有 focused tests 的项必须明确标记 test gap，不得虚构 coverage。

### Expected artifacts

```text
docs/submission/agent_delivery/
├── prompt_registry.json
├── prompt_registry.md
├── skill_registry.json
└── skill_registry.md
```

如 schema 需要独立文件，建议使用 `tools/agent_delivery/schemas.py`，但不得引入第三方 dependency 或新的 packaging framework。

### Tests / Acceptance criteria

至少验证：

1. registry schema；
2. prompt_id/skill_id 唯一；
3. source path 存在且相对；
4. source SHA256 匹配；
5. G3-B2 frozen registry 未改变；
6. prompt input/output contract 非空或明确 unavailable；
7. historical unavailable 不被虚构 version 替代；
8. Skill source/import/test mapping 可解析；
9. online Skill 不进入 mandatory replay dependency；
10. roadmap-only/Prompt-only capability 不得标 `CURRENT_IMPLEMENTED`；
11. secrets、absolute local paths 和 raw private logs 不进入 registry；
12. stable ordering 与 deterministic serialization。

预期 sentinels：

```text
PROMPT_REGISTRY_OK
SKILL_REGISTRY_OK
```

### Truth boundaries

- current canonical Prompt version 不等于 historical execution version；
- Prompt source existence 不证明它被某个 historical run 调用；
- Skill registration 不证明真实硬件执行；
- `ReasoningSkill`/`LLMClient` 只能标 `ONLINE_LLM_OPTIONAL`；
- deterministic G3-B2/G3-B3 loops 可登记为 offline-capable，但新运行不是历史运行。

### Forbidden changes

- 不改 Prompt 文本以改写历史；
- 不改 Prompt engine/LLM behavior；
- 不新增 algorithm/Skill capability；
- 不更新 Schedule/selector/cost semantics；
- 不修改 G3-B2 registry 或 frozen evidence；
- 不把 stale documentation 直接转成 registry truth。

### Commit boundary

本阶段只允许提交 Prompt/Skill registries、schema、registry-focused tests 和必要的 read-only builder/validator。

建议 commit：

```text
G3-D-B build prompt and skill registries
```

### Exit criteria

- Prompt Registry complete and validated；
- Skill Registry complete and validated；
- all hashes PASS；
- G3-B2 prompt identities preserved；
- historical unavailable cases explicit；
- mandatory path has no online dependency；
- no feature semantics changed；
- focused G3-D-B tests PASS。

---

## 14.11 G3-D-C — Trace Normalization and Offline Replay

### Objective

把已有 G3-B2/G3-B3 frozen Agent records 标准化为统一、可审计的 trace index，并建立 deterministic mandatory offline replay。

### Inputs / Authority

#### Evidence line A：G3-B2 Optimization Agent Trace

必须消费：

```text
agent/evidence/g3_b2/
experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/
```

覆盖 proposal、evaluation、reflection、replanning、final selection、A0-A7 ablation、human intervention 和 commit/evidence mapping。

必须保持 frozen performance：

```text
raw weighted improvement = 45.59283008%
display value            = 45.59%
wins                     = 18
ties                     = 0
losses                   = 0
truth identity           = SIMULATED_ONLY
```

#### Evidence line B：G3-B3 Feature Completion Agent Trace

必须消费：

```text
experiments/feature_completion/evidence/
    g3_b3_f_final_20260807T170000Z/
experiments/feature_completion/evidence/
    g3_b3_d_agent_flow_20260807T150515Z/
```

覆盖 feature proposal、deterministic evaluation、correctness hard gate、reflection、dense/sparse decision、integrity/retry/flow policy decision、B0-B6 ablation 和 final feature decisions。

必须明确：

```text
INT8
→ DEFERRED_BY_PRECISION_GATE

PairWise
→ SKIPPED_BY_VALUE_GATE
```

并引用已实施 feature 的现有 evidence，不得重跑 feature benchmark。

### Implementation scope

建立统一 normalized trace schema，每条 trace 至少包含：

```text
trace_id
schema_version
scenario
source_checkpoint
source_evidence_path
source_evidence_sha256
source_evidence_root_sha256
source_commit
prompt_id
prompt_version
prompt_relationship_status
skills
input
proposal
deterministic_evaluation
reflection
replanning
final_decision
human_intervention_status
human_intervention_refs
output_artifact
source_refs
commit_refs
claim_refs
limitations
provenance_identity
execution_identity
```

字段无法证明时必须使用 `null`、`[]`、`HISTORICAL_TRACE_UNAVAILABLE` 或 `RECONSTRUCTED_FROM_FROZEN_EVIDENCE`，不得填入猜测值。

`replanning` 对不适用或无历史记录的场景必须明确 `NOT_APPLICABLE` 或 `HISTORICAL_TRACE_UNAVAILABLE`，不得为了满足 schema 生成虚假 replan。

#### Offline replay CLI

优先建立最小、独立的 delivery CLI：

```text
python -m tools.agent_delivery_cli describe
python -m tools.agent_delivery_cli verify
python -m tools.agent_delivery_cli replay --trace <trace_id>
```

若 G3-D-A 证明现有 `tools.submission_cli` 已有完全适合的 extension seam，可采用等价 subcommand；不得把 Agent delivery 行为塞入 G3-C `report_cli` 而破坏其 reporting-only contract。

CLI contract：

```text
describe → read-only inventory summary
verify   → read-only schema/hash/pointer/provenance validation
replay   → read frozen normalized inputs and emit canonical decision flow
```

普通 `describe/verify/replay` 不得写 tracked file。G3-D-E final evidence generation 使用独立、明确授权的 freeze command 或 existing staging integration。

### Expected artifacts

```text
docs/submission/agent_delivery/
├── trace_index.json
├── trace_index.md
└── traces/
    ├── g3_b2_optimization_trace.json
    └── g3_b3_feature_completion_trace.json

tools/agent_delivery/
├── __init__.py
├── schemas.py
├── evidence_reader.py
├── trace_normalizer.py
├── replay.py
└── verifier.py

tools/agent_delivery_cli.py
```

实际文件可以按仓库风格合并，但 logical artifacts 和 CLI behavior 不得缺失。

### Tests / Acceptance criteria

至少验证：

1. normalized trace schema 与 unique trace_id；
2. frozen source path、file SHA、root SHA 和 manifest pointer；
3. asserted source commit 可由本地 Git object 解析；
4. 无法证明的 commit relationship 标 unavailable；
5. Prompt id/version 可解析或明确 unavailable；
6. Skill ids 可解析；
7. G3-B2 45.59283008/45.59/18/0/0 与 G3-C ledger 一致；
8. G3-B2 truth=`SIMULATED_ONLY`；
9. G3-B3 20/20/20 inventory 与 frozen evidence 一致；
10. INT8 deferred 与 PairWise skipped gate 一致；
11. replay 不要求 API Key、不发起网络；
12. replay 两次 canonical JSON/hash 完全相同；
13. replay 不修改 frozen evidence 或 tracked worktree；
14. reconstructed replay 不标 historical execution；
15. no hidden chain-of-thought fields；
16. malformed/overclaim/unresolved pointer 被拒绝。

预期 sentinels：

```text
TRACE_INDEX_OK
OFFLINE_REPLAY_OK
```

### Truth boundaries

- G3-D 新执行 replay 不是 historical execution；
- normalized trace 不是 original raw Agent log；
- G3-B2 historical timestamp 只可原样引用，不能补写；
- G3-B3 20/20/20 records 不证明 online LLM participation；
- G3-B2 performance 仍是 `SIMULATED_ONLY`；
- replay result 不构成新性能、硬件或 correctness claim。

### Forbidden changes

- 不重跑 G3-B2 benchmark/A0-A7 或 G3-B3 benchmark/B0-B6；
- 不修改 frozen trace/evidence；
- 不调用 external LLM 或 `HCCLAgent.run()` 作为 mandatory replay；
- 不执行 ACL/HCCL/device API；
- 不修改 selector/cost/Schedule/Agent proposal semantics；
- 不补造 Prompt/Response/CoT/human decision。

### Commit boundary

本阶段只允许提交 normalized trace artifacts、offline replay/verify tooling 和 focused tests。

建议 commit：

```text
G3-D-C normalize and replay frozen Agent traces
```

### Exit criteria

- G3-B2/G3-B3 normalized traces validated；
- trace index complete；
- authority hashes and pointers PASS；
- offline replay succeeds without Key/network；
- replay determinism PASS；
- historical/replay/reconstruction identities distinct；
- no frozen evidence mutation；
- focused G3-D-C tests PASS。

---

## 14.12 G3-D-D — Provenance, Human Intervention and Submission Documentation

### Objective

形成比赛正式 Agent/Prompt 文档，关闭 G3-A 中 provenance、autonomy、Prompt/Skill 和 reproduction 交付缺口。

### Inputs / Authority

必须从以下 authority 派生，不得手工创建第二套事实：

```text
G3-D-A authority/inventory
G3-D-B Prompt/Skill registries
G3-D-C normalized trace/index
G3-C claim ledger
G3-C data ledger
G3-C reports/source index
G3-B2/G3-B3 frozen evidence
G3-A requirement/risk/roadmap records
```

### Implementation scope

每个展示 workflow 必须区分：

```text
Agent-generated proposal
deterministic evaluation
human-supplied goal/constraint
human approval/intervention
offline replay
reconstructed documentation
historical evidence
historical trace unavailable
optional online LLM
```

建立完整可审计链：

```text
Prompt
→ Skill
→ Agent Trace
→ Source
→ Commit
→ Evidence
→ G3-C Claim
```

如果某个 historical relationship 无法证明，必须标记 `HISTORICAL_TRACE_UNAVAILABLE` 或 `RECONSTRUCTED_FROM_FROZEN_EVIDENCE`，不能通过文档叙事补齐关系。

文档中涉及数字时必须使用：

```text
G3-C data ledger
→ G3-D reference
```

不得重新从 benchmark 日志挑选或手工维护数字。

### Expected artifacts

`docs/submission/agent_delivery/` 至少形成：

```text
README.md
01_agent_architecture_and_workflow.md
02_prompt_registry_and_version_reference.md
03_skill_inventory.md
04_trace_and_provenance_index.md
05_offline_replay_guide.md
06_human_intervention_and_autonomy_disclosure.md
07_limitations_and_online_llm_boundary.md
08_source_commit_evidence_claim_mapping.md
source_commit_evidence_claim_mapping.json
human_intervention_disclosure.json
```

### Tests / Acceptance criteria

至少验证：

1. required documents 全部存在；
2. docs 与 registries/trace index 一致；
3. Prompt/Skill/Trace link 可解析；
4. source/commit/evidence/claim mapping 可解析；
5. G3-C claim refs 存在；
6. 数值只引用 G3-C ledger；
7. human intervention fields 完整；
8. historical unavailable cases 显式；
9. reconstructed docs 不标 original log；
10. mandatory replay 文档不要求 API Key；
11. online LLM 始终 optional；
12. 禁止 `fully autonomous` 等 unsupported claim；
13. no hidden chain-of-thought；
14. no secrets；
15. no local absolute paths；
16. relative links PASS；
17. stale `docs/agent_capabilities.md` / `docs/agent_development_demo.md` 不作为 current authority；是否 supersede 由本阶段显式说明，不删除历史文件。

预期 sentinels：

```text
PROVENANCE_OK
CLAIM_BOUNDARIES_OK
```

### Truth boundaries

- 正式描述优先使用 `Agent-assisted`、`deterministically evaluated`、`human-governed`、`offline replayable`；
- 只有 frozen evidence 明确支持时才使用 `AGENT_GENERATED`；
- 无原始 historical trace 时不能声称 G3-D 恢复了 original prompt/response；
- human authorization 不等于 human algorithm choice；
- no scenario-level human intervention 只能按 G3-B2 frozen record 原样解释；
- 当前 code generation demo 是 `OFFLINE_TEMPLATE` 临时目录演示，不得描述成核心 C/C++ 生产代码 provenance。

### Forbidden changes

- 不修改 G3-C claim/data ledger；
- 不复制 G3-C 大量数字；
- 不改 Agent feature source；
- 不新增 Prompt、Skill 或 algorithm behavior；
- 不修改 historical docs 以伪装历史；
- 不披露 secrets/private logs；
- 不输出 hidden chain-of-thought。

### Commit boundary

本阶段只允许提交 Agent/Prompt formal documentation、provenance/human disclosure、mapping artifact 和 documentation-focused verifier/tests。

建议 commit：

```text
G3-D-D document Agent provenance and autonomy boundaries
```

### Exit criteria

- formal Agent/Prompt documentation complete；
- provenance chain auditable；
- human/Agent/deterministic roles disclosed；
- historical unavailable cases explicit；
- G3-C claim wording preserved；
- offline/online boundary documented；
- no overclaim/secrets/local paths；
- focused G3-D-D tests PASS。

---

## 14.13 G3-D-E — Final Validation, Staging and Evidence Freeze

### Objective

完成 G3-D 软件交付验收、existing submission staging integration、唯一 authority evidence freeze 和最终 stop。

### Inputs / Authority

消费：

```text
G3-D-A contract/inventory
G3-D-B registries
G3-D-C normalized traces/replay
G3-D-D formal docs/mappings
existing tools.submission_cli staging framework
scripts/validate_linux_cpu_sim.sh
G3-C ledgers and final evidence
G3-B2/G3-B3 authority evidence
```

不得创建新的平行 staging framework。

### Implementation scope

1. 完成 focused G3-D verifier；
2. 把 Agent/Prompt delivery logical artifacts 纳入 existing submission staging；
3. 校验 staging coverage、exclude policy、relative paths 和 size；
4. 执行完整 regression；
5. 生成唯一 G3-D final authority evidence；
6. 生成 `SHA256SUMS` 并校验 digest；
7. 记录 final Git state、source commit 和 Feature Freeze state；
8. 最终停止，不进入 G3-E。

### Expected artifacts

唯一最终 authority evidence 建议放在：

```text
experiments/submission/evidence/
    g3_d_<timestamp>/
```

至少包含：

```text
README.md
manifest.json
result.json
authority_inventory_validation.json
delivery_contract_validation.json
prompt_registry_validation.json
skill_registry_validation.json
trace_index_validation.json
g3_b2_trace_validation.json
g3_b3_trace_validation.json
offline_replay_validation.json
replay_determinism.json
provenance_validation.json
human_intervention_validation.json
historical_unavailable_validation.json
claim_boundary_validation.json
source_commit_mapping_validation.json
staging_verification.json
regression_summary.json
no_secrets_audit.json
path_portability_audit.json
git_state.json
user_action_required.json
SHA256SUMS
```

不得复制整个 G3-B2/G3-B3/G3-C evidence tree。只通过 relative pointer、source SHA256 和 authority root `SHA256SUMS` digest 引用。

### Tests / Acceptance criteria

focused tests 至少验证：

```text
prompt registry schema
prompt hashes
skill registry schema
skill mappings/hashes
trace schema
trace evidence hashes
evidence pointers
commit validity where asserted
provenance vocabulary
offline replay without API keys
offline replay without network
replay determinism
no frozen-evidence mutation
human-intervention fields
historical-unavailable handling
G3-C claim reference resolution
forbidden overclaim rejection
no local absolute paths
no secrets
submission staging coverage
```

Mandatory validation 至少输出：

```text
G3_D_AUTHORITY_INVENTORY_OK
PROMPT_REGISTRY_OK
SKILL_REGISTRY_OK
TRACE_INDEX_OK
OFFLINE_REPLAY_OK
PROVENANCE_OK
CLAIM_BOUNDARIES_OK
NO_SECRETS_OK
G3_D_AGENT_PROMPT_DELIVERY_OK
```

名称可按现有 CLI convention 最小调整，但必须有唯一最终成功 sentinel：

```text
G3_D_AGENT_PROMPT_DELIVERY_OK
```

运行 focused G3-D tests 后，必须完整执行：

```bash
bash scripts/validate_linux_cpu_sim.sh /tmp/hccl-agent-linux-review
```

必须继续满足：

```text
CMake configure PASS
build PASS
CTest PASS
focused CPU_SIM unittest PASS
full pytest PASS
existing skip count no abnormal increase
LINUX_CPU_SIM_VALIDATION_OK
```

并执行：

```text
git diff --check
```

final evidence freeze 前后必须比较：

```text
G3-B2 authority hash unchanged
G3-B3 authority hash unchanged
G3-C factual ledger hash unchanged
Final Feature Freeze source contracts unchanged
```

### Truth boundaries

- G3-D evidence 证明 delivery、traceability 和 offline replay，不证明新 algorithm 或真实 hardware；
- full regression 不得表述成 real-device execution；
- G3-D final timestamp 只表示本次 evidence freeze，不表示 historical Agent execution 时间；
- staging copy 不改变 source/evidence authority；
- final evidence 中 `runtime_api_calls=[]`。

### Forbidden changes

- 不降低测试或增加无理由 skip；
- 不修改 frozen feature semantics；
- 不修改 G3-B2/G3-B3/G3-C evidence/ledgers；
- 不重跑大型 benchmark；
- 不调用 online LLM 或任何真实设备 API；
- 不创建新 staging framework；
- 不复制完整旧 evidence tree；
- 不创建 release/archive/tag。

### Commit boundary

本阶段只允许提交 final validation、existing staging integration、G3-D final evidence 和必要 focused tests。

建议 commit：

```text
G3-D-E finalize Agent prompt delivery evidence
```

完成本 commit 后立即 `STOP`。

### Exit criteria

- all G3-D focused tests PASS；
- Prompt/Skill/Trace/Provenance/Claim sentinels PASS；
- offline replay deterministic and keyless；
- full pytest PASS；
- CTest PASS；
- Linux CPU_SIM validation PASS；
- staging PASS；
- no secrets/local absolute paths；
- old evidence/ledgers unchanged；
- unique final evidence frozen；
- SHA256SUMS validated；
- Feature Freeze preserved；
- real-device state unchanged；
- worktree clean after commit；
- no push/merge/G3-E。

---

## 14.14 Normalized trace 与 mapping contract

为避免 G3-D-C/G3-D-D 维护不一致数据，必须建立单一 machine-readable mapping source：

```text
prompt_id
  └── skill_ids[]
        └── trace_ids[]
              ├── source_paths[]
              ├── commit_refs[]
              ├── evidence_refs[]
              └── claim_refs[]
```

每条关系至少包含：

```text
relationship_id
from_type
from_id
to_type
to_id
authority_level
source_pointer
source_sha256
provenance
confidence
limitations
```

若 `claim_refs=[]`，必须说明没有适用 G3-C external claim，而不是发明 Agent claim。

若 commit 只能由 frozen mapping 中的 abbreviated SHA 或 unresolved placeholder 表示，必须设置：

```text
commit_validity=UNRESOLVED
provenance=HISTORICAL_TRACE_UNAVAILABLE
```

不得擅自匹配相似 commit message。

---

## 14.15 G3-D Test Requirements

至少覆盖以下类别。

### Authority / inventory

1. authority schema；
2. L1–L5 level validation；
3. G3-B2 root digest；
4. G3-B3 root digest；
5. G3-C ledger readability；
6. source path existence；
7. current/frozen/unavailable status validation；
8. ignored logs excluded；
9. roadmap-only rejection；
10. deterministic ordering。

### Prompt Registry

11. prompt schema；
12. unique prompt_id；
13. current version rule；
14. historical unavailable rule；
15. prompt source SHA；
16. input contract；
17. output contract；
18. online/offline classification；
19. G3-B2 registry parity；
20. aspirational wording limitation。

### Skill Registry

21. skill schema；
22. unique skill_id；
23. source SHA；
24. inputs/outputs；
25. deterministic/online classification；
26. Agent stage mapping；
27. prompt dependency；
28. test mapping；
29. frozen evidence mapping；
30. untested/partial status handling。

### Trace / replay

31. trace schema；
32. unique trace_id；
33. evidence pointer；
34. evidence SHA；
35. source commit validity；
36. unavailable commit handling；
37. G3-B2 proposal/evaluation/reflection/replan；
38. G3-B2 human intervention；
39. G3-B2 45.59283008/45.59；
40. G3-B2 18/0/0；
41. G3-B2 `SIMULATED_ONLY`；
42. G3-B3 20/20/20；
43. G3-B3 deterministic hard gate；
44. INT8 deferred；
45. PairWise skipped；
46. missing historical Prompt handling；
47. no fabricated replanning；
48. replay canonical output；
49. replay repeat hash equality；
50. no network；
51. no API key；
52. no tracked writes；
53. no old evidence mutation。

### Provenance / docs / claims

54. vocabulary allowlist；
55. Agent/human/deterministic distinction；
56. historical/replay/reconstruction distinction；
57. no hidden chain-of-thought；
58. G3-C claim resolution；
59. 45.59 real-speedup rejection；
60. Direct runtime overclaim rejection；
61. sparse physical-wire overclaim rejection；
62. CRC/NIC overclaim rejection；
63. retry/HCCL overclaim rejection；
64. backpressure/NIC overclaim rejection；
65. `fully autonomous` rejection without evidence；
66. required docs/headings；
67. relative links；
68. no absolute paths；
69. no secrets；
70. source/commit/evidence/claim mapping completeness。

### Staging / regression

71. staging inventory；
72. Prompt/Skill/trace/docs included；
73. frozen evidence referenced not copied wholesale；
74. private logs excluded；
75. controlled material excluded；
76. official SDK/source/DSO excluded；
77. focused G3-D tests；
78. full pytest；
79. CTest；
80. Linux CPU_SIM validation；
81. existing skip count guard；
82. G3-B2/G3-B3/G3-C hash immutability；
83. final evidence SHA；
84. git diff check；
85. clean final worktree。

实际测试数量可以更多，但以上语义必须覆盖，且不得新增无理由 skip。

---

## 14.16 USER_ACTION_REQUIRED

G3-D 继承并保持 unresolved：

```text
UA-B-001 project license/copyright
UA-B-002 official artifact redistribution
UA-B-003 controlled competition material
UA-B-004 submission archive/size rules
UA-C-001 FP32/FP16/BF16 precision interpretation for <=1e-6
UA-C-002 final report language
UA-C-003 final submission template/page/cover/font/anonymity/PDF rules
```

### UA-D-001：Historical Prompt / Agent Run Availability

确认是否存在可合法提交的 original historical Prompt、Response、Agent run log、generation log 或更完整 human-intervention record，以及是否授权公开使用。

在用户未提供并授权前，必须保留：

```text
HISTORICAL_TRACE_UNAVAILABLE
```

该 user action 不阻塞以 frozen evidence 完成 mandatory offline replay，但会限制历史“核心代码由 Agent 全流程生成”的 claim。

### UA-D-002：Final Agent/Prompt Disclosure Detail

确认最终平台是否要求：

```text
raw prompt/response
model/provider/version
token usage
human intervention disclosure format
generated-code provenance form
```

在未知时采用最小、脱敏、evidence-backed disclosure，不猜测平台要求。

### UA-D-003：Real-device Acceptance

继续保留真实硬件验收需求，状态必须是：

```text
HARDWARE_BLOCKED
```

G3-D 不得自行关闭任何 USER_ACTION_REQUIRED。

---

## 14.17 Failure 与状态分类

### FAIL

用于：

```text
registry schema/hash failure
trace schema/hash failure
evidence pointer mismatch
false commit mapping
replay nondeterminism
mandatory online/API-key dependency
network access in mandatory replay
frozen evidence mutation
G3-C ledger mutation
provenance vocabulary violation
historical execution fabrication
hidden chain-of-thought exposure
forbidden overclaim
secret/private path leakage
staging coverage failure
full regression failure
Feature Freeze violation
```

### PARTIAL

只用于非 mandatory relationship 或 disclosure 的有限缺失，例如 optional historical Prompt relationship unavailable、optional online LLM metadata incomplete 或 non-critical Skill lacks dedicated historical evidence。

不得用 PARTIAL 绕过 mandatory registry、offline replay、provenance、claim 或 staging gate。

### ENV_BLOCKED

只用于：

```text
repository/evidence unreadable
Python/CMake/toolchain unavailable
filesystem corruption
Git object database unavailable for asserted commit validation
```

### USER_ACTION_REQUIRED

用于 14.16 中需要外部规则或用户材料/授权的事项。

### HARDWARE_BLOCKED

只用于：

```text
real NPU
ACL/HCCL runtime
communicator
real collective
real topology/network
msprof
real training
real failover
real long-running stress
```

不得用 HARDWARE_BLOCKED 掩盖 registry、trace、replay、documentation 或 testing bug。

---

## 14.18 Branch 与 commit strategy

建议单一分支：

```text
codex/g3-d-agent-prompt-delivery
```

建议五个阶段性 commit：

```text
G3-D-A freeze Agent prompt delivery contract

G3-D-B build prompt and skill registries

G3-D-C normalize and replay frozen Agent traces

G3-D-D document Agent provenance and autonomy boundaries

G3-D-E finalize Agent prompt delivery evidence
```

实际文案允许根据实现做最小调整，但必须保持 A→E 顺序和阶段边界。

G3-D 执行时不得：

```text
push
merge
rebase
amend published history
reset --hard
git clean -fd
create tag
create release
create submission archive
```

最终停在本地 commits，等待用户检查。

---

## 14.19 G3-D Exit Criteria

只有以下全部满足，才允许标记：

```text
G3-D Agent/Prompt Delivery: COMPLETED
```

必须：

- authority/inventory complete；
- delivery contract validated；
- Prompt Registry validated；
- Skill Registry validated；
- Prompt/Skill source hashes PASS；
- normalized G3-B2 trace validated；
- normalized G3-B3 trace validated；
- G3-B2 performance identity保持 `SIMULATED_ONLY`；
- 45.59283008 raw / 45.59 display / 18-0-0 与 G3-C ledger 一致；
- INT8=`DEFERRED_BY_PRECISION_GATE`；
- PairWise=`SKIPPED_BY_VALUE_GATE`；
- offline replay deterministic；
- no mandatory external API dependency；
- no mandatory network dependency；
- human/Agent/deterministic provenance disclosed；
- historical unavailable cases explicitly marked；
- replay/reconstruction 与 historical execution 明确区分；
- no hidden chain-of-thought；
- source/commit/evidence/claim mapping validated；
- G3-C claim boundaries preserved；
- G3-C factual ledgers unchanged；
- G3-B2/G3-B3 frozen evidence unchanged；
- focused G3-D tests PASS；
- full pytest PASS；
- CTest PASS；
- Linux CPU_SIM validation PASS；
- existing skip count无异常增加；
- staging PASS；
- no secrets；
- no local absolute paths；
- G3-D unique final evidence frozen；
- `SHA256SUMS` PASS；
- `G3_D_AGENT_PROMPT_DELIVERY_OK` emitted；
- Final Feature Freeze preserved；
- CPU_SIM public ABI/SONAME/19 symbols unchanged；
- real-device status unchanged；
- `runtime_api_calls=[]`；
- worktree clean after final commit；
- 未 push、未 merge、未开始 G3-E。

最终 `result.json` 至少记录：

```text
checkpoint=G3-D
checkpoint_status=COMPLETED

authority_inventory=COMPLETED
prompt_registry=COMPLETED
skill_registry=COMPLETED
normalized_traces=COMPLETED
offline_replay=COMPLETED
provenance_disclosure=COMPLETED
human_intervention_disclosure=COMPLETED
submission_staging=COMPLETED

mandatory_external_api_dependency=false
mandatory_network_dependency=false
online_llm=OPTIONAL
historical_unavailable_cases_disclosed=true
hidden_chain_of_thought_included=false

final_feature_freeze_preserved=true
old_evidence_modified=false
g3_c_factual_ledgers_modified=false
public_abi_changed=false
soname_changed=false
export_allowlist_changed=false

real_device_acceptance=HARDWARE_BLOCKED
real_device_api_executed=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
measured_on_real_npu=false
msprof_executed=false
runtime_api_calls=[]
```

---

## 14.20 G3-E boundary

只有 G3-D 满足 14.19 全部 exit criteria 并由用户确认后，才允许进入 G3-E。

G3-E 将消费：

```text
G3-C report_data_ledger.json
G3-C report_chart_data/
G3-C report_claim_ledger.json
+
G3-D Agent provenance
G3-D normalized trace
G3-D innovation evidence mapping
```

进行：

```text
charts
innovation narrative
```

G3-E 不得重新运行 benchmark，不得重新解释 G3-B2/G3-B3 Agent history，也不得改变 G3-C/G3-D claim boundary。

G3-D-E 完成后必须：

```text
STOP
```

不得自动开始 G3-E implementation。
