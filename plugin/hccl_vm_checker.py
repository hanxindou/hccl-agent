"""Strict, contract-driven parsing for official HCCL-VM Checker output."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from plugin.hccl_vm_registry import ResolvedCollectiveContract


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
    r"CheckerV3stagefinished,stage=(?P<stage>[^,]+),"
    r"status=(?P<status>[A-Za-z]+)",
    re.IGNORECASE,
)
TEST_EXIT_RE = re.compile(r"__HCCL_AGENT_TEST_EXIT_CODE=(-?\d+)")
MOCK_EXIT_RE = re.compile(r"__HCCL_AGENT_MOCK_EXIT_CODE=(-?\d+)")
CHECKER_EXIT_RE = re.compile(r"__HCCL_AGENT_CHECKER_EXIT_CODE=(-?\d+)")
HCCL_CONFIG_EXIT_RE = re.compile(
    r"__HCCL_AGENT_HCCL_CONFIG_EXIT_CODE=(-?\d+)"
)
VM_EXIT_RE = re.compile(r"__HCCL_AGENT_VM_EXIT_CODE=(-?\d+)")
WARNING_103_RE = re.compile(r"ErrorCode:\s*103\]?\s*(.*)", re.IGNORECASE)


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
    primitive: str | None = None
    input_alias: str | None = None
    registry_version: str | None = None
    rank_count: int | None = None
    dtype: str | None = None
    reduce_op: str | None = None
    elements: int | None = None
    byte_count: int | None = None
    element_semantics: str | None = None
    input_elements_per_rank: int | None = None
    output_elements_per_rank: int | None = None
    input_bytes_per_rank: int | None = None
    output_bytes_per_rank: int | None = None
    hccl_test_bytes: int | None = None
    executable_basename: str | None = None
    required_checker_stages: list[str] = field(default_factory=list)
    hccl_config_exit_code: int | None = None
    mock_exit_code: int | None = None
    test_exit_code: int | None = None
    checker_exit_code: int | None = None
    vm_exit_code: int | None = None
    outer_exit_code: int | None = None
    checker_success: bool = False
    checker_success_count: int = 0
    checker_stages: dict[str, str] = field(default_factory=dict)
    operation_results: list[dict[str, Any]] = field(default_factory=list)
    op_summaries: list[dict[str, Any]] = field(default_factory=list)
    metadata_match: bool = False
    warning_103_count: int = 0
    warning_summaries: list[str] = field(default_factory=list)
    warning_baseline_count: int | None = None
    warning_baseline_summaries: list[str] = field(default_factory=list)
    warning_regression: bool = False
    warning_regression_reasons: list[str] = field(default_factory=list)
    stage_failures: list[str] = field(default_factory=list)
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
    request: Any | None = None,
) -> OfficialVerificationResult:
    """Parse a run conservatively; omitted evidence cannot infer success."""

    contract = _resolved_contract(request)
    clean = ANSI_ESCAPE_RE.sub("", log_text)
    compact = re.sub(r"\s+", "", clean)
    lower_compact = compact.casefold()
    summary_matches = list(SUMMARY_RE.finditer(compact))
    summaries = [_summary_from_match(match) for match in summary_matches]
    operation_results = _operation_results(
        compact,
        summary_matches,
        summaries,
        contract,
    )
    checker_stages = _aggregate_stages(operation_results)
    metadata_match = (
        contract is not None
        and bool(summaries)
        and all(_summary_matches_contract(summary, contract) for summary in summaries)
    )
    stage_failures = _stage_failures(operation_results, contract)
    warning_summaries = _warning_summaries(clean)
    warning_103_count = len(re.findall(r"ErrorCode:\s*103", clean, re.I))
    warning_regression_reasons = _warning_regression_reasons(
        warning_103_count,
        warning_summaries,
        contract,
    )
    checker_success_count = lower_compact.count("checkersuccess")
    vm_exit_code = _last_exit_code(VM_EXIT_RE, compact)
    vm_normal_shutdown = (
        vm_exit_code == 0
        and "shellexited.hostshuttingdown." in lower_compact
    )

    result = OfficialVerificationResult(
        primitive=(contract.canonical_primitive if contract else None),
        input_alias=(contract.input_alias if contract else None),
        registry_version=(contract.registry_version if contract else None),
        rank_count=(contract.rank_count if contract else None),
        dtype=(contract.dtype if contract else None),
        reduce_op=(contract.reduce_op if contract else None),
        elements=(contract.request_elements if contract else None),
        byte_count=(contract.byte_count if contract else None),
        element_semantics=(contract.element_semantics if contract else None),
        input_elements_per_rank=(
            contract.input_elements_per_rank if contract else None
        ),
        output_elements_per_rank=(
            contract.output_elements_per_rank if contract else None
        ),
        input_bytes_per_rank=(
            contract.input_bytes_per_rank if contract else None
        ),
        output_bytes_per_rank=(
            contract.output_bytes_per_rank if contract else None
        ),
        hccl_test_bytes=(contract.hccl_test_bytes if contract else None),
        executable_basename=(contract.executable_basename if contract else None),
        required_checker_stages=(
            list(contract.required_checker_stages) if contract else []
        ),
        hccl_config_exit_code=_last_exit_code(HCCL_CONFIG_EXIT_RE, compact),
        mock_exit_code=_last_exit_code(MOCK_EXIT_RE, compact),
        test_exit_code=_last_exit_code(TEST_EXIT_RE, compact),
        checker_exit_code=_last_exit_code(CHECKER_EXIT_RE, compact),
        vm_exit_code=vm_exit_code,
        outer_exit_code=outer_exit_code,
        checker_success=checker_success_count > 0,
        checker_success_count=checker_success_count,
        checker_stages=checker_stages,
        operation_results=operation_results,
        op_summaries=[asdict(summary) for summary in summaries],
        metadata_match=metadata_match,
        warning_103_count=warning_103_count,
        warning_summaries=warning_summaries,
        warning_baseline_count=(
            contract.warning_baseline_count if contract else None
        ),
        warning_baseline_summaries=(
            list(contract.warning_baseline_summaries) if contract else []
        ),
        warning_regression=bool(warning_regression_reasons),
        warning_regression_reasons=warning_regression_reasons,
        stage_failures=stage_failures,
        fatal_signals=_fatal_signals(lower_compact),
        vm_normal_shutdown=vm_normal_shutdown,
    )
    result.failure_reasons = _failure_reasons(result, contract)
    result.passed = not result.failure_reasons
    if result.passed:
        result.status = (
            "PASS_WITH_WARNING" if warning_103_count else "PASS_CLEAN"
        )
    return result


def _resolved_contract(request: Any | None) -> ResolvedCollectiveContract | None:
    if request is None:
        return None
    if isinstance(request, ResolvedCollectiveContract):
        return request
    resolver = getattr(request, "resolve", None)
    if callable(resolver):
        resolved = resolver()
        if isinstance(resolved, ResolvedCollectiveContract):
            return resolved
    raise ValueError("request must provide a resolved collective contract")


def _summary_from_match(match: re.Match[str]) -> CheckerOpSummary:
    return CheckerOpSummary(
        op_index=int(match.group("op_index")),
        collective_type=match.group("collective_type"),
        rank_count=int(match.group("rank_count")),
        data_type=match.group("data_type"),
        element_count=int(match.group("element_count")),
        reduce_type=match.group("reduce_type"),
    )


def _operation_results(
    compact: str,
    summary_matches: list[re.Match[str]],
    summaries: list[CheckerOpSummary],
    contract: ResolvedCollectiveContract | None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, (match, summary) in enumerate(zip(summary_matches, summaries)):
        end = (
            summary_matches[index + 1].start()
            if index + 1 < len(summary_matches)
            else len(compact)
        )
        stages = {
            stage: status.casefold()
            for stage, status in STAGE_RE.findall(compact[match.end():end])
        }
        required = contract.required_checker_stages if contract else ()
        missing = [
            stage
            for stage in required
            if stages.get(stage, "").casefold() != "success"
        ]
        failed = [
            stage
            for stage, status in stages.items()
            if status.casefold() != "success"
        ]
        results.append({
            "op_summary": asdict(summary),
            "stages": stages,
            "missing_or_unsuccessful_required_stages": missing,
            "failed_observed_stages": failed,
            "metadata_match": bool(
                contract and _summary_matches_contract(summary, contract)
            ),
        })
    return results


def _aggregate_stages(
    operation_results: list[dict[str, Any]],
) -> dict[str, str]:
    aggregate: dict[str, str] = {}
    for operation in operation_results:
        for stage, status in operation["stages"].items():
            aggregate.setdefault(stage, status)
    return aggregate


def _summary_matches_contract(
    summary: CheckerOpSummary,
    contract: ResolvedCollectiveContract,
) -> bool:
    if (
        summary.collective_type.casefold()
        != contract.checker_collective_type.casefold()
        or summary.rank_count != contract.rank_count
        or summary.data_type.casefold() != contract.dtype.casefold()
        or summary.element_count != contract.checker_element_count
    ):
        return False
    return (
        contract.checker_reduce_type is None
        or summary.reduce_type.casefold()
        == contract.checker_reduce_type.casefold()
    )


def _stage_failures(
    operation_results: list[dict[str, Any]],
    contract: ResolvedCollectiveContract | None,
) -> list[str]:
    if contract is None:
        return []
    failures: list[str] = []
    for operation in operation_results:
        op_index = operation["op_summary"]["op_index"]
        for stage in operation["missing_or_unsuccessful_required_stages"]:
            failures.append(f"opIndex={op_index} required stage {stage} missing or not success")
        for stage in operation["failed_observed_stages"]:
            failures.append(f"opIndex={op_index} observed stage {stage} failed")
    return failures


def _last_exit_code(pattern: re.Pattern[str], text: str) -> int | None:
    matches = pattern.findall(text)
    return int(matches[-1]) if matches else None


def _warning_summaries(clean_text: str) -> list[str]:
    summaries: list[str] = []
    for line in clean_text.splitlines():
        match = WARNING_103_RE.search(line)
        if match is None:
            continue
        normalized = " ".join(match.group(1).strip(" []:\t").split()).casefold()
        normalized = normalized.rstrip(":")
        if normalized and normalized not in summaries:
            summaries.append(normalized[:500])
    return summaries


def _warning_regression_reasons(
    warning_count: int,
    warning_summaries: list[str],
    contract: ResolvedCollectiveContract | None,
) -> list[str]:
    if contract is None:
        return []
    reasons: list[str] = []
    if warning_count != contract.warning_baseline_count:
        reasons.append(
            "ErrorCode 103 count differs from baseline "
            f"{contract.warning_baseline_count}: observed {warning_count}"
        )
    expected = set(contract.warning_baseline_summaries)
    observed = set(warning_summaries)
    unexpected = sorted(observed - expected)
    if unexpected:
        reasons.append(
            "ErrorCode 103 normalized form differs from baseline: "
            + "; ".join(unexpected)
        )
    return reasons


def _fatal_signals(lower_compact: str) -> list[str]:
    patterns = {
        "Segmentation fault": "segmentationfault",
        "MPI_ABORT": "mpi_abort",
        "undefined symbol": "undefinedsymbol",
        "fatal failure": "fatalfailure",
        "Checker Failed": "checkerfailed",
    }
    return [
        label
        for label, token in patterns.items()
        if token in lower_compact
    ]


def _failure_reasons(
    result: OfficialVerificationResult,
    contract: ResolvedCollectiveContract | None,
) -> list[str]:
    failures: list[str] = []
    if contract is None:
        failures.append("resolved collective contract was not provided")
    if result.hccl_config_exit_code != 0:
        failures.append(
            "HCCL-VM hccl_config.sh exit code is not 0 or was not captured"
        )
    if result.mock_exit_code != 0:
        failures.append(
            "hccl-vm mock-comm exit code is not 0 or was not captured"
        )
    if result.test_exit_code != 0:
        executable = contract.executable_basename if contract else "hccl_test"
        failures.append(
            f"{executable} exit code is not 0 or was not captured"
        )
    if not result.metadata_match:
        failures.append("checker metadata does not match the resolved contract")
    if result.stage_failures:
        failures.append("checker stage contract failed: " + "; ".join(
            result.stage_failures
        ))
    if not result.checker_success:
        failures.append("Checker Success was not observed")
    if result.checker_exit_code != 0:
        failures.append("checker command exit code is not 0 or was not captured")
    if result.fatal_signals:
        failures.append("fatal signals observed: " + ", ".join(result.fatal_signals))
    if result.vm_exit_code != 0:
        failures.append("HCCL-VM exit code is not 0 or was not captured")
    if not result.vm_normal_shutdown:
        failures.append("HCCL-VM normal shutdown was not observed")
    if result.outer_exit_code != 0:
        failures.append("outer process exit code is not 0")
    return failures
