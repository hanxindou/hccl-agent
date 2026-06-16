from skills.performance_model import PerformanceModel


# Algorithm bandwidth efficiency relative to raw link capacity.
ALGORITHM_EFFICIENCY = {
    "Ring AllReduce": 0.90,
    "Butterfly":      0.85,
    "Mesh":           0.88,
    "NHR":            0.93,
    "Fat-Tree":       0.95,
    "PairWise":       0.82,
}

# Mesh on Full Mesh: N-1 simultaneous sends per node → real wall-clock
# grows faster than a single link-hop.  Model as effective steps.
MESH_EFFECTIVE_STEPS_COEFF = 0.15   # added to step count per node

# Bandwidth contention for algorithms that share links concurrently.
# Ring / Butterfly / NHR serialise traffic → no contention.
# Mesh → all N-1 peers share each link → bandwidth drops.
BW_CONTENTION_COEFF = {
    "Mesh":     0.12,   # each link shared by N-1 peers
    "Fat-Tree": 0.04,   # hierarchical — only intra-rack is full mesh
}


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
        import math

        link_bw_gbps = (bandwidth_gbps
                        if bandwidth_gbps is not None
                        else 100.0)
        link_lat_us = ((latency_ms * 1000.0)
                       if latency_ms is not None
                       else 2.0)

        algo_eff = ALGORITHM_EFFICIENCY.get(algorithm, 0.85)

        # ---- step count ----
        if algorithm == "Ring AllReduce":
            steps = 2 * (nodes - 1)
        elif algorithm == "Butterfly":
            steps = int(math.ceil(math.log2(max(nodes, 1))))
        elif algorithm == "PairWise":
            steps = nodes - 1
        elif algorithm == "NHR":
            steps = 2 * (nodes - 1)
        elif algorithm == "Mesh":
            # 1 logical round, but wall-clock grows with N due to queue depth.
            steps = 1 + nodes * MESH_EFFECTIVE_STEPS_COEFF
        elif algorithm == "Fat-Tree":
            steps = int(2 * math.ceil(math.log2(max(nodes, 1))))
        else:
            steps = nodes

        # ---- latency (ms) ----
        # Topology factor.
        if topology == "Full Mesh":
            topo_lat_factor = 1.0
        elif topology == "Ring":
            topo_lat_factor = 1.0
        elif topology == "Fat Tree":
            topo_lat_factor = 1.15
        else:
            topo_lat_factor = 1.2

        # Algorithm-specific latency contention.
        # Mesh: N-1 simultaneous sends per node cause NIC queue depth.
        algo_lat_contention = 1.0
        if algorithm == "Mesh":
            algo_lat_contention = 1.0 + nodes * 0.15
        elif algorithm == "Fat-Tree":
            algo_lat_contention = 1.0 + nodes * 0.04

        # Primitive factor.
        if primitive == "AllGather":
            prim_factor = 0.9
        elif primitive == "ReduceScatter":
            prim_factor = 0.95
        else:
            prim_factor = 1.0

        latency_us = (steps * link_lat_us * topo_lat_factor
                      * prim_factor * algo_lat_contention)
        latency_ms_result = latency_us / 1000.0

        # ---- bandwidth (GB/s) ----
        bw_contention = 1.0
        bw_coeff = BW_CONTENTION_COEFF.get(algorithm, 0.0)
        if bw_coeff > 0:
            bw_contention = 1.0 / (1.0 + (nodes - 1) * bw_coeff)

        effective_bw_gbps = (link_bw_gbps * algo_eff
                             * prim_factor * bw_contention)
        bandwidth_gb_s = effective_bw_gbps / 8.0

        # ---- score (0–100) ----
        theoretical_max_gb_s = link_bw_gbps / 8.0
        score = self.model.calculate_score(
            latency_ms_result,
            bandwidth_gb_s,
            theoretical_max_bandwidth_gb_s=theoretical_max_gb_s,
        )

        return {
            "latency": round(latency_ms_result, 4),
            "bandwidth": round(bandwidth_gb_s, 2),
            "score": score,
        }
