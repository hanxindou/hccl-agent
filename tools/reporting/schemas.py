"""Schemas and frozen output inventories for the G3-C report suite."""

from __future__ import annotations


REPORT_FILES = (
    "README.md",
    "01_system_architecture_and_algorithm_design.md",
    "02_collective_schedule_ir_and_algorithm_evolution.md",
    "03_topology_and_hardware_model.md",
    "04_dense_and_sparse_correctness_report.md",
    "05_sparse_communication_and_wire_accounting_report.md",
    "06_simulator_performance_and_scale_report.md",
    "07_integrity_retry_and_reliability_report.md",
    "08_simulator_user_manual.md",
    "09_native_plugin_and_abi_appendix.md",
    "10_direct_compile_link_readiness_appendix.md",
    "11_known_limitations_and_future_hardware_plan.md",
    "report_source_index.md",
)

CHART_FILES = (
    "correctness_coverage.json",
    "algorithm_support_matrix.json",
    "schedule_phase_comparison.json",
    "g3_b2_latency_comparison.json",
    "g3_b2_bandwidth_comparison.json",
    "g3_b2_scale.json",
    "g3_b2_ablation.json",
    "sparse_compression_ratio.json",
    "sparse_break_even.json",
    "sparse_wire_bytes.json",
    "sparse_dense_fallback.json",
    "crc_retry_cases.json",
    "reliability_outcomes.json",
    "backpressure_behavior.json",
    "direct_readiness_status.json",
    "claim_boundary_summary.json",
)

TRUTH_LABELS = frozenset({
    "HOST_EXECUTED",
    "CPU_EXECUTED",
    "SIMULATED_ONLY",
    "LOSSLESS_SPARSE_HOST_EXECUTED",
    "HOST_INTEGRITY_VALIDATED",
    "HOST_RETRY_VALIDATED",
    "SIMULATED_BACKPRESSURE",
    "DIRECT_READINESS_ONLY",
    "DIRECT_COMPILE_LINK_ONLY",
    "REAL_DEVICE_NOT_EXECUTED",
    "HISTORICAL_EVIDENCE",
})

PROHIBITED_TRUTH_LABELS = frozenset({
    "REAL_DEVICE_MEASURED",
    "REAL_DEVICE_PASS",
    "DIRECT_RUNTIME_EXECUTED",
    "REAL_HCCL_COLLECTIVE_EXECUTED",
    "REAL_SPARSE_NETWORK_MEASURED",
    "REAL_WIRE_BYTES_MEASURED",
    "REAL_HARDWARE_CRC_VALIDATED",
    "REAL_NIC_RETRY_VALIDATED",
    "REAL_BACKPRESSURE_VALIDATED",
    "REAL_TRAINING_SPEEDUP",
    "NPU_UTILIZATION_MEASURED",
    "MSPROF_EXECUTED",
    "ZERO_CPU_INTERVENTION_VERIFIED",
    "UB_HBM_REUSE_VERIFIED",
})

METRIC_FIELDS = (
    "metric_id", "metric_group", "report_id", "section_id",
    "value", "unit", "display_value", "rounding_rule",
    "truth_label", "execution_identity", "checkpoint", "feature_family",
    "backend", "track", "primitive", "algorithm", "schedule_ir_version",
    "topology", "rank_size", "message_size_bytes", "dtype", "reduce_op",
    "source_path", "source_json_pointer", "source_sha256", "source_evidence_root",
    "extraction_method", "limitations",
    "sparsity_ratio", "payload_mode", "codec", "logical_bytes", "dense_wire_bytes",
    "payload_bytes", "value_bytes", "index_bytes", "metadata_bytes",
    "modeled_wire_bytes", "compression_ratio", "dense_fallback", "fallback_reason",
    "encode_cost", "decode_cost", "break_even_status",
    "crc_type", "corruption_type", "corruption_detected", "sequence_valid",
    "attempt_count", "max_retries", "retransmitted_bytes", "timeout_ticks",
    "retry_status", "terminal_reason", "credit_window", "max_inflight_chunks",
    "peak_inflight_chunks", "blocked_producer_events", "credit_return_events",
    "deadlock_detected", "memory_budget_bytes", "official_call_expression_count",
    "compile_passed", "link_passed", "loaded", "executed", "runtime_api_calls",
)

CLAIM_FIELDS = (
    "claim_id", "report_id", "claim_text", "truth_label", "allowed_wording",
    "prohibited_wording", "evidence_refs", "metric_refs", "limitations",
    "hardware_dependency", "status",
)

REPORT_REQUIRED_HEADINGS = (
    "## Validation Identity",
    "## Claim Boundaries",
    "## Known Limitations",
)

USER_ACTIONS = (
    {"id": "UA-B-001", "subject": "project license/copyright", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-B-002", "subject": "official asset redistribution", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-B-003", "subject": "controlled competition material", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-B-004", "subject": "platform archive and size requirements", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-C-001", "subject": "FP32/FP16/BF16 precision interpretation for <=1e-6", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-C-002", "subject": "final report language", "status": "USER_ACTION_REQUIRED", "default": "Chinese body with English technical terminology"},
    {"id": "UA-C-003", "subject": "final submission template, page, cover, font, anonymity, and PDF rules", "status": "USER_ACTION_REQUIRED"},
)
