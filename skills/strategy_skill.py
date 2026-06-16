import math


class StrategySkill:

    def generate(
        self,
        algorithm,
        nodes,
        primitive="AllReduce",
    ):
        """Generate communication steps for *algorithm* under *primitive*.

        Different collective primitives imply different data-flow patterns
        even when using the same underlying topology algorithm.
        """

        if algorithm == "Ring AllReduce":
            return self._generate_ring(nodes, primitive)

        elif algorithm == "Butterfly":
            return self._generate_butterfly(nodes, primitive)

        elif algorithm == "Mesh":
            return self._generate_mesh(nodes, primitive)

        elif algorithm in ("NHR", "Fat-Tree", "PairWise"):
            return self._generate_generic(algorithm, nodes, primitive)

        else:
            return {
                "steps": ["All Nodes Connected"]
            }

    # ------------------------------------------------------------------
    # Ring family
    # ------------------------------------------------------------------

    def _generate_ring(self, nodes, primitive):
        steps = []
        ring_path = [
            f"{i}->{(i + 1) % nodes}" for i in range(nodes)
        ]

        if primitive == "AllReduce":
            steps.append(
                "Phase 1 — ReduceScatter along ring: "
                + ", ".join(ring_path)
            )
            steps.append(
                "Phase 2 — AllGather along ring: "
                + ", ".join(ring_path)
            )
            steps.append(
                f"Total: 2*({nodes}-1) = {2 * (nodes - 1)} steps, "
                f"each rank sends/receives {nodes} chunks of "
                f"size M/{nodes}"
            )

        elif primitive == "AllGather":
            steps.append(
                "Phase 1 — Gather along ring: "
                + ", ".join(ring_path)
            )
            steps.append(
                f"Total: {nodes - 1} steps, "
                f"each rank sends its own chunk and forwards "
                f"received chunks"
            )

        elif primitive == "ReduceScatter":
            steps.append(
                "Phase 1 — Reduce along ring: "
                + ", ".join(ring_path)
            )
            steps.append(
                f"Total: {nodes - 1} steps, "
                f"each rank ends up with 1/{nodes} of the "
                f"fully reduced result"
            )

        else:
            steps = ring_path

        return {"steps": steps, "algorithm": "Ring", "primitive": primitive}

    # ------------------------------------------------------------------
    # Butterfly family
    # ------------------------------------------------------------------

    def _generate_butterfly(self, nodes, primitive):
        """Recursive-doubling / butterfly steps."""
        if nodes < 2:
            return {"steps": ["0"], "algorithm": "Butterfly",
                    "primitive": primitive}

        steps = []
        num_steps = int(math.floor(math.log2(nodes)))

        for step_idx in range(num_steps):
            distance = 1 << step_idx
            step_pairs = []

            for rank in range(nodes):
                partner = rank ^ distance
                if partner < nodes and rank < partner:
                    step_pairs.append(f"{rank}<->{partner}")

            if step_pairs:
                if primitive == "AllReduce":
                    action = "exchange + reduce"
                elif primitive == "AllGather":
                    action = "exchange all accumulated data"
                elif primitive == "ReduceScatter":
                    action = "exchange & reduce, keep owned chunk"
                else:
                    action = "exchange"

                step_label = (
                    f"Step {step_idx + 1} "
                    f"(distance={distance}, {action}): "
                    + ", ".join(step_pairs)
                )
                steps.append(step_label)

        # Handle leftovers.
        power_of_two = 1 << num_steps
        if power_of_two < nodes:
            leftover = list(range(power_of_two, nodes))
            for i, rank in enumerate(leftover):
                partner = i % power_of_two
                steps.append(
                    f"Leftover: {rank}<->{partner}"
                )

        summary = (
            f"Total: log2(N) = {num_steps} steps (recursive doubling)"
        )
        steps.append(summary)

        return {"steps": steps, "algorithm": "Butterfly",
                "primitive": primitive}

    # ------------------------------------------------------------------
    # Mesh family
    # ------------------------------------------------------------------

    def _generate_mesh(self, nodes, primitive):
        steps = []

        if primitive == "AllReduce":
            steps.append(
                f"Step 1: All {nodes} ranks send data to all other "
                f"ranks concurrently ({nodes}*({nodes}-1) = "
                f"{nodes * (nodes - 1)} simultaneous transfers)"
            )
            steps.append(
                "Step 2: Each rank reduces N received chunks locally "
                "(using in-line reduction unit on HCCS)"
            )
        elif primitive == "AllGather":
            steps.append(
                f"Step 1: Each rank sends its chunk to all other "
                f"{nodes - 1} ranks concurrently"
            )
            steps.append(
                "Step 2: Each rank concatenates received chunks"
            )
        elif primitive == "ReduceScatter":
            steps.append(
                f"Step 1: All ranks send chunk-k to rank-k "
                f"simultaneously (each rank receives {nodes} chunks)"
            )
            steps.append(
                "Step 2: Receiving rank reduces its assigned chunk"
            )
        else:
            steps.append("All Nodes Connected")

        steps.append(
            f"Best for: Full Mesh HCCS intra-server ({nodes} NPUs)"
        )

        return {"steps": steps, "algorithm": "Mesh", "primitive": primitive}

    # ------------------------------------------------------------------
    # Generic / other algorithms
    # ------------------------------------------------------------------

    def _generate_generic(self, algorithm, nodes, primitive):
        desc = (
            f"{algorithm} strategy for {primitive} on {nodes} nodes."
        )
        return {
            "steps": [desc],
            "algorithm": algorithm,
            "primitive": primitive,
        }
