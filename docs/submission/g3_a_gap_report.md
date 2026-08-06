# G3-A Competition Delivery Gap Report

## Executive summary

G3-A is complete as an audit. G3 delivery readiness remains PARTIAL and real-device acceptance remains HARDWARE_BLOCKED. Current strength is frozen simulator correctness/performance/scale/reliability evidence; the decisive gaps are the final C/C++ plugin identity, Agent generation provenance, submission packaging, formal reports, demo, and release compliance.

- Requirements: 86
- Deliverables: 33
- Claims: 14
- Risks: 59
- Status counts: `{"HARDWARE_BLOCKED": 4, "MISSING": 14, "NOT_APPLICABLE": 2, "PARTIALLY_SATISFIED": 36, "SATISFIED": 27, "UNVERIFIED": 3}`
- Risk counts: `{"BLOCKER": 15, "HIGH": 36, "INFO": 2, "MEDIUM": 6}`

## Satisfied requirements

| Requirement | Summary | Evidence |
| --- | --- | --- |
| REQ-PRIM-001 | 实现 AllReduce 核心集通信原语 | E5_SIMULATOR_VALIDATED |
| REQ-PRIM-002 | 实现 AllGather 核心集通信原语 | E5_SIMULATOR_VALIDATED |
| REQ-PRIM-003 | 实现 ReduceScatter 核心集通信原语 | E5_SIMULATOR_VALIDATED |
| REQ-TOPO-001 | 覆盖 Full Mesh、Ring 与分层 Fat-Tree 拓扑模型 | E5_SIMULATOR_VALIDATED |
| REQ-TOPO-003 | 建模 HCCS、RoCE、PCIe 带宽、延迟与误码率 | E5_SIMULATOR_VALIDATED |
| REQ-TOPO-004 | 覆盖小消息与逻辑 1 GB 大消息 | E5_SIMULATOR_VALIDATED |
| REQ-INNOV-002 | 依据消息、拓扑与链路自适应选择算法 | E3_HOST_EXECUTED |
| REQ-INNOV-005 | 支持反思、重规划与迭代优化 | E3_HOST_EXECUTED |
| REQ-CO-005 | 不得修改官方驱动、固件、HCOMM、HCCL 或 CANN | E2_STATIC_VERIFIED |
| REQ-REL-001 | 支持链路健康监测和退化检测 | E5_SIMULATOR_VALIDATED |
| REQ-REL-002 | 覆盖 link down、degradation、timeout 与 retry | E5_SIMULATOR_VALIDATED |
| REQ-REL-004 | 模拟 100 ms 内切换备用路径并处理无路可用 | E5_SIMULATOR_VALIDATED |
| REQ-REL-005 | 模拟重传率不高于 0.1% | E5_SIMULATOR_VALIDATED |
| REQ-REL-006 | 提供 logical 72h 可靠性证据 | E5_SIMULATOR_VALIDATED |
| REQ-SCALE-001 | 覆盖 8/16/32/64/128/256/512/1024 ranks | E5_SIMULATOR_VALIDATED |
| REQ-CORR-001 | 覆盖 FP16、BF16、FP32，并审计 INT32 | E5_SIMULATOR_VALIDATED |
| REQ-CORR-002 | 覆盖 SUM、MAX、MIN 归约操作 | E3_HOST_EXECUTED |
| REQ-CORR-003 | 使用独立 host reference、exact 数据和随机 stress 数据 | E5_SIMULATOR_VALIDATED |
| REQ-CORR-004 | 审计绝对/相对误差、NaN/Inf、hash 与 rank ordering | E5_SIMULATOR_VALIDATED |
| REQ-CORR-006 | CPU_SIM 与 simulator 交叉验证 | E3_HOST_EXECUTED |
| REQ-CPP-003 | 提供匹配头文件和 CMake 构建入口 | E2_STATIC_VERIFIED |
| REQ-AGENT-003 | 覆盖 planning、topology、generation、selection、execution、evaluation、reflection、replanning、reliability、reporting | E3_HOST_EXECUTED |
| REQ-SIM-002 | 提供拓扑/硬件参数配置及来源 | E5_SIMULATOR_VALIDATED |
| REQ-SIM-003 | 提供三原语正确性、logical 1 GB 和 CPU_SIM 交叉验证 | E5_SIMULATOR_VALIDATED |
| REQ-SIM-004 | 提供性能、规模、algorithm comparison、profiling 与 workload trace | E5_SIMULATOR_VALIDATED |
| REQ-SIM-005 | 提供 fault injection、100 ms、retry 与 logical 72h | E5_SIMULATOR_VALIDATED |
| REQ-TEST-001 | 提供 CTest 与 Python 测试体系 | E3_HOST_EXECUTED |

## Blockers

| Risk | Requirement | Gap | Action | Owner |
| --- | --- | --- | --- | --- |
| RISK-INNOV-006 | REQ-INNOV-006 | 示例无生成时间、原始调用、Prompt 版本、commit 或人工干预映射；HISTORICAL_RECORD_UNAVAILABLE | G3-D 建立可复现的新 trace；用户提供可合法使用的历史原始记录 | G3-D |
| RISK-CO-001 | REQ-CO-001 | CPU_SIM 使用项目本地 hccl* ABI；direct 层只做官方 Hccl* ABI 静态检查，未形成最终插件接口 | G3-B 确定官方插件 ABI、兼容包装层和提交入口 | G3-B |
| RISK-CPP-001 | REQ-CPP-001 | CPU_SIM 核心为 C；direct C++ 仅 readiness 模型，未承担官方 collective 算法插件角色 | G3-B 冻结最终插件 ABI 与构建产物 | G3-B |
| RISK-CPP-002 | REQ-CPP-002 | 可构建的 libhccl_plugin.so 是 CPU_SIM；direct 产物为静态 libhccl_direct_adapter.a，不是最终官方插件 .so | G3-B 定义并验证最终 .so、导出 ABI 和无设备构建说明 | G3-B |
| RISK-CPP-005 | REQ-CPP-005 | CPU_SIM 仅 libc；direct link audit 依赖 CANN DSOs，其再分发权未确认且 artifact 不是提交插件 | G3-B 默认排除官方 DSO；用户完成 redistribution review | G3-B |
| RISK-CPP-006 | REQ-CPP-006 | 两套 ABI 已隔离但缺最终评委兼容说明/包装层 | G3-B 增加兼容说明与唯一插件入口 | G3-B |
| RISK-AGENT-005 | REQ-AGENT-005 | logs/ 下本机记录被 .gitignore 排除；仓库没有可提交的权威 Agent run/prompt log | G3-D 生成新的脱敏权威 trace；用户提供/确认历史记录使用边界 | G3-D |
| RISK-AGENT-006 | REQ-AGENT-006 | 示例无来源元数据；历史原始 Prompt/Agent 记录不可由当前仓库恢复 | G3-D 只创建未来可验证 trace，不伪造历史；用户披露可用历史材料与人工工作 | G3-D |
| RISK-AGENT-007 | REQ-AGENT-007 | 现有 autonomous loop 是 host 工具演示，未与最终 C/C++ 插件生成和 commit trace 闭环 | G3-D 建立受控、可重放、脱敏的完整流程 | G3-D |
| RISK-PACKAGE-001 | REQ-PACKAGE-001 | 源码/headers/CMake 存在，但最终合规 .so 与 submission manifest 不存在 | G3-B 构建 staging package 和 manifest，不在 G3-A 打包 | G3-B |
| RISK-PACKAGE-002 | REQ-PACKAGE-002 | 源码/Prompt 在仓库；权威 logs 与 generation trace 缺失 | G3-D 产出后由 G3-B/G3-G 纳入包 | G3-D |
| RISK-PACKAGE-004 | REQ-PACKAGE-004 | 旧 evidence 有 SHA256；最终提交级 manifest、license 和排除审计未生成 | G3-B 建 manifest；G3-G 执行 release audit；用户确认许可证 | G3-B |
| RISK-COMP-001 | REQ-COMP-001 | 仓库根目录无 LICENSE/NOTICE | 用户选择许可证并确认版权；G3-G 纳入 release | USER_ACTION |
| RISK-COMP-003 | REQ-COMP-003 | 仓库未复制官方源码/DSO，但 CANN/HCOMM/HCCL redistribution 权利尚未人工确认 | 保持默认排除；用户完成 REDISTRIBUTION_REVIEW_REQUIRED | USER_ACTION |
| RISK-COMP-004 | REQ-COMP-004 | 当前受控仓库包含正式 DOCX；最终提交和公开 release 是否可包含需用户确认 | G3-B/G3-G 默认排除；用户完成 CONFIDENTIALITY_REVIEW_REQUIRED | USER_ACTION |

## High risks

| Risk | Requirement | Gap | Action | Owner |
| --- | --- | --- | --- | --- |
| RISK-TOPO-002 | REQ-TOPO-002 | 仅为 SIMULATOR_CONFIGURED；未自动探测 910A2/910A3 或真实非对称链路 | 形成可注入拓扑接口和静态兼容说明；实机探测留待设备阶段 | G3-B |
| RISK-TOPO-005 | REQ-TOPO-005 | host/simulator 事件链可执行，但无真实节点热插拔与不中断训练证明 | 在技术报告中给出状态机与限制；实机留待未来 | G3-C |
| RISK-TOPO-006 | REQ-TOPO-006 | 配置存在，但没有真实探测；HBM/UB 未进入官方插件数据路径 | G3-C 明确静态配置边界，G3-B 补交付说明 | G3-C |
| RISK-INNOV-001 | REQ-INNOV-001 | 多数 C 算法入口复用 host reference kernel；名称不等同完整通信调度或官方插件算法 | G3-E 仅展示已实现差异；G3-C 逐算法说明实现深度 | G3-E |
| RISK-INNOV-003 | REQ-INNOV-003 | 路由切换仅为模拟模型，未进入 C/C++ collective 数据路径 | G3-C 报告模型；REAL_DEVICE_FUTURE 验收 | G3-C |
| RISK-CO-002 | REQ-CO-002 | HOST_HARNESS_VERIFIED；没有 ACL/HCCL runtime 执行 | G3-C 写入 direct readiness appendix；设备阶段验收 | G3-C |
| RISK-CO-003 | REQ-CO-003 | 只有容量模型；未分配设备 buffer 或提交 collective | 保留 readiness 边界，设备阶段执行 | REAL_DEVICE_FUTURE |
| RISK-CO-004 | REQ-CO-004 | 仅在 Prompt 和设计文字出现；无 C/C++ 实现、静态证据或 host harness | G3-C/G3-E 明确未实现；真实实现需独立后续 checkpoint | G3-C |
| RISK-REL-003 | REQ-REL-003 | 仅 host/simulator CRC 模型，未进入 C/C++ collective 或真实传输 | G3-C 说明模拟范围；设备实现需后续 checkpoint | G3-C |
| RISK-SCALE-002 | REQ-SCALE-002 | Fat-Tree 模型为 O(log N)，但 C 算法实现未提供相同的真实调度复杂度证据 | G3-C 形成逐算法复杂度与实现映射 | G3-C |
| RISK-SCALE-003 | REQ-SCALE-003 | 只有通信模型扩展趋势，没有 compute workload、训练吞吐或线性加速比计算 | G3-C/G3-E 明确未验证；不得从通信 latency 推导训练加速比 | G3-C |
| RISK-CORR-005 | REQ-CORR-005 | exact 数据满足零误差和 1e-6；FP16/BF16 stress 使用 1e-3/1e-2，不可替代统一 1e-6 结论 | G3-C 明确数据集与容差；用户/赛事规则确认阈值解释 | G3-C |
| RISK-CPP-004 | REQ-CPP-004 | 历史 evidence 只列 direct static archive 的 4 个符号；G3-A 需静态查询当前 CPU_SIM .so，且该 ABI 仍非官方 direct plugin | G3-B 输出正式 ABI 清单并校验 | G3-B |
| RISK-AGENT-001 | REQ-AGENT-001 | 入口存在，但无冻结依赖清单、clean-environment 安装与一键复现验证 | G3-B 提供环境锁定和 quick/full reproduce | G3-B |
| RISK-AGENT-002 | REQ-AGENT-002 | 能力文档含已过时的 C 层范围描述，未形成提交 manifest | G3-D 重建版本化 Skills 清单 | G3-D |
| RISK-AGENT-004 | REQ-AGENT-004 | Prompt 文件有 5 类模板但无显式版本/schema；本地调用日志被 gitignore 排除 | G3-D 增加版本、schema、最小可公开调用样例 | G3-D |
| RISK-SIM-001 | REQ-SIM-001 | 验收 runner 存在，但 G2-F-5 需要预构建 CPU_SIM .so；没有统一提交级入口 | G3-B 提供无隐藏状态的 simulator quick/full reproduce | G3-B |
| RISK-SIM-006 | REQ-SIM-006 | evidence 完整且有 SHA256，但 simulator guide 描述旧简化模型，缺统一复现/打包入口 | G3-B 建复现入口；G3-C 更新 simulator manual | G3-B |
| RISK-TEST-002 | REQ-TEST-002 | 仅 simulator 8/64/1024 ranks；没有真实 8/64 设备脚本验收 | G3-B 将模拟场景打包并标注；真实设备留待未来 | G3-B |
| RISK-TEST-003 | REQ-TEST-003 | 工具分散，缺 submission-level 统一 CLI 和 clean-environment 运行证明 | G3-B 提供统一入口与 quick/full 模式 | G3-B |
| RISK-TEST-004 | REQ-TEST-004 | 已有 focused contracts；缺最终提交包 clean extraction/build/run 验证 | G3-B/G3-G 分别验证构建和 release candidate | G3-B |
| RISK-DOC-001 | REQ-DOC-001 | README 有当前三后端边界，但无冻结依赖/clean start，且若干历史命令未作为提交入口验证 | G3-B 更新复现说明并验证 | G3-B |
| RISK-DOC-002 | REQ-DOC-002 | competition_analysis 等包含已过时的空 Prompt/主流程故障描述；缺 G3 正式算法报告 | G3-C 以当前审计为基线重建正式报告 | G3-C |
| RISK-DOC-003 | REQ-DOC-003 | 正确性矩阵和可靠性报告存在；缺基于 G2-F-6 的正式性能/规模/算法对比报告 | G3-C 生成正式 simulator reports | G3-C |
| RISK-DOC-004 | REQ-DOC-004 | direct 文档较完整；simulator guide 仍是旧概念模型，未覆盖 G2-F-5/F6 evidence workflow | G3-C 更新正式 simulator manual | G3-C |
| RISK-DOC-005 | REQ-DOC-005 | 架构/能力文档存在；缺版本化 Prompt 工程、真实生成 trace、人工干预披露和独立复现手册 | G3-D 完成专项交付 | G3-D |
| RISK-PACKAGE-003 | REQ-PACKAGE-003 | 资产分散且 docs/guide stale；未建立 submission inclusion/exclusion manifest | G3-B 生成 staging manifest 与复现入口 | G3-B |
| RISK-PACKAGE-005 | REQ-PACKAGE-005 | G3-A 不生成 archive；平台格式、大小和 clean extraction 尚未验证 | G3-B 验证 staging；G3-G 验证 release candidate；用户确认平台约束 | G3-G |
| RISK-REPORT-001 | REQ-REPORT-001 | 机器 evidence 完整，但正式评委报告未形成 | G3-C 生成 SIMULATOR PERFORMANCE REPORT；G3-E 生成图表 | G3-C |
| RISK-REPORT-002 | REQ-REPORT-002 | 现有报告来自早期固定 seed 场景，未汇总 G2-F-6 12 场景与 logical 72h | G3-C 更新正式 reliability report | G3-C |
| RISK-REPORT-003 | REQ-REPORT-003 | 只有 BERT/LLaMA communication trace；real_model_executed=false、msprof_executed=false、无 throughput | G3-C/E 使用受限措辞；实机指标留待未来 | G3-C |
| RISK-DEMO-001 | REQ-DEMO-001 | 仓库没有视频文件 | G3-F 制作视频，不得标记 HARDWARE_BLOCKED | G3-F |
| RISK-DEMO-003 | REQ-DEMO-003 | 未建立最终演示内容和 claim boundary slide | G3-F 使用 G3-A claim matrix 制作；G3-G 复核 | G3-F |
| RISK-COMP-002 | REQ-COMP-002 | 无冻结 dependency/license inventory；生成示例 provenance 缺失 | G3-G 建 SBOM/依赖清单；G3-D 补生成 provenance | G3-G |
| RISK-COMP-005 | REQ-COMP-005 | 未发现提交凭据证据，但文档含本机绝对路径，ignored logs 未经隐私审计 | G3-G 执行 secrets/privacy scan；仅纳入脱敏日志 | G3-G |
| RISK-COMP-006 | REQ-COMP-006 | 仓库无法确定团队/平台字段、公开策略和历史人工干预 | 用户提供团队/平台/公开策略与人工干预披露 | USER_ACTION |

## Medium/low/informational gaps

| Risk | Level | Requirement | Gap | Owner |
| --- | --- | --- | --- | --- |
| RISK-PRIM-004 | INFO | REQ-PRIM-004 | NOT_SELECTED_OPTIONAL_PRIMITIVE；当前 wrapper 返回 NOT_SUPPORTED | NO_ACTION |
| RISK-PRIM-005 | INFO | REQ-PRIM-005 | NOT_SELECTED_OPTIONAL_PRIMITIVE | NO_ACTION |
| RISK-TOPO-007 | MEDIUM | REQ-TOPO-007 | 只有官方 ABI 静态检查和生命周期模型；未调用 hcclGetTopology 或检测真实设备 | REAL_DEVICE_FUTURE |
| RISK-INNOV-004 | MEDIUM | REQ-INNOV-004 | 只有 Prompt/赛题方向描述，没有稀疏或压缩实现、测试或 evidence | G3-E |
| RISK-CO-006 | MEDIUM | REQ-CO-006 | guard 在 runtime 前停止；direct_hccl_api_call=false | REAL_DEVICE_FUTURE |
| RISK-REL-007 | MEDIUM | REQ-REL-007 | 无真实 NPU、链路故障或 72h 压测 | REAL_DEVICE_FUTURE |
| RISK-SCALE-004 | MEDIUM | REQ-SCALE-004 | 仅模拟 8/64/1024 ranks | REAL_DEVICE_FUTURE |
| RISK-DEMO-002 | MEDIUM | REQ-DEMO-002 | 只有开发工具演示文档；无比赛 demo script/配置/storyboard/字幕 | G3-F |

## C/C++ plugin compliance findings

Status: `PARTIALLY_SATISFIED`.

libhccl_plugin.so is the reproducible current shared object, but it is CPU_SIM and not an official direct HCCL plugin. libhccl_direct_adapter.a is STATIC_COMPILE_ONLY; hccl_direct_link_audit is an ELF inspection executable and must not be distributed as the plugin.

## Agent/Prompt trace findings

Status: `PARTIALLY_SATISFIED`. Historical core-code generation records are `HISTORICAL_RECORD_UNAVAILABLE`; current ignored logs are not authority and are not copied into this audit.

## Simulator deliverability findings

Status: `PARTIALLY_SATISFIED`. Frozen G2-F-5/G2-F-6 evidence is complete and deterministic, but the submission-level runner/manual/package are not complete.

## Performance claim findings

- SIMULATOR_EVIDENCE_COMPLETENESS: `SATISFIED`
- PERFORMANCE_TARGET_ACHIEVEMENT: `PARTIALLY_SATISFIED`
- REAL_DEVICE_PERFORMANCE: `HARDWARE_BLOCKED`

## Confidentiality and license findings

The competition DOCX and official CANN/HCOMM/HCCL assets are excluded from public release by default. LICENSE_REVIEW_REQUIRED, REDISTRIBUTION_REVIEW_REQUIRED, and CONFIDENTIALITY_REVIEW_REQUIRED remain user actions.

## Recommended G3-B to G3-G order

1. G3-B: final plugin identity, reproducible build/test, simulator entry, staging manifest.
2. G3-C: evidence-derived technical reports and current simulator/direct documentation.
3. G3-D: versioned Skills/Prompt and truthful end-to-end Agent trace.
4. G3-E: evidence-linked figures and bounded innovation narrative.
5. G3-F: five-minute demo, script, captions, fallback recording.
6. G3-G: privacy/license/redistribution review and release-candidate audit.

No G3-B implementation is performed by this checkpoint.
