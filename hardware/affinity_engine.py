"""Affinity Engine — compute device/NIC locality scores."""

from typing import Any, Dict


class AffinityEngine:
    """Evaluate hardware affinity for communication placement."""

    @staticmethod
    def calculate_device_affinity(
        device_a: int, device_b: int, node_profile: Any,
    ) -> float:
        """Return 0-1 affinity between two devices on the same node."""
        aff = node_profile.device_affinity
        # Same NUMA domain → high affinity.
        if aff.get(device_a) == aff.get(device_b):
            return 0.9
        return 0.5

    @staticmethod
    def calculate_nic_affinity(device: int, nic: int, node_profile: Any) -> float:
        """Return 0-1 affinity between a device and a NIC."""
        nic_aff = node_profile.nic_affinity
        if nic_aff.get(device) == nic:
            return 1.0
        return 0.3

    @staticmethod
    def evaluate_locality(node_profile: Any) -> Dict[str, Any]:
        """Compute overall locality score and NUMA penalty."""
        numa = node_profile.numa_domains
        devices = node_profile.num_devices
        # More NUMA domains → more cross-domain traffic → penalty.
        numa_penalty = max(0.0, (numa - 1) * 0.1)
        locality = max(0.0, 1.0 - numa_penalty)
        return {
            "locality_score": round(locality, 2),
            "numa_penalty": round(numa_penalty, 2),
        }
