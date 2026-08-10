"""Shared, deterministic helpers for the G3-G release audit."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
RELEASE_ROOT = ROOT / "docs/submission/release"
GENERATED_ROOT = ROOT / "dist/g3-g-release"
EVIDENCE_PARENT = ROOT / "experiments/submission/evidence"
MARKER = ".g3-g-owned"


class ReleaseAuditError(RuntimeError):
    """Raised when a mandatory G3-G release gate cannot be satisfied."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def git_output(*args: str, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        raise ReleaseAuditError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def verify_sha256sums(root: Path) -> dict[str, Any]:
    checksum = root / "SHA256SUMS"
    if not checksum.is_file():
        return {"status": "FAIL", "root": root.relative_to(ROOT).as_posix(), "errors": ["missing SHA256SUMS"]}
    errors: list[str] = []
    entries = 0
    for line in checksum.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            errors.append("malformed SHA256SUMS line")
            continue
        target = root / relative
        entries += 1
        if not target.is_file():
            errors.append(f"missing: {relative}")
        elif sha256_file(target) != expected:
            errors.append(f"digest mismatch: {relative}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "root": root.relative_to(ROOT).as_posix(),
        "entries_verified": entries,
        "errors": errors,
        "sha256sums_sha256": sha256_file(checksum),
    }


def relative_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())


def tree_digest(root: Path, *, exclude: Iterable[str] = ()) -> str:
    excluded = set(exclude)
    digest = hashlib.sha256()
    for path in relative_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def portable_text_findings(paths: Iterable[Path], *, base: Path = ROOT) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    patterns = {
        "windows_user_path": re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+"),
        "private_home_path": re.compile(r"/home/(?!workspace(?:/|\b))[A-Za-z0-9._-]+/"),
        "file_uri": re.compile(r"file://", re.IGNORECASE),
    }
    for path in paths:
        if path.suffix.lower() not in {".json", ".md", ".txt", ".py", ".c", ".cpp", ".h", ".cmake"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for kind, pattern in patterns.items():
            if pattern.search(text):
                findings.append({"path": path.relative_to(base).as_posix(), "kind": kind})
    return findings


def secret_findings(paths: Iterable[Path], *, base: Path = ROOT) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    patterns = {
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "credential_value": re.compile(
            r"(?i)(?:api[_-]?key|access[_-]?token|password|cookie)\s*[:=]\s*['\"]?"
            r"(?:sk-|ghp_|github_pat_|AKIA|Bearer\s+)[A-Za-z0-9_./+=-]{8,}"
        ),
    }
    for path in paths:
        if path.suffix.lower() not in {".json", ".md", ".txt", ".py", ".yml", ".yaml", ".sh", ".c", ".cpp", ".h"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for kind, pattern in patterns.items():
            if pattern.search(text):
                findings.append({"path": path.relative_to(base).as_posix(), "kind": kind})
    return findings


def prepare_owned_root(path: Path, *, clean: bool = False) -> Path:
    resolved = path.resolve()
    allowed = GENERATED_ROOT.resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ReleaseAuditError(f"unsafe G3-G generated root: {path}")
    if clean and path.exists():
        if not (path / MARKER).is_file():
            raise ReleaseAuditError(f"refusing to clean unmarked root: {path}")
        import shutil
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / MARKER).write_text("G3-G generated root\n", encoding="utf-8")
    return path


def sanitized_environment() -> dict[str, str]:
    env = dict(os.environ)
    for name in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    return env
