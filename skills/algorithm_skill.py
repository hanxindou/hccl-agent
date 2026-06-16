class AlgorithmSkill:

    # Message-size thresholds in MB (the contest covers <=64 KB through >=1 GB).
    SMALL_THRESHOLD_MB = 0.0625   # 64 KB
    MEDIUM_THRESHOLD_MB = 1       # 1 MB
    LARGE_THRESHOLD_MB = 512      # 512 MB
    HUGE_THRESHOLD_MB = 1024      # 1 GB

    def choose_algorithms(
        self,
        nodes,
        message_size_mb,
        primitive="AllReduce"
    ):
        """Return candidate algorithms considering node count, message size, and primitive.

        Small data (<=64 KB):
            Butterfly / recursive-doubling for low latency; PairWise for very small payloads.
        Medium data (64 KB – 512 MB):
            Ring AllReduce balances bandwidth and latency;
            NHR (non-uniform ring) when node count varies widely.
        Large data (512 MB – 1 GB):
            Mesh for full-interconnect single-machine; Ring for cross-node.
        Huge data (>=1 GB):
            Fat-Tree hierarchical for multi-machine; Mesh for single-machine.
        """

        candidates = []

        if message_size_mb <= self.SMALL_THRESHOLD_MB:
            # Tiny messages — latency-bound.
            candidates.extend(["Butterfly", "PairWise"])

        elif message_size_mb <= self.MEDIUM_THRESHOLD_MB:
            # Small messages — still latency-sensitive, Ring becomes viable.
            candidates.extend(["Butterfly", "PairWise", "Ring AllReduce"])

        elif message_size_mb <= self.LARGE_THRESHOLD_MB:
            # Medium-to-large — bandwidth-bound, Ring and Mesh are primary.
            if nodes <= 8:
                candidates.extend(["Ring AllReduce", "Mesh", "Butterfly"])
            elif nodes <= 64:
                candidates.extend(["Ring AllReduce", "NHR"])
            else:
                candidates.extend(["Ring AllReduce", "Fat-Tree"])

        elif message_size_mb <= self.HUGE_THRESHOLD_MB:
            # Large data — Mesh for single-machine, hierarchical for multi-machine.
            if nodes <= 8:
                candidates.extend(["Mesh", "Ring AllReduce"])
            else:
                candidates.extend(["Fat-Tree", "Ring AllReduce"])

        else:
            # Huge data (>=1 GB) — hierarchical / Fat-Tree preferred.
            if nodes <= 8:
                candidates.extend(["Mesh"])
            else:
                candidates.extend(["Fat-Tree"])

        # Primitive-specific adjustments.
        if primitive == "AllGather":
            # AllGather benefits from recursive-doubling and Ring.
            if "Butterfly" not in candidates:
                candidates.append("Butterfly")
            if "Ring AllReduce" not in candidates:
                candidates.append("Ring AllReduce")

        elif primitive == "ReduceScatter":
            # ReduceScatter works well with Ring and Mesh chunked approaches.
            if "Ring AllReduce" not in candidates:
                candidates.append("Ring AllReduce")

        # Deduplicate while preserving order.
        seen = set()
        unique = []
        for algo in candidates:
            if algo not in seen:
                seen.add(algo)
                unique.append(algo)

        return unique
