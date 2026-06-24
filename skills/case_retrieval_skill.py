"""Case Retrieval Skill — find similar historical cases."""

from typing import Any, Dict, List


class CaseRetrievalSkill:
    """Search knowledge base for relevant past cases."""

    def __init__(self, knowledge_base: Any = None) -> None:
        self.kb = knowledge_base

    def set_kb(self, kb: Any) -> None:
        self.kb = kb

    def retrieve(
        self, primitive: str, topology: str, nodes: int, top_k: int = 5,
    ) -> Dict[str, Any]:
        if self.kb is None:
            return {"cases": [], "count": 0, "best_practice": None}
        cases = self.kb.retrieve_cases(primitive, topology, nodes, top_k)
        bp = self.kb.get_best_practice(primitive, topology)
        return {
            "cases": cases,
            "count": len(cases),
            "best_practice": bp,
        }
