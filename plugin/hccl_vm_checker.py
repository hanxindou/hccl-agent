"""Strict parsing for official HCCL-VM AllReduce and Checker output."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from plugin.hccl_vm_runner import OfficialAllReduceRequest


ANSI_ESCAPE_RE = re.compile(
    r"(?:\x1B[@-_][0-?]*[ -/]*[@-~])|(?:\x9B[0-?]*[ -/]*[@-~])"
)
SUMMARY_RE = re.compile(
    r"Opsummary,"
    r"opIndex=(?P<op_index>\d+),"
    r"collectiveType=(?P<collective_type>[^,]+),"
    r"rankCount=(?P<rank_count>\d+),"
    r"dataType=(?P<data_type>[^,]+),"
    r"elementCount=(?P<element_count>\d+),"
    r"reduceType=(?P<reduce_type>[^,]+),"
)
STAGE_RE = re.compile(
    r"stage\s*=\s*([A-Za-z0-9_]+)\s*,\s*status\s*=\s*([A-Za-z0-9_]+)",
    re.IGNORECASE,
)
TEST_EXIT_RE = re.compile(r"__HCCL_AGENT_TEST_EXIT_CODE=(-?\d+)")
VM_EXIT_RE = re.compile(r"__HCCL_AGENT_VM_EXIT_CODE=(-?\d+)")


@dataclass(frozen=True)
class CheckerOpSummary:
    op_index: int
    collective_type: str
    rank_count: int
    data_type: str
    element_count: int
    reduce_type: str


@dataclass
class OfficialVerificationResult:
    backend: str = "ASCEND_HCCL_VM"
    execution_mode: str = "subprocess_hccl_test"
    primitive: str = "AllReduce"
    rank_count: int = 2
    dtype: str = "int32"
    reduce_op: str = "sum"
    elements: int = 16
    byte_count: int = 64
    test_exit_code: int | None = None
    vm_exit_code: int | None = None
    outer_exit_code: int | None = None
    checker_success: bool = False
    checker_success_count: int = 0
    checker_stages: dict[str, str] = field(default_factory=dict)
    op_summaries: list[dict[str, Any]] = field(default_factory=list)
    metadata_match: bool = False
    warning_103_count: int = 0
    warning_summaries: list[str] = field(default_factory=list)
    fatal_signals: list[str] = field(default_factory=list)
    vm_normal_shutdown: bool = False
    failure_reasons: list[str] = field(default_factory=list)
    passed: bool = False
    status: str = "FAIL"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_official_result(
    log_text: str,
    *,
    outer_exit_code: int,
    request: OfficialAllReduceRequest | None = None,
) -> OfficialVerificationResult:
    """Parse output conservatively; missing evidence always means failure."""

    expected = request or OfficialAllReduceRequest()
    clean = ANSI_ESCAPE_RE.sub("", log_text)
    compact = re.sub(r"\s+", "", clean)
    lower_compact = compact.lower()

    summaries = [
        CheckerOpSummary(
            op_index=int(match.group("op_index")),
            collective_type=match.group("collective_type"),
            rank_count=int(match.group("rank_count")),
            data_type=match.group("data_type"),
            element_count=int(match.group("element_count")),
            reduce_type=match.group("reduce_type"),
        )
        for match in SUMMARY_RE.finditer(compact)
    ]
    metadata_match = bool(summaries) and all(
        summary.collective_type == expected.primitive
        and summary.rank_count == expected.rank_count
        and summary.data_type.upper() == expected.dtype.upper()
        and summary.element_count == expected.elements
        and summary.reduce_type.upper() == expected.reduce_op.upper()
        for summary in summaries
    )

    checker_success_count = lower_compact.count("checkersuccess")
    warning_103_count = lower_compact.count("errorcode:103")
    warning_summaries = _warning_summaries(clean)
    checker_stages = {
        stage: status.lower()
        for stage, status in STAGE_RE.findall(clean)
    }
    fatal_signals = _fatal_signals(lower_compact)
    test_exit_code = _last_exit_code(TEST_EXIT_RE, compact)
    vm_exit_code = _last_exit_code(VM_EXIT_RE, compact)
    vm_normal_shutdown = (
        vm_exit_code == 0
        and "Shellexited.Hostshuttingdown.".lower() in lower_compact
    )

    result = OfficialVerificationResult(
        primitive=expected.primitive,
        rank_count=expected.rank_count,
        dtype=expected.dtype,
        reduce_op=expected.reduce_op,
        elements=expected.elements,
        byte_count=expected.byte_count,
        test_exit_code=test_exit_code,
        vm_exit_code=vm_exit_code,
        outer_exit_code=outer_exit_code,
        checker_success=checker_success_count > 0,
        checker_success_count=checker_success_count,
        checker_stages=checker_stages,
        op_summaries=[asdict(summary) for summary in summaries],
        metadata_match=metadata_match,
        warning_103_count=warning_103_count,
        warning_summaries=warning_summaries,
        fatal_signals=fatal_signals,
        vm_normal_shutdown=vm_normal_shutdown,
    )
    result.failure_reasons = _failure_reasons(result)
    result.passed = not result.failure_reasons
    if result.passed:
        result.status = (
            "PASS_WITH_WARNING"
            if warning_103_count
            else "PASS_CLEAN"
        )
    return result


def _last_exit_code(pattern: re.Pattern[str], text: str) -> int | None:
    matches = pattern.findall(text)
    return int(matches[-1]) if matches else None


def _warning_summaries(clean_text: str) -> list[str]:
    summaries: list[str] = []
    for line in clean_text.splitlines():
        if re.search(r"ErrorCode:\s*103", line, re.IGNORECASE):
            normalized = " ".join(line.split())
            if normalized and normalized not in summaries:
                summaries.append(normalized[:500])
    return summaries


def _fatal_signals(lower_compact: str) -> list[str]:
    patterns = {
        "Segmentation fault": "segmentationfault",
        "MPI_ABORT": "mpi_abort",
        "undefined symbol": "undefinedsymbol",
        "fatal failure": "fatalfailure",
        "Checker Failed": "checkerfailed",
        "Checker stage failed": "stagefailed",
        "Checker status failed": "status=failed",
    }
    return [
        label
        for label, token in patterns.items()
        if token in lower_compact
    ]


def _failure_reasons(
    result: OfficialVerificationResult,
) -> list[str]:
    failures: list[str] = []
    if result.test_exit_code != 0:
        failures.append(
            "all_reduce_test exit code is not 0 or was not captured"
        )
    if not result.metadata_match:
        failures.append(
            "checker metadata does not exclusively match "
            "AllReduce/2/INT32/SUM/16"
        )
    if not result.checker_success:
        failures.append("Checker Success was not observed")
    if result.fatal_signals:
        failures.append(
            "fatal signals observed: " + ", ".join(result.fatal_signals)
        )
    if result.vm_exit_code != 0:
        failures.append(
            "HCCL-VM exit code is not 0 or was not captured"
        )
    if not result.vm_normal_shutdown:
        failures.append("HCCL-VM normal shutdown was not observed")
    if result.outer_exit_code != 0:
        failures.append("outer process exit code is not 0")
    return failures
