"""Experience Store — persist and query historical Agent runs.

Saves each run to logs/experience.jsonl and provides lookup for
similar past scenarios so the LLM can factor historical performance
into its decisions.
"""

import json
import os
from datetime import datetime


class ExperienceStore:

    def __init__(self, path=None):
        if path is None:
            path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "logs", "experience.jsonl",
            )
        self.path = os.path.normpath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, record):
        """Append a single experience record (JSON line)."""
        record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_all(self):
        """Return every record stored so far."""
        if not os.path.exists(self.path):
            return []
        records = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query_similar(self, nodes, topology, primitive,
                      nodes_tolerance=0.2):
        """Return records whose scenario is close to the given parameters.

        A record is considered similar when the topology and primitive
        match exactly and the node count is within *nodes_tolerance*
        fractional distance.
        """
        all_records = self.load_all()
        lo = nodes * (1.0 - nodes_tolerance)
        hi = nodes * (1.0 + nodes_tolerance)
        return [
            r for r in all_records
            if r.get("topology") == topology
            and r.get("primitive") == primitive
            and lo <= r.get("nodes", 0) <= hi
        ]

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @staticmethod
    def aggregate_statistics(records):
        """Group records by algorithm and compute per-algorithm stats."""
        groups = {}
        for r in records:
            algo = r.get("algorithm", "unknown")
            if algo not in groups:
                groups[algo] = {"count": 0, "total_score": 0.0,
                                "total_time_ms": 0.0}
            groups[algo]["count"] += 1
            groups[algo]["total_score"] += r.get("score", 0.0)
            groups[algo]["total_time_ms"] += r.get("execution_time_ms", 0.0)

        stats = {}
        for algo, g in groups.items():
            n = g["count"]
            stats[algo] = {
                "count": n,
                "avg_score": round(g["total_score"] / n, 2),
                "avg_time_ms": round(g["total_time_ms"] / n, 4),
            }
        return stats
