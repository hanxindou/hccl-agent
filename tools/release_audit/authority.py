"""G3-G-A authority, inventory, and release-contract implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import RELEASE_ROOT, ROOT, git_output, portable_text_findings, read_json, sha256_file, verify_sha256sums, write_json, write_text


AUTHORITY_ROOTS = {
    "g3_b2": ("experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z", "99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483"),
    "g3_b3": ("experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z", "45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754"),
    "g3_c": ("experiments/submission/evidence/g3_c_20260809T000000Z", "cc29469e79d9a242aa7eb2859d5ca94357bc2700ad6a6887ffdce1852bf44707"),
    "g3_d": ("experiments/submission/evidence/g3_d_20260809T123956Z", "1f702c043e6e73bf2f1464a1d40367eb4d8599d5b56b67604acdac69494bb312"),
    "g3_e": ("experiments/submission/evidence/g3_e_20260809T155045Z", "f57cbe2743042008075098a482264902129539a4a87a83e22b051edb5808cbdf"),
    "g3_f": ("experiments/submission/evidence/g3_f_20260810T013950Z", "2cc72eef68c0b788ad81006cc9b7a0f8e81188dc4bd4df3eab8528069cfc3124"),
}

TRUTH_IDENTITIES = [
    "HOST_EXECUTED", "CPU_EXECUTED", "SIMULATED_ONLY", "LOSSLESS_SPARSE_HOST_EXECUTED",
    "HOST_INTEGRITY_VALIDATED", "HOST_RETRY_VALIDATED", "SIMULATED_BACKPRESSURE",
    "DIRECT_READINESS_ONLY", "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED",
    "HISTORICAL_EVIDENCE", "OFFLINE_REPLAY", "REPLAYED_FROM_FROZEN_TRACE",
    "RECONSTRUCTED_FROM_FROZEN_EVIDENCE", "AGENT_GENERATED", "DETERMINISTIC_EVALUATION",
    "HUMAN_INTERVENTION", "HISTORICAL_TRACE_UNAVAILABLE", "ONLINE_LLM_OPTIONAL",
    "LIVE_DEMO_CPU_SIM", "DEMO_REPLAY", "PRERECORDED_DETERMINISTIC_OUTPUT", "REFERENCE_VIDEO_ONLY",
]

USER_ACTION_SUBJECTS = {
    "UA-B-001": "project license and copyright ownership",
    "UA-B-002": "official artifact redistribution authorization",
    "UA-B-003": "controlled competition material disposition",
    "UA-B-004": "submission archive and size rules",
    "UA-C-001": "precision interpretation",
    "UA-C-002": "final report language",
    "UA-C-003": "final template, font, anonymity, and PDF rules",
    "UA-D-001": "historical Agent and Prompt record availability",
    "UA-D-002": "Agent disclosure detail",
    "UA-D-003": "real-device acceptance",
    "UA-E-001": "final visual language",
    "UA-E-002": "competition visual template",
    "UA-E-003": "logo and external asset permission",
    "UA-E-004": "final innovation wording approval",
    "UA-F-001": "competition video specification",
    "UA-F-002": "final narration and subtitle language",
    "UA-F-003": "voice and audio policy",
    "UA-F-004": "live demo environment",
    "UA-F-005": "recording and branding approval",
    "UA-F-006": "final video and demo wording approval",
    "UA-G-001": "final submission package specification",
    "UA-G-002": "final legal and redistribution authorization",
    "UA-G-003": "final controlled-material inclusion decision",
    "UA-G-004": "final release candidate approval",
    "UA-G-005": "Git tag and GitHub release authorization",
    "UA-G-006": "final competition submission authorization",
}

OLD_AUTHORITY_SCOPES = [
    "docs/submission/report_claim_ledger.json",
    "docs/submission/report_data_ledger.json",
    "docs/submission/report_chart_data",
    "docs/submission/agent_delivery/prompt_registry.json",
    "docs/submission/agent_delivery/skill_registry.json",
    "docs/submission/agent_delivery/trace_index.json",
    "docs/submission/agent_delivery/traces",
    "docs/submission/agent_delivery/source_commit_evidence_claim_mapping.json",
    "docs/submission/visualization/chart_registry.json",
    "docs/submission/visualization/assets",
    "docs/submission/visualization/innovation_map.json",
    "docs/submission/visualization/competition_narrative.md",
    "docs/submission/visualization/claim_safe_phrasebook.md",
    "docs/submission/demo_video/demo_manifest.json",
    "docs/submission/demo_video/storyboard.json",
    "docs/submission/demo_video/narration_source.json",
    "docs/submission/demo_video/subtitle_source.json",
    "docs/submission/demo_video/presentation_flow.json",
]

MANDATORY_ENTRY_POINTS = [
    ["python", "-m", "tools.submission_cli", "check"],
    ["python", "-m", "tools.submission_cli", "quick", "--rank-size", "4", "--message-size", "4096"],
    ["python", "-m", "pytest", "tests", "-q"],
    ["python", "-m", "tools.report_cli", "verify"],
    ["python", "-m", "tools.agent_delivery_cli", "verify"],
    ["python", "-m", "tools.agent_delivery_cli", "replay", "--trace", "g3-b2-optimization-authoritative-round1"],
    ["python", "-m", "tools.agent_delivery_cli", "replay", "--trace", "g3-b3-feature-completion-agent-flow"],
    ["python", "-m", "tools.visualization_cli", "build-charts"],
    ["python", "-m", "tools.visualization_cli", "verify"],
    ["python", "-m", "tools.demo_delivery_cli", "run", "--profile", "quick"],
    ["python", "-m", "tools.demo_delivery_cli", "transcript", "--profile", "fallback"],
    ["python", "-m", "tools.demo_delivery_cli", "stage"],
    ["python", "-m", "tools.demo_delivery_cli", "verify-stage"],
    ["python", "-m", "tools.release_cli", "preflight"],
]


def _classify(relative: str) -> dict[str, Any]:
    suffix = Path(relative).suffix.lower()
    if relative.startswith(("build/", "dist/")) or suffix in {".pyc", ".o", ".so"}:
        status, reason = "EXCLUDE_BUILD_ARTIFACT", "generated build output is rebuilt from source"
    elif relative.startswith(("experiments/optimization/evidence/", "experiments/feature_completion/evidence/", "experiments/submission/evidence/")):
        status, reason = "OPTIONAL", "frozen evidence is referenced by pointer and digest; selected material only"
    elif relative.endswith((".docx", ".pptx", ".mp4", ".mov", ".wav", ".mp3")):
        status, reason = "EXCLUDE_CONTROLLED", "binary or controlled material is excluded without explicit authorization"
    elif relative.startswith((".github/", "docs/plans/")):
        status, reason = "OPTIONAL", "development and governance metadata is not a mandatory runtime payload"
    else:
        status, reason = "INCLUDE", "project source, test, configuration, or submission documentation"
    category = relative.split("/", 1)[0].upper().replace(".", "_")
    return {
        "path": relative, "category": category, "tracked_status": "TRACKED",
        "source_or_generated": "SOURCE", "mandatory_or_optional": "MANDATORY" if status == "INCLUDE" else "OPTIONAL",
        "staging_status": "CANONICAL_STAGE_OR_OVERLAY" if status == "INCLUDE" else "NOT_REQUIRED_IN_STAGE",
        "release_status": status, "license_status": "USER_ACTION_REQUIRED",
        "copyright_status": "USER_ACTION_REQUIRED", "redistribution_status": "USER_ACTION_REQUIRED",
        "controlled_material_status": "EXCLUDED_BY_DEFAULT" if status == "EXCLUDE_CONTROLLED" else "NOT_IDENTIFIED_BY_PATH",
        "secret_risk": "SCAN_REQUIRED", "privacy_risk": "SCAN_REQUIRED",
        "platform_specific": relative.startswith((".github/", "scripts/")), "reproducible": True,
        "authority_level": "L1", "hash_required": status in {"INCLUDE", "OPTIONAL"},
        "reason": reason, "user_action_required_refs": ["UA-B-001", "UA-G-002"],
    }


def _authority_inventory() -> dict[str, Any]:
    checked: dict[str, Any] = {}
    for name, (relative, expected) in AUTHORITY_ROOTS.items():
        result = verify_sha256sums(ROOT / relative)
        result["expected_sha256sums_sha256"] = expected
        result["digest_match"] = result.get("sha256sums_sha256") == expected
        checked[name] = result
    return {
        "schema_version": "g3-g-release-authority-v1", "checkpoint": "G3-G-A",
        "status": "PASS" if all(item["status"] == "PASS" and item["digest_match"] for item in checked.values()) else "FAIL",
        "source_baseline": git_output("rev-parse", "origin/main"),
        "branch_base": git_output("merge-base", "HEAD", "origin/main"),
        "authority_hierarchy": ["L1_MERGED_SOURCE", "L2_G3_C", "L3_G3_D", "L4_G3_E", "L5_G3_F", "L6_G3_B3", "L7_G3_B2", "L8_EARLIER_DELIVERY_AND_G3_A"],
        "authority_roots": checked, "truth_identities": TRUTH_IDENTITIES,
        "benchmark_rerun": False, "network_required": False, "external_llm_required": False,
        "real_device_required": False, "runtime_api_calls": [],
    }


def _release_inventory() -> dict[str, Any]:
    tracked = [line for line in git_output("ls-files", "-z").split("\0") if line]
    entries = [_classify(relative) for relative in tracked]
    counts: dict[str, int] = {}
    for row in entries:
        counts[row["release_status"]] = counts.get(row["release_status"], 0) + 1
    return {
        "schema_version": "g3-g-release-inventory-v1", "status": "PASS",
        "source_baseline": git_output("rev-parse", "origin/main"), "tracked_file_count": len(entries),
        "release_status_counts": counts, "unknown_source_count": 0, "entries": entries,
    }


def _release_contract() -> dict[str, Any]:
    return {
        "schema_version": "g3-g-release-contract-v1", "status": "PASS",
        "repository_source_baseline": git_output("rev-parse", "origin/main"),
        "authority_roots": {name: {"path": path, "sha256sums_sha256": digest} for name, (path, digest) in AUTHORITY_ROOTS.items()},
        "hash_algorithm": "SHA256", "canonical_staging_root": "dist/submission-staging",
        "release_candidate_root": "dist/g3-g-release/candidate",
        "clean_environment_models": ["CLEAN_WORKTREE_REPRODUCTION", "CLEAN_EXTRACTION_REPRODUCTION"],
        "cold_start_run_count": 2, "canonical_sequence": MANDATORY_ENTRY_POINTS,
        "mandatory_environment": {"offline": True, "api_keys": False, "npu": False, "acl_hccl_runtime": False, "mpi": False},
        "required_software": ["Python 3", "pytest", "CMake", "C compiler", "make-compatible build tool", "Git", "WSL/Linux environment class on Windows host"],
        "optional_software": ["archive writer when local candidate archive is authorized by contract"],
        "required_documentation": ["README.md", "QUICKSTART.md", "CLAIM_BOUNDARIES.md", "docs/submission/release/release_readiness.md"],
        "required_native_artifacts": ["native/lib/libhccl_plugin.so", "native/include/hccl_comm.h", "native/include/hccl_algorithms.h"],
        "path_policy": {"separator": "/", "relative_only": True, "dot_segments": False, "absolute_paths": False, "case_collisions": False},
        "line_ending_policy": "repository text retained; generated metadata UTF-8 LF",
        "timestamp_policy": "SOURCE_DATE_EPOCH or normalized zero/1980 archive timestamp; timestamps excluded from semantic reproducibility",
        "permissions_policy": "regular files only; executable bit limited to declared scripts",
        "symlink_policy": "no symlinks in release candidate or archive",
        "manifest_schema": "g3-g-release-manifest-v1", "archive_ordering": "UTF-8 POSIX path byte order",
        "compression_policy": "ZIP_DEFLATED with fixed metadata when local release-candidate archive is created",
        "forbidden_paths": [".git", ".env", "build", "dist", "logs", "venv", ".venv", "__pycache__", ".pytest_cache"],
        "forbidden_file_types": ["private keys", "credentials", "official binaries", "unapproved controlled documents", "unapproved media binaries"],
        "secret_patterns": ["private key headers", "credential assignments with recognizable token prefixes"],
        "privacy_rules": ["no local absolute paths", "no usernames", "no environment dumps", "no raw private logs"],
        "controlled_material_policy": "EXCLUDE_UNLESS_EXPLICITLY_AUTHORIZED",
        "license_and_redistribution_policy": "AUDIT_ONLY_NOT_LEGAL_AUTHORIZATION",
        "external_asset_policy": "EXCLUDE_UNLESS_SOURCE_AND_PERMISSION_ARE_DECLARED",
        "final_authorization_boundary": "SOFTWARE_RELEASE_READY != FINAL_SUBMISSION_AUTHORIZED",
        "release_candidate_archive_status": "NOT_CREATED", "final_submission_archive_status": "NOT_AUTHORIZED",
    }


def _exclusion_policy() -> dict[str, Any]:
    return {
        "schema_version": "g3-g-release-exclusion-policy-v1", "status": "PASS",
        "default_controlled_material_policy": "EXCLUDE_UNLESS_EXPLICITLY_AUTHORIZED",
        "classes": [
            {"status": "EXCLUDE_GENERATED", "patterns": ["logs/", "*.pyc"], "reason": "non-authoritative generated output"},
            {"status": "EXCLUDE_TOOL_CACHE", "patterns": ["__pycache__/", ".pytest_cache/", ".mypy_cache/"], "reason": "host-local cache"},
            {"status": "EXCLUDE_BUILD_ARTIFACT", "patterns": ["build/", "dist/"], "reason": "reconstructed by cold-start"},
            {"status": "EXCLUDE_PRIVATE", "patterns": [".env", "private keys", "credential-bearing logs"], "reason": "secret and privacy boundary"},
            {"status": "EXCLUDE_CONTROLLED", "patterns": ["controlled attachments", "official SDK/HCOMM/HCCL material"], "reason": "authorization unresolved"},
            {"status": "EXCLUDE_UNRESOLVED_LICENSE", "patterns": ["unowned third-party assets"], "reason": "license audit is not authorization"},
        ],
    }


def _user_actions() -> dict[str, Any]:
    return {
        "schema_version": "g3-g-user-action-release-gate-v1", "status": "USER_ACTION_REQUIRED",
        "item_count": len(USER_ACTION_SUBJECTS),
        "items": [
            {"id": item, "subject": subject, "status": "USER_ACTION_REQUIRED", "closed_by_g3_g": False,
             "blocking_scope": "FINAL_COMPETITION_SUBMISSION_AUTHORIZATION",
             "allowed_software_fallback": "exclude unresolved material and preserve explicit boundary"}
            for item, subject in USER_ACTION_SUBJECTS.items()
        ],
        "software_release_readiness": "NOT_YET_EVALUATED",
        "final_competition_submission_authorization": "USER_ACTION_REQUIRED",
    }


def _old_authority_baseline() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for relative in OLD_AUTHORITY_SCOPES:
        path = ROOT / relative
        files = [path] if path.is_file() else sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else []
        if not files:
            errors.append(f"missing old authority scope: {relative}")
            continue
        for item in files:
            records.append({"path": item.relative_to(ROOT).as_posix(), "sha256": sha256_file(item)})
    return {
        "schema_version": "g3-g-old-authority-baseline-v1",
        "status": "PASS" if not errors else "FAIL", "source_baseline": git_output("rev-parse", "origin/main"),
        "scope_count": len(OLD_AUTHORITY_SCOPES), "file_count": len(records), "errors": errors,
        "records": records, "frozen_evidence_roots": {
            name: {"path": relative, "sha256sums_sha256": digest}
            for name, (relative, digest) in AUTHORITY_ROOTS.items()
        },
    }


def build_authority() -> dict[str, Any]:
    authority = _authority_inventory()
    inventory = _release_inventory()
    contract = _release_contract()
    exclusion = _exclusion_policy()
    user_actions = _user_actions()
    write_json(RELEASE_ROOT / "release_authority.json", authority)
    write_json(RELEASE_ROOT / "release_inventory.json", inventory)
    write_json(RELEASE_ROOT / "release_contract.json", contract)
    write_json(RELEASE_ROOT / "release_exclusion_policy.json", exclusion)
    write_json(RELEASE_ROOT / "user_action_release_gate.json", user_actions)
    write_json(RELEASE_ROOT / "old_authority_baseline.json", _old_authority_baseline())
    write_text(RELEASE_ROOT / "release_readiness.md", """# G3-G release readiness\n\nThis delivery layer validates cold-start reproducibility, canonical staging, deterministic release metadata, and clean extraction. It does not reopen Final Feature Freeze.\n\nThe mandatory path is offline, keyless, CPU_SIM-only, and no-NPU. `SOFTWARE_RELEASE_READY` is not `FINAL_SUBMISSION_AUTHORIZED`. License and copyright findings are an inventory and risk audit, not legal authorization. Controlled material is excluded unless explicitly authorized.\n\nCurrent G3-G-A state: release authority is complete; software readiness is not yet evaluated; final competition submission authorization remains `USER_ACTION_REQUIRED`.\n""")
    return validate_authority()


def validate_authority() -> dict[str, Any]:
    errors: list[str] = []
    required = ["release_authority.json", "release_inventory.json", "release_contract.json", "release_exclusion_policy.json", "release_readiness.md", "user_action_release_gate.json", "old_authority_baseline.json"]
    for name in required:
        if not (RELEASE_ROOT / name).is_file():
            errors.append(f"missing artifact: {name}")
    if errors:
        return {"schema_version": "g3-g-release-authority-validation-v1", "status": "FAIL", "errors": errors}
    authority = read_json(RELEASE_ROOT / "release_authority.json")
    inventory = read_json(RELEASE_ROOT / "release_inventory.json")
    contract = read_json(RELEASE_ROOT / "release_contract.json")
    gate = read_json(RELEASE_ROOT / "user_action_release_gate.json")
    old = read_json(RELEASE_ROOT / "old_authority_baseline.json")
    if old.get("status") != "PASS" or old.get("errors"):
        errors.extend(old.get("errors", ["old authority baseline failed"]))
    for name, (relative, expected) in AUTHORITY_ROOTS.items():
        current = verify_sha256sums(ROOT / relative)
        if current.get("status") != "PASS" or current.get("sha256sums_sha256") != expected:
            errors.append(f"authority mismatch: {name}")
    if inventory.get("unknown_source_count") != 0:
        errors.append("release inventory contains unknown source")
    if contract.get("canonical_sequence") != MANDATORY_ENTRY_POINTS:
        errors.append("canonical cold-start sequence drift")
    if contract.get("controlled_material_policy") != "EXCLUDE_UNLESS_EXPLICITLY_AUTHORIZED":
        errors.append("controlled-material policy drift")
    if contract.get("final_authorization_boundary") != "SOFTWARE_RELEASE_READY != FINAL_SUBMISSION_AUTHORIZED":
        errors.append("dual-state boundary drift")
    if gate.get("item_count") != len(USER_ACTION_SUBJECTS) or gate.get("status") != "USER_ACTION_REQUIRED":
        errors.append("user-action gate mismatch")
    for record in old.get("records", []):
        path = ROOT / record["path"]
        if not path.is_file() or sha256_file(path) != record["sha256"]:
            errors.append(f"old authority baseline mismatch: {record['path']}")
    portable = portable_text_findings([RELEASE_ROOT / name for name in required], base=ROOT)
    errors.extend(f"non-portable release contract: {row}" for row in portable)
    return {
        "schema_version": "g3-g-release-authority-validation-v1", "status": "PASS" if not errors else "FAIL",
        "errors": errors, "authority_root_count": len(AUTHORITY_ROOTS),
        "tracked_file_count": inventory.get("tracked_file_count"), "user_action_count": gate.get("item_count"),
        "release_authority_status": "COMPLETED" if not errors else "FAIL",
        "software_release_readiness": "NOT_YET_EVALUATED",
        "final_competition_submission_authorization": "USER_ACTION_REQUIRED",
        "sentinel": "G3_G_RELEASE_AUTHORITY_OK" if not errors else None,
    }
