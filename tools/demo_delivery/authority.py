"""G3-F-A authority, inventory, and production-contract builder."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .common import DELIVERY_ROOT, ROOT, git_output, read_json, sha256_file, verify_sha256sums, write_json


AUTHORITY_ROOTS = {
    "g3_b2": (
        "experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z",
        "99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483",
    ),
    "g3_b3": (
        "experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z",
        "45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754",
    ),
    "g3_c": (
        "experiments/submission/evidence/g3_c_20260809T000000Z",
        "cc29469e79d9a242aa7eb2859d5ca94357bc2700ad6a6887ffdce1852bf44707",
    ),
    "g3_d": (
        "experiments/submission/evidence/g3_d_20260809T123956Z",
        "1f702c043e6e73bf2f1464a1d40367eb4d8599d5b56b67604acdac69494bb312",
    ),
    "g3_e": (
        "experiments/submission/evidence/g3_e_20260809T155045Z",
        "f57cbe2743042008075098a482264902129539a4a87a83e22b051edb5808cbdf",
    ),
}

TRUTH_IDENTITIES = [
    "HOST_EXECUTED", "CPU_EXECUTED", "SIMULATED_ONLY", "LOSSLESS_SPARSE_HOST_EXECUTED",
    "HOST_INTEGRITY_VALIDATED", "HOST_RETRY_VALIDATED", "SIMULATED_BACKPRESSURE",
    "DIRECT_READINESS_ONLY", "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED",
    "HISTORICAL_EVIDENCE", "OFFLINE_REPLAY", "REPLAYED_FROM_FROZEN_TRACE",
    "RECONSTRUCTED_FROM_FROZEN_EVIDENCE", "AGENT_GENERATED", "DETERMINISTIC_EVALUATION",
    "HUMAN_INTERVENTION", "HISTORICAL_TRACE_UNAVAILABLE", "ONLINE_LLM_OPTIONAL",
    "LIVE_DEMO_CPU_SIM", "DEMO_REPLAY", "PRERECORDED_DETERMINISTIC_OUTPUT",
    "REFERENCE_VIDEO_ONLY",
]

USER_ACTIONS = [
    *(f"UA-B-{index:03d}" for index in range(1, 5)),
    *(f"UA-C-{index:03d}" for index in range(1, 4)),
    *(f"UA-D-{index:03d}" for index in range(1, 4)),
    *(f"UA-E-{index:03d}" for index in range(1, 5)),
    *(f"UA-F-{index:03d}" for index in range(1, 7)),
]


def _candidate(
    step_id: str, purpose: str, command: list[str], truth: str, status: str, timeout: int,
    *, claims: list[str] | None = None, figures: list[str] | None = None,
    traces: list[str] | None = None, writes: list[str] | None = None,
    fallback: str | None = None,
) -> dict[str, Any]:
    return {
        "demo_step_id": step_id,
        "purpose": purpose,
        "command_or_source": command,
        "entry_point": command[:3],
        "expected_runtime": f"bounded by {timeout} seconds; measured in G3-F-E",
        "expected_exit_code": 0,
        "expected_sentinel": None,
        "truth_identity": truth,
        "claim_refs": claims or [],
        "figure_refs": figures or [],
        "trace_refs": traces or [],
        "dependencies": ["Python 3", "repository checkout"],
        "network_required": False,
        "api_key_required": False,
        "hardware_required": False,
        "side_effects": writes or [],
        "timeout": timeout,
        "failure_mode": "non-zero exit; no claim or fallback upgrade",
        "fallback": fallback,
        "priority": "MANDATORY" if status == "REQUIRED" else "SUPPORTING",
        "status": status,
    }


def _candidates() -> list[dict[str, Any]]:
    return [
        _candidate(
            "DEMO-CPU-SIM", "Build and execute the project-owned CPU_SIM functional path",
            ["python", "-m", "tools.submission_cli", "quick"], "LIVE_DEMO_CPU_SIM", "REQUIRED", 300,
            claims=["C-ABI-001"], writes=["build/submission", "dist/submission-install", "dist/submission-results"],
            fallback="FALLBACK-CPU-SIM",
        ),
        _candidate(
            "DEMO-AGENT-REPLAY", "Replay the frozen G3-B2 optimization decision flow offline",
            ["python", "-m", "tools.agent_delivery_cli", "replay", "--trace", "g3-b2-optimization-authoritative-round1"],
            "DEMO_REPLAY", "REQUIRED", 30, traces=["g3-b2-optimization-authoritative-round1"],
            fallback="FALLBACK-AGENT-REPLAY",
        ),
        _candidate(
            "DEMO-VISUAL-VERIFY", "Verify registered G3-E figures without rebuilding benchmark data",
            ["python", "-m", "tools.visualization_cli", "verify-charts"], "HISTORICAL_EVIDENCE", "REQUIRED", 30,
            figures=["FIG-03", "FIG-04", "FIG-12"], fallback="FALLBACK-VISUAL-VERIFY",
        ),
        _candidate(
            "DEMO-AGENT-VERIFY", "Validate Prompt, Skill, trace, and provenance delivery",
            ["python", "-m", "tools.agent_delivery_cli", "verify"], "OFFLINE_REPLAY", "RECOMMENDED", 30,
        ),
        _candidate(
            "DEMO-REPORT-DESCRIBE", "Describe frozen factual reporting authority read-only",
            ["python", "-m", "tools.report_cli", "describe"], "HISTORICAL_EVIDENCE", "RECOMMENDED", 30,
        ),
        _candidate(
            "DEMO-SUBMISSION-DESCRIBE", "Describe CPU_SIM and Direct readiness boundaries",
            ["python", "-m", "tools.submission_cli", "describe"], "DIRECT_READINESS_ONLY", "RECOMMENDED", 30,
            claims=["C-DIRECT-001", "C-DIRECT-002"], figures=["FIG-10"],
        ),
        _candidate(
            "DEMO-SPARSE-RELIABILITY", "Explain host/simulator feature layers using registered figures",
            ["registered-figure", "FIG-06", "FIG-07"], "RECONSTRUCTED_FROM_FROZEN_EVIDENCE", "OPTIONAL", 60,
            figures=["FIG-06", "FIG-07"], claims=["C-SPARSE-001", "C-CRC-001", "C-RETRY-001", "C-BP-001"],
        ),
    ]


def _authority_inventory() -> dict[str, Any]:
    roots: dict[str, Any] = {}
    for name, (relative, expected) in AUTHORITY_ROOTS.items():
        checked = verify_sha256sums(ROOT / relative)
        checked["expected_sha256sums_sha256"] = expected
        roots[name] = checked
    claim_ledger = read_json(ROOT / "docs/submission/report_claim_ledger.json")
    data_ledger = read_json(ROOT / "docs/submission/report_data_ledger.json")
    chart_registry = read_json(ROOT / "docs/submission/visualization/chart_registry.json")
    trace_index = read_json(ROOT / "docs/submission/agent_delivery/trace_index.json")
    return {
        "schema_version": "g3-f-authority-inventory-v1",
        "checkpoint": "G3-F-A",
        "status": "PASS" if all(row["status"] == "PASS" and row["sha256sums_sha256"] == row["expected_sha256sums_sha256"] for row in roots.values()) else "FAIL",
        "merged_main_commit": git_output("rev-parse", "origin/main"),
        "branch_base_commit": git_output("merge-base", "HEAD", "origin/main"),
        "authority_roots": roots,
        "authority_hierarchy": ["L1_SOURCE", "L2_G3_C", "L3_G3_D", "L4_G3_E", "L5_G3_B3", "L6_G3_B2", "L7_G3_A"],
        "claim_count": claim_ledger["claim_count"],
        "metric_count": data_ledger["metric_count"],
        "figure_count": len(chart_registry["figures"]),
        "trace_count": len(trace_index["traces"]),
        "truth_identities": TRUTH_IDENTITIES,
        "user_action_required": USER_ACTIONS,
        "benchmark_rerun": False,
        "network_required": False,
        "real_device_api_executed": False,
        "runtime_api_calls": [],
        "sentinel": "G3_F_DEMO_AUTHORITY_OK",
    }


def build_authority() -> dict[str, Any]:
    inventory = _authority_inventory()
    candidates = {
        "schema_version": "g3-f-demo-candidate-inventory-v1",
        "status": "PASS",
        "candidates": _candidates(),
        "candidate_count": len(_candidates()),
        "mandatory_offline": True,
        "benchmark_rerun": False,
        "runtime_api_calls": [],
    }
    production = {
        "schema_version": "g3-f-video-production-contract-v1",
        "status": "PASS",
        "mandatory_deliverable": "VALIDATED_PRODUCTION_PACKAGE",
        "final_video_binary_status": "USER_ACTION_REQUIRED",
        "profiles": ["QUICK_DEMO", "TECHNICAL_DEMO", "FALLBACK_DEMO"],
        "required_truth_badges": ["SIMULATED_ONLY", "HOST_VALIDATED", "LOGICAL_MODEL_SCALE", "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED", "OFFLINE_REPLAY"],
        "reference_render_identity": "REFERENCE_VIDEO_ONLY",
        "language_status": "USER_ACTION_REQUIRED",
        "voiceover_status": "USER_ACTION_REQUIRED",
        "user_action_required": [f"UA-F-{index:03d}" for index in range(1, 7)],
    }
    environment = {
        "schema_version": "g3-f-recording-environment-contract-v1",
        "status": "PASS",
        "mandatory_environment": {"offline": True, "api_keys": False, "npu": False, "acl_hccl_runtime": False, "mpi": False},
        "media_tooling": {
            "ffmpeg": {"available": shutil.which("ffmpeg") is not None, "installation_attempted": False},
            "ffprobe": {"available": shutil.which("ffprobe") is not None, "installation_attempted": False},
        },
        "tooling_decision": "REFERENCE_RENDER_NOT_AUTHORIZED_WITHOUT_TOOLS_AND_RESOLVED_SPECIFICATIONS",
        "sanitized_prompt_scope": "COMMAND_LOCAL_ONLY",
        "absolute_paths_in_canonical_output": False,
    }
    write_json(DELIVERY_ROOT / "authority_inventory.json", inventory)
    write_json(DELIVERY_ROOT / "demo_candidate_inventory.json", candidates)
    write_json(DELIVERY_ROOT / "video_production_contract.json", production)
    write_json(DELIVERY_ROOT / "recording_environment_contract.json", environment)
    return validate_authority()


def validate_authority() -> dict[str, Any]:
    errors: list[str] = []
    required = [
        "authority_inventory.json", "demo_candidate_inventory.json",
        "video_production_contract.json", "recording_environment_contract.json",
    ]
    for name in required:
        if not (DELIVERY_ROOT / name).is_file():
            errors.append(f"missing artifact: {name}")
    if errors:
        return {"schema_version": "g3-f-authority-validation-v1", "status": "FAIL", "errors": errors, "sentinel": None}
    inventory = read_json(DELIVERY_ROOT / "authority_inventory.json")
    candidates = read_json(DELIVERY_ROOT / "demo_candidate_inventory.json")
    production = read_json(DELIVERY_ROOT / "video_production_contract.json")
    environment = read_json(DELIVERY_ROOT / "recording_environment_contract.json")
    for key, root in inventory.get("authority_roots", {}).items():
        current = verify_sha256sums(ROOT / AUTHORITY_ROOTS[key][0])
        expected = AUTHORITY_ROOTS[key][1]
        if current["status"] != "PASS" or current["sha256sums_sha256"] != expected:
            errors.append(f"authority mismatch: {key}")
    required_candidates = [row for row in candidates.get("candidates", []) if row.get("status") == "REQUIRED"]
    if {row.get("demo_step_id") for row in required_candidates} != {"DEMO-CPU-SIM", "DEMO-AGENT-REPLAY", "DEMO-VISUAL-VERIFY"}:
        errors.append("required candidate set mismatch")
    for row in required_candidates:
        if row.get("network_required") or row.get("api_key_required") or row.get("hardware_required"):
            errors.append(f"mandatory candidate is not offline/keyless/no-NPU: {row.get('demo_step_id')}")
    if production.get("final_video_binary_status") != "USER_ACTION_REQUIRED":
        errors.append("final video binary must remain USER_ACTION_REQUIRED")
    if environment.get("mandatory_environment", {}).get("offline") is not True:
        errors.append("mandatory environment is not offline")
    for path in (DELIVERY_ROOT / name for name in required):
        text = path.read_text(encoding="utf-8")
        if str(ROOT) in text or "C:\\Users\\" in text or "/home/" in text:
            errors.append(f"local absolute path in {path.name}")
    return {
        "schema_version": "g3-f-authority-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "authority_root_count": len(inventory.get("authority_roots", {})),
        "candidate_count": candidates.get("candidate_count", 0),
        "required_candidate_count": len(required_candidates),
        "media_tooling": environment.get("media_tooling"),
        "benchmark_rerun": False,
        "runtime_api_calls": [],
        "sentinel": "G3_F_DEMO_AUTHORITY_OK" if not errors else None,
    }

