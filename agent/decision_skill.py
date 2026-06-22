"""Decision Skill — LLM-based algorithm selection.

Upgrades the LLM from commentator to decision-maker.
Falls back to max-score selection when the API is unavailable.
"""

from agent.llm_client import LLMClient

_DECISION_PROMPT = """\
You are an expert in collective communication optimization.

Scenario:
  Nodes: {nodes}
  Message Size: {message_size} MB
  Topology: {topology}
  Primitive: {primitive}

Candidates with simulated performance:

{candidates_text}

Historical Performance (from past runs in similar scenarios):
{historical_text}

Choose ONE algorithm.  Reply EXACTLY in this format:

Algorithm: <name>
Reason: <one-sentence technical reason>
"""


class DecisionSkill:

    def __init__(self, client=None):
        self.client = client or LLMClient()

    def choose_algorithm(self, nodes, message_size, topology,
                         primitive, candidate_results,
                         historical_stats=None):
        """Ask the LLM to pick the best algorithm.

        Parameters
        ----------
        nodes, message_size, topology, primitive : same as Agent.run()
        candidate_results : list[dict]
        historical_stats : dict or None
            {"Ring AllReduce": {"count": 5, "avg_score": 84.3, ...}, ...}

        Returns
        -------
        dict or None
        """
        candidate_text = "\n".join(
            f"  {r['algorithm']}\n"
            f"    Score: {r['score']:.2f}  "
            f"Latency: {r['latency']:.4f} ms  "
            f"Bandwidth: {r['bandwidth']:.2f} GB/s"
            for r in candidate_results
        )

        if historical_stats:
            historical_text = "\n".join(
                f"  {algo}:  runs={s['count']}, "
                f"avg_score={s['avg_score']}, "
                f"avg_time={s['avg_time_ms']}ms"
                for algo, s in sorted(historical_stats.items())
            )
        else:
            historical_text = "  (no historical data yet)"

        prompt = _DECISION_PROMPT.format(
            nodes=nodes,
            message_size=message_size,
            topology=topology,
            primitive=primitive,
            candidates_text=candidate_text,
            historical_text=historical_text,
        )

        try:
            raw = self.client.ask(prompt)
            return self._parse(raw)
        except Exception:
            return None

    @staticmethod
    def _parse(raw):
        """Extract Algorithm: and Reason: lines."""
        algorithm = ""
        reason = ""
        for line in raw.splitlines():
            s = line.strip()
            if s.lower().startswith("algorithm:"):
                algorithm = s.split(":", 1)[1].strip()
            elif s.lower().startswith("reason:"):
                reason = s.split(":", 1)[1].strip()

        if not algorithm:
            # LLM returned an unparseable response.
            return None

        return {"algorithm": algorithm, "reason": reason}
