"""Report Generator — format execution, evaluation, and benchmark results."""


class ReportGenerator:

    @staticmethod
    def generate_report(execution_result, evaluation_result,
                        benchmark=None):
        algo   = execution_result.get("algorithm", "Unknown")
        lat    = execution_result.get("latency", "N/A")
        bw     = execution_result.get("bandwidth", "N/A")
        score  = execution_result.get("score", "N/A")
        grade  = evaluation_result.get("grade", "N/A")
        rec    = evaluation_result.get("recommendation", "")

        lines = [
            "Execution Report",
            "=================",
            "",
            "Algorithm:",
            f"  {algo}",
            "",
            "Predicted Score:",
            f"  {score}",
            "",
            "Latency:",
            f"  {lat} ms",
            "",
            "Bandwidth:",
            f"  {bw} GB/s",
        ]

        if benchmark:
            t = benchmark.get("execution_time_ms", "N/A")
            lines += [
                "",
                "Actual Execution Time:",
                f"  {t} ms",
            ]

        lines += [
            "",
            "Evaluation:",
            f"  {grade}",
            "",
            "Recommendation:",
            f"  {rec}",
        ]

        return "\n".join(lines) + "\n"
