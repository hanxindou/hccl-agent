"""Report Generator — format execution, evaluation, benchmark, and
historical statistics into a text report."""


class ReportGenerator:

    @staticmethod
    def generate_report(execution_result, evaluation_result,
                        benchmark=None, historical_stats=None,
                        policy_ranking=None, reflection=None,
                        replanned=False, replan_algorithm=None,
                        plan=None, hccl_result=None,
                        selection_info=None, decision_trace=None):
        algo  = execution_result.get("algorithm", "Unknown")
        lat   = execution_result.get("latency", "N/A")
        bw    = execution_result.get("bandwidth", "N/A")
        score = execution_result.get("score", "N/A")
        grade = evaluation_result.get("grade", "N/A")
        rec   = evaluation_result.get("recommendation", "")

        lines = [
            "Execution Report",
            "=================",
        ]

        if plan:
            lines += ["", "Planning:", "---------"]
            for step_item in plan:
                lines.append(
                    f"  {step_item['step']}. {step_item['task']}"
                )

        if selection_info:
            lines += [
                "",
                "Algorithm Selection Report:",
                "---------------------------",
                f"  Candidates: {', '.join(c['algorithm'] for c in selection_info.get('candidates', []))}",
            ]
            for c in selection_info.get("candidates", []):
                lines.append(
                    f"    {c['algorithm']:20s}  score={c['score']:.1f}"
                )
            lines += [
                f"  Selected:  {selection_info.get('algorithm', 'N/A')}",
                f"  Reason:    {selection_info.get('reason', '')}",
            ]

        lines += [
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

        if policy_ranking:
            lines += [
                "",
                "Policy Ranking:",
            ]
            max_len = max(len(a) for a, _ in policy_ranking) if policy_ranking else 0
            for algo, score in policy_ranking:
                lines.append(f"  {algo + ' ':.{max_len + 2}} {score}")

        if historical_stats:
            lines += [
                "",
                "Historical Performance:",
            ]
            for a, s in sorted(historical_stats.items()):
                lines.append(
                    f"  {a}:  runs={s['count']}, "
                    f"avg_score={s['avg_score']}, "
                    f"avg_time={s['avg_time_ms']}ms"
                )

        lines += [
            "",
            "Evaluation:",
            f"  {grade}",
            "",
            "Recommendation:",
            f"  {rec}",
        ]

        if decision_trace:
            lines += [
                "",
                "Decision Trace:",
                "---------------",
            ]
            for line in decision_trace.get("decision_trace", []):
                lines.append(f"  {line}")

        if reflection:
            lines += [
                "",
                "Reflection:",
                f"  Status: {reflection.get('status', 'N/A').upper()}",
                f"  Message: {reflection.get('message', '')}",
                f"  Need Replan: {reflection.get('need_replan', False)}",
            ]
            dq = reflection.get("decision_quality")
            if dq:
                lines += [
                    "",
                    "Reflection on Decision:",
                    "-----------------------",
                    f"  Selected:          {dq.get('selected_algorithm', '?')}",
                    f"  Selected Score:    {dq.get('selected_score', '?')}",
                    f"  Best Alternative:  {dq.get('best_alternative', '?')}",
                    f"  Alt Score:         {dq.get('best_alternative_score', '?')}",
                    f"  Score Gap:         {dq.get('score_gap', '?')}",
                    f"  Verdict:           {dq.get('recommendation', '')}",
                ]

        if replanned:
            lines += [
                "",
                "Replanning:",
                f"  Triggered: True",
                f"  Original Algorithm: {execution_result.get('algorithm', 'N/A')}",
                f"  Replanned Algorithm: {replan_algorithm or 'N/A'}",
            ]

        score_bd = execution_result.get("score_breakdown")
        if score_bd:
            lines += [
                "",
                "Performance Score Breakdown:",
                "-----------------------------",
                f"  Bandwidth Contribution:  {score_bd.get('bandwidth_score', 0):.1f} × {score_bd.get('bandwidth_weight', 0)} = {score_bd.get('bw_weighted', 0):.2f}",
                f"  Latency Contribution:    {score_bd.get('latency_score', 0):.1f} × {score_bd.get('latency_weight', 0)} = {score_bd.get('lat_weighted', 0):.2f}",
                f"  Final Score:             {score_bd.get('score', 0):.2f}",
            ]

        if hccl_result:
            lines += [
                "",
                "HCCL Compatibility Report:",
                "-----------------------------",
                f"  Primitive:  {hccl_result.get('primitive', 'N/A')}",
                f"  Algorithm:  {hccl_result.get('algorithm', 'N/A')}",
                f"  Topology:   {hccl_result.get('topology', 'N/A')}",
                f"  Latency:    {hccl_result.get('latency', 'N/A')} ms",
                f"  Bandwidth:  {hccl_result.get('bandwidth', 'N/A')} GB/s",
                f"  Score:      {hccl_result.get('score', 'N/A')}",
            ]

        reliability = execution_result.get("reliability")
        if reliability:
            health = reliability.get("health", {})
            retry = reliability.get("retry", {})
            fo = reliability.get("failover", {})
            lines += [
                "",
                "Reliability Report:",
                "--------------------",
                f"  Cluster Health:  {health.get('status', 'N/A')}",
                f"  Error Rate:      {health.get('error_rate', 'N/A')}",
                f"  Failed Links:    {health.get('failed_links', 'N/A')}",
                f"  Failed Nodes:    {health.get('failed_nodes', 'N/A')}",
                f"  Retry Success:   {retry.get('success', 'N/A')}",
                f"  Retry Attempts:  {retry.get('attempts', 'N/A')}",
                f"  Failover:        triggered={fo.get('triggered', 'N/A')}, found={fo.get('found', 'N/A')}",
            ]

        return "\n".join(lines) + "\n"
