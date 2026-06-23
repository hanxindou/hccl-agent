"""Explanation Skill — generate human-readable decision traces."""

from typing import Any, Dict, List, Optional


class ExplanationSkill:
    """Produce a structured decision trace explaining WHY the Agent
    chose a particular algorithm."""

    @staticmethod
    def generate_decision_trace(
        topology_analysis: Dict[str, Any],
        candidate_scores: List[Dict[str, Any]],
        selected_algorithm: str,
        selection_reason: str = "",
        reflection_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a full decision trace from raw data.

        Parameters
        ----------
        topology_analysis : dict
            Output of TopologyReasoningSkill.analyze().
        candidate_scores : list[dict]
            Each has "algorithm", "score", "latency", "bandwidth".
        selected_algorithm : str
        selection_reason : str
        reflection_result : dict or None

        Returns
        -------
        dict  with summary, decision_trace, selection_reason,
              rejected_candidates.
        """
        # Sort candidates by score descending for display.
        ranked = sorted(candidate_scores,
                        key=lambda x: x["score"], reverse=True)
        rejected = [c for c in ranked if c["algorithm"] != selected_algorithm]

        trace: List[str] = []

        # Step 1: Topology
        trace.append(
            f"[1] Detected topology: {topology_analysis.get('topology_type', 'Unknown')}  "
            f"Nodes: {topology_analysis.get('node_count', '?')}  "
            f"Dominant Link: {topology_analysis.get('dominant_link', '?')}"
        )

        # Step 2: Candidates
        algo_names = [c["algorithm"] for c in ranked]
        trace.append(f"[2] Generated candidates: {', '.join(algo_names)}")

        # Step 3: Simulation
        sim_parts = [f"{c['algorithm']} Score: {c['score']:.1f}" for c in ranked]
        trace.append("[3] Simulation results:  " + "  |  ".join(sim_parts))

        # Step 4: Cost Evaluation (latency/bandwidth for selected).
        selected = next(
            (c for c in ranked if c["algorithm"] == selected_algorithm), None,
        )
        if selected:
            trace.append(
                f"[4] Cost Evaluation:  latency={selected.get('latency', '?'):.4f}ms  "
                f"bandwidth={selected.get('bandwidth', '?'):.2f}GB/s"
            )

        # Step 5: Selection
        trace.append(f"[5] Selected: {selected_algorithm}")
        if selection_reason:
            trace.append(f"     Reason: {selection_reason}")

        # Step 6: Reflection
        if reflection_result:
            trace.append(
                f"[6] Reflection: status={reflection_result.get('status', '?')}  "
                f"need_replan={reflection_result.get('need_replan', False)}"
            )

        summary = (
            f"Chose {selected_algorithm} over "
            f"{len(rejected)} alternatives based on graph-simulated "
            f"performance on a {topology_analysis.get('topology_type', 'unknown')} "
            f"topology."
        )

        return {
            "summary": summary,
            "decision_trace": trace,
            "selected_algorithm": selected_algorithm,
            "selection_reason": selection_reason,
            "rejected_candidates": [
                {"algorithm": r["algorithm"], "score": r["score"]}
                for r in rejected
            ],
        }
