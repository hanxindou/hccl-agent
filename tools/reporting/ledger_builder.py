"""Build the G3-C metric ledger directly from frozen JSON evidence."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Iterable

from .evidence_reader import G3_B2_ROOT, G3_B3_ROOT, evidence_inventory, read_json, relative, sha256
from .schemas import METRIC_FIELDS


def _unit(field: str, value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if field.endswith("_us") or field in {"p50", "p95"}:
        return "us"
    if field.endswith("_ms"):
        return "ms"
    if "bandwidth" in field:
        return "GB/s_decimal"
    if field.endswith("_bytes") or field in {"wire_bytes", "logical_bytes", "index_bytes", "value_bytes", "metadata_bytes"}:
        return "byte"
    if field.endswith("_percent"):
        return "percent"
    if field.endswith("_ratio") or field in {"weight", "overlap_ratio"}:
        return "ratio"
    if field.endswith("_ticks") or field.endswith("_tick"):
        return "logical_tick"
    if isinstance(value, int):
        return "count"
    if isinstance(value, float):
        return "scalar"
    return "string"


def _display(value: Any, unit: str) -> tuple[str, str]:
    if isinstance(value, bool):
        return ("true" if value else "false", "exact boolean")
    if isinstance(value, int):
        return (str(value), "exact integer")
    if isinstance(value, float):
        if not math.isfinite(value):
            return (str(value), "exact non-finite token")
        places = 2 if unit == "percent" else 3 if unit in {"us", "ms", "GB/s_decimal"} else 4
        suffix = "%" if unit == "percent" else ""
        return (f"{value:.{places}f}{suffix}", f"round half even to {places} decimal places")
    return (str(value), "exact string")


def _safe(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


class Ledger:
    def __init__(self) -> None:
        self.metrics: list[dict[str, Any]] = []
        self.ids: set[str] = set()
        self.documents: dict[Path, Any] = {}

    def document(self, path: Path) -> Any:
        if path not in self.documents:
            self.documents[path] = read_json(path)
        return self.documents[path]

    def add(self, metric_id: str, source: Path, pointer: str, *,
            value: Any | None = None, extraction_method: str = "json_pointer",
            metric_group: str, report_id: str, section_id: str,
            truth_label: str, checkpoint: str, feature_family: str,
            backend: str = "CPU_SIM", track: str = "REPORTING",
            context: dict[str, Any] | None = None, limitations: Iterable[str] = ()) -> None:
        if metric_id in self.ids:
            raise ValueError(f"duplicate metric id: {metric_id}")
        document = self.document(source)
        if value is None:
            from .evidence_reader import resolve_pointer
            selected = resolve_pointer(document, pointer)
            value = len(selected) if extraction_method == "derived:length" else selected
        field = pointer.rsplit("/", 1)[-1] or metric_id.rsplit(".", 1)[-1]
        unit = _unit(field, value)
        display, rounding = _display(value, unit)
        row = {field: None for field in METRIC_FIELDS}
        row.update({
            "metric_id": metric_id, "metric_group": metric_group, "report_id": report_id,
            "section_id": section_id, "value": value, "unit": unit,
            "display_value": display, "rounding_rule": rounding,
            "truth_label": truth_label, "execution_identity": truth_label,
            "checkpoint": checkpoint, "feature_family": feature_family,
            "backend": backend, "track": track, "source_path": relative(source),
            "source_json_pointer": pointer, "source_sha256": sha256(source),
            "source_evidence_root": relative(G3_B2_ROOT if checkpoint == "G3-B2" else G3_B3_ROOT),
            "extraction_method": extraction_method, "limitations": list(limitations),
            "runtime_api_calls": [] if feature_family == "DIRECT" else None,
        })
        if context:
            for key, item in context.items():
                if key in row:
                    row[key] = item
        self.metrics.append(row)
        self.ids.add(metric_id)


def _add_g3_b2(ledger: Ledger) -> None:
    support = G3_B2_ROOT / "algorithm_support_matrix.json"
    for algorithm, primitives in ledger.document(support).items():
        for primitive, status in primitives.items():
            ledger.add(f"g3b2.algorithm.{_safe(algorithm)}.{_safe(primitive)}", support,
                       f"/{algorithm}/{primitive}", metric_group="algorithm_support", report_id="R01",
                       section_id="algorithm-support", truth_label="HISTORICAL_EVIDENCE",
                       checkpoint="G3-B2", feature_family="SCHEDULING",
                       context={"algorithm": algorithm, "primitive": primitive})
    performance = G3_B2_ROOT / "performance_summary.json"
    for name in ("weighted_geomean_improvement_percent", "priority_scenarios_at_least_10_percent",
                 "regressions_over_5_percent", "logical_1024_max_regression_percent"):
        ledger.add(f"g3b2.performance.{name}", performance, f"/{name}", metric_group="g3_b2_performance",
                   report_id="R06", section_id="g3-b2-performance", truth_label="SIMULATED_ONLY",
                   checkpoint="G3-B2", feature_family="SCHEDULING",
                   limitations=("communication simulator result; not real NPU or training performance",))
    outcomes = G3_B2_ROOT / "wins_ties_losses.json"
    for name in ("wins", "ties", "losses"):
        ledger.add(f"g3b2.outcomes.{name}", outcomes, f"/{name}", metric_group="g3_b2_outcomes",
                   report_id="R06", section_id="wins-ties-losses", truth_label="SIMULATED_ONLY",
                   checkpoint="G3-B2", feature_family="SCHEDULING",
                   limitations=("relative to frozen fixed-Ring baseline",))
    ledger.add("g3b2.performance.scenario_count", outcomes, "/scenarios", extraction_method="derived:length",
               metric_group="g3_b2_performance", report_id="R06", section_id="g3-b2-performance",
               truth_label="SIMULATED_ONLY", checkpoint="G3-B2", feature_family="SCHEDULING")
    for index, row in enumerate(ledger.document(outcomes)["scenarios"]):
        sid = row["scenario_id"].lower()
        context = {"algorithm": row["candidate"]["algorithm"], "topology": row["topology"]}
        for pointer_name, field in (("p50", "candidate_p50_us"), ("p95", "candidate_p95_us"),
                                    ("bandwidth", "effective_bandwidth_gb_s"),
                                    ("relative_difference_percent", "improvement_vs_fixed_ring_percent"),
                                    ("baseline/p50_us", "baseline_p50_us"),
                                    ("baseline/p95_us", "baseline_p95_us")):
            ledger.add(f"g3b2.scenario.{sid}.{field}", outcomes, f"/scenarios/{index}/{pointer_name}",
                       metric_group="g3_b2_scenarios", report_id="R06", section_id="scenario-table",
                       truth_label="SIMULATED_ONLY", checkpoint="G3-B2", feature_family="SCHEDULING",
                       context=context, limitations=("simulator-modeled collective metric",))
    scale = G3_B2_ROOT / "scale_summary.json"
    for index, row in enumerate(ledger.document(scale)["scenarios"]):
        sid = row["scenario_id"].lower()
        context = {"algorithm": row["candidate"]["algorithm"], "topology": row["topology"],
                   "rank_size": 1024, "message_size_bytes": row["memory"]["logical_message_bytes"]}
        for field in ("p50", "p95", "bandwidth", "relative_difference_percent"):
            ledger.add(f"g3b2.scale.{sid}.{field}", scale, f"/scenarios/{index}/{field}",
                       metric_group="g3_b2_scale", report_id="R06", section_id="logical-scale",
                       truth_label="SIMULATED_ONLY", checkpoint="G3-B2", feature_family="SCALE",
                       context=context, limitations=("logical ranks; not physical devices",))
    ablation = G3_B2_ROOT / "ablation_summary.json"
    for index, row in enumerate(ledger.document(ablation)["rows"]):
        stage, sid = row["stage"].lower(), row["scenario_id"].lower()
        context = {key: row.get(key) for key in ("primitive", "algorithm", "topology", "rank_size",
                                                  "message_size_bytes", "dtype")}
        for field in ("p50_us", "p95_us", "effective_bandwidth_gb_s", "phase_count"):
            ledger.add(f"g3b2.ablation.{stage}.{sid}.{field}", ablation, f"/rows/{index}/{field}",
                       metric_group="g3_b2_ablation", report_id="R06", section_id="a0-a7",
                       truth_label="SIMULATED_ONLY", checkpoint="G3-B2", feature_family="ABLATION",
                       context=context, limitations=("A7 pipeline overlap is simulator-modeled",))
    correctness = G3_B2_ROOT / "correctness_summary.json"
    ledger.add("g3b2.correctness.all_scenarios_correct", correctness, "/all_scenarios_correct",
               metric_group="correctness", report_id="R04", section_id="dense-correctness",
               truth_label="SIMULATED_ONLY", checkpoint="G3-B2", feature_family="DENSE_CORRECTNESS")
    parity = G3_B2_ROOT / "c_python_parity_audit.json"
    parity_rows = ledger.document(parity)
    ledger.add("g3b2.parity.case_count", parity, "/", value=len(parity_rows), extraction_method="derived:length",
               metric_group="schedule_ir", report_id="R02", section_id="c-python-parity",
               truth_label="CPU_EXECUTED", checkpoint="G3-B2", feature_family="SCHEDULE_IR")
    ledger.add("g3b2.parity.all_canonical_equal", parity, "/", value=all(row["canonical_equal"] for row in parity_rows),
               extraction_method="derived:all_canonical_equal", metric_group="schedule_ir", report_id="R02",
               section_id="c-python-parity", truth_label="CPU_EXECUTED", checkpoint="G3-B2",
               feature_family="SCHEDULE_IR")
    ledger.add("g3b2.parity.representative_schedule_hash", parity, "/0/c_schedule_hash",
               metric_group="schedule_ir", report_id="R02", section_id="c-python-parity",
               truth_label="CPU_EXECUTED", checkpoint="G3-B2", feature_family="SCHEDULE_IR")


def _add_g3_b3(ledger: Ledger) -> None:
    support = G3_B3_ROOT / "sparse_support_matrix.json"
    for name in ("primitives", "dtypes", "reduce_ops"):
        ledger.add(f"g3b3.sparse.supported_{name}_count", support, f"/{name}", extraction_method="derived:length",
                   metric_group="correctness_coverage", report_id="R04", section_id="sparse-coverage",
                   truth_label="LOSSLESS_SPARSE_HOST_EXECUTED", checkpoint="G3-B3", feature_family="SPARSE")
    sparse = G3_B3_ROOT / "sparse_benchmark.json"
    sparse_rows = ledger.document(sparse)["rows"]
    ledger.add("g3b3.sparse.benchmark_correct_case_count", sparse, "/rows",
               value=sum(1 for row in sparse_rows if row["correctness"]),
               extraction_method="derived:true_count:correctness", metric_group="correctness_coverage",
               report_id="R04", section_id="sparse-coverage",
               truth_label="LOSSLESS_SPARSE_HOST_EXECUTED", checkpoint="G3-B3", feature_family="SPARSE")
    for index, row in enumerate(sparse_rows):
        sid = row["scenario_id"].lower()
        context = {
            "primitive": row.get("primitive"), "algorithm": row.get("algorithm"),
            "topology": row.get("topology_variant"), "rank_size": row.get("ranks"),
            "message_size_bytes": row.get("message_size_bytes"), "dtype": row.get("dtype"),
            "reduce_op": row.get("reduce_op"), "sparsity_ratio": row.get("sparsity_ratio"),
            "payload_mode": row.get("selected_mode"), "codec": "SPARSE_INDEX_VALUE",
            "logical_bytes": row.get("logical_bytes"), "dense_wire_bytes": row.get("logical_bytes"),
            "value_bytes": row.get("value_bytes"), "index_bytes": row.get("index_bytes"),
            "metadata_bytes": row.get("metadata_bytes"), "modeled_wire_bytes": row.get("wire_bytes"),
            "compression_ratio": row.get("compression_ratio"),
            "dense_fallback": row.get("selected_mode") == "DENSE", "fallback_reason": row.get("fallback_reason"),
            "encode_cost": row.get("host_encode_decode_p50_us"), "decode_cost": row.get("host_encode_decode_p95_us"),
        }
        fields = ("sparsity_ratio", "compression_ratio", "logical_bytes", "value_bytes", "index_bytes",
                  "metadata_bytes", "wire_bytes", "wire_byte_reduction_ratio", "estimated_dense_total_cost",
                  "estimated_sparse_total_cost", "host_encode_decode_p50_us", "host_encode_decode_p95_us",
                  "correctness", "selected_mode")
        for field in fields:
            ledger.add(f"g3b3.sparse.{sid}.{field}", sparse, f"/rows/{index}/{field}",
                       metric_group="sparse", report_id="R05", section_id="sparse-scenarios",
                       truth_label="LOSSLESS_SPARSE_HOST_EXECUTED", checkpoint="G3-B3", feature_family="SPARSE",
                       context=context, limitations=("modeled wire bytes are not physical NIC bytes",))
    break_even = G3_B3_ROOT / "sparse_break_even.json"
    for index, row in enumerate(ledger.document(break_even)["rows"]):
        key = f"{row['dtype'].lower()}_{row['logical_bytes']}"
        ledger.add(f"g3b3.sparse.break_even.{key}", break_even, f"/rows/{index}/break_even_sparsity_ratio",
                   metric_group="sparse_break_even", report_id="R05", section_id="break-even",
                   truth_label="SIMULATED_ONLY", checkpoint="G3-B3", feature_family="SPARSE",
                   context={"dtype": row["dtype"], "logical_bytes": row["logical_bytes"],
                            "message_size_bytes": row["logical_bytes"], "break_even_status": "MODELED"},
                   limitations=("model break-even; not measured network crossover",))
    fallback = G3_B3_ROOT / "dense_fallback_audit.json"
    ledger.add("g3b3.sparse.dense_fallback_case_count", fallback, "/rows", extraction_method="derived:length",
               metric_group="sparse", report_id="R05", section_id="dense-fallback",
               truth_label="HOST_EXECUTED", checkpoint="G3-B3", feature_family="SPARSE")
    crc = G3_B3_ROOT / "crc_audit.json"
    ledger.add("g3b3.integrity.crc_vector_count", crc, "/known_vectors/vectors", extraction_method="derived:length",
               metric_group="integrity", report_id="R07", section_id="crc32",
               truth_label="HOST_INTEGRITY_VALIDATED", checkpoint="G3-B3", feature_family="INTEGRITY",
               context={"crc_type": "CRC32"}, limitations=("host payload CRC; not NIC/HCCL hardware CRC",))
    ledger.add("g3b3.integrity.crc_c_python_parity", crc, "/c_python_parity/passed",
               metric_group="integrity", report_id="R07", section_id="crc32",
               truth_label="HOST_INTEGRITY_VALIDATED", checkpoint="G3-B3", feature_family="INTEGRITY",
               context={"crc_type": "CRC32"})
    retry = G3_B3_ROOT / "retry_audit.json"
    retry_rows = ledger.document(retry)["cases"]["rows"]
    ledger.add("g3b3.retry.case_count", retry, "/cases/rows", value=len(retry_rows), extraction_method="derived:length",
               metric_group="retry", report_id="R07", section_id="bounded-retry",
               truth_label="HOST_RETRY_VALIDATED", checkpoint="G3-B3", feature_family="RETRY")
    for index, row in enumerate(retry_rows):
        key = f"case_{index + 1}"
        context = {"attempt_count": row.get("attempt_count"), "retransmitted_bytes": row.get("retransmitted_bytes"),
                   "retry_status": row.get("classification"), "terminal_reason": row.get("failure_reason"),
                   "corruption_detected": row.get("corruption_detected"), "sequence_valid": row.get("sequence_valid")}
        for field in ("attempt_count", "retransmitted_bytes", "recovered", "timed_out", "classification", "failure_reason"):
            ledger.add(f"g3b3.retry.{key}.{field}", retry, f"/cases/rows/{index}/{field}",
                       metric_group="retry", report_id="R07", section_id="bounded-retry",
                       truth_label="HOST_RETRY_VALIDATED", checkpoint="G3-B3", feature_family="RETRY",
                       context=context, limitations=("logical retry semantics; not real transport retransmission",))
    timeout = G3_B3_ROOT / "timeout_audit.json"
    for name, pointer in (("recovered_attempt_count", "/recovered/attempt_count"),
                          ("terminal_attempt_count", "/terminal/attempt_count"),
                          ("wall_clock_sleep", "/wall_clock_sleep")):
        ledger.add(f"g3b3.retry.timeout_{name}", timeout, pointer, metric_group="retry", report_id="R07",
                   section_id="logical-timeout", truth_label="HOST_RETRY_VALIDATED", checkpoint="G3-B3",
                   feature_family="RETRY", limitations=("logical ticks; not network wall-clock timeout",))
    flow = G3_B3_ROOT / "flow_control_audit.json"
    for index, row in enumerate(ledger.document(flow)["cases"]):
        key = _safe(row["case"])
        context = {"credit_window": row["config"]["credit_window"],
                   "max_inflight_chunks": row["config"]["max_inflight_chunks"],
                   "peak_inflight_chunks": row["max_inflight_observed"],
                   "blocked_producer_events": row["blocked_producer_events"],
                   "credit_return_events": row["credit_return_events"],
                   "deadlock_detected": not row["no_deadlock"],
                   "memory_budget_bytes": row["config"]["memory_budget_bytes"]}
        for field in ("blocked_producer_events", "credit_return_events", "max_inflight_observed",
                      "peak_materialized_bytes", "ticks", "no_deadlock"):
            ledger.add(f"g3b3.flow.{key}.{field}", flow, f"/cases/{index}/{field}",
                       metric_group="backpressure", report_id="R07", section_id="flow-control",
                       truth_label="SIMULATED_BACKPRESSURE", checkpoint="G3-B3", feature_family="FLOW_CONTROL",
                       context=context, limitations=("simulated credit/backpressure; not NIC/HCCL backpressure",))
    direct = G3_B3_ROOT / "official_api_call_expression_audit.json"
    call_count = len(ledger.document(direct)["calls"])
    ledger.add("g3b3.direct.official_call_expression_count", direct, "/calls", value=call_count,
               extraction_method="derived:length", metric_group="direct", report_id="R10",
               section_id="call-expression-audit", truth_label="DIRECT_COMPILE_LINK_ONLY",
               checkpoint="G3-B3", feature_family="DIRECT", backend="ASCEND_HCCL_DIRECT",
               context={"official_call_expression_count": call_count, "loaded": False, "executed": False,
                        "compile_passed": True, "link_passed": True},
               limitations=("actual source call expressions; runtime never loaded or executed",))
    for field in ("runtime_execution",):
        ledger.add(f"g3b3.direct.{field}", direct, f"/{field}", metric_group="direct", report_id="R10",
                   section_id="runtime-state", truth_label="REAL_DEVICE_NOT_EXECUTED", checkpoint="G3-B3",
                   feature_family="DIRECT", backend="ASCEND_HCCL_DIRECT",
                   context={"loaded": False, "executed": False},
                   limitations=("compile/link/static inspection only",))
    native = G3_B3_ROOT / "native_elf_audit.json"
    for name, pointer in (("exported_symbol_count", "/exported_symbols"), ("artifact_sha256", "/sha256"),
                          ("soname", "/soname"), ("dependency_count", "/needed")):
        method = "derived:length" if name in {"exported_symbol_count", "dependency_count"} else "json_pointer"
        ledger.add(f"g3b3.native.{name}", native, pointer, extraction_method=method,
                   metric_group="native_abi", report_id="R09", section_id="abi-inventory",
                   truth_label="CPU_EXECUTED", checkpoint="G3-B3", feature_family="NATIVE_ABI",
                   limitations=("project CPU_SIM ABI; not official HCCL plugin-loader ABI",))
    regression = G3_B3_ROOT / "submission_regression.json"
    for name, pointer in (("ctest_passed", "/ctest/passed"), ("ctest_failed", "/ctest/failed"),
                          ("python_passed", "/python/passed")):
        ledger.add(f"g3b3.regression.{name}", regression, pointer, metric_group="regression", report_id="R09",
                   section_id="reproducibility", truth_label="HOST_EXECUTED", checkpoint="G3-B3",
                   feature_family="REGRESSION")
    traces = G3_B3_ROOT / "agent_trace_inventory.json"
    for name in ("proposal_records", "evaluation_records", "reflection_records"):
        ledger.add(f"g3b3.agent.{name}", traces, f"/{name}", metric_group="agent", report_id="R01",
                   section_id="agent-loop", truth_label="SIMULATED_ONLY", checkpoint="G3-B3",
                   feature_family="AGENT")
    result = G3_B3_ROOT / "result.json"
    for name in ("int8_quantization", "pairwise"):
        ledger.add(f"g3b3.gates.{name}", result, f"/{name}", metric_group="feature_gates", report_id="R11",
                   section_id="deferred-features", truth_label="HISTORICAL_EVIDENCE", checkpoint="G3-B3",
                   feature_family="FEATURE_GATE")
    reproducible = G3_B3_ROOT / "reproducible_build.json"
    ledger.add("g3b3.native.reproducible_build_status", reproducible, "/status",
               metric_group="native_abi", report_id="R09", section_id="reproducibility",
               truth_label="CPU_EXECUTED", checkpoint="G3-B3", feature_family="NATIVE_ABI")


def build_data_ledger() -> dict[str, Any]:
    ledger = Ledger()
    _add_g3_b2(ledger)
    _add_g3_b3(ledger)
    metrics = sorted(ledger.metrics, key=lambda row: row["metric_id"])
    inventory = evidence_inventory()
    return {
        "schema_version": "g3-c-report-data-ledger-v1",
        "source_commit": inventory["source_commit"],
        "evidence_snapshots": inventory["families"],
        "metric_count": len(metrics),
        "metrics": metrics,
        "numeric_policy": {
            "latency": "us or ms as declared per metric",
            "bandwidth": "decimal GB/s",
            "raw_value_preserved": True,
            "display_value_is_canonical": True,
        },
    }
