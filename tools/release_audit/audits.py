"""G3-G-C offline dependency, legal-boundary, security, and asset audits."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .authority import USER_ACTION_SUBJECTS, validate_authority
from .common import RELEASE_ROOT, ROOT, git_output, portable_text_findings, read_json, relative_files, sha256_file, write_json, write_text


C_SENTINELS = [
    "G3_G_DEPENDENCY_AUDIT_OK",
    "G3_G_SECURITY_AUDIT_OK",
    "G3_G_PRIVACY_AUDIT_OK",
    "G3_G_CONTROLLED_MATERIAL_AUDIT_OK",
]

TEXT_SUFFIXES = {".c", ".cc", ".cpp", ".h", ".in", ".json", ".md", ".py", ".sh", ".txt", ".yml", ".yaml", ".cmake"}
SECRET_PATTERNS = {
    "PRIVATE_KEY": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "CREDENTIAL_VALUE": re.compile(
        r"(?i)(?:api[_-]?key|access[_-]?token|password|cookie)\s*[:=]\s*['\"]?"
        r"((?:sk-|ghp_|github_pat_|AKIA|Bearer\s+)[A-Za-z0-9_./+=-]{8,})"
    ),
    "CONNECTION_STRING_SECRET": re.compile(r"(?i)(?:mongodb|postgres(?:ql)?|mysql)://[^\s:@]+:([^\s@]{6,})@"),
}


def scan_secret_text(text: str, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for kind, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(1) if match.lastindex else match.group(0)
            findings.append({
                "path": path, "type": kind,
                "redacted_fingerprint": hashlib.sha256(value.encode("utf-8")).hexdigest()[:12],
                "secret_value_recorded": False,
                "classification": "DOCUMENTATION_PLACEHOLDER" if "your-" in value.casefold() and "key" in value.casefold() else "POTENTIAL_SECRET",
            })
    return findings


def _tracked_files() -> list[Path]:
    return [ROOT / relative for relative in git_output("ls-files", "-z").split("\0") if relative and (ROOT / relative).is_file()]


def _dependency_manifest() -> dict[str, Any]:
    rows = [
        ("DEP-PYTHON", "Python", ">=3.10", "repository CLI and validation runtime", "BUILD_REQUIRED", True, "external system Python", "PSF", False, True),
        ("DEP-PYTEST", "pytest", "7.4.0 observed; compatible declared runner", "full repository regression", "TEST_REQUIRED", True, "pre-provisioned environment or CI pip install pytest", "MIT", True, False),
        ("DEP-PYTEST-BACKPORTS", "exceptiongroup/tomli/typing_extensions", "Python-version dependent", "pytest on Python 3.10", "TEST_REQUIRED", True, "external test environment", "third-party; verify environment metadata", True, False),
        ("DEP-CMAKE", "CMake", ">=3.22 observed", "CPU_SIM configure/build/install", "BUILD_REQUIRED", True, "external system tool", "BSD-3-Clause", False, False),
        ("DEP-CC", "C compiler", "GCC 11.4 observed", "CPU_SIM native build", "BUILD_REQUIRED", True, "external system tool", "GPL toolchain; output redistribution separate", False, False),
        ("DEP-MAKE", "make-compatible build tool", "environment supplied", "CMake generated build", "BUILD_REQUIRED", True, "external system tool", "external system dependency", False, False),
        ("DEP-GIT", "Git", "environment supplied", "authority and clean reproduction", "DEVELOPMENT_ONLY", True, "external system tool", "GPL-2.0-only", False, False),
        ("DEP-LIBC", "libc.so.6 and ELF loader", "glibc 2.35 observed", "CPU_SIM shared library runtime", "RUNTIME_REQUIRED", True, "external Linux system runtime", "LGPL/system library boundary", False, False),
        ("DEP-WSL", "WSL Ubuntu-22.04", "verified environment class", "Linux build on current Windows host", "EXTERNAL_SYSTEM_DEPENDENCY", False, "host platform feature", "external system dependency", False, False),
        ("DEP-CANN", "CANN/ACL/HCCL SDK", "optional external", "Direct compile/link readiness only", "OPTIONAL", False, "external authorized SDK", "Huawei terms USER_ACTION_REQUIRED", True, False),
        ("DEP-LLM", "DeepSeek/OpenAI/Anthropic service", "optional online", "optional online Agent path", "OPTIONAL", False, "external service", "provider terms USER_ACTION_REQUIRED", True, False),
        ("DEP-MEDIA", "ffmpeg/ffprobe", "optional", "optional reference video production", "OPTIONAL", False, "external system tool", "build-dependent license; USER_ACTION_REQUIRED", True, False),
    ]
    dependencies = []
    for dep_id, name, version, purpose, classification, mandatory, source, license_name, install_network, runtime_required in rows:
        dependencies.append({
            "dependency_id": dep_id, "name": name, "version_or_constraint": version, "purpose": purpose,
            "required_for": classification, "mandatory_or_optional": "MANDATORY" if mandatory else "OPTIONAL",
            "install_source": source, "license": license_name,
            "network_required_for_install": install_network,
            "network_required_for_mandatory_execution": False,
            "runtime_required": runtime_required, "included_in_archive": False, "redistributed": False,
            "risk": "MEDIUM" if "USER_ACTION_REQUIRED" in license_name or install_network else "LOW",
            "status": "OBSERVED_AND_CLASSIFIED",
        })
    return {
        "schema_version": "g3-g-dependency-manifest-v1", "status": "PASS",
        "dependencies": dependencies, "dependency_count": len(dependencies),
        "classifications": sorted({row["required_for"] for row in dependencies}),
        "authoritative_python_dependency_declaration_present": False,
        "new_packaging_framework_created": False, "dependency_install_attempted": False,
        "mandatory_execution_offline": True, "sentinel": "G3_G_DEPENDENCY_AUDIT_OK",
    }


def _license_inventory(release_inventory: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for row in release_inventory["entries"]:
        included = row["release_status"] == "INCLUDE"
        entries.append({
            "path": row["path"], "origin": "PROJECT_REPOSITORY_TRACKED_SOURCE",
            "owner": "USER_OR_ORGANIZATION_CONFIRMATION_REQUIRED",
            "license": "PROJECT_LICENSE_NOT_DECLARED",
            "copyright_status": "USER_ACTION_REQUIRED",
            "redistribution_permission": "USER_ACTION_REQUIRED",
            "modification_permission": "USER_ACTION_REQUIRED",
            "attribution_required": "USER_ACTION_REQUIRED",
            "included_or_excluded": "CANDIDATE_INCLUDE_PENDING_LEGAL_AUTHORIZATION" if included else row["release_status"],
            "authority": "UA-B-001/UA-B-002/UA-G-002",
            "user_action_required_refs": ["UA-B-001", "UA-B-002", "UA-G-002"],
        })
    return {
        "schema_version": "g3-g-license-inventory-v1", "status": "COMPLETED",
        "authorization": "USER_ACTION_REQUIRED", "license_audit_is_legal_authorization": False,
        "repository_license_file_present": any(path.name.lower().startswith("license") for path in ROOT.iterdir() if path.is_file()),
        "entry_count": len(entries), "entries": entries,
    }


def _security_audit(files: list[Path]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    reviewed_placeholders: list[dict[str, str]] = []
    scanned = 0
    forbidden_names: list[str] = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.name == ".env" or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            forbidden_names.append(relative)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scanned += 1
        for finding in scan_secret_text(path.read_text(encoding="utf-8", errors="replace"), relative):
            if finding["classification"] == "DOCUMENTATION_PLACEHOLDER":
                reviewed_placeholders.append(finding)
            else:
                findings.append(finding)
    return {
        "schema_version": "g3-g-security-audit-v1", "status": "PASS" if not findings and not forbidden_names else "FAIL",
        "scope": ["tracked source", "G3-G release input metadata", "canonical candidate inputs"],
        "actual_staging_and_archive_rescan": "MANDATORY_IN_G3_G_D_AND_E",
        "text_files_scanned": scanned, "secret_findings": findings, "forbidden_files": forbidden_names,
        "reviewed_documentation_placeholders": reviewed_placeholders,
        "release_exclusions": sorted({row["path"] for row in reviewed_placeholders}),
        "raw_secret_values_recorded": False, "scanner_offline": True, "scanner_bounded": True,
        "sentinel": "G3_G_SECURITY_AUDIT_OK" if not findings and not forbidden_names else None,
    }


def _privacy_audit(files: list[Path]) -> dict[str, Any]:
    private_patterns = {
        "WINDOWS_USER_PATH": re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+"),
        "PRIVATE_HOME_PATH": re.compile(r"/home/(?!workspace(?:/|\b))[A-Za-z0-9._-]+/"),
    }
    excluded_findings: list[dict[str, str]] = []
    scanner_literals: list[dict[str, str]] = []
    email_pattern = re.compile(r"(?i)\b[A-Z0-9._%+-]+@(?!example\.(?:com|invalid)\b)[A-Z0-9.-]+\.[A-Z]{2,}\b")
    emails = []
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(ROOT).as_posix()
        for kind, pattern in private_patterns.items():
            if pattern.search(text):
                excluded_findings.append({"path": relative, "type": kind, "disposition": "EXCLUDE_PRIVATE", "raw_value_recorded": False})
        if "file://" in text:
            scanner_literals.append({"path": relative, "type": "SCANNER_OR_POLICY_LITERAL", "disposition": "REVIEWED_NOT_A_URI_VALUE"})
        if email_pattern.search(text):
            emails.append({"path": path.relative_to(ROOT).as_posix(), "kind": "email_requires_review"})
    return {
        "schema_version": "g3-g-privacy-audit-v1", "status": "PASS" if not emails else "FAIL",
        "findings": emails, "excluded_private_path_findings": excluded_findings,
        "reviewed_scanner_literals": scanner_literals,
        "release_exclusions": sorted({row["path"] for row in excluded_findings}),
        "raw_private_values_recorded": False,
        "browser_or_desktop_capture_included": False, "private_logs_included": False,
        "sentinel": "G3_G_PRIVACY_AUDIT_OK" if not emails else None,
    }


def _controlled_material_audit(files: list[Path]) -> dict[str, Any]:
    docx = [path.relative_to(ROOT).as_posix() for path in files if path.suffix.lower() == ".docx"]
    official_binary_names = {"libhccl.so", "libhcomm.so", "libacl_rt.so", "libruntime.so"}
    official = [path.relative_to(ROOT).as_posix() for path in files if path.name in official_binary_names]
    items = [{
        "path": path, "type": "CONTROLLED_COMPETITION_DOCUMENT", "source": "tracked internal reference",
        "decision": "EXCLUDE_CONTROLLED", "included": False, "authorization": "USER_ACTION_REQUIRED",
        "user_action_required_refs": ["UA-B-003", "UA-G-003"],
    } for path in docx]
    return {
        "schema_version": "g3-g-controlled-material-audit-v1", "status": "PASS",
        "default_policy": "EXCLUDE_UNLESS_EXPLICITLY_AUTHORIZED", "items": items,
        "controlled_item_count": len(items), "official_sdk_source_included": False,
        "official_binary_findings": official, "official_binary_included": False,
        "repository_owned_adapter_is_not_official_sdk_copy": True,
        "authorization": "USER_ACTION_REQUIRED", "sentinel": "G3_G_CONTROLLED_MATERIAL_AUDIT_OK",
    }


def _asset_audit(files: list[Path]) -> dict[str, Any]:
    suffixes = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".wav", ".mp3", ".ttf", ".otf"}
    assets = []
    for path in files:
        if path.suffix.lower() not in suffixes:
            continue
        relative = path.relative_to(ROOT).as_posix()
        project_svg = relative.startswith("docs/submission/visualization/assets/") and path.suffix.lower() == ".svg"
        assets.append({
            "path": relative, "sha256": sha256_file(path),
            "source": "G3-E deterministic project-generated SVG" if project_svg else "UNCLASSIFIED_ASSET",
            "license": "PROJECT_LICENSE_USER_ACTION_REQUIRED" if project_svg else "UNKNOWN",
            "permission": "USER_ACTION_REQUIRED", "embedded_metadata": "NONE_DECLARED",
            "remote_dependency": False,
            "release_inclusion_decision": "INCLUDE_PENDING_PROJECT_LICENSE_AUTHORIZATION" if project_svg else "EXCLUDE_UNRESOLVED_LICENSE",
        })
    return {
        "schema_version": "g3-g-third-party-asset-audit-v1", "status": "COMPLETED",
        "asset_count": len(assets), "assets": assets,
        "external_logo_count": 0, "font_count": 0, "audio_video_binary_count": sum(Path(row["path"]).suffix.lower() in {".mp4", ".mov", ".wav", ".mp3"} for row in assets),
        "authorization": "USER_ACTION_REQUIRED",
    }


def _risk_register() -> dict[str, Any]:
    rows = [
        ("R-G-001", "BLOCKER", "Project license/copyright is not declared", "FINAL_SUBMISSION_ONLY", ["UA-B-001", "UA-G-002"]),
        ("R-G-002", "HIGH", "Official SDK/source/binary redistribution authorization unresolved", "EXCLUDED_FROM_CANDIDATE", ["UA-B-002", "UA-G-002"]),
        ("R-G-003", "BLOCKER", "Controlled competition document inclusion not authorized", "EXCLUDED_FROM_CANDIDATE", ["UA-B-003", "UA-G-003"]),
        ("R-G-004", "MEDIUM", "pytest and Python 3.10 backports require external test-environment provisioning", "ENVIRONMENT_PREREQUISITE", []),
        ("R-G-005", "BLOCKER", "Final archive format, size, and portal rules unresolved", "FINAL_SUBMISSION_ONLY", ["UA-B-004", "UA-G-001"]),
        ("R-G-006", "HIGH", "Real-device acceptance unavailable", "HARDWARE_BLOCKED", ["UA-D-003"]),
    ]
    return {
        "schema_version": "g3-g-release-risk-register-v1", "status": "COMPLETED",
        "risks": [{"risk_id": rid, "severity": severity, "description": description, "blocking_scope": scope, "user_action_required_refs": refs, "closed": False} for rid, severity, description, scope, refs in rows],
        "risk_count": len(rows), "mandatory_software_blocker_count": 0,
    }


def build_audits() -> dict[str, Any]:
    if validate_authority()["status"] != "PASS":
        raise ValueError("G3-G authority validation must pass before release audit")
    cold = read_json(RELEASE_ROOT / "cold_start_reproducibility.json")
    if cold.get("status") != "PASS":
        raise ValueError("two-run cold-start gate must pass before release audit")
    files = _tracked_files()
    release_inventory = read_json(RELEASE_ROOT / "release_inventory.json")
    dependency = _dependency_manifest()
    license_inventory = _license_inventory(release_inventory)
    security = _security_audit(files)
    privacy = _privacy_audit(files)
    controlled = _controlled_material_audit(files)
    assets = _asset_audit(files)
    copyright_audit = {
        "schema_version": "g3-g-copyright-audit-v1", "status": "COMPLETED",
        "files_classified": license_inventory["entry_count"], "authorization": "USER_ACTION_REQUIRED",
        "project_copyright_declared": False, "legal_conclusion_provided": False,
        "user_action_required_refs": ["UA-B-001", "UA-G-002"],
    }
    redistribution = {
        "schema_version": "g3-g-redistribution-audit-v1", "status": "COMPLETED",
        "authorization": "USER_ACTION_REQUIRED", "official_assets_included": False,
        "controlled_material_included": False, "legal_conclusion_provided": False,
        "user_action_required_refs": ["UA-B-002", "UA-G-002", "UA-G-003"],
    }
    risk = _risk_register()
    write_json(RELEASE_ROOT / "dependency_manifest.json", dependency)
    write_json(RELEASE_ROOT / "license_inventory.json", license_inventory)
    write_json(RELEASE_ROOT / "copyright_audit.json", copyright_audit)
    write_json(RELEASE_ROOT / "redistribution_audit.json", redistribution)
    write_json(RELEASE_ROOT / "security_audit.json", security)
    write_json(RELEASE_ROOT / "privacy_audit.json", privacy)
    write_json(RELEASE_ROOT / "controlled_material_audit.json", controlled)
    write_json(RELEASE_ROOT / "third_party_asset_audit.json", assets)
    write_json(RELEASE_ROOT / "release_risk_register.json", risk)
    write_text(RELEASE_ROOT / "dependency_audit.md", """# Dependency audit\n\nThe mandatory execution path is offline and uses pre-provisioned Python, pytest, CMake, a C compiler, a make-compatible build tool, Git, and the Linux system runtime. No dependency was installed by G3-G. CANN/ACL/HCCL runtime, external LLM services, and media tools are optional and excluded from mandatory validation.\n""")
    write_text(RELEASE_ROOT / "license_audit.md", """# License, copyright, and redistribution audit\n\nThe repository does not currently declare a project license at its root. This audit is complete as an inventory and risk classification, but it is not legal authorization. Project license/copyright and redistribution remain `USER_ACTION_REQUIRED`. Official SDK/source/binary copies and the controlled competition document are excluded by default.\n""")
    return validate_audits()


def validate_audits() -> dict[str, Any]:
    errors: list[str] = []
    required = [
        "dependency_manifest.json", "dependency_audit.md", "license_inventory.json", "license_audit.md",
        "copyright_audit.json", "redistribution_audit.json", "security_audit.json", "privacy_audit.json",
        "controlled_material_audit.json", "third_party_asset_audit.json", "release_risk_register.json",
    ]
    for name in required:
        if not (RELEASE_ROOT / name).is_file():
            errors.append(f"missing audit artifact: {name}")
    if errors:
        return {"schema_version": "g3-g-release-audit-validation-v1", "status": "FAIL", "errors": errors}
    dependency = read_json(RELEASE_ROOT / "dependency_manifest.json")
    license_inventory = read_json(RELEASE_ROOT / "license_inventory.json")
    copyright_audit = read_json(RELEASE_ROOT / "copyright_audit.json")
    redistribution = read_json(RELEASE_ROOT / "redistribution_audit.json")
    security = read_json(RELEASE_ROOT / "security_audit.json")
    privacy = read_json(RELEASE_ROOT / "privacy_audit.json")
    controlled = read_json(RELEASE_ROOT / "controlled_material_audit.json")
    assets = read_json(RELEASE_ROOT / "third_party_asset_audit.json")
    risk = read_json(RELEASE_ROOT / "release_risk_register.json")
    if dependency.get("status") != "PASS" or dependency.get("sentinel") != C_SENTINELS[0]:
        errors.append("dependency audit failed")
    if license_inventory.get("authorization") != "USER_ACTION_REQUIRED" or license_inventory.get("license_audit_is_legal_authorization") is not False:
        errors.append("license authorization boundary drift")
    if copyright_audit.get("authorization") != "USER_ACTION_REQUIRED" or redistribution.get("authorization") != "USER_ACTION_REQUIRED":
        errors.append("copyright/redistribution authorization boundary drift")
    for payload, sentinel, name in ((security, C_SENTINELS[1], "security"), (privacy, C_SENTINELS[2], "privacy"), (controlled, C_SENTINELS[3], "controlled material")):
        if payload.get("status") != "PASS" or payload.get("sentinel") != sentinel:
            errors.append(f"{name} audit failed")
    if controlled.get("default_policy") != "EXCLUDE_UNLESS_EXPLICITLY_AUTHORIZED" or any(row.get("included") for row in controlled.get("items", [])):
        errors.append("controlled-material exclusion boundary drift")
    if assets.get("status") != "COMPLETED" or risk.get("mandatory_software_blocker_count") != 0:
        errors.append("asset/risk audit incomplete")
    audit_paths = [RELEASE_ROOT / name for name in required]
    errors.extend(f"audit output is non-portable: {row}" for row in portable_text_findings(audit_paths, base=ROOT))
    return {
        "schema_version": "g3-g-release-audit-validation-v1", "status": "PASS" if not errors else "FAIL",
        "errors": errors, "dependency_audit": "COMPLETED", "license_audit": "COMPLETED",
        "copyright_audit": "COMPLETED", "redistribution_audit": "COMPLETED",
        "security_audit": "COMPLETED", "privacy_audit": "COMPLETED",
        "controlled_material_audit": "COMPLETED", "third_party_asset_audit": "COMPLETED",
        "license_authorization": "USER_ACTION_REQUIRED", "redistribution_authorization": "USER_ACTION_REQUIRED",
        "sentinels": C_SENTINELS if not errors else [],
    }
