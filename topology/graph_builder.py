"""Topology Graph Builder — cluster config + hardware profile → weighted graph."""

import math
from typing import Any, Dict, List, Tuple

from hardware.profile import HardwareProfile


class TopologyEdge:
    """A directed edge in the communication graph."""

    def __init__(self, src: int, dst: int, link_type: str,
                 bandwidth_gbps: float, latency_ms: float,
                 contention_weight: float = 1.0) -> None:
        self.src = src
        self.dst = dst
        self.link_type = link_type
        self.bandwidth_gbps = bandwidth_gbps
        self.latency_ms = latency_ms
        self.contention_weight = contention_weight

    def __repr__(self) -> str:
        return (
            f"Edge({self.src}→{self.dst} {self.link_type} "
            f"{self.bandwidth_gbps}Gbps {self.latency_ms}ms)"
        )


class CommunicationGraph:
    """Weighted directed graph for collective communication simulation."""

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.num_nodes: int = 0
        self.edges: List[TopologyEdge] = []
        self._adj: Dict[int, List[TopologyEdge]] = {}

    def add_edge(self, src: int, dst: int, link_type: str,
                 bandwidth_gbps: float, latency_ms: float,
                 bidirectional: bool = True,
                 contention_weight: float = 1.0) -> None:
        """Add a directed edge (and optionally its reverse)."""
        self.num_nodes = max(self.num_nodes, src + 1, dst + 1)
        e = TopologyEdge(src, dst, link_type, bandwidth_gbps,
                         latency_ms, contention_weight)
        self.edges.append(e)
        self._adj.setdefault(src, []).append(e)
        if bidirectional:
            rev = TopologyEdge(dst, src, link_type, bandwidth_gbps,
                               latency_ms, contention_weight)
            self.edges.append(rev)
            self._adj.setdefault(dst, []).append(rev)

    def outgoing(self, node: int) -> List[TopologyEdge]:
        """Edges originating at *node*."""
        return self._adj.get(node, [])

    def all_paths_segments(self, path: List[int]) -> List[TopologyEdge]:
        """Return the edge sequence traversed by *path*."""
        segs: List[TopologyEdge] = []
        for i in range(len(path) - 1):
            src, dst = path[i], path[i + 1]
            found = None
            for e in self._adj.get(src, []):
                if e.dst == dst:
                    found = e
                    break
            if found:
                segs.append(found)
        return segs


class TopologyGraphBuilder:
    """Build a CommunicationGraph from cluster params and a HardwareProfile."""

    @staticmethod
    def build(
        num_nodes: int,
        num_gpus_per_node: int = 8,
        profile: HardwareProfile | None = None,
        mode: str = "SINGLE_NODE",
    ) -> Tuple[CommunicationGraph, Dict[str, Any]]:
        """Construct a weighted communication graph.

        Parameters
        ----------
        num_nodes : int
            Total NPU count.
        num_gpus_per_node : int
            GPUs per server (used in MULTI_NODE mode).
        profile : HardwareProfile or None
        mode : "SINGLE_NODE" | "MULTI_NODE" | "HETEROGENEOUS"

        Returns
        -------
        (CommunicationGraph, metadata dict)
        """
        if profile is None:
            profile = HardwareProfile.tier_medium()

        if mode == "SINGLE_NODE":
            return TopologyGraphBuilder._build_single(num_nodes, profile)
        elif mode == "MULTI_NODE":
            return TopologyGraphBuilder._build_multi(
                num_nodes, num_gpus_per_node, profile,
            )
        else:  # HETEROGENEOUS
            return TopologyGraphBuilder._build_hetero(
                num_nodes, num_gpus_per_node, profile,
            )

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_single(
        N: int, profile: HardwareProfile,
    ) -> Tuple[CommunicationGraph, Dict[str, Any]]:
        g = CommunicationGraph(name=f"single-node-{N}")
        hccs = profile.get_link_properties("HCCS")
        bw, lat = hccs["bandwidth_gbps"], hccs["latency_ms"]
        # Full mesh within a single server.
        for i in range(N):
            for j in range(i + 1, N):
                cw = 1.0 + (N - 1) * 0.03  # mild contention per link
                g.add_edge(i, j, "HCCS", bw, lat, bidirectional=True,
                           contention_weight=cw)
        return g, {"mode": "SINGLE_NODE", "topology": "Full Mesh"}

    @staticmethod
    def _build_multi(
        N: int, gpus_per: int, profile: HardwareProfile,
    ) -> Tuple[CommunicationGraph, Dict[str, Any]]:
        g = CommunicationGraph(name=f"multi-node-{N}")
        hccs = profile.get_link_properties("HCCS")
        roce = profile.get_link_properties("RoCE")
        num_servers = max(1, int(math.ceil(N / gpus_per)))

        # Intra-server: full mesh per server (HCCS).
        for s in range(num_servers):
            base = s * gpus_per
            end = min(base + gpus_per, N)
            for i in range(base, end):
                for j in range(i + 1, end):
                    g.add_edge(i, j, "HCCS", hccs["bandwidth_gbps"],
                               hccs["latency_ms"], bidirectional=True)

        # Inter-server: ring among server leaders (RoCE).
        leaders = [s * gpus_per for s in range(num_servers)]
        for si in range(num_servers):
            sj = (si + 1) % num_servers
            g.add_edge(leaders[si], leaders[sj], "RoCE",
                       roce["bandwidth_gbps"], roce["latency_ms"],
                       bidirectional=False,
                       contention_weight=1.0 + num_servers * 0.05)

        return g, {"mode": "MULTI_NODE", "topology": "Fat Tree",
                   "num_servers": num_servers}

    @staticmethod
    def _build_hetero(
        N: int, gpus_per: int, profile: HardwareProfile,
    ) -> Tuple[CommunicationGraph, Dict[str, Any]]:
        g = CommunicationGraph(name=f"hetero-{N}")
        hccs = profile.get_link_properties("HCCS")
        roce = profile.get_link_properties("RoCE")
        pcie = profile.get_link_properties("PCIe")
        num_servers = max(1, int(math.ceil(N / gpus_per)))

        # Intra-server: HCCS full mesh.
        for s in range(num_servers):
            base = s * gpus_per
            end = min(base + gpus_per, N)
            for i in range(base, end):
                for j in range(i + 1, end):
                    g.add_edge(i, j, "HCCS", hccs["bandwidth_gbps"],
                               hccs["latency_ms"], bidirectional=True)

        # Inter-server: asymmetric RoCE with PCIe fallback.
        for s in range(num_servers):
            for t in range(num_servers):
                if s == t:
                    continue
                ldr_s = s * gpus_per
                ldr_t = t * gpus_per
                # Simple asymmetry: half bandwidth for cross-rack.
                bw = roce["bandwidth_gbps"] * 0.5
                g.add_edge(ldr_s, ldr_t, "RoCE", bw,
                           roce["latency_ms"], bidirectional=False,
                           contention_weight=1.2)

        # PCIe links for leaf-level nodes.
        for i in range(N):
            for j in range(i + 1, N):
                if not any(e.src == i and e.dst == j for e in g.edges):
                    g.add_edge(i, j, "PCIe", pcie["bandwidth_gbps"],
                               pcie["latency_ms"], bidirectional=True,
                               contention_weight=2.0)

        return g, {"mode": "HETEROGENEOUS", "topology": "Mixed",
                   "num_servers": num_servers}
