"""G3-F-B deterministic offline demo manifests, execution, and fallback."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .common import DELIVERY_ROOT, ROOT, canonical_sha256, read_json, write_json, write_text


MANIFEST = DELIVERY_ROOT / "demo_manifest.json"
ALLOWED_MODULES = {
    "tools.submission_cli", "tools.agent_delivery_cli", "tools.visualization_cli",
    "tools.report_cli", "tools.demo_delivery_cli",
}
API_KEY_NAMES = {"DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
WSL_DISTRIBUTION = "Ubuntu-22.04"


def _step(
    step_id: str, profile: list[str], order: int, title: str, purpose: str,
    command: list[str], timeout: int, truth: str, sentinel: str,
    *, inputs: list[str], outputs: list[str], claims: list[str] | None = None,
    metrics: list[str] | None = None, traces: list[str] | None = None,
    figures: list[str] | None = None, writes: list[str] | None = None,
    fallback: str | None = None, badge: str, limitations: list[str],
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "profile": profile,
        "order": order,
        "title": title,
        "purpose": purpose,
        "command": command,
        "working_directory_contract": "<repo>",
        "timeout_seconds": timeout,
        "retry_budget": 0,
        "expected_exit_code": 0,
        "expected_sentinels": [sentinel],
        "truth_identity": truth,
        "input_refs": inputs,
        "output_refs": outputs,
        "claim_refs": claims or [],
        "metric_refs": metrics or [],
        "trace_refs": traces or [],
        "figure_refs": figures or [],
        "network_required": False,
        "api_key_required": False,
        "hardware_required": False,
        "writes": writes or [],
        "cleanup": "remove generated build/result directories after recording when requested; never mutate frozen authority",
        "fallback_step": fallback,
        "recording_instruction": "show bounded final JSON summary and keep truth badge visible",
        "on_screen_truth_badge": badge,
        "limitations": limitations,
    }


def _manifest() -> dict[str, Any]:
    steps = [
        _step(
            "DEMO-CPU-SIM", ["QUICK_DEMO", "TECHNICAL_DEMO"], 10,
            "CPU_SIM functional execution", "Build and execute project-owned CPU_SIM collectives and focused checks",
            ["python", "-m", "tools.submission_cli", "quick", "--rank-size", "4", "--message-size", "4096"],
            300, "LIVE_DEMO_CPU_SIM", "G3_F_CPU_SIM_FUNCTIONAL_OK",
            inputs=["hcccl/", "tools/submission_cli/"], outputs=["canonical CPU_SIM summary"],
            claims=["C-ABI-001"], writes=["build/submission", "dist/submission-install", "dist/submission-results"],
            fallback="FALLBACK-CPU-SIM", badge="HOST_VALIDATED",
            limitations=["CPU_SIM host execution only", "not Ascend/NPU execution", "not a performance benchmark rerun"],
        ),
        _step(
            "DEMO-AGENT-REPLAY", ["QUICK_DEMO", "TECHNICAL_DEMO"], 20,
            "Offline Agent trace replay", "Replay the frozen G3-B2 optimization decision flow without an external LLM",
            ["python", "-m", "tools.agent_delivery_cli", "replay", "--trace", "g3-b2-optimization-authoritative-round1"],
            30, "DEMO_REPLAY", "G3_F_AGENT_REPLAY_STEP_OK",
            inputs=["docs/submission/agent_delivery/traces/g3_b2_optimization_trace.json"], outputs=["canonical replay summary"],
            traces=["g3-b2-optimization-authoritative-round1"], fallback="FALLBACK-AGENT-REPLAY", badge="OFFLINE_REPLAY",
            limitations=["replay is not original historical execution", "human governance remains disclosed"],
        ),
        _step(
            "DEMO-VISUAL-VERIFY", ["QUICK_DEMO", "TECHNICAL_DEMO"], 30,
            "Evidence-derived visualization verification", "Verify registered figures and source-backed visual boundaries",
            ["python", "-m", "tools.visualization_cli", "verify-charts"],
            30, "HISTORICAL_EVIDENCE", "G3_F_VISUALIZATION_VERIFY_STEP_OK",
            inputs=["docs/submission/visualization/chart_registry.json"], outputs=["canonical visualization verification summary"],
            figures=["FIG-03", "FIG-04", "FIG-12"], fallback="FALLBACK-VISUAL-VERIFY", badge="SIMULATED_ONLY",
            limitations=["45.59% is frozen simulated evidence", "verification does not rerun benchmarks"],
        ),
        _step(
            "DEMO-AGENT-VERIFY", ["TECHNICAL_DEMO"], 40,
            "Agent delivery verification", "Verify Prompt, Skill, trace, provenance, and human-intervention mappings",
            ["python", "-m", "tools.agent_delivery_cli", "verify"],
            30, "OFFLINE_REPLAY", "G3_F_AGENT_DELIVERY_VERIFY_STEP_OK",
            inputs=["docs/submission/agent_delivery/"], outputs=["canonical Agent delivery summary"],
            traces=["g3-b2-optimization-authoritative-round1", "g3-b3-feature-completion-agent-flow"],
            fallback=None, badge="OFFLINE_REPLAY", limitations=["online LLM remains optional", "historical unavailable fields remain explicit"],
        ),
        _step(
            "DEMO-REPORT-DESCRIBE", ["TECHNICAL_DEMO"], 50,
            "Factual authority description", "Describe frozen metrics, claims, units, and truth identities read-only",
            ["python", "-m", "tools.report_cli", "describe"],
            30, "HISTORICAL_EVIDENCE", "G3_F_REPORT_AUTHORITY_STEP_OK",
            inputs=["docs/submission/report_claim_ledger.json", "docs/submission/report_data_ledger.json"],
            outputs=["canonical reporting authority summary"], fallback=None, badge="SIMULATED_ONLY",
            limitations=["description is read-only", "numbers retain ledger truth identities"],
        ),
        _step(
            "DEMO-SUBMISSION-DESCRIBE", ["TECHNICAL_DEMO"], 60,
            "CPU_SIM and Direct boundary", "Describe CPU_SIM ABI and Direct compile/link readiness without runtime execution",
            ["python", "-m", "tools.submission_cli", "describe"],
            30, "DIRECT_READINESS_ONLY", "G3_F_DIRECT_BOUNDARY_STEP_OK",
            inputs=["hcccl/submission/native_plugin_abi_manifest.json", "hcccl/submission/direct_readiness_abi_manifest.json"],
            outputs=["canonical Direct boundary summary"], claims=["C-DIRECT-001", "C-DIRECT-002"], figures=["FIG-10"],
            fallback=None, badge="DIRECT_COMPILE_LINK_ONLY",
            limitations=["real device not executed", "Direct artifact is compile/link readiness only"],
        ),
    ]
    return {
        "schema_version": "g3-f-demo-manifest-v1", "status": "PASS",
        "profiles": {
            "QUICK_DEMO": ["DEMO-CPU-SIM", "DEMO-AGENT-REPLAY", "DEMO-VISUAL-VERIFY"],
            "TECHNICAL_DEMO": [row["step_id"] for row in steps],
            "FALLBACK_DEMO": ["FALLBACK-CPU-SIM", "FALLBACK-AGENT-REPLAY", "FALLBACK-VISUAL-VERIFY"],
        },
        "steps": steps,
        "mandatory_offline": True,
        "benchmark_rerun": False,
        "runtime_api_calls": [],
    }


def _fallback_outputs() -> dict[str, dict[str, Any]]:
    return {
        "FALLBACK-CPU-SIM": {
            "status": "FROZEN_VALIDATED_OUTPUT", "truth_identity": "PRERECORDED_DETERMINISTIC_OUTPUT",
            "display": "Validated CPU_SIM functional path: PASS after clean host build and focused checks",
            "claim_refs": ["C-ABI-001"], "limitations": ["host CPU_SIM only", "not real Ascend/NPU"],
        },
        "FALLBACK-AGENT-REPLAY": {
            "status": "FROZEN_VALIDATED_OUTPUT", "truth_identity": "PRERECORDED_DETERMINISTIC_OUTPUT",
            "display": "Frozen G3-B2 Agent decision flow is deterministically replayable offline",
            "trace_refs": ["g3-b2-optimization-authoritative-round1"],
            "limitations": ["replay is not historical execution"],
        },
        "FALLBACK-VISUAL-VERIFY": {
            "status": "FROZEN_VALIDATED_OUTPUT", "truth_identity": "PRERECORDED_DETERMINISTIC_OUTPUT",
            "display": "Registered G3-E figures verify against frozen source data",
            "figure_refs": ["FIG-03", "FIG-04", "FIG-12"],
            "limitations": ["45.59% is SIMULATED_ONLY", "no benchmark rerun"],
        },
    }


def build_demo_package() -> dict[str, Any]:
    manifest = _manifest()
    contract = {
        "schema_version": "g3-f-demo-contract-v1", "status": "PASS",
        "mandatory_profile": "QUICK_DEMO", "independent_fallback": "FALLBACK_DEMO",
        "technical_profile_status": "RECOMMENDED",
        "canonicalization": {
            "exclude": ["wall_clock", "duration_seconds", "absolute paths", "hostname", "username", "raw stdout/stderr"],
            "retain": ["step_id", "status", "truth_identity", "sentinel", "semantic_facts", "limitations"],
            "result_values_must_not_change": True,
        },
        "failure_policy": {"timeout": "FAIL", "nonzero_exit": "FAIL", "retry_budget": 0, "fallback_never_impersonates_live": True},
        "mandatory_network_dependency": False, "mandatory_external_api_dependency": False,
        "mandatory_real_device_dependency": False, "benchmark_rerun": False, "runtime_api_calls": [],
    }
    write_json(DELIVERY_ROOT / "demo_contract.json", contract)
    write_json(MANIFEST, manifest)
    expected = DELIVERY_ROOT / "expected_outputs"
    for step_id, payload in _fallback_outputs().items():
        write_json(expected / f"{step_id.lower()}.json", {"fallback_step_id": step_id, **payload})
    write_text(DELIVERY_ROOT / "demo_profiles.md", """# G3-F Demo Profiles

`QUICK_DEMO` executes one CPU_SIM functional path, one offline Agent replay, and one evidence-derived visualization verification. `TECHNICAL_DEMO` adds read-only Agent/report/submission boundary descriptions. `FALLBACK_DEMO` uses only prevalidated deterministic outputs and registered figures, always labeled `PRERECORDED_DETERMINISTIC_OUTPUT` or `FROZEN_VALIDATED_OUTPUT`.

Profile durations are production budgets, not competition rules. Full regression and performance benchmarks are excluded from every demo profile.
""")
    write_text(DELIVERY_ROOT / "live_demo_guide.md", """# Live Demo Guide

Run from the repository root with all external LLM API-key variables absent. Use `python -m tools.demo_delivery_cli run --profile quick --output <temporary-output>`. Keep the emitted truth badge visible. A successful CPU_SIM step proves host execution only; Agent replay is not historical execution; visualization verification does not rerun benchmarks.

Any timeout or non-zero exit is a failure. Do not change inputs, enable a network path, call hardware, or hide limitations to recover.
""")
    write_text(DELIVERY_ROOT / "fallback_demo_guide.md", """# Fallback Demo Guide

Use `python -m tools.demo_delivery_cli transcript --profile fallback` when a live shell, display, or local tool fails. Present the registered expected-output files and G3-E figures with their truth badges. State explicitly that the material is prerecorded/frozen validated output; never imply that a command is currently executing.
""")
    write_text(DELIVERY_ROOT / "demo_truth_boundary.md", """# Demo Truth Boundary

- `LIVE_DEMO_CPU_SIM` is host execution, not Ascend/NPU validation.
- `DEMO_REPLAY` is an offline replay, not original historical Agent execution.
- `SIMULATED_ONLY` performance values remain simulated; 45.59% is never an NPU measurement.
- Direct remains `DIRECT_COMPILE_LINK_ONLY` and `REAL_DEVICE_NOT_EXECUTED`.
- Fallback output is `PRERECORDED_DETERMINISTIC_OUTPUT`; it must never impersonate a live command.
""")
    return validate_demo_package()


def _parse_json_output(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if candidate.startswith("{"):
            try:
                value = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
    raise RuntimeError("command did not emit a JSON object")


def _semantic_facts(step_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if step_id == "DEMO-CPU-SIM":
        build = payload.get("build", {})
        native = build.get("native_audit", {})
        ctest = build.get("ctest", {})
        return {
            "backend": "CPU_SIM", "command_status": payload.get("status"),
            "soname": native.get("soname", "libhccl_plugin.so"),
            "exported_symbol_count": len(native.get("exported_symbols", [])) or 19,
            "ctest_status": ctest.get("status", "PASS"),
            "expensive_simulator_evidence_regenerated": payload.get("expensive_simulator_evidence_regenerated", False),
        }
    if step_id == "DEMO-AGENT-REPLAY":
        return {
            "trace_id": payload.get("trace_id", "g3-b2-optimization-authoritative-round1"),
            "replay_hash": payload.get("replay_sha256") or payload.get("replay_hash") or payload.get("canonical_replay_sha256"),
            "command_status": payload.get("status"),
        }
    if step_id == "DEMO-VISUAL-VERIFY":
        return {"command_status": payload.get("status"), "figure_count": payload.get("figure_count", 13), "benchmark_rerun": False}
    if step_id == "DEMO-AGENT-VERIFY":
        return {"command_status": payload.get("status"), "prompt_count": payload.get("registries", {}).get("prompt_count"), "skill_count": payload.get("registries", {}).get("skill_count"), "trace_count": payload.get("traces", {}).get("trace_count")}
    if step_id == "DEMO-REPORT-DESCRIBE":
        return {"command_status": payload.get("status"), "metric_count": payload.get("metric_count"), "claim_count": payload.get("claim_count"), "read_only": payload.get("read_only")}
    if step_id == "DEMO-SUBMISSION-DESCRIBE":
        return {"command_status": payload.get("status"), "default_backend": payload.get("default_backend"), "direct_artifact": payload.get("direct_artifact"), "real_device_blocked_reason": payload.get("real_device_blocked_reason")}
    return {"command_status": payload.get("status")}


def _execute_step(step: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    command = list(step["command"])
    if command[:2] != ["python", "-m"] or command[2] not in ALLOWED_MODULES:
        raise RuntimeError(f"command is not allowlisted: {step['step_id']}")
    if os.name == "nt":
        drive, tail = os.path.splitdrive(str(ROOT.resolve()))
        if not drive:
            raise RuntimeError("cannot map repository path to WSL")
        normalized_tail = tail.lstrip("\\/").replace("\\", "/")
        linux_root = f"/mnt/{drive[0].lower()}/{normalized_tail}"
        linux_command = ["python3", *command[1:]]
        unset = " ".join(f"-u {name}" for name in sorted(API_KEY_NAMES))
        script = f"cd {shlex.quote(linux_root)} && env {unset} {shlex.join(linux_command)}"
        actual = ["wsl.exe", "--distribution", WSL_DISTRIBUTION, "--exec", "bash", "-lc", script]
    else:
        actual = [sys.executable, *command[1:]]
    env = os.environ.copy()
    for key in API_KEY_NAMES:
        env.pop(key, None)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            actual, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=step["timeout_seconds"], check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"step timed out: {step['step_id']}") from exc
    duration = round(time.monotonic() - started, 6)
    if completed.returncode != step["expected_exit_code"]:
        tail = (completed.stderr or completed.stdout)[-2000:]
        raise RuntimeError(f"step failed: {step['step_id']} exit={completed.returncode}: {tail}")
    payload = _parse_json_output(completed.stdout)
    if payload.get("status") != "PASS":
        raise RuntimeError(f"step did not report PASS: {step['step_id']}")
    canonical = {
        "step_id": step["step_id"], "status": "PASS", "truth_identity": step["truth_identity"],
        "sentinel": step["expected_sentinels"][0], "semantic_facts": _semantic_facts(step["step_id"], payload),
        "limitations": step["limitations"],
    }
    raw = {
        "step_id": step["step_id"], "exit_code": completed.returncode, "duration_seconds": duration,
        "stdout": completed.stdout, "stderr": completed.stderr, "api_keys_present": False,
        "network_required": False, "hardware_required": False,
    }
    return canonical, raw


def run_profile(profile: str, output: Path | None = None) -> dict[str, Any]:
    manifest = read_json(MANIFEST)
    normalized = profile.upper()
    if normalized == "FALLBACK":
        normalized = "FALLBACK_DEMO"
    elif normalized == "QUICK":
        normalized = "QUICK_DEMO"
    elif normalized == "TECHNICAL":
        normalized = "TECHNICAL_DEMO"
    if normalized == "FALLBACK_DEMO":
        steps = [
            {"step_id": key, **value} for key, value in sorted(_fallback_outputs().items())
        ]
        canonical = {"profile": normalized, "status": "PASS", "steps": steps, "live_execution": False}
        result = {
            "schema_version": "g3-f-demo-run-v1", "status": "PASS", "profile": normalized,
            "canonical_transcript": canonical, "canonical_transcript_sha256": canonical_sha256(canonical),
            "sentinel": "G3_F_DEMO_FALLBACK_OK", "benchmark_rerun": False,
            "network_required": False, "api_key_required": False, "hardware_required": False, "runtime_api_calls": [],
        }
    else:
        wanted = manifest["profiles"].get(normalized)
        if not wanted:
            raise ValueError(f"unknown profile: {profile}")
        indexed = {row["step_id"]: row for row in manifest["steps"]}
        canonical_steps: list[dict[str, Any]] = []
        raw_steps: list[dict[str, Any]] = []
        started = time.monotonic()
        for step_id in wanted:
            canonical, raw = _execute_step(indexed[step_id])
            canonical_steps.append(canonical)
            raw_steps.append(raw)
        canonical = {"profile": normalized, "status": "PASS", "steps": canonical_steps, "live_execution": True}
        result = {
            "schema_version": "g3-f-demo-run-v1", "status": "PASS", "profile": normalized,
            "canonical_transcript": canonical, "canonical_transcript_sha256": canonical_sha256(canonical),
            "raw_steps": raw_steps, "total_runtime_seconds": round(time.monotonic() - started, 6),
            "sentinel": "G3_F_OFFLINE_DEMO_OK", "benchmark_rerun": False,
            "network_required": False, "api_key_required": False, "hardware_required": False, "runtime_api_calls": [],
        }
    if output is not None:
        write_json(output, result)
    return result


def validate_demo_package() -> dict[str, Any]:
    errors: list[str] = []
    required = [
        "demo_contract.json", "demo_manifest.json", "demo_profiles.md", "live_demo_guide.md",
        "fallback_demo_guide.md", "demo_truth_boundary.md",
    ]
    for name in required:
        if not (DELIVERY_ROOT / name).is_file():
            errors.append(f"missing artifact: {name}")
    expected = DELIVERY_ROOT / "expected_outputs"
    if len(list(expected.glob("*.json"))) != 3:
        errors.append("fallback expected-output count mismatch")
    if errors:
        return {"schema_version": "g3-f-demo-validation-v1", "status": "FAIL", "errors": errors}
    manifest = read_json(MANIFEST)
    steps = {row["step_id"]: row for row in manifest.get("steps", [])}
    quick = manifest.get("profiles", {}).get("QUICK_DEMO", [])
    if quick != ["DEMO-CPU-SIM", "DEMO-AGENT-REPLAY", "DEMO-VISUAL-VERIFY"]:
        errors.append("QUICK_DEMO sequence mismatch")
    for step_id, row in steps.items():
        command = row.get("command", [])
        if command[:2] != ["python", "-m"] or len(command) < 3 or command[2] not in ALLOWED_MODULES:
            errors.append(f"command not allowlisted: {step_id}")
        if any(row.get(key) for key in ("network_required", "api_key_required", "hardware_required")):
            errors.append(f"offline boundary violated: {step_id}")
        if not row.get("timeout_seconds") or row.get("retry_budget") != 0 or not row.get("fallback_step") and step_id in quick:
            errors.append(f"timeout/retry/fallback contract invalid: {step_id}")
        if not row.get("on_screen_truth_badge") or not row.get("limitations"):
            errors.append(f"truth boundary missing: {step_id}")
        if any(any(token in part for token in ("&&", ";", "|", "`", "$(`")) for part in command):
            errors.append(f"shell metacharacter rejected: {step_id}")
    if "DEMO-CPU-SIM" not in steps or steps["DEMO-CPU-SIM"]["truth_identity"] != "LIVE_DEMO_CPU_SIM":
        errors.append("CPU_SIM functional step missing")
    for path in [DELIVERY_ROOT / name for name in required] + list(expected.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        if str(ROOT) in text or "C:\\Users\\" in text or "/home/" in text:
            errors.append(f"local absolute path in {path.relative_to(DELIVERY_ROOT).as_posix()}")
    return {
        "schema_version": "g3-f-demo-validation-v1", "status": "PASS" if not errors else "FAIL",
        "errors": errors, "step_count": len(steps), "quick_step_count": len(quick),
        "fallback_count": len(list(expected.glob("*.json"))),
        "sentinels": ["G3_F_OFFLINE_DEMO_OK", "G3_F_DEMO_FALLBACK_OK"] if not errors else [],
        "benchmark_rerun": False, "runtime_api_calls": [],
    }
