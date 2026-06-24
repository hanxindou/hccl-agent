"""Knowledge Extraction Skill — generate lessons from run results."""

from typing import Any, Dict


class KnowledgeExtractionSkill:
    """Rule-based knowledge extraction — no LLM required."""

    @staticmethod
    def generate_lesson(result: Dict[str, Any]) -> str:
        algo = result.get("algorithm", "unknown")
        score = result.get("score", 0)
        nodes = result.get("nodes", 0)
        topo = result.get("topology", "unknown")

        if score >= 80:
            perf = "excellent performance"
        elif score >= 50:
            perf = "good performance"
        else:
            perf = "below-average performance"

        scale = "small-scale" if nodes <= 8 else (
            "mid-scale" if nodes <= 64 else "large-scale"
        )

        return (
            f"{algo} shows {perf} on {scale} {topo} "
            f"clusters (score={score:.1f}, nodes={nodes})."
        )
