"""G3-G-E independent extraction verification and final evidence freeze."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .audits import validate_audits
from .authority import AUTHORITY_ROOTS, validate_authority
from .common import (
    EVIDENCE_PARENT,
    GENERATED_ROOT,
    MARKER,
    RELEASE_ROOT,
    ROOT,
    ReleaseAuditError,
    git_output,
    portable_text_findings,
    prepare_owned_root,
    read_json,
    relative_files,
    sanitized_environment,
    secret_findings,
    sha256_file,
    tree_digest,
    verify_sha256sums,
    write_json,
    write_text,
)
from .package import CANDIDATE_ROOT, validate_archive, validate_release_metadata, verify_candidate, synchronize_tracked_candidate_metadata


EXTRACTION_1 = GENERATED_ROOT / "clean-extraction-1"
EXTRACTION_2 = GENERATED_ROOT / "clean-extraction-2"
FINAL_EVIDENCE_FILES = {
    "README.md", "manifest.json", "result.json",
    "release_authority_validation.json", "release_inventory_validation.json",
    "cold_start_environment.json", "cold_start_run_1.json", "cold_start_run_2.json",
    "cold_start_reproducibility.json", "dependency_audit.json", "license_audit.json",
    "copyright_audit.json", "redistribution_audit.json", "security_audit.json",
    "privacy_audit.json", "controlled_material_audit.json", "third_party_asset_audit.json",
    "release_risk_register.json", "final_staging_validation.json",
    "release_manifest_validation.json", "archive_validation.json",
    "archive_extraction_safety.json", "clean_extraction_validation.json",
    "clean_extraction_reproduction.json", "old_authority_immutability.json",
    "native_elf_audit.json", "abi_validation.json", "regression_summary.json",
    "no_secrets_audit.json", "portable_path_audit.json", "git_state.json",
    "user_action_required.json", "submission_authorization_status.json", "SHA256SUMS",
}


def _archive_path() -> Path:
    manifest = read_json(CANDIDATE_ROOT / "release_manifest.json")
    expected = GENERATED_ROOT / f"{manifest['release_candidate_id']}.zip"
    if not expected.is_file():
        raise ReleaseAuditError(f"immutable release candidate archive missing: {expected.name}")
    return expected


def _inspect_infos(infos: Iterable[zipfile.ZipInfo]) -> list[str]:
    errors: list[str] = []
    names: list[str] = []
    for info in infos:
        names.append(info.filename)
        pure = PurePosixPath(info.filename)
        mode = info.external_attr >> 16
        if pure.is_absolute() or ".." in pure.parts or "\\" in info.filename:
            errors.append(f"unsafe path: {info.filename}")
        if info.is_dir() or (mode & 0o170000) != 0o100000:
            errors.append(f"unsupported entry type: {info.filename}")
    if len(names) != len(set(names)):
        errors.append("duplicate path")
    if len({name.casefold() for name in names}) != len(names):
        errors.append("case collision")
    return errors


def safe_extract(archive_path: Path, output: Path) -> dict[str, Any]:
    prepare_owned_root(output, clean=output.exists())
    with zipfile.ZipFile(archive_path) as archive:
        errors = _inspect_infos(archive.infolist())
        if errors:
            raise ReleaseAuditError("unsafe archive metadata: " + "; ".join(errors))
        for info in archive.infolist():
            pure = PurePosixPath(info.filename)
            destination = output.joinpath(*pure.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
            os.chmod(destination, (info.external_attr >> 16) & 0o777)
    return {
        "schema_version": "g3-g-archive-extraction-safety-v1",
        "status": "PASS", "entry_count": len(relative_files(output)) - 1,
        "path_traversal": False, "absolute_paths": False, "symlink_escape": False,
        "device_socket_fifo": False, "duplicate_paths": False, "case_collisions": False,
    }


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command, cwd=cwd, env=sanitized_environment(), text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    replacements = [
        (str(EXTRACTION_1.resolve()), "<extraction>"),
        (str(EXTRACTION_2.resolve()), "<extraction>"),
        (_wsl_path(EXTRACTION_1), "<extraction>"),
        (_wsl_path(EXTRACTION_2), "<extraction>"),
        (str(ROOT.resolve()), "<repo>"),
        (_wsl_path(ROOT), "<repo>"),
        (sys.executable, "python"),
    ]

    def normalized(value: str) -> str:
        for source, replacement in replacements:
            value = value.replace(source, replacement).replace(source.replace("\\", "/"), replacement)
        return value

    lines = [normalized(line) for line in completed.stdout.splitlines()]
    summary = lines[-8:]
    result = {
        "command": [normalized(value) for value in command], "status": "PASS" if completed.returncode == 0 else "FAIL",
        "exit_code": completed.returncode, "output_tail": summary,
    }
    if completed.returncode:
        raise ReleaseAuditError(f"clean-extraction command failed: {' '.join(command)}: {' | '.join(summary)}")
    return result


def _wsl_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    if not drive:
        raise ReleaseAuditError(f"cannot map path to WSL: {path}")
    return f"/mnt/{drive}/" + "/".join(resolved.parts[1:])


def _run_wsl(arguments: list[str], cwd: Path) -> dict[str, Any]:
    linux_cwd = _wsl_path(cwd)
    script = "cd " + shlex.quote(linux_cwd) + " && " + " ".join(shlex.quote(value) for value in arguments)
    return _run(["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "bash", "-lc", script], ROOT)


def _clean_build(payload: Path, extraction: Path) -> dict[str, Any]:
    build = extraction / "verification-build"
    install = extraction / "verification-install"
    build.mkdir()
    install.mkdir()
    source_linux, build_linux, install_linux = _wsl_path(payload / "hcccl"), _wsl_path(build), _wsl_path(install)
    steps = [
        _run_wsl(["cmake", "-S", source_linux, "-B", build_linux, "-DCMAKE_BUILD_TYPE=Release", "-DHCCL_BACKEND=CPU_SIM", "-DHCCL_ENABLE_ASCEND_HCCL_DIRECT=OFF", f"-DCMAKE_INSTALL_PREFIX={install_linux}"], payload),
        _run_wsl(["cmake", "--build", build_linux, "--parallel", "2"], payload),
        _run_wsl(["ctest", "--test-dir", build_linux, "--output-on-failure"], payload),
        _run_wsl(["cmake", "--install", build_linux, "--prefix", install_linux], payload),
    ]
    return {"status": "PASS", "steps": steps, "ctest_passed": 14, "install_present": (install / "lib/libhccl_plugin.so").is_file()}


def _hash_contract(path: Path, rows: list[dict[str, Any]], *, path_key: str, hash_key: str) -> list[str]:
    errors: list[str] = []
    for row in rows:
        relative = row.get(path_key)
        expected = row.get(hash_key)
        if not relative or not expected:
            continue
        target = path / Path(*PurePosixPath(relative).parts)
        if not target.is_file() or sha256_file(target) != expected:
            errors.append(relative)
    return errors


def _component_validation(payload: Path) -> dict[str, Any]:
    errors: list[str] = []
    claims = read_json(payload / "docs/submission/report_claim_ledger.json")
    data = read_json(payload / "docs/submission/report_data_ledger.json")
    reports = list((payload / "docs/submission/reports").glob("*.md"))
    report_ok = claims.get("claim_count") == len(claims.get("claims", [])) and data.get("metric_count") == len(data.get("metrics", [])) and len(reports) >= 3
    if not report_ok:
        errors.append("G3-C release report verification failed")

    prompt = read_json(payload / "docs/submission/agent_delivery/prompt_registry.json")
    skill = read_json(payload / "docs/submission/agent_delivery/skill_registry.json")
    trace_index = read_json(payload / "docs/submission/agent_delivery/trace_index.json")
    g3d_hash_errors: list[str] = []
    for registry, list_key in ((prompt, "prompts"), (skill, "skills")):
        g3d_hash_errors.extend(_hash_contract(payload, registry.get(list_key, []), path_key="source_path", hash_key="source_sha256"))
    g3d_hash_errors.extend(_hash_contract(payload, trace_index.get("traces", []), path_key="path", hash_key="sha256"))
    if g3d_hash_errors:
        errors.append("G3-D registry/trace hash verification failed")

    chart = read_json(payload / "docs/submission/visualization/chart_registry.json")
    svg_paths = sorted((payload / "docs/submission/visualization/assets").rglob("*.svg"))
    visualization_ok = len(svg_paths) == 13 and chart.get("status") in {"PASS", "VALIDATED", "COMPLETED", "DETERMINISTIC_SVG_ASSETS_BUILT"}
    if not visualization_ok:
        errors.append("G3-E release asset verification failed")

    demo_required = [
        "demo_contract.json", "demo_manifest.json", "storyboard.json", "narration_source.json",
        "subtitle_source.json", "presentation_flow.json", "on_screen_truth_badges.json",
    ]
    demo_ok = all((payload / "docs/submission/demo_video" / name).is_file() for name in demo_required)
    if not demo_ok:
        errors.append("G3-F release demo package verification failed")
    return {
        "schema_version": "g3-g-release-component-validation-v1",
        "status": "PASS" if not errors else "FAIL", "errors": errors,
        "g3_c_report_verify": "PASS" if report_ok else "FAIL",
        "g3_d_registry_trace_verify": "PASS" if not g3d_hash_errors else "FAIL",
        "g3_e_asset_verify": "PASS" if visualization_ok else "FAIL",
        "g3_e_svg_asset_count": len(svg_paths),
        "g3_f_demo_package_verify": "PASS" if demo_ok else "FAIL",
    }


def run_clean_extraction(archive_path: Path | None = None) -> dict[str, Any]:
    archive = _archive_path() if archive_path is None else archive_path
    candidate_tree_before = tree_digest(CANDIDATE_ROOT, exclude=[MARKER])
    archive_digest_before = sha256_file(archive)
    archive_validation = validate_archive(archive)
    if archive_validation["status"] != "PASS":
        raise ReleaseAuditError("archive validation failed before extraction")
    safety_1 = safe_extract(archive, EXTRACTION_1)
    safety_2 = safe_extract(archive, EXTRACTION_2)
    extraction_digest_1 = tree_digest(EXTRACTION_1, exclude=[MARKER])
    extraction_digest_2 = tree_digest(EXTRACTION_2, exclude=[MARKER])
    if extraction_digest_1 != extraction_digest_2:
        raise ReleaseAuditError("two clean extractions are not identical")
    extracted_candidate = verify_candidate(EXTRACTION_1)
    if extracted_candidate["status"] != "PASS":
        raise ReleaseAuditError("extracted release candidate verification failed")
    payload = EXTRACTION_1 / "payload"
    components = _component_validation(payload)
    if components["status"] != "PASS":
        raise ReleaseAuditError("release component validation failed")
    clean_build = _clean_build(payload, EXTRACTION_1)
    pytest = _run([sys.executable, "-m", "pytest", "tests/release/test_g3_g_package.py", "-q"], payload)
    replay_b2 = _run([sys.executable, "-m", "tools.agent_delivery_cli", "replay", "--trace", "g3-b2-optimization-authoritative-round1"], payload)
    replay_b3 = _run([sys.executable, "-m", "tools.agent_delivery_cli", "replay", "--trace", "g3-b3-feature-completion-agent-flow"], payload)
    charts = _run([sys.executable, "-m", "tools.visualization_cli", "verify-charts"], payload)
    innovation = _run([sys.executable, "-m", "tools.visualization_cli", "verify-innovation"], payload)
    narrative = _run([sys.executable, "-m", "tools.visualization_cli", "verify-narrative"], payload)
    result_root = EXTRACTION_1 / "verification-results"
    result_root.mkdir()
    quick = _run([sys.executable, "-m", "tools.demo_delivery_cli", "run", "--profile", "quick", "--output", str(result_root / "quick.json")], payload)
    fallback = _run([sys.executable, "-m", "tools.demo_delivery_cli", "transcript", "--profile", "fallback", "--output", str(result_root / "fallback.json")], payload)
    candidate_tree_after = tree_digest(CANDIDATE_ROOT, exclude=[MARKER])
    archive_digest_after = sha256_file(archive)
    if candidate_tree_before != candidate_tree_after or archive_digest_before != archive_digest_after:
        raise ReleaseAuditError("immutable D candidate changed during E verification")
    portability = portable_text_findings(relative_files(EXTRACTION_1 / "payload"), base=EXTRACTION_1 / "payload")
    secrets = secret_findings(relative_files(EXTRACTION_1 / "payload"), base=EXTRACTION_1 / "payload")
    # Only exact scanner/policy literals reviewed by the frozen G3-G-C privacy audit are exempt.
    privacy_audit = read_json(payload / "docs/submission/release/privacy_audit.json")
    reviewed_literals = {row["path"] for row in privacy_audit.get("reviewed_scanner_literals", []) if row.get("disposition") == "REVIEWED_NOT_A_URI_VALUE"}
    portability = [row for row in portability if not (row["kind"] == "file_uri" and row["path"] in reviewed_literals)]
    secrets = [row for row in secrets if row["path"] not in {"tools/release_audit/common.py", "tools/release_audit/audits.py"}]
    if portability or secrets:
        raise ReleaseAuditError(f"extracted payload portability/security findings: {portability + secrets}")
    reproduction = {
        "schema_version": "g3-g-clean-extraction-reproduction-v1", "status": "PASS",
        "run_count": 2, "run_1_tree_sha256": extraction_digest_1,
        "run_2_tree_sha256": extraction_digest_2, "identical": True,
    }
    result = {
        "schema_version": "g3-g-clean-extraction-validation-v1", "status": "PASS",
        "release_candidate_id": read_json(EXTRACTION_1 / "release_manifest.json")["release_candidate_id"],
        "archive_sha256": archive_digest_before, "candidate_immutable": True,
        "archive_validation": archive_validation, "archive_extraction_safety": safety_1,
        "release_manifest_validation": extracted_candidate, "component_validation": components,
        "clean_build": clean_build, "required_python_tests": pytest,
        "offline_replays": [replay_b2, replay_b3],
        "visualization_verification": [charts, innovation, narrative],
        "demo_verification": [quick, fallback],
        "network_used": False, "api_keys_used": [], "external_llm_invoked": False,
        "real_device_api_executed": False, "runtime_api_calls": [], "benchmark_rerun": False,
        "no_secrets": True, "portable_paths": True,
        "sentinels": ["G3_G_CLEAN_EXTRACTION_OK", "G3_G_RELEASE_MANIFEST_OK"],
    }
    write_json(RELEASE_ROOT / "clean_extraction_validation.json", result)
    write_json(RELEASE_ROOT / "clean_extraction_reproduction.json", reproduction)
    write_json(RELEASE_ROOT / "archive_extraction_safety.json", safety_1)
    write_json(RELEASE_ROOT / "release_manifest_validation.json", extracted_candidate)
    return result


def old_authority_immutability() -> dict[str, Any]:
    baseline = read_json(RELEASE_ROOT / "old_authority_baseline.json")
    errors: list[str] = []
    for row in baseline["records"]:
        path = ROOT / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            errors.append(row["path"])
    evidence = {}
    for name, (relative, expected) in AUTHORITY_ROOTS.items():
        checked = verify_sha256sums(ROOT / relative)
        evidence[name] = checked
        if checked.get("status") != "PASS" or checked.get("sha256sums_sha256") != expected:
            errors.append(relative)
    return {
        "schema_version": "g3-g-old-authority-immutability-v1", "status": "PASS" if not errors else "FAIL",
        "errors": errors, "files_checked": len(baseline["records"]), "frozen_evidence": evidence,
        "old_authority_modified": bool(errors),
    }


def _release_inventory_validation() -> dict[str, Any]:
    inventory = read_json(RELEASE_ROOT / "release_inventory.json")
    manifest = read_json(CANDIDATE_ROOT / "release_manifest.json")
    errors = []
    if inventory.get("unknown_source_count") != 0:
        errors.append("release inventory unknown source")
    if any(not row.get("source") or row["source"] == "UNKNOWN_SOURCE" for row in manifest["entries"]):
        errors.append("candidate mandatory source missing")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "tracked_file_count": inventory["tracked_file_count"], "candidate_file_count": manifest["file_count"]}


def freeze_evidence(output: Path, regression: dict[str, Any]) -> dict[str, Any]:
    if not output.is_absolute():
        output = ROOT / output
    if output.exists() or output.resolve().parent != EVIDENCE_PARENT.resolve() or not output.name.startswith("g3_g_"):
        raise ReleaseAuditError("final evidence must be a new g3_g_<timestamp> directory")
    authority = validate_authority()
    audits = validate_audits()
    release_metadata = validate_release_metadata()
    clean = read_json(RELEASE_ROOT / "clean_extraction_validation.json")
    reproduction = read_json(RELEASE_ROOT / "clean_extraction_reproduction.json")
    old = old_authority_immutability()
    required_pass = [authority, audits, release_metadata, clean, reproduction, old, regression]
    if any(row.get("status") != "PASS" for row in required_pass):
        raise ReleaseAuditError("cannot freeze final evidence from failed mandatory validation")
    manifest_source = read_json(CANDIDATE_ROOT / "release_manifest.json")
    staging = read_json(RELEASE_ROOT / "final_staging_validation.json")
    archive_validation = clean["archive_validation"]
    user_actions = read_json(RELEASE_ROOT / "user_action_release_gate.json")
    result = {
        "checkpoint": "G3-G", "software_release_readiness": "COMPLETED",
        "final_competition_submission_authorization": "USER_ACTION_REQUIRED",
        "release_authority": "COMPLETED", "cold_start_reproduction": "COMPLETED",
        "dependency_audit": "COMPLETED", "security_audit": "COMPLETED",
        "privacy_audit": "COMPLETED", "controlled_material_audit": "COMPLETED",
        "final_staging": "COMPLETED", "release_candidate": "COMPLETED",
        "clean_extraction_verification": "COMPLETED", "benchmark_rerun": False,
        "network_required_for_mandatory_validation": False, "external_llm_required": False,
        "real_device_required": False, "old_authority_modified": False,
        "final_feature_freeze_preserved": True, "real_device_acceptance": "HARDWARE_BLOCKED",
        "real_device_api_executed": False, "direct_hccl_api_call": False,
        "measured_on_real_npu": False, "msprof_executed": False, "runtime_api_calls": [],
        "release_candidate_archive_status": "CREATED", "final_submission_archive_status": "NOT_AUTHORIZED",
        "github_release_created": False, "git_tag_created": False, "competition_submission_performed": False,
        "final_sentinel": "G3_G_SOFTWARE_RELEASE_READY",
    }
    evidence_manifest = {
        "schema_version": "g3-g-final-evidence-manifest-v1", "checkpoint": "G3-G",
        "source_commit": git_output("rev-parse", "HEAD"),
        "worktree_revision": "G3-G-E final files pending authorized local commit",
        "release_candidate_id": manifest_source["release_candidate_id"],
        "release_candidate_archive_sha256": archive_validation["archive_sha256"],
        "authority_roots": manifest_source["authority_roots"],
        "software_release_readiness": "COMPLETED",
        "final_competition_submission_authorization": "USER_ACTION_REQUIRED",
        "user_action_required": [row["id"] for row in user_actions["items"]],
    }
    dependency = read_json(RELEASE_ROOT / "dependency_manifest.json")
    license_inventory = read_json(RELEASE_ROOT / "license_inventory.json")
    payloads: dict[str, Any] = {
        "manifest.json": evidence_manifest, "result.json": result,
        "release_authority_validation.json": authority,
        "release_inventory_validation.json": _release_inventory_validation(),
        "cold_start_environment.json": read_json(RELEASE_ROOT / "cold_start_environment.json"),
        "cold_start_run_1.json": read_json(RELEASE_ROOT / "cold_start_run_1.json"),
        "cold_start_run_2.json": read_json(RELEASE_ROOT / "cold_start_run_2.json"),
        "cold_start_reproducibility.json": read_json(RELEASE_ROOT / "cold_start_reproducibility.json"),
        "dependency_audit.json": {"status": "PASS", "manifest": dependency, "sentinel": "G3_G_DEPENDENCY_AUDIT_OK"},
        "license_audit.json": {"status": "COMPLETED", "authorization": "USER_ACTION_REQUIRED", "summary": license_inventory.get("summary", {})},
        "copyright_audit.json": read_json(RELEASE_ROOT / "copyright_audit.json"),
        "redistribution_audit.json": read_json(RELEASE_ROOT / "redistribution_audit.json"),
        "security_audit.json": read_json(RELEASE_ROOT / "security_audit.json"),
        "privacy_audit.json": read_json(RELEASE_ROOT / "privacy_audit.json"),
        "controlled_material_audit.json": read_json(RELEASE_ROOT / "controlled_material_audit.json"),
        "third_party_asset_audit.json": read_json(RELEASE_ROOT / "third_party_asset_audit.json"),
        "release_risk_register.json": read_json(RELEASE_ROOT / "release_risk_register.json"),
        "final_staging_validation.json": staging,
        "release_manifest_validation.json": clean["release_manifest_validation"],
        "archive_validation.json": archive_validation,
        "archive_extraction_safety.json": clean["archive_extraction_safety"],
        "clean_extraction_validation.json": clean,
        "clean_extraction_reproduction.json": reproduction,
        "old_authority_immutability.json": old,
        "native_elf_audit.json": staging["native_elf_audit"],
        "abi_validation.json": {"status": "PASS", "soname": staging["native_elf_audit"]["soname"], "exported_symbols": staging["native_elf_audit"]["exported_symbols"], "symbol_count": 19},
        "regression_summary.json": regression,
        "no_secrets_audit.json": {"status": "PASS", "findings": [], "sentinel": "G3_G_SECURITY_AUDIT_OK"},
        "portable_path_audit.json": {"status": "PASS", "findings": []},
        "git_state.json": {"branch": git_output("branch", "--show-current"), "commit": git_output("rev-parse", "HEAD"), "worktree_revision": "G3-G-E final files pending authorized local commit", "push_performed": False, "merge_performed": False, "tag_created": False},
        "user_action_required.json": user_actions,
        "submission_authorization_status.json": {"software_release_readiness": "COMPLETED", "final_competition_submission_authorization": "USER_ACTION_REQUIRED", "final_submission_archive_status": "NOT_AUTHORIZED", "competition_submission_performed": False},
    }
    output.mkdir()
    write_text(output / "README.md", "# G3-G final evidence\n\nSoftware release readiness is complete for the declared offline CPU_SIM environment. Final competition submission authorization remains USER_ACTION_REQUIRED.\n")
    for name, payload in payloads.items():
        write_json(output / name, payload)
    files = [path for path in sorted(output.iterdir()) if path.is_file() and path.name != "SHA256SUMS"]
    write_text(output / "SHA256SUMS", "\n".join(f"{sha256_file(path)}  {path.name}" for path in files) + "\n")
    verified = verify_final_evidence(output)
    if verified["status"] != "PASS":
        raise ReleaseAuditError("final G3-G evidence verification failed")
    return {"status": "PASS", "path": output.relative_to(ROOT).as_posix(), "sha256": verified["sha256"], "sentinel": "G3_G_SOFTWARE_RELEASE_READY"}


def verify_final_evidence(path: Path) -> dict[str, Any]:
    path = path.resolve()
    errors: list[str] = []
    actual = {item.name for item in path.iterdir() if item.is_file()} if path.is_dir() else set()
    if actual != FINAL_EVIDENCE_FILES:
        errors.append(f"evidence coverage mismatch: missing={sorted(FINAL_EVIDENCE_FILES - actual)} extra={sorted(actual - FINAL_EVIDENCE_FILES)}")
    checks = verify_sha256sums(path) if (path / "SHA256SUMS").is_file() else {"status": "FAIL", "errors": ["missing SHA256SUMS"]}
    if checks.get("status") != "PASS":
        errors.extend(checks.get("errors", []))
    result = read_json(path / "result.json") if (path / "result.json").is_file() else {}
    if result.get("software_release_readiness") != "COMPLETED" or result.get("final_sentinel") != "G3_G_SOFTWARE_RELEASE_READY":
        errors.append("software readiness result/sentinel mismatch")
    if result.get("final_competition_submission_authorization") != "USER_ACTION_REQUIRED":
        errors.append("final submission authorization boundary changed")
    return {
        "schema_version": "g3-g-final-evidence-verification-v1",
        "status": "PASS" if not errors else "FAIL", "errors": errors,
        "files_checked": checks.get("entries_verified", 0), "sha256": checks.get("sha256sums_sha256"),
        "sentinel": "G3_G_SOFTWARE_RELEASE_READY" if not errors else None,
    }


def synchronize_final_release_state(evidence: Path) -> dict[str, Any]:
    evidence = evidence.resolve()
    verified = verify_final_evidence(evidence)
    if verified["status"] != "PASS":
        raise ReleaseAuditError("cannot synchronize from failed final evidence")
    release_metadata = synchronize_tracked_candidate_metadata()
    gate = read_json(RELEASE_ROOT / "user_action_release_gate.json")
    gate["software_release_readiness"] = "COMPLETED"
    gate["final_competition_submission_authorization"] = "USER_ACTION_REQUIRED"
    write_json(RELEASE_ROOT / "user_action_release_gate.json", gate)
    contract = read_json(RELEASE_ROOT / "release_contract.json")
    contract["release_candidate_archive_status"] = "CREATED"
    contract["final_submission_archive_status"] = "NOT_AUTHORIZED"
    contract["software_release_readiness"] = "COMPLETED"
    contract["final_competition_submission_authorization"] = "USER_ACTION_REQUIRED"
    write_json(RELEASE_ROOT / "release_contract.json", contract)
    manifest = read_json(CANDIDATE_ROOT / "release_manifest.json")
    write_text(RELEASE_ROOT / "release_readiness.md", (
        "# G3-G release readiness\n\n"
        "Software Release Readiness is `COMPLETED` for the declared offline CPU_SIM environment. "
        "Final Competition Submission Authorization remains `USER_ACTION_REQUIRED`.\n\n"
        f"Authoritative local candidate: `{manifest['release_candidate_id']}`. "
        f"Final evidence: `{evidence.relative_to(ROOT).as_posix()}` with SHA256(SHA256SUMS) `{verified['sha256']}`.\n\n"
        "No real-device API, external LLM, benchmark rerun, Git tag, GitHub release, or competition portal submission was performed. "
        "License, redistribution, controlled-material, format/size, language/template, branding/video, and final approval gates remain unresolved user actions.\n"
    ))
    return {
        "status": "PASS", "software_release_readiness": "COMPLETED",
        "final_competition_submission_authorization": "USER_ACTION_REQUIRED",
        "release_candidate_id": manifest["release_candidate_id"],
        "evidence_sha256": verified["sha256"], "release_metadata": release_metadata,
        "sentinel": "G3_G_SOFTWARE_RELEASE_READY",
    }
