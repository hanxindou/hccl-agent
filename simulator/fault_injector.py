"""Fault injection for communication reliability simulation.

Models link failures, timeouts, data corruption, and congestion events so
the Agent can evaluate algorithm robustness under adverse conditions — a
key requirement for the competition's reliability report.
"""

import random
import time


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
        self.fault_log = []            # list of FaultEvent
        self.retransmit_count = 0
        self.total_packets = 0
        self.corrupted_packets = 0

    # ------------------------------------------------------------------
    # Fault generation
    # ------------------------------------------------------------------

    def inject_link_failure(self, graph, src, dst, duration_ms=100):
        """Bring down a specific link for *duration_ms*."""
        graph.set_link_health(src, dst, False)
        event = FaultEvent(
            "link_down",
            (src, dst),
            time.time(),
            duration_ms,
            f"Link {src}->{dst} down for {duration_ms}ms",
        )
        self.fault_log.append(event)
        return event

    def inject_random_link_failure(self, graph, duration_ms=100):
        """Randomly pick one edge and bring it down."""
        if not graph.edges:
            return None
        edge_key = self.rng.choice(list(graph.edges.keys()))
        return self.inject_link_failure(
            graph, edge_key[0], edge_key[1], duration_ms
        )

    def inject_timeout(self, graph, src, dst, timeout_ms=500):
        """Simulate a timeout on a specific link."""
        event = FaultEvent(
            "timeout",
            (src, dst),
            time.time(),
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
            time.time(),
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
            time.time(),
            duration_ms,
            f"Congestion on {src}->{dst} "
            f"(BW reduced {bandwidth_reduction*100:.0f}%)",
        )
        self.fault_log.append(event)

        # Temporarily reduce bandwidth on the edge.
        key = (src, dst)
        if key in graph.edges:
            edge = graph.edges[key]
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
        graph.set_link_health(src, dst, True)

    def recover_all_links(self, graph):
        """Restore all links in the graph to healthy."""
        for key in graph.edges:
            graph.edges[key].healthy = True

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
        key = (src, dst)
        edge = graph.edges.get(key)

        if edge is None or not edge.healthy:
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
        ber_prob = 1.0 - (1.0 - edge.ber) ** bits_per_packet
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
            "target_retransmission_rate": 0.001,   # <=0.1% per contest spec
            "retransmission_ok": retransmit_rate <= 0.001,
        }
