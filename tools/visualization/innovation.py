"""Evidence-backed innovation mapping for G3-E-C."""

from __future__ import annotations

from typing import Any

from .authority import TRUTH_IDENTITIES
from .common import CLAIM_LEDGER, DATA_LEDGER, OUTPUT_ROOT, ROOT, git, load_json, sha256_file, write_json, write_text


def _innovation(
    innovation_id: str,
    title: str,
    problem: str,
    mechanism: str,
    sources: list[str],
    agent_role: str,
    validation: str,
    claims: list[str],
    traces: list[str],
    figures: list[str],
    truths: list[str],
    limitations: list[str],
    relevance: str,
) -> dict[str, Any]:
    return {
        "innovation_id": innovation_id,
        "title": title,
        "problem": problem,
        "technical_mechanism": mechanism,
        "implementation_sources": sources,
        "agent_role": agent_role,
        "deterministic_validation": validation,
        "claim_refs": claims,
        "trace_refs": traces,
        "figure_refs": figures,
        "truth_identity": truths,
        "limitations": limitations,
        "competition_relevance": relevance,
        "decision_status": "EVIDENCE_BACKED_INNOVATION_CANDIDATE",
        "provenance": "RECONSTRUCTED_FROM_FROZEN_EVIDENCE",
    }


def innovation_definitions() -> list[dict[str, Any]]:
    return [
        _innovation(
            "INNOV-01", "Topology-aware Schedule IR optimization pipeline",
            "Collective selection must expose auditable topology, chunking, dependency, and cost decisions instead of hiding them inside a monolithic algorithm call.",
            "A shared Schedule IR v2 carries phases and reliability metadata into topology-aware schedule generation, selector scoring, deterministic evaluation, and replanning.",
            ["algorithm/schedule_ir.py", "algorithm/schedule_selector.py", "algorithm/topology_schedules.py", "skills/performance_model.py", "hcccl/src/schedule_ir.c"],
            "The Agent proposes and replans schedules; deterministic gates evaluate them; human governance freezes accepted scope.",
            "Python/C schedule parity, schema and invariant audits, frozen simulator comparison, and offline trace replay.",
            ["C-IR-001", "C-PIPE-001", "C-PERF-001"], ["g3-b2-optimization-authoritative-round1", "g3-b3-feature-completion-agent-flow"], ["FIG-02", "FIG-03", "FIG-11", "FIG-13"],
            ["HOST_EXECUTED", "SIMULATED_ONLY", "AGENT_GENERATED", "DETERMINISTIC_EVALUATION"],
            ["performance results are simulator/model outcomes", "no real-device collective was executed"],
            "Combines explainable Agent assistance with an implementation-facing collective schedule contract and frozen evidence gates.",
        ),
        _innovation(
            "INNOV-02", "Evidence-governed Agent optimization and feature loop",
            "Agent proposals are difficult to trust when proposal, evaluation, human intervention, and evidence provenance are not separable.",
            "Normalized proposal/evaluation/reflection/replanning records map prompts and skills through deterministic gates to sources, commits, evidence, figures, and claim boundaries.",
            ["agent/g3_b2_optimization_loop.py", "agent/g3_b3_feature_loop.py", "tools/agent_delivery/trace.py", "tools/agent_delivery/documentation.py"],
            "The Agent supplies proposals and reflections; deterministic evaluators and explicit human gates control decisions.",
            "Mandatory offline replay verifies hashes, schemas, decision flow, human-intervention fields, and frozen source pointers without API keys.",
            ["C-PERF-001", "C-IR-001", "C-INT8-001", "C-PAIR-001"], ["g3-b2-optimization-authoritative-round1", "g3-b3-feature-completion-agent-flow"], ["FIG-08", "FIG-09"],
            ["AGENT_GENERATED", "DETERMINISTIC_EVALUATION", "HUMAN_INTERVENTION", "OFFLINE_REPLAY", "RECONSTRUCTED_FROM_FROZEN_EVIDENCE"],
            ["normalized traces are not hidden chain-of-thought", "G3-B3 historical Prompt/Response is unavailable"],
            "Makes Agent contribution reproducible and defensible while retaining explicit human governance and negative feature gates.",
        ),
        _innovation(
            "INNOV-03", "Lossless sparse collective path with wire-aware fallback",
            "Sparse communication can add index overhead and lose value unless density, encoding, reconstruction, and dense fallback share one accounting boundary.",
            "A lossless index/value codec, sparse reconstruction, modeled wire-byte accounting, break-even decision, and dense fallback integrate with collective and schedule paths.",
            ["hcccl/src/internal/sparse_codec.c", "hcccl/src/internal/sparse_codec.h", "hcccl/tests/test_sparse_collective.c", "algorithm/schedule_ir.py"],
            "The Agent feature loop proposed sparse delivery and recorded its evidence-gated implementation decision.",
            "Host-executed correctness/parity cases plus frozen logical byte, compression-ratio, and break-even accounting.",
            ["C-SPARSE-001", "C-SPARSE-002", "C-SPARSE-003"], ["g3-b3-feature-completion-agent-flow"], ["FIG-06"],
            ["LOSSLESS_SPARSE_HOST_EXECUTED"],
            ["wire bytes are modeled/logical accounting, not NIC measurement", "sparse path is not real-device validated"],
            "Adds an auditable, lossless communication reduction path while explicitly rejecting unprofitable sparse encodings.",
        ),
        _innovation(
            "INNOV-04", "Layered integrity, retry, and backpressure contract",
            "Reliability claims become misleading when host corruption checks, retry policy, and simulator flow control are blended into one hardware claim.",
            "CRC32 sequence/chunk integrity metadata and retry budgets execute on host paths, while credit/backpressure semantics remain a Schedule IR and simulator layer.",
            ["hcccl/src/internal/integrity_transport.c", "hcccl/src/internal/integrity_transport.h", "hcccl/tests/test_integrity_retry.c", "algorithm/schedule_ir.py"],
            "The feature Agent proposed reliability work; deterministic gates split implemented host semantics from simulator-only backpressure.",
            "C/Python CRC parity, corruption injection/detection, retry recovery/exhaustion cases, and simulated credit-window scenarios.",
            ["C-CRC-001", "C-RETRY-001", "C-BP-001"], ["g3-b3-feature-completion-agent-flow"], ["FIG-07", "FIG-12"],
            ["HOST_INTEGRITY_VALIDATED", "HOST_RETRY_VALIDATED", "SIMULATED_BACKPRESSURE"],
            ["no NIC or HCCL hardware reliability validation", "backpressure is simulated rather than host-runtime executed"],
            "Provides a precise reliability story whose evidence identity remains visible at every layer.",
        ),
        _innovation(
            "INNOV-05", "Layered CPU_SIM ABI and Direct production readiness",
            "A submission plugin needs reproducible CPU validation while retaining a credible path toward official ACL/HCCL integration without pretending hardware execution.",
            "The frozen CPU_SIM plugin preserves SONAME and 19-symbol ABI; a default-OFF Direct adapter expresses official calls and supports compile/link/lifecycle readiness artifacts.",
            ["hcccl/CMakeLists.txt", "hcccl/cmake/hccl_plugin.exports.map", "hcccl/direct/src/hccl_direct_runtime_source.cpp", "hcccl/direct/src/hccl_direct_adapter.cpp"],
            "Agent and report layers describe capability boundaries; no runtime Agent action invokes ACL/HCCL in the mandatory path.",
            "Linux CPU_SIM ABI/CTest/pytest validation plus Direct declaration, expression, compile, link, and lifecycle readiness checks.",
            ["C-ABI-001", "C-DIRECT-001", "C-DIRECT-002"], [], ["FIG-01", "FIG-10", "FIG-12"],
            ["CPU_EXECUTED", "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED"],
            ["Direct artifact is readiness-only", "real-device acceptance remains HARDWARE_BLOCKED"],
            "Balances portable submission verification with an explicit production integration source path and honest hardware boundary.",
        ),
    ]


def build_innovation_map() -> dict[str, Any]:
    chart_registry = load_json(OUTPUT_ROOT / "chart_registry.json")
    figure_metrics = {row["figure_id"]: row["metric_ids"] for row in chart_registry["figures"]}
    rows = innovation_definitions()
    for row in rows:
        row["metric_refs"] = sorted({metric for figure in row["figure_refs"] for metric in figure_metrics.get(figure, [])})
        row["source_records"] = [
            {
                "path": source,
                "sha256": sha256_file(ROOT / source),
                "commit": git("log", "-1", "--format=%H", "--", source),
            }
            for source in row["implementation_sources"]
        ]
    payload = {
        "schema_version": "g3-e-innovation-map-v1",
        "status": "EVIDENCE_BACKED",
        "innovation_count": len(rows),
        "novelty_claim_policy": "No first, unique, industry-leading, production-ready, or hardware-validated claim is asserted.",
        "innovations": rows,
    }
    write_json(OUTPUT_ROOT / "innovation_map.json", payload)
    traceability = {
        "schema_version": "g3-e-innovation-traceability-v1",
        "relationships": [
            {"innovation_id": row["innovation_id"], "claim_refs": row["claim_refs"], "metric_refs": row["metric_refs"], "trace_refs": row["trace_refs"], "figure_refs": row["figure_refs"]}
            for row in rows
        ],
    }
    write_json(OUTPUT_ROOT / "innovation_traceability.json", traceability)
    lines = ["# Evidence-backed Innovation Map", "", "These are competition-facing technical differentiators, not unsupported novelty or production claims.", ""]
    for row in rows:
        lines.extend([
            f"## {row['innovation_id']} — {row['title']}", "",
            f"Problem: {row['problem']}", "", f"Mechanism: {row['technical_mechanism']}", "",
            f"Agent role: {row['agent_role']}", "", f"Validation: {row['deterministic_validation']}", "",
            f"Truth identity: `{', '.join(row['truth_identity'])}`", "",
            f"Claims: `{', '.join(row['claim_refs'])}`; figures: `{', '.join(row['figure_refs'])}`.", "",
            f"Limitations: {'; '.join(row['limitations'])}.", "",
        ])
    write_text(OUTPUT_ROOT / "innovation_map.md", "\n".join(lines))
    return validate_innovation_map()


def validate_innovation_map() -> dict[str, Any]:
    errors: list[str] = []
    payload = load_json(OUTPUT_ROOT / "innovation_map.json")
    chart_registry = load_json(OUTPUT_ROOT / "chart_registry.json")
    claims = {row["claim_id"] for row in load_json(CLAIM_LEDGER)["claims"]}
    metrics = {row["metric_id"] for row in load_json(DATA_LEDGER)["metrics"]}
    traces = {row["trace_id"] for row in load_json(ROOT / "docs/submission/agent_delivery/trace_index.json")["traces"]}
    figures = {row["figure_id"] for row in chart_registry["figures"]}
    ids = [row["innovation_id"] for row in payload.get("innovations", [])]
    if payload.get("innovation_count") != 5 or len(ids) != len(set(ids)):
        errors.append("innovation ID/count mismatch")
    forbidden = ["world-first", "industry-leading", "production-ready", "real npu validated"]
    for row in payload.get("innovations", []):
        if not set(row["claim_refs"]) <= claims:
            errors.append(f"unknown claim: {row['innovation_id']}")
        if not set(row["metric_refs"]) <= metrics:
            errors.append(f"unknown metric: {row['innovation_id']}")
        if not set(row["trace_refs"]) <= traces:
            errors.append(f"unknown trace: {row['innovation_id']}")
        if not set(row["figure_refs"]) <= figures:
            errors.append(f"unknown figure: {row['innovation_id']}")
        if not set(row["truth_identity"]) <= set(TRUTH_IDENTITIES):
            errors.append(f"unknown truth identity: {row['innovation_id']}")
        for source in row["source_records"]:
            path = ROOT / source["path"]
            if not path.is_file() or sha256_file(path) != source["sha256"]:
                errors.append(f"source hash mismatch: {row['innovation_id']} {source['path']}")
            if not source["commit"]:
                errors.append(f"source commit unavailable: {row['innovation_id']} {source['path']}")
        text = " ".join(str(value) for value in row.values()).lower()
        if any(term in text for term in forbidden):
            errors.append(f"forbidden overclaim: {row['innovation_id']}")
    return {
        "schema_version": "g3-e-innovation-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "innovation_count": payload.get("innovation_count"),
        "claim_reference_count": len({claim for row in payload.get("innovations", []) for claim in row["claim_refs"]}),
        "metric_reference_count": len({metric for row in payload.get("innovations", []) for metric in row["metric_refs"]}),
        "trace_reference_count": len({trace for row in payload.get("innovations", []) for trace in row["trace_refs"]}),
        "figure_reference_count": len({figure for row in payload.get("innovations", []) for figure in row["figure_refs"]}),
        "benchmark_rerun": False,
        "runtime_api_calls": [],
        "sentinel": "G3_E_INNOVATION_MAPPING_OK" if not errors else None,
    }
