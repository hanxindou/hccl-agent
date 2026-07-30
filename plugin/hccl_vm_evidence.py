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
from plugin.hccl_vm_runner import OfficialAllReduceRequest, OfficialRunOutcome


EVIDENCE_SCHEMA_VERSION = "g2-d-v1"
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


def archive_official_evidence(
    outcome: OfficialRunOutcome,
    request: OfficialAllReduceRequest,
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
    directory = _create_evidence_directory(
        Path(config.evidence_root),
        timestamp.strftime("g2_d_%Y%m%dT%H%M%S.%fZ"),
    )

    public_result = outcome.to_public_dict()
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "generated_at_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "validation_class": VALIDATION_CLASS,
        "execution_mode": "subprocess_hccl_test",
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "request": request.to_dict(),
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
        "# G2-D Official HCCL-VM Validation Evidence",
        "",
        "This archive records a subprocess-driven run of the official HCCL-VM, "
        "hccl_test, and checker tools. It is not a direct HCCL API integration "
        "and does not claim validation on a real Ascend NPU.",
        "",
        f"- Status: `{result.get('status', 'UNKNOWN')}`",
        f"- Passed: `{result.get('passed', False)}`",
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
