"""Knowledge Base — case accumulation, retrieval, best-practice export."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List


class KnowledgeBase:
    """Persistent store of structured communication cases with lessons learned."""

    def __init__(self, path: str | None = None) -> None:
        if path is None:
            path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "logs", "knowledge_base.jsonl",
            )
        self.path = os.path.normpath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def add_case(self, case: Dict[str, Any]) -> None:
        """Append a case (with timestamp)."""
        case["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    def load_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        cases: List[Dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        cases.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return cases

    def get_best_practice(
        self, primitive: str | None = None, topology: str | None = None,
    ) -> Dict[str, Any] | None:
        """Return the highest-scoring case matching filters."""
        cases = self.load_all()
        filtered = [
            c for c in cases
            if (primitive is None or c.get("primitive") == primitive)
            and (topology is None or c.get("topology") == topology)
        ]
        if not filtered:
            return None
        return max(filtered, key=lambda c: c.get("score", 0.0))

    def retrieve_cases(
        self,
        primitive: str,
        topology: str,
        nodes: int,
        top_k: int = 10,
        node_tolerance: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """Find cases matching primitive + topology with node-count tolerance."""
        cases = self.load_all()
        scored: List[tuple] = []
        lo = nodes * (1.0 - node_tolerance)
        hi = nodes * (1.0 + node_tolerance)
        for c in cases:
            if c.get("primitive") != primitive:
                continue
            if c.get("topology") != topology:
                continue
            cn = c.get("nodes", 0)
            if lo <= cn <= hi:
                proximity = abs(nodes - cn) / max(nodes, cn)
                scored.append((proximity, c))
        scored.sort(key=lambda x: x[0])
        return [c for _, c in scored[:top_k]]

    def export_summary(self) -> Dict[str, Any]:
        cases = self.load_all()
        if not cases:
            return {"total_cases": 0, "by_primitive": {}, "best_score": 0}
        by_prim: Dict[str, int] = {}
        best = cases[0]
        for c in cases:
            p = c.get("primitive", "unknown")
            by_prim[p] = by_prim.get(p, 0) + 1
            if c.get("score", 0) > best.get("score", 0):
                best = c
        return {
            "total_cases": len(cases),
            "by_primitive": by_prim,
            "best_score": best.get("score", 0),
            "best_algorithm": best.get("algorithm", "N/A"),
        }
