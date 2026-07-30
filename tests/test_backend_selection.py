"""G2-D-1 backend selection, configuration, and CLI tests."""

import json
import os
import tempfile
import unittest
from unittest import mock

from main import _config_from_args, parse_args
from plugin.hccl_vm_backend import (
    Backend,
    HcclVmConfig,
    load_hccl_vm_config,
    normalize_backend,
)


class TestBackendSelection(unittest.TestCase):

    def test_default_backend_remains_cpu_sim(self):
        config = load_hccl_vm_config(environ={})
        self.assertEqual(config.backend, Backend.CPU_SIM.value)

    def test_normalize_backend_rejects_unknown_value(self):
        with self.assertRaisesRegex(ValueError, "Unsupported backend"):
            normalize_backend("real_npu")

    def test_environment_overrides_json_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "hccl_vm.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"backend": "CPU_SIM"}, handle)

            config = load_hccl_vm_config(
                config_path,
                environ={"HCCL_AGENT_BACKEND": "ASCEND_HCCL_VM"},
            )
        self.assertEqual(config.backend, Backend.ASCEND_HCCL_VM.value)

    def test_explicit_override_takes_priority_over_environment(self):
        config = load_hccl_vm_config(
            environ={"HCCL_AGENT_BACKEND": "ASCEND_HCCL_VM"},
            overrides={"backend": "CPU_SIM"},
        )
        self.assertEqual(config.backend, Backend.CPU_SIM.value)

    def test_legacy_cli_keeps_run_command_and_cpu_default(self):
        args = parse_args([
            "--nodes", "8",
            "--message-size", "128",
            "--primitive", "AllGather",
        ])
        config = _config_from_args(args)
        self.assertEqual(args.command, "run")
        self.assertEqual(config.backend, Backend.CPU_SIM.value)
        self.assertEqual(args.primitive, "AllGather")

    def test_official_subcommands_default_to_official_backend(self):
        for command in ("diagnose", "dry-run", "verify-official"):
            with self.subTest(command=command):
                argv = [command]
                if command == "verify-official":
                    argv.extend([
                        "--primitive", "AllReduce", "--op", "sum",
                    ])
                args = parse_args(argv)
                self.assertEqual(
                    args.backend,
                    Backend.ASCEND_HCCL_VM.value,
                )

    def test_cli_paths_override_environment_and_json(self):
        args = parse_args([
            "diagnose",
            "--cann-path", "/cli/cann",
            "--hccl-vm-install-dir", "/cli/hccl-vm",
            "--hccl-test-bin", "/cli/cann/tools/hccl_test/bin",
        ])
        with mock.patch.dict(
            os.environ,
            {"HCCL_VM_CANN_PATH": "/env/cann"},
            clear=False,
        ):
            config = _config_from_args(args)
        self.assertEqual(config.cann_path, "/cli/cann")
        self.assertEqual(config.hccl_vm_install_dir, "/cli/hccl-vm")

    def test_importable_config_has_no_environment_side_effects(self):
        config = HcclVmConfig()
        self.assertEqual(config.backend, Backend.CPU_SIM.value)

    def test_hccl_test_bin_must_use_the_fixed_cann_layout(self):
        with self.assertRaisesRegex(ValueError, "must be exactly"):
            HcclVmConfig(
                cann_path="/opt/cann",
                hccl_test_bin="/tmp/other-bin",
            )


if __name__ == "__main__":
    unittest.main()
