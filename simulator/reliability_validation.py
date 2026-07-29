"""Deterministic reliability validation flow for CPU_SIM runs."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from simulator.failover_engine import FailoverEngine
from simulator.fault_injector import FaultInjector
from simulator.health_monitor import HealthMonitor
from simulator.retry_policy import RetryPolicy
from topology.graph_builder import TopologyGraphBuilder


class ReliabilityValidationFlow:
    """Run a fixed-seed reliability scenario and produce audit evidence.

    The flow is intentionally CPU_SIM-only. Reported failover time is model
    time derived from hop count and event duration, not real wall-clock time.
    """

    MODEL_STATUS = "CPU_SIMULATED / RELIABILITY_MODEL"

    def __init__(
        self,
        seed: int = 20260729,
        num_nodes: int = 8,
        message_size_mb: float = 64.0,
        max_retry: int = 3,
        payload: bytes | None = None,
    ) -> None:
        self.seed = seed
        self.num_nodes = num_nodes
        self.message_size_mb = message_size_mb
        self.max_retry = max_retry
        self.payload = payload or b"hccl-agent-f1-reference-payload"

    def run(self) -> Dict[str, Any]:
        """Execute the deterministic reliability scenario."""
        wall_start = time.perf_counter()
        graph, metadata = TopologyGraphBuilder.build(
            self.num_nodes, mode="SINGLE_NODE",
        )
        injector = FaultInjector(seed=self.seed)
        monitor = HealthMonitor(seed=self.seed)

        injected_edges = self._select_edges()
        link_event = injector.inject_link_failure(
            graph, *injected_edges[0], duration_ms=40,
        )
        monitor.link_states[self._link_key(*injected_edges[0])] = False
        timeout_event = injector.inject_timeout(
            graph, *injected_edges[1], timeout_ms=15,
        )
        corruption_event = injector.inject_corruption(
            graph, *injected_edges[2],
        )
        congestion_event = injector.inject_congestion(
            graph, *injected_edges[3], duration_ms=25,
            bandwidth_reduction=0.25,
        )

        corrupted_payload = self._corrupt_payload(self.payload)
        reference_crc = FaultInjector.compute_crc32(self.payload)
        candidate_crc = FaultInjector.compute_crc32(corrupted_payload)
        corruption_detected = FaultInjector.detect_corruption(
            self.payload, corrupted_payload,
        )

        health = monitor.evaluate_cluster_health(graph)
        retry_result = self._run_retry_probe()
        failover = FailoverEngine().reroute(
            graph,
            injected_edges[0][0],
            injected_edges[0][1],
            failed_edge=injected_edges[0],
            monitor=monitor,
        )
        transmission = injector.simulate_transmission(
            graph,
            injected_edges[3][0],
            injected_edges[3][1],
            num_packets=128,
            corruption_prob=0.002,
            timeout_prob=0.001,
        )

        events = [
            link_event, timeout_event, corruption_event, congestion_event,
        ]
        retry_count = (
            max(retry_result["attempts"] - 1, 0)
            + injector.retransmit_count
        )
        detection_count = (
            int(not health["healthy"])
            + int(corruption_detected)
            + len([e for e in events if e.fault_type in ("timeout", "congestion")])
        )
        recovered_count = int(failover["found"])
        failed_cases = [] if failover["found"] else ["failover_route_missing"]
        dropped = injector.dropped_packets + transmission.get("packets_lost", 0)

        model_failover_time_ms = self._model_failover_time_ms(
            failover, link_event.duration_ms,
        )
        wall_clock_elapsed_ms = (time.perf_counter() - wall_start) * 1000.0

        return {
            "model_status": self.MODEL_STATUS,
            "seed": self.seed,
            "test_scale": {
                "num_nodes": self.num_nodes,
                "message_size_mb": self.message_size_mb,
                "topology": metadata.get("topology", "Full Mesh"),
            },
            "fault_types": FaultInjector.FAULT_TYPES,
            "event_sequence": [self._event_to_dict(e) for e in events],
            "injection_count": len(events),
            "detection_count": detection_count,
            "retry_count": retry_count,
            "recovered_count": recovered_count,
            "success_count": int(retry_result["success"]) + int(failover["found"]),
            "failure_count": len(failed_cases),
            "dropped_count": dropped,
            "failover": failover,
            "model_failover_time_ms": model_failover_time_ms,
            "wall_clock_elapsed_ms": round(wall_clock_elapsed_ms, 3),
            "wall_clock_note": (
                "wall-clock is observational only; "
                "not a hardware failover SLA"
            ),
            "crc32": {
                "reference": reference_crc,
                "candidate": candidate_crc,
                "corruption_detected": corruption_detected,
                "payload_source": "simulated payload",
            },
            "retry": retry_result,
            "transmission": transmission,
            "failed_cases": failed_cases,
            "summary": injector.get_reliability_report(),
            "limitations": [
                "No real Ascend hardware CRC path is exercised.",
                "Failover time is model time, not measured wall-clock failover.",
                "Retry and packet loss are simulated with fixed-seed CPU logic.",
            ],
        }

    def write_markdown_report(
        self, path: str | Path, result: Dict[str, Any] | None = None,
    ) -> Path:
        """Write a Markdown reliability report and return its path."""
        report = result or self.run()
        output = Path(path)
        output.write_text(
            self.render_markdown(report), encoding="utf-8", newline="\n",
        )
        return output

    @staticmethod
    def render_markdown(report: Dict[str, Any]) -> str:
        """Render a compact Markdown report for audit and competition docs."""
        lines = [
            "# Reliability Simulation Report",
            "",
            "## Model Scope",
            "",
            f"- Status: `{report['model_status']}`",
            "- Interpretation: 模拟器在给定模型和固定 seed 下的统计结果。",
            f"- Seed: `{report['seed']}`",
            f"- Scale: `{report['test_scale']['num_nodes']}` ranks, "
            f"`{report['test_scale']['message_size_mb']}` MB message",
            "",
            "## Fault Summary",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Injection count | {report['injection_count']} |",
            f"| Detection count | {report['detection_count']} |",
            f"| Retry count | {report['retry_count']} |",
            f"| Recovery count | {report['recovered_count']} |",
            f"| Success count | {report['success_count']} |",
            f"| Failure count | {report['failure_count']} |",
            f"| Dropped/lost packets | {report['dropped_count']} |",
            f"| Model failover time ms | {report['model_failover_time_ms']} |",
            f"| Wall-clock elapsed ms | {report['wall_clock_elapsed_ms']} |",
            "",
            f"- Wall-clock note: {report['wall_clock_note']}",
            "",
            "## Fault Types",
            "",
            "- link_down",
            "- timeout",
            "- corruption",
            "- congestion",
            "",
            "## CRC32",
            "",
            f"- Reference CRC32: `{report['crc32']['reference']}`",
            f"- Candidate CRC32: `{report['crc32']['candidate']}`",
            f"- Corruption detected: `{report['crc32']['corruption_detected']}`",
            f"- Payload source: `{report['crc32']['payload_source']}`",
            "",
            "## Event Sequence",
            "",
            "| # | Fault | Link | Model time ms | Duration ms |",
            "| ---: | --- | --- | ---: | ---: |",
        ]
        for index, event in enumerate(report["event_sequence"], start=1):
            lines.append(
                f"| {index} | {event['fault_type']} | {event['link']} | "
                f"{event['model_time_ms']} | {event['duration_ms']} |"
            )

        lines.extend([
            "",
            "## Failover",
            "",
            f"- Triggered: `{report['failover']['failover_triggered']}`",
            f"- Found: `{report['failover']['found']}`",
            f"- Hops: `{report['failover']['hops']}`",
            f"- Route: `{report['failover']['route']}`",
            "",
            "## Failed Cases",
            "",
        ])
        if report["failed_cases"]:
            lines.extend(f"- {case}" for case in report["failed_cases"])
        else:
            lines.append("- None in this fixed-seed CPU_SIM scenario.")

        lines.extend([
            "",
            "## Gap To Real Competition Acceptance",
            "",
        ])
        lines.extend(f"- {item}" for item in report["limitations"])
        lines.append("")
        return "\n".join(lines)

    def _select_edges(self) -> List[Tuple[int, int]]:
        nodes = max(self.num_nodes, 5)
        return [
            (0, 1),
            (1, 2 % nodes),
            (2, 3 % nodes),
            (3, 4 % nodes),
        ]

    @staticmethod
    def _link_key(src: int, dst: int) -> str:
        return f"{src}->{dst}"

    def _corrupt_payload(self, payload: bytes) -> bytes:
        if not payload:
            return b"\x01"
        data = bytearray(payload)
        index = self.seed % len(data)
        data[index] ^= 0x01
        return bytes(data)

    def _run_retry_probe(self) -> Dict[str, Any]:
        attempts = {"count": 0}

        def flaky_operation() -> str:
            attempts["count"] += 1
            if attempts["count"] < self.max_retry:
                raise RuntimeError("simulated timeout")
            return "ok"

        return RetryPolicy(
            max_retry=self.max_retry,
            initial_delay_ms=0,
        ).execute_with_retry(flaky_operation)

    @staticmethod
    def _model_failover_time_ms(
        failover: Dict[str, Any], failed_duration_ms: float,
    ) -> float:
        if not failover["found"]:
            return float(failed_duration_ms)
        return round(failover["hops"] * 0.05 + failed_duration_ms * 0.1, 3)

    @staticmethod
    def _event_to_dict(event: Any) -> Dict[str, Any]:
        return {
            "fault_type": event.fault_type,
            "link": f"{event.link[0]}->{event.link[1]}",
            "model_time_ms": event.model_time_ms,
            "duration_ms": event.duration_ms,
            "description": event.description,
        }
