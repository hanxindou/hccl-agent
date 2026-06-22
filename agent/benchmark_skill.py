"""Benchmark Skill — measure actual execution time of algorithms."""

import time


class BenchmarkSkill:

    def __init__(self, execution_skill=None):
        self._execution_skill = execution_skill

    def set_execution_skill(self, skill):
        self._execution_skill = skill

    def benchmark_execution(self, algorithm, input_data):
        """Time a single algorithm execution via the C plugin.

        Returns
        -------
        dict  {"execution_time_ms": float, "execution_result": dict}
        """
        if self._execution_skill is None:
            return {"execution_time_ms": 0.0, "execution_result": None}

        start = time.perf_counter()
        result = self._execution_skill.execute(algorithm, input_data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "execution_time_ms": round(elapsed_ms, 4),
            "execution_result": result,
        }
