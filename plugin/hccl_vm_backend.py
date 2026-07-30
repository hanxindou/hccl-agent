"""Backend selection and configuration for official HCCL-VM validation."""

from __future__ import annotations

import json
import os
import posixpath
from dataclasses import asdict, dataclass, fields
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class Backend(str, Enum):
    CPU_SIM = "CPU_SIM"
    ASCEND_HCCL_VM = "ASCEND_HCCL_VM"


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "hccl_vm.json"
)

ENV_FIELDS = {
    "backend": "HCCL_AGENT_BACKEND",
    "wsl_distro": "HCCL_VM_WSL_DISTRO",
    "cann_path": "HCCL_VM_CANN_PATH",
    "hccl_vm_install_dir": "HCCL_VM_INSTALL_DIR",
    "hccl_test_bin": "HCCL_VM_HCCL_TEST_BIN",
    "hcomm_source_dir": "HCCL_VM_HCOMM_SOURCE_DIR",
    "hccl_source_dir": "HCCL_VM_HCCL_SOURCE_DIR",
    "topology": "HCCL_VM_TOPOLOGY",
    "mock_comm": "HCCL_VM_MOCK_COMM",
    "expansion_mode": "HCCL_VM_EXPANSION_MODE",
    "check_only": "HCCL_VM_CHECK_ONLY",
    "evidence_root": "HCCL_VM_EVIDENCE_ROOT",
    "timeout_seconds": "HCCL_VM_TIMEOUT_SECONDS",
}


@dataclass(frozen=True)
class HcclVmConfig:
    backend: str = Backend.CPU_SIM.value
    wsl_distro: str = "Ubuntu-22.04"
    cann_path: str = "/home/workspace/Ascend/cann-9.1.0"
    hccl_vm_install_dir: str = (
        "/home/workspace/hcomm/test/hccl_vm/hccl_vm_install"
    )
    hccl_test_bin: str = (
        "/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin"
    )
    hcomm_source_dir: str = "/home/workspace/hcomm"
    hccl_source_dir: str = "/home/workspace/hccl"
    topology: str = "ascend950_cluster_32_server_normal.yaml"
    mock_comm: str = "112"
    expansion_mode: str = "CCU_SCHED"
    check_only: bool = True
    evidence_root: str = "experiments/hccl_vm/evidence"
    timeout_seconds: int = 900

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend", normalize_backend(self.backend))
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, str) and (
                "\x00" in value or "\n" in value or "\r" in value
            ):
                raise ValueError(
                    f"{field.name} must not contain NUL or newline characters"
                )
        for field_name in ("hcomm_source_dir", "hccl_source_dir"):
            _validate_exact_repo_path(field_name, getattr(self, field_name))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_backend(value: str | Backend) -> str:
    raw_value = value.value if isinstance(value, Backend) else str(value)
    normalized = raw_value.strip().upper()
    try:
        return Backend(normalized).value
    except ValueError as exc:
        choices = ", ".join(item.value for item in Backend)
        raise ValueError(
            f"Unsupported backend {raw_value!r}; expected one of: {choices}"
        ) from exc


def load_hccl_vm_config(
    config_path: str | os.PathLike[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> HcclVmConfig:
    """Load config with CLI overrides > environment > JSON > defaults."""

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    raw_config: dict[str, Any] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError(f"HCCL-VM config must be a JSON object: {path}")
        raw_config.update(loaded)
    elif config_path is not None:
        raise FileNotFoundError(f"HCCL-VM config not found: {path}")

    valid_fields = {field.name for field in fields(HcclVmConfig)}
    unknown = sorted(set(raw_config) - valid_fields)
    if unknown:
        raise ValueError(
            "Unknown HCCL-VM config fields: " + ", ".join(unknown)
        )

    values = HcclVmConfig().to_dict()
    values.update(raw_config)

    env_values = os.environ if environ is None else environ
    for field_name, env_name in ENV_FIELDS.items():
        if env_name in env_values and env_values[env_name] != "":
            values[field_name] = _coerce_value(
                field_name, env_values[env_name]
            )

    for field_name, value in (overrides or {}).items():
        if field_name not in valid_fields:
            raise ValueError(f"Unknown HCCL-VM override: {field_name}")
        if value is not None:
            values[field_name] = _coerce_value(field_name, value)

    return HcclVmConfig(**values)


def _coerce_value(field_name: str, value: Any) -> Any:
    if field_name == "check_only":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"Invalid boolean for {field_name}: {value!r}")
    if field_name == "timeout_seconds":
        return int(value)
    if field_name == "backend":
        return normalize_backend(value)
    return str(value)


def _validate_exact_repo_path(field_name: str, value: str) -> None:
    if not posixpath.isabs(value):
        raise ValueError(f"{field_name} must be an absolute POSIX path")
    if posixpath.normpath(value) == "/":
        raise ValueError(f"{field_name} must not be the filesystem root")
    if any(character in value for character in ("*", "?", "[", "]")):
        raise ValueError(f"{field_name} must not contain glob characters")
