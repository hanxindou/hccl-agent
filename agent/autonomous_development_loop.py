"""Offline autonomous development loop for controlled demonstrations.

This module intentionally avoids external LLMs, network access, shell text,
and repository writes. It generates a tiny Python reference checker in an
isolated temporary directory, compiles it with ``py_compile``, runs it, reads
the deterministic failure, and applies one bounded template repair.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Dict, List, Sequence


OFFLINE_TEMPLATE = "OFFLINE_TEMPLATE"


@dataclass
class CommandRecord:
    """Captured command execution evidence."""

    command: List[str]
    exit_code: int
    stdout: str
    stderr: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "command": list(self.command),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


class OfflineDevelopmentLoop:
    """Run a deterministic generate-compile-test-repair demonstration."""

    MAX_FIX_ATTEMPTS = 2
    TIMEOUT_SECONDS = 10

    def __init__(self, python_executable: str | None = None) -> None:
        self.python_executable = python_executable or sys.executable

    def run_demo(self, requirement: str | None = None) -> Dict[str, object]:
        """Run the offline development loop in a temporary directory."""
        requirement = requirement or (
            "Generate a small AllReduce SUM reference checker with tests."
        )

        with tempfile.TemporaryDirectory(prefix="hccl-agent-e1-") as tmp:
            workspace = Path(tmp).resolve()
            generated = workspace / "generated_reference_checker.py"
            records: List[Dict[str, object]] = []
            fixes: List[Dict[str, str]] = []

            self._write_file(workspace, generated, self._broken_template())

            first_compile = self._run_allowed(
                [self.python_executable, "-m", "py_compile", str(generated)],
                workspace,
            )
            records.append(first_compile.as_dict())

            if first_compile.exit_code != 0:
                fixes.append({
                    "attempt": "1",
                    "reason": "py_compile reported a deterministic SyntaxError",
                    "action": "replace the malformed return statement with a valid expression",
                })
                self._write_file(workspace, generated, self._fixed_template())

            second_compile = self._run_allowed(
                [self.python_executable, "-m", "py_compile", str(generated)],
                workspace,
            )
            records.append(second_compile.as_dict())

            test_result = self._run_allowed(
                [self.python_executable, str(generated)],
                workspace,
            )
            records.append(test_result.as_dict())

            success = (
                first_compile.exit_code != 0 and
                second_compile.exit_code == 0 and
                test_result.exit_code == 0 and
                len(fixes) <= self.MAX_FIX_ATTEMPTS
            )

            result = {
                "mode": OFFLINE_TEMPLATE,
                "requirement": requirement,
                "workspace_strategy": "tempfile.TemporaryDirectory",
                "workspace_path": str(workspace),
                "generated_files": [generated.name],
                "max_fix_attempts": self.MAX_FIX_ATTEMPTS,
                "fix_attempts": len(fixes),
                "fixes": fixes,
                "commands": records,
                "success": success,
                "external_llm_used": False,
                "network_used": False,
            }
        result["workspace_removed"] = not Path(result["workspace_path"]).exists()
        return result

    def _run_allowed(self, command: Sequence[str], cwd: Path) -> CommandRecord:
        self._validate_command(command, cwd)
        proc = subprocess.run(
            list(command),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=self.TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
        return CommandRecord(
            command=list(command),
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def _validate_command(self, command: Sequence[str], cwd: Path) -> None:
        if not command:
            raise ValueError("empty command is not allowed")
        if Path(command[0]).resolve() != Path(self.python_executable).resolve():
            raise ValueError("only the configured Python executable is allowed")
        if len(command) < 2:
            raise ValueError("command is incomplete")
        if command[1] == "-m":
            if len(command) != 4 or command[2] != "py_compile":
                raise ValueError("only python -m py_compile <file> is allowed")
            target = Path(command[3]).resolve()
        else:
            if len(command) != 2:
                raise ValueError("only direct execution of one generated file is allowed")
            target = Path(command[1]).resolve()

        cwd = cwd.resolve()
        if cwd not in target.parents and target != cwd:
            raise ValueError("command target must stay inside the temporary workspace")

    def _write_file(self, workspace: Path, path: Path, content: str) -> None:
        target = path.resolve()
        workspace = workspace.resolve()
        if workspace not in target.parents:
            raise ValueError("write target must stay inside the temporary workspace")
        target.write_text(content, encoding="utf-8")

    @staticmethod
    def _broken_template() -> str:
        return (
            "def allreduce_sum(values):\n"
            "    return sum(values\n"
            "\n"
            "def test_allreduce_sum():\n"
            "    assert allreduce_sum([1.0, -2.0, 0.5, 4.0]) == 3.5\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    test_allreduce_sum()\n"
            "    print('offline reference checker passed')\n"
        )

    @staticmethod
    def _fixed_template() -> str:
        return (
            "def allreduce_sum(values):\n"
            "    return sum(values)\n"
            "\n"
            "def test_allreduce_sum():\n"
            "    assert allreduce_sum([1.0, -2.0, 0.5, 4.0]) == 3.5\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    test_allreduce_sum()\n"
            "    print('offline reference checker passed')\n"
        )
