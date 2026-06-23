"""Hardware Abstraction Layer — configurable link profiles.

Provides a HardwareProfile that models link types (HCCS, RoCE, PCIe)
without hard-coding real Ascend hardware values.  Profiles can be
expressed as relative tiers (high / medium / low) or fully custom.
"""

import json
from typing import Any, Dict


class HardwareProfile:
    """Configurable hardware link-behaviour profile."""

    def __init__(
        self,
        device_type: str = "generic-ascend",
        link_types: Dict[str, Dict[str, float]] | None = None,
    ) -> None:
        self.device_type = device_type
        if link_types is None:
            link_types = HardwareProfile._default_links()
        self.link_types = link_types

    # ----------------------------------------------------------------
    # Serialisation
    # ----------------------------------------------------------------

    @classmethod
    def from_json(cls, path: str) -> "HardwareProfile":
        """Load a profile from a JSON file."""
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(
            device_type=data.get("device_type", "generic-ascend"),
            link_types=data.get("link_types", {}),
        )

    def to_json(self, path: str) -> None:
        """Persist this profile to *path*."""
        payload: Dict[str, Any] = {
            "device_type": self.device_type,
            "link_types": self.link_types,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    # ----------------------------------------------------------------
    # Query
    # ----------------------------------------------------------------

    def get_link_properties(self, link_type: str) -> Dict[str, float]:
        """Return (bandwidth_gbps, latency_ms) for *link_type*."""
        entry = self.link_types.get(
            link_type, {"bandwidth_gbps": 100.0, "latency_ms": 0.005}
        )
        return dict(entry)

    # ----------------------------------------------------------------
    # Pre-built tiers (relative models — NOT real hardware values)
    # ----------------------------------------------------------------

    @classmethod
    def tier_high(cls) -> "HardwareProfile":
        return cls(device_type="high-tier", link_types={
            "HCCS": {"bandwidth_gbps": 200.0, "latency_ms": 0.001},
            "RoCE": {"bandwidth_gbps": 100.0, "latency_ms": 0.003},
            "PCIe": {"bandwidth_gbps":  64.0, "latency_ms": 0.008},
        })

    @classmethod
    def tier_medium(cls) -> "HardwareProfile":
        return cls(device_type="medium-tier", link_types={
            "HCCS": {"bandwidth_gbps": 100.0, "latency_ms": 0.002},
            "RoCE": {"bandwidth_gbps":  50.0, "latency_ms": 0.005},
            "PCIe": {"bandwidth_gbps":  32.0, "latency_ms": 0.010},
        })

    @classmethod
    def tier_low(cls) -> "HardwareProfile":
        return cls(device_type="low-tier", link_types={
            "HCCS": {"bandwidth_gbps":  50.0, "latency_ms": 0.004},
            "RoCE": {"bandwidth_gbps":  25.0, "latency_ms": 0.010},
            "PCIe": {"bandwidth_gbps":  16.0, "latency_ms": 0.020},
        })

    # ----------------------------------------------------------------
    # Internal
    # ----------------------------------------------------------------

    @staticmethod
    def _default_links() -> Dict[str, Dict[str, float]]:
        return HardwareProfile.tier_medium().link_types
