"""Optimization Proposal Skill — analyse, recommend, estimate, plan."""

from typing import Any, Dict, List


class OptimizationProposalSkill:
    """Generate a structured optimization proposal from Agent results."""

    @staticmethod
    def generate_proposal(
        current_result: Dict[str, Any],
        candidate_scores: List[Dict[str, Any]],
        topology_analysis: Dict[str, Any],
        hardware_analysis: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Produce a full optimization proposal.

        Parameters
        ----------
        current_result : dict  — from Agent.run() best_result
        candidate_scores : list[dict]  — each has "algorithm", "score"
        topology_analysis : dict  — from TopologyReasoningSkill
        hardware_analysis : dict or None  — from HardwareReasoningSkill

        Returns
        -------
        dict with summary, bottlenecks, recommendations,
             expected_improvements, confidence, migration_plan.
        """
        current_algo = current_result.get("algorithm", "unknown")
        current_score = current_result.get("score", 0.0)

        bottlenecks = OptimizationProposalSkill._detect_bottlenecks(
            current_result, topology_analysis, hardware_analysis,
        )

        recommendations = OptimizationProposalSkill._generate_recommendations(
            current_algo, candidate_scores, bottlenecks,
        )

        improvements = OptimizationProposalSkill._estimate_improvements(
            current_score, candidate_scores, current_algo,
        )

        confidence = OptimizationProposalSkill._compute_confidence(
            current_score, candidate_scores, topology_analysis,
        )

        migration = OptimizationProposalSkill._generate_migration_plan(
            current_algo, recommendations,
        )

        summary = (
            f"Optimization proposal for {current_algo} "
            f"(current score={current_score:.1f}): "
            f"{len(recommendations)} recommendation(s), "
            f"confidence={confidence:.2f}."
        )

        return {
            "summary": summary,
            "detected_bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "expected_improvements": improvements,
            "confidence": confidence,
            "migration_plan": migration,
        }

    # ------------------------------------------------------------------
    # Bottleneck detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_bottlenecks(
        result: Dict[str, Any],
        topo: Dict[str, Any],
        hw: Dict[str, Any] | None,
    ) -> List[Dict[str, str]]:
        bottlenecks: List[Dict[str, str]] = []

        latency = result.get("latency", 0.0)
        bandwidth = result.get("bandwidth", 0.0)
        score = result.get("score", 0.0)

        if latency > 1.0:
            bottlenecks.append({
                "type": "Latency",
                "description": f"High latency ({latency:.4f} ms) — consider lower-step-count algorithm",
            })
        if bandwidth < 5.0:
            bottlenecks.append({
                "type": "Bandwidth",
                "description": f"Low bandwidth ({bandwidth:.2f} GB/s) — link contention or topology limitation",
            })
        if score < 50 and latency <= 1.0:
            bottlenecks.append({
                "type": "Topology",
                "description": "Score below threshold despite moderate latency — topology mismatch",
            })
        if hw:
            pressure = hw.get("resources", {}).get("resource_pressure", 0)
            if pressure > 0.5:
                bottlenecks.append({
                    "type": "Hardware",
                    "description": f"Resource pressure ({pressure:.2f}) — consider hardware-aware placement",
                })
        if result.get("reliability", {}).get("health", {}).get("error_rate", 0) > 0:
            bottlenecks.append({
                "type": "Reliability",
                "description": "Link failures detected — reliability impact on performance",
            })

        if not bottlenecks:
            bottlenecks.append({
                "type": "None",
                "description": "No significant bottlenecks detected.",
            })
        return bottlenecks

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_recommendations(
        current_algo: str,
        candidates: List[Dict[str, Any]],
        bottlenecks: List[Dict[str, str]],
    ) -> List[str]:
        recs: List[str] = []

        # If there's a better-scoring algorithm, recommend switching.
        ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
        if ranked and ranked[0]["algorithm"] != current_algo:
            recs.append(
                f"Switch {current_algo} → {ranked[0]['algorithm']} "
                f"(score gain: +{ranked[0]['score'] - candidates[0].get('score', 0):.1f} pts)"
            )

        for b in bottlenecks:
            t = b["type"]
            if t == "Latency":
                recs.append("Increase pipeline depth to hide latency")
            elif t == "Bandwidth":
                recs.append("Tune chunk size to improve bandwidth utilisation")
            elif t == "Topology":
                recs.append("Re-evaluate topology mode for algorithm placement")
            elif t == "Hardware":
                recs.append("Improve NIC locality / NUMA affinity")
            elif t == "Reliability":
                recs.append("Enable failover routing for reliability")

        if not recs:
            recs.append("Current configuration is optimal — no changes recommended.")
        return recs

    # ------------------------------------------------------------------
    # Improvement estimation (deterministic)
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_improvements(
        current_score: float,
        candidates: List[Dict[str, Any]],
        current_algo: str,
    ) -> Dict[str, float]:
        ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
        best_score = ranked[0]["score"] if ranked else current_score

        if current_score > 0:
            score_gain = (best_score - current_score) / current_score * 100.0
        else:
            score_gain = 0.0

        # Heuristic: latency and bandwidth improvements track score gain.
        lat_reduction = max(0.0, score_gain * 0.8)
        bw_gain = max(0.0, score_gain * 0.5)

        return {
            "latency_reduction_pct": round(lat_reduction, 1),
            "bandwidth_gain_pct": round(bw_gain, 1),
            "score_gain_pct": round(score_gain, 1),
        }

    # ------------------------------------------------------------------
    # Confidence (deterministic)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_confidence(
        current_score: float,
        candidates: List[Dict[str, Any]],
        topo: Dict[str, Any],
    ) -> float:
        ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
        gap = ranked[0]["score"] - current_score if ranked else 0.0

        # Larger gap → higher confidence in recommendation.
        base = 0.5 + min(gap / 50.0, 0.4)

        # Topology stability bonus.
        nodes = topo.get("node_count", 8)
        if nodes <= 8:
            base += 0.1

        return round(min(base, 1.0), 2)

    # ------------------------------------------------------------------
    # Migration plan
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_migration_plan(
        current_algo: str,
        recommendations: List[str],
    ) -> List[str]:
        plan = ["1. Backup current configuration"]
        step = 2
        for r in recommendations:
            if "Switch" in r:
                plan.append(f"{step}. Apply algorithm change per recommendation")
                step += 1
        plan.append(f"{step}. Deploy updated communication strategy")
        step += 1
        plan.append(f"{step}. Run validation benchmark")
        step += 1
        plan.append(f"{step}. Monitor latency and bandwidth metrics")
        step += 1
        plan.append(f"{step}. Confirm improvement and finalize")
        return plan
