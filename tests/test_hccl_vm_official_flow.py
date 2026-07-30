"""G2-D-5 official runner flow tests with an opt-in real environment test."""

import os
import sys
import unittest

from plugin.hccl_vm_backend import HcclVmConfig
from plugin.hccl_vm_runner import (
    HcclVmRunner,
    InteractiveStep,
    OfficialAllReduceRequest,
    OfficialCollectiveRequest,
    ProcessExecution,
    _audit_related_processes,
    _execute_interactive_process,
)


SUCCESS_LOG = """
__HCCL_AGENT_HCCL_CONFIG_EXIT_CODE=0
__HCCL_AGENT_MOCK_EXIT_CODE=0
__HCCL_AGENT_TEST_EXIT_CODE=0
[info] Op summary, opIndex=0, collectiveType=AllReduce, rankCount=2,
dataType=INT32, elementCount=16, reduceType=SUM, opGroupSize=2
[info] CheckerV3 stage finished, stage=GenGraph, status=success
[info] CheckerV3 stage finished, stage=SingleTaskCheck, status=success
[info] CheckerV3 stage finished, stage=MemConflict, status=success
[info] CheckerV3 stage finished, stage=SemanticCheck, status=success
[info] op[0] Checker Success
__HCCL_AGENT_CHECKER_EXIT_CODE=0
[info] Shell exited. Host shutting down.
__HCCL_AGENT_VM_EXIT_CODE=0
"""


class FakeEnvironment:

    def __init__(self, status="OK"):
        self.status = status

    def diagnose(self):
        return {
            "status": self.status,
            "missing_items": (
                [] if self.status == "OK" else ["test environment missing"]
            ),
        }

    def diagnose_for(self, contract):
        return self.diagnose()


class FakeExecutor:

    def __init__(self, result):
        self.result = result
        self.calls = []

    def __call__(self, command, steps, *, timeout_seconds):
        self.calls.append((command, steps, timeout_seconds))
        return self.result


class TestHcclVmOfficialFlow(unittest.TestCase):

    def setUp(self):
        self.config = HcclVmConfig(
            backend="ASCEND_HCCL_VM",
            timeout_seconds=30,
        )
        self.request = OfficialAllReduceRequest()

    def test_successful_flow_runs_all_commands_and_parses_pass(self):
        executor = FakeExecutor(ProcessExecution(
            raw_log=SUCCESS_LOG,
            returncode=0,
            timed_out=False,
        ))
        outcome = HcclVmRunner(
            self.config,
            host_system="Windows",
            process_executor=executor,
        ).verify(
            self.request,
            environment=FakeEnvironment(),
        )
        self.assertTrue(outcome.result["passed"])
        self.assertEqual(outcome.result["status"], "PASS_CLEAN")
        commands = "\n".join(
            step.command for step in executor.calls[0][1]
        )
        self.assertIn("hccl-vm mock-comm 112", commands)
        self.assertIn("all_reduce_test -b 64 -e 64", commands)
        self.assertIn("hccl-vm plugin run @checker", commands)
        self.assertTrue(commands.endswith("exit"))
        self.assertTrue(
            executor.calls[0][0][-1].startswith("source <(")
        )

    def test_environment_block_prevents_process_start(self):
        executor = FakeExecutor(ProcessExecution("", 0, False))
        outcome = HcclVmRunner(
            self.config,
            process_executor=executor,
        ).verify(
            self.request,
            environment=FakeEnvironment("ENV_BLOCKED_CANN"),
        )
        self.assertFalse(outcome.result["passed"])
        self.assertEqual(
            outcome.result["status"],
            "ENV_BLOCKED_CANN",
        )
        self.assertEqual(executor.calls, [])

    def test_allgather_flow_uses_the_allgather_contract(self):
        allgather_log = SUCCESS_LOG.replace(
            "AllReduce", "AllGather"
        ).replace("elementCount=16", "elementCount=8")
        executor = FakeExecutor(ProcessExecution(
            raw_log=allgather_log,
            returncode=0,
            timed_out=False,
        ))
        request = OfficialCollectiveRequest(
            primitive="AllGather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        )
        outcome = HcclVmRunner(
            self.config,
            process_executor=executor,
        ).verify(request, environment=FakeEnvironment())
        self.assertTrue(outcome.result["passed"])
        test_command = executor.calls[0][1][1].command
        self.assertIn("all_gather_test -b 64 -e 64 -d int32", test_command)
        self.assertNotIn(" -o ", test_command)

    def test_timeout_terminates_process_and_cannot_pass(self):
        executor = FakeExecutor(ProcessExecution(
            raw_log="partial output\n",
            returncode=124,
            timed_out=True,
        ))
        outcome = HcclVmRunner(
            self.config,
            process_executor=executor,
        ).verify(
            self.request,
            environment=FakeEnvironment(),
        )
        self.assertFalse(outcome.result["passed"])
        self.assertEqual(
            outcome.result["status"],
            "ENV_BLOCKED_TIMEOUT",
        )
        self.assertIn(
            "partial output",
            outcome.to_public_dict()["log_tail"],
        )

    def test_execution_script_uses_pty_and_linux_timeout(self):
        runner = HcclVmRunner(self.config)
        script = runner._build_startup_script(for_execution=True)
        self.assertIn("timeout --signal=TERM --kill-after=10s 30s", script)
        self.assertIn("script -qef -E never -c", script)
        self.assertIn("__HCCL_AGENT_VM_EXIT_CODE", script)

    def test_process_audit_reports_only_exact_residual_names(self):
        class AuditEnvironment:
            def run_linux_script(self, script):
                return type("Result", (), {
                    "returncode": 0,
                    "stderr": "",
                    "stdout": (
                        "  12 hccl-vm hccl-vm start\n"
                        "  13 unrelated all_reduce_test_helper\n"
                    ),
                })()

        audit = _audit_related_processes(
            AuditEnvironment(),
            self.request.resolve(),
        )
        self.assertEqual(audit["status"], "RESIDUAL_PROCESSES")
        self.assertEqual(audit["residual_processes"][0]["comm"], "hccl-vm")

    def test_process_driver_waits_for_prompt_and_each_marker(self):
        helper = "\n".join([
            "import sys",
            "markers = {",
            "  'mock': '__HCCL_AGENT_MOCK_EXIT_CODE=0',",
            "  'test': '__HCCL_AGENT_TEST_EXIT_CODE=0',",
            "  'checker': '__HCCL_AGENT_CHECKER_EXIT_CODE=0',",
            "}",
            "sys.stdout.write('(hvm)$> ')",
            "sys.stdout.flush()",
            "for line in sys.stdin:",
            "    command = line.strip()",
            "    if command == 'exit':",
            "        print('Shell exited. Host shutting down.', flush=True)",
            "        break",
            "    print(markers[command], flush=True)",
        ])
        execution = _execute_interactive_process(
            [sys.executable, "-u", "-c", helper],
            [
                InteractiveStep(
                    "mock", "__HCCL_AGENT_MOCK_EXIT_CODE"
                ),
                InteractiveStep(
                    "test", "__HCCL_AGENT_TEST_EXIT_CODE"
                ),
                InteractiveStep(
                    "checker", "__HCCL_AGENT_CHECKER_EXIT_CODE"
                ),
                InteractiveStep("exit", None),
            ],
            timeout_seconds=5,
        )
        self.assertFalse(execution.timed_out)
        self.assertEqual(execution.returncode, 0)
        self.assertIn(
            "__HCCL_AGENT_CHECKER_EXIT_CODE=0",
            execution.raw_log,
        )
        self.assertIn(
            "Shell exited. Host shutting down.",
            execution.raw_log,
        )

    @unittest.skipUnless(
        os.environ.get("HCCL_VM_RUN_OFFICIAL_TEST") == "1",
        "set HCCL_VM_RUN_OFFICIAL_TEST=1 for the real HCCL-VM flow",
    )
    def test_real_official_environment(self):
        outcome = HcclVmRunner(
            HcclVmConfig(backend="ASCEND_HCCL_VM"),
        ).verify(self.request)
        self.assertTrue(outcome.result["passed"], outcome.result)


if __name__ == "__main__":
    unittest.main()
