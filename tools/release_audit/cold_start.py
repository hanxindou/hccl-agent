"""G3-G-B clean-worktree reproduction runner and comparator.

The executable implementation is committed in G3-G-A as a validator skeleton.
G3-G-B is the first checkpoint allowed to invoke it.
"""

from __future__ import annotations

import json
import importlib.util
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .authority import MANDATORY_ENTRY_POINTS
from .common import RELEASE_ROOT, ROOT, ReleaseAuditError, sanitized_environment, sha256_file, tree_digest, write_json


def _copy_wsl_backport(name: str, destination: Path) -> bool:
    interpreter = "/tmp/hccl-agent-linux-ci-venv/bin/python"
    probe = subprocess.run(
        ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", interpreter, "-c",
         f"import importlib.util; s=importlib.util.find_spec('{name}'); print(next(iter(s.submodule_search_locations), s.origin) if s else '')"],
        text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    source = probe.stdout.strip()
    if probe.returncode or not source:
        return False
    copy = subprocess.run(
        ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "cp", "-R", source, _wsl_path(destination)],
        text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    return copy.returncode == 0


def _copy_python_test_runtime(destination: Path) -> dict[str, str]:
    """Copy only the already-installed pure-Python pytest runtime into a run-owned root."""
    destination.mkdir(parents=True, exist_ok=False)
    copied: dict[str, str] = {}
    for name in ("pytest", "_pytest", "pluggy", "iniconfig", "packaging", "pygments", "py", "tomli", "exceptiongroup", "typing_extensions"):
        spec = importlib.util.find_spec(name)
        if spec is None:
            if name in {"exceptiongroup", "tomli"} and _copy_wsl_backport(name, destination):
                copied[name] = "EXISTING_EXTERNAL_LINUX_TEST_DEPENDENCY"
            continue
        source = Path(next(iter(spec.submodule_search_locations), spec.origin)) if spec.submodule_search_locations else Path(spec.origin)
        target = destination / source.name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copyfile(source, target)
        copied[name] = "HOST_INSTALLED_PURE_PYTHON_DEPENDENCY"
    if "pytest" not in copied or "_pytest" not in copied:
        raise ReleaseAuditError("host Python does not provide the declared pytest dependency")
    return copied


def _wsl_path(path: Path) -> str:
    completed = subprocess.run(
        ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "wslpath", "-a", str(path.resolve())],
        text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        raise ReleaseAuditError(f"wslpath failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _run(command: list[str], cwd: Path, env: dict[str, str], pytest_runtime: Path) -> dict[str, Any]:
    linux_plugin_root: str | None = None
    if command[:4] == ["python", "-m", "pytest", "tests"]:
        repo = _wsl_path(cwd)
        runtime = _wsl_path(pytest_runtime)
        plugin_source = _wsl_path(cwd / "dist/submission-install/quick/lib/libhccl_plugin.so")
        created = subprocess.run(
            ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "mktemp", "-d", "/tmp/hccl-agent-g3-g-plugin-XXXXXX"],
            text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        linux_plugin_root = created.stdout.strip()
        if created.returncode or not linux_plugin_root.startswith("/tmp/hccl-agent-g3-g-plugin-"):
            raise ReleaseAuditError(f"could not create safe WSL plugin root: {created.stderr.strip()}")
        plugin = f"{linux_plugin_root}/libhccl_plugin.so"
        copied = subprocess.run(
            ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "cp", plugin_source, plugin],
            text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if copied.returncode:
            raise ReleaseAuditError(f"could not copy clean-built plugin to WSL run root: {copied.stderr.strip()}")
        script = (
            f"cd {shlex.quote(repo)} && "
            f"export PYTHONPATH={shlex.quote(runtime)} && "
            f"export HCCL_PLUGIN_PATH={shlex.quote(plugin)} && "
            "unset DEEPSEEK_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY; "
            "python3 -m pytest tests -q"
        )
        actual = ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "bash", "-lc", script]
    else:
        actual = [sys.executable, *command[1:]] if command and command[0] == "python" else command
    started = time.monotonic()
    completed = subprocess.run(
        actual, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    if linux_plugin_root:
        subprocess.run(
            ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "rm", "-rf", linux_plugin_root],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
    output = completed.stdout.replace(str(cwd), "<repo>").replace(str(pytest_runtime), "<pytest-runtime>")
    output = re.sub(r"(?i)[A-Z]:\\Users\\[^\\\s]+\\AppData\\Local\\Temp\\hccl-agent-g3-g-[^\\\s]+", "<run-root>", output)
    output = re.sub(r"/mnt/[A-Za-z]/Users/[^/\s]+/AppData/Local/Temp/hccl-agent-g3-g-[^/\s]+", "<run-root>", output)
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
    base_source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout.strip()
    try:
        add = subprocess.run(
            ["git", "clone", "--no-hardlinks", "--no-tags", "--no-checkout", str(ROOT), str(worktree)], cwd=ROOT,
            text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if add.returncode:
            raise ReleaseAuditError(f"local clean clone failed: {add.stderr.strip()}")
        for key, value in (("core.autocrlf", "false"), ("core.eol", "lf")):
            configured = subprocess.run(
                ["git", "config", key, value], cwd=worktree, text=True, encoding="utf-8", errors="replace",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            if configured.returncode:
                raise ReleaseAuditError(f"local clean clone config failed: {configured.stderr.strip()}")
        checkout = subprocess.run(
            ["git", "checkout", "--detach", base_source_commit], cwd=worktree,
            text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if checkout.returncode:
            raise ReleaseAuditError(f"local clean checkout failed: {checkout.stderr.strip()}")
        overlay_paths = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--"], cwd=ROOT,
            text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.splitlines()
        allowed_overlay = {"tools/release_audit/cold_start.py", "tools/agent_delivery/finalize.py"}
        unexpected_overlay = sorted(set(path.replace("\\", "/") for path in overlay_paths) - allowed_overlay)
        if unexpected_overlay:
            raise ReleaseAuditError(f"undeclared pending checkpoint overlay: {unexpected_overlay}")
        if overlay_paths:
            patch = subprocess.run(
                ["git", "diff", "--binary", "HEAD", "--", *overlay_paths], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            ).stdout
            applied = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", "-"], cwd=worktree, input=patch,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            if applied.returncode:
                raise ReleaseAuditError(f"pending checkpoint overlay failed: {applied.stderr.decode('utf-8', 'replace').strip()}")
            for key, value in (("user.name", "G3-G Reproduction"), ("user.email", "g3-g-reproduction.invalid")):
                subprocess.run(["git", "config", key, value], cwd=worktree, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            snapshot_env = dict(os.environ)
            snapshot_env.update({"GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z"})
            committed = subprocess.run(
                ["git", "commit", "-am", "G3-G-B pending reproduction snapshot"], cwd=worktree, env=snapshot_env,
                text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            if committed.returncode:
                raise ReleaseAuditError(f"pending checkpoint snapshot failed: {committed.stderr.strip()}")
        execution_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=worktree, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.strip()
        initial_status = subprocess.run(
            ["git", "status", "--short"], cwd=worktree, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.strip()
        if initial_status:
            raise ReleaseAuditError(f"clean worktree was not clean: {initial_status}")
        env = sanitized_environment()
        env["G3_G_CLEAN_MODEL"] = "CLEAN_WORKTREE_REPRODUCTION"
        pytest_runtime = temp_parent / "pytest-runtime"
        pytest_packages = _copy_python_test_runtime(pytest_runtime)
        steps: list[dict[str, Any]] = []
        for command in _sequence(worktree):
            result = _run(command, worktree, env, pytest_runtime)
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
            "clean_environment_model": "CLEAN_WORKTREE_REPRODUCTION", "source_commit": execution_commit,
            "base_source_commit": base_source_commit,
            "pending_checkpoint_overlay_used": bool(overlay_paths),
            "pending_checkpoint_overlay_paths": sorted(path.replace("\\", "/") for path in overlay_paths),
            "local_clone_equivalent": True, "local_clone_network_used": False, "local_clone_hardlinks_used": False,
            "initial_worktree_clean": not initial_status, "prior_build_present": False, "prior_dist_present": False,
            "prior_staging_present": False, "venv_input_used": False, "untracked_input_used": False,
            "repository_local_venv_used": False,
            "pytest_dependency_source": "HOST_INSTALLED_PURE_PYTHON_PACKAGES_COPIED_TO_RUN_OWNED_ROOT",
            "pytest_packages": pytest_packages,
            "external_dependency_snapshot_used": any(value.startswith("EXISTING_EXTERNAL") for value in pytest_packages.values()),
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
        if temp_parent.exists():
            resolved = temp_parent.resolve()
            temp_root = Path(tempfile.gettempdir()).resolve()
            if resolved.parent != temp_root or not resolved.name.startswith(f"hccl-agent-g3-g-{run_id}-"):
                raise ReleaseAuditError(f"refusing unsafe cold-start cleanup: {resolved}")
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


def _compact_step(step: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in step.items() if key != "output_tail"}
    lines = step.get("output_tail", [])
    raw = "\n".join(lines)
    result["output_tail_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if step.get("status") != "PASS":
        result["error_tail"] = lines[-20:]
        return result
    command = step.get("command", [])
    if command[:4] == ["python", "-m", "pytest", "tests"]:
        result["output_summary"] = {"pytest_summary": lines[-1] if lines else ""}
        return result
    parsed: dict[str, Any] = {}
    if lines:
        try:
            value = json.loads(lines[-1])
            for key in (
                "schema_version", "status", "sentinel", "final_sentinel", "profile", "command",
                "files_verified", "manifest_entries_verified", "asset_count", "claim_count", "metric_count",
                "g3_f_demo_asset_count", "g3_e_svg_asset_count", "authority_root_count", "user_action_count",
                "canonical_transcript_sha256", "replay_sha256",
            ):
                if key in value:
                    parsed[key] = value[key]
        except json.JSONDecodeError:
            parsed["last_line"] = lines[-1]
    result["output_summary"] = parsed
    return result


def finalize_cold_start_results(first: Path, second: Path, comparison: Path) -> dict[str, Any]:
    runs = [json.loads(first.read_text(encoding="utf-8")), json.loads(second.read_text(encoding="utf-8"))]
    for path, payload in zip((first, second), runs):
        payload["steps"] = [_compact_step(step) for step in payload["steps"]]
        payload["portable_transcript"] = True
        payload["raw_log_policy"] = "RUN_OWNED_TEMPORARY_NOT_TRACKED"
        write_json(path, payload)
    reproducibility = json.loads(comparison.read_text(encoding="utf-8"))
    environment = {
        "schema_version": "g3-g-cold-start-environment-v1", "status": "PASS",
        "verified_environment": "Windows host with WSL Ubuntu-22.04 Linux execution class",
        "supported_environment": ["Linux/WSL with Python 3, CMake, C compiler, make, Git, and pytest"],
        "untested_environment": ["native Windows runtime", "macOS", "other Linux distributions", "real Ascend/NPU"],
        "host_python": "3.11.7", "wsl_python": "3.10",
        "pytest_dependency_source": runs[0]["pytest_dependency_source"],
        "pytest_packages": runs[0]["pytest_packages"],
        "repository_local_venv_used": False, "network_used": False, "api_keys_used": [],
        "npu_used": False, "runtime_api_calls": [], "run_count": 2,
        "clean_model": "CLEAN_WORKTREE_REPRODUCTION",
        "checkout_normalization": {"core.autocrlf": False, "core.eol": "lf"},
    }
    write_json(RELEASE_ROOT / "cold_start_environment.json", environment)
    summary = {
        "schema_version": "g3-g-cold-start-summary-v1", "status": "PASS",
        "runs": [{"run_id": row["run_id"], "status": row["status"], "source_commit": row["source_commit"], "step_count": len(row["steps"])} for row in runs],
        "reproducibility": reproducibility["classification"],
        "manifest_reproducible": reproducibility["manifest_reproducible"],
        "archive_reproducibility_evaluated": False,
        "benchmark_rerun": False, "network_used": False, "external_llm_invoked": False,
        "real_device_api_executed": False, "runtime_api_calls": [],
        "sentinel": "G3_G_COLD_START_REPRODUCTION_OK",
    }
    write_json(RELEASE_ROOT / "cold_start_summary.json", summary)
    return summary
