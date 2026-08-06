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
