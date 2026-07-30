"""G2-D-3 tests for shell-safe, side-effect-free dry-run plans."""

import subprocess
import unittest
from unittest import mock

from main import _run_official_command, parse_args
from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_runner import (
    HcclVmRunner,
    OfficialAllReduceRequest,
)


class TestHcclVmRunnerDryRun(unittest.TestCase):

    def setUp(self):
        self.config = HcclVmConfig(backend="ASCEND_HCCL_VM")
        self.request = OfficialAllReduceRequest()

    def test_plan_has_fixed_official_validation_shape(self):
        plan = HcclVmRunner(
            self.config,
            host_system="Windows",
        ).dry_run(self.request)
        self.assertEqual(plan["status"], "DRY_RUN")
        self.assertTrue(plan["not_executed"])
        self.assertEqual(plan["request"]["primitive"], "AllReduce")
        self.assertEqual(plan["request"]["rank_count"], 2)
        self.assertEqual(plan["request"]["dtype"], "int32")
        self.assertEqual(plan["request"]["reduce_op"], "sum")
        self.assertEqual(plan["request"]["elements"], 16)
        self.assertEqual(plan["request"]["byte_count"], 64)

    def test_plan_sources_both_environment_scripts(self):
        script = HcclVmRunner(self.config).dry_run(
            self.request
        )["startup_script"]
        self.assertIn(
            "source /home/workspace/Ascend/cann-9.1.0/set_env.sh",
            script,
        )
        self.assertIn(
            "source "
            "/home/workspace/hcomm/test/hccl_vm/hccl_vm_install/"
            "script/hccl_config.sh",
            script,
        )
        self.assertEqual(
            script.count(
                "source /home/workspace/Ascend/cann-9.1.0/set_env.sh"
            ),
            2,
        )
        self.assertIn("__HCCL_AGENT_HCCL_CONFIG_EXIT_CODE", script)
        self.assertIn(
            "start ascend950_cluster_32_server_normal.yaml --check-only",
            script,
        )

    def test_interactive_commands_match_minimum_closure(self):
        commands = HcclVmRunner(self.config).dry_run(
            self.request
        )["interactive_commands"]
        self.assertTrue(commands[0].startswith("hccl-vm mock-comm 112;"))
        self.assertIn("__HCCL_AGENT_MOCK_EXIT_CODE", commands[0])
        self.assertIn("mpirun --allow-run-as-root --oversubscribe -np 2", commands[1])
        self.assertIn("all_reduce_test -b 64 -e 64 -d int32 -o sum", commands[1])
        self.assertTrue(
            commands[2].startswith("hccl-vm plugin run @checker;")
        )
        self.assertIn("__HCCL_AGENT_CHECKER_EXIT_CODE", commands[2])
        self.assertEqual(commands[3], "exit")

    def test_dry_run_does_not_start_subprocess(self):
        with mock.patch.object(subprocess, "Popen") as popen:
            HcclVmRunner(self.config).dry_run(self.request)
        popen.assert_not_called()

    def test_shell_metacharacters_in_path_are_quoted(self):
        config = HcclVmConfig(
            backend="ASCEND_HCCL_VM",
            cann_path="/tmp/cann; touch /tmp/not-allowed",
        )
        script = HcclVmRunner(config).dry_run(
            self.request
        )["startup_script"]
        self.assertIn(
            "'/tmp/cann; touch /tmp/not-allowed'",
            script,
        )

    def test_control_characters_in_config_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "newline"):
            HcclVmConfig(
                backend="ASCEND_HCCL_VM",
                topology="valid.yaml\nmalicious",
            )

    def test_out_of_scope_collective_is_rejected(self):
        invalid_requests = [
            {"primitive": "AllGather"},
            {"rank_count": 4},
            {"dtype": "fp32"},
            {"reduce_op": "max"},
            {"elements": 32},
        ]
        for values in invalid_requests:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    OfficialAllReduceRequest(**values)

    def test_cli_dry_run_returns_without_environment_probe(self):
        args = parse_args([
            "dry-run",
            "--primitive", "AllReduce",
            "--nodes", "2",
            "--dtype", "int32",
            "--op", "sum",
            "--elements", "16",
        ])
        with mock.patch(
            "main.HcclVmEnvironment.diagnose"
        ) as diagnose:
            with mock.patch("builtins.print"):
                _run_official_command(args, self.config)
        diagnose.assert_not_called()


if __name__ == "__main__":
    unittest.main()
