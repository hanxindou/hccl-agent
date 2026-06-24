"""Knowledge Report Skill — summarise retrieved knowledge context."""

from typing import Any, Dict


class KnowledgeReportSkill:
    """Format knowledge retrieval results for reporting."""

    @staticmethod
    def generate_summary(knowledge_context: Dict[str, Any]) -> Dict[str, Any]:
        cases = knowledge_context.get("cases", [])
        bp = knowledge_context.get("best_practice")

        return {
            "similar_cases": len(cases),
            "best_practice": (
                f"{bp['algorithm']} (score={bp['score']:.1f})" if bp else "N/A"
            ),
            "retrieval_confidence": min(1.0, len(cases) / 10.0),
        }
