"""Immutable G2-E collective contracts for official HCCL-VM validation."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


REGISTRY_VERSION = "g2-e-v1"
INT32_SIZE_BYTES = 4
REQUIRED_CHECKER_STAGES = (
    "GenGraph",
    "SingleTaskCheck",
    "MemConflict",
    "SemanticCheck",
)
WARNING_103_BASELINE_COUNT = 4
WARNING_103_BASELINE_SUMMARY = (
    "found ccu post/local-post tasks that were never consumed by any wait task"
)


@dataclass(frozen=True)
class CollectiveSpec:
    canonical_name: str
    aliases: tuple[str, ...]
    executable_basename: str
    requires_reduce_op: bool
    allowed_reduce_ops: tuple[str, ...]
    allowed_dtypes: tuple[str, ...]
    allowed_rank_counts: tuple[int, ...]
    allowed_elements: tuple[int, ...]
    element_semantics: str
    checker_element_count: int
    input_elements_per_rank: int
    output_elements_per_rank: int
    hccl_test_elements_per_rank: int
    checker_collective_type: str
    checker_reduce_type: str | None
    required_checker_stages: tuple[str, ...]
    warning_baseline_count: int
    warning_baseline_summaries: tuple[str, ...]
    official_baseline: bool = True


@dataclass(frozen=True)
class ResolvedCollectiveContract:
    registry_version: str
    canonical_primitive: str
    input_alias: str
    rank_count: int
    dtype: str
    dtype_size_bytes: int
    reduce_op: str | None
    request_elements: int
    element_semantics: str
    checker_element_count: int
    input_elements_per_rank: int
    output_elements_per_rank: int
    input_bytes_per_rank: int
    output_bytes_per_rank: int
    hccl_test_bytes: int
    executable_basename: str
    checker_collective_type: str
    checker_reduce_type: str | None
    required_checker_stages: tuple[str, ...]
    warning_baseline_count: int
    warning_baseline_summaries: tuple[str, ...]

    @property
    def byte_count(self) -> int:
        """G2-D compatibility name for the fixed hccl_test byte value."""
        return self.hccl_test_bytes

    def to_dict(self) -> dict[str, object]:
        return {
            "registry_version": self.registry_version,
            "canonical_primitive": self.canonical_primitive,
            "input_alias": self.input_alias,
            "rank_count": self.rank_count,
            "dtype": self.dtype,
            "dtype_size_bytes": self.dtype_size_bytes,
            "reduce_op": self.reduce_op,
            "request_elements": self.request_elements,
            "element_semantics": self.element_semantics,
            "checker_element_count": self.checker_element_count,
            "input_elements_per_rank": self.input_elements_per_rank,
            "output_elements_per_rank": self.output_elements_per_rank,
            "input_bytes_per_rank": self.input_bytes_per_rank,
            "output_bytes_per_rank": self.output_bytes_per_rank,
            "hccl_test_bytes": self.hccl_test_bytes,
            "executable_basename": self.executable_basename,
            "checker_collective_type": self.checker_collective_type,
            "checker_reduce_type": self.checker_reduce_type,
            "required_checker_stages": list(self.required_checker_stages),
            "warning_baseline_count": self.warning_baseline_count,
            "warning_baseline_summaries": list(
                self.warning_baseline_summaries
            ),
        }


_SPECS = (
    CollectiveSpec(
        canonical_name="AllReduce",
        aliases=("allreduce", "all_reduce", "all-reduce"),
        executable_basename="all_reduce_test",
        requires_reduce_op=True,
        allowed_reduce_ops=("sum",),
        allowed_dtypes=("int32",),
        allowed_rank_counts=(2,),
        allowed_elements=(16,),
        element_semantics="input_and_output_elements_per_rank",
        checker_element_count=16,
        input_elements_per_rank=16,
        output_elements_per_rank=16,
        hccl_test_elements_per_rank=16,
        checker_collective_type="AllReduce",
        checker_reduce_type="SUM",
        required_checker_stages=REQUIRED_CHECKER_STAGES,
        warning_baseline_count=WARNING_103_BASELINE_COUNT,
        warning_baseline_summaries=(WARNING_103_BASELINE_SUMMARY,),
    ),
    CollectiveSpec(
        canonical_name="AllGather",
        aliases=("allgather", "all_gather", "all-gather"),
        executable_basename="all_gather_test",
        requires_reduce_op=False,
        allowed_reduce_ops=(),
        allowed_dtypes=("int32",),
        allowed_rank_counts=(2,),
        allowed_elements=(8,),
        element_semantics="input_elements_per_rank",
        checker_element_count=8,
        input_elements_per_rank=8,
        output_elements_per_rank=16,
        hccl_test_elements_per_rank=16,
        checker_collective_type="AllGather",
        checker_reduce_type=None,
        required_checker_stages=REQUIRED_CHECKER_STAGES,
        warning_baseline_count=WARNING_103_BASELINE_COUNT,
        warning_baseline_summaries=(WARNING_103_BASELINE_SUMMARY,),
    ),
    CollectiveSpec(
        canonical_name="ReduceScatter",
        aliases=(
            "reducescatter",
            "reduce_scatter",
            "reduce-scatter",
        ),
        executable_basename="reduce_scatter_test",
        requires_reduce_op=True,
        allowed_reduce_ops=("sum",),
        allowed_dtypes=("int32",),
        allowed_rank_counts=(2,),
        allowed_elements=(8,),
        element_semantics="output_elements_per_rank",
        checker_element_count=8,
        input_elements_per_rank=16,
        output_elements_per_rank=8,
        hccl_test_elements_per_rank=16,
        checker_collective_type="ReduceScatter",
        checker_reduce_type="SUM",
        required_checker_stages=REQUIRED_CHECKER_STAGES,
        warning_baseline_count=WARNING_103_BASELINE_COUNT,
        warning_baseline_summaries=(WARNING_103_BASELINE_SUMMARY,),
    ),
)

PRIMITIVE_REGISTRY: Mapping[str, CollectiveSpec] = MappingProxyType({
    spec.canonical_name: spec for spec in _SPECS
})
_ALIASES: Mapping[str, CollectiveSpec] = MappingProxyType({
    alias: spec
    for spec in _SPECS
    for alias in spec.aliases
})


def normalize_primitive(value: str) -> CollectiveSpec:
    if not isinstance(value, str):
        raise ValueError("primitive must be a string")
    normalized = value.strip().casefold()
    try:
        return _ALIASES[normalized]
    except KeyError as exc:
        choices = ", ".join(PRIMITIVE_REGISTRY)
        raise ValueError(
            f"Unsupported official primitive {value!r}; expected one of: {choices}"
        ) from exc


def resolve_collective_request(
    *,
    primitive: str,
    rank_count: int,
    dtype: str,
    reduce_op: str | None,
    elements: int,
) -> ResolvedCollectiveContract:
    spec = normalize_primitive(primitive)
    normalized_dtype = _normalize_token("dtype", dtype)
    if normalized_dtype not in spec.allowed_dtypes:
        raise ValueError(
            f"{spec.canonical_name} supports only dtype="
            f"{', '.join(spec.allowed_dtypes)}"
        )
    if rank_count not in spec.allowed_rank_counts:
        allowed = ", ".join(str(value) for value in spec.allowed_rank_counts)
        raise ValueError(
            f"{spec.canonical_name} supports only rank_count={allowed}"
        )
    if elements not in spec.allowed_elements:
        allowed = ", ".join(str(value) for value in spec.allowed_elements)
        raise ValueError(
            f"{spec.canonical_name} supports only elements={allowed}"
        )
    if spec.requires_reduce_op:
        if reduce_op is None:
            raise ValueError(
                f"{spec.canonical_name} requires an explicit reduce_op"
            )
        normalized_op = _normalize_token("reduce_op", reduce_op)
        if normalized_op not in spec.allowed_reduce_ops:
            allowed = ", ".join(spec.allowed_reduce_ops)
            raise ValueError(
                f"{spec.canonical_name} supports only reduce_op={allowed}"
            )
    else:
        if reduce_op is not None:
            raise ValueError(
                f"{spec.canonical_name} does not accept reduce_op"
            )
        normalized_op = None

    _validate_executable_basename(spec.executable_basename)
    return ResolvedCollectiveContract(
        registry_version=REGISTRY_VERSION,
        canonical_primitive=spec.canonical_name,
        input_alias=primitive.strip(),
        rank_count=rank_count,
        dtype=normalized_dtype,
        dtype_size_bytes=INT32_SIZE_BYTES,
        reduce_op=normalized_op,
        request_elements=elements,
        element_semantics=spec.element_semantics,
        checker_element_count=spec.checker_element_count,
        input_elements_per_rank=spec.input_elements_per_rank,
        output_elements_per_rank=spec.output_elements_per_rank,
        input_bytes_per_rank=(
            spec.input_elements_per_rank * INT32_SIZE_BYTES
        ),
        output_bytes_per_rank=(
            spec.output_elements_per_rank * INT32_SIZE_BYTES
        ),
        hccl_test_bytes=(
            spec.hccl_test_elements_per_rank * INT32_SIZE_BYTES
        ),
        executable_basename=spec.executable_basename,
        checker_collective_type=spec.checker_collective_type,
        checker_reduce_type=spec.checker_reduce_type,
        required_checker_stages=spec.required_checker_stages,
        warning_baseline_count=spec.warning_baseline_count,
        warning_baseline_summaries=spec.warning_baseline_summaries,
    )


def resolve_hccl_test_path(
    hccl_test_bin: str,
    contract: ResolvedCollectiveContract,
) -> str:
    """Join only an immutable registry basename below the configured bin dir."""
    _validate_executable_basename(contract.executable_basename)
    normalized_bin = posixpath.normpath(hccl_test_bin)
    if not posixpath.isabs(normalized_bin):
        raise ValueError("hccl_test_bin must be an absolute POSIX path")
    executable_path = posixpath.normpath(posixpath.join(
        normalized_bin,
        contract.executable_basename,
    ))
    if posixpath.dirname(executable_path) != normalized_bin:
        raise ValueError("resolved hccl_test executable escaped hccl_test_bin")
    return executable_path


def build_hccl_test_argv(
    contract: ResolvedCollectiveContract,
    hccl_test_bin: str,
) -> list[str]:
    argv = [
        "mpirun",
        "--allow-run-as-root",
        "--oversubscribe",
        "-np",
        str(contract.rank_count),
        resolve_hccl_test_path(hccl_test_bin, contract),
        "-b",
        str(contract.hccl_test_bytes),
        "-e",
        str(contract.hccl_test_bytes),
        "-d",
        contract.dtype,
    ]
    if contract.reduce_op is not None:
        argv.extend(["-o", contract.reduce_op])
    argv.extend(["-w", "0", "-n", "1", "-c", "1"])
    return argv


def _normalize_token(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip().casefold()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _validate_executable_basename(value: str) -> None:
    if (
        not value
        or value != posixpath.basename(value)
        or "/" in value
        or "\\" in value
        or ".." in value
        or "\x00" in value
        or any(character.isspace() for character in value)
    ):
        raise ValueError("registry executable basename is invalid")
