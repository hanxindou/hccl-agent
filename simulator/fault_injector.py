"""Fault injection for communication reliability simulation.

Models link failures, timeouts, data corruption, and congestion events so
the Agent can evaluate algorithm robustness under adverse conditions — a
key requirement for the competition's reliability report.
"""

import random
import zlib


class FaultEvent:
    """A single injected fault."""

    def __init__(self, fault_type, link, timestamp, duration_ms=0,
                 description=""):
        self.fault_type = fault_type      # link_down, timeout, corruption,
                                          # congestion
        self.link = link                  # (src, dst) tuple
        self.timestamp = timestamp
        self.duration_ms = duration_ms
        self.description = description
        self.model_time_ms = int(round(timestamp * 1000.0))

    def __repr__(self):
        return (
            f"Fault({self.fault_type} on {self.link} "
            f"at {self.timestamp:.3f}s, {self.duration_ms}ms)"
        )


class FaultInjector:
    """Inject faults into a TopologyGraph and track reliability metrics."""

    FAULT_TYPES = ["link_down", "timeout", "corruption", "congestion"]

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.seed = seed
        self.fault_log = []            # list of FaultEvent
        self.retransmit_count = 0
        self.total_packets = 0
        self.corrupted_packets = 0
        self.dropped_packets = 0

    def _next_model_time(self):
        return len(self.fault_log) * 0.001

    @staticmethod
    def _iter_edges(graph):
        edges = getattr(graph, "edges", {})
        if isinstance(edges, dict):
            return edges.values()
        return edges

    @staticmethod
    def _find_edge(graph, src, dst):
        edges = getattr(graph, "edges", {})
        if isinstance(edges, dict):
            return edges.get((src, dst))
        for edge in edges:
            if getattr(edge, "src", None) == src and getattr(edge, "dst", None) == dst:
                return edge
        return None

    @staticmethod
    def compute_crc32(payload):
        """Return CRC32 for bytes-like payloads used by CPU_SIM tests."""
        return zlib.crc32(bytes(payload)) & 0xFFFFFFFF

    @classmethod
    def detect_corruption(cls, reference_payload, candidate_payload):
        """Detect simulated payload corruption through CRC32 mismatch."""
        return (
            cls.compute_crc32(reference_payload)
            != cls.compute_crc32(candidate_payload)
        )

    # ------------------------------------------------------------------
    # Fault generation
    # ------------------------------------------------------------------

    def inject_link_failure(self, graph, src, dst, duration_ms=100):
        """Bring down a specific link for *duration_ms*."""
        if hasattr(graph, "set_link_health"):
            graph.set_link_health(src, dst, False)
        edge = self._find_edge(graph, src, dst)
        if edge is not None:
            edge.healthy = False
        event = FaultEvent(
            "link_down",
            (src, dst),
            self._next_model_time(),
            duration_ms,
            f"Link {src}->{dst} down for {duration_ms}ms",
        )
        self.fault_log.append(event)
        return event

    def inject_random_link_failure(self, graph, duration_ms=100):
        """Randomly pick one edge and bring it down."""
        if not graph.edges:
            return None
        edge = self.rng.choice(list(self._iter_edges(graph)))
        edge_key = (
            (edge.src, edge.dst)
            if hasattr(edge, "src")
            else edge
        )
        return self.inject_link_failure(
            graph, edge_key[0], edge_key[1], duration_ms
        )

    def inject_timeout(self, graph, src, dst, timeout_ms=500):
        """Simulate a timeout on a specific link."""
        event = FaultEvent(
            "timeout",
            (src, dst),
            self._next_model_time(),
            timeout_ms,
            f"Timeout on {src}->{dst} ({timeout_ms}ms)",
        )
        self.fault_log.append(event)
        self.retransmit_count += 1
        return event

    def inject_corruption(self, graph, src, dst):
        """Simulate data corruption detected by CRC on a link."""
        event = FaultEvent(
            "corruption",
            (src, dst),
            self._next_model_time(),
            0,
            f"Data corruption on {src}->{dst}",
        )
        self.fault_log.append(event)
        self.corrupted_packets += 1
        self.retransmit_count += 1
        return event

    def inject_congestion(self, graph, src, dst, duration_ms=200,
                          bandwidth_reduction=0.5):
        """Reduce effective bandwidth on a link to simulate congestion."""
        event = FaultEvent(
            "congestion",
            (src, dst),
            self._next_model_time(),
            duration_ms,
            f"Congestion on {src}->{dst} "
            f"(BW reduced {bandwidth_reduction*100:.0f}%)",
        )
        self.fault_log.append(event)

        # Temporarily reduce bandwidth on the edge.
        edge = self._find_edge(graph, src, dst)
        if edge is not None:
            original_bw = edge.bandwidth_gbps
            edge.bandwidth_gbps *= (1.0 - bandwidth_reduction)
            # Store original so the caller can restore it.
            event._original_bw = original_bw

        return event

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def recover_link(self, graph, src, dst):
        """Restore a previously failed link to healthy state."""
        if hasattr(graph, "set_link_health"):
            graph.set_link_health(src, dst, True)
        edge = self._find_edge(graph, src, dst)
        if edge is not None:
            edge.healthy = True

    def recover_all_links(self, graph):
        """Restore all links in the graph to healthy."""
        for edge in self._iter_edges(graph):
            edge.healthy = True

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------

    def simulate_transmission(
        self,
        graph,
        src,
        dst,
        num_packets=1000,
        corruption_prob=0.001,
        timeout_prob=0.0005,
    ):
        """Simulate sending *num_packets* from src to dst.

        Applies random corruption and timeout faults based on the link BER
        and given probabilities.

        Returns a dict with success rate and retransmission stats.
        """
        self.total_packets += num_packets
        edge = self._find_edge(graph, src, dst)

        if edge is None or not getattr(edge, "healthy", True):
            self.dropped_packets += num_packets
            return {
                "success": False,
                "packets_sent": num_packets,
                "packets_lost": num_packets,
                "retransmissions": 0,
                "success_rate": 0.0,
            }

        # Corruption from BER: prob = 1 - (1 - BER)^bits_per_packet
        # Assume 4096-byte packets for the model.
        bits_per_packet = 4096 * 8
        ber = getattr(edge, "ber", 0.0)
        ber_prob = 1.0 - (1.0 - ber) ** bits_per_packet
        effective_corruption_prob = max(corruption_prob, ber_prob)

        corrupted = 0
        timeouts = 0

        for _ in range(num_packets):
            if self.rng.random() < effective_corruption_prob:
                corrupted += 1
                self.corrupted_packets += 1
                self.retransmit_count += 1
            elif self.rng.random() < timeout_prob:
                timeouts += 1
                self.retransmit_count += 1

        lost = corrupted + timeouts
        success = num_packets - lost

        return {
            "success": True,
            "packets_sent": num_packets,
            "packets_lost": lost,
            "packets_corrupted": corrupted,
            "packets_timeout": timeouts,
            "retransmissions": lost,
            "success_rate": round(success / num_packets, 6),
        }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_reliability_report(self):
        """Return a summary dict suitable for the competition reliability
        report."""
        fault_counts = {}
        for ft in self.FAULT_TYPES:
            fault_counts[ft] = sum(
                1 for e in self.fault_log if e.fault_type == ft
            )

        retransmit_rate = (
            self.retransmit_count / self.total_packets
            if self.total_packets > 0
            else 0.0
        )

        return {
            "total_faults": len(self.fault_log),
            "faults_by_type": fault_counts,
            "total_packets_sent": self.total_packets,
            "total_retransmissions": self.retransmit_count,
            "retransmission_rate": round(retransmit_rate, 6),
            "corrupted_packets": self.corrupted_packets,
            "dropped_packets": self.dropped_packets,
            "seed": self.seed,
            "target_retransmission_rate": 0.001,   # <=0.1% per contest spec
            "retransmission_ok": retransmit_rate <= 0.001,
        }
