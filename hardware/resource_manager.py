"""Resource Manager — track HBM and UB allocation across nodes."""

from typing import Any, Dict, List


class ResourceManager:
    """Simulated resource allocator for HBM and UB."""

    def __init__(self, node_profiles: List[Any]) -> None:
        self.profiles = node_profiles
        self._hbm_used: Dict[int, float] = {}
        self._ub_used: Dict[int, float] = {}

    def allocate_hbm(self, node_id: int, amount_gb: float) -> bool:
        profile = self._find(node_id)
        if not profile:
            return False
        used = self._hbm_used.get(node_id, 0.0)
        if used + amount_gb <= profile.hbm_capacity_gb:
            self._hbm_used[node_id] = used + amount_gb
            return True
        return False

    def release_hbm(self, node_id: int, amount_gb: float) -> None:
        self._hbm_used[node_id] = max(
            0.0, self._hbm_used.get(node_id, 0.0) - amount_gb,
        )

    def allocate_ub(self, node_id: int, amount_mb: float) -> bool:
        profile = self._find(node_id)
        if not profile:
            return False
        used = self._ub_used.get(node_id, 0.0)
        if used + amount_mb <= profile.ub_capacity_mb:
            self._ub_used[node_id] = used + amount_mb
            return True
        return False

    def release_ub(self, node_id: int, amount_mb: float) -> None:
        self._ub_used[node_id] = max(
            0.0, self._ub_used.get(node_id, 0.0) - amount_mb,
        )

    def get_resource_usage(self, node_id: int) -> Dict[str, Any]:
        profile = self._find(node_id)
        if not profile:
            return {}
        return {
            "hbm_used_gb": self._hbm_used.get(node_id, 0.0),
            "hbm_available_gb": max(
                0.0, profile.hbm_capacity_gb - self._hbm_used.get(node_id, 0.0),
            ),
            "ub_used_mb": self._ub_used.get(node_id, 0.0),
            "ub_available_mb": max(
                0.0, profile.ub_capacity_mb - self._ub_used.get(node_id, 0.0),
            ),
        }

    def _find(self, node_id: int) -> Any:
        for p in self.profiles:
            if p.node_id == node_id:
                return p
        return None
