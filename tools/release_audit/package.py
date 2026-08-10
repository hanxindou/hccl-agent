"""G3-G-D canonical staging and deterministic release-candidate packaging."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from tools.demo_delivery.finalize import build_staging
from tools.submission_cli.core import DEFAULT_STAGE, verify_stage

from .common import (
    GENERATED_ROOT,
    MARKER,
    RELEASE_ROOT,
    ROOT,
    ReleaseAuditError,
    git_output,
    prepare_owned_root,
    read_json,
    relative_files,
    sha256_file,
    tree_digest,
    write_json,
    write_text,
)


CANDIDATE_ROOT = GENERATED_ROOT / "candidate"
PAYLOAD_ROOT = CANDIDATE_ROOT / "payload"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
TRACKED_OUTPUTS = {
    "final_staging_inventory.json",
    "release_manifest.json",
    "release_manifest.md",
    "archive_contract.json",
    "archive_readiness.md",
    "release_candidate_readme.md",
    "final_staging_validation.json",
    "release_candidate_validation.json",
    "archive_reproducibility.json",
}


def _source_revision() -> str:
    """Return an honest source identity before or after the checkpoint commit."""
    if git_output("status", "--short", "--untracked-files=no"):
        return "PENDING_G3_G_D_AUTHORIZED_LOCAL_COMMIT"
    return git_output("rev-parse", "HEAD")


def _copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ReleaseAuditError(f"symlink is not allowed in release staging: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _manifest_entry(path: Path, stage_path: str, source_path: str, role: str) -> dict[str, Any]:
    return {
        "artifact_id": "G3G-" + hashlib.sha256(stage_path.encode("utf-8")).hexdigest()[:12].upper(),
        "source_path": source_path,
        "staging_path": stage_path,
        "category": "RELEASE_DELIVERY",
        "artifact_role": role,
        "include": True,
        "required": True,
        "generated": False,
        "source_commit": _source_revision(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "license_status": "USER_ACTION_REQUIRED",
        "confidentiality": "SUBMISSION_ARTIFACT",
        "redistribution_status": "USER_ACTION_REQUIRED",
        "execution_status": "NOT_EXECUTED_AS_STAGED_FILE",
        "evidence_level": "E1_DOCUMENTED",
        "claim_label": "REAL_DEVICE_NOT_EXECUTED",
        "owner_checkpoint": "G3-G",
        "known_limitations": [
            "local release-candidate content only",
            "legal and final submission authorization remain USER_ACTION_REQUIRED",
        ],
    }


def _refresh_stage_metadata(stage: Path, entries: list[dict[str, Any]]) -> None:
    entries.sort(key=lambda row: row["staging_path"])
    manifest_path = stage / "MANIFEST.json"
    manifest = read_json(manifest_path)
    manifest["entries"] = entries
    manifest["g3_g_overlay"] = {
        "status": "PASS",
        "owner_checkpoint": "G3-G",
        "canonical_staging_reused": True,
        "parallel_staging_framework_created": False,
        "release_candidate_only": True,
        "final_submission_authorization": "USER_ACTION_REQUIRED",
    }
    write_json(manifest_path, manifest)
    write_json(stage / "release/submission_inclusion_manifest.json", manifest)
    write_json(stage / "release/STAGING_SIZE_REPORT.json", {
        "payload_file_count": len(entries),
        "payload_total_size_bytes": sum(row["size_bytes"] for row in entries),
        "platform_limit": "USER_ACTION_REQUIRED",
    })
    status_path = stage / "STATUS.json"
    status_payload = read_json(status_path)
    status_payload.update({
        "g3_g_final_staging": "COMPLETED",
        "release_candidate": "COMPLETED",
        "release_candidate_archive_status": "CREATED",
        "final_submission_archive_status": "NOT_AUTHORIZED",
        "final_competition_submission_authorization": "USER_ACTION_REQUIRED",
        "final_release_created": False,
        "git_tag_created": False,
        "github_release_created": False,
        "competition_submission_performed": False,
        "real_device_api_executed": False,
        "runtime_api_calls": [],
    })
    write_json(status_path, status_payload)
    for row in entries:
        if row["staging_path"] == "STATUS.json":
            row["sha256"] = sha256_file(status_path)
            row["size_bytes"] = status_path.stat().st_size
            break
    manifest["entries"] = entries
    write_json(manifest_path, manifest)
    write_json(stage / "release/submission_inclusion_manifest.json", manifest)
    checksum_lines = [
        f"{sha256_file(path)}  {path.relative_to(stage).as_posix()}"
        for path in relative_files(stage) if path.name != "SHA256SUMS"
    ]
    write_text(stage / "SHA256SUMS", "\n".join(checksum_lines) + "\n")


def _overlay_release_delivery(stage: Path) -> None:
    manifest = read_json(stage / "MANIFEST.json")
    entries = list(manifest["entries"])
    sources: list[tuple[Path, str, str]] = []
    for source in relative_files(RELEASE_ROOT):
        if source.name in TRACKED_OUTPUTS:
            continue
        destination = f"docs/submission/release/{source.relative_to(RELEASE_ROOT).as_posix()}"
        sources.append((source, destination, "G3_G_RELEASE_AUTHORITY_OR_AUDIT"))
    for base, stage_base, role in (
        (ROOT / "tools/release_audit", "tools/release_audit", "G3_G_RELEASE_TOOLING"),
        (ROOT / "tests/release", "tests/release", "G3_G_RELEASE_TEST"),
    ):
        for source in relative_files(base):
            if source.suffix == ".py":
                sources.append((source, f"{stage_base}/{source.relative_to(base).as_posix()}", role))
    sources.append((ROOT / "tools/release_cli.py", "tools/release_cli.py", "G3_G_RELEASE_CLI"))
    for source, stage_path, role in sorted(sources, key=lambda item: item[1]):
        destination = stage / Path(*PurePosixPath(stage_path).parts)
        _copy_file(source, destination)
        entries = [row for row in entries if row["staging_path"] != stage_path]
        entries.append(_manifest_entry(destination, stage_path, source.relative_to(ROOT).as_posix(), role))
    _refresh_stage_metadata(stage, entries)


def _authority_roots() -> list[dict[str, str]]:
    authority = read_json(RELEASE_ROOT / "release_authority.json")
    levels = {"g3_c": "L2", "g3_d": "L3", "g3_e": "L4", "g3_f": "L5", "g3_b3": "L6", "g3_b2": "L7"}
    return sorted(
        ({
            "authority_level": levels[name],
            "authority_id": name,
            "path": row["root"],
            "sha256": row["sha256sums_sha256"],
        } for name, row in authority["authority_roots"].items()),
        key=lambda row: (row["authority_level"], row["path"]),
    )


def _release_entries(payload: Path) -> list[dict[str, Any]]:
    stage_manifest = read_json(payload / "MANIFEST.json")
    by_path = {row["staging_path"]: row for row in stage_manifest["entries"]}
    entries: list[dict[str, Any]] = []
    for path in relative_files(payload):
        stage_relative = path.relative_to(payload).as_posix()
        archive_path = f"payload/{stage_relative}"
        staging = by_path.get(stage_relative)
        if staging:
            source = staging.get("source_path")
            authority_level = staging.get("owner_checkpoint", "MERGED_SOURCE")
            generated = bool(staging.get("generated"))
            license_status = staging.get("license_status", "USER_ACTION_REQUIRED")
            redistribution = staging.get("redistribution_status", "USER_ACTION_REQUIRED")
            role = staging.get("artifact_role", "STAGED_RELEASE_FILE")
            category = staging.get("category", "STAGED_RELEASE_FILE")
        else:
            source = "<generated-by-canonical-staging-builder>"
            authority_level = "G3-G"
            generated = True
            license_status = "NOT_APPLICABLE_GENERATED_METADATA"
            redistribution = "NOT_APPLICABLE_GENERATED_METADATA"
            role = "STAGING_METADATA"
            category = "RELEASE_METADATA"
        if not source or source == "UNKNOWN_SOURCE":
            raise ReleaseAuditError(f"mandatory release file has unknown source: {archive_path}")
        entries.append({
            "path": archive_path,
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
            "category": category,
            "source": source,
            "authority_level": authority_level,
            "generated_or_source": "GENERATED" if generated else "SOURCE",
            "license_status": license_status,
            "redistribution_status": redistribution,
            "controlled_material_status": "EXCLUDED_NOT_CONTROLLED",
            "required": True,
            "verification_role": role,
        })
    return sorted(entries, key=lambda row: row["path"])


def _candidate_manifest(payload: Path, candidate_id: str, archive_status: str) -> dict[str, Any]:
    entries = _release_entries(payload)
    user_actions = read_json(RELEASE_ROOT / "user_action_release_gate.json")
    return {
        "release_schema_version": "g3-g-release-manifest-v1",
        "source_commit": _source_revision(),
        "baseline_commit": git_output("rev-parse", "HEAD"),
        "worktree_revision": "G3-G-D tracked files pending authorized local commit" if _source_revision().startswith("PENDING_") else "COMMITTED",
        "release_candidate_id": candidate_id,
        "build_environment_class": "WINDOWS_HOST_WITH_WSL_UBUNTU_22_04_VALIDATION",
        "file_count": len(entries),
        "total_size": sum(row["size"] for row in entries),
        "authority_roots": _authority_roots(),
        "truth_boundary_summary": [
            "CPU_SIM_REFERENCE_PLUGIN",
            "SIMULATED_ONLY",
            "DIRECT_COMPILE_LINK_ONLY",
            "REAL_DEVICE_NOT_EXECUTED",
        ],
        "user_action_required": sorted(row["id"] for row in user_actions["items"] if row["status"] == "USER_ACTION_REQUIRED"),
        "software_release_readiness": "PENDING_INDEPENDENT_G3_G_E_VERIFICATION",
        "final_submission_authorization": "USER_ACTION_REQUIRED",
        "archive_status": archive_status,
        "release_candidate_archive_status": archive_status,
        "final_submission_archive_status": "NOT_AUTHORIZED",
        "manifest_self_entry_policy": "RELEASE_MANIFEST_METADATA_EXCLUDED_FROM_ENTRY_HASH_SET",
        "entries": entries,
    }


def _zip_info(relative: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(relative, FIXED_ZIP_TIME)
    info.create_system = 3
    executable = relative.startswith("payload/scripts/") and relative.endswith(".sh")
    mode = (stat.S_IFREG | (0o755 if executable else 0o644))
    info.external_attr = mode << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    info.flag_bits |= 0x800
    return info


def _write_deterministic_zip(candidate: Path, output: Path) -> str:
    paths = [path for path in relative_files(candidate) if path.name != MARKER]
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as archive:
        for path in sorted(paths, key=lambda item: item.relative_to(candidate).as_posix()):
            relative = path.relative_to(candidate).as_posix()
            archive.writestr(_zip_info(relative), path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return sha256_file(output)


def validate_archive(archive_path: Path, candidate: Path = CANDIDATE_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    expected = {path.relative_to(candidate).as_posix() for path in relative_files(candidate) if path.name != MARKER}
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            errors.append("duplicate archive path")
        if len({name.casefold() for name in names}) != len(names):
            errors.append("case-colliding archive path")
        for info in infos:
            pure = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            if pure.is_absolute() or ".." in pure.parts or "\\" in info.filename:
                errors.append(f"unsafe archive path: {info.filename}")
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                errors.append(f"unsupported archive entry type: {info.filename}")
            expected_mode = 0o755 if info.filename.startswith("payload/scripts/") and info.filename.endswith(".sh") else 0o644
            if stat.S_IMODE(mode) != expected_mode:
                errors.append(f"unexpected permission: {info.filename}")
            if info.date_time != FIXED_ZIP_TIME:
                errors.append(f"non-normalized timestamp: {info.filename}")
        if set(names) != expected:
            errors.append("archive/candidate file coverage mismatch")
    return {
        "schema_version": "g3-g-archive-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "archive_sha256": sha256_file(archive_path),
        "entry_count": len(expected),
        "path_traversal": False if not errors else any("path" in error for error in errors),
        "symlink_escape": False,
        "sentinel": "G3_G_RELEASE_CANDIDATE_OK" if not errors else None,
    }


def verify_candidate(candidate: Path = CANDIDATE_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    manifest_path = candidate / "release_manifest.json"
    if not manifest_path.is_file() or not (candidate / MARKER).is_file():
        return {"status": "FAIL", "errors": ["candidate root or manifest missing"]}
    manifest = read_json(manifest_path)
    entries = manifest.get("entries", [])
    declared = {row["path"] for row in entries}
    actual = {
        path.relative_to(candidate).as_posix()
        for path in relative_files(candidate)
        if path.name not in {MARKER, "release_manifest.json"}
    }
    if declared != actual:
        errors.append("release manifest/candidate coverage mismatch")
    for row in entries:
        pure = PurePosixPath(row["path"])
        path = candidate / Path(*pure.parts)
        if pure.is_absolute() or ".." in pure.parts:
            errors.append(f"unsafe manifest path: {row['path']}")
        elif not path.is_file() or sha256_file(path) != row["sha256"] or path.stat().st_size != row["size"]:
            errors.append(f"release manifest mismatch: {row['path']}")
        if not row.get("source") or row.get("source") == "UNKNOWN_SOURCE":
            errors.append(f"unknown mandatory source: {row['path']}")
    stage_result: dict[str, Any]
    try:
        stage_result = verify_stage(candidate / "payload")
    except Exception as exc:  # normalized into release validation result
        stage_result = {"status": "FAIL", "error": str(exc)}
        errors.append("canonical staging verification failed")
    if manifest.get("final_submission_authorization") != "USER_ACTION_REQUIRED":
        errors.append("final submission authorization boundary changed")
    return {
        "schema_version": "g3-g-release-candidate-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "release_candidate_id": manifest.get("release_candidate_id"),
        "file_count": len(entries),
        "manifest_sha256": sha256_file(manifest_path),
        "candidate_tree_sha256": tree_digest(candidate, exclude=[MARKER]),
        "staging_validation": stage_result,
        "sentinels": ["G3_G_FINAL_STAGING_OK", "G3_G_RELEASE_CANDIDATE_OK"] if not errors else [],
    }


def _tracked_payloads(
    manifest: dict[str, Any], staging: dict[str, Any], candidate: dict[str, Any], archive: dict[str, Any],
    reproducibility: dict[str, Any],
) -> dict[str, Any]:
    inventory = {
        "schema_version": "g3-g-final-staging-inventory-v1",
        "status": staging["status"],
        "canonical_staging": "dist/submission-staging",
        "parallel_staging_framework_created": False,
        "file_count": manifest["file_count"],
        "total_size": manifest["total_size"],
        "paths": [row["path"] for row in manifest["entries"]],
        "excluded_controlled_material": True,
        "excluded_official_source_and_binaries": True,
        "sentinel": "G3_G_FINAL_STAGING_OK",
    }
    return {
        "final_staging_inventory.json": inventory,
        "release_manifest.json": manifest,
        "archive_contract.json": {
            "schema_version": "g3-g-archive-contract-v1",
            "status": "PASS",
            "artifact_identity": "RELEASE_CANDIDATE_ARCHIVE",
            "final_submission_archive": False,
            "format": "ZIP",
            "ordering": "UTF8_POSIX_PATH_SORTED",
            "timestamp": "1980-01-01T00:00:00",
            "compression": "DEFLATE_LEVEL_9",
            "permissions": "0644_FILES_0755_SHELL_ENTRYPOINTS",
            "symlink_policy": "FORBIDDEN",
            "duplicate_and_case_collision_policy": "FORBIDDEN",
            "final_submission_archive_status": "NOT_AUTHORIZED",
        },
        "final_staging_validation.json": staging,
        "release_candidate_validation.json": {**candidate, "archive_validation": archive},
        "archive_reproducibility.json": reproducibility,
    }


def _write_tracked_release_metadata(payloads: dict[str, Any]) -> None:
    for name, payload in payloads.items():
        write_json(RELEASE_ROOT / name, payload)
    manifest = payloads["release_manifest.json"]
    write_text(RELEASE_ROOT / "release_manifest.md", (
        "# G3-G release manifest\n\n"
        f"Candidate `{manifest['release_candidate_id']}` contains {manifest['file_count']} declared payload files. "
        "It is an audited local RELEASE_CANDIDATE_ONLY package; legal and final submission authorization remain USER_ACTION_REQUIRED.\n"
    ))
    write_text(RELEASE_ROOT / "archive_readiness.md", (
        "# Archive readiness\n\n"
        "The deterministic ZIP is a local release candidate, not a final competition submission archive. "
        "Its entry ordering, timestamps, permissions, compression, symlink policy, and extraction safety are audited.\n"
    ))
    write_text(RELEASE_ROOT / "release_candidate_readme.md", (
        "# Release candidate\n\n"
        "Use `python -m tools.release_cli verify-candidate` for read-only validation. "
        "Do not treat this candidate as legal approval, real-device acceptance, a GitHub release, or portal submission.\n"
    ))


def build_candidate(*, write_tracked_metadata: bool = True) -> dict[str, Any]:
    stage_build = build_staging()
    if stage_build.get("status") != "PASS":
        raise ReleaseAuditError("canonical G3-F staging build failed")
    _overlay_release_delivery(DEFAULT_STAGE)
    staging = verify_stage(DEFAULT_STAGE)
    if staging.get("status") != "PASS":
        raise ReleaseAuditError("canonical staging verification failed")
    prepare_owned_root(GENERATED_ROOT, clean=GENERATED_ROOT.exists())
    shutil.copytree(DEFAULT_STAGE, PAYLOAD_ROOT)
    (CANDIDATE_ROOT / MARKER).write_text("G3-G generated root\n", encoding="utf-8")
    candidate_id = "G3-G-RC-" + tree_digest(PAYLOAD_ROOT)[:16].upper()
    manifest = _candidate_manifest(PAYLOAD_ROOT, candidate_id, "CREATED")
    write_json(CANDIDATE_ROOT / "release_manifest.json", manifest)
    run_1 = GENERATED_ROOT / f"{candidate_id}-run-1.zip"
    run_2 = GENERATED_ROOT / f"{candidate_id}-run-2.zip"
    digest_1 = _write_deterministic_zip(CANDIDATE_ROOT, run_1)
    digest_2 = _write_deterministic_zip(CANDIDATE_ROOT, run_2)
    if digest_1 != digest_2:
        raise ReleaseAuditError("release candidate archive is not bit-for-bit reproducible")
    final_archive = GENERATED_ROOT / f"{candidate_id}.zip"
    os.replace(run_1, final_archive)
    run_2.unlink()
    archive = validate_archive(final_archive)
    candidate = verify_candidate()
    if archive["status"] != "PASS" or candidate["status"] != "PASS":
        raise ReleaseAuditError("release candidate validation failed")
    reproducibility = {
        "schema_version": "g3-g-archive-reproducibility-v1",
        "status": "PASS",
        "classification": "BIT_FOR_BIT_REPRODUCIBLE",
        "run_count": 2,
        "run_1_sha256": digest_1,
        "run_2_sha256": digest_2,
        "identical": True,
        "normalized_metadata_scope": ["path_order", "timestamp", "permissions", "compression", "symlink_policy"],
    }
    staging_result = {
        "schema_version": "g3-g-final-staging-validation-v1",
        "status": "PASS",
        "canonical_staging_reused": True,
        "parallel_staging_framework_created": False,
        "manifest_entries_verified": staging["manifest_entries_verified"],
        "files_verified": staging["files_verified"],
        "native_elf_audit": staging["native_elf_audit"],
        "controlled_material_included": False,
        "official_source_or_binary_included": False,
        "sentinel": "G3_G_FINAL_STAGING_OK",
    }
    tracked = _tracked_payloads(manifest, staging_result, candidate, archive, reproducibility)
    if write_tracked_metadata:
        _write_tracked_release_metadata(tracked)
    return {
        "schema_version": "g3-g-package-build-v1",
        "status": "PASS",
        "release_candidate_id": candidate_id,
        "candidate_root": "dist/g3-g-release/candidate",
        "archive": f"dist/g3-g-release/{final_archive.name}",
        "archive_sha256": digest_1,
        "release_candidate_archive_status": "CREATED",
        "final_submission_archive_status": "NOT_AUTHORIZED",
        "final_competition_submission_authorization": "USER_ACTION_REQUIRED",
        "git_tag_created": False,
        "github_release_created": False,
        "competition_submission_performed": False,
        "sentinels": ["G3_G_FINAL_STAGING_OK", "G3_G_RELEASE_CANDIDATE_OK"],
    }


def validate_release_metadata() -> dict[str, Any]:
    errors: list[str] = []
    for name in TRACKED_OUTPUTS:
        if not (RELEASE_ROOT / name).is_file():
            errors.append(f"missing tracked release metadata: {name}")
    if errors:
        return {"status": "FAIL", "errors": errors}
    manifest = read_json(RELEASE_ROOT / "release_manifest.json")
    candidate = read_json(RELEASE_ROOT / "release_candidate_validation.json")
    staging = read_json(RELEASE_ROOT / "final_staging_validation.json")
    reproducibility = read_json(RELEASE_ROOT / "archive_reproducibility.json")
    if manifest.get("final_submission_authorization") != "USER_ACTION_REQUIRED":
        errors.append("final submission authorization is not USER_ACTION_REQUIRED")
    if manifest.get("final_submission_archive_status") != "NOT_AUTHORIZED":
        errors.append("final submission archive boundary changed")
    if any(not row.get("source") or row.get("source") == "UNKNOWN_SOURCE" for row in manifest.get("entries", [])):
        errors.append("mandatory source mapping incomplete")
    if candidate.get("status") != "PASS" or staging.get("status") != "PASS" or reproducibility.get("status") != "PASS":
        errors.append("tracked release validation is not PASS")
    return {
        "schema_version": "g3-g-tracked-release-metadata-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "release_candidate_id": manifest.get("release_candidate_id"),
        "file_count": manifest.get("file_count"),
        "sentinels": ["G3_G_FINAL_STAGING_OK", "G3_G_RELEASE_CANDIDATE_OK"] if not errors else [],
    }
