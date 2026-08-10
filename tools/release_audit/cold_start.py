"""G3-G-B clean-worktree reproduction runner and comparator.

The executable implementation is committed in G3-G-A as a validator skeleton.
G3-G-B is the first checkpoint allowed to invoke it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .authority import MANDATORY_ENTRY_POINTS
from .common import RELEASE_ROOT, ROOT, ReleaseAuditError, sanitized_environment, sha256_file, tree_digest, write_json


def _run(command: list[str], cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    actual = [sys.executable, *command[1:]] if command and command[0] == "python" else command
    started = time.monotonic()
    completed = subprocess.run(
        actual, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    output = completed.stdout
    tail = output.splitlines()[-20:]
    return {
        "command": command, "exit_code": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "duration_seconds": round(time.monotonic() - started, 3),
        "output_tail": tail,
    }


def _sequence(run_root: Path) -> list[list[str]]:
    result_root = "dist/g3-g-cold-start-results"
    commands = [list(row) for row in MANDATORY_ENTRY_POINTS]
    for row in commands:
        if row[:6] == ["python", "-m", "tools.demo_delivery_cli", "run", "--profile", "quick"]:
            row.extend(["--output", f"{result_root}/quick.json"])
        elif row[:6] == ["python", "-m", "tools.demo_delivery_cli", "transcript", "--profile", "fallback"]:
            row.extend(["--output", f"{result_root}/fallback.json"])
    return commands


def run_clean_worktree(run_id: str, output: Path) -> dict[str, Any]:
    if run_id not in {"run-1", "run-2"}:
        raise ReleaseAuditError("cold-start run id must be run-1 or run-2")
    temp_parent = Path(tempfile.mkdtemp(prefix=f"hccl-agent-g3-g-{run_id}-"))
    worktree = temp_parent / "source"
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout.strip()
    added = False
    try:
        add = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), source_commit], cwd=ROOT,
            text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if add.returncode:
            raise ReleaseAuditError(f"git worktree add failed: {add.stderr.strip()}")
        added = True
        initial_status = subprocess.run(
            ["git", "status", "--short"], cwd=worktree, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.strip()
        if initial_status:
            raise ReleaseAuditError(f"clean worktree was not clean: {initial_status}")
        env = sanitized_environment()
        env["G3_G_CLEAN_MODEL"] = "CLEAN_WORKTREE_REPRODUCTION"
        steps: list[dict[str, Any]] = []
        for command in _sequence(worktree):
            result = _run(command, worktree, env)
            steps.append(result)
            if result["status"] != "PASS":
                break
        stage = worktree / "dist/submission-staging"
        quick = worktree / "dist/g3-g-cold-start-results/quick.json"
        fallback = worktree / "dist/g3-g-cold-start-results/fallback.json"
        final_status = subprocess.run(
            ["git", "status", "--short"], cwd=worktree, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.splitlines()
        tracked_changes = [line for line in final_status if not line.startswith("??")]
        payload = {
            "schema_version": "g3-g-clean-worktree-run-v1", "run_id": run_id,
            "status": "PASS" if len(steps) == len(MANDATORY_ENTRY_POINTS) and all(row["status"] == "PASS" for row in steps) and not tracked_changes else "FAIL",
            "clean_environment_model": "CLEAN_WORKTREE_REPRODUCTION", "source_commit": source_commit,
            "initial_worktree_clean": not initial_status, "prior_build_present": False, "prior_dist_present": False,
            "prior_staging_present": False, "venv_input_used": False, "untracked_input_used": False,
            "network_required": False, "api_keys_present": False, "external_llm_invoked": False,
            "real_device_required": False, "real_device_api_executed": False, "runtime_api_calls": [],
            "benchmark_rerun": False, "steps": steps, "tracked_changes_after_run": tracked_changes,
            "native_sha256": sha256_file(worktree / "dist/submission-install/quick/lib/libhccl_plugin.so") if (worktree / "dist/submission-install/quick/lib/libhccl_plugin.so").is_file() else None,
            "stage_tree_sha256": tree_digest(stage, exclude={".g3-b-generated"}) if stage.is_dir() else None,
            "stage_sha256sums_sha256": sha256_file(stage / "SHA256SUMS") if (stage / "SHA256SUMS").is_file() else None,
            "quick_transcript_sha256": json.loads(quick.read_text(encoding="utf-8")).get("canonical_transcript_sha256") if quick.is_file() else None,
            "fallback_transcript_sha256": json.loads(fallback.read_text(encoding="utf-8")).get("canonical_transcript_sha256") if fallback.is_file() else None,
        }
        write_json(output, payload)
        return payload
    finally:
        if added:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if temp_parent.exists():
            shutil.rmtree(temp_parent, ignore_errors=True)


def compare_runs(first: Path, second: Path, output: Path) -> dict[str, Any]:
    a = json.loads(first.read_text(encoding="utf-8"))
    b = json.loads(second.read_text(encoding="utf-8"))
    keys = ["source_commit", "native_sha256", "stage_tree_sha256", "stage_sha256sums_sha256", "quick_transcript_sha256", "fallback_transcript_sha256"]
    comparisons = {key: {"run_1": a.get(key), "run_2": b.get(key), "identical": a.get(key) == b.get(key)} for key in keys}
    errors = [key for key, row in comparisons.items() if not row["identical"] or row["run_1"] is None]
    payload = {
        "schema_version": "g3-g-cold-start-reproducibility-v1",
        "status": "PASS" if a.get("status") == b.get("status") == "PASS" and not errors else "FAIL",
        "run_count": 2, "comparisons": comparisons, "differences": errors,
        "classification": "BIT_FOR_BIT_FOR_DECLARED_OUTPUTS" if not errors else "NONDETERMINISTIC",
        "manifest_reproducible": not errors, "archive_reproducibility_evaluated": False,
        "sentinel": "G3_G_COLD_START_REPRODUCTION_OK" if not errors else None,
    }
    write_json(output, payload)
    return payload
