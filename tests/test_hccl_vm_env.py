"""G2-D-2 tests for read-only HCCL-VM environment discovery."""

import subprocess
import unittest

from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_env import (
    EXPECTED_HCCL_COMMIT,
    EXPECTED_HCOMM_COMMIT,
    HcclVmEnvironment,
    PROBE_PREFIX,
    parse_probe_output,
)
from plugin.hccl_vm_registry import resolve_collective_request


def _probe_output(**overrides):
    values = {
        "cann_available": "true",
        "cann_version": "9.1.0",
        "hccl_vm_executable": "true",
        "hccl_config_available": "true",
        "hccl_test_AllReduce_executable": "true",
        "hccl_test_AllReduce_dependencies_resolved": "true",
        "hccl_test_AllGather_executable": "true",
        "hccl_test_AllGather_dependencies_resolved": "true",
        "hccl_test_ReduceScatter_executable": "true",
        "hccl_test_ReduceScatter_dependencies_resolved": "true",
        "checker_available": "true",
        "topology_available": "true",
        "mock_comm_available": "true",
        "mpi_path": "/usr/bin/mpirun",
        "mpi_implementation": "mpirun (Open MPI) 4.1.2",
        "script_path": "/usr/bin/script",
        "timeout_path": "/usr/bin/timeout",
        "sudo_non_interactive": "true",
        "hcomm_branch": "competition/campus-2026",
        "hcomm_commit": EXPECTED_HCOMM_COMMIT,
        "hcomm_worktree": "clean",
        "hccl_branch": "competition/campus-2026",
        "hccl_commit": EXPECTED_HCCL_COMMIT,
        "hccl_worktree": "clean",
    }
    values.update(overrides)
    return "\n".join(
        f"{PROBE_PREFIX}{key}={value}" for key, value in values.items()
    )


class FakeRunner:

    def __init__(self, stdout, returncode=0, stderr=""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            self.returncode,
            stdout=self.stdout,
            stderr=self.stderr,
        )


class TestHcclVmEnvironment(unittest.TestCase):

    def setUp(self):
        self.config = HcclVmConfig(backend="ASCEND_HCCL_VM")

    def test_parse_probe_output_ignores_unrelated_lines(self):
        values = parse_probe_output(
            "tool noise\n"
            f"{PROBE_PREFIX}cann_version=9.1.0\n"
            f"{PROBE_PREFIX}checker_available=true\n"
        )
        self.assertEqual(values["cann_version"], "9.1.0")
        self.assertEqual(values["checker_available"], "true")
        self.assertNotIn("tool noise", values)

    def test_complete_environment_is_ok(self):
        runner = FakeRunner(_probe_output())
        report = HcclVmEnvironment(
            self.config,
            host_system="Windows",
            command_runner=runner,
            which=lambda name: f"C:\\Windows\\System32\\{name}",
        ).diagnose()
        self.assertEqual(report["status"], "OK")
        self.assertEqual(report["missing_items"], [])
        self.assertEqual(report["selected_backend"], "ASCEND_HCCL_VM")
        self.assertEqual(report["cann"]["version"], "9.1.0")
        self.assertTrue(report["checker"]["available"])
        self.assertEqual(runner.calls[0][0][:4], [
            "wsl.exe", "-d", "Ubuntu-22.04", "--",
        ])
        self.assertTrue(
            report["hccl_test"]["executables"]["AllGather"]["executable"]
        )

    def test_missing_wsl_is_reported_without_subprocess(self):
        runner = FakeRunner(_probe_output())
        report = HcclVmEnvironment(
            self.config,
            host_system="Windows",
            command_runner=runner,
            which=lambda name: None,
        ).diagnose()
        self.assertEqual(report["status"], "ENV_BLOCKED_WSL")
        self.assertIn("wsl.exe is not available", report["missing_items"])
        self.assertEqual(runner.calls, [])

    def test_missing_checker_is_env_blocked(self):
        report = HcclVmEnvironment(
            self.config,
            host_system="Linux",
            command_runner=FakeRunner(
                _probe_output(checker_available="false")
            ),
            which=lambda name: f"/usr/bin/{name}",
        ).diagnose()
        self.assertEqual(report["status"], "ENV_BLOCKED")
        self.assertIn("checker plugin", report["missing_items"])

    def test_interactive_sudo_requirement_is_env_blocked(self):
        report = HcclVmEnvironment(
            self.config,
            host_system="Linux",
            command_runner=FakeRunner(
                _probe_output(sudo_non_interactive="false")
            ),
            which=lambda name: f"/usr/bin/{name}",
        ).diagnose()
        self.assertEqual(report["status"], "ENV_BLOCKED")
        self.assertIn(
            "root or non-interactive sudo for HCCL-VM startup",
            report["missing_items"],
        )

    def test_branch_mismatch_is_env_blocked(self):
        report = HcclVmEnvironment(
            self.config,
            host_system="Linux",
            command_runner=FakeRunner(
                _probe_output(hcomm_branch="main")
            ),
            which=lambda name: f"/usr/bin/{name}",
        ).diagnose()
        self.assertIn(
            "hcomm branch/commit mismatch",
            report["missing_items"],
        )

    def test_empty_git_commit_metadata_is_env_blocked(self):
        report = HcclVmEnvironment(
            self.config,
            host_system="Linux",
            command_runner=FakeRunner(
                _probe_output(hcomm_commit="")
            ),
            which=lambda name: f"/usr/bin/{name}",
        ).diagnose()
        self.assertEqual(report["status"], "ENV_BLOCKED")
        self.assertIn("hcomm git metadata", report["missing_items"])

    def test_git_probe_uses_exact_process_local_safe_directory(self):
        config = HcclVmConfig(
            backend="ASCEND_HCCL_VM",
            hcomm_source_dir="/srv/official/hcomm",
            hccl_source_dir="/srv/official/hccl",
        )
        script = HcclVmEnvironment(
            config,
            host_system="Linux",
        )._build_probe_script()
        self.assertIn(
            'git_safe=(git -c "safe.directory=$repo_path" '
            '-C "$repo_path")',
            script,
        )
        self.assertIn('hcomm=/srv/official/hcomm', script)
        self.assertIn('hccl=/srv/official/hccl', script)
        self.assertNotIn("git config --global", script)
        self.assertNotIn("git config --system", script)
        self.assertNotIn("safe.directory=*", script)

    def test_git_repo_paths_reject_wildcards_and_broad_roots(self):
        invalid_values = ("*", "/srv/*", "/", "relative/repo")
        for path in invalid_values:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    HcclVmConfig(
                        backend="ASCEND_HCCL_VM",
                        hcomm_source_dir=path,
                    )

    def test_command_timeout_is_reported(self):
        def timeout_runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        report = HcclVmEnvironment(
            self.config,
            host_system="Linux",
            command_runner=timeout_runner,
            which=lambda name: f"/usr/bin/{name}",
        ).diagnose()
        self.assertEqual(report["wsl"]["exit_code"], 124)
        self.assertIn(
            "environment probe exited with code 124",
            report["missing_items"],
        )

    def test_cpu_backend_is_rejected_without_probe(self):
        runner = FakeRunner(_probe_output())
        report = HcclVmEnvironment(
            HcclVmConfig(),
            host_system="Linux",
            command_runner=runner,
            which=lambda name: f"/usr/bin/{name}",
        ).diagnose()
        self.assertEqual(report["status"], "ENV_BLOCKED_BACKEND")
        self.assertEqual(runner.calls, [])

    def test_selected_primitive_can_run_when_another_is_missing(self):
        report = HcclVmEnvironment(
            self.config,
            host_system="Linux",
            command_runner=FakeRunner(_probe_output(
                hccl_test_AllGather_executable="false",
            )),
            which=lambda name: f"/usr/bin/{name}",
        ).diagnose_for(resolve_collective_request(
            primitive="AllReduce",
            rank_count=2,
            dtype="int32",
            reduce_op="sum",
            elements=16,
        ))
        self.assertEqual(report["overall_status"], "ENV_BLOCKED")
        self.assertEqual(report["status"], "OK")
        self.assertEqual(report["selected_primitive"], "AllReduce")


if __name__ == "__main__":
    unittest.main()
