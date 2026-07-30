"""Evidence archive writer for official HCCL-VM validation runs."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.report_generator import ReportGenerator
from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_runner import OfficialCollectiveRequest, OfficialRunOutcome


EVIDENCE_SCHEMA_VERSION = "g2-e-primitive-v1"
VALIDATION_CLASS = "OFFICIAL_HCCL_VM_SIMULATOR"
_IMPORTANT_LOG_RE = re.compile(
    r"__HCCL_AGENT_|Opsummary|Op summary|Checker (?:Success|Failed)|"
    r"stage\s*=|ErrorCode:\s*103|Shell exited|Segmentation fault|"
    r"MPI_ABORT|undefined symbol|fatal failure",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EvidenceArchive:
    directory: Path
    checksums: dict[str, str]
    checksum_file_sha256: str


@dataclass(frozen=True)
class SuiteEvidenceArchive:
    directory: Path
    checksums: dict[str, str]
    checksum_file_sha256: str
    summary: dict[str, Any]


def archive_official_evidence(
    outcome: OfficialRunOutcome,
    request: OfficialCollectiveRequest,
    config: HcclVmConfig,
    *,
    command: str,
    generated_at: datetime | None = None,
) -> EvidenceArchive:
    """Write a compact, checksummed archive without altering raw results."""

    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)
    contract = request.resolve()
    directory = _create_evidence_directory(
        Path(config.evidence_root),
        timestamp.strftime(
            "g2_e_"
            + contract.canonical_primitive.casefold()
            + "_%Y%m%dT%H%M%S.%fZ"
        ),
    )

    public_result = outcome.to_public_dict()
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "generated_at_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "validation_class": VALIDATION_CLASS,
        "execution_mode": "subprocess_hccl_test",
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "primitive": contract.canonical_primitive,
        "input_alias": contract.input_alias,
        "request": request.to_dict(),
        "resolved_contract": contract.to_dict(),
        "hccl_test_argv": outcome.plan.get("hccl_test_argv", []),
        "configuration": config.to_dict(),
        "diagnosis": outcome.diagnosis,
    }

    _write_json(directory / "manifest.json", manifest)
    _write_text(directory / "command.txt", command.rstrip() + "\n")
    _write_json(directory / "result.json", public_result)
    _write_text(
        directory / "concise.log",
        _concise_log(outcome.raw_log),
    )
    (directory / "raw.log.gz").write_bytes(
        gzip.compress(outcome.raw_log.encode("utf-8"), mtime=0)
    )

    report = ReportGenerator.generate_official_validation_report(
        public_result,
        evidence_directory=str(directory),
    )
    _write_text(directory / "report.txt", report)
    _write_text(
        directory / "README.md",
        _readme(public_result, report),
    )

    evidence_files = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.name != "SHA256SUMS"
    )
    checksums = {
        path.name: _sha256(path)
        for path in evidence_files
    }
    checksum_text = "".join(
        f"{digest}  {name}\n"
        for name, digest in sorted(checksums.items())
    )
    checksum_path = directory / "SHA256SUMS"
    _write_text(checksum_path, checksum_text)
    return EvidenceArchive(
        directory=directory,
        checksums=checksums,
        checksum_file_sha256=_sha256(checksum_path),
    )


def archive_g2_e_suite_evidence(
    entries: list[dict[str, Any]],
    config: HcclVmConfig,
    *,
    command: str,
    generated_at: datetime | None = None,
) -> SuiteEvidenceArchive:
    """Create a compact suite index that references, never copies, raw logs."""
    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)
    directory = _create_evidence_directory(
        Path(config.evidence_root),
        timestamp.strftime("g2_e_summary_%Y%m%dT%H%M%S.%fZ"),
    )
    primitive_results = []
    for entry in entries:
        request = entry["request"]
        archive = entry["archive"]
        result = entry["result"]
        contract = request.resolve()
        primitive_results.append({
            "primitive": contract.canonical_primitive,
            "passed": bool(result.get("passed")),
            "status": result.get("status"),
            "checker_success_count": result.get("checker_success_count"),
            "warning_103_count": result.get("warning_103_count"),
            "warning_regression": result.get("warning_regression"),
            "evidence_dir": str(archive.directory),
            "evidence_sha256": archive.checksum_file_sha256,
        })
    expected_primitives = ["AllReduce", "AllGather", "ReduceScatter"]
    environment_records = [
        _suite_environment_record(entry)
        for entry in entries
    ]
    environment_consistent = len({
        json.dumps(record, sort_keys=True)
        for record in environment_records
    }) == 1
    passed = (
        [result["primitive"] for result in primitive_results]
        == expected_primitives
        and all(result["passed"] for result in primitive_results)
        and environment_consistent
    )
    status = "COMPLETED" if passed else "INCOMPLETE"
    if not environment_consistent:
        status = "ENV_BLOCKED_ENVIRONMENT_MISMATCH"
    summary = {
        "schema_version": "g2-e-suite-v1",
        "suite": "g2-e",
        "execution_mode": "subprocess_hccl_test",
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "status": status,
        "passed": passed,
        "environment_consistent": environment_consistent,
        "environment_records": environment_records,
        "primitive_results": primitive_results,
    }
    manifest = {
        "schema_version": "g2-e-suite-v1",
        "generated_at_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "validation_class": VALIDATION_CLASS,
        "command": command.rstrip(),
        "configuration": config.to_dict(),
        "environment_consistent": environment_consistent,
        "primitive_evidence_references": primitive_results,
        "raw_logs_copied": False,
    }
    _write_json(directory / "summary.json", summary)
    _write_json(directory / "manifest.json", manifest)
    _write_text(directory / "README.md", _suite_readme(summary))
    evidence_files = sorted(path for path in directory.iterdir() if path.is_file())
    checksums = {path.name: _sha256(path) for path in evidence_files}
    checksum_path = directory / "SHA256SUMS"
    _write_text(checksum_path, "".join(
        f"{digest}  {name}\n" for name, digest in sorted(checksums.items())
    ))
    return SuiteEvidenceArchive(
        directory=directory,
        checksums=checksums,
        checksum_file_sha256=_sha256(checksum_path),
        summary=summary,
    )


def _create_evidence_directory(root: Path, name: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / name
    suffix = 1
    while candidate.exists():
        candidate = root / f"{name}_{suffix}"
        suffix += 1
    candidate.mkdir()
    return candidate


def _write_json(path: Path, value: Any) -> None:
    _write_text(
        path,
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    )


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _concise_log(raw_log: str) -> str:
    lines = []
    for line in raw_log.splitlines():
        normalized = " ".join(line.split())
        if normalized and _IMPORTANT_LOG_RE.search(normalized):
            lines.append(normalized[:2000])
    if not lines:
        return "(no key validation log lines captured)\n"
    return "\n".join(lines[-500:]) + "\n"


def _readme(result: dict[str, Any], report: str) -> str:
    return "\n".join([
        "# G2-E Official HCCL-VM Primitive Validation Evidence",
        "",
        "This archive records a subprocess-driven run of the official HCCL-VM, "
        "hccl_test, and checker tools. It is not a direct HCCL API integration "
        "and does not claim validation on a real Ascend NPU.",
        "",
        f"- Status: `{result.get('status', 'UNKNOWN')}`",
        f"- Passed: `{result.get('passed', False)}`",
        f"- Primitive: `{result.get('primitive', 'UNKNOWN')}`",
        f"- Checker Success: `{result.get('checker_success', False)}`",
        f"- ErrorCode 103 warnings: `{result.get('warning_103_count', 0)}`",
        f"- Outer exit code: `{result.get('outer_exit_code')}`",
        f"- HCCL-VM normal shutdown: `{result.get('vm_normal_shutdown', False)}`",
        "",
        "## Agent Report",
        "",
        "```text",
        report.rstrip(),
        "```",
        "",
        "Use `SHA256SUMS` to verify every archived evidence file.",
        "",
    ])


def _suite_readme(summary: dict[str, Any]) -> str:
    lines = [
        "# G2-E Official HCCL-VM Suite Evidence",
        "",
        "This suite references per-primitive subprocess-driven official "
        "HCCL-VM evidence. It does not copy raw logs, call HCCL directly, "
        "or claim real Ascend NPU validation.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Passed: `{summary['passed']}`",
        "",
        "## Primitive References",
        "",
    ]
    for result in summary["primitive_results"]:
        lines.append(
            f"- `{result['primitive']}`: `{result['status']}`, "
            f"evidence `{result['evidence_dir']}`, "
            f"SHA256SUMS SHA256 `{result['evidence_sha256']}`"
        )
    lines.extend([
        "",
        "Use `SHA256SUMS` to verify every suite file.",
        "",
    ])
    return "\n".join(lines)


def _suite_environment_record(entry: dict[str, Any]) -> dict[str, Any]:
    outcome = entry.get("outcome")
    diagnosis = getattr(outcome, "diagnosis", {}) if outcome is not None else {}
    request = entry["request"]
    contract = request.resolve()
    return {
        "registry_version": contract.registry_version,
        "cann_version": diagnosis.get("cann", {}).get("version"),
        "hcomm_branch": diagnosis.get("hcomm", {}).get("branch"),
        "hcomm_commit": diagnosis.get("hcomm", {}).get("commit"),
        "hccl_branch": diagnosis.get("hccl", {}).get("branch"),
        "hccl_commit": diagnosis.get("hccl", {}).get("commit"),
    }
