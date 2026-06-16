"""Structured experiment logger for reproducible Agent runs.

Each Agent invocation produces a JSON log entry saved under logs/ so that
judges can trace every algorithm selection, simulation result, and ranking.
"""

import json
import os
import time
from datetime import datetime


class ExperimentLogger:

    def __init__(self, log_dir=None):
        if log_dir is None:
            log_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "logs",
            )
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        self.run_log_path = os.path.join(
            self.log_dir, "runs.jsonl"
        )
        self.summary_path = os.path.join(
            self.log_dir, "summary.json"
        )

    def log_run(self, output):
        """Persist one Agent run as a JSON-lines record.

        Parameters
        ----------
        output : dict
            The full return value of HCCLAgent.run().
        """
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "unix_time": time.time(),
            "nodes": output["cluster"]["nodes"],
            "message_size_mb": output.get("message_size_mb"),
            "primitive": output["primitive"],
            "topology": output["topology"],
            "candidate_algorithms": output["candidate_algorithms"],
            "best_algorithm": output["best_algorithm"],
            "best_result": output["best_result"],
            "ranking": output["ranking"],
        }

        with open(self.run_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        self._update_summary()

    def _update_summary(self):
        """Regenerate the summary file with aggregate stats."""
        runs = []
        if os.path.exists(self.run_log_path):
            with open(self.run_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            runs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

        if not runs:
            if os.path.exists(self.summary_path):
                os.remove(self.summary_path)
            return

        # Aggregate: count runs per primitive and best-algorithm wins.
        primitives = {}
        algorithms = {}
        topologies = {}

        for r in runs:
            p = r.get("primitive", "unknown")
            primitives[p] = primitives.get(p, 0) + 1

            a = r.get("best_algorithm", "unknown")
            algorithms[a] = algorithms.get(a, 0) + 1

            t = r.get("topology", "unknown")
            topologies[t] = topologies.get(t, 0) + 1

        summary = {
            "total_runs": len(runs),
            "last_run_at": runs[-1]["timestamp"],
            "runs_by_primitive": primitives,
            "wins_by_algorithm": algorithms,
            "runs_by_topology": topologies,
        }

        with open(self.summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    def get_summary(self):
        """Return the current summary dict, or empty dict if none exists."""
        if not os.path.exists(self.summary_path):
            return {}
        with open(self.summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
