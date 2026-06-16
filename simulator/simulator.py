from skills.performance_model import (
    PerformanceModel
)


class Simulator:

    def __init__(self):
        self.model = PerformanceModel()

    def evaluate(
        self,
        algorithm,
        topology,
        nodes,
        message_size_mb,
        primitive="AllReduce",
        bandwidth_gbps=None,
        latency_ms=None,
    ):
        """Estimate latency, bandwidth, and score for a candidate algorithm.

        Parameters
        ----------
        algorithm : str
            Algorithm name (Ring AllReduce, Butterfly, Mesh, etc.).
        topology : str
            Cluster topology (Full Mesh, Ring, Fat Tree, etc.).
        nodes : int
            Number of NPU devices.
        message_size_mb : float
            Message size in MB.
        primitive : str
            Collective primitive: AllReduce, AllGather, or ReduceScatter.
        bandwidth_gbps : float or None
            Per-link bandwidth in Gbps from cluster config.
        latency_ms : float or None
            Per-link base latency in ms from cluster config.

        Returns
        -------
        dict with keys: latency (ms), bandwidth (GB/s), score.
        """

        # Use config values when provided, otherwise fall back to defaults.
        link_bw_gbps = bandwidth_gbps if bandwidth_gbps is not None else 100.0
        link_lat_us = (
            latency_ms * 1000.0 if latency_ms is not None else 2000.0
        )  # us

        # Convert message size to bytes for model calculations.
        message_bytes = message_size_mb * 1024.0 * 1024.0

        # ---- algorithm-specific step count ----
        if algorithm == "Ring AllReduce":
            # 2*(N-1) steps, each sending M/N bytes.
            steps = 2 * (nodes - 1)
            data_per_step = message_bytes / nodes
        elif algorithm == "Butterfly":
            # log2(N) steps for recursive doubling.
            import math
            steps = int(math.ceil(math.log2(max(nodes, 1))))
            data_per_step = message_bytes
        elif algorithm == "PairWise":
            # N-1 steps, each sends full message to one partner.
            steps = nodes - 1
            data_per_step = message_bytes
        elif algorithm == "NHR":
            # Non-uniform ring — roughly 2*(N-1) with varying chunk sizes.
            steps = 2 * (nodes - 1)
            data_per_step = message_bytes / nodes
        elif algorithm == "Mesh":
            # Full pairwise exchange in O(1) concurrent steps.
            steps = 1
            data_per_step = message_bytes
        elif algorithm == "Fat-Tree":
            # log_k(N) up + log_k(N) down.
            import math
            steps = int(2 * math.ceil(math.log2(max(nodes, 1))))
            data_per_step = message_bytes
        else:
            # Generic fallback.
            steps = nodes
            data_per_step = message_bytes

        # ---- topology factor ----
        if topology == "Full Mesh":
            link_factor = 1.0
        elif topology == "Ring":
            link_factor = 1.0
        elif topology == "Fat Tree":
            # Multi-level switches add overhead.
            link_factor = 1.15
        else:
            link_factor = 1.2

        # ---- primitive overhead ----
        if primitive == "AllReduce":
            primitive_factor = 1.0
        elif primitive == "AllGather":
            # AllGather sends (N-1)/N of total data without reduction.
            primitive_factor = 0.9
        elif primitive == "ReduceScatter":
            # ReduceScatter sends (N-1)/N data chunks.
            primitive_factor = 0.95
        else:
            primitive_factor = 1.0

        # ---- latency calculation (ms) ----
        # Total latency = steps * per-link-latency * link_factor * primitive_factor
        latency_us = (
            steps * link_lat_us * link_factor * primitive_factor
        )
        latency_ms = latency_us / 1000.0

        # ---- bandwidth calculation (GB/s) ----
        # Effective bandwidth = link_bw * link_factor adjusted by algorithm
        # efficiency and primitive overhead.
        base_bandwidth_gbps = link_bw_gbps * link_factor
        effective_bandwidth_gbps = (
            base_bandwidth_gbps * primitive_factor
        )
        bandwidth_gb_s = effective_bandwidth_gbps / 8.0  # Gbps -> GB/s

        # ---- score ----
        score = self.model.calculate_score(latency_ms, bandwidth_gb_s)

        return {
            "latency": round(latency_ms, 4),
            "bandwidth": round(bandwidth_gb_s, 2),
            "score": score,
        }
