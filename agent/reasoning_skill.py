"""Reasoning Skill — use DeepSeek to analyse candidate algorithms.

Wraps LLMClient with a task-specific prompt that asks the model to
recommend the best algorithm for the given topology / message-size /
primitive context.
"""

from agent.llm_client import LLMClient

_REASONING_SYSTEM_PROMPT = (
    "You are an expert in distributed collective-communication "
    "algorithms for Ascend NPU clusters.  Answer concisely in English."
)

_REASONING_USER_TEMPLATE = """\
Analyse the following HCCL communication scenario and recommend the best algorithm.

Nodes: {nodes}
Message Size: {message_size} MB
Topology: {topology}

Candidate algorithms:
{candidates}

Please:
1. State which single algorithm you recommend.
2. Explain your reasoning in 2–3 sentences.

Reply in this format:
Recommendation: <algorithm name>
Reasoning: <your technical analysis>
"""


class ReasoningSkill:
    """Ask DeepSeek to reason about candidate algorithms."""

    def __init__(self, client=None):
        self.client = client or LLMClient()

    def analyze(self, nodes, message_size, topology,
                candidate_algorithms):
        """Return an LLM-based recommendation.

        Parameters
        ----------
        nodes : int
        message_size : float  (MB)
        topology : str
        candidate_algorithms : list[str]

        Returns
        -------
        dict
            {"recommendation": "Ring AllReduce",
             "reasoning": "..."}
        """
        candidates_str = "\n".join(
            f"- {a}" for a in candidate_algorithms
        )

        prompt = _REASONING_USER_TEMPLATE.format(
            nodes=nodes,
            message_size=message_size,
            topology=topology,
            candidates=candidates_str,
        )

        raw = self.client.ask(
            prompt=prompt,
            system_prompt=_REASONING_SYSTEM_PROMPT,
        )

        return self._parse_response(raw)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(raw):
        """Extract recommendation and reasoning from the model's reply."""
        recommendation = ""
        reasoning = ""

        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("recommendation:"):
                recommendation = stripped.split(":", 1)[1].strip()
            elif stripped.lower().startswith("reasoning:"):
                reasoning = stripped.split(":", 1)[1].strip()

        # Fallback: use the whole response as reasoning.
        if not recommendation and not reasoning:
            reasoning = raw.strip()

        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
        }
