"""Read-only discovery for the external official HCCL-VM toolchain."""

from __future__ import annotations

import base64
import platform
import posixpath
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

from plugin.hccl_vm_backend import Backend, HcclVmConfig


EXPECTED_HCOMM_BRANCH = "competition/campus-2026"
EXPECTED_HCOMM_COMMIT = "c8a3dc68a37315aa1e908a971fa706abe612f6ee"
EXPECTED_HCCL_BRANCH = "competition/campus-2026"
EXPECTED_HCCL_COMMIT = "2c87cc1937bab23b8574ef24017c03572d3340e2"
PROBE_PREFIX = "__HCCL_AGENT_PROBE__"


@dataclass(frozen=True)
class LinuxCommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class HcclVmEnvironment:
    """Discover HCCL-VM without importing CANN libraries or starting the VM."""

    def __init__(
        self,
        config: HcclVmConfig,
        *,
        host_system: str | None = None,
        command_runner: Callable[..., Any] | None = None,
        which: Callable[[str], str | None] | None = None,
    ) -> None:
        self.config = config
        self.host_system = host_system or platform.system()
        self.command_runner = command_runner or subprocess.run
        self.which = which or shutil.which

    def diagnose(self) -> dict[str, Any]:
        report = self._base_report()
        if self.config.backend != Backend.ASCEND_HCCL_VM.value:
            report["missing_items"].append(
                "selected_backend must be ASCEND_HCCL_VM for official diagnose"
            )
            report["status"] = "ENV_BLOCKED_BACKEND"
            return report

        transport_error = self._transport_error()
        if transport_error:
            report["wsl"]["error"] = transport_error
            report["missing_items"].append(transport_error)
            report["status"] = "ENV_BLOCKED_WSL"
            return report

        result = self.run_linux_script(self._build_probe_script())
        report["wsl"]["command"] = _display_command(result.command)
        report["wsl"]["exit_code"] = result.returncode
        report["wsl"]["available"] = result.returncode == 0
        report["wsl"]["stderr"] = result.stderr.strip()

        values = parse_probe_output(result.stdout)
        self._apply_probe_values(report, values)
        self._classify_report(report, result.returncode)
        return report

    def run_linux_script(self, script: str) -> LinuxCommandResult:
        if self.host_system == "Windows":
            payload = base64.b64encode(script.encode("utf-8")).decode("ascii")
            launcher = f"printf %s {payload} | base64 -d | bash"
            command = [
                "wsl.exe",
                "-d",
                self.config.wsl_distro,
                "--",
                "bash",
                "-lc",
                launcher,
            ]
        else:
            command = ["bash", "-lc", script]

        try:
            completed = self.command_runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return LinuxCommandResult(
                command=command,
                returncode=124 if isinstance(exc, subprocess.TimeoutExpired) else 127,
                stdout=getattr(exc, "stdout", "") or "",
                stderr=str(exc),
            )

        return LinuxCommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )

    def _base_report(self) -> dict[str, Any]:
        release = platform.release().lower()
        running_in_wsl = (
            self.host_system == "Linux" and "microsoft" in release
        )
        return {
            "selected_backend": self.config.backend,
            "execution_mode": "subprocess_hccl_test",
            "host_os": self.host_system,
            "wsl": {
                "distro": self.config.wsl_distro,
                "transport": (
                    "wsl.exe" if self.host_system == "Windows" else "direct_bash"
                ),
                "running_in_wsl": running_in_wsl,
                "available": False,
            },
            "cann": {
                "path": self.config.cann_path,
                "set_env_path": posixpath.join(
                    self.config.cann_path, "set_env.sh"
                ),
                "version": None,
                "available": False,
            },
            "hccl_vm": {
                "install_dir": self.config.hccl_vm_install_dir,
                "executable_path": posixpath.join(
                    self.config.hccl_vm_install_dir, "bin", "hccl-vm"
                ),
                "config_path": posixpath.join(
                    self.config.hccl_vm_install_dir,
                    "script",
                    "hccl_config.sh",
                ),
                "executable": False,
                "config_available": False,
            },
            "hccl_test": {
                "bin_dir": self.config.hccl_test_bin,
                "all_reduce_path": posixpath.join(
                    self.config.hccl_test_bin, "all_reduce_test"
                ),
                "executable": False,
                "dependencies_resolved": False,
            },
            "checker": {
                "path": posixpath.join(
                    self.config.hccl_vm_install_dir,
                    "plugin",
                    "checker",
                    "checker",
                ),
                "available": False,
            },
            "topology": {
                "name": self.config.topology,
                "path": posixpath.join(
                    self.config.hccl_vm_install_dir,
                    "config",
                    "cluster",
                    self.config.topology,
                ),
                "available": False,
            },
            "mock_comm": {
                "name": self.config.mock_comm,
                "path": posixpath.join(
                    self.config.hccl_vm_install_dir,
                    "config",
                    "topo_meta",
                    f"{self.config.mock_comm}.yaml",
                ),
                "available": False,
            },
            "mpi": {
                "path": None,
                "implementation": None,
                "available": False,
            },
            "runner_tools": {
                "script_path": None,
                "timeout_path": None,
                "sudo_non_interactive": False,
                "available": False,
            },
            "hcomm": {
                "path": self.config.hcomm_source_dir,
                "branch": None,
                "commit": None,
                "worktree": None,
                "expected_branch": EXPECTED_HCOMM_BRANCH,
                "expected_commit": EXPECTED_HCOMM_COMMIT,
            },
            "hccl": {
                "path": self.config.hccl_source_dir,
                "branch": None,
                "commit": None,
                "worktree": None,
                "expected_branch": EXPECTED_HCCL_BRANCH,
                "expected_commit": EXPECTED_HCCL_COMMIT,
            },
            "missing_items": [],
            "status": "ENV_BLOCKED",
        }

    def _transport_error(self) -> str | None:
        if self.host_system == "Windows" and self.which("wsl.exe") is None:
            return "wsl.exe is not available"
        if self.host_system != "Windows" and self.which("bash") is None:
            return "bash is not available"
        return None

    def _build_probe_script(self) -> str:
        paths = {
            "cann": self.config.cann_path,
            "set_env": posixpath.join(self.config.cann_path, "set_env.sh"),
            "install": self.config.hccl_vm_install_dir,
            "hccl_vm": posixpath.join(
                self.config.hccl_vm_install_dir, "bin", "hccl-vm"
            ),
            "hccl_config": posixpath.join(
                self.config.hccl_vm_install_dir, "script", "hccl_config.sh"
            ),
            "all_reduce": posixpath.join(
                self.config.hccl_test_bin, "all_reduce_test"
            ),
            "checker": posixpath.join(
                self.config.hccl_vm_install_dir,
                "plugin",
                "checker",
                "checker",
            ),
            "topology": posixpath.join(
                self.config.hccl_vm_install_dir,
                "config",
                "cluster",
                self.config.topology,
            ),
            "mock_comm": posixpath.join(
                self.config.hccl_vm_install_dir,
                "config",
                "topo_meta",
                f"{self.config.mock_comm}.yaml",
            ),
            "hcomm": self.config.hcomm_source_dir,
            "hccl": self.config.hccl_source_dir,
        }
        assignments = "\n".join(
            f"{name}={shlex.quote(value)}" for name, value in paths.items()
        )
        return f"""set +e
{assignments}
emit() {{ printf '{PROBE_PREFIX}%s=%s\\n' "$1" "$2"; }}
bool_file() {{ if [ -f "$2" ]; then emit "$1" true; else emit "$1" false; fi; }}
bool_exec() {{ if [ -x "$2" ]; then emit "$1" true; else emit "$1" false; fi; }}

bool_file cann_available "$set_env"
bool_exec hccl_vm_executable "$hccl_vm"
bool_file hccl_config_available "$hccl_config"
bool_exec hccl_test_executable "$all_reduce"
bool_exec checker_available "$checker"
bool_file topology_available "$topology"
bool_file mock_comm_available "$mock_comm"

cann_version=
for version_file in "$cann/x86_64-linux/ascend_toolkit_install.info" "$cann/opp/version.info"; do
    if [ -f "$version_file" ]; then
        cann_version=$(awk -F= 'tolower($1) == "version" {{gsub(/"/, "", $2); print $2; exit}}' "$version_file")
        [ -n "$cann_version" ] && break
    fi
done
emit cann_version "$cann_version"

mpi_path=$(command -v mpirun 2>/dev/null)
emit mpi_path "$mpi_path"
if [ -n "$mpi_path" ]; then
    mpi_version=$(mpirun --version 2>/dev/null | head -n 1)
    emit mpi_implementation "$mpi_version"
else
    emit mpi_implementation ""
fi
emit script_path "$(command -v script 2>/dev/null)"
emit timeout_path "$(command -v timeout 2>/dev/null)"
if [ "$(id -u)" -eq 0 ] || sudo -n true >/dev/null 2>&1; then
    emit sudo_non_interactive true
else
    emit sudo_non_interactive false
fi

dependencies_resolved=false
if [ -f "$set_env" ] && [ -x "$all_reduce" ]; then
    source "$set_env" >/dev/null 2>&1
    if ldd "$all_reduce" 2>&1 | grep -q 'not found'; then
        dependencies_resolved=false
    else
        dependencies_resolved=true
    fi
fi
emit dependencies_resolved "$dependencies_resolved"

probe_git_repo() {{
    repo_name="$1"
    repo_path="$2"
    git_safe=(git -c "safe.directory=$repo_path" -C "$repo_path")
    if "${{git_safe[@]}}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        emit "${{repo_name}}_branch" "$("${{git_safe[@]}}" branch --show-current 2>/dev/null)"
        emit "${{repo_name}}_commit" "$("${{git_safe[@]}}" rev-parse HEAD 2>/dev/null)"
        if [ -n "$("${{git_safe[@]}}" status --porcelain 2>/dev/null)" ]; then
            emit "${{repo_name}}_worktree" dirty
        else
            emit "${{repo_name}}_worktree" clean
        fi
    fi
}}
probe_git_repo hcomm "$hcomm"
probe_git_repo hccl "$hccl"
exit 0
"""

    def _apply_probe_values(
        self,
        report: dict[str, Any],
        values: dict[str, str],
    ) -> None:
        report["cann"]["available"] = _as_bool(values.get("cann_available"))
        report["cann"]["version"] = values.get("cann_version") or None
        report["hccl_vm"]["executable"] = _as_bool(
            values.get("hccl_vm_executable")
        )
        report["hccl_vm"]["config_available"] = _as_bool(
            values.get("hccl_config_available")
        )
        report["hccl_test"]["executable"] = _as_bool(
            values.get("hccl_test_executable")
        )
        report["hccl_test"]["dependencies_resolved"] = _as_bool(
            values.get("dependencies_resolved")
        )
        report["checker"]["available"] = _as_bool(
            values.get("checker_available")
        )
        report["topology"]["available"] = _as_bool(
            values.get("topology_available")
        )
        report["mock_comm"]["available"] = _as_bool(
            values.get("mock_comm_available")
        )
        report["mpi"]["path"] = values.get("mpi_path") or None
        report["mpi"]["implementation"] = (
            values.get("mpi_implementation") or None
        )
        report["mpi"]["available"] = bool(report["mpi"]["path"])
        report["runner_tools"]["script_path"] = (
            values.get("script_path") or None
        )
        report["runner_tools"]["timeout_path"] = (
            values.get("timeout_path") or None
        )
        report["runner_tools"]["sudo_non_interactive"] = _as_bool(
            values.get("sudo_non_interactive")
        )
        report["runner_tools"]["available"] = bool(
            report["runner_tools"]["script_path"]
            and report["runner_tools"]["timeout_path"]
        )
        for repo_name in ("hcomm", "hccl"):
            report[repo_name]["branch"] = values.get(f"{repo_name}_branch")
            report[repo_name]["commit"] = values.get(f"{repo_name}_commit")
            report[repo_name]["worktree"] = values.get(
                f"{repo_name}_worktree"
            )

    def _classify_report(
        self,
        report: dict[str, Any],
        returncode: int,
    ) -> None:
        required = [
            ("cann.set_env.sh", report["cann"]["available"]),
            ("CANN version", bool(report["cann"]["version"])),
            ("hccl-vm executable", report["hccl_vm"]["executable"]),
            ("HCCL-VM hccl_config.sh", report["hccl_vm"]["config_available"]),
            ("all_reduce_test executable", report["hccl_test"]["executable"]),
            (
                "all_reduce_test shared libraries",
                report["hccl_test"]["dependencies_resolved"],
            ),
            ("checker plugin", report["checker"]["available"]),
            ("topology profile", report["topology"]["available"]),
            ("mock-comm profile", report["mock_comm"]["available"]),
            ("mpirun", report["mpi"]["available"]),
            (
                "script and timeout runner tools",
                report["runner_tools"]["available"],
            ),
            (
                "root or non-interactive sudo for HCCL-VM startup",
                report["runner_tools"]["sudo_non_interactive"],
            ),
        ]
        report["missing_items"].extend(
            name for name, available in required if not available
        )
        if returncode != 0:
            report["missing_items"].append(
                f"environment probe exited with code {returncode}"
            )

        for repo_name in ("hcomm", "hccl"):
            repo = report[repo_name]
            if not repo["branch"] or not repo["commit"]:
                report["missing_items"].append(f"{repo_name} git metadata")
                continue
            if (
                repo["branch"] != repo["expected_branch"]
                or repo["commit"] != repo["expected_commit"]
            ):
                report["missing_items"].append(
                    f"{repo_name} branch/commit mismatch"
                )

        report["status"] = (
            "OK" if not report["missing_items"] else "ENV_BLOCKED"
        )


def parse_probe_output(stdout: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        if not line.startswith(PROBE_PREFIX):
            continue
        payload = line[len(PROBE_PREFIX):]
        key, separator, value = payload.partition("=")
        if separator and key:
            values[key] = value
    return values


def _as_bool(value: str | None) -> bool:
    return value == "true"


def _display_command(command: list[str]) -> list[str]:
    if not command:
        return []
    label = (
        "<base64-encoded probe script>"
        if command[0].lower().endswith("wsl.exe")
        else "<probe script>"
    )
    return [*command[:-1], label]
