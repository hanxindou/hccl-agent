"""Failover Engine — reroute communication around failed links."""

from typing import Any, Dict, List, Optional


class FailoverEngine:
    """Find alternative paths when links fail."""

    def __init__(self) -> None:
        self.failover_count: int = 0

    def reroute(
        self,
        graph: Any,
        src: int,
        dst: int,
        failed_edge: Optional[tuple] = None,
        monitor: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Find an alternative path from *src* to *dst* avoiding failed links.

        Returns
        -------
        dict
            {"found": bool, "route": list, "hops": int, "failover_triggered": bool}
        """
        # Direct path is healthy → no failover needed.
        direct_healthy = True
        if monitor and failed_edge:
            direct_healthy = monitor.is_link_healthy(
                failed_edge[0], failed_edge[1],
            )

        if direct_healthy and failed_edge is None:
            return {
                "found": True,
                "route": [src, dst],
                "hops": 1,
                "failover_triggered": False,
            }

        # Try to find a path via an intermediate node.
        N = graph.num_nodes if hasattr(graph, "num_nodes") else 0
        for via in range(N):
            if via == src or via == dst:
                continue
            if monitor:
                if (not monitor.is_link_healthy(src, via) or
                        not monitor.is_link_healthy(via, dst)):
                    continue
            self.failover_count += 1
            return {
                "found": True,
                "route": [src, via, dst],
                "hops": 2,
                "failover_triggered": True,
            }

        return {
            "found": False,
            "route": [],
            "hops": 0,
            "failover_triggered": True,
        }
