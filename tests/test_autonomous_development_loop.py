"""Tests for the E1 offline autonomous development loop."""

import os
from pathlib import Path
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.autonomous_development_loop import (
    OFFLINE_TEMPLATE,
    OfflineDevelopmentLoop,
)


class TestOfflineDevelopmentLoop(unittest.TestCase):

    def test_demo_runs_failure_fix_compile_and_test(self):
        result = OfflineDevelopmentLoop().run_demo()

        self.assertTrue(result["success"])
        self.assertEqual(result["mode"], OFFLINE_TEMPLATE)
        self.assertFalse(result["external_llm_used"])
        self.assertFalse(result["network_used"])
        self.assertTrue(result["workspace_removed"])
        self.assertEqual(result["fix_attempts"], 1)
        self.assertLessEqual(result["fix_attempts"], result["max_fix_attempts"])

        commands = result["commands"]
        self.assertEqual(len(commands), 3)
        self.assertNotEqual(commands[0]["exit_code"], 0)
        self.assertIn("SyntaxError", commands[0]["stderr"])
        self.assertEqual(commands[1]["exit_code"], 0)
        self.assertEqual(commands[2]["exit_code"], 0)
        self.assertIn("offline reference checker passed", commands[2]["stdout"])

    def test_command_whitelist_rejects_shell_like_commands(self):
        loop = OfflineDevelopmentLoop()
        with self.assertRaises(ValueError):
            loop._validate_command(["cmd.exe", "/c", "echo unsafe"], Path(os.getcwd()))


if __name__ == "__main__":
    unittest.main()
