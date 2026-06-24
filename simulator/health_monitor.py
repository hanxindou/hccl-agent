"""Health Monitor — evaluate cluster and link health status."""

import random
from typing import Any, Dict, List, Optional


class HealthMonitor:
    """Monitor link and node health in a communication graph."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)
        self.link_states: Dict[str, bool] = {}
        self.node_states: Dict[int, bool] = {}

    def check_link(self, src: int, dst: int) -> Dict[str, Any]:
        """Check health of a specific link."""
        key = f"{src}->{dst}"
        healthy = self.link_states.get(key, True)
        return {
            "link": key,
            "healthy": healthy,
            "error_rate": 0.0 if healthy else 1.0,
            "status": "UP" if healthy else "DOWN",
        }

    def check_node(self, node_id: int) -> Dict[str, Any]:
        """Check health of a specific node."""
        healthy = self.node_states.get(node_id, True)
        return {
            "node": node_id,
            "healthy": healthy,
            "status": "UP" if healthy else "DOWN",
        }

    def inject_failures(
        self,
        num_nodes: int,
        link_failure_rate: float = 0.0,
        node_failure_rate: float = 0.0,
    ) -> None:
        """Randomly mark links/nodes as unhealthy based on rates."""
        # Node failures.
        for nid in range(num_nodes):
            if self.rng.random() < node_failure_rate:
                self.node_states[nid] = False
        # Link failures (Full Mesh assumption: all pairs).
        for src in range(num_nodes):
            for dst in range(num_nodes):
                if src != dst and self.rng.random() < link_failure_rate:
                    self.link_states[f"{src}->{dst}"] = False

    def evaluate_cluster_health(
        self, graph: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Return overall cluster health summary."""
        total_links = len(self.link_states)
        failed_links = sum(1 for v in self.link_states.values() if not v)
        total_nodes = len(self.node_states)
        failed_nodes = sum(1 for v in self.node_states.values() if not v)

        link_error_rate = failed_links / max(total_links, 1)
        healthy = failed_links == 0 and failed_nodes == 0

        return {
            "healthy": healthy,
            "error_rate": round(link_error_rate, 4),
            "failed_links": failed_links,
            "failed_nodes": failed_nodes,
            "status": "HEALTHY" if healthy else "DEGRADED",
        }

    def is_link_healthy(self, src: int, dst: int) -> bool:
        """Quick boolean check for a link."""
        return self.link_states.get(f"{src}->{dst}", True)

    def is_node_healthy(self, node_id: int) -> bool:
        """Quick boolean check for a node."""
        return self.node_states.get(node_id, True)
