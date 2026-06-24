"""Node Profile — per-node hardware resource description."""

from typing import Any, Dict


class NodeProfile:
    """Hardware resource model for a single server node."""

    def __init__(
        self,
        node_id: int = 0,
        num_devices: int = 8,
        num_nics: int = 4,
        numa_domains: int = 2,
        hbm_capacity_gb: float = 64.0,
        ub_capacity_mb: float = 0.192,
        device_affinity: Dict[int, int] | None = None,
        nic_affinity: Dict[int, int] | None = None,
    ) -> None:
        self.node_id = node_id
        self.num_devices = num_devices
        self.num_nics = num_nics
        self.numa_domains = numa_domains
        self.hbm_capacity_gb = hbm_capacity_gb
        self.ub_capacity_mb = ub_capacity_mb
        self.device_affinity = device_affinity or {}
        self.nic_affinity = nic_affinity or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "num_devices": self.num_devices,
            "num_nics": self.num_nics,
            "numa_domains": self.numa_domains,
            "hbm_capacity_gb": self.hbm_capacity_gb,
            "ub_capacity_mb": self.ub_capacity_mb,
            "device_affinity": self.device_affinity,
            "nic_affinity": self.nic_affinity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeProfile":
        return cls(
            node_id=data.get("node_id", 0),
            num_devices=data.get("num_devices", 8),
            num_nics=data.get("num_nics", 4),
            numa_domains=data.get("numa_domains", 2),
            hbm_capacity_gb=data.get("hbm_capacity_gb", 64.0),
            ub_capacity_mb=data.get("ub_capacity_mb", 0.192),
            device_affinity=data.get("device_affinity", {}),
            nic_affinity=data.get("nic_affinity", {}),
        )

    def resource_summary(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "devices": self.num_devices,
            "nics": self.num_nics,
            "numa": self.numa_domains,
            "hbm_gb": self.hbm_capacity_gb,
            "ub_mb": self.ub_capacity_mb,
        }
