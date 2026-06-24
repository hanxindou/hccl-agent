"""Report Generator — format execution, evaluation, benchmark, and
historical statistics into a text report."""


class ReportGenerator:

    @staticmethod
    def generate_report(execution_result, evaluation_result,
                        benchmark=None, historical_stats=None,
                        policy_ranking=None, reflection=None,
                        replanned=False, replan_algorithm=None,
                        plan=None, hccl_result=None,
                        selection_info=None, decision_trace=None,
                        code_generation=None):
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
        if code_generation:
            cfg = code_generation.get("hccl_config", {})
            plan_phases = code_generation.get("execution_plan", {})
            skeleton = code_generation.get("algorithm_skeleton", "")
            notes = code_generation.get("optimization_notes", [])
            lines += [
                "",
                "Generated Communication Strategy:",
                "----------------------------------",
                f"  Algorithm:            {cfg.get('algorithm', 'N/A')}",
                f"  Chunk Size:           {cfg.get('chunk_size_mb', 'N/A')} MB",
                f"  Pipeline Depth:       {cfg.get('pipeline_depth', 'N/A')}",
                f"  Pattern:              {cfg.get('communication_pattern', 'N/A')}",
            ]
            for phase, desc in plan_phases.items():
                lines.append(f"  {phase}: {desc}")
            if skeleton:
                lines += ["", "  Algorithm Skeleton:", ""]
                for line in skeleton.splitlines():
                    lines.append(f"    {line}")
            if notes:
                lines += ["", "  Optimization Notes:"]
                for n in notes:
                    lines.append(f"    - {n}")

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

        kc = execution_result.get("knowledge_context")
        if kc and kc.get("count", 0) > 0:
            bp = kc.get("best_practice") or {}
            lines += [
                "",
                "Knowledge Base Report:",
                "-----------------------",
                f"  Retrieved Cases:     {kc.get('count', 0)}",
                f"  Best Practice:       {bp.get('algorithm', 'N/A')} "
                f"(score={bp.get('score', 'N/A')})",
            ]
            for c in kc.get("cases", [])[:3]:
                lines.append(
                    f"  Case: {c.get('algorithm', '?')} "
                    f"score={c.get('score', '?')} "
                    f"lesson: {c.get('lesson_learned', '')[:80]}"
                )

        tuning = execution_result.get("auto_tuning")
        if tuning:
            bc = tuning.get("best_config", {})
            lines += [
                "",
                "Auto-Tuning Report:",
                "--------------------",
                f"  Evaluated Configurations: {tuning.get('evaluated_configs', 0)}",
                f"  Best Configuration:",
                f"    chunk_size_mb:  {bc.get('chunk_size_mb', 'N/A')}",
                f"    pipeline_depth: {bc.get('pipeline_depth', 'N/A')}",
                f"    overlap_factor: {bc.get('overlap_factor', 'N/A')}",
                f"  Best Score:            {tuning.get('best_score', 'N/A')}",
            ]
            top = tuning.get("top_k", [])
            if top:
                lines.append("  Top Configurations:")
                for i, entry in enumerate(top[:5]):
                    c = entry["config"]
                    lines.append(
                        f"    {i+1}. chunk={c['chunk_size_mb']:.0f} "
                        f"depth={c['pipeline_depth']:.0f} "
                        f"overlap={c['overlap_factor']:.2f} "
                        f"→ score={entry['score']:.1f}"
                    )

        exp = execution_result.get("experience_learning")
        if exp:
            lines += [
                "",
                "Experience Learning Report:",
                "----------------------------",
                f"  Historical Similar Runs: {exp.get('similar_runs', 0)}",
                f"  Recommended Algorithm:   {exp.get('recommended_algorithm', 'N/A')}",
                f"  Confidence:              {exp.get('confidence', 'N/A')}",
                f"  Reason:                  {exp.get('reason', '')}",
            ]
            stats = exp.get("stats", {})
            for algo, s in sorted(stats.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True):
                lines.append(
                    f"  {algo:20s}  avg_score={s['avg_score']:.1f}  runs={s['runs']}"
                )

        proposal = execution_result.get("optimization_proposal")
        if proposal:
            lines += [
                "",
                "Optimization Proposal Report:",
                "-----------------------------",
                f"  Summary: {proposal.get('summary', '')}",
                f"  Confidence: {proposal.get('confidence', 'N/A')}",
            ]
            for b in proposal.get("detected_bottlenecks", []):
                lines.append(f"  Bottleneck [{b['type']}]: {b['description']}")
            for r in proposal.get("recommendations", []):
                lines.append(f"  Recommendation: {r}")
            imp = proposal.get("expected_improvements", {})
            if imp:
                lines.append(
                    f"  Expected: latency {imp.get('latency_reduction_pct', 0):.1f}%↓, "
                    f"bandwidth {imp.get('bandwidth_gain_pct', 0):.1f}%↑, "
                    f"score {imp.get('score_gain_pct', 0):.1f}%↑"
                )
            for step in proposal.get("migration_plan", []):
                lines.append(f"  {step}")

        hw = execution_result.get("hardware_analysis")
        if hw:
            res = hw.get("resources", {})
            place = hw.get("placement", {})
            lines += [
                "",
                "Hardware Awareness Report:",
                "---------------------------",
                f"  Resource Pressure: {res.get('resource_pressure', 'N/A')}",
                f"  HBM Available:     {res.get('hbm_available', 'N/A')} GB",
                f"  UB Available:      {res.get('ub_available', 'N/A')} MB",
                f"  Locality Score:    {place.get('locality_score', 'N/A')}",
                f"  Ranks per NUMA:    {place.get('ranks_per_numa', 'N/A')}",
                f"  Bottlenecks:       {', '.join(hw.get('bottlenecks', [])) or 'None'}",
            ]

        topo_change = execution_result.get("topology_changed")
        if topo_change is not None:
            lines += [
                "",
                "Dynamic Topology Report:",
                "-------------------------",
                f"  Topology Changed: {topo_change}",
                f"  Reason: {execution_result.get('topology_change_reason', 'N/A')}",
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
