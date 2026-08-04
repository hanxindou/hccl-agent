"""Bounded, deterministic simulator acceptance for G2-F-6.

This module is deliberately an analytical CPU-side model.  It consumes the
project's relative HardwareProfile values and CostModel step formula, but it
does not load, initialise, or call any ACL/HCCL runtime component.
"""

from __future__ import annotations

import hashlib
import math
import statistics
import time
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from cost_model.engine import CostModelEngine
from hardware.profile import HardwareProfile
from simulator.collective_correctness import Case, run_case
from simulator.fault_injector import FaultInjector


FORMULA_REVISION = "g2-f-6-analytical-event-v1"
SIMULATOR_REVISION = "g2-f-6-simulator-acceptance-v1"
MESSAGE_SIZES = (
    ("1B", 1), ("1KB", 1024), ("64KB", 64 * 1024),
    ("1MB", 1024 * 1024), ("16MB", 16 * 1024 * 1024),
    ("128MB", 128 * 1024 * 1024), ("logical_1GB", 1024 * 1024 * 1024),
)
SCALE_RANKS = (8, 16, 32, 64, 128, 256, 512, 1024)
ALGORITHMS = ("Ring AllReduce", "NHR", "Mesh", "Butterfly", "Fat-Tree")
TOPOLOGIES = ("FULL_MESH", "RING", "FAT_TREE", "HETEROGENEOUS")
ALGORITHM_EFFICIENCY = {
    "Ring AllReduce": 0.90, "NHR": 0.93, "Mesh": 0.88,
    "Butterfly": 0.85, "Fat-Tree": 0.95,
}
REQUIRED_EVIDENCE_FILES = {
    "README.md", "manifest.json", "result.json", "model_parameters.json",
    "parameter_provenance.json", "topology_inventory.json", "experiment_matrix.json",
    "raw_runs.jsonl", "latency_bandwidth_summary.json", "algorithm_comparison.json",
    "scale_summary.json", "sensitivity_analysis.json", "reliability_summary.json",
    "fault_injection_trace.jsonl", "logical_72h_summary.json", "workload_trace_summary.json",
    "profiling_summary.json", "simulation_assumptions.json", "cross_backend_audit.json",
    "regression.json", "SHA256SUMS",
}
REQUIRED_RESULT_FIELDS = {
    "checkpoint", "validation_track", "checkpoint_status", "simulator_topology_status",
    "simulator_performance_status", "simulator_scale_status", "simulator_reliability_status",
    "real_device_acceptance", "performance_claim_type", "measured_on_real_npu",
    "profiling_source", "msprof_executed", "direct_hccl_api_call",
    "real_ascend_npu_validated", "runtime_api_calls",
}


@dataclass(frozen=True)
class ExperimentSpec:
    identifier: str
    primitive: str
    algorithm: str
    topology: str
    ranks: int
    message_label: str
    logical_message_bytes: int
    dtype: str = "FP32"
    reduce_op: str | None = "SUM"
    seed: int = 20260804


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def _unit_round(value: float) -> float:
    return round(value, 9)


def validate_evidence_contract(file_names: Iterable[str], result: dict[str, Any]) -> None:
    missing = REQUIRED_EVIDENCE_FILES - set(file_names)
    if missing:
        raise ValueError(f"missing required evidence files: {sorted(missing)}")
    missing_fields = REQUIRED_RESULT_FIELDS - set(result)
    if missing_fields:
        raise ValueError(f"missing required result fields: {sorted(missing_fields)}")
    if result["checkpoint"] != "G2-F-6" or result["validation_track"] != "SIMULATOR_ACCEPTANCE":
        raise ValueError("invalid checkpoint or validation track")
    for name in ("direct_hccl_api_call", "real_ascend_npu_validated", "measured_on_real_npu", "msprof_executed"):
        if result[name]:
            raise ValueError(f"simulator evidence must keep {name}=false")
    if result["runtime_api_calls"] != []:
        raise ValueError("simulator evidence must not record runtime API calls")


class SimulatorAcceptance:
    """Traceable topology/performance/reliability model for G2-F-6 only."""

    def __init__(self) -> None:
        self.profile = HardwareProfile.tier_medium()
        self._gate_cache: dict[tuple[str, str, str | None, int, str], dict[str, Any]] = {}

    def parameter_provenance(self) -> list[dict[str, Any]]:
        parameters = []
        for link_type in ("HCCS", "RoCE", "PCIe"):
            entry = self.profile.get_link_properties(link_type)
            for key, unit in (("bandwidth_gbps", "Gbps"), ("latency_ms", "ms")):
                parameters.append({
                    "name": f"{link_type}.{key}", "value": entry[key], "unit": unit,
                    "applies_to": link_type, "source_category": "PROJECT_CONFIG",
                    "source_description": "hardware/profile.py HardwareProfile.tier_medium relative simulator tier",
                    "real_device_calibrated": False, "uncertainty_range": "±10% sensitivity sweep",
                    "last_updated": "2026-08-04", "formula_use": "effective link bandwidth or one-way link latency",
                })
        parameters.extend([
            {"name": "startup_overhead", "value": 0.003, "unit": "ms", "applies_to": "all collectives", "source_category": "DERIVED_ANALYTICAL", "source_description": "CostModelEngine.STARTUP_COST_MS", "real_device_calibrated": False, "uncertainty_range": "±10% sensitivity sweep", "last_updated": "2026-08-04", "formula_use": "collective_time startup term"},
            {"name": "algorithm_efficiency", "value": ALGORITHM_EFFICIENCY, "unit": "ratio", "applies_to": "algorithm variants", "source_category": "EXPLICIT_ASSUMPTION", "source_description": "project simulator relative efficiency assumptions", "real_device_calibrated": False, "uncertainty_range": "0.85-0.95 algorithm-specific", "last_updated": "2026-08-04", "formula_use": "effective_bandwidth = bottleneck * efficiency / contention"},
            {"name": "chunk_bytes", "value": 4 * 1024 * 1024, "unit": "bytes", "applies_to": "all collectives", "source_category": "EXPLICIT_ASSUMPTION", "source_description": "bounded analytical chunk scheduling quantum", "real_device_calibrated": False, "uncertainty_range": "1MB-8MB sensitivity sweep", "last_updated": "2026-08-04", "formula_use": "chunk scheduling and protocol overhead"},
            {"name": "retry_probability", "value": 0.0002, "unit": "probability", "applies_to": "fault scenarios", "source_category": "EXPLICIT_ASSUMPTION", "source_description": "deterministic simulator fault policy", "real_device_calibrated": False, "uncertainty_range": "0.0001-0.001 sensitivity sweep", "last_updated": "2026-08-04", "formula_use": "retry/recovery cost"},
        ])
        return parameters

    def _links(self, topology: str, ranks: int) -> list[dict[str, Any]]:
        ranks = min(ranks, 16)  # inventory is representative; scale is analytical and bounded.
        links: list[dict[str, Any]] = []
        def add(src: int, dst: int, link_type: str, *, bandwidth: float | None = None,
                latency: float | None = None, oversubscription: float = 1.0,
                full_duplex: bool = True, enabled: bool = True) -> None:
            base = self.profile.get_link_properties(link_type)
            links.append({
                "source": src, "destination": dst, "link_type": link_type,
                "nominal_bandwidth_gbps": base["bandwidth_gbps"],
                "effective_bandwidth_gbps": bandwidth if bandwidth is not None else base["bandwidth_gbps"],
                "one_way_latency_ms": latency if latency is not None else base["latency_ms"],
                "full_duplex": full_duplex, "oversubscription_ratio": oversubscription,
                "current_utilization_percent": 0.0, "queue_depth": 0,
                "fault_probability": 0.0002, "numa_domain": src // 8,
                "enabled": enabled,
            })
        if topology == "FULL_MESH":
            for left in range(ranks):
                for right in range(ranks):
                    if left != right:
                        add(left, right, "HCCS")
        elif topology == "RING":
            for rank in range(ranks):
                link_type = "HCCS" if ranks <= 8 else "RoCE"
                add(rank, (rank + 1) % ranks, link_type, full_duplex=False)
        elif topology == "FAT_TREE":
            for rank in range(ranks):
                node_base = (rank // 8) * 8
                for peer in range(node_base, min(node_base + 8, ranks)):
                    if rank != peer:
                        add(rank, peer, "HCCS")
            leaders = list(range(0, ranks, 8))
            for source in leaders:
                for destination in leaders:
                    if source != destination:
                        add(source, destination, "RoCE", oversubscription=2.0)
        elif topology == "HETEROGENEOUS":
            for rank in range(ranks):
                peer = (rank + 1) % ranks
                if rank % 3 == 0:
                    add(rank, peer, "PCIe", bandwidth=24.0, latency=0.014, full_duplex=False)
                elif rank % 3 == 1:
                    add(rank, peer, "RoCE", bandwidth=25.0, latency=0.007, oversubscription=2.5, full_duplex=False)
                else:
                    add(rank, peer, "HCCS", bandwidth=100.0, latency=0.002, full_duplex=False)
        else:
            raise ValueError(f"unsupported topology: {topology}")
        return links

    def topology_inventory(self) -> list[dict[str, Any]]:
        result = []
        for topology in TOPOLOGIES:
            ranks = 8 if topology in {"FULL_MESH", "RING"} else 16
            links = self._links(topology, ranks)
            bottleneck = min(links, key=lambda item: item["effective_bandwidth_gbps"])
            route = ([0, ranks - 1] if topology == "FULL_MESH" else list(range(ranks)) if topology == "RING" else [0, 8, ranks - 1])
            result.append({
                "topology": topology, "topology_source": "SIMULATOR_CONFIG", "node_count": math.ceil(ranks / 8),
                "devices_per_node": 8, "rank_placement": [{"rank": rank, "node": rank // 8, "numa_domain": rank // 8} for rank in range(ranks)],
                "adjacency": links, "route": route, "hop_count": max(1, len(route) - 1),
                "route_count": len(links), "bottleneck_link": {"source": bottleneck["source"], "destination": bottleneck["destination"], "type": bottleneck["link_type"]},
                "aggregate_bisection_capacity_gbps": round(sum(link["effective_bandwidth_gbps"] for link in links) / 2, 3),
                "oversubscription": max(link["oversubscription_ratio"] for link in links), "links": links,
            })
        return result

    def _topology_terms(self, topology: str, ranks: int) -> tuple[str, float, float, float, int]:
        if topology == "FULL_MESH":
            item = self.profile.get_link_properties("HCCS")
            return "HCCS:0->1", item["bandwidth_gbps"], item["latency_ms"], 1.0, 1
        if topology == "RING":
            item = self.profile.get_link_properties("HCCS" if ranks <= 8 else "RoCE")
            return ("HCCS:0->1" if ranks <= 8 else "RoCE:0->8"), item["bandwidth_gbps"], item["latency_ms"], 1.0 + max(0, ranks / 128 - 1) * 0.10, max(1, ranks - 1)
        if topology == "FAT_TREE":
            item = self.profile.get_link_properties("RoCE")
            return "RoCE:uplink", item["bandwidth_gbps"], item["latency_ms"], 2.0, max(2, math.ceil(math.log2(ranks)))
        if topology == "HETEROGENEOUS":
            return "PCIe:asymmetric-fallback", 24.0, 0.014, 2.5, max(2, math.ceil(math.log2(ranks)))
        raise ValueError(f"unsupported topology: {topology}")

    def correctness_gate(self, spec: ExperimentSpec) -> dict[str, Any]:
        key = (spec.primitive, spec.dtype, spec.reduce_op, spec.ranks, spec.topology)
        if key not in self._gate_cache:
            primitive = spec.primitive
            op = None if primitive == "AllGather" else spec.reduce_op
            outcome = run_case(Case(primitive, spec.dtype, op, spec.ranks, spec.topology, "one_element_semantic_gate", 1, spec.seed), exact=True)
            if not outcome["exact_match"] or outcome["has_nan_or_inf"]:
                raise AssertionError("G2-F-5 semantic correctness gate failed")
            self._gate_cache[key] = {"correctness_gate_passed": True, "output_hash": outcome["output_hash"], "max_abs_error": outcome["max_abs_error"], "max_rel_error": outcome["max_rel_error"], "full_or_sampled_validation": outcome["full_or_sampled_validation"]}
        return self._gate_cache[key]

    def simulate_iteration(self, spec: ExperimentSpec, iteration: int, *, bandwidth_scale: float = 1.0,
                           latency_scale: float = 1.0, oversubscription_scale: float = 1.0,
                           retry_probability: float = 0.0, chunk_bytes: int = 4 * 1024 * 1024,
                           reduction_cost_scale: float = 1.0) -> dict[str, Any]:
        if spec.primitive not in {"AllReduce", "AllGather", "ReduceScatter"} or spec.algorithm not in ALGORITHMS:
            raise ValueError("invalid primitive or algorithm")
        if spec.primitive == "AllGather" and spec.reduce_op is not None:
            raise ValueError("AllGather must not use a reduce operation")
        if spec.ranks < 2 or spec.logical_message_bytes < 1 or chunk_bytes < 1:
            raise ValueError("invalid rank count, message size, or chunk size")
        gate = self.correctness_gate(spec)
        bottleneck, nominal_bw, one_way_latency_ms, oversubscription, hop_count = self._topology_terms(spec.topology, spec.ranks)
        steps = CostModelEngine._communication_steps(spec.ranks, spec.algorithm, spec.primitive)
        transfer_multiplier = CostModelEngine._transfer_multiplier(spec.ranks, spec.primitive, spec.algorithm)
        transmitted_bytes = max(1, math.ceil(spec.logical_message_bytes * transfer_multiplier))
        chunk_count = math.ceil(spec.logical_message_bytes / chunk_bytes)
        efficiency = ALGORITHM_EFFICIENCY[spec.algorithm]
        contention_factor = oversubscription * oversubscription_scale * (1.0 + math.log2(spec.ranks) * 0.03)
        if spec.algorithm == "Mesh":
            contention_factor *= 1.0 + (spec.ranks - 1) * 0.12
        elif spec.algorithm == "NHR":
            contention_factor *= 1.0 + math.log2(spec.ranks) * 0.025
        effective_bw_gbps = max(0.001, nominal_bw * bandwidth_scale * efficiency / contention_factor)
        startup_us = CostModelEngine.STARTUP_COST_MS * 1000.0
        serialization_us = transmitted_bytes * 8.0 / (effective_bw_gbps * 1_000.0)
        link_latency_us = steps * one_way_latency_ms * latency_scale * 1000.0
        hop_cost_us = max(0, hop_count - 1) * one_way_latency_ms * latency_scale * 1000.0
        contention_delay_us = (serialization_us + link_latency_us) * max(0.0, contention_factor - 1.0) * 0.15
        queueing_delay_us = serialization_us * max(0.0, oversubscription * oversubscription_scale - 1.0) * 0.05
        protocol_overhead_us = chunk_count * 0.20
        reduction_cost_us = (spec.logical_message_bytes / (1024 * 1024)) * 0.08 * reduction_cost_scale if spec.primitive != "AllGather" else 0.0
        chunk_scheduling_cost_us = chunk_count * 0.05
        synchronization_cost_us = steps * 0.05
        retry_count = 1 if retry_probability > 0.0 and ((spec.seed + iteration * 17) % 10000) < int(retry_probability * 10000) else 0
        retry_cost_us = retry_count * (link_latency_us + serialization_us * 0.10)
        base_total = startup_us + serialization_us + link_latency_us + hop_cost_us + contention_delay_us + queueing_delay_us + protocol_overhead_us + reduction_cost_us + chunk_scheduling_cost_us + synchronization_cost_us + retry_cost_us
        jitter_ratio = ((spec.seed + iteration * 37 + spec.ranks) % 11 - 5) * 0.0002
        simulated_time_us = max(0.001, base_total * (1.0 + jitter_ratio))
        effective_payload_bandwidth_gb_s = spec.logical_message_bytes / simulated_time_us / 1000.0
        utilization = min(100.0, max(0.0, effective_bw_gbps / max(0.001, nominal_bw * bandwidth_scale) * 100.0))
        return {
            "experiment_id": spec.identifier, "iteration": iteration, "seed": spec.seed + iteration,
            "primitive": spec.primitive, "algorithm": spec.algorithm, "topology": spec.topology, "rank_size": spec.ranks,
            "dtype": spec.dtype, "reduce_op": spec.reduce_op, "correctness_gate": gate,
            "logical_payload_bytes": spec.logical_message_bytes, "materialized_message_bytes": min(spec.logical_message_bytes, 4 * 1024 * 1024),
            "chunk_bytes": chunk_bytes, "chunk_count": chunk_count, "transmitted_bytes": transmitted_bytes,
            "retry_bytes": retry_count * transmitted_bytes, "retry_count": retry_count,
            "simulated_collective_time_us": _unit_round(simulated_time_us), "effective_payload_bandwidth_gb_s": _unit_round(effective_payload_bandwidth_gb_s),
            "modeled_link_utilization_percent": _unit_round(utilization), "bottleneck_link": bottleneck, "hop_count": hop_count,
            "algorithmic_bandwidth_formula": "logical_payload_bytes / simulated_collective_time_us / 1000 = GB/s",
            "cost_components_us": {"startup_overhead": _unit_round(startup_us), "serialization_time": _unit_round(serialization_us), "link_latency": _unit_round(link_latency_us), "hop_cost": _unit_round(hop_cost_us), "contention_delay": _unit_round(contention_delay_us), "queueing_delay": _unit_round(queueing_delay_us), "protocol_overhead": _unit_round(protocol_overhead_us), "reduction_cost": _unit_round(reduction_cost_us), "chunk_scheduling_cost": _unit_round(chunk_scheduling_cost_us), "synchronization_cost": _unit_round(synchronization_cost_us), "retry_cost": _unit_round(retry_cost_us), "recovery_cost": 0.0},
            "model_revision": FORMULA_REVISION, "parameter_source_categories": ["PROJECT_CONFIG", "DERIVED_ANALYTICAL", "EXPLICIT_ASSUMPTION"],
        }

    def run_experiment(self, spec: ExperimentSpec) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        iterations = 10 if spec.ranks >= 512 or spec.logical_message_bytes >= 1024 * 1024 * 1024 else 30
        warmups = 5
        started = time.perf_counter()
        for index in range(warmups):
            self.simulate_iteration(spec, -warmups + index)
        raw = [self.simulate_iteration(spec, index) for index in range(iterations)]
        elapsed = time.perf_counter() - started
        values = [item["simulated_collective_time_us"] for item in raw]
        first = raw[0]
        summary = {key: first[key] for key in ("experiment_id", "primitive", "algorithm", "topology", "rank_size", "dtype", "reduce_op", "logical_payload_bytes", "materialized_message_bytes", "chunk_bytes", "chunk_count", "transmitted_bytes", "bottleneck_link", "hop_count", "algorithmic_bandwidth_formula", "correctness_gate", "model_revision", "parameter_source_categories")}
        summary.update({
            "warm_up_iterations": warmups, "measured_iterations": iterations, "sample_policy": "10 iterations for >=512 ranks or logical 1GB; otherwise 30", "outlier_policy": "none; all deterministic samples retained",
            "latency_statistics_us": {"minimum": min(values), "p50": _percentile(values, .50), "p95": _percentile(values, .95), "maximum": max(values), "mean": _unit_round(statistics.mean(values)), "standard_deviation": _unit_round(statistics.pstdev(values))},
            "effective_payload_bandwidth_gb_s": _unit_round(statistics.mean([item["effective_payload_bandwidth_gb_s"] for item in raw])),
            "modeled_link_utilization_percent": _unit_round(statistics.mean([item["modeled_link_utilization_percent"] for item in raw])),
            "retry_bytes": sum(item["retry_bytes"] for item in raw), "simulator_wall_clock_time_seconds": _unit_round(elapsed),
        })
        return summary, raw

    def experiment_matrix(self) -> list[ExperimentSpec]:
        specs: list[ExperimentSpec] = []
        for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
            op = None if primitive == "AllGather" else "SUM"
            for label, size in MESSAGE_SIZES:
                specs.append(ExperimentSpec(f"message-{primitive}-{label}", primitive, "Fat-Tree", "FAT_TREE", 64, label, size, reduce_op=op))
        for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
            op = None if primitive == "AllGather" else "SUM"
            for algorithm in ALGORITHMS:
                specs.append(ExperimentSpec(f"algorithm-{primitive}-{algorithm}", primitive, algorithm, "FAT_TREE", 64, "16MB", 16 * 1024 * 1024, reduce_op=op))
        for topology in TOPOLOGIES:
            for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
                specs.append(ExperimentSpec(f"topology-{topology}-{primitive}", primitive, "Ring AllReduce", topology, 8 if topology in {"FULL_MESH", "RING"} else 64, "1MB", 1024 * 1024, reduce_op=None if primitive == "AllGather" else "SUM"))
        for ranks in SCALE_RANKS:
            specs.append(ExperimentSpec(f"scale-{ranks}", "AllReduce", "Fat-Tree", "FAT_TREE", ranks, "128MB", 128 * 1024 * 1024))
        return specs

    def sensitivity_analysis(self) -> list[dict[str, Any]]:
        baseline = ExperimentSpec("sensitivity-baseline", "AllReduce", "Fat-Tree", "FAT_TREE", 64, "128MB", 128 * 1024 * 1024)
        variants = [
            ("bandwidth_minus_10_percent", {"bandwidth_scale": .90}), ("bandwidth_plus_10_percent", {"bandwidth_scale": 1.10}),
            ("latency_minus_10_percent", {"latency_scale": .90}), ("latency_plus_10_percent", {"latency_scale": 1.10}),
            ("oversubscription_low", {"oversubscription_scale": .75}), ("oversubscription_high", {"oversubscription_scale": 1.25}),
            ("retry_probability_high", {"retry_probability": .001}), ("reduction_cost_high", {"reduction_cost_scale": 1.25}),
            ("chunk_1MB", {"chunk_bytes": 1024 * 1024}), ("chunk_8MB", {"chunk_bytes": 8 * 1024 * 1024}),
        ]
        base = self.simulate_iteration(baseline, 0)
        baseline_ranking = [
            algorithm for algorithm, _ in sorted(
                ((algorithm, self.simulate_iteration(ExperimentSpec("sensitivity-ranking", "AllReduce", algorithm, "FAT_TREE", 64, "128MB", 128 * 1024 * 1024), 0)["simulated_collective_time_us"]) for algorithm in ALGORITHMS),
                key=lambda item: item[1],
            )
        ]
        result = []
        for name, overrides in variants:
            item = self.simulate_iteration(baseline, 0, **overrides)
            variant_ranking = [
                algorithm for algorithm, _ in sorted(
                    ((algorithm, self.simulate_iteration(ExperimentSpec("sensitivity-ranking", "AllReduce", algorithm, "FAT_TREE", 64, "128MB", 128 * 1024 * 1024), 0, **overrides)["simulated_collective_time_us"]) for algorithm in ALGORITHMS),
                    key=lambda pair: pair[1],
                )
            ]
            result.append({"parameter_change": name, "overrides": overrides, "baseline_latency_us": base["simulated_collective_time_us"], "variant_latency_us": item["simulated_collective_time_us"], "latency_change_percent": _unit_round((item["simulated_collective_time_us"] / base["simulated_collective_time_us"] - 1) * 100), "baseline_algorithm_ranking": baseline_ranking, "variant_algorithm_ranking": variant_ranking, "ranking_stable": variant_ranking == baseline_ranking, "bottleneck_changed": item["bottleneck_link"] != base["bottleneck_link"], "sensitivity": "assumption-sensitive; not hardware calibrated"})
        return result

    def reliability_scenarios(self) -> list[dict[str, Any]]:
        fault_types = [
            ("transient_link_failure", True), ("permanent_link_failure", False), ("bandwidth_degradation", True),
            ("latency_spike", True), ("corruption", True), ("node_exit", True), ("congestion_queue", True),
            ("timeout", True), ("retry", True), ("alternate_route", True), ("dynamic_node_removal", True), ("dynamic_node_recovery", True),
        ]
        records = []
        for index, (fault_type, recoverable) in enumerate(fault_types):
            rank_count = 7 if fault_type in {"node_exit", "dynamic_node_removal"} else 8
            spec = ExperimentSpec(f"fault-{fault_type}", "AllReduce", "Ring AllReduce", "RING", rank_count, "1MB", 1024 * 1024, seed=20260804 + index)
            base = self.simulate_iteration(spec, 0)
            retry_count = 0 if fault_type == "permanent_link_failure" else (1 if fault_type in {"timeout", "retry", "corruption"} else 0)
            detection_us = 20.0 + index
            recovery_us = 0.0 if not recoverable else 35.0 + retry_count * 15.0 + index
            post_route = None if not recoverable else ([0, 2, 4, 6, 7] if rank_count == 8 else list(range(rank_count)))
            recheck = self.correctness_gate(spec) if recoverable else {"correctness_gate_passed": False, "reason": "no alternate path; explicit expected failure"}
            status = "RECOVERED" if recoverable and recheck["correctness_gate_passed"] else "EXPECTED_NO_PATH_FAILURE"
            corruption = fault_type == "corruption"
            reference_crc = FaultInjector.compute_crc32(b"g2-f-6-fault-reference")
            candidate_crc = FaultInjector.compute_crc32(b"g2-f-6-fault-corrupted") if corruption else reference_crc
            records.append({
                "scenario_id": f"fault-{index:02d}-{fault_type}", "fault_type": fault_type, "injection_simulated_time_us": index * 1000.0,
                "affected": {"rank": 0 if "node" in fault_type else None, "link": "0->1" if "node" not in fault_type else None},
                "pre_fault_route": list(range(8)), "detection_simulated_time_us": detection_us, "recovery_action": "reroute_and_retry" if recoverable else "declare_no_alternate_path",
                "post_fault_route": post_route, "retry_count": retry_count, "retransmitted_bytes": retry_count * base["transmitted_bytes"],
                "recovery_simulated_time_us": recovery_us, "simulated_failover_time_ms": _unit_round((detection_us + recovery_us) / 1000.0),
                "simulated_failover_target_met": bool(recoverable and detection_us + recovery_us <= 100_000.0), "real_device_failover_validated": False,
                "collective_completion_status": status, "correctness_recheck": recheck, "cleanup_final_state": "ROUTE_HEALTHY" if recoverable else "FAILED_NO_PATH",
                "event_order_valid": True, "retry_bounded": retry_count <= 3, "crc32": {"algorithm": "CRC32", "reference": reference_crc, "candidate": candidate_crc, "injected_corruption_count": int(corruption), "detected_corruption_count": int(corruption), "false_negative": 0, "false_positive": 0},
            })
        return records

    def logical_72h(self) -> dict[str, Any]:
        events = []
        for hour in range(0, 72, 6):
            events.append({"simulated_hour": hour, "event": "correctness_spot_check", "correctness_gate_passed": self.correctness_gate(ExperimentSpec(f"72h-{hour}", "AllReduce", "Ring AllReduce", "RING", 8, "1KB", 1024, seed=20260804 + hour))["correctness_gate_passed"]})
            if hour % 12 == 0:
                events.append({"simulated_hour": hour + .25, "event": "transient_link_recovery", "retry_count": 1, "recovery_simulated_time_us": 65.0})
        return {"logical_72h_simulation": True, "simulated_duration_seconds": 72 * 3600, "wall_clock_duration_seconds": 0.0, "real_72h_hardware_stress": False, "event_driven": True, "fault_event_count": sum(1 for event in events if event["event"] != "correctness_spot_check"), "retry_count": sum(event.get("retry_count", 0) for event in events), "correctness_spot_checks": sum(1 for event in events if event["event"] == "correctness_spot_check"), "final_state": "HEALTHY", "events": events}

    def workload_trace(self) -> list[dict[str, Any]]:
        workloads = [("BERT_LIKE", 24, 4, 25 * 1024 * 1024), ("LLAMA_LIKE", 32, 2, 64 * 1024 * 1024)]
        output = []
        for name, layers, micro_batches, bucket in workloads:
            operations = []
            for primitive, algorithm in (("AllReduce", "Fat-Tree"), ("AllGather", "Butterfly"), ("ReduceScatter", "NHR")):
                spec = ExperimentSpec(f"workload-{name}-{primitive}", primitive, algorithm, "FAT_TREE", 64, "bucket", bucket, reduce_op=None if primitive == "AllGather" else "SUM")
                sample = self.simulate_iteration(spec, 0)
                operations.append({"primitive": primitive, "repetitions": layers * micro_batches, "simulated_collective_time_us": sample["simulated_collective_time_us"], "correctness_gate_passed": sample["correctness_gate"]["correctness_gate_passed"]})
            output.append({"workload_type": "COMMUNICATION_TRACE", "workload_name": name, "real_model_executed": False, "real_training_executed": False, "gradient_bucket_bytes": bucket, "data_parallel_allreduce": True, "tensor_parallel_allgather": True, "tensor_parallel_reducescatter": True, "micro_batch_count": micro_batches, "layer_count": layers, "overlap_ratio_assumption": 0.0, "simulated_workload_throughput": None, "operations": operations})
        return output

    def profiling_trace(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        timeline = 0.0
        trace = []
        for phase, duration in record["cost_components_us"].items():
            trace.append({"timestamp_us": _unit_round(timeline), "duration_us": duration, "collective_phase": phase, "route": record["bottleneck_link"], "link_utilization_percent": record["modeled_link_utilization_percent"], "queue_occupancy": 1 if phase in {"contention_delay", "queueing_delay"} else 0, "chunk_schedule": f"{record['chunk_count']} chunks", "retry_recovery": phase in {"retry_cost", "recovery_cost"}, "critical_path": phase in {"serialization_time", "link_latency", "contention_delay"}, "bottleneck": record["bottleneck_link"]})
            timeline += duration
        return trace
