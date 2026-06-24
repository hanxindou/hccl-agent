"""Hardware Reasoning Skill — analyze resources, detect bottlenecks."""

from typing import Any, Dict, List

from hardware.affinity_engine import AffinityEngine
from hardware.resource_manager import ResourceManager


class HardwareReasoningSkill:
    """Analyze hardware resources and provide placement recommendations."""

    @staticmethod
    def analyze_resources(
        resource_manager: ResourceManager,
        node_id: int,
    ) -> Dict[str, Any]:
        usage = resource_manager.get_resource_usage(node_id)
        hbm_pressure = (
            1.0 - usage.get("hbm_available_gb", 0) /
            max(usage.get("hbm_available_gb", 0) + usage.get("hbm_used_gb", 0), 0.001)
        )
        return {
            "resource_pressure": round(hbm_pressure, 2),
            "hbm_available": usage.get("hbm_available_gb", 0),
            "ub_available": usage.get("ub_available_mb", 0),
        }

    @staticmethod
    def detect_bottlenecks(
        node_profiles: List[Any],
        resource_manager: ResourceManager,
    ) -> List[str]:
        bottlenecks: List[str] = []
        for np in node_profiles:
            usage = resource_manager.get_resource_usage(np.node_id)
            if usage.get("hbm_available_gb", 0) < 1.0:
                bottlenecks.append(
                    f"Node {np.node_id}: HBM nearly exhausted "
                    f"({usage['hbm_available_gb']:.2f} GB free)"
                )
            if usage.get("ub_available_mb", 0) < 0.01:
                bottlenecks.append(
                    f"Node {np.node_id}: UB nearly exhausted"
                )
        return bottlenecks

    @staticmethod
    def recommend_placement(
        node_profile: Any,
        num_ranks: int,
    ) -> Dict[str, Any]:
        """Suggest how to place ranks across NUMA domains."""
        devices_per_numa = max(
            1, node_profile.num_devices // node_profile.numa_domains,
        )
        locality = AffinityEngine.evaluate_locality(node_profile)
        return {
            "ranks_per_numa": min(num_ranks, devices_per_numa),
            "numa_domains_used": min(
                node_profile.numa_domains,
                (num_ranks + devices_per_numa - 1) // devices_per_numa,
            ),
            "locality_score": locality["locality_score"],
        }
