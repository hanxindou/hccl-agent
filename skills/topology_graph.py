"""Weighted directed graph model for NPU cluster topology.

Moves beyond the simple string-based topology (Full Mesh / Ring / Fat Tree)
to a graph that supports link types, bandwidth, latency, BER, and path
computation — a key requirement for the competition's hardware-aware
algorithm selection.
"""

import heapq
import math


class TopologyNode:
    """A single NPU device in the topology graph."""

    def __init__(self, node_id, device_type="Ascend910A"):
        self.node_id = node_id
        self.device_type = device_type

    def __repr__(self):
        return f"Node({self.node_id}, {self.device_type})"


class TopologyEdge:
    """A directed or undirected link between two NPU nodes."""

    def __init__(
        self,
        src,
        dst,
        link_type="HCCS",
        bandwidth_gbps=100.0,
        latency_ms=0.002,
        ber=1e-12,
        healthy=True,
    ):
        self.src = src
        self.dst = dst
        self.link_type = link_type
        self.bandwidth_gbps = bandwidth_gbps
        self.latency_ms = latency_ms
        self.ber = ber           # bit error rate
        self.healthy = healthy   # True unless a fault is injected

    def __repr__(self):
        state = "up" if self.healthy else "DOWN"
        return (
            f"Edge({self.src}->{self.dst}, "
            f"{self.link_type}, {self.bandwidth_gbps}Gbps, "
            f"{state})"
        )

    @property
    def weight_latency(self):
        """Edge weight for latency-minimising path computation."""
        if not self.healthy:
            return float("inf")
        return self.latency_ms

    @property
    def weight_bandwidth(self):
        """Edge weight for bandwidth-maximising path computation.

        Returns inverse bandwidth so Dijkstra picks the highest-bandwidth
        path.
        """
        if not self.healthy or self.bandwidth_gbps <= 0:
            return float("inf")
        return 1.0 / self.bandwidth_gbps


class TopologyGraph:
    """Weighted graph representing NPU cluster connectivity."""

    def __init__(self, name="cluster"):
        self.name = name
        self.nodes = {}    # node_id -> TopologyNode
        self.edges = {}    # (src, dst) -> TopologyEdge

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def add_node(self, node_id, device_type="Ascend910A"):
        if node_id not in self.nodes:
            self.nodes[node_id] = TopologyNode(node_id, device_type)

    def add_edge(
        self,
        src,
        dst,
        link_type="HCCS",
        bandwidth_gbps=100.0,
        latency_ms=0.002,
        ber=1e-12,
        bidirectional=True,
    ):
        """Add an edge.  *bidirectional* adds the reverse edge as well."""
        self.add_node(src)
        self.add_node(dst)
        self.edges[(src, dst)] = TopologyEdge(
            src, dst, link_type, bandwidth_gbps, latency_ms, ber
        )
        if bidirectional:
            self.edges[(dst, src)] = TopologyEdge(
                dst, src, link_type, bandwidth_gbps, latency_ms, ber
            )

    # ------------------------------------------------------------------
    # Factory methods for standard topologies
    # ------------------------------------------------------------------

    @classmethod
    def full_mesh(cls, num_nodes, link_type="HCCS", **kwargs):
        """Every node connected to every other node."""
        g = cls(name=f"FullMesh-{num_nodes}")
        for i in range(num_nodes):
            g.add_node(i)
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                g.add_edge(i, j, link_type=link_type, **kwargs)
        return g

    @classmethod
    def ring(cls, num_nodes, link_type="HCCS", **kwargs):
        """Unidirectional ring: 0->1->2->...->N-1->0."""
        g = cls(name=f"Ring-{num_nodes}")
        for i in range(num_nodes):
            g.add_node(i)
        for i in range(num_nodes):
            nxt = (i + 1) % num_nodes
            g.add_edge(i, nxt, link_type=link_type, bidirectional=False,
                       **kwargs)
        return g

    @classmethod
    def fat_tree(cls, num_nodes, link_type="HCCS", **kwargs):
        """Simplified Fat-Tree: nodes grouped into racks, one switch per rack.

        Nodes in the same rack are fully connected (intra-rack); racks are
        connected in a ring (inter-rack).
        """
        g = cls(name=f"FatTree-{num_nodes}")
        rack_size = min(8, max(2, num_nodes // 4))
        num_racks = int(math.ceil(num_nodes / rack_size))

        for i in range(num_nodes):
            g.add_node(i, device_type="Ascend910A")

        # Intra-rack: full mesh within each rack.
        for r in range(num_racks):
            start = r * rack_size
            end = min(start + rack_size, num_nodes)
            for i in range(start, end):
                for j in range(i + 1, end):
                    g.add_edge(i, j, link_type="HCCS", **kwargs)

        # Inter-rack: ring of rack-0 nodes.
        rack_heads = [
            r * rack_size for r in range(num_racks)
        ]
        for ri in range(num_racks):
            rj = (ri + 1) % num_racks
            g.add_edge(
                rack_heads[ri],
                rack_heads[rj],
                link_type="RoCE",
                bandwidth_gbps=kwargs.get("bandwidth_gbps", 100) * 0.5,
                latency_ms=kwargs.get("latency_ms", 0.002) * 5,
                bidirectional=False,
            )

        return g

    # ------------------------------------------------------------------
    # Path computation (Dijkstra)
    # ------------------------------------------------------------------

    def _dijkstra(self, start, weight_attr):
        """Return (dist, prev) maps from *start* using the given edge weight."""
        dist = {n: float("inf") for n in self.nodes}
        prev = {n: None for n in self.nodes}
        dist[start] = 0.0
        visited = set()
        heap = [(0.0, start)]

        while heap:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            for (src, dst), edge in self.edges.items():
                if src != u:
                    continue
                w = getattr(edge, weight_attr)
                if w == float("inf"):
                    continue
                nd = d + w
                if nd < dist[dst]:
                    dist[dst] = nd
                    prev[dst] = u
                    heapq.heappush(heap, (nd, dst))

        return dist, prev

    def shortest_path_latency(self, start, end):
        """Return (path, total_latency_ms) for the lowest-latency route."""
        dist, prev = self._dijkstra(start, "weight_latency")
        if dist[end] == float("inf"):
            return None, float("inf")
        path = []
        cur = end
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path, round(dist[end], 6)

    def max_bandwidth_path(self, start, end):
        """Return (path, bottleneck_bandwidth_gbps) via the widest path.

        Uses a max-bandwidth variant of Dijkstra (like modified shortest-path
        on inverse bandwidth).
        """
        bw = {n: 0.0 for n in self.nodes}
        prev = {n: None for n in self.nodes}
        bw[start] = float("inf")
        visited = set()
        # Use negative bandwidth for max-heap behavior with heapq (min-heap).
        heap = [(-float("inf"), start)]

        while heap:
            neg_b, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            for (src, dst), edge in self.edges.items():
                if src != u:
                    continue
                if not edge.healthy:
                    continue
                bottleneck = min(bw[u], edge.bandwidth_gbps)
                if bottleneck > bw[dst]:
                    bw[dst] = bottleneck
                    prev[dst] = u
                    heapq.heappush(heap, (-bottleneck, dst))

        if bw[end] == 0.0:
            return None, 0.0

        path = []
        cur = end
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path, round(bw[end], 2)

    # ------------------------------------------------------------------
    # Fault injection helpers (used by FaultInjector)
    # ------------------------------------------------------------------

    def set_link_health(self, src, dst, healthy):
        key = (src, dst)
        if key in self.edges:
            self.edges[key].healthy = healthy

    def get_unhealthy_links(self):
        return [
            key for key, e in self.edges.items() if not e.healthy
        ]

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self):
        return {
            "name": self.name,
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "link_types": list(
                set(e.link_type for e in self.edges.values())
            ),
        }
