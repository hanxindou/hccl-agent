"""Execution Skill — Agent-facing wrapper around the Execution Engine.

Provides a uniform interface for the Agent to run HCCL algorithms
discovered through the plugin system.
"""

from plugin.execution_engine import ExecutionEngine


class ExecutionSkill:

    def __init__(self):
        self.engine = ExecutionEngine()

    def execute(self, algorithm_name, input_data):
        """Run *algorithm_name* on *input_data* via the Execution Engine.

        Parameters
        ----------
        algorithm_name : str
            e.g. "Ring AllReduce"
        input_data : list[float]
            One float per rank.

        Returns
        -------
        dict — ExecutionEngine.execute_algorithm() result.
        """
        return self.engine.execute_algorithm(algorithm_name, input_data)
