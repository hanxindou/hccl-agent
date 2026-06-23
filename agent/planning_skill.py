"""Planning Skill — decompose a high-level optimisation goal into
ordered, executable sub-tasks."""


class PlanningSkill:

    _PRIMITIVE_CANDIDATES = {
        "AllReduce":     ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"],
        "AllGather":     ["Mesh", "Butterfly", "Ring AllReduce"],
        "ReduceScatter": ["Ring AllReduce", "NHR", "Fat-Tree"],
        "Broadcast":     ["Fat-Tree", "Ring AllReduce"],
    }

    @staticmethod
    def create_plan(nodes, message_size, primitive,
                    topology_graph=None, hardware_profile=None):
        """Produce a multi-step execution plan for the given scenario.

        Parameters
        ----------
        nodes : int
        message_size : float  (MB)
        primitive : str       AllReduce / AllGather / ReduceScatter
        topology_graph : CommunicationGraph or None
        hardware_profile : HardwareProfile or None

        Returns
        -------
        list[dict]   each entry: {"step": int, "task": str}
        """
        candidates = PlanningSkill._PRIMITIVE_CANDIDATES.get(
            primitive, ["Ring AllReduce"],
        )

        plan = [
            {"step": 1, "task": "Analyze topology",
             "candidate_algorithms": candidates},
            {"step": 2, "task": "Simulate candidate algorithms on topology graph"},
            {"step": 3, "task": "Rank algorithms by graph-based scores"},
            {"step": 4, "task": "Select best algorithm via topology-aware selector",
             "primitive": primitive},
            {"step": 5, "task": f"Execute {primitive} via HCCL API (graph mode)"},
            {"step": 6, "task": "Evaluate execution performance"},
            {"step": 7, "task": "Reflect on result and replan if needed"},
            {"step": 8, "task": "Record experience for future learning"},
        ]

        for i, item in enumerate(plan):
            item["step"] = i + 1

        return plan
