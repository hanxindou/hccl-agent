"""Final validation and evidence freeze for G3-D Agent/Prompt delivery."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools.submission_cli.core import verify_stage

from .authority import PROVENANCE_VOCABULARY, validate_authority_artifacts
from .common import (
    G3_B2_ROOT,
    G3_B2_SHA256SUMS_SHA256,
    G3_B3_ROOT,
    G3_B3_SHA256SUMS_SHA256,
    G3_C_ROOT,
    OUTPUT_ROOT,
    ROOT,
    assert_relative_repository_paths,
    git,
    load_json,
    relative,
    sha256_file,
    verify_sha256sums,
    write_json,
)
from .documentation import REQUIRED_DOCUMENTS, validate_documentation
from .registry import validate_registries
from .trace import replay_trace, validate_traces


FINAL_SENTINELS = (
    "G3_D_AUTHORITY_INVENTORY_OK",
    "PROMPT_REGISTRY_OK",
    "SKILL_REGISTRY_OK",
    "TRACE_INDEX_OK",
    "OFFLINE_REPLAY_OK",
    "PROVENANCE_OK",
    "CLAIM_BOUNDARIES_OK",
    "NO_SECRETS_OK",
    "G3_D_AGENT_PROMPT_DELIVERY_OK",
)

EXPECTED_EVIDENCE_FILES = (
    "README.md",
    "manifest.json",
    "result.json",
    "authority_inventory_validation.json",
    "delivery_contract_validation.json",
    "prompt_registry_validation.json",
    "skill_registry_validation.json",
    "trace_index_validation.json",
    "g3_b2_trace_validation.json",
    "g3_b3_trace_validation.json",
    "offline_replay_validation.json",
    "replay_determinism.json",
    "provenance_validation.json",
    "human_intervention_validation.json",
    "historical_unavailable_validation.json",
    "claim_boundary_validation.json",
    "source_commit_mapping_validation.json",
    "staging_verification.json",
    "regression_summary.json",
    "no_secrets_audit.json",
    "path_portability_audit.json",
    "git_state.json",
    "user_action_required.json",
    "SHA256SUMS",
)

ALLOWED_G3_D_CHANGE_PREFIXES = (
    "docs/plans/g3-competition-delivery-readiness.md",
    "docs/submission/agent_delivery/",
    "experiments/submission/evidence/g3_d_",
    "tests/agent_delivery/",
    "tests/reporting/test_git_base_ref.py",
    "tools/agent_delivery/",
    "tools/agent_delivery_cli.py",
    "tools/reporting/evidence_reader.py",
    "tools/submission_cli/core.py",
    # Later delivery-only checkpoints may add presentation artifacts and their
    # validators without reopening the G3-B3 technical Feature Freeze.
    "docs/submission/visualization/",
    "experiments/submission/evidence/g3_e_",
    "tests/visualization/",
    "tools/visualization/",
    "tools/visualization_cli.py",
)

USER_ACTION_REQUIRED = (
    {"id": "UA-B-001", "topic": "license/copyright", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-B-002", "topic": "official artifact redistribution", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-B-003", "topic": "controlled competition materials", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-B-004", "topic": "submission archive format and size limits", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-D-001", "topic": "precision interpretation", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-D-002", "topic": "final submission language and template", "status": "USER_ACTION_REQUIRED"},
    {"id": "UA-D-003", "topic": "real-device acceptance", "status": "USER_ACTION_REQUIRED", "current_truth": "HARDWARE_BLOCKED"},
)


def _status(errors: list[str]) -> str:
    return "PASS" if not errors else "FAIL"


def _changed_paths() -> list[str]:
    committed = git("diff", "--name-only", "origin/main", "--").splitlines()
    status_paths = []
    for line in git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if len(line) >= 3:
            # common.git strips the full output, so the first porcelain line may
            # lose its leading worktree-status space. Preserve both forms.
            offset = 2 if line[1] == " " else 3
            status_paths.append(line[offset:].replace("\\", "/"))
    return sorted(set(
        path.replace("\\", "/")
        for path in committed + status_paths
        if path and not path.replace("\\", "/").startswith("dist/")
    ))


def _allowed_change(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_G3_D_CHANGE_PREFIXES)


def _claim_validation() -> dict[str, Any]:
    current_claim = ROOT / "docs/submission/report_claim_ledger.json"
    current_data = ROOT / "docs/submission/report_data_ledger.json"
    frozen_claim = G3_C_ROOT / "report_claim_ledger.json"
    frozen_data = G3_C_ROOT / "report_data_ledger.json"
    errors: list[str] = []
    hashes = {
        "claim_ledger": {"current": sha256_file(current_claim), "g3_c_frozen": sha256_file(frozen_claim)},
        "data_ledger": {"current": sha256_file(current_data), "g3_c_frozen": sha256_file(frozen_data)},
    }
    for name, pair in hashes.items():
        if pair["current"] != pair["g3_c_frozen"]:
            errors.append(f"G3-C {name} changed")
    claims = load_json(current_claim)
    required_truth = {
        "LOSSLESS_SPARSE_HOST_EXECUTED",
        "HOST_INTEGRITY_VALIDATED",
        "HOST_RETRY_VALIDATED",
        "SIMULATED_BACKPRESSURE",
        "SIMULATED_ONLY",
        "DIRECT_COMPILE_LINK_ONLY",
        "REAL_DEVICE_NOT_EXECUTED",
    }
    ledger_text = current_claim.read_text(encoding="utf-8")
    missing_truth = sorted(label for label in required_truth if label not in ledger_text)
    if missing_truth:
        errors.append(f"required truth labels missing: {missing_truth}")
    return {
        "schema_version": "g3-d-claim-boundary-validation-v1",
        "status": _status(errors),
        "errors": errors,
        "claim_authority": "docs/submission/report_claim_ledger.json",
        "claim_count": claims["claim_count"],
        "ledger_hashes": hashes,
        "required_truth_labels": sorted(required_truth),
        "forbidden_promotions": [
            "45.59% as real Ascend NPU performance",
            "17 official ACL/HCCL call expressions as real-device execution",
            "simulation or compile-only readiness as runtime validation",
        ],
    }


def _freeze_validation() -> dict[str, Any]:
    changed = _changed_paths()
    forbidden = [path for path in changed if not _allowed_change(path)]
    abi = load_json(ROOT / "hcccl/submission/native_plugin_abi_manifest.json")
    errors = list(f"feature-freeze path changed: {path}" for path in forbidden)
    if abi.get("artifact_name") != "libhccl_plugin.so" or abi.get("soname") != "libhccl_plugin.so":
        errors.append("CPU_SIM artifact name or SONAME changed")
    if len(abi.get("exported_symbols", [])) != 19 or len(set(abi.get("exported_symbols", []))) != 19:
        errors.append("CPU_SIM 19-symbol allowlist changed")
    if abi.get("artifact_role") != "CPU_SIM_REFERENCE_PLUGIN":
        errors.append("CPU_SIM artifact role changed")
    return {
        "schema_version": "g3-d-feature-freeze-validation-v1",
        "status": _status(errors),
        "errors": errors,
        "changed_paths": changed,
        "forbidden_changed_paths": forbidden,
        "cpu_sim_contract": {
            "artifact_role": abi.get("artifact_role"),
            "soname": abi.get("soname"),
            "exported_symbol_count": len(abi.get("exported_symbols", [])),
        },
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "runtime_api_calls": [],
    }


def _content_audits() -> tuple[dict[str, Any], dict[str, Any]]:
    secret_findings: list[dict[str, str]] = []
    path_findings: list[dict[str, str]] = []
    secret_pattern = re.compile(r"\b(?:sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]+|AIza[A-Za-z0-9_-]{12,})\b")
    path_pattern = re.compile(r"(?:[A-Za-z]:\\(?:Users|projects)\\|/home/[^/]+/|/Users/[^/]+/|/mnt/[a-z]/)", re.IGNORECASE)
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if secret_pattern.search(text):
            secret_findings.append({"path": relative(path), "kind": "secret-like token"})
        if path_pattern.search(text):
            path_findings.append({"path": relative(path), "kind": "local absolute path"})
    return (
        {
            "schema_version": "g3-d-no-secrets-audit-v1",
            "status": "PASS" if not secret_findings else "FAIL",
            "findings": secret_findings,
            "api_keys_required": [],
            "sentinel": "NO_SECRETS_OK" if not secret_findings else None,
        },
        {
            "schema_version": "g3-d-path-portability-audit-v1",
            "status": "PASS" if not path_findings else "FAIL",
            "findings": path_findings,
            "scan_root": "docs/submission/agent_delivery",
        },
    )


def collect_final_validation(stage_root: Path) -> dict[str, Any]:
    authority = validate_authority_artifacts()
    registries = validate_registries()
    traces = validate_traces()
    documentation = validate_documentation()
    staging = verify_stage(stage_root)
    claims = _claim_validation()
    freeze = _freeze_validation()
    secrets, paths = _content_audits()
    b2_root = verify_sha256sums(G3_B2_ROOT, G3_B2_SHA256SUMS_SHA256)
    b3_root = verify_sha256sums(G3_B3_ROOT, G3_B3_SHA256SUMS_SHA256)
    replays = {
        trace_id: replay_trace(trace_id)
        for trace_id in ("g3-b2-optimization-authoritative-round1", "g3-b3-feature-completion-agent-flow")
    }
    checks = (authority, registries, traces, documentation, staging, claims, freeze, secrets, paths, b2_root, b3_root)
    return {
        "status": "PASS" if all(item.get("status") == "PASS" for item in checks) else "FAIL",
        "authority": authority,
        "registries": registries,
        "traces": traces,
        "documentation": documentation,
        "staging": staging,
        "claims": claims,
        "feature_freeze": freeze,
        "secrets": secrets,
        "paths": paths,
        "g3_b2_root": b2_root,
        "g3_b3_root": b3_root,
        "replays": replays,
    }


def _trace_detail(trace_id: str) -> dict[str, Any]:
    index = load_json(OUTPUT_ROOT / "trace_index.json")
    row = next(item for item in index["traces"] if item["trace_id"] == trace_id)
    trace = load_json(ROOT / row["path"])
    return {
        "schema_version": "g3-d-normalized-trace-evidence-validation-v1",
        "status": "PASS",
        "trace_id": trace_id,
        "normalized_trace": row,
        "source_checkpoint": trace["source_checkpoint"],
        "source_evidence_path": trace["source_evidence_path"],
        "source_evidence_sha256": trace["source_evidence_sha256"],
        "source_commit": trace["source_commit"],
        "provenance_identity": trace["provenance_identity"],
        "historical_execution": False,
        "hidden_chain_of_thought_included": False,
    }


def _write_checksums(root: Path) -> str:
    lines = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            lines.append(f"{sha256_file(path)}  {path.relative_to(root).as_posix()}")
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return sha256_file(root / "SHA256SUMS")


def freeze_evidence(
    evidence_root: Path,
    stage_root: Path,
    *,
    focused_passed: int,
    full_pytest_passed: int,
    full_pytest_skipped: int,
    ctest_passed: int,
    linux_validation_ok: bool,
) -> dict[str, Any]:
    if evidence_root.exists() and any(evidence_root.iterdir()):
        raise ValueError("refusing to overwrite existing G3-D evidence")
    validation = collect_final_validation(stage_root)
    if validation["status"] != "PASS" or not linux_validation_ok:
        raise ValueError("G3-D final validation is not PASS")
    evidence_root.mkdir(parents=True, exist_ok=True)
    regression = {
        "schema_version": "g3-d-regression-summary-v1",
        "status": "PASS",
        "focused_g3_d": {"status": "PASS", "passed": focused_passed, "command": "python -m pytest tests/agent_delivery -q"},
        "full_pytest": {"status": "PASS", "passed": full_pytest_passed, "skipped": full_pytest_skipped},
        "ctest": {"status": "PASS", "passed": ctest_passed},
        "linux_cpu_sim_validation": {"status": "PASS", "sentinel": "LINUX_CPU_SIM_VALIDATION_OK", "temporary_build_root": "<temporary-linux-build-root>"},
    }
    replay_validation = {
        "schema_version": "g3-d-offline-replay-validation-v1",
        "status": "PASS",
        "mandatory_identity": "OFFLINE_REPLAY",
        "network_used": False,
        "api_keys_used": [],
        "runtime_api_calls": [],
        "historical_execution": False,
        "replays": validation["replays"],
    }
    replay_determinism = {
        "schema_version": "g3-d-replay-determinism-v1",
        "status": "PASS",
        "hashes": validation["traces"]["replay_hashes"],
        "repeat_count": 2,
        "outputs_equal": True,
    }
    mapping = load_json(OUTPUT_ROOT / "source_commit_evidence_claim_mapping.json")
    disclosure = load_json(OUTPUT_ROOT / "human_intervention_disclosure.json")
    artifacts: dict[str, Any] = {
        "authority_inventory_validation.json": validation["authority"],
        "delivery_contract_validation.json": {
            "schema_version": "g3-d-delivery-contract-validation-v1",
            "status": "PASS",
            "authority_hierarchy": load_json(OUTPUT_ROOT / "delivery_contract.json")["authority_hierarchy"],
            "provenance_vocabulary": list(PROVENANCE_VOCABULARY),
            "mandatory_path": load_json(OUTPUT_ROOT / "delivery_contract.json")["mandatory_path"],
            "feature_freeze": validation["feature_freeze"],
        },
        "prompt_registry_validation.json": {"schema_version": "g3-d-prompt-registry-validation-v1", "status": "PASS", "prompt_count": validation["registries"]["prompt_count"], "source_hashes": "VALIDATED", "sentinel": "PROMPT_REGISTRY_OK"},
        "skill_registry_validation.json": {"schema_version": "g3-d-skill-registry-validation-v1", "status": "PASS", "skill_count": validation["registries"]["skill_count"], "source_and_test_mappings": "VALIDATED", "sentinel": "SKILL_REGISTRY_OK"},
        "trace_index_validation.json": validation["traces"],
        "g3_b2_trace_validation.json": _trace_detail("g3-b2-optimization-authoritative-round1"),
        "g3_b3_trace_validation.json": _trace_detail("g3-b3-feature-completion-agent-flow"),
        "offline_replay_validation.json": replay_validation,
        "replay_determinism.json": replay_determinism,
        "provenance_validation.json": validation["documentation"],
        "human_intervention_validation.json": {"schema_version": "g3-d-human-intervention-validation-v1", "status": "PASS", "disclosure": disclosure, "agent_description": "Agent-assisted, deterministically evaluated, human-governed, and offline replayable"},
        "historical_unavailable_validation.json": {"schema_version": "g3-d-historical-unavailable-validation-v1", "status": "PASS", "g3_b3_prompt_response": "HISTORICAL_TRACE_UNAVAILABLE", "g3_b3_human_intervention": "HISTORICAL_TRACE_UNAVAILABLE", "fabricated_history": False, "hidden_chain_of_thought_included": False},
        "claim_boundary_validation.json": validation["claims"],
        "source_commit_mapping_validation.json": {"schema_version": "g3-d-source-commit-mapping-validation-v1", "status": "PASS", "relationship_count": mapping["relationship_count"], "commit_validity": "VALIDATED_WHERE_ASSERTED", "unavailable_relationships_preserved": True},
        "staging_verification.json": validation["staging"],
        "regression_summary.json": regression,
        "no_secrets_audit.json": validation["secrets"],
        "path_portability_audit.json": validation["paths"],
        "git_state.json": {
            "schema_version": "g3-d-git-state-v1",
            "status": "PRE_FINAL_COMMIT_CAPTURE",
            "branch": git("branch", "--show-current"),
            "source_commit_before_final_freeze": git("rev-parse", "HEAD"),
            "planned_final_commit": "G3-D-E finalize Agent prompt delivery evidence",
            "changed_paths": validation["feature_freeze"]["changed_paths"],
            "forbidden_changed_paths": [],
        },
        "user_action_required.json": {"schema_version": "g3-d-user-action-required-v1", "status": "USER_ACTION_REQUIRED", "items": list(USER_ACTION_REQUIRED)},
    }
    result = {
        "schema_version": "g3-d-final-result-v1",
        "checkpoint": "G3-D-E",
        "status": "COMPLETED",
        "delivery_status": "G3_D_AGENT_PROMPT_DELIVERY_OK",
        "mandatory_replay": "OFFLINE_REPLAY",
        "external_api_required": False,
        "historical_execution_claimed": False,
        "feature_freeze": "PRESERVED",
        "claim_ledger": "PRESERVED",
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "runtime_api_calls": [],
        "sentinels": list(FINAL_SENTINELS),
    }
    manifest = {
        "schema_version": "g3-d-evidence-manifest-v1",
        "status": "FROZEN",
        "authority_mode": "POINTER_AND_HASH_NO_PRIOR_TREE_COPY",
        "source_commit_before_final_freeze": git("rev-parse", "HEAD"),
        "artifacts": [name for name in EXPECTED_EVIDENCE_FILES if name != "SHA256SUMS"],
        "authority_roots": {
            "g3_b2": {"path": relative(G3_B2_ROOT), "sha256sums_sha256": G3_B2_SHA256SUMS_SHA256},
            "g3_b3": {"path": relative(G3_B3_ROOT), "sha256sums_sha256": G3_B3_SHA256SUMS_SHA256},
            "g3_c": {"path": relative(G3_C_ROOT), "claim_ledger_sha256": validation["claims"]["ledger_hashes"]["claim_ledger"]["current"]},
        },
    }
    for name, value in artifacts.items():
        assert_relative_repository_paths(value)
        write_json(evidence_root / name, value)
    write_json(evidence_root / "result.json", result)
    write_json(evidence_root / "manifest.json", manifest)
    readme = """# G3-D Agent / Prompt Reproducible Delivery Evidence

Status: `COMPLETED`

This evidence freezes the keyless offline replay, Prompt/Skill registries, normalized frozen-trace reconstruction, provenance disclosure, G3-C claim-boundary preservation, staging coverage, and regression results for G3-D. It references prior authority evidence by repository-relative pointer and hash; it does not copy or rewrite G3-B2, G3-B3, or G3-C evidence.

The replay is not historical execution. Missing historical Prompt/Response and human-intervention records remain `HISTORICAL_TRACE_UNAVAILABLE`. No hidden chain-of-thought is included. Real-device acceptance remains `HARDWARE_BLOCKED`; runtime API calls are empty.
"""
    (evidence_root / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    sums_digest = _write_checksums(evidence_root)
    verified = verify_final_evidence(evidence_root)
    return {
        "schema_version": "g3-d-evidence-freeze-v1",
        "status": verified["status"],
        "evidence_root": relative(evidence_root),
        "sha256sums_sha256": sums_digest,
        "sentinel": "G3_D_AGENT_PROMPT_DELIVERY_OK" if verified["status"] == "PASS" else None,
    }


def verify_final_evidence(evidence_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    present = {path.name for path in evidence_root.iterdir() if path.is_file()} if evidence_root.is_dir() else set()
    missing = sorted(set(EXPECTED_EVIDENCE_FILES) - present)
    if missing:
        errors.append(f"missing evidence artifacts: {missing}")
    sums = evidence_root / "SHA256SUMS"
    checksummed: set[str] = set()
    if sums.is_file():
        for raw in sums.read_text(encoding="utf-8").splitlines():
            digest, name = raw.split("  ", 1)
            path = evidence_root / name
            if not path.is_file() or sha256_file(path) != digest:
                errors.append(f"evidence checksum mismatch: {name}")
            checksummed.add(name)
        actual = {path.relative_to(evidence_root).as_posix() for path in evidence_root.rglob("*") if path.is_file() and path.name != "SHA256SUMS"}
        if checksummed != actual:
            errors.append("SHA256SUMS coverage mismatch")
    result = load_json(evidence_root / "result.json") if (evidence_root / "result.json").is_file() else {}
    if result.get("delivery_status") != "G3_D_AGENT_PROMPT_DELIVERY_OK":
        errors.append("final delivery sentinel missing")
    if result.get("external_api_required") is not False or result.get("real_device_api_executed") is not False or result.get("runtime_api_calls"):
        errors.append("offline/hardware boundary mismatch")
    if set(result.get("sentinels", [])) != set(FINAL_SENTINELS):
        errors.append("final sentinel set mismatch")
    return {
        "schema_version": "g3-d-final-evidence-verification-v1",
        "status": _status(errors),
        "errors": errors,
        "files_verified": len(checksummed),
        "sha256sums_sha256": sha256_file(sums) if sums.is_file() else None,
        "sentinel": "G3_D_AGENT_PROMPT_DELIVERY_OK" if not errors else None,
    }
