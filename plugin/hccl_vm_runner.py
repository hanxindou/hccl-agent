"""Command planning and execution boundary for official HCCL-VM validation."""

from __future__ import annotations

import base64
import platform
import posixpath
import shlex
from dataclasses import asdict, dataclass
from typing import Any

from plugin.hccl_vm_backend import Backend, HcclVmConfig


@dataclass(frozen=True)
class OfficialAllReduceRequest:
    primitive: str = "AllReduce"
    rank_count: int = 2
    dtype: str = "int32"
    reduce_op: str = "sum"
    elements: int = 16

    def __post_init__(self) -> None:
        canonical_primitive = self.primitive.strip().lower()
        canonical_dtype = self.dtype.strip().lower()
        canonical_op = self.reduce_op.strip().lower()
        if canonical_primitive != "allreduce":
            raise ValueError("G2-D supports only primitive=AllReduce")
        if self.rank_count != 2:
            raise ValueError("G2-D supports only rank_count=2")
        if canonical_dtype != "int32":
            raise ValueError("G2-D supports only dtype=int32")
        if canonical_op != "sum":
            raise ValueError("G2-D supports only reduce_op=sum")
        if self.elements != 16:
            raise ValueError("G2-D supports only elements=16")
        object.__setattr__(self, "primitive", "AllReduce")
        object.__setattr__(self, "dtype", "int32")
        object.__setattr__(self, "reduce_op", "sum")

    @property
    def byte_count(self) -> int:
        return self.elements * 4

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["byte_count"] = self.byte_count
        return result


class HcclVmRunner:
    """Build a shell-safe official validation plan.

    Process execution is added in G2-D-5. This class intentionally has no
    subprocess side effect while serving dry-run.
    """

    def __init__(
        self,
        config: HcclVmConfig,
        *,
        host_system: str | None = None,
    ) -> None:
        if config.backend != Backend.ASCEND_HCCL_VM.value:
            raise ValueError(
                "HcclVmRunner requires backend=ASCEND_HCCL_VM"
            )
        self.config = config
        self.host_system = host_system or platform.system()

    def dry_run(
        self,
        request: OfficialAllReduceRequest,
    ) -> dict[str, Any]:
        startup_script = self._build_startup_script()
        interactive_commands = self._build_interactive_commands(request)
        transport_argv = self._build_transport_argv(startup_script)
        return {
            "selected_backend": self.config.backend,
            "execution_mode": "subprocess_hccl_test",
            "status": "DRY_RUN",
            "not_executed": True,
            "request": request.to_dict(),
            "topology": self.config.topology,
            "mock_comm": self.config.mock_comm,
            "startup_script": startup_script,
            "transport_argv": transport_argv,
            "interactive_commands": interactive_commands,
            "cleanup_commands": ["exit"],
            "success_requirements": [
                "all_reduce_test exit code 0",
                "collectiveType=AllReduce",
                "rankCount=2",
                "dataType=INT32",
                "reduceType=SUM",
                "Checker Success",
                "no Segmentation fault",
                "no MPI_ABORT",
                "no undefined symbol",
                "no fatal failure",
                "HCCL-VM normal shutdown",
                "outer process exit code 0",
            ],
            "evidence_directory_pattern": posixpath.join(
                self.config.evidence_root,
                "g2_d_<timestamp>",
            ),
        }

    def _build_startup_script(self) -> str:
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
        return "\n".join([
            "set -eo pipefail",
            f"export ASCEND_HOME_PATH={cann_path}",
            f"source {set_env}",
            f"cd {install_dir}/bin",
            f"source {hccl_config}",
            f"export ASCEND_HOME_PATH={cann_path}",
            f"export HCCL_VM_INSTALL_DIR={install_dir}",
            f"export RANK_TABLE_FILE={rank_table}",
            f"export HCCL_OP_EXPANSION_MODE={expansion_mode}",
            (
                f"exec {hccl_vm} start {topology}{check_only}"
            ),
        ])

    def _build_interactive_commands(
        self,
        request: OfficialAllReduceRequest,
    ) -> list[str]:
        hccl_vm_command = shlex.join([
            "hccl-vm",
            "mock-comm",
            self.config.mock_comm,
        ])
        all_reduce_path = posixpath.join(
            self.config.hccl_test_bin,
            "all_reduce_test",
        )
        test_command = shlex.join([
            "mpirun",
            "--allow-run-as-root",
            "--oversubscribe",
            "-np",
            str(request.rank_count),
            all_reduce_path,
            "-b",
            str(request.byte_count),
            "-e",
            str(request.byte_count),
            "-d",
            request.dtype,
            "-o",
            request.reduce_op,
            "-w",
            "0",
            "-n",
            "1",
            "-c",
            "1",
        ])
        checker_command = shlex.join([
            "hccl-vm",
            "plugin",
            "run",
            "@checker",
        ])
        return [
            hccl_vm_command,
            test_command,
            checker_command,
            "exit",
        ]

    def _build_transport_argv(self, startup_script: str) -> list[str]:
        if self.host_system == "Windows":
            payload = base64.b64encode(
                startup_script.encode("utf-8")
            ).decode("ascii")
            launcher = f"printf %s {payload} | base64 -d | bash"
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
