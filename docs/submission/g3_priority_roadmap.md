# G3 Priority Roadmap

- Total risk assignments: 59

| Risk | Requirement | Level | Owner | Dependency | Action |
| --- | --- | --- | --- | --- | --- |
| RISK-PRIM-004 | REQ-PRIM-004 | INFO | NO_ACTION | NONE | 维持边界，规则变化时重新评估 |
| RISK-PRIM-005 | REQ-PRIM-005 | INFO | NO_ACTION | NONE | 维持边界，规则变化时重新评估 |
| RISK-TOPO-002 | REQ-TOPO-002 | HIGH | G3-B | NONE | 形成可注入拓扑接口和静态兼容说明；实机探测留待设备阶段 |
| RISK-TOPO-005 | REQ-TOPO-005 | HIGH | G3-C | NONE | 在技术报告中给出状态机与限制；实机留待未来 |
| RISK-TOPO-006 | REQ-TOPO-006 | HIGH | G3-C | NONE | G3-C 明确静态配置边界，G3-B 补交付说明 |
| RISK-TOPO-007 | REQ-TOPO-007 | MEDIUM | REAL_DEVICE_FUTURE | REAL_DEVICE | 在获授权设备环境执行冻结的 direct acceptance |
| RISK-INNOV-001 | REQ-INNOV-001 | HIGH | G3-E | NONE | G3-E 仅展示已实现差异；G3-C 逐算法说明实现深度 |
| RISK-INNOV-003 | REQ-INNOV-003 | HIGH | G3-C | NONE | G3-C 报告模型；REAL_DEVICE_FUTURE 验收 |
| RISK-INNOV-004 | REQ-INNOV-004 | MEDIUM | G3-E | NONE | G3-E 不作实现主张；若参赛策略需要，另设后续功能 checkpoint |
| RISK-INNOV-006 | REQ-INNOV-006 | BLOCKER | G3-D | USER_ACTION | G3-D 建立可复现的新 trace；用户提供可合法使用的历史原始记录 |
| RISK-CO-001 | REQ-CO-001 | BLOCKER | G3-B | NONE | G3-B 确定官方插件 ABI、兼容包装层和提交入口 |
| RISK-CO-002 | REQ-CO-002 | HIGH | G3-C | NONE | G3-C 写入 direct readiness appendix；设备阶段验收 |
| RISK-CO-003 | REQ-CO-003 | HIGH | REAL_DEVICE_FUTURE | REAL_DEVICE | 保留 readiness 边界，设备阶段执行 |
| RISK-CO-004 | REQ-CO-004 | HIGH | G3-C | NONE | G3-C/G3-E 明确未实现；真实实现需独立后续 checkpoint |
| RISK-CO-006 | REQ-CO-006 | MEDIUM | REAL_DEVICE_FUTURE | REAL_DEVICE | 有设备且授权后执行冻结 acceptance |
| RISK-REL-003 | REQ-REL-003 | HIGH | G3-C | NONE | G3-C 说明模拟范围；设备实现需后续 checkpoint |
| RISK-REL-007 | REQ-REL-007 | MEDIUM | REAL_DEVICE_FUTURE | REAL_DEVICE | 有设备且授权后执行 |
| RISK-SCALE-002 | REQ-SCALE-002 | HIGH | G3-C | NONE | G3-C 形成逐算法复杂度与实现映射 |
| RISK-SCALE-003 | REQ-SCALE-003 | HIGH | G3-C | NONE | G3-C/G3-E 明确未验证；不得从通信 latency 推导训练加速比 |
| RISK-SCALE-004 | REQ-SCALE-004 | MEDIUM | REAL_DEVICE_FUTURE | REAL_DEVICE | 设备资源可用后执行 |
| RISK-CORR-005 | REQ-CORR-005 | HIGH | G3-C | USER_ACTION | G3-C 明确数据集与容差；用户/赛事规则确认阈值解释 |
| RISK-CPP-001 | REQ-CPP-001 | BLOCKER | G3-B | NONE | G3-B 冻结最终插件 ABI 与构建产物 |
| RISK-CPP-002 | REQ-CPP-002 | BLOCKER | G3-B | NONE | G3-B 定义并验证最终 .so、导出 ABI 和无设备构建说明 |
| RISK-CPP-004 | REQ-CPP-004 | HIGH | G3-B | NONE | G3-B 输出正式 ABI 清单并校验 |
| RISK-CPP-005 | REQ-CPP-005 | BLOCKER | G3-B | USER_ACTION | G3-B 默认排除官方 DSO；用户完成 redistribution review |
| RISK-CPP-006 | REQ-CPP-006 | BLOCKER | G3-B | NONE | G3-B 增加兼容说明与唯一插件入口 |
| RISK-AGENT-001 | REQ-AGENT-001 | HIGH | G3-B | NONE | G3-B 提供环境锁定和 quick/full reproduce |
| RISK-AGENT-002 | REQ-AGENT-002 | HIGH | G3-D | NONE | G3-D 重建版本化 Skills 清单 |
| RISK-AGENT-004 | REQ-AGENT-004 | HIGH | G3-D | NONE | G3-D 增加版本、schema、最小可公开调用样例 |
| RISK-AGENT-005 | REQ-AGENT-005 | BLOCKER | G3-D | USER_ACTION | G3-D 生成新的脱敏权威 trace；用户提供/确认历史记录使用边界 |
| RISK-AGENT-006 | REQ-AGENT-006 | BLOCKER | G3-D | USER_ACTION | G3-D 只创建未来可验证 trace，不伪造历史；用户披露可用历史材料与人工工作 |
| RISK-AGENT-007 | REQ-AGENT-007 | BLOCKER | G3-D | NONE | G3-D 建立受控、可重放、脱敏的完整流程 |
| RISK-SIM-001 | REQ-SIM-001 | HIGH | G3-B | NONE | G3-B 提供无隐藏状态的 simulator quick/full reproduce |
| RISK-SIM-006 | REQ-SIM-006 | HIGH | G3-B | NONE | G3-B 建复现入口；G3-C 更新 simulator manual |
| RISK-TEST-002 | REQ-TEST-002 | HIGH | G3-B | NONE | G3-B 将模拟场景打包并标注；真实设备留待未来 |
| RISK-TEST-003 | REQ-TEST-003 | HIGH | G3-B | NONE | G3-B 提供统一入口与 quick/full 模式 |
| RISK-TEST-004 | REQ-TEST-004 | HIGH | G3-B | NONE | G3-B/G3-G 分别验证构建和 release candidate |
| RISK-DOC-001 | REQ-DOC-001 | HIGH | G3-B | NONE | G3-B 更新复现说明并验证 |
| RISK-DOC-002 | REQ-DOC-002 | HIGH | G3-C | NONE | G3-C 以当前审计为基线重建正式报告 |
| RISK-DOC-003 | REQ-DOC-003 | HIGH | G3-C | NONE | G3-C 生成正式 simulator reports |
| RISK-DOC-004 | REQ-DOC-004 | HIGH | G3-C | NONE | G3-C 更新正式 simulator manual |
| RISK-DOC-005 | REQ-DOC-005 | HIGH | G3-D | NONE | G3-D 完成专项交付 |
| RISK-PACKAGE-001 | REQ-PACKAGE-001 | BLOCKER | G3-B | NONE | G3-B 构建 staging package 和 manifest，不在 G3-A 打包 |
| RISK-PACKAGE-002 | REQ-PACKAGE-002 | BLOCKER | G3-D | NONE | G3-D 产出后由 G3-B/G3-G 纳入包 |
| RISK-PACKAGE-003 | REQ-PACKAGE-003 | HIGH | G3-B | NONE | G3-B 生成 staging manifest 与复现入口 |
| RISK-PACKAGE-004 | REQ-PACKAGE-004 | BLOCKER | G3-B | USER_ACTION | G3-B 建 manifest；G3-G 执行 release audit；用户确认许可证 |
| RISK-PACKAGE-005 | REQ-PACKAGE-005 | HIGH | G3-G | USER_ACTION | G3-B 验证 staging；G3-G 验证 release candidate；用户确认平台约束 |
| RISK-REPORT-001 | REQ-REPORT-001 | HIGH | G3-C | NONE | G3-C 生成 SIMULATOR PERFORMANCE REPORT；G3-E 生成图表 |
| RISK-REPORT-002 | REQ-REPORT-002 | HIGH | G3-C | NONE | G3-C 更新正式 reliability report |
| RISK-REPORT-003 | REQ-REPORT-003 | HIGH | G3-C | NONE | G3-C/E 使用受限措辞；实机指标留待未来 |
| RISK-DEMO-001 | REQ-DEMO-001 | HIGH | G3-F | NONE | G3-F 制作视频，不得标记 HARDWARE_BLOCKED |
| RISK-DEMO-002 | REQ-DEMO-002 | MEDIUM | G3-F | NONE | G3-F 完成演示资产 |
| RISK-DEMO-003 | REQ-DEMO-003 | HIGH | G3-F | NONE | G3-F 使用 G3-A claim matrix 制作；G3-G 复核 |
| RISK-COMP-001 | REQ-COMP-001 | BLOCKER | USER_ACTION | USER_ACTION | 用户选择许可证并确认版权；G3-G 纳入 release |
| RISK-COMP-002 | REQ-COMP-002 | HIGH | G3-G | USER_ACTION | G3-G 建 SBOM/依赖清单；G3-D 补生成 provenance |
| RISK-COMP-003 | REQ-COMP-003 | BLOCKER | USER_ACTION | USER_ACTION | 保持默认排除；用户完成 REDISTRIBUTION_REVIEW_REQUIRED |
| RISK-COMP-004 | REQ-COMP-004 | BLOCKER | USER_ACTION | USER_ACTION | G3-B/G3-G 默认排除；用户完成 CONFIDENTIALITY_REVIEW_REQUIRED |
| RISK-COMP-005 | REQ-COMP-005 | HIGH | G3-G | NONE | G3-G 执行 secrets/privacy scan；仅纳入脱敏日志 |
| RISK-COMP-006 | REQ-COMP-006 | HIGH | USER_ACTION | USER_ACTION | 用户提供团队/平台/公开策略与人工干预披露 |

## User actions

| ID | Reason | Action |
| --- | --- | --- |
| UA-001 | CONFIDENTIALITY_REVIEW_REQUIRED | Confirm whether the controlled competition DOCX may be included in the submission; public release remains excluded by default. |
| UA-002 | LICENSE_REVIEW_REQUIRED | Choose the project license and confirm team/copyright ownership. |
| UA-003 | REDISTRIBUTION_REVIEW_REQUIRED | Confirm that official CANN/HCOMM/HCCL source and binaries remain excluded, or provide redistribution authorization. |
| UA-004 | HISTORICAL_RECORD_UNAVAILABLE | Provide any lawful original Prompt/Agent run records and disclose human intervention; missing history must not be reconstructed. |
| UA-005 | SUBMISSION_PLATFORM_CONFIRMATION | Confirm registration-platform archive format, size limits, required team fields, and final submission inventory. |
| UA-006 | PUBLIC_RELEASE_DECISION | Decide whether a public release will be made and which evidence/third-party assets may be public. |
| UA-007 | ACCEPTANCE_INTERPRETATION_REQUIRED | Confirm the competition interpretation of the <=1e-6 threshold for FP16/BF16 final quantized outputs. |
