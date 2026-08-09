"""Build the G3-C claim ledger with explicit truth and wording boundaries."""

from __future__ import annotations

from typing import Any

from .evidence_reader import G3_B2_ROOT, G3_B3_ROOT, relative, source_commit
from .schemas import CLAIM_FIELDS


def _claim(claim_id: str, report_id: str, text: str, truth: str, *,
           allowed: list[str], prohibited: list[str], evidence: list[str], metrics: list[str] = [],
           limitations: list[str] = [], hardware: bool = False) -> dict[str, Any]:
    row = {field: None for field in CLAIM_FIELDS}
    row.update({
        "claim_id": claim_id, "report_id": report_id, "claim_text": text,
        "truth_label": truth, "allowed_wording": allowed, "prohibited_wording": prohibited,
        "evidence_refs": evidence, "metric_refs": metrics, "limitations": limitations,
        "hardware_dependency": hardware, "status": "SUPPORTED",
    })
    return row


def build_claim_ledger(metric_ids: set[str]) -> dict[str, Any]:
    b2, b3 = relative(G3_B2_ROOT), relative(G3_B3_ROOT)
    claims = [
        _claim("C-ARCH-001", "R01", "CPU_SIM is the default project-owned host backend and fallback is NONE.", "HOST_EXECUTED",
               allowed=["default backend=CPU_SIM", "fallback=NONE"], prohibited=["automatic real-device fallback"],
               evidence=[f"{b3}/g3_b3_baseline_reference.json"]),
        _claim("C-ARCH-002", "R01", "SIMULATOR_ACCEPTANCE is a validation track, not a fourth backend.", "HISTORICAL_EVIDENCE",
               allowed=["independent validation track"], prohibited=["fourth backend"], evidence=["tools/submission_cli/core.py"]),
        _claim("C-IR-001", "R02", "Schedule IR v2 extends v1 without rewriting frozen G3-B2 history.", "HOST_EXECUTED",
               allowed=["v1 history remains immutable", "v2 extension"], prohibited=["v2 replaces G3-B2 evidence"],
               evidence=[f"{b3}/schedule_ir_v2_audit.json", "feature_completion/contracts.py"]),
        _claim("C-PERF-001", "R06", "The G3-B2 optimization stack achieved the frozen weighted simulated collective-time improvement relative to fixed Ring.", "SIMULATED_ONLY",
               allowed=["weighted simulated collective-time improvement", "relative to frozen fixed-Ring baseline"],
               prohibited=["real HCCL speedup", "NPU speedup", "training speedup"],
               evidence=[f"{b2}/performance_summary.json"], metrics=["g3b2.performance.weighted_geomean_improvement_percent"],
               limitations=["communication simulator only"]),
        _claim("C-PERF-002", "R06", "The frozen G3-B2 outcome inventory is reported as wins, ties, and losses against fixed Ring.", "SIMULATED_ONLY",
               allowed=["18 wins, 0 ties, 0 losses against fixed Ring"], prohibited=["all real workloads win"],
               evidence=[f"{b2}/wins_ties_losses.json"],
               metrics=["g3b2.outcomes.wins", "g3b2.outcomes.ties", "g3b2.outcomes.losses"]),
        _claim("C-SCALE-001", "R06", "The 1024-rank cases are logical simulator scale.", "SIMULATED_ONLY",
               allowed=["1024 logical ranks"], prohibited=["1024 real devices", "1024-card validation"],
               evidence=[f"{b2}/scale_summary.json"], metrics=["g3b2.scale.p17.p50", "g3b2.scale.p18.p50"],
               limitations=["not a physical cluster"]),
        _claim("C-PIPE-001", "R06", "Pipeline overlap in A7 is simulator-modeled.", "SIMULATED_ONLY",
               allowed=["SIMULATED_PIPELINED_OVERLAP"], prohibited=["hardware stream overlap verified"],
               evidence=[f"{b2}/pipeline_summary.json"]),
        _claim("C-SPARSE-001", "R04", "The sparse index/value codec preserves host-observed collective semantics and reconstruction correctness.", "LOSSLESS_SPARSE_HOST_EXECUTED",
               allowed=["lossless sparse host correctness"], prohibited=["real sparse network speedup"],
               evidence=[f"{b3}/sparse_correctness.json", f"{b3}/sparse_c_python_parity.json"]),
        _claim("C-SPARSE-002", "R05", "Sparse reporting distinguishes logical, value, index, metadata, and modeled wire bytes.", "LOSSLESS_SPARSE_HOST_EXECUTED",
               allowed=["modeled wire bytes", "modeled payload-byte reduction"],
               prohibited=["physically measured NIC bytes", "real wire reduction measured"],
               evidence=[f"{b3}/sparse_benchmark.json"]),
        _claim("C-SPARSE-003", "R05", "Dense fallback is retained when sparse modeled cost is unfavorable.", "HOST_EXECUTED",
               allowed=["dense fallback"], prohibited=["sparse always wins"], evidence=[f"{b3}/dense_fallback_audit.json"],
               metrics=["g3b3.sparse.dense_fallback_case_count"]),
        _claim("C-CRC-001", "R07", "CPU_SIM host payload paths validate CRC32 integrity semantics.", "HOST_INTEGRITY_VALIDATED",
               allowed=["host CRC32 integrity"], prohibited=["hardware CRC", "NIC CRC", "HCCL internal CRC"],
               evidence=[f"{b3}/crc_audit.json"], metrics=["g3b3.integrity.crc_vector_count", "g3b3.integrity.crc_c_python_parity"]),
        _claim("C-RETRY-001", "R07", "Logical timeout and bounded retry semantics are host validated.", "HOST_RETRY_VALIDATED",
               allowed=["logical timeout", "bounded retry"], prohibited=["real HCCL transport retransmission", "real network timeout"],
               evidence=[f"{b3}/retry_audit.json", f"{b3}/timeout_audit.json"], metrics=["g3b3.retry.case_count"]),
        _claim("C-BP-001", "R07", "Credit flow control and backpressure behavior are simulated with bounded inflight state.", "SIMULATED_BACKPRESSURE",
               allowed=["simulated backpressure"], prohibited=["NIC backpressure implemented", "HCCL backpressure measured"],
               evidence=[f"{b3}/flow_control_audit.json", f"{b3}/backpressure_audit.json"]),
        _claim("C-DIRECT-001", "R10", "Official ACL/HCCL API call expressions are present in a compile/link-only source artifact.", "DIRECT_COMPILE_LINK_ONLY",
               allowed=["actual official API call expressions", "compile/link-only production source readiness"],
               prohibited=["runtime executed", "real collective executed"], evidence=[f"{b3}/official_api_call_expression_audit.json"],
               metrics=["g3b3.direct.official_call_expression_count"], hardware=True),
        _claim("C-DIRECT-002", "R10", "The Direct source was not loaded or executed and runtime_api_calls remains empty.", "REAL_DEVICE_NOT_EXECUTED",
               allowed=["loaded=false", "executed=false", "runtime_api_calls=[]", "direct_hccl_api_call=false"],
               prohibited=["DIRECT_RUNTIME_EXECUTED", "REAL_HCCL_COLLECTIVE_EXECUTED"],
               evidence=[f"{b3}/direct_compile_link_audit.json", f"{b3}/result.json"],
               metrics=["g3b3.direct.runtime_execution"], hardware=True),
        _claim("C-ABI-001", "R09", "The 19-symbol library is a project CPU_SIM ABI, not the official HCCL plugin-loader ABI.", "CPU_EXECUTED",
               allowed=["project CPU_SIM ABI"], prohibited=["official plugin ABI verified"],
               evidence=[f"{b3}/native_elf_audit.json"], metrics=["g3b3.native.exported_symbol_count"]),
        _claim("C-INT8-001", "R11", "INT8 quantization is deferred by the precision gate.", "HISTORICAL_EVIDENCE",
               allowed=["DEFERRED_BY_PRECISION_GATE"], prohibited=["INT8 implemented"], evidence=[f"{b3}/result.json"]),
        _claim("C-PAIR-001", "R01", "PairWise is skipped by the value gate and is not in the implemented algorithm matrix.", "HISTORICAL_EVIDENCE",
               allowed=["SKIPPED_BY_VALUE_GATE"], prohibited=["PairWise implemented"], evidence=[f"{b3}/result.json"]),
        _claim("C-TRAIN-001", "R06", "Communication simulator scaling does not verify 90% training linear speedup.", "REAL_DEVICE_NOT_EXECUTED",
               allowed=["TRAINING_LINEAR_SPEEDUP_NOT_VERIFIED=true"], prohibited=["90% training scale achieved"],
               evidence=[f"{b2}/claim_boundary_audit.json"], hardware=True),
        _claim("C-MODEL-001", "R06", "No real BERT or LLaMA model was executed.", "REAL_DEVICE_NOT_EXECUTED",
               allowed=["real_model_executed=false", "training_throughput=null"], prohibited=["real model throughput"],
               evidence=[f"{b2}/result.json"], hardware=True),
        _claim("C-PROFILE-001", "R06", "Profiling evidence is simulator trace only and msprof was not executed.", "SIMULATED_ONLY",
               allowed=["profiling_source=SIMULATOR_TRACE", "msprof_executed=false"], prohibited=["msprof profile"],
               evidence=[f"{b2}/result.json"], hardware=True),
    ]
    for claim in claims:
        missing = sorted(set(claim["metric_refs"]) - metric_ids)
        if missing:
            raise ValueError(f"claim {claim['claim_id']} references missing metrics: {missing}")
    return {
        "schema_version": "g3-c-report-claim-ledger-v1", "source_commit": source_commit(),
        "claim_count": len(claims), "claims": sorted(claims, key=lambda row: row["claim_id"]),
    }
