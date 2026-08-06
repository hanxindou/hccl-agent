"""Generate the G3-A competition delivery gap audit.

The inventory is deliberately curated from the controlled competition DOCX,
current source/build/test files, and frozen G2 evidence.  The generator checks
every referenced repository path and never infers compliance from a filename.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DOC = "docs/2026年中国研究生人工智能大赛--华为赛题.docx"
SOURCE_PAGE = "1 (OOXML logical stream; rendered page metadata unavailable)"
G2_E = "experiments/hccl_vm/evidence/g2_e_summary_20260730T095800.105217Z"
G2_F_1 = "experiments/direct_api/evidence/g2_f_1_20260730T203000Z"
G2_F_2 = "experiments/direct_api/evidence/g2_f_2_20260730T210000Z"
G2_F_3 = "experiments/direct_api/evidence/g2_f_3_20260802T000000Z"
G2_F_4 = "experiments/direct_api/evidence/g2_f_4_20260802T010000Z"
G2_F_5 = "experiments/simulator/evidence/g2_f_5_simulator_20260804T010000Z"
G2_F_6 = "experiments/simulator/evidence/g2_f_6_simulator_20260804T020000Z"
G2_F_7 = "experiments/final_audit/evidence/g2_f_7_20260805T010000Z"

STATUSES = {
    "SATISFIED", "PARTIALLY_SATISFIED", "MISSING", "UNVERIFIED",
    "HARDWARE_BLOCKED", "NOT_APPLICABLE",
}
EVIDENCE_LEVELS = {
    "E0_NONE", "E1_DOCUMENTED", "E2_STATIC_VERIFIED", "E3_HOST_EXECUTED",
    "E4_OFFICIAL_VM_EXECUTED", "E5_SIMULATOR_VALIDATED", "E6_REAL_DEVICE_MEASURED",
}
RISKS = {"BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"}
OWNERS = {
    "G3-B", "G3-C", "G3-D", "G3-E", "G3-F", "G3-G",
    "REAL_DEVICE_FUTURE", "USER_ACTION", "NO_ACTION",
}
CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}
DELIVERABLE_CATEGORIES = {
    "SOURCE_CODE", "NATIVE_PLUGIN", "BUILD_CONFIGURATION", "TEST_TOOL",
    "BENCHMARK_TOOL", "FAULT_INJECTION_TOOL", "AGENT_ENGINEERING",
    "PROMPT_AND_SKILLS", "SIMULATOR", "CONFIGURATION", "EVIDENCE",
    "TECHNICAL_REPORT", "DEMO_MATERIAL", "RELEASE_METADATA", "INTERNAL_REFERENCE",
}


def _req(
    requirement_id: str,
    source_section: str,
    summary: str,
    level: str,
    category: str,
    acceptance: str,
    status: str,
    evidence_level: str,
    confidence: str,
    *,
    implementation: Iterable[str] = (),
    tests: Iterable[str] = (),
    evidence: Iterable[str] = (),
    documentation: Iterable[str] = (),
    agent_trace: Iterable[str] = (),
    tracks: Iterable[str] = (),
    gap: str = "",
    risk: str = "INFO",
    impact: str = "",
    action: str = "",
    owner: str = "NO_ACTION",
    user_action: bool = False,
    hardware_blocked: bool = False,
    hardware_dependency: str = "NONE",
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "source_document": SOURCE_DOC,
        "source_section": source_section,
        "source_page": SOURCE_PAGE,
        "requirement_summary": summary,
        "requirement_level": level,
        "deliverable_category": category,
        "acceptance_expectation": acceptance,
        "hardware_dependency": hardware_dependency,
        "confidentiality": "INTERNAL_REFERENCE_SUMMARY_ONLY",
        "implementation_paths": list(implementation),
        "test_paths": list(tests),
        "evidence_paths": list(evidence),
        "documentation_paths": list(documentation),
        "agent_trace_paths": list(agent_trace),
        "evidence_tracks": list(tracks),
        "status": status,
        "evidence_level": evidence_level,
        "confidence": confidence,
        "gap_summary": gap,
        "risk_level": risk,
        "impact": impact,
        "recommended_action": action,
        "owner_checkpoint": owner,
        "user_action_required": user_action,
        "hardware_blocked": hardware_blocked,
    }


def build_requirements() -> list[dict[str, Any]]:
    reqs: list[dict[str, Any]] = []
    add = reqs.append
    primitive_impl = ["hcccl/src/hccl_comm.c", "hcccl/src/hccl_algorithms.c"]
    primitive_evidence = [G2_E, G2_F_5, G2_F_7]

    add(_req("REQ-PRIM-001", "任务范围/通信原语与算法要求", "实现 AllReduce 核心集通信原语", "MANDATORY", "NATIVE_PLUGIN", "C/C++/CPU_SIM、官方 VM 与模拟器轨道均有可追溯验证", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=primitive_impl, tests=["hcccl/tests/test_api_wrappers.c", "tests/test_allgather.py"], evidence=primitive_evidence, documentation=["docs/correctness_matrix.md"], tracks=["CPU_SIM:E3_HOST_EXECUTED", "ASCEND_HCCL_VM:E4_OFFICIAL_VM_EXECUTED", "SIMULATOR_ACCEPTANCE:E5_SIMULATOR_VALIDATED"]))
    add(_req("REQ-PRIM-002", "任务范围/通信原语与算法要求", "实现 AllGather 核心集通信原语", "MANDATORY", "NATIVE_PLUGIN", "三原语之一，结果布局和 rank 顺序可验证", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=primitive_impl, tests=["hcccl/tests/test_allgather.c", "tests/test_allgather.py"], evidence=primitive_evidence, documentation=["docs/correctness_matrix.md"], tracks=["CPU_SIM:E3_HOST_EXECUTED", "ASCEND_HCCL_VM:E4_OFFICIAL_VM_EXECUTED", "SIMULATOR_ACCEPTANCE:E5_SIMULATOR_VALIDATED"]))
    add(_req("REQ-PRIM-003", "任务范围/通信原语与算法要求", "实现 ReduceScatter 核心集通信原语", "MANDATORY", "NATIVE_PLUGIN", "三原语之一，归约和分片布局可验证", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=primitive_impl, tests=["hcccl/tests/test_reducescatter.c", "tests/test_reducescatter.py"], evidence=primitive_evidence, documentation=["docs/correctness_matrix.md"], tracks=["CPU_SIM:E3_HOST_EXECUTED", "ASCEND_HCCL_VM:E4_OFFICIAL_VM_EXECUTED", "SIMULATOR_ACCEPTANCE:E5_SIMULATOR_VALIDATED"]))
    add(_req("REQ-PRIM-004", "任务范围/通信原语与算法要求", "Broadcast 未被选为当前至少三种原语之一", "OPTIONAL", "SOURCE_CODE", "明确记录为未选择的可选原语，不伪装成已交付", "NOT_APPLICABLE", "E2_STATIC_VERIFIED", "HIGH", implementation=["hcccl/src/hccl_comm.c"], gap="NOT_SELECTED_OPTIONAL_PRIMITIVE；当前 wrapper 返回 NOT_SUPPORTED", risk="INFO", impact="不影响至少三种原语的当前范围", action="维持边界，规则变化时重新评估", owner="NO_ACTION"))
    add(_req("REQ-PRIM-005", "任务范围/通信原语与算法要求", "AlltoAll 未被选为当前至少三种原语之一", "OPTIONAL", "SOURCE_CODE", "明确记录为未选择的可选原语", "NOT_APPLICABLE", "E0_NONE", "HIGH", gap="NOT_SELECTED_OPTIONAL_PRIMITIVE", risk="INFO", impact="不影响至少三种原语的当前范围", action="维持边界，规则变化时重新评估", owner="NO_ACTION"))

    add(_req("REQ-TOPO-001", "任务范围/硬件与拓扑适配场景", "覆盖 Full Mesh、Ring 与分层 Fat-Tree 拓扑模型", "MANDATORY", "SIMULATOR", "配置、算法选择、模型和 evidence 可追溯", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["skills/topology_graph.py", "simulator/g2_f_6_acceptance.py"], tests=["tests/test_topology_graph.py", "tests/test_g2_f_6_simulator_acceptance.py"], evidence=[f"{G2_F_6}/topology_inventory.json"], documentation=["docs/topology_cost_model.md"]))
    add(_req("REQ-TOPO-002", "任务范围/硬件与拓扑适配场景", "表达异构设备与非对称链路", "MANDATORY", "SIMULATOR", "异构拓扑和非对称参数影响模拟结果", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["skills/topology_graph.py", "hardware/profile.py", "simulator/g2_f_6_acceptance.py"], tests=["tests/test_hardware_profile.py", "tests/test_topology_sensitivity_report.py"], evidence=[f"{G2_F_6}/topology_inventory.json"], gap="仅为 SIMULATOR_CONFIGURED；未自动探测 910A2/910A3 或真实非对称链路", risk="HIGH", impact="硬件感知评分缺少真实输入闭环", action="形成可注入拓扑接口和静态兼容说明；实机探测留待设备阶段", owner="G3-B"))
    add(_req("REQ-TOPO-003", "关键技术要求/硬件感知", "建模 HCCS、RoCE、PCIe 带宽、延迟与误码率", "MANDATORY", "CONFIGURATION", "参数来源、单位、不确定性和限制可审计", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["config/cluster.json", "simulator/g2_f_6_acceptance.py"], tests=["tests/test_calibration_profile.py"], evidence=[f"{G2_F_6}/parameter_provenance.json"], documentation=["docs/simulator_guide.md"], tracks=["SIMULATOR_CONFIGURED", "REAL_HARDWARE_DETECTED:not achieved"]))
    add(_req("REQ-TOPO-004", "任务范围/硬件与拓扑适配场景", "覆盖小消息与逻辑 1 GB 大消息", "MANDATORY", "SIMULATOR", "边界消息规模可复现且物化策略明确", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/collective_correctness.py", "simulator/g2_f_6_acceptance.py"], tests=["tests/test_g2_f_6_simulator_acceptance.py"], evidence=[f"{G2_F_5}/large_message_audit.json", f"{G2_F_6}/latency_bandwidth_summary.json"], documentation=["docs/correctness_matrix.md"], tracks=["logical 1GB; bounded 4MB materialization; SIMULATED_ONLY"]))
    add(_req("REQ-TOPO-005", "任务范围/硬件与拓扑适配场景", "支持动态拓扑、节点增减与重规划", "MANDATORY", "AGENT_ENGINEERING", "拓扑事件触发检测和重规划，并明确不等于热插拔实机", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["topology/dynamic_topology.py", "topology/topology_events.py", "agent/replanning_skill.py"], tests=["tests/test_dynamic_topology.py", "tests/test_topology_replanning.py"], evidence=[f"{G2_F_6}/fault_injection_trace.jsonl"], gap="host/simulator 事件链可执行，但无真实节点热插拔与不中断训练证明", risk="HIGH", impact="动态适配主张必须限制在模型和控制面", action="在技术报告中给出状态机与限制；实机留待未来", owner="G3-C"))
    add(_req("REQ-TOPO-006", "关键技术要求/硬件感知", "表达 NUMA、HBM 分区与 UB 容量", "MANDATORY", "CONFIGURATION", "配置可读取并参与决策或明确仅文档化", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", implementation=["config/cluster.json", "hardware/node_profile.py"], tests=["tests/test_node_profile.py"], documentation=["docs/simulator_guide.md"], gap="配置存在，但没有真实探测；HBM/UB 未进入官方插件数据路径", risk="HIGH", impact="软硬协同无法由当前 evidence 证明", action="G3-C 明确静态配置边界，G3-B 补交付说明", owner="G3-C"))
    add(_req("REQ-TOPO-007", "技术实现路径/拓扑探测与建模", "通过官方 HCOMM 拓扑接口探测真实硬件", "MANDATORY", "NATIVE_PLUGIN", "官方接口调用在真实设备产生可追溯拓扑", "HARDWARE_BLOCKED", "E0_NONE", "HIGH", implementation=["hcccl/direct/src/hccl_direct_adapter.cpp"], evidence=[G2_F_3, G2_F_4], gap="只有官方 ABI 静态检查和生命周期模型；未调用 hcclGetTopology 或检测真实设备", risk="MEDIUM", impact="不能宣称 REAL_HARDWARE_DETECTED", action="在获授权设备环境执行冻结的 direct acceptance", owner="REAL_DEVICE_FUTURE", hardware_blocked=True, hardware_dependency="REAL_ASCEND_NPU"))

    add(_req("REQ-INNOV-001", "关键技术要求/算法创新", "提供 Ring、Butterfly、Mesh、NHR、Fat-Tree 候选算法", "MANDATORY", "SOURCE_CODE", "算法有可执行调度或明确的模型、测试与 evidence", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["hcccl/src/hccl_algorithms.c", "skills/algorithm_skill.py", "cost_model/engine.py"], tests=["hcccl/tests/test_ring.c", "hcccl/tests/test_butterfly.c", "hcccl/tests/test_nhr.c", "hcccl/tests/test_mesh.c", "hcccl/tests/test_fattree.c"], evidence=[f"{G2_F_6}/algorithm_comparison.json"], gap="多数 C 算法入口复用 host reference kernel；名称不等同完整通信调度或官方插件算法", risk="HIGH", impact="创新叙事若越界会构成真实性风险", action="G3-E 仅展示已实现差异；G3-C 逐算法说明实现深度", owner="G3-E"))
    add(_req("REQ-INNOV-002", "技术实现路径/算法库设计", "依据消息、拓扑与链路自适应选择算法", "MANDATORY", "AGENT_ENGINEERING", "选择输入、候选、评分、反思和结果可复现", "SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["skills/algorithm_skill.py", "skills/optimization_skill.py", "agent/decision_skill.py"], tests=["tests/test_algorithm_selection_flow.py", "tests/test_hardware_aware_selection.py"], documentation=["docs/agent_capabilities.md"]))
    add(_req("REQ-INNOV-003", "关键技术要求/算法创新", "实现动态路由和故障后的路径重选", "RECOMMENDED", "SIMULATOR", "故障场景与替代路径可确定重放", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/failover_engine.py", "skills/topology_graph.py"], tests=["tests/test_failover_engine.py", "tests/test_topology_replanning.py"], evidence=[f"{G2_F_6}/fault_injection_trace.jsonl"], gap="路由切换仅为模拟模型，未进入 C/C++ collective 数据路径", risk="HIGH", impact="不能表述为真实自愈插件", action="G3-C 报告模型；REAL_DEVICE_FUTURE 验收", owner="G3-C"))
    add(_req("REQ-INNOV-004", "技术实现路径/算法库设计", "支持稀疏通信或量化压缩创新", "RECOMMENDED", "SOURCE_CODE", "至少一个可执行实现、正确性测试和对比 evidence", "MISSING", "E1_DOCUMENTED", "HIGH", documentation=["prompts/algorithm_prompt.txt"], gap="只有 Prompt/赛题方向描述，没有稀疏或压缩实现、测试或 evidence", risk="MEDIUM", impact="创新维度覆盖较弱", action="G3-E 不作实现主张；若参赛策略需要，另设后续功能 checkpoint", owner="G3-E"))
    add(_req("REQ-INNOV-005", "Agent 工程实现", "支持反思、重规划与迭代优化", "MANDATORY", "AGENT_ENGINEERING", "Agent 控制流有可执行测试和输出字段", "SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["agent/reflection_skill.py", "agent/replanning_skill.py", "agent/optimization_loop_skill.py"], tests=["tests/test_reflection_skill.py", "tests/test_replanning_skill.py", "tests/test_optimization_loop.py"], documentation=["docs/agent_capabilities.md"]))
    add(_req("REQ-INNOV-006", "Agent 工程实现", "保留算法生成与迭代 trace", "MANDATORY", "PROMPT_AND_SKILLS", "原始 Prompt、生成输出、修改过程与 commit 映射可追溯", "MISSING", "E0_NONE", "HIGH", implementation=["agent/code_generation_skill.py"], agent_trace=["examples/generated_code", "examples/generated_configs"], gap="示例无生成时间、原始调用、Prompt 版本、commit 或人工干预映射；HISTORICAL_RECORD_UNAVAILABLE", risk="BLOCKER", impact="无法证明核心 C/C++ 代码由 Agent 全流程生成", action="G3-D 建立可复现的新 trace；用户提供可合法使用的历史原始记录", owner="G3-D", user_action=True))

    add(_req("REQ-CO-001", "开发约束", "仅基于 HCOMM 开源接口并遵循官方 HCCL ABI", "MANDATORY", "NATIVE_PLUGIN", "公开头文件、实现签名和官方接口可逐项对照", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", implementation=["hcccl/include/hccl_comm.h", "hcccl/direct/src/hccl_direct_adapter.cpp"], tests=["hcccl/direct/tests/direct_adapter_abi_compile.c"], evidence=[G2_F_1, G2_F_3], documentation=["docs/direct_api_contract.md"], gap="CPU_SIM 使用项目本地 hccl* ABI；direct 层只做官方 Hccl* ABI 静态检查，未形成最终插件接口", risk="BLOCKER", impact="最终 .so 可能不被评委加载或被误解为官方插件", action="G3-B 确定官方插件 ABI、兼容包装层和提交入口", owner="G3-B"))
    add(_req("REQ-CO-002", "技术实现路径/昇腾硬件优化", "管理 device/context/stream/communicator 生命周期", "MANDATORY", "NATIVE_PLUGIN", "生命周期、所有权、容量和失败清理有 host harness", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["hcccl/direct/src/hccl_direct_adapter.cpp", "hcccl/direct/include/hccl_direct_adapter.h"], tests=["hcccl/direct/tests/direct_lifecycle_harness_test.cpp", "tests/test_direct_lifecycle_contract.py"], evidence=[G2_F_4], gap="HOST_HARNESS_VERIFIED；没有 ACL/HCCL runtime 执行", risk="HIGH", impact="只证明控制面模型，不能证明设备资源生命周期", action="G3-C 写入 direct readiness appendix；设备阶段验收", owner="G3-C"))
    add(_req("REQ-CO-003", "技术实现路径/昇腾硬件优化", "满足设备 buffer 与三原语容量契约", "MANDATORY", "NATIVE_PLUGIN", "输入输出字节数和溢出检查可验证", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["hcccl/direct/src/hccl_direct_adapter.cpp"], tests=["tests/test_direct_lifecycle_contract.py"], evidence=[f"{G2_F_4}/capacity_contract.json"], gap="只有容量模型；未分配设备 buffer 或提交 collective", risk="HIGH", impact="无法证明 direct 数据路径", action="保留 readiness 边界，设备阶段执行", owner="REAL_DEVICE_FUTURE", hardware_blocked=True, hardware_dependency="REAL_ASCEND_NPU"))
    add(_req("REQ-CO-004", "关键技术要求/软硬协同", "随路归约、UB/HBM 复用、零 CPU、计算通信重叠", "RECOMMENDED", "NATIVE_PLUGIN", "各优化需真实设备或被明确标为设计/模拟", "MISSING", "E1_DOCUMENTED", "HIGH", documentation=["prompts/algorithm_prompt.txt"], gap="仅在 Prompt 和设计文字出现；无 C/C++ 实现、静态证据或 host harness", risk="HIGH", impact="不得用于性能达成或硬件协同已完成的宣传", action="G3-C/G3-E 明确未实现；真实实现需独立后续 checkpoint", owner="G3-C"))
    add(_req("REQ-CO-005", "开发约束", "不得修改官方驱动、固件、HCOMM、HCCL 或 CANN", "MANDATORY", "INTERNAL_REFERENCE", "官方仓库冻结 commit 且 tracked worktree clean", "SATISFIED", "E2_STATIC_VERIFIED", "HIGH", evidence=[f"{G2_F_7}/official_repositories.json"], documentation=["docs/plans/g3-competition-delivery-readiness.md"]))
    add(_req("REQ-CO-006", "技术实现路径/昇腾硬件优化", "执行真实 direct API collective 并形成设备证据", "RECOMMENDED", "EVIDENCE", "真实设备初始化、communicator、buffer、collective 与同步成功", "HARDWARE_BLOCKED", "E0_NONE", "HIGH", implementation=["hcccl/direct/src/hccl_direct_adapter.cpp"], evidence=[G2_F_7], gap="guard 在 runtime 前停止；direct_hccl_api_call=false", risk="MEDIUM", impact="真实 direct acceptance 未完成，但模拟器路径仍允许参赛", action="有设备且授权后执行冻结 acceptance", owner="REAL_DEVICE_FUTURE", hardware_blocked=True, hardware_dependency="REAL_ASCEND_NPU"))

    add(_req("REQ-REL-001", "关键技术要求/可靠性", "支持链路健康监测和退化检测", "MANDATORY", "SIMULATOR", "监测状态与固定 seed 场景可重放", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/health_monitor.py", "simulator/fault_injector.py"], tests=["tests/test_health_monitor.py", "tests/test_f1_reliability_validation.py"], evidence=[f"{G2_F_6}/fault_injection_trace.jsonl"]))
    add(_req("REQ-REL-002", "关键技术要求/可靠性", "覆盖 link down、degradation、timeout 与 retry", "MANDATORY", "FAULT_INJECTION_TOOL", "多类故障和恢复结果有 trace", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/fault_injector.py", "simulator/retry_policy.py"], tests=["tests/test_retry_policy.py", "tests/test_failover_engine.py"], evidence=[f"{G2_F_6}/reliability_summary.json"]))
    add(_req("REQ-REL-003", "技术实现路径/可靠性机制", "实现校验/CRC 与损坏检测", "MANDATORY", "FAULT_INJECTION_TOOL", "模拟损坏可检测并保持恢复后正确性", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["simulator/fault_injector.py"], tests=["tests/test_f1_reliability_validation.py"], documentation=["docs/reliability_report.md"], gap="仅 host/simulator CRC 模型，未进入 C/C++ collective 或真实传输", risk="HIGH", impact="不能宣称真实链路数据校验", action="G3-C 说明模拟范围；设备实现需后续 checkpoint", owner="G3-C"))
    add(_req("REQ-REL-004", "技术实现路径/可靠性机制", "模拟 100 ms 内切换备用路径并处理无路可用", "MANDATORY", "SIMULATOR", "恢复与 expected no-path 场景区分且正确性复检", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/failover_engine.py", "simulator/g2_f_6_acceptance.py"], tests=["tests/test_g2_f_6_simulator_acceptance.py"], evidence=[f"{G2_F_6}/reliability_summary.json"], tracks=["11 recovered scenarios met simulated target", "1 expected no-path failure", "SIMULATED_ONLY"]))
    add(_req("REQ-REL-005", "关键技术要求/可靠性", "模拟重传率不高于 0.1%", "MANDATORY", "SIMULATOR", "定义统计分母与适用范围", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[f"{G2_F_6}/reliability_summary.json"], documentation=["docs/reliability_report.md"], tracks=["simulated_retry_rate=0.00025", "not real RoCE/HCCL retransmission"]))
    add(_req("REQ-REL-006", "参赛作品要求/技术文档", "提供 logical 72h 可靠性证据", "MANDATORY", "EVIDENCE", "事件模型、wall-clock 与 real-hardware 边界明确", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/g2_f_6_acceptance.py"], evidence=[f"{G2_F_6}/logical_72h_summary.json"], tracks=["simulated_duration_seconds=259200", "wall_clock_duration_seconds=0", "SIMULATED_ONLY"]))
    add(_req("REQ-REL-007", "参赛作品要求/技术文档", "真实设备故障切换、重传与 72h 压测", "RECOMMENDED", "EVIDENCE", "真实集群故障和长稳日志可追溯", "HARDWARE_BLOCKED", "E0_NONE", "HIGH", evidence=[G2_F_7], gap="无真实 NPU、链路故障或 72h 压测", risk="MEDIUM", impact="不能给出实机可靠性结论", action="有设备且授权后执行", owner="REAL_DEVICE_FUTURE", hardware_blocked=True, hardware_dependency="REAL_ASCEND_CLUSTER"))

    add(_req("REQ-SCALE-001", "关键技术要求/可扩展性", "覆盖 8/16/32/64/128/256/512/1024 ranks", "MANDATORY", "SIMULATOR", "每个规模点有模型输出、内存估计和真实性标签", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/g2_f_6_acceptance.py"], tests=["tests/test_g2_f_6_simulator_acceptance.py"], evidence=[f"{G2_F_6}/scale_summary.json"], tracks=["logical ranks only", "not real device count"]))
    add(_req("REQ-SCALE-002", "关键技术要求/可扩展性", "算法复杂度为 O(N) 到 O(NlogN) 且内存有界", "MANDATORY", "TECHNICAL_REPORT", "复杂度声明与模型 step、物化上限一致", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["cost_model/engine.py", "simulator/g2_f_6_acceptance.py"], evidence=[f"{G2_F_6}/scale_summary.json"], gap="Fat-Tree 模型为 O(log N)，但 C 算法实现未提供相同的真实调度复杂度证据", risk="HIGH", impact="算法说明必须区分模型和实现", action="G3-C 形成逐算法复杂度与实现映射", owner="G3-C"))
    add(_req("REQ-SCALE-003", "关键技术要求/可扩展性", "达到 8 到 1024 卡线性加速比不低于 90%", "MANDATORY", "TECHNICAL_REPORT", "需要完整 compute workload 或真实训练基准", "UNVERIFIED", "E0_NONE", "HIGH", evidence=[f"{G2_F_6}/scale_summary.json"], gap="只有通信模型扩展趋势，没有 compute workload、训练吞吐或线性加速比计算", risk="HIGH", impact="核心性能目标尚不能判定达成", action="G3-C/G3-E 明确未验证；不得从通信 latency 推导训练加速比", owner="G3-C"))
    add(_req("REQ-SCALE-004", "关键技术要求/可扩展性", "真实 8/64/1024 设备规模验证", "RECOMMENDED", "EVIDENCE", "真实设备规模、拓扑与日志", "HARDWARE_BLOCKED", "E0_NONE", "HIGH", gap="仅模拟 8/64/1024 ranks", risk="MEDIUM", impact="不能宣称真实卡规模支持", action="设备资源可用后执行", owner="REAL_DEVICE_FUTURE", hardware_blocked=True, hardware_dependency="REAL_ASCEND_CLUSTER"))

    add(_req("REQ-CORR-001", "关键技术要求/精度保障", "覆盖 FP16、BF16、FP32，并审计 INT32", "MANDATORY", "TEST_TOOL", "各 dtype 的量化规则与容差明确", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/collective_correctness.py", "hcccl/src/hccl_algorithms.c"], tests=["hcccl/tests/test_dtype_emulation.c", "tests/test_dtype_emulation.py"], evidence=[f"{G2_F_5}/precision_audit.json"], documentation=["docs/correctness_matrix.md"]))
    add(_req("REQ-CORR-002", "任务范围/通信原语与算法要求", "覆盖 SUM、MAX、MIN 归约操作", "MANDATORY", "TEST_TOOL", "AllReduce/ReduceScatter 归约操作有独立检查", "SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["hcccl/src/hccl_algorithms.c"], tests=["hcccl/tests/test_reduce_ops.c", "tests/test_reduce_ops.py"], evidence=[G2_F_5]))
    add(_req("REQ-CORR-003", "评判标准/通信原语正确性", "使用独立 host reference、exact 数据和随机 stress 数据", "MANDATORY", "TEST_TOOL", "reference 不复用被测实现且 seed 可重放", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/collective_correctness.py"], tests=["tests/test_simulator_collective_correctness.py", "tests/test_randomized_collective_correctness.py"], evidence=[f"{G2_F_5}/test_matrix.json"]))
    add(_req("REQ-CORR-004", "评判标准/通信原语正确性", "审计绝对/相对误差、NaN/Inf、hash 与 rank ordering", "MANDATORY", "EVIDENCE", "记录最大误差、有限性、输出 hash 和顺序", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator/collective_correctness.py"], evidence=[f"{G2_F_5}/test_matrix.json", f"{G2_F_6}/latency_bandwidth_summary.json"]))
    add(_req("REQ-CORR-005", "关键技术要求/精度保障", "判定赛题误差不高于 1e-6", "MANDATORY", "TECHNICAL_REPORT", "精确数据与 dtype-aware stress 结论分别报告", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[f"{G2_F_5}/precision_audit.json"], documentation=["docs/correctness_matrix.md"], gap="exact 数据满足零误差和 1e-6；FP16/BF16 stress 使用 1e-3/1e-2，不可替代统一 1e-6 结论", risk="HIGH", impact="不能宣称所有混合精度均达到 1e-6", action="G3-C 明确数据集与容差；用户/赛事规则确认阈值解释", owner="G3-C", user_action=True))
    add(_req("REQ-CORR-006", "评判标准/通信原语正确性", "CPU_SIM 与 simulator 交叉验证", "RECOMMENDED", "TEST_TOOL", "三原语 host 语义一致且轨道隔离", "SATISFIED", "E3_HOST_EXECUTED", "HIGH", tests=["tests/test_g2_f_6_simulator_acceptance.py"], evidence=[f"{G2_F_5}/cross_backend_audit.json"]))

    add(_req("REQ-CPP-001", "开发约束", "核心交付代码采用 C/C++", "MANDATORY", "SOURCE_CODE", "三原语核心入口位于 C/C++ 且可定位", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["hcccl/src/hccl_comm.c", "hcccl/src/hccl_algorithms.c", "hcccl/direct/src/hccl_direct_adapter.cpp"], tests=["hcccl/tests/test_api_wrappers.c"], evidence=[G2_F_2], gap="CPU_SIM 核心为 C；direct C++ 仅 readiness 模型，未承担官方 collective 算法插件角色", risk="BLOCKER", impact="当前不能证明满足最终 HCCL 插件交付角色", action="G3-B 冻结最终插件 ABI 与构建产物", owner="G3-B"))
    add(_req("REQ-CPP-002", "参赛作品要求/代码包", "提交可重复构建的 HCCL 算法 .so", "MANDATORY", "NATIVE_PLUGIN", "当前源码构建出明确 hash 的 Linux .so，且角色与官方接口一致", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["hcccl/CMakeLists.txt", "hcccl/src/hccl_comm.c", "hcccl/src/hccl_algorithms.c"], tests=["hcccl/tests/test_api_wrappers.c"], evidence=[G2_F_2], gap="可构建的 libhccl_plugin.so 是 CPU_SIM；direct 产物为静态 libhccl_direct_adapter.a，不是最终官方插件 .so", risk="BLOCKER", impact="最终参赛核心二进制不满足已证明的官方插件加载契约", action="G3-B 定义并验证最终 .so、导出 ABI 和无设备构建说明", owner="G3-B"))
    add(_req("REQ-CPP-003", "参赛作品要求/代码包", "提供匹配头文件和 CMake 构建入口", "MANDATORY", "BUILD_CONFIGURATION", "公开头文件、target 和 install 规则一致", "SATISFIED", "E2_STATIC_VERIFIED", "HIGH", implementation=["hcccl/include/hccl_comm.h", "hcccl/include/hccl_algorithms.h", "hcccl/CMakeLists.txt"], tests=["tests/test_direct_adapter_build_contract.py"], evidence=[G2_F_2]))
    add(_req("REQ-CPP-004", "开发约束", "导出三原语和插件发现符号", "MANDATORY", "NATIVE_PLUGIN", "当前构建产物的动态符号与公开头文件一致", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", implementation=["hcccl/include/hccl_comm.h", "hcccl/src/hccl_comm.c"], tests=["hcccl/tests/test_api_wrappers.c"], evidence=[G2_F_2], gap="历史 evidence 只列 direct static archive 的 4 个符号；G3-A 需静态查询当前 CPU_SIM .so，且该 ABI 仍非官方 direct plugin", risk="HIGH", impact="符号存在不等于官方加载兼容", action="G3-B 输出正式 ABI 清单并校验", owner="G3-B"))
    add(_req("REQ-CPP-005", "参赛作品要求/代码包", "插件仅依赖允许的系统/官方库", "MANDATORY", "NATIVE_PLUGIN", "CPU_SIM 与 direct 依赖分别列出，官方库不随包默认分发", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", evidence=[f"{G2_F_2}/cpu_sim_ldd.txt", f"{G2_F_3}/build_link.json"], gap="CPU_SIM 仅 libc；direct link audit 依赖 CANN DSOs，其再分发权未确认且 artifact 不是提交插件", risk="BLOCKER", impact="错误打包官方二进制会产生合规风险", action="G3-B 默认排除官方 DSO；用户完成 redistribution review", owner="G3-B", user_action=True))
    add(_req("REQ-CPP-006", "开发约束", "赛题接口名称与项目 ABI 一致并区分 CPU_SIM/direct", "MANDATORY", "TECHNICAL_REPORT", "不得将 hccl* 项目 ABI 或 CPU_SIM .so 误标为官方 Hccl* direct plugin", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", implementation=["hcccl/include/hccl_comm.h", "hcccl/direct/include/hccl_direct_adapter.h"], documentation=["docs/direct_api_contract.md"], evidence=[G2_F_7], gap="两套 ABI 已隔离但缺最终评委兼容说明/包装层", risk="BLOCKER", impact="交付件身份不清会导致评审构建或加载失败", action="G3-B 增加兼容说明与唯一插件入口", owner="G3-B"))

    add(_req("REQ-AGENT-001", "Agent 专项输出物", "提供可独立运行的 Agent 工程入口", "MANDATORY", "AGENT_ENGINEERING", "无需隐藏状态即可启动代表 CPU_SIM 流程", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["main.py", "agent/hccl_agent.py"], tests=["tests/test_agent.py", "tests/test_backend_selection.py"], documentation=["README.MD"], gap="入口存在，但无冻结依赖清单、clean-environment 安装与一键复现验证", risk="HIGH", impact="评委环境可能无法独立重现", action="G3-B 提供环境锁定和 quick/full reproduce", owner="G3-B"))
    add(_req("REQ-AGENT-002", "Agent 专项输出物", "提交 Agent Skills 能力清单", "MANDATORY", "PROMPT_AND_SKILLS", "能力模块与源码/测试一一映射", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["skills", "agent"], tests=["tests/test_planning_skill.py", "tests/test_reflection_skill.py"], documentation=["docs/agent_capabilities.md"], gap="能力文档含已过时的 C 层范围描述，未形成提交 manifest", risk="HIGH", impact="会混淆当前能力和历史状态", action="G3-D 重建版本化 Skills 清单", owner="G3-D"))
    add(_req("REQ-AGENT-003", "Agent 工程实现", "覆盖 planning、topology、generation、selection、execution、evaluation、reflection、replanning、reliability、reporting", "MANDATORY", "AGENT_ENGINEERING", "模块可定位且 focused tests 覆盖", "SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["agent/hccl_agent.py", "agent/planning_skill.py", "agent/code_generation_skill.py", "agent/reflection_skill.py", "agent/replanning_skill.py"], tests=["tests/test_planning_skill.py", "tests/test_code_generation_flow.py", "tests/test_reflection_skill.py", "tests/test_replanning_skill.py"]))
    add(_req("REQ-AGENT-004", "Agent 专项输出物", "提交版本化 Prompt 体系及输入/输出 schema", "MANDATORY", "PROMPT_AND_SKILLS", "Prompt 文件版本、占位符、输入输出和调用记录均明确", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", implementation=["prompts/algorithm_prompt.txt", "agent/prompt_engine.py"], tests=["tests/test_llm_client.py"], gap="Prompt 文件有 5 类模板但无显式版本/schema；本地调用日志被 gitignore 排除", risk="HIGH", impact="Prompt 复现和结果对照不稳定", action="G3-D 增加版本、schema、最小可公开调用样例", owner="G3-D"))
    add(_req("REQ-AGENT-005", "参赛作品要求/代码包", "提交 Agent 运行日志与 Prompt 调用记录", "MANDATORY", "EVIDENCE", "仓库提交中存在脱敏、可追溯、与 commit 对应的日志", "MISSING", "E0_NONE", "HIGH", implementation=["agent/experiment_logger.py", "agent/prompt_engine.py"], gap="logs/ 下本机记录被 .gitignore 排除；仓库没有可提交的权威 Agent run/prompt log", risk="BLOCKER", impact="评委无法复现 Agent 生成全过程", action="G3-D 生成新的脱敏权威 trace；用户提供/确认历史记录使用边界", owner="G3-D", user_action=True))
    add(_req("REQ-AGENT-006", "Agent 专项输出物", "建立 generated code trace、commit mapping 与人工干预披露", "MANDATORY", "EVIDENCE", "每个核心产物关联 Prompt、输出、审核、修改与 commit", "MISSING", "E0_NONE", "HIGH", agent_trace=["examples/generated_code", "examples/generated_configs"], gap="示例无来源元数据；历史原始 Prompt/Agent 记录不可由当前仓库恢复", risk="BLOCKER", impact="无法证实核心算法和代码均通过 Agent 完成", action="G3-D 只创建未来可验证 trace，不伪造历史；用户披露可用历史材料与人工工作", owner="G3-D", user_action=True))
    add(_req("REQ-AGENT-007", "评判标准", "评委可完整复现 Agent 生成算法与代码全过程", "MANDATORY", "AGENT_ENGINEERING", "独立入口从 Prompt 输入到代码/测试/evidence 输出", "MISSING", "E1_DOCUMENTED", "HIGH", implementation=["agent/autonomous_development_loop.py"], tests=["tests/test_autonomous_development_loop.py"], documentation=["docs/agent_development_demo.md"], gap="现有 autonomous loop 是 host 工具演示，未与最终 C/C++ 插件生成和 commit trace 闭环", risk="BLOCKER", impact="Agent 专项验收主链路未形成", action="G3-D 建立受控、可重放、脱敏的完整流程", owner="G3-D"))

    add(_req("REQ-SIM-001", "开发约束", "提供模拟器源码和独立运行入口", "MANDATORY", "SIMULATOR", "评委可运行代表正确性/性能/可靠性流程", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["simulator/collective_correctness.py", "simulator/g2_f_6_acceptance.py", "simulator/tools/run_g2_f_5_acceptance.py", "simulator/tools/run_g2_f_6_acceptance.py"], tests=["tests/test_g2_f_6_simulator_acceptance.py"], gap="验收 runner 存在，但 G2-F-5 需要预构建 CPU_SIM .so；没有统一提交级入口", risk="HIGH", impact="冷启动复现步骤不完整", action="G3-B 提供无隐藏状态的 simulator quick/full reproduce", owner="G3-B"))
    add(_req("REQ-SIM-002", "核心目标", "提供拓扑/硬件参数配置及来源", "MANDATORY", "CONFIGURATION", "配置、单位、参数 provenance、灵敏度和未校准状态齐全", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["config/cluster.json", "simulator/g2_f_6_acceptance.py"], evidence=[f"{G2_F_6}/parameter_provenance.json", f"{G2_F_6}/sensitivity_analysis.json"]))
    add(_req("REQ-SIM-003", "参赛作品要求/技术文档", "提供三原语正确性、logical 1 GB 和 CPU_SIM 交叉验证", "MANDATORY", "EVIDENCE", "固定 seed、hash、误差和限制可审计", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[G2_F_5]))
    add(_req("REQ-SIM-004", "参赛作品要求/技术文档", "提供性能、规模、algorithm comparison、profiling 与 workload trace", "MANDATORY", "EVIDENCE", "p50/p95、baseline、scale、bottleneck、trace 与标签齐全", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[G2_F_6]))
    add(_req("REQ-SIM-005", "参赛作品要求/技术文档", "提供 fault injection、100 ms、retry 与 logical 72h", "MANDATORY", "EVIDENCE", "原始 trace、摘要、固定 seed 和 correctness recheck", "SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[f"{G2_F_6}/fault_injection_trace.jsonl", f"{G2_F_6}/reliability_summary.json", f"{G2_F_6}/logical_72h_summary.json"]))
    add(_req("REQ-SIM-006", "核心目标", "模拟器结果可由评委读取配置、运行、验证日志并对照 evidence", "MANDATORY", "SIMULATOR", "提交包中有统一说明、命令、原始日志、SHA256 和限制", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[G2_F_5, G2_F_6], documentation=["docs/simulator_guide.md"], gap="evidence 完整且有 SHA256，但 simulator guide 描述旧简化模型，缺统一复现/打包入口", risk="HIGH", impact="资产存在但交付体验不可独立验证", action="G3-B 建复现入口；G3-C 更新 simulator manual", owner="G3-B"))

    add(_req("REQ-TEST-001", "参赛作品要求/代码包", "提供 CTest 与 Python 测试体系", "MANDATORY", "TEST_TOOL", "三原语、dtype、op 和 Agent/模拟器均有测试", "SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["hcccl/CMakeLists.txt", "tests"], tests=["hcccl/tests", "tests/test_simulator_collective_correctness.py"], evidence=[f"{G2_F_7}/regression.json"]))
    add(_req("REQ-TEST-002", "参赛作品要求/代码包", "提供单机 8 卡、多机 64 卡和 logical 1024 ranks 场景", "MANDATORY", "TEST_TOOL", "明确模拟 ranks 与真实设备测试区别", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", tests=["tests/test_g2_f_6_simulator_acceptance.py"], evidence=[f"{G2_F_6}/scale_summary.json"], gap="仅 simulator 8/64/1024 ranks；没有真实 8/64 设备脚本验收", risk="HIGH", impact="代码包测试声明必须标记 SIMULATED_ONLY", action="G3-B 将模拟场景打包并标注；真实设备留待未来", owner="G3-B"))
    add(_req("REQ-TEST-003", "参赛作品要求/代码包", "提供 benchmark、stress、fault injection 与 evidence verifier", "MANDATORY", "TEST_TOOL", "工具可定位、可运行且输出可校验", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", implementation=["agent/benchmark_skill.py", "simulator/fault_injector.py", "agent/final_audit.py"], tests=["tests/test_benchmark_runner.py", "tests/test_failover_engine.py"], gap="工具分散，缺 submission-level 统一 CLI 和 clean-environment 运行证明", risk="HIGH", impact="评委需手工拼装流程", action="G3-B 提供统一入口与 quick/full 模式", owner="G3-B"))
    add(_req("REQ-TEST-004", "Agent 专项输出物", "提供 Windows/WSL import、direct build/link/no-device/lifecycle 与 clean environment 测试", "RECOMMENDED", "TEST_TOOL", "静态/host 测试与设备边界分离", "PARTIALLY_SATISFIED", "E3_HOST_EXECUTED", "HIGH", tests=["tests/test_direct_adapter_build_contract.py", "tests/test_direct_link_contract.py", "tests/test_direct_lifecycle_contract.py", "tests/test_g2_f_7_backend_final_audit.py"], evidence=[G2_F_3, G2_F_4, G2_F_7], gap="已有 focused contracts；缺最终提交包 clean extraction/build/run 验证", risk="HIGH", impact="发布候选尚不可判定可复现", action="G3-B/G3-G 分别验证构建和 release candidate", owner="G3-B"))

    add(_req("REQ-DOC-001", "参赛作品要求/技术文档", "提供顶层 README、quick start 与环境指南", "MANDATORY", "TECHNICAL_REPORT", "当前行为、依赖、边界和代表命令准确", "PARTIALLY_SATISFIED", "E1_DOCUMENTED", "HIGH", documentation=["README.MD"], gap="README 有当前三后端边界，但无冻结依赖/clean start，且若干历史命令未作为提交入口验证", risk="HIGH", impact="初次复现不可靠", action="G3-B 更新复现说明并验证", owner="G3-B"))
    add(_req("REQ-DOC-002", "参赛作品要求/技术文档", "提供架构、算法、拓扑、复杂度与硬件适配说明", "MANDATORY", "TECHNICAL_REPORT", "文档与当前代码/evidence 一致", "PARTIALLY_SATISFIED", "E1_DOCUMENTED", "HIGH", documentation=["docs/project_documentation.md", "docs/topology_cost_model.md", "docs/competition_analysis.md"], gap="competition_analysis 等包含已过时的空 Prompt/主流程故障描述；缺 G3 正式算法报告", risk="HIGH", impact="评委可能依据 stale 文档得出错误结论", action="G3-C 以当前审计为基线重建正式报告", owner="G3-C"))
    add(_req("REQ-DOC-003", "参赛作品要求/技术文档", "提供正确性、性能、规模与可靠性报告", "MANDATORY", "TECHNICAL_REPORT", "报告由 evidence 生成并携带 SIMULATED_ONLY 标签", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", documentation=["docs/correctness_matrix.md", "docs/reliability_report.md"], evidence=[G2_F_5, G2_F_6], gap="正确性矩阵和可靠性报告存在；缺基于 G2-F-6 的正式性能/规模/算法对比报告", risk="HIGH", impact="核心评分证据尚未形成评委可读报告", action="G3-C 生成正式 simulator reports", owner="G3-C"))
    add(_req("REQ-DOC-004", "参赛作品要求/技术文档", "提供 simulator manual 与 direct readiness appendix", "MANDATORY", "TECHNICAL_REPORT", "说明运行、参数、限制、direct 静态/host/实机边界", "PARTIALLY_SATISFIED", "E1_DOCUMENTED", "HIGH", documentation=["docs/simulator_guide.md", "docs/direct_api_contract.md", "docs/direct_api_lifecycle_harness.md"], gap="direct 文档较完整；simulator guide 仍是旧概念模型，未覆盖 G2-F-5/F6 evidence workflow", risk="HIGH", impact="模拟器不可按最终 evidence 独立复现", action="G3-C 更新正式 simulator manual", owner="G3-C"))
    add(_req("REQ-DOC-005", "Agent 专项输出物", "提供 Agent architecture、Skills、Prompt、generation trace、known limitations 与 reproduction guide", "MANDATORY", "TECHNICAL_REPORT", "Agent 全流程文档与可运行 trace 一致", "PARTIALLY_SATISFIED", "E1_DOCUMENTED", "HIGH", documentation=["docs/agent_capabilities.md", "docs/agent_development_demo.md"], gap="架构/能力文档存在；缺版本化 Prompt 工程、真实生成 trace、人工干预披露和独立复现手册", risk="HIGH", impact="Agent 专项材料不完整", action="G3-D 完成专项交付", owner="G3-D"))

    add(_req("REQ-PACKAGE-001", "参赛作品要求/代码包", "代码包包含 .so、headers、CMake 与 source", "MANDATORY", "RELEASE_METADATA", "唯一清单中标明构建来源、hash 和 inclusion", "MISSING", "E2_STATIC_VERIFIED", "HIGH", implementation=["hcccl", "hcccl/CMakeLists.txt"], gap="源码/headers/CMake 存在，但最终合规 .so 与 submission manifest 不存在", risk="BLOCKER", impact="当前不能形成合规参赛核心包", action="G3-B 构建 staging package 和 manifest，不在 G3-A 打包", owner="G3-B"))
    add(_req("REQ-PACKAGE-002", "Agent 专项输出物", "代码包包含 Agent source、Skills、Prompt 与 generation logs", "MANDATORY", "RELEASE_METADATA", "所有资产已脱敏并可追溯", "MISSING", "E1_DOCUMENTED", "HIGH", implementation=["agent", "skills", "prompts/algorithm_prompt.txt"], gap="源码/Prompt 在仓库；权威 logs 与 generation trace 缺失", risk="BLOCKER", impact="Agent 专项包不完整", action="G3-D 产出后由 G3-B/G3-G 纳入包", owner="G3-D"))
    add(_req("REQ-PACKAGE-003", "参赛作品要求/代码包", "代码包包含 simulator、config、tests、benchmark、fault tool、logs 与 evidence", "MANDATORY", "RELEASE_METADATA", "提交清单与可运行入口完整", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", implementation=["simulator", "config/cluster.json", "tests"], evidence=[G2_F_5, G2_F_6], gap="资产分散且 docs/guide stale；未建立 submission inclusion/exclusion manifest", risk="HIGH", impact="打包时易漏项或错误纳入内部材料", action="G3-B 生成 staging manifest 与复现入口", owner="G3-B"))
    add(_req("REQ-PACKAGE-004", "参赛作品要求/代码包", "提供 manifest、SHA256、license、excluded files 与 forbidden-data audit", "MANDATORY", "RELEASE_METADATA", "清单可机器校验且不包含内部赛题材料/秘密", "MISSING", "E0_NONE", "HIGH", gap="旧 evidence 有 SHA256；最终提交级 manifest、license 和排除审计未生成", risk="BLOCKER", impact="发布可能不合规或不可验证", action="G3-B 建 manifest；G3-G 执行 release audit；用户确认许可证", owner="G3-B", user_action=True))
    add(_req("REQ-PACKAGE-005", "参赛作品要求/代码包", "clean extraction 后可构建、测试且归档大小/格式符合平台", "MANDATORY", "RELEASE_METADATA", "隔离目录或干净环境完成构建和 quick test", "UNVERIFIED", "E0_NONE", "HIGH", gap="G3-A 不生成 archive；平台格式、大小和 clean extraction 尚未验证", risk="HIGH", impact="最终上传前仍可能失败", action="G3-B 验证 staging；G3-G 验证 release candidate；用户确认平台约束", owner="G3-G", user_action=True))

    add(_req("REQ-REPORT-001", "参赛作品要求/技术文档", "性能报告包含 latency、bandwidth、p50/p95、baseline、algorithm comparison、scale、sensitivity、bottleneck、profiling", "MANDATORY", "TECHNICAL_REPORT", "所有数字链接到 simulator evidence 并注明模型参数", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[G2_F_6], gap="机器 evidence 完整，但正式评委报告未形成", risk="HIGH", impact="性能评分证据不可直接审阅", action="G3-C 生成 SIMULATOR PERFORMANCE REPORT；G3-E 生成图表", owner="G3-C"))
    add(_req("REQ-REPORT-002", "参赛作品要求/技术文档", "可靠性报告包含故障检测、failover、retry、logical 72h、correctness 和限制", "MANDATORY", "TECHNICAL_REPORT", "报告与 trace/SHA256 一致且标注模拟", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", documentation=["docs/reliability_report.md"], evidence=[G2_F_6], gap="现有报告来自早期固定 seed 场景，未汇总 G2-F-6 12 场景与 logical 72h", risk="HIGH", impact="可靠性 evidence 未形成正式交付叙事", action="G3-C 更新正式 reliability report", owner="G3-C"))
    add(_req("REQ-REPORT-003", "技术实现路径/Profiling与调优", "BERT/LLaMA workload 与 msprof/NPU 指标", "RECOMMENDED", "TECHNICAL_REPORT", "真实 workload 或明确的 communication trace，不虚构吞吐/NPU 利用率", "PARTIALLY_SATISFIED", "E5_SIMULATOR_VALIDATED", "HIGH", evidence=[f"{G2_F_6}/workload_trace_summary.json", f"{G2_F_6}/profiling_summary.json"], gap="只有 BERT/LLaMA communication trace；real_model_executed=false、msprof_executed=false、无 throughput", risk="HIGH", impact="不得宣称端到端训练或 NPU profiling", action="G3-C/E 使用受限措辞；实机指标留待未来", owner="G3-C"))

    add(_req("REQ-DEMO-001", "参赛作品要求/演示材料", "提交 5 分钟演示视频", "MANDATORY", "DEMO_MATERIAL", "视频存在并覆盖指定主题", "MISSING", "E0_NONE", "HIGH", gap="仓库没有视频文件", risk="HIGH", impact="最终参赛材料不完整", action="G3-F 制作视频，不得标记 HARDWARE_BLOCKED", owner="G3-F"))
    add(_req("REQ-DEMO-002", "参赛作品要求/演示材料", "提供 demo script、CLI、确定性配置、storyboard、旁白、字幕与 fallback recording", "MANDATORY", "DEMO_MATERIAL", "演示可重放且失败有替代路径", "MISSING", "E0_NONE", "HIGH", documentation=["docs/agent_development_demo.md"], gap="只有开发工具演示文档；无比赛 demo script/配置/storyboard/字幕", risk="MEDIUM", impact="视频制作与现场演示风险高", action="G3-F 完成演示资产", owner="G3-F"))
    add(_req("REQ-DEMO-003", "参赛作品要求/演示材料", "演示算法、硬件协同、性能、可靠性、Agent 生成、模拟器和 claim boundary", "MANDATORY", "DEMO_MATERIAL", "每个画面使用允许措辞并链接 evidence", "MISSING", "E0_NONE", "HIGH", gap="未建立最终演示内容和 claim boundary slide", risk="HIGH", impact="易出现模拟器/实机表述越界", action="G3-F 使用 G3-A claim matrix 制作；G3-G 复核", owner="G3-F"))

    add(_req("REQ-COMP-001", "开发约束", "提供项目许可证和版权声明", "MANDATORY", "RELEASE_METADATA", "根许可证、作者/团队与生成代码版权边界明确", "MISSING", "E0_NONE", "HIGH", gap="仓库根目录无 LICENSE/NOTICE", risk="BLOCKER", impact="提交或公开发布的使用权不明确", action="用户选择许可证并确认版权；G3-G 纳入 release", owner="USER_ACTION", user_action=True))
    add(_req("REQ-COMP-002", "开发约束", "审计第三方依赖、copied code 与生成代码 provenance", "MANDATORY", "RELEASE_METADATA", "依赖清单、许可证和来源可审阅", "UNVERIFIED", "E1_DOCUMENTED", "MEDIUM", documentation=["README.MD"], gap="无冻结 dependency/license inventory；生成示例 provenance 缺失", risk="HIGH", impact="许可证与来源风险未关闭", action="G3-G 建 SBOM/依赖清单；G3-D 补生成 provenance", owner="G3-G", user_action=True))
    add(_req("REQ-COMP-003", "开发约束", "官方 HCOMM/HCCL/CANN 文件仅作受控引用且不默认再分发", "MANDATORY", "INTERNAL_REFERENCE", "提交清单默认排除官方源码/DSO，用户确认例外", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", evidence=[f"{G2_F_3}/build_link.json", f"{G2_F_7}/official_repositories.json"], gap="仓库未复制官方源码/DSO，但 CANN/HCOMM/HCCL redistribution 权利尚未人工确认", risk="BLOCKER", impact="错误纳入正式包会产生严重合规风险", action="保持默认排除；用户完成 REDISTRIBUTION_REVIEW_REQUIRED", owner="USER_ACTION", user_action=True))
    add(_req("REQ-COMP-004", "核心目标", "正式赛题文件作为 INTERNAL_REFERENCE，不默认进入公开包", "MANDATORY", "INTERNAL_REFERENCE", "审计仅保存摘要/章节，不复制原文", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", implementation=[SOURCE_DOC], gap="当前受控仓库包含正式 DOCX；最终提交和公开 release 是否可包含需用户确认", risk="BLOCKER", impact="未经授权再分发可能违反保密/限制扩散要求", action="G3-B/G3-G 默认排除；用户完成 CONFIDENTIALITY_REVIEW_REQUIRED", owner="USER_ACTION", user_action=True))
    add(_req("REQ-COMP-005", "参赛作品要求/代码包", "排除 secrets、credentials、个人路径与私密 Agent 日志", "MANDATORY", "RELEASE_METADATA", "发布前机器扫描且内部路径最小化", "PARTIALLY_SATISFIED", "E2_STATIC_VERIFIED", "HIGH", documentation=["docs/project_audit.md"], gap="未发现提交凭据证据，但文档含本机绝对路径，ignored logs 未经隐私审计", risk="HIGH", impact="直接打包仓库可能泄露环境信息或日志内容", action="G3-G 执行 secrets/privacy scan；仅纳入脱敏日志", owner="G3-G"))
    add(_req("REQ-COMP-006", "Agent 专项输出物", "公开/提交边界与人工干预披露由用户确认", "MANDATORY", "RELEASE_METADATA", "团队信息、报名格式、公开 release 决策和披露文本齐全", "MISSING", "E0_NONE", "HIGH", gap="仓库无法确定团队/平台字段、公开策略和历史人工干预", risk="HIGH", impact="无法单独完成报名和最终声明", action="用户提供团队/平台/公开策略与人工干预披露", owner="USER_ACTION", user_action=True))

    return reqs


def _artifact(
    artifact_id: str,
    artifact: str,
    category: str,
    current_path: str | None,
    expected_path: str,
    build_status: str,
    run_status: str,
    inclusion: str,
    owner: str,
    *,
    generated_by_agent: str = "UNVERIFIED",
    evidence_status: str = "NONE",
    license_status: str = "PROJECT_LICENSE_MISSING",
    confidentiality: str = "SUBMISSION_ARTIFACT",
    missing_dependencies: Iterable[str] = (),
    limitations: Iterable[str] = (),
    public_release_inclusion: str = "REVIEW_REQUIRED",
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact": artifact,
        "category": category,
        "current_path": current_path,
        "expected_submission_path": expected_path,
        "required_by_competition": True,
        "generated_by_agent": generated_by_agent,
        "build_status": build_status,
        "run_status": run_status,
        "evidence_status": evidence_status,
        "inclusion_decision": inclusion,
        "license_status": license_status,
        "confidentiality": confidentiality,
        "public_release_inclusion": public_release_inclusion,
        "missing_dependencies": list(missing_dependencies),
        "known_limitations": list(limitations),
        "owner_checkpoint": owner,
    }


def build_deliverables() -> list[dict[str, Any]]:
    return [
        _artifact("ART-NATIVE-001", "CPU_SIM shared library source", "NATIVE_PLUGIN", "hcccl", "native/libhccl_plugin.so", "BUILDABLE_STATIC_AUDIT_REQUIRED", "HOST_EXECUTED_HISTORICAL", "INCLUDE_WITH_CPU_SIM_LABEL", "G3-B", evidence_status="G2_F_2", limitations=["CPU_SIM only", "not official HCCL direct plugin"]),
        _artifact("ART-NATIVE-002", "Official-ABI direct adapter", "NATIVE_PLUGIN", "hcccl/direct", "native/direct_adapter_or_wrapper", "STATIC_ARCHIVE_BUILD_ONLY", "HOST_HARNESS_ONLY", "INCLUDE_SOURCE_AND_READINESS_DOCS", "G3-B", evidence_status="G2_F_2_TO_G2_F_4", limitations=["not a final .so", "no runtime API call"]),
        _artifact("ART-BUILD-001", "CMake build configuration", "BUILD_CONFIGURATION", "hcccl/CMakeLists.txt", "native/CMakeLists.txt", "PRESENT", "CONFIGURED_HISTORICAL", "INCLUDE", "G3-B", evidence_status="G2_F_2_TO_G2_F_4"),
        _artifact("ART-SOURCE-001", "Public CPU_SIM headers", "SOURCE_CODE", "hcccl/include", "native/include", "PRESENT", "NOT_EXECUTABLE", "INCLUDE", "G3-B"),
        _artifact("ART-SOURCE-002", "Direct adapter public header", "SOURCE_CODE", "hcccl/direct/include/hccl_direct_adapter.h", "native/include/hccl_direct_adapter.h", "PRESENT", "HOST_HARNESS_ONLY", "INCLUDE_WITH_BOUNDARY", "G3-B"),
        _artifact("ART-AGENT-001", "Agent source and CLI", "AGENT_ENGINEERING", "agent", "agent", "PYTHON_IMPORTABLE", "HOST_EXECUTED", "INCLUDE", "G3-D", evidence_status="G2_F_7"),
        _artifact("ART-AGENT-002", "Top-level Agent CLI", "AGENT_ENGINEERING", "main.py", "main.py", "PYTHON_IMPORTABLE", "CPU_SIM_HOST_EXECUTED", "INCLUDE", "G3-B", evidence_status="G2_F_7", missing_dependencies=["frozen dependency inventory", "clean-environment bootstrap"]),
        _artifact("ART-SKILL-001", "Agent Skills source", "PROMPT_AND_SKILLS", "skills", "agent/skills", "PYTHON_IMPORTABLE", "HOST_EXECUTED", "INCLUDE", "G3-D"),
        _artifact("ART-PROMPT-001", "Prompt template set", "PROMPT_AND_SKILLS", "prompts/algorithm_prompt.txt", "agent/prompts/algorithm_prompt.txt", "PRESENT", "PARTIAL_RUNTIME_USE", "INCLUDE_AFTER_VERSIONING", "G3-D", limitations=["no explicit version", "no formal input/output schema"]),
        _artifact("ART-TRACE-001", "Authoritative Agent run logs", "EVIDENCE", None, "agent/evidence/runs.jsonl", "MISSING", "MISSING", "MISSING", "G3-D", missing_dependencies=["sanitized authoritative run log", "commit mapping"], limitations=["local logs are ignored and not submission evidence"]),
        _artifact("ART-TRACE-002", "Authoritative Prompt call logs", "EVIDENCE", None, "agent/evidence/prompt_calls.jsonl", "MISSING", "MISSING", "MISSING", "G3-D", missing_dependencies=["sanitized prompt records", "prompt version"]),
        _artifact("ART-TRACE-003", "Generated code and commit trace", "EVIDENCE", "examples/generated_code", "agent/evidence/generation_trace", "UNVERIFIED_PROVENANCE", "STATIC_EXAMPLES_ONLY", "REBUILD_IN_G3_D", "G3-D", limitations=["HISTORICAL_RECORD_UNAVAILABLE"]),
        _artifact("ART-SIM-001", "Simulator source", "SIMULATOR", "simulator", "simulator", "PYTHON_IMPORTABLE", "HOST_EXECUTED", "INCLUDE", "G3-B", evidence_status="G2_F_5_AND_G2_F_6"),
        _artifact("ART-SIM-002", "Simulator acceptance runners", "SIMULATOR", "simulator/tools", "simulator/tools", "PYTHON_IMPORTABLE", "HOST_EXECUTED_HISTORICAL", "INCLUDE_AFTER_REPRO_WRAPPER", "G3-B", evidence_status="G2_F_5_AND_G2_F_6", missing_dependencies=["G2-F-5 requires built CPU_SIM library"]),
        _artifact("ART-CONFIG-001", "Cluster configuration", "CONFIGURATION", "config/cluster.json", "simulator/config/cluster.json", "PRESENT", "READ_BY_AGENT", "INCLUDE", "G3-B", evidence_status="PARAMETER_PROVENANCE_PRESENT", limitations=["relative simulator profile", "not hardware detected"]),
        _artifact("ART-TEST-001", "C tests", "TEST_TOOL", "hcccl/tests", "tests/native", "BUILDABLE", "HOST_EXECUTED_HISTORICAL", "INCLUDE", "G3-B"),
        _artifact("ART-TEST-002", "Python tests", "TEST_TOOL", "tests", "tests/python", "PYTHON_IMPORTABLE", "HOST_EXECUTED_HISTORICAL", "INCLUDE", "G3-B"),
        _artifact("ART-BENCH-001", "Benchmark tools", "BENCHMARK_TOOL", "agent/benchmark_skill.py", "tools/benchmark", "PYTHON_IMPORTABLE", "HOST_EXECUTED", "INCLUDE_AFTER_UNIFIED_CLI", "G3-B"),
        _artifact("ART-FAULT-001", "Fault injection tools", "FAULT_INJECTION_TOOL", "simulator/fault_injector.py", "tools/fault_injection", "PYTHON_IMPORTABLE", "SIMULATOR_EXECUTED", "INCLUDE", "G3-B", evidence_status="G2_F_6"),
        _artifact("ART-EVID-001", "G2-E official VM final evidence", "EVIDENCE", G2_E, "evidence/g2_e", "IMMUTABLE", "VERIFIED", "INCLUDE_OR_REFERENCE_AFTER_SIZE_REVIEW", "G3-B", evidence_status="SHA256_VERIFIED", license_status="PROJECT_EVIDENCE", limitations=["HCCL-VM subprocess, not real NPU"]),
        _artifact("ART-EVID-002", "G2-F final evidence", "EVIDENCE", G2_F_7, "evidence/g2_f_7", "IMMUTABLE", "VERIFIED", "INCLUDE", "G3-B", evidence_status="SHA256_VERIFIED", license_status="PROJECT_EVIDENCE"),
        _artifact("ART-EVID-003", "Simulator correctness evidence", "EVIDENCE", G2_F_5, "evidence/simulator_correctness", "IMMUTABLE", "VERIFIED", "INCLUDE", "G3-B", evidence_status="SHA256_VERIFIED", license_status="PROJECT_EVIDENCE"),
        _artifact("ART-EVID-004", "Simulator performance/reliability evidence", "EVIDENCE", G2_F_6, "evidence/simulator_performance", "IMMUTABLE", "VERIFIED", "INCLUDE", "G3-B", evidence_status="SHA256_VERIFIED", license_status="PROJECT_EVIDENCE"),
        _artifact("ART-DOC-001", "Top-level README", "TECHNICAL_REPORT", "README.MD", "README.md", "PRESENT", "NOT_EXECUTABLE", "UPDATE_AND_INCLUDE", "G3-B"),
        _artifact("ART-DOC-002", "Simulator manual", "TECHNICAL_REPORT", "docs/simulator_guide.md", "docs/simulator_manual.md", "STALE", "NOT_EXECUTABLE", "REWRITE_FROM_EVIDENCE", "G3-C"),
        _artifact("ART-DOC-003", "Direct readiness appendix", "TECHNICAL_REPORT", "docs/direct_api_contract.md", "docs/direct_readiness_appendix.md", "PRESENT", "NOT_EXECUTABLE", "UPDATE_AND_INCLUDE", "G3-C"),
        _artifact("ART-DOC-004", "Formal algorithm/correctness/performance/reliability reports", "TECHNICAL_REPORT", None, "reports", "INCOMPLETE", "NOT_EXECUTABLE", "MISSING", "G3-C", missing_dependencies=["formal performance report", "formal scale report", "updated reliability report"]),
        _artifact("ART-DEMO-001", "Five-minute demo video", "DEMO_MATERIAL", None, "demo/five_minute_demo.mp4", "MISSING", "MISSING", "MISSING", "G3-F"),
        _artifact("ART-DEMO-002", "Demo script/storyboard/captions", "DEMO_MATERIAL", None, "demo", "MISSING", "MISSING", "MISSING", "G3-F"),
        _artifact("ART-RELEASE-001", "Submission manifest and SHA256", "RELEASE_METADATA", None, "manifest", "MISSING", "MISSING", "MISSING", "G3-B"),
        _artifact("ART-RELEASE-002", "Project license and notices", "RELEASE_METADATA", None, "LICENSE", "MISSING", "MISSING", "MISSING", "USER_ACTION", missing_dependencies=["license choice", "copyright/team confirmation"]),
        _artifact("ART-INTERNAL-001", "Controlled competition DOCX", "INTERNAL_REFERENCE", SOURCE_DOC, "EXCLUDED_BY_DEFAULT", "PRESENT", "READ_ONLY", "EXCLUDE_PENDING_USER_CONFIRMATION", "USER_ACTION", license_status="CONFIDENTIALITY_REVIEW_REQUIRED", confidentiality="INTERNAL_REFERENCE", public_release_inclusion="EXCLUDE"),
        _artifact("ART-OFFICIAL-001", "Official CANN/HCOMM/HCCL binaries/source", "INTERNAL_REFERENCE", None, "EXCLUDED_BY_DEFAULT", "EXTERNAL_ONLY", "STATIC_QUERIES_ONLY", "EXCLUDE", "USER_ACTION", license_status="REDISTRIBUTION_REVIEW_REQUIRED", confidentiality="OFFICIAL_THIRD_PARTY", public_release_inclusion="EXCLUDE"),
    ]


def _claim(
    claim_id: str,
    claim: str,
    allowed: str,
    prohibited: str,
    source_track: str,
    evidence_level: str,
    evidence_paths: Iterable[str],
    report_location: str,
    demo_usage: str,
    limitations: str,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "claim": claim,
        "allowed_wording": allowed,
        "prohibited_wording": prohibited,
        "source_backend_or_track": source_track,
        "evidence_level": evidence_level,
        "evidence_paths": list(evidence_paths),
        "report_location": report_location,
        "demo_usage": demo_usage,
        "known_limitations": limitations,
    }


def build_claims() -> list[dict[str, Any]]:
    return [
        _claim("CLM-001", "1024 ranks", "在指定 Fat-Tree simulator model 下完成 logical 1024-rank 预测", "真实支持或验证 1024 卡", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_6}/scale_summary.json"], "G3-C scale report", "可展示并固定显示 SIMULATED_ONLY", "无真实设备、传输或训练 workload"),
        _claim("CLM-002", "1 GB", "logical 1 GB 使用分析记账和最大 4 MB 有界物化", "实机传输了 1 GB 或完成真实 1 GB collective", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_5}/large_message_audit.json", f"{G2_F_6}/latency_bandwidth_summary.json"], "G3-C correctness/performance report", "可演示 logical 配置与 evidence", "非真实链路传输"),
        _claim("CLM-003", "72h", "事件驱动 logical 72h，模拟时长 259200 秒、wall-clock 0 秒", "完成真实 72 小时稳定性压测", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_6}/logical_72h_summary.json"], "G3-C reliability report", "可展示事件时间线", "无真实长稳运行"),
        _claim("CLM-004", "100 ms failover", "11 个可恢复模拟场景达到模型化 100 ms 目标", "真实集群 100 ms 内完成故障切换", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_6}/reliability_summary.json"], "G3-C reliability report", "可展示模拟 fault trace", "模型结果，另有 1 个预期无路失败"),
        _claim("CLM-005", "retry rate", "模拟故障场景 retry rate=0.00025，低于模型目标 0.001", "真实 RoCE/HCCL 重传率低于 0.1%", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_6}/reliability_summary.json"], "G3-C reliability report", "可展示并注明统计分母", "非真实协议重传"),
        _claim("CLM-006", "BERT/LLaMA", "提供 BERT/LLaMA communication trace，不执行模型训练且吞吐为空", "完成 BERT/LLaMA 端到端训练验证", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_6}/workload_trace_summary.json"], "G3-C performance report", "仅可展示通信 trace", "real_model_executed=false"),
        _claim("CLM-007", "HCCS/RoCE/PCIe", "基于项目参数来源的相对链路 profile 进行模拟", "测得真实 HCCS/RoCE/PCIe 带宽或利用率", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_6}/parameter_provenance.json"], "G3-C topology report", "可展示参数卡片", "未硬件校准"),
        _claim("CLM-008", "direct API", "官方 ABI/build/link/guard/lifecycle readiness 已静态或 host 验证", "direct HCCL collective 成功或 runtime 已初始化", "ASCEND_HCCL_DIRECT", "E3_HOST_EXECUTED", [G2_F_1, G2_F_2, G2_F_3, G2_F_4], "G3-C direct appendix", "只可展示 readiness 状态", "direct_hccl_api_call=false"),
        _claim("CLM-009", "NPU performance", "当前没有真实 NPU 性能数据", "真实 NPU latency/bandwidth/utilization 已测量", "REAL_DEVICE_NOT_EXECUTED", "E0_NONE", [G2_F_7], "claim boundary section", "显示 HARDWARE_BLOCKED", "measured_on_real_npu=false"),
        _claim("CLM-010", "msprof", "simulator profiling trace 可用，msprof 未执行", "已运行 msprof 或获得真实 profiling", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [f"{G2_F_6}/profiling_summary.json"], "G3-C performance report", "仅展示 simulator trace", "msprof_executed=false"),
        _claim("CLM-011", "zero CPU intervention", "仅为赛题目标/设计方向，当前未验证", "实现或测得零 CPU 介入", "DIRECT_READINESS_ONLY", "E1_DOCUMENTED", ["prompts/algorithm_prompt.txt"], "known limitations", "不得作为成果画面", "无 C/C++ 实现或设备 evidence"),
        _claim("CLM-012", "performance target achievement", "G2-F-6 simulator performance/scale/reliability gates通过；赛题 90% 线性加速目标未验证", "性能目标全部达成", "SIMULATOR_ACCEPTANCE", "E5_SIMULATOR_VALIDATED", [G2_F_6], "G3-C performance report", "可展示分项状态", "缺 compute workload 与真实训练吞吐"),
        _claim("CLM-013", "C/C++ plugin", "CPU_SIM C .so 可构建；direct C++ 为静态 compile-only readiness", "已交付官方 HCCL direct plugin .so", "CPU_SIM_AND_DIRECT_READINESS", "E3_HOST_EXECUTED", [G2_F_2, G2_F_3], "G3-C plugin appendix", "可展示两条轨道对比", "最终插件 ABI/包装层未完成"),
        _claim("CLM-014", "Agent-generated code", "仓库包含 Agent/Skills/Prompt 与代码生成工具，但历史核心代码生成链不可用", "全部核心代码已由 Agent 生成且可完整复现", "AGENT_ENGINEERING", "E2_STATIC_VERIFIED", ["agent/code_generation_skill.py", "prompts/algorithm_prompt.txt"], "G3-D Agent report", "必须显示 HISTORICAL_RECORD_UNAVAILABLE", "缺原始 Prompt、run log、commit mapping 与人工披露"),
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_text(
        path,
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def _repo_path(value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"not a repository-relative path: {value}")
    return ROOT.joinpath(*pure.parts)


def _all_reference_paths(requirements: list[dict[str, Any]]) -> Iterable[str]:
    for item in requirements:
        for key in (
            "implementation_paths", "test_paths", "evidence_paths",
            "documentation_paths", "agent_trace_paths",
        ):
            yield from item[key]


def verify_sha256sums(directory: Path) -> dict[str, Any]:
    manifest = directory / "SHA256SUMS"
    if not manifest.is_file():
        raise ValueError(f"SHA256SUMS missing: {manifest}")
    checked: list[str] = []
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        digest, separator, name = raw.partition("  ")
        if not separator or len(digest) != 64:
            raise ValueError(f"invalid SHA256SUMS line: {raw!r}")
        if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts:
            raise ValueError(f"unsafe SHA256SUMS path: {name}")
        target = directory / name
        if not target.is_file() or _sha256(target) != digest:
            raise ValueError(f"SHA256 mismatch: {target}")
        checked.append(name)
    try:
        display_path = directory.relative_to(ROOT).as_posix()
    except ValueError:
        display_path = directory.as_posix()
    return {
        "path": display_path,
        "verified": True,
        "entry_count": len(checked),
        "sha256sums_sha256": _sha256(manifest),
    }


def verify_old_evidence() -> list[dict[str, Any]]:
    evidence_paths = [G2_E, G2_F_1, G2_F_2, G2_F_3, G2_F_4, G2_F_5, G2_F_6, G2_F_7]
    return [verify_sha256sums(_repo_path(path)) for path in evidence_paths]


def _risk_register(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in requirements:
        if item["status"] == "SATISFIED":
            continue
        result.append({
            "risk_id": f"RISK-{item['requirement_id'][4:]}",
            "requirement_id": item["requirement_id"],
            "risk_level": item["risk_level"],
            "gap_summary": item["gap_summary"],
            "impact": item["impact"],
            "recommended_action": item["recommended_action"],
            "owner_checkpoint": item["owner_checkpoint"],
            "user_action_required": item["user_action_required"],
            "hardware_blocked": item["hardware_blocked"],
        })
    return result


def _roadmap(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "risk_id": risk["risk_id"],
        "requirement_id": risk["requirement_id"],
        "risk_level": risk["risk_level"],
        "owner_checkpoint": risk["owner_checkpoint"],
        "recommended_action": risk["recommended_action"],
        "dependency": "USER_ACTION" if risk["user_action_required"] else (
            "REAL_DEVICE" if risk["hardware_blocked"] else "NONE"
        ),
    } for risk in risks]


def _source_inventory() -> dict[str, Any]:
    tracked = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8"
    ).splitlines()
    ignored_logs = [
        path for path in (
            "logs/runs.jsonl", "logs/prompt_calls.jsonl", "logs/experience.jsonl",
            "logs/knowledge_base.jsonl", "logs/summary.json",
        ) if _repo_path(path).exists()
    ]
    return {
        "schema_version": "g3-a-source-inventory-v1",
        "source_documents": [{
            "path": SOURCE_DOC,
            "category": "INTERNAL_REFERENCE",
            "confidentiality": "INTERNAL_REFERENCE",
            "sha256": _sha256(_repo_path(SOURCE_DOC)),
            "extraction": "OOXML document-order text; no complete source text retained",
            "render_status": "UNAVAILABLE_SOFT_OFFICE_NOT_INSTALLED",
            "page_reference_policy": SOURCE_PAGE,
        }],
        "priority_evidence": [G2_F_7, G2_F_5, G2_F_6, G2_E, G2_F_1, G2_F_2, G2_F_3, G2_F_4],
        "scanned_paths": [
            "hcccl", "agent", "skills", "prompts", "simulator", "config", "tests",
            "tools", "scripts", "docs", "experiments/final_audit/evidence",
            "experiments/direct_api/evidence", "experiments/simulator/evidence",
            "experiments/hccl_vm/evidence",
        ],
        "excluded_paths": [
            ".git", ".venv", "__pycache__", "build", "official HCOMM/HCCL/CANN contents",
            "full Git history", "G2-F-5/G2-F-6 rerun", "real-device runtime paths",
        ],
        "tracked_file_count": len(tracked),
        "project_owned_boundaries": ["hcccl", "agent", "skills", "simulator", "plugin", "tests"],
        "official_or_third_party_boundaries": [
            "/home/workspace/hcomm", "/home/workspace/hccl",
            "/home/workspace/Ascend/cann-9.1.0",
        ],
        "ignored_local_deliverables": [{
            "path": path,
            "submission_status": "NOT_TRACKED_NOT_AUTHORITY",
        } for path in ignored_logs],
        "untracked_log_record_counts": {
            path: sum(1 for line in _repo_path(path).read_text(encoding="utf-8").splitlines() if line.strip())
            for path in ignored_logs if path.endswith(".jsonl")
        },
    }


def build_audit_data() -> dict[str, Any]:
    requirements = build_requirements()
    deliverables = build_deliverables()
    claims = build_claims()
    risks = _risk_register(requirements)
    roadmap = _roadmap(risks)
    return {
        "requirements": requirements,
        "deliverables": deliverables,
        "claims": claims,
        "risks": risks,
        "roadmap": roadmap,
        "source_inventory": _source_inventory(),
    }


def validate_audit_data(data: dict[str, Any], *, require_paths: bool = True) -> None:
    requirements = data["requirements"]
    ids = [item["requirement_id"] for item in requirements]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate requirement ID")
    required_fields = {
        "requirement_id", "source_document", "source_section", "source_page",
        "requirement_summary", "requirement_level", "deliverable_category",
        "acceptance_expectation", "hardware_dependency", "confidentiality",
        "implementation_paths", "test_paths", "evidence_paths", "documentation_paths",
        "agent_trace_paths", "status", "evidence_level", "confidence", "gap_summary",
        "risk_level", "impact", "recommended_action", "owner_checkpoint",
        "user_action_required", "hardware_blocked",
    }
    for item in requirements:
        missing = required_fields - item.keys()
        if missing:
            raise ValueError(f"{item['requirement_id']} missing fields: {sorted(missing)}")
        if item["source_document"] != SOURCE_DOC or not _repo_path(item["source_document"]).is_file():
            raise ValueError(f"invalid source document: {item['requirement_id']}")
        if item["status"] not in STATUSES:
            raise ValueError(f"invalid status: {item['status']}")
        if item["evidence_level"] not in EVIDENCE_LEVELS or item["evidence_level"] == "E6_REAL_DEVICE_MEASURED":
            raise ValueError(f"invalid/currently forbidden evidence level: {item['evidence_level']}")
        if item["risk_level"] not in RISKS or item["owner_checkpoint"] not in OWNERS:
            raise ValueError(f"invalid risk/owner: {item['requirement_id']}")
        if item["confidence"] not in CONFIDENCES or item["deliverable_category"] not in DELIVERABLE_CATEGORIES:
            raise ValueError(f"invalid confidence/category: {item['requirement_id']}")
        if item["status"] != "SATISFIED":
            for field in ("gap_summary", "impact", "recommended_action"):
                if not item[field]:
                    raise ValueError(f"{item['requirement_id']} missing {field}")
        if require_paths:
            for path in _all_reference_paths([item]):
                if not _repo_path(path).exists():
                    raise ValueError(f"fabricated or missing path in {item['requirement_id']}: {path}")
    artifact_ids = [item["artifact_id"] for item in data["deliverables"]]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise ValueError("duplicate artifact ID")
    for item in data["deliverables"]:
        if item["category"] not in DELIVERABLE_CATEGORIES or item["owner_checkpoint"] not in OWNERS:
            raise ValueError(f"invalid deliverable enum: {item['artifact_id']}")
        if item["current_path"] and require_paths and not _repo_path(item["current_path"]).exists():
            raise ValueError(f"missing deliverable path: {item['current_path']}")
    claim_ids = [item["claim_id"] for item in data["claims"]]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("duplicate claim ID")
    for item in data["claims"]:
        if not item["allowed_wording"] or not item["prohibited_wording"]:
            raise ValueError(f"claim wording incomplete: {item['claim_id']}")
        if item["evidence_level"] not in EVIDENCE_LEVELS:
            raise ValueError(f"invalid claim evidence level: {item['claim_id']}")
        for path in item["evidence_paths"]:
            if require_paths and not _repo_path(path).exists():
                raise ValueError(f"missing claim evidence path: {path}")
    for risk in data["risks"]:
        if risk["risk_level"] not in RISKS or risk["owner_checkpoint"] not in OWNERS:
            raise ValueError(f"invalid risk record: {risk['risk_id']}")


def _counts(data: dict[str, Any]) -> dict[str, Any]:
    requirements = data["requirements"]
    return {
        "requirement_count": len(requirements),
        "deliverable_count": len(data["deliverables"]),
        "claim_count": len(data["claims"]),
        "risk_count": len(data["risks"]),
        "status_counts": dict(sorted(Counter(item["status"] for item in requirements).items())),
        "risk_counts": dict(sorted(Counter(item["risk_level"] for item in data["risks"]).items())),
        "evidence_level_counts": dict(sorted(Counter(item["evidence_level"] for item in requirements).items())),
        "owner_checkpoint_distribution": dict(sorted(Counter(item["owner_checkpoint"] for item in data["risks"]).items())),
        "missing_artifact_count": sum(item["current_path"] is None for item in data["deliverables"]),
        "blocker_count": sum(item["risk_level"] == "BLOCKER" for item in data["risks"]),
        "high_count": sum(item["risk_level"] == "HIGH" for item in data["risks"]),
    }


def _cell(value: Any) -> str:
    if isinstance(value, list):
        value = "<br>".join(str(item) for item in value) if value else "—"
    if value is None or value == "":
        value = "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _specialized_conclusions() -> dict[str, Any]:
    return {
        "cpp_plugin_compliance": {
            "status": "PARTIALLY_SATISFIED",
            "final_so": "libhccl_plugin.so is the reproducible current shared object, but it is CPU_SIM and not an official direct HCCL plugin",
            "direct_artifact": "libhccl_direct_adapter.a is STATIC_COMPILE_ONLY; hccl_direct_link_audit is an ELF inspection executable and must not be distributed as the plugin",
            "cmake": "hcccl/CMakeLists.txt",
            "headers": ["hcccl/include/hccl_comm.h", "hcccl/include/hccl_algorithms.h", "hcccl/direct/include/hccl_direct_adapter.h"],
            "core_logic": ["hcccl/src/hccl_comm.c", "hcccl/src/hccl_algorithms.c"],
            "simulator_direct_distinction": "CPU_SIM shared library, direct compile/link/lifecycle readiness, and simulator validation are separate tracks",
            "agent_generation_trace": "HISTORICAL_RECORD_UNAVAILABLE",
            "next_action": "G3-B must define the official plugin ABI/wrapper, final .so, export list, dependency policy, and evaluator build path",
        },
        "agent_reproducibility": {
            "status": "PARTIALLY_SATISFIED",
            "skills": "source and tests present",
            "prompt": "one five-section template exists without explicit version/schema",
            "run_logs": "local ignored records exist but are not tracked authority",
            "generation_trace": "MISSING",
            "commit_mapping": "MISSING",
            "historical_records": "HISTORICAL_RECORD_UNAVAILABLE",
            "independent_entry": "main.py exists; clean-environment reproduction is not verified",
            "next_action": "G3-D must create a truthful new end-to-end trace and disclose unavailable history/human intervention",
        },
        "simulator_deliverability": {
            "status": "PARTIALLY_SATISFIED",
            "config": "present with parameter provenance and sensitivity evidence",
            "workflow": "G2-F-5/G2-F-6 runners exist but are not unified as a submission entry",
            "logs": "frozen raw and summary evidence with SHA256 exists",
            "deterministic_replay": "validated in frozen evidence",
            "correctness": "SATISFIED on SIMULATOR_ACCEPTANCE",
            "performance": "SATISFIED as SIMULATED_ONLY evidence",
            "reliability": "SATISFIED as SIMULATED_ONLY evidence",
            "limitations": "no real-device calibration; old simulator guide is stale",
            "package_readiness": "PARTIAL",
            "next_action": "G3-B adds quick/full reproduce; G3-C updates the simulator manual",
        },
        "performance": {
            "SIMULATOR_EVIDENCE_COMPLETENESS": "SATISFIED",
            "PERFORMANCE_TARGET_ACHIEVEMENT": "PARTIALLY_SATISFIED",
            "REAL_DEVICE_PERFORMANCE": "HARDWARE_BLOCKED",
            "basis": "G2-F-6 covers latency/bandwidth/p50/p95/comparison/scale/sensitivity/bottleneck/profiling/reliability; 90% training speedup, real BERT/LLaMA throughput, msprof, and NPU utilization are not established",
        },
        "package_readiness": {
            "SOURCE_READY": "PARTIALLY_SATISFIED",
            "BUILD_READY": "PARTIALLY_SATISFIED",
            "TEST_READY": "PARTIALLY_SATISFIED",
            "DOCUMENT_READY": "PARTIALLY_SATISFIED",
            "AGENT_READY": "PARTIALLY_SATISFIED",
            "SIMULATOR_READY": "PARTIALLY_SATISFIED",
            "DEMO_READY": "MISSING",
            "RELEASE_READY": "MISSING",
        },
    }


def _user_actions() -> list[dict[str, str]]:
    return [
        {"id": "UA-001", "action": "Confirm whether the controlled competition DOCX may be included in the submission; public release remains excluded by default.", "reason": "CONFIDENTIALITY_REVIEW_REQUIRED"},
        {"id": "UA-002", "action": "Choose the project license and confirm team/copyright ownership.", "reason": "LICENSE_REVIEW_REQUIRED"},
        {"id": "UA-003", "action": "Confirm that official CANN/HCOMM/HCCL source and binaries remain excluded, or provide redistribution authorization.", "reason": "REDISTRIBUTION_REVIEW_REQUIRED"},
        {"id": "UA-004", "action": "Provide any lawful original Prompt/Agent run records and disclose human intervention; missing history must not be reconstructed.", "reason": "HISTORICAL_RECORD_UNAVAILABLE"},
        {"id": "UA-005", "action": "Confirm registration-platform archive format, size limits, required team fields, and final submission inventory.", "reason": "SUBMISSION_PLATFORM_CONFIRMATION"},
        {"id": "UA-006", "action": "Decide whether a public release will be made and which evidence/third-party assets may be public.", "reason": "PUBLIC_RELEASE_DECISION"},
        {"id": "UA-007", "action": "Confirm the competition interpretation of the <=1e-6 threshold for FP16/BF16 final quantized outputs.", "reason": "ACCEPTANCE_INTERPRETATION_REQUIRED"},
    ]


def _audit_summary(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "g3-a-audit-summary-v1",
        "checkpoint": "G3-A",
        "checkpoint_status": "COMPLETED",
        "audit_type": "COMPETITION_DELIVERY_GAP_AUDIT",
        "g2_f_baseline_status": "FROZEN",
        "g3_delivery_readiness": "PARTIAL",
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "counts": _counts(data),
        "specialized_conclusions": _specialized_conclusions(),
        "user_actions": _user_actions(),
        "truthfulness": {
            "old_evidence_modified": False,
            "real_device_api_executed": False,
            "direct_hccl_api_call": False,
            "real_ascend_npu_validated": False,
            "measured_on_real_npu": False,
            "real_device_performance": "HARDWARE_BLOCKED",
        },
        "known_limitations": [
            "The competition DOCX has no usable rendered-page-break metadata; source sections are authoritative and source_page records this limitation.",
            "LibreOffice/soffice was unavailable, so the DOCX was structurally inspected rather than visually rendered.",
            "No G2-F-5/G2-F-6 large experiment, HCCL-VM suite, MPI, msprof, ACL/HCCL runtime, communicator, device buffer, collective, or real device step was executed.",
            "The final G3-A commit cannot be self-referential inside its own evidence; project_commit is the audited main baseline and the enclosing Git commit is reported after commit.",
        ],
    }


def write_docs(data: dict[str, Any], output: Path) -> list[str]:
    validate_audit_data(data)
    output.mkdir(parents=True, exist_ok=True)
    counts = _counts(data)
    requirements = data["requirements"]
    deliverables = data["deliverables"]
    claims = data["claims"]
    risks = data["risks"]
    conclusions = _specialized_conclusions()

    matrix = [
        "# Competition Requirement Matrix",
        "",
        "Controlled competition text is summarized, not reproduced. All paths are repository-relative and existence-checked.",
        "",
        f"- Total requirements: {counts['requirement_count']}",
        "",
        _table(
            ["ID", "Summary", "Level", "Implementation", "Test", "Evidence", "Status", "Evidence level", "Risk", "Owner"],
            ((item["requirement_id"], item["requirement_summary"], item["requirement_level"], item["implementation_paths"], item["test_paths"], item["evidence_paths"], item["status"], item["evidence_level"], item["risk_level"], item["owner_checkpoint"]) for item in requirements),
        ),
        "",
    ]
    _write_text(output / "competition_requirement_matrix.md", "\n".join(matrix))

    inventory = [
        "# Deliverable Inventory", "", f"- Total deliverables: {counts['deliverable_count']}", "",
        _table(
            ["ID", "Artifact", "Category", "Current path", "Expected path", "Build", "Run", "Inclusion", "License/confidentiality", "Missing dependencies", "Owner"],
            ((item["artifact_id"], item["artifact"], item["category"], item["current_path"], item["expected_submission_path"], item["build_status"], item["run_status"], item["inclusion_decision"], f"{item['license_status']} / {item['confidentiality']}", item["missing_dependencies"], item["owner_checkpoint"]) for item in deliverables),
        ), "",
    ]
    _write_text(output / "deliverable_inventory.md", "\n".join(inventory))

    claim_md = [
        "# Claim Boundary Matrix", "", f"- Total claims: {counts['claim_count']}", "",
        _table(
            ["ID", "Claim", "Allowed wording", "Prohibited wording", "Source", "Evidence level", "Report", "Demo", "Limitations"],
            ((item["claim_id"], item["claim"], item["allowed_wording"], item["prohibited_wording"], item["source_backend_or_track"], item["evidence_level"], item["report_location"], item["demo_usage"], item["known_limitations"]) for item in claims),
        ), "",
    ]
    _write_text(output / "claim_boundary_matrix.md", "\n".join(claim_md))

    blockers = [item for item in risks if item["risk_level"] == "BLOCKER"]
    highs = [item for item in risks if item["risk_level"] == "HIGH"]
    lower = [item for item in risks if item["risk_level"] in {"MEDIUM", "LOW", "INFO"}]
    gap_lines = [
        "# G3-A Competition Delivery Gap Report", "",
        "## Executive summary", "",
        "G3-A is complete as an audit. G3 delivery readiness remains PARTIAL and real-device acceptance remains HARDWARE_BLOCKED. Current strength is frozen simulator correctness/performance/scale/reliability evidence; the decisive gaps are the final C/C++ plugin identity, Agent generation provenance, submission packaging, formal reports, demo, and release compliance.", "",
        f"- Requirements: {counts['requirement_count']}",
        f"- Deliverables: {counts['deliverable_count']}",
        f"- Claims: {counts['claim_count']}",
        f"- Risks: {counts['risk_count']}",
        f"- Status counts: `{json.dumps(counts['status_counts'], sort_keys=True)}`",
        f"- Risk counts: `{json.dumps(counts['risk_counts'], sort_keys=True)}`", "",
        "## Satisfied requirements", "",
        _table(["Requirement", "Summary", "Evidence"], ((item["requirement_id"], item["requirement_summary"], item["evidence_level"]) for item in requirements if item["status"] == "SATISFIED")), "",
        "## Blockers", "",
        _table(["Risk", "Requirement", "Gap", "Action", "Owner"], ((item["risk_id"], item["requirement_id"], item["gap_summary"], item["recommended_action"], item["owner_checkpoint"]) for item in blockers)), "",
        "## High risks", "",
        _table(["Risk", "Requirement", "Gap", "Action", "Owner"], ((item["risk_id"], item["requirement_id"], item["gap_summary"], item["recommended_action"], item["owner_checkpoint"]) for item in highs)), "",
        "## Medium/low/informational gaps", "",
        _table(["Risk", "Level", "Requirement", "Gap", "Owner"], ((item["risk_id"], item["risk_level"], item["requirement_id"], item["gap_summary"], item["owner_checkpoint"]) for item in lower)), "",
        "## C/C++ plugin compliance findings", "", f"Status: `{conclusions['cpp_plugin_compliance']['status']}`.", "", conclusions["cpp_plugin_compliance"]["final_so"] + ". " + conclusions["cpp_plugin_compliance"]["direct_artifact"] + ".", "",
        "## Agent/Prompt trace findings", "", f"Status: `{conclusions['agent_reproducibility']['status']}`. Historical core-code generation records are `HISTORICAL_RECORD_UNAVAILABLE`; current ignored logs are not authority and are not copied into this audit.", "",
        "## Simulator deliverability findings", "", f"Status: `{conclusions['simulator_deliverability']['status']}`. Frozen G2-F-5/G2-F-6 evidence is complete and deterministic, but the submission-level runner/manual/package are not complete.", "",
        "## Performance claim findings", "", f"- SIMULATOR_EVIDENCE_COMPLETENESS: `{conclusions['performance']['SIMULATOR_EVIDENCE_COMPLETENESS']}`", f"- PERFORMANCE_TARGET_ACHIEVEMENT: `{conclusions['performance']['PERFORMANCE_TARGET_ACHIEVEMENT']}`", f"- REAL_DEVICE_PERFORMANCE: `{conclusions['performance']['REAL_DEVICE_PERFORMANCE']}`", "",
        "## Confidentiality and license findings", "", "The competition DOCX and official CANN/HCOMM/HCCL assets are excluded from public release by default. LICENSE_REVIEW_REQUIRED, REDISTRIBUTION_REVIEW_REQUIRED, and CONFIDENTIALITY_REVIEW_REQUIRED remain user actions.", "",
        "## Recommended G3-B to G3-G order", "", "1. G3-B: final plugin identity, reproducible build/test, simulator entry, staging manifest.", "2. G3-C: evidence-derived technical reports and current simulator/direct documentation.", "3. G3-D: versioned Skills/Prompt and truthful end-to-end Agent trace.", "4. G3-E: evidence-linked figures and bounded innovation narrative.", "5. G3-F: five-minute demo, script, captions, fallback recording.", "6. G3-G: privacy/license/redistribution review and release-candidate audit.", "", "No G3-B implementation is performed by this checkpoint.", "",
    ]
    _write_text(output / "g3_a_gap_report.md", "\n".join(gap_lines))

    roadmap_lines = [
        "# G3 Priority Roadmap", "", f"- Total risk assignments: {counts['risk_count']}", "",
        _table(["Risk", "Requirement", "Level", "Owner", "Dependency", "Action"], ((item["risk_id"], item["requirement_id"], item["risk_level"], item["owner_checkpoint"], item["dependency"], item["recommended_action"]) for item in data["roadmap"])), "",
        "## User actions", "",
        _table(["ID", "Reason", "Action"], ((item["id"], item["reason"], item["action"]) for item in _user_actions())), "",
    ]
    _write_text(output / "g3_priority_roadmap.md", "\n".join(roadmap_lines))

    json_payloads = {
        "requirement_matrix.json": {"schema_version": "g3-a-requirement-matrix-v1", "requirements": requirements},
        "deliverable_inventory.json": {"schema_version": "g3-a-deliverable-inventory-v1", "deliverables": deliverables},
        "claim_boundary_matrix.json": {"schema_version": "g3-a-claim-boundary-v1", "claims": claims},
        "risk_register.json": {"schema_version": "g3-a-risk-register-v1", "risks": risks},
        "source_inventory.json": data["source_inventory"],
        "roadmap_assignment.json": {"schema_version": "g3-a-roadmap-v1", "assignments": data["roadmap"], "user_actions": _user_actions()},
    }
    for name, payload in json_payloads.items():
        _json(output / name, payload)
    return [
        "docs/submission/competition_requirement_matrix.md",
        "docs/submission/deliverable_inventory.md",
        "docs/submission/claim_boundary_matrix.md",
        "docs/submission/g3_a_gap_report.md",
        "docs/submission/g3_priority_roadmap.md",
        *(f"docs/submission/{name}" for name in json_payloads),
    ]


def _old_evidence_changes() -> list[str]:
    paths = [
        "experiments/hccl_vm/evidence", "experiments/direct_api/evidence",
        "experiments/simulator/evidence", "experiments/final_audit/evidence",
    ]
    output = subprocess.check_output(
        ["git", "diff", "--name-only", "--", *paths],
        cwd=ROOT, text=True, encoding="utf-8",
    )
    return [line for line in output.splitlines() if line.strip()]


def write_evidence(
    data: dict[str, Any],
    evidence_dir: Path,
    native_audit_path: Path,
    focused_tests_passed: int,
    focused_tests_failed: int,
) -> dict[str, Any]:
    validate_audit_data(data)
    if evidence_dir.exists():
        raise ValueError(f"authoritative evidence already exists: {evidence_dir}")
    if focused_tests_passed < 20 or focused_tests_failed != 0:
        raise ValueError("focused test gate did not pass")
    native = json.loads(native_audit_path.read_text(encoding="utf-8"))
    if native.get("status") != "PASS" or native.get("real_device_api_executed") is not False:
        raise ValueError("native static audit did not pass truthfulness gate")
    for repo in ("hcomm", "hccl"):
        state = native.get("official_repositories", {}).get(repo, {})
        if not state.get("tracked_worktree_clean"):
            raise ValueError(f"official {repo} tracked worktree is not clean")
    old_changes = _old_evidence_changes()
    if old_changes:
        raise ValueError(f"old evidence modified: {old_changes}")
    old_evidence = verify_old_evidence()
    docs_output = ROOT / "docs" / "submission"
    generated_documents = write_docs(data, docs_output)
    counts = _counts(data)
    audited_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()
    summary = _audit_summary(data)
    summary.update({
        "baseline_commit": audited_commit,
        "project_commit": audited_commit,
        "project_commit_semantics": "audited main baseline before the enclosing G3-A audit commit",
        "source_documents": [SOURCE_DOC],
        "source_confidentiality": {SOURCE_DOC: "INTERNAL_REFERENCE"},
        "scanned_paths": data["source_inventory"]["scanned_paths"],
        "excluded_paths": data["source_inventory"]["excluded_paths"],
        "generated_documents": generated_documents,
        "focused_tests": {
            "command": "python -m unittest discover -s tests/submission_audit -p test_g3_a_audit.py -v",
            "passed": focused_tests_passed,
            "failed": focused_tests_failed,
            "status": "PASS",
        },
        "old_evidence_validation": old_evidence,
        "old_evidence_modified": False,
        "native_static_audit": "native_plugin_audit.json",
        "official_repositories": native["official_repositories"],
        "evidence_sha256": "See EVIDENCE_SHA256 for SHA256(SHA256SUMS)",
    })
    result = {
        "checkpoint": "G3-A",
        "checkpoint_status": "COMPLETED",
        "audit_type": "COMPETITION_DELIVERY_GAP_AUDIT",
        "g2_f_baseline_status": "FROZEN",
        "competition_requirement_inventory": "COMPLETED",
        "deliverable_inventory": "COMPLETED",
        "claim_boundary_audit": "COMPLETED",
        "gap_and_risk_register": "COMPLETED",
        "g3_delivery_readiness": "PARTIAL",
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "old_evidence_modified": False,
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "measured_on_real_npu": False,
        "counts": counts,
        "specialized_conclusions": summary["specialized_conclusions"],
    }
    regression = {
        "schema_version": "g3-a-regression-v1",
        "focused_tests": summary["focused_tests"],
        "old_evidence_sha256": {"status": "PASS", "verified_directories": len(old_evidence), "details": old_evidence},
        "native_plugin_static_audit": {"status": "PASS", "cpu_sim_ctest_passed": native["cpu_sim"]["ctest_passed"]},
        "markdown_json_consistency": "PASS",
        "truthfulness_guards": {
            "forbidden_real_device_pass_label_absent": True,
            "measured_on_real_npu": False,
            "direct_hccl_api_call": False,
            "real_device_api_executed": False,
        },
    }
    manifest = {
        "schema_version": "g3-a-evidence-v1",
        "checkpoint": "G3-A",
        "project_commit": audited_commit,
        "baseline_commit": audited_commit,
        "audit_type": "COMPETITION_DELIVERY_GAP_AUDIT",
        "source_documents": [SOURCE_DOC],
        "source_confidentiality": "INTERNAL_REFERENCE",
        "generated_artifacts": generated_documents,
        "counts": counts,
    }

    evidence_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = evidence_dir.parent / f".{evidence_dir.name}.tmp"
    if temp_dir.exists():
        raise ValueError(f"temporary evidence directory already exists: {temp_dir}")
    temp_dir.mkdir()
    for name in (
        "requirement_matrix.json", "deliverable_inventory.json", "claim_boundary_matrix.json",
        "risk_register.json", "source_inventory.json", "roadmap_assignment.json",
    ):
        shutil.copyfile(docs_output / name, temp_dir / name)
    _json(temp_dir / "manifest.json", manifest)
    _json(temp_dir / "result.json", result)
    _json(temp_dir / "audit_summary.json", summary)
    _json(temp_dir / "regression.json", regression)
    _json(temp_dir / "native_plugin_audit.json", native)
    readme = """# G3-A Competition Delivery Gap Audit Evidence

This is the single authoritative G3-A evidence set. It summarizes the controlled competition document without reproducing it and maps current source, tests, frozen evidence, deliverables, claims, gaps, risks, and checkpoint owners.

Truthfulness boundary: no ACL/HCCL runtime, device, communicator, collective, MPI, hccl_test, msprof, real NPU, G2-F-5/G2-F-6 large experiment, or logical 72h rerun was executed. Native checks are CPU_SIM build/CTest/ELF queries plus read-only HCOMM/HCCL Git state.

`SHA256SUMS` covers every evidence payload except itself and `EVIDENCE_SHA256`; `EVIDENCE_SHA256` records SHA256(SHA256SUMS).
"""
    _write_text(temp_dir / "README.md", readme)
    checksum_lines = [
        f"{_sha256(path)}  {path.name}"
        for path in sorted(temp_dir.iterdir(), key=lambda item: item.name)
        if path.is_file()
    ]
    _write_text(temp_dir / "SHA256SUMS", "\n".join(checksum_lines) + "\n")
    checksum_digest = _sha256(temp_dir / "SHA256SUMS")
    _write_text(temp_dir / "EVIDENCE_SHA256", checksum_digest + "  SHA256SUMS\n")
    temp_dir.replace(evidence_dir)
    verified = verify_sha256sums(evidence_dir)
    recorded = (evidence_dir / "EVIDENCE_SHA256").read_text(encoding="utf-8").split()[0]
    if recorded != verified["sha256sums_sha256"]:
        raise ValueError("EVIDENCE_SHA256 does not match SHA256SUMS")
    return {"path": evidence_dir.relative_to(ROOT).as_posix(), **verified}


def refresh_evidence_checksums(evidence_dir: Path) -> dict[str, Any]:
    if not evidence_dir.is_dir() or ROOT not in evidence_dir.resolve().parents:
        raise ValueError(f"evidence directory must be inside the repository: {evidence_dir}")
    checksum_lines = [
        f"{_sha256(path)}  {path.name}"
        for path in sorted(evidence_dir.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.name not in {"SHA256SUMS", "EVIDENCE_SHA256"}
    ]
    _write_text(evidence_dir / "SHA256SUMS", "\n".join(checksum_lines) + "\n")
    checksum_digest = _sha256(evidence_dir / "SHA256SUMS")
    _write_text(evidence_dir / "EVIDENCE_SHA256", checksum_digest + "  SHA256SUMS\n")
    verified = verify_sha256sums(evidence_dir)
    if verified["sha256sums_sha256"] != checksum_digest:
        raise ValueError("refreshed evidence SHA256 mismatch")
    return verified


def normalize_lf(target: Path) -> int:
    resolved = target.resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        raise ValueError(f"normalization target must be inside the repository: {target}")
    candidates = [resolved] if resolved.is_file() else [path for path in resolved.rglob("*") if path.is_file()]
    normalized = 0
    for path in candidates:
        if path.suffix.lower() not in {".md", ".json", ".py", ".sh", ".txt"} and path.name not in {"SHA256SUMS", "EVIDENCE_SHA256"}:
            continue
        value = path.read_text(encoding="utf-8")
        _write_text(path, value.replace("\r\n", "\n").replace("\r", "\n"))
        normalized += 1
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-docs", action="store_true")
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--native-audit", type=Path)
    parser.add_argument("--focused-tests-passed", type=int, default=0)
    parser.add_argument("--focused-tests-failed", type=int, default=0)
    parser.add_argument("--refresh-checksums", type=Path)
    parser.add_argument("--normalize-lf", type=Path, action="append", default=[])
    args = parser.parse_args()
    data = build_audit_data()
    validate_audit_data(data)
    result: dict[str, Any] = {"validation": "PASS", "counts": _counts(data)}
    if args.write_docs:
        result["generated_documents"] = write_docs(data, ROOT / "docs" / "submission")
    if args.evidence_dir:
        if not args.native_audit:
            parser.error("--evidence-dir requires --native-audit")
        evidence_dir = args.evidence_dir if args.evidence_dir.is_absolute() else ROOT / args.evidence_dir
        native_audit = args.native_audit if args.native_audit.is_absolute() else ROOT / args.native_audit
        result["evidence"] = write_evidence(
            data, evidence_dir, native_audit,
            args.focused_tests_passed, args.focused_tests_failed,
        )
    if args.refresh_checksums:
        target = args.refresh_checksums if args.refresh_checksums.is_absolute() else ROOT / args.refresh_checksums
        result["checksum_refresh"] = refresh_evidence_checksums(target)
    if args.normalize_lf:
        result["normalized_lf_files"] = sum(
            normalize_lf(target if target.is_absolute() else ROOT / target)
            for target in args.normalize_lf
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
