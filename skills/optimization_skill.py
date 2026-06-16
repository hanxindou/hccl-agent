class OptimizationSkill:

    def optimize(
        self,
        simulator,
        cluster_info,
        candidate_algorithms,
        nodes,
        message_size,
        primitive="AllReduce",
    ):
        """Evaluate each candidate algorithm and return the best one.

        Parameters
        ----------
        simulator : Simulator
        cluster_info : dict
            Cluster configuration with bandwidth_gbps, latency_ms, topology, etc.
        candidate_algorithms : list[str]
        nodes : int
        message_size : float
        primitive : str

        Returns
        -------
        (best_algorithm, best_result, ranking)
        """

        best_algorithm = None
        best_result = None
        ranking = []

        # Extract config values for the simulator.
        bandwidth_gbps = cluster_info.get("bandwidth_gbps")
        latency_ms = cluster_info.get("latency_ms")
        topology = cluster_info.get("topology", "Unknown")

        for algorithm in candidate_algorithms:
            result = simulator.evaluate(
                algorithm,
                topology,
                nodes,
                message_size,
                primitive=primitive,
                bandwidth_gbps=bandwidth_gbps,
                latency_ms=latency_ms,
            )

            if (
                best_result is None
                or result["score"] > best_result["score"]
            ):
                best_algorithm = algorithm
                best_result = result

            ranking.append(
                (algorithm, result["score"])
            )

        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return (
            best_algorithm,
            best_result,
            ranking,
        )
