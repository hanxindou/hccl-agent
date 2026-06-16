"""Report Generator — format execution and evaluation results into text."""


class ReportGenerator:

    @staticmethod
    def generate_report(execution_result, evaluation_result):
        """Produce a human-readable execution report.

        Parameters
        ----------
        execution_result : dict
            From Simulator or ExecutionEngine.  Expected keys:
            "algorithm", "latency", "bandwidth", "score".
        evaluation_result : dict
            From EvaluationSkill.evaluate().  Expected keys:
            "grade", "recommendation".

        Returns
        -------
        str — multi-line report.
        """
        algo   = execution_result.get("algorithm", "Unknown")
        lat    = execution_result.get("latency", "N/A")
        bw     = execution_result.get("bandwidth", "N/A")
        score  = execution_result.get("score", "N/A")
        grade  = evaluation_result.get("grade", "N/A")
        rec    = evaluation_result.get("recommendation", "")

        return (
            f"Execution Report\n"
            f"=================\n"
            f"\n"
            f"Algorithm:\n"
            f"  {algo}\n"
            f"\n"
            f"Latency:\n"
            f"  {lat} ms\n"
            f"\n"
            f"Bandwidth:\n"
            f"  {bw} GB/s\n"
            f"\n"
            f"Score:\n"
            f"  {score}\n"
            f"\n"
            f"Evaluation:\n"
            f"  {grade}\n"
            f"\n"
            f"Recommendation:\n"
            f"  {rec}\n"
        )
