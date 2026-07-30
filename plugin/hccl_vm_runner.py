"""Command planning and execution boundary for official HCCL-VM validation."""

from __future__ import annotations

import base64
import os
import platform
import posixpath
import re
import shlex
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

from plugin.hccl_vm_backend import Backend, HcclVmConfig
from plugin.hccl_vm_checker import parse_official_result
from plugin.hccl_vm_env import HcclVmEnvironment
from plugin.hccl_vm_registry import (
    ResolvedCollectiveContract,
    build_hccl_test_argv,
    resolve_collective_request,
)


@dataclass(frozen=True)
class OfficialCollectiveRequest:
    primitive: str = "AllReduce"
    rank_count: int = 2
    dtype: str = "int32"
    reduce_op: str | None = None
    elements: int = 16

    def resolve(self) -> ResolvedCollectiveContract:
        return resolve_collective_request(
            primitive=self.primitive,
            rank_count=self.rank_count,
            dtype=self.dtype,
            reduce_op=self.reduce_op,
            elements=self.elements,
        )

    @property
    def byte_count(self) -> int:
        return self.resolve().byte_count

    def to_dict(self) -> dict[str, Any]:
        contract = self.resolve()
        result = asdict(self)
        result["primitive"] = contract.canonical_primitive
        result["byte_count"] = contract.byte_count
        result["resolved_contract"] = contract.to_dict()
        return result


class OfficialAllReduceRequest(OfficialCollectiveRequest):
    """Temporary G2-D source compatibility adapter.

    New callers must use :class:`OfficialCollectiveRequest`; this adapter keeps
    existing evidence/report fixtures importable while later checkpoints migrate
    them to the generic type.
    """

    def __init__(
        self,
        primitive: str = "AllReduce",
        rank_count: int = 2,
        dtype: str = "int32",
        reduce_op: str | None = "sum",
        elements: int = 16,
    ) -> None:
        super().__init__(
            primitive=primitive,
            rank_count=rank_count,
            dtype=dtype,
            reduce_op=reduce_op,
            elements=elements,
        )
        if self.resolve().canonical_primitive != "AllReduce":
            raise ValueError("OfficialAllReduceRequest requires AllReduce")


class HcclVmRunner:
    """Build and run the isolated official HCCL-VM validation workflow."""

    def __init__(
        self,
        config: HcclVmConfig,
        *,
        host_system: str | None = None,
        process_executor: Callable[..., Any] | None = None,
    ) -> None:
        if config.backend != Backend.ASCEND_HCCL_VM.value:
            raise ValueError(
                "HcclVmRunner requires backend=ASCEND_HCCL_VM"
            )
        self.config = config
        self.host_system = host_system or platform.system()
        self.process_executor = (
            process_executor or _execute_interactive_process
        )

    def dry_run(
        self,
        request: OfficialCollectiveRequest,
    ) -> dict[str, Any]:
        contract = request.resolve()
        startup_script = self._build_startup_script()
        interactive_commands = self._build_interactive_commands(request)
        transport_argv = self._build_transport_argv(startup_script)
        return {
            "selected_backend": self.config.backend,
            "execution_mode": "subprocess_hccl_test",
            "status": "DRY_RUN",
            "not_executed": True,
            "request": request.to_dict(),
            "registry": contract.to_dict(),
            "hccl_test_argv": build_hccl_test_argv(
                contract,
                self.config.hccl_test_bin,
            ),
            "topology": self.config.topology,
            "mock_comm": self.config.mock_comm,
            "startup_script": startup_script,
            "transport_argv": transport_argv,
            "interactive_commands": interactive_commands,
            "cleanup_commands": ["exit"],
            "success_requirements": _success_requirements(contract),
            "evidence_directory_pattern": posixpath.join(
                self.config.evidence_root,
                _evidence_directory_pattern(contract),
            ),
        }

    def verify(
        self,
        request: OfficialCollectiveRequest,
        *,
        environment: HcclVmEnvironment | None = None,
    ) -> "OfficialRunOutcome":
        contract = request.resolve()
        if contract.canonical_primitive not in {"AllReduce", "AllGather"}:
            raise ValueError(
                "official verification for this primitive is introduced by "
                "a later G2-E checkpoint"
            )
        environment_probe = environment or HcclVmEnvironment(
            self.config,
            host_system=self.host_system,
        )
        diagnosis = environment_probe.diagnose_for(contract)
        plan = self.dry_run(request)
        if diagnosis["status"] != "OK":
            return OfficialRunOutcome(
                diagnosis=diagnosis,
                plan=plan,
                result={
                    "status": diagnosis["status"],
                    "passed": False,
                    "failure_reasons": list(diagnosis["missing_items"]),
                },
                raw_log="",
                duration_seconds=0.0,
                timed_out=False,
            )

        startup_script = self._build_startup_script(for_execution=True)
        command = self._build_transport_argv(startup_script)
        steps = self._build_interactive_steps(request)
        started = time.monotonic()
        execution = self.process_executor(
            command,
            steps,
            timeout_seconds=self.config.timeout_seconds,
        )
        parsed = parse_official_result(
            execution.raw_log,
            outer_exit_code=execution.returncode,
            request=request,
        ).to_dict()
        cleanup_audit = _audit_related_processes(
            environment_probe,
            contract,
        )
        parsed["cleanup_audit"] = cleanup_audit
        if cleanup_audit["status"] not in {"CLEAN", "NOT_RUN_TEST_DOUBLE"}:
            parsed["passed"] = False
            parsed["failure_reasons"].append(
                "postflight process cleanup audit failed"
            )
            parsed["status"] = "FAIL_CLEANUP"
        if execution.timed_out:
            parsed["status"] = "ENV_BLOCKED_TIMEOUT"
            parsed["passed"] = False
            if "official validation timed out" not in parsed["failure_reasons"]:
                parsed["failure_reasons"].append(
                    "official validation timed out"
                )

        return OfficialRunOutcome(
            diagnosis=diagnosis,
            plan=plan,
            result=parsed,
            raw_log=execution.raw_log,
            duration_seconds=round(time.monotonic() - started, 3),
            timed_out=execution.timed_out,
        )

    def _build_startup_script(self, *, for_execution: bool = False) -> str:
        cann_path = shlex.quote(self.config.cann_path)
        install_dir = shlex.quote(self.config.hccl_vm_install_dir)
        set_env = shlex.quote(
            posixpath.join(self.config.cann_path, "set_env.sh")
        )
        hccl_config = shlex.quote(
            posixpath.join(
                self.config.hccl_vm_install_dir,
                "script",
                "hccl_config.sh",
            )
        )
        hccl_vm = shlex.quote(
            posixpath.join(
                self.config.hccl_vm_install_dir,
                "bin",
                "hccl-vm",
            )
        )
        topology = shlex.quote(self.config.topology)
        expansion_mode = shlex.quote(self.config.expansion_mode)
        rank_table = shlex.quote(
            posixpath.join(
                self.config.hccl_vm_install_dir,
                "data",
                "ranktable.json",
            )
        )
        check_only = " --check-only" if self.config.check_only else ""
        start_command = shlex.join([
            posixpath.join(
                self.config.hccl_vm_install_dir,
                "bin",
                "hccl-vm",
            ),
            "start",
            self.config.topology,
            *(["--check-only"] if self.config.check_only else []),
        ])
        if for_execution:
            run_command = (
                "timeout --signal=TERM --kill-after=10s "
                f"{self.config.timeout_seconds}s "
                "script -qef -E never -c "
                f"{shlex.quote(start_command)} /dev/null"
            )
            final_lines = [
                "set +e",
                run_command,
                "vm_rc=$?",
                "set -e",
                "printf '__HCCL_AGENT_VM_EXIT_CODE=%s\\n' \"$vm_rc\"",
                "exit \"$vm_rc\"",
            ]
        else:
            final_lines = [f"exec {hccl_vm} start {topology}{check_only}"]

        return "\n".join([
            "set -eo pipefail",
            f"export ASCEND_HOME_PATH={cann_path}",
            f"source {set_env}",
            f"cd {install_dir}/bin",
            "set +e",
            f"source {hccl_config}",
            "hccl_config_rc=$?",
            "set -e",
            f"source {set_env}",
            f"export ASCEND_HOME_PATH={cann_path}",
            f"export HCCL_VM_INSTALL_DIR={install_dir}",
            f"export RANK_TABLE_FILE={rank_table}",
            f"export HCCL_OP_EXPANSION_MODE={expansion_mode}",
            (
                "printf '__HCCL_AGENT_HCCL_CONFIG_EXIT_CODE=%s\\n' "
                "\"$hccl_config_rc\""
            ),
            *final_lines,
        ])

    def _build_interactive_commands(
        self,
        request: OfficialCollectiveRequest,
    ) -> list[str]:
        return [
            step.command
            for step in self._build_interactive_steps(request)
        ]

    def _build_interactive_steps(
        self,
        request: OfficialCollectiveRequest,
    ) -> list["InteractiveStep"]:
        mock_command = shlex.join([
            "hccl-vm",
            "mock-comm",
            self.config.mock_comm,
        ])
        test_command = shlex.join(build_hccl_test_argv(
            request.resolve(),
            self.config.hccl_test_bin,
        ))
        checker_command = shlex.join([
            "hccl-vm",
            "plugin",
            "run",
            "@checker",
        ])
        return [
            InteractiveStep(
                command=_command_with_exit_marker(
                    mock_command,
                    "__HCCL_AGENT_MOCK_EXIT_CODE",
                ),
                completion_marker="__HCCL_AGENT_MOCK_EXIT_CODE",
            ),
            InteractiveStep(
                command=_command_with_exit_marker(
                    test_command,
                    "__HCCL_AGENT_TEST_EXIT_CODE",
                ),
                completion_marker="__HCCL_AGENT_TEST_EXIT_CODE",
            ),
            InteractiveStep(
                command=_command_with_exit_marker(
                    checker_command,
                    "__HCCL_AGENT_CHECKER_EXIT_CODE",
                ),
                completion_marker="__HCCL_AGENT_CHECKER_EXIT_CODE",
            ),
            InteractiveStep(command="exit", completion_marker=None),
        ]

    def _build_transport_argv(self, startup_script: str) -> list[str]:
        if self.host_system == "Windows":
            payload = base64.b64encode(
                startup_script.encode("utf-8")
            ).decode("ascii")
            launcher = (
                f"source <(printf %s {payload} | base64 -d)"
            )
            return [
                "wsl.exe",
                "-d",
                self.config.wsl_distro,
                "--",
                "bash",
                "-lc",
                launcher,
            ]
        return ["bash", "-lc", startup_script]


@dataclass
class OfficialRunOutcome:
    diagnosis: dict[str, Any]
    plan: dict[str, Any]
    result: dict[str, Any]
    raw_log: str
    duration_seconds: float
    timed_out: bool

    def to_public_dict(self) -> dict[str, Any]:
        public = {
            **self.result,
            "duration_seconds": self.duration_seconds,
            "timed_out": self.timed_out,
            "diagnose_status": self.diagnosis["status"],
            "topology": self.plan["topology"],
            "mock_comm": self.plan["mock_comm"],
        }
        if not self.result.get("passed", False):
            public["log_tail"] = _log_tail(self.raw_log)
        return public


@dataclass(frozen=True)
class InteractiveStep:
    command: str
    completion_marker: str | None


@dataclass(frozen=True)
class ProcessExecution:
    raw_log: str
    returncode: int
    timed_out: bool


def _command_with_exit_marker(command: str, marker: str) -> str:
    return (
        f"{command}; command_rc=$?; "
        f"printf '{marker}=%s\\n' \"$command_rc\""
    )


def _success_requirements(
    contract: ResolvedCollectiveContract,
) -> list[str]:
    requirements = [
        f"{contract.executable_basename} exit code 0",
        f"collectiveType={contract.checker_collective_type}",
        f"rankCount={contract.rank_count}",
        f"dataType={contract.dtype.upper()}",
    ]
    if contract.checker_reduce_type is not None:
        requirements.append(
            f"reduceType={contract.checker_reduce_type}"
        )
    requirements.extend(
        [
            f"CheckerV3 stage {stage}=success"
            for stage in contract.required_checker_stages
        ]
    )
    requirements.extend([
        "Checker Success",
        "no Segmentation fault",
        "no MPI_ABORT",
        "no undefined symbol",
        "no fatal failure",
        "HCCL-VM normal shutdown",
        "outer process exit code 0",
    ])
    return requirements


def _evidence_directory_pattern(
    contract: ResolvedCollectiveContract,
) -> str:
    primitive = contract.canonical_primitive.casefold()
    return f"g2_e_{primitive}_<timestamp>"


def _audit_related_processes(
    environment: Any,
    contract: ResolvedCollectiveContract,
) -> dict[str, Any]:
    """Read only exact process names; never kill a potentially foreign run."""
    runner = getattr(environment, "run_linux_script", None)
    if not callable(runner):
        return {
            "status": "NOT_RUN_TEST_DOUBLE",
            "residual_processes": [],
        }
    result = runner("ps -eo pid=,comm=,args=")
    if result.returncode != 0:
        return {
            "status": "AUDIT_ERROR",
            "exit_code": result.returncode,
            "stderr": result.stderr.strip()[:1000],
            "residual_processes": [],
        }
    expected_names = {
        "hccl-vm",
        "mpirun",
        "checker",
        contract.executable_basename,
    }
    residual = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) < 2 or fields[1] not in expected_names:
            continue
        residual.append({
            "pid": fields[0],
            "comm": fields[1],
            "args": fields[2] if len(fields) == 3 else "",
        })
    return {
        "status": "CLEAN" if not residual else "RESIDUAL_PROCESSES",
        "exit_code": result.returncode,
        "residual_processes": residual,
    }


def _execute_interactive_process(
    command: list[str],
    steps: list[InteractiveStep],
    *,
    timeout_seconds: int,
) -> ProcessExecution:
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    if process.stdin is None or process.stdout is None:
        process.kill()
        raise RuntimeError("interactive process pipes were not created")

    output = bytearray()
    condition = threading.Condition()
    reader_closed = False

    def read_output() -> None:
        nonlocal reader_closed
        try:
            while True:
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                with condition:
                    output.extend(chunk)
                    condition.notify_all()
        finally:
            with condition:
                reader_closed = True
                condition.notify_all()

    reader = threading.Thread(
        target=read_output,
        name="hccl-vm-output-reader",
        daemon=True,
    )
    reader.start()
    deadline = time.monotonic() + timeout_seconds
    timed_out = False

    prompt_match = _wait_for_output(
        output,
        condition,
        lambda data: b"(hvm)$>" in data,
        process,
        reader_closed=lambda: reader_closed,
        deadline=deadline,
        start=0,
    )
    if not prompt_match:
        timed_out = process.poll() is None
    else:
        for step in steps:
            start = len(output)
            try:
                process.stdin.write((step.command + "\n").encode("utf-8"))
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                break
            if step.completion_marker is None:
                break

            marker_pattern = re.compile(
                re.escape(step.completion_marker.encode("ascii"))
                + rb"=(-?\d+)"
            )
            match = _wait_for_output(
                output,
                condition,
                lambda data, pattern=marker_pattern: pattern.search(data),
                process,
                reader_closed=lambda: reader_closed,
                deadline=deadline,
                start=start,
            )
            if match is None:
                timed_out = process.poll() is None
                break
            if int(match.group(1)) != 0:
                try:
                    process.stdin.write(b"exit\n")
                    process.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
                break

    try:
        process.stdin.close()
    except OSError:
        pass

    remaining = max(0.0, deadline - time.monotonic())
    try:
        process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    reader.join(timeout=5)
    raw_log = bytes(output).decode("utf-8", errors="replace")
    process.stdout.close()
    return ProcessExecution(
        raw_log=raw_log,
        returncode=124 if timed_out else int(process.returncode),
        timed_out=timed_out,
    )


def _wait_for_output(
    output: bytearray,
    condition: threading.Condition,
    matcher: Callable[[bytes], Any],
    process: subprocess.Popen,
    *,
    reader_closed: Callable[[], bool],
    deadline: float,
    start: int,
) -> Any:
    while True:
        with condition:
            matched = matcher(bytes(output[start:]))
            if matched:
                return matched
            if reader_closed() or process.poll() is not None:
                return None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            condition.wait(timeout=min(0.2, remaining))


def _log_tail(log_text: str, line_count: int = 80) -> str:
    return "\n".join(log_text.splitlines()[-line_count:])
