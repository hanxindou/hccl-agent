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
        graph, metadata = self._build_graph_for_evaluate(
            topology, nodes, bandwidth_gbps, latency_ms,
        )
        result = self.simulate_with_graph(
            graph=graph,
            primitive=primitive,
            algorithm=algorithm,
            message_size_mb=message_size_mb,
        )
        result["topology"] = topology
        result["topology_metadata"] = metadata
        return result

    def simulate_collective(
        self,
        primitive,
        algorithm,
        topology,
        nodes,
        message_size_mb=128.0,
    ):
        """Unified entry point for HCCL collective simulation.

        Delegates to ``evaluate()`` so all existing modelling
        (algorithm efficiency, contention, etc.) is reused.

        Parameters
        ----------
        primitive : str
            AllReduce / AllGather / ReduceScatter.
        algorithm : str
            e.g. "Ring AllReduce".
        topology : str
        nodes : int
        message_size_mb : float

        Returns
        -------
        dict  with keys latency, bandwidth, score.
        """
        return self.evaluate(
            algorithm=algorithm,
            topology=topology,
            nodes=nodes,
            message_size_mb=message_size_mb,
            primitive=primitive,
        )

    def simulate_with_graph(
        self,
        graph,
        primitive,
        algorithm,
        message_size_mb=128.0,
        profile=None,
    ):
        """Graph-based collective simulation.

        Uses CostModelEngine to traverse the communication graph
        and compute end-to-end latency and bandwidth.

        Parameters
        ----------
        graph : CommunicationGraph
            From topology/graph_builder.py.
        primitive : str
        algorithm : str
        message_size_mb : float
        profile : HardwareProfile or None

        Returns
        -------
        dict  with latency_ms, bandwidth_gbps, algorithm, primitive, nodes.
        """
        from cost_model.engine import CostModelEngine
        engine = CostModelEngine()

        if algorithm in ("Ring AllReduce", "NHR"):
            raw = engine.estimate_allreduce_ring(
                graph, message_size_mb, algorithm, primitive,
            )
        elif algorithm in ("Butterfly", "Fat-Tree", "Mesh"):
            raw = engine.estimate_allreduce_tree(
                graph, message_size_mb, algorithm, primitive,
            )
        else:
            raw = engine.estimate_generic(
                graph, message_size_mb, algorithm, primitive,
            )

        # Convert to the same format as evaluate() for downstream consumption.
        bw_gb_s = raw["bandwidth_gbps"] / 8.0
        score = self.model.calculate_score(
            raw["latency_ms"], bw_gb_s,
            theoretical_max_bandwidth_gb_s=bw_gb_s if bw_gb_s > 0 else 12.5,
        )

        return {
            "latency": raw["latency_ms"],
            "bandwidth": round(bw_gb_s, 2),
            "score": score,
            "algorithm": algorithm,
            "primitive": primitive,
            "topology": "graph",
            "model_type": raw.get("model_type", "ANALYTICAL_MODEL"),
            "communication_steps": raw.get("communication_steps", 0),
            "transferred_bytes": raw.get("transferred_bytes", 0),
            "contention_penalty_ms": raw.get("contention_penalty_ms", 0.0),
            "link_types": raw.get("link_types", []),
            "edge_count": raw.get("edge_count", 0),
            "parameter_sources": raw.get("parameter_sources", {}),
            "model_assumptions": raw.get("model_assumptions", []),
        }

    def simulate_with_failures(
        self,
        graph,
        primitive,
        algorithm,
        message_size_mb=128.0,
        link_failure_rate=0.0,
        node_failure_rate=0.0,
        max_retry=3,
        seed=None,
    ):
        """Simulate collective communication with reliability mechanisms.

        Parameters
        ----------
        graph : CommunicationGraph
        primitive : str
        algorithm : str
        message_size_mb : float
        link_failure_rate : float  — probability per link
        node_failure_rate : float  — probability per node
        max_retry : int
        seed : int or None

        Returns
        -------
        dict  with base_result + reliability section.
        """
        from simulator.health_monitor import HealthMonitor
        from simulator.retry_policy import RetryPolicy
        from simulator.failover_engine import FailoverEngine

        monitor = HealthMonitor(seed=seed)
        monitor.inject_failures(
            graph.num_nodes, link_failure_rate, node_failure_rate,
        )

        health = monitor.evaluate_cluster_health(graph)

        retry = RetryPolicy(max_retry=max_retry)
        failover = FailoverEngine()

        def _run():
            return self.simulate_with_graph(
                graph, primitive, algorithm, message_size_mb,
            )

        retry_result = retry.execute_with_retry(_run)
        base = retry_result["result"] or {
            "latency": 0.0, "bandwidth": 0.0, "score": 0.0,
            "algorithm": algorithm, "primitive": primitive,
        }

        # Test a failover on a random edge.
        fo_result = None
        if graph.num_nodes >= 2:
            fo_result = failover.reroute(
                graph, 0, graph.num_nodes - 1, monitor=monitor,
            )

        base["reliability"] = {
            "health": health,
            "retry": {
                "success": retry_result["success"],
                "attempts": retry_result["attempts"],
            },
            "failover": (
                {"triggered": fo_result["failover_triggered"],
                 "found": fo_result["found"],
                 "hops": fo_result["hops"]}
                if fo_result else {"triggered": False, "found": True, "hops": 1}
            ),
        }
        return base

    def _build_graph_for_evaluate(
        self,
        topology,
        nodes,
        bandwidth_gbps=None,
        latency_ms=None,
    ):
        from hardware.profile import HardwareProfile
        from topology.graph_builder import TopologyGraphBuilder

        profile = HardwareProfile.tier_medium()
        if bandwidth_gbps is not None or latency_ms is not None:
            links = {}
            for link_type, values in profile.link_types.items():
                links[link_type] = dict(values)
                if bandwidth_gbps is not None:
                    links[link_type]["bandwidth_gbps"] = float(bandwidth_gbps)
                if latency_ms is not None:
                    links[link_type]["latency_ms"] = float(latency_ms)
            profile = HardwareProfile(
                device_type="evaluate-override",
                link_types=links,
            )

        normalized = (topology or "").lower().replace("_", " ")
        if normalized in {"full mesh", "single node", "hccs"} and nodes <= 8:
            mode = "SINGLE_NODE"
        elif normalized in {"mixed", "heterogeneous", "pcie"}:
            mode = "HETEROGENEOUS"
        else:
            mode = "MULTI_NODE" if nodes > 8 else "SINGLE_NODE"

        graph, metadata = TopologyGraphBuilder.build(
            nodes,
            num_gpus_per_node=8,
            profile=profile,
            mode=mode,
        )
        metadata["main_topology_model"] = "topology.graph_builder.CommunicationGraph"
        metadata["requested_topology"] = topology
        return graph, metadata
