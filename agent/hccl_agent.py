from skills.algorithm_skill import AlgorithmSkill
from simulator.simulator import Simulator
from skills.topology_skill import TopologySkill
from skills.config_skill import ConfigSkill
from skills.optimization_skill import OptimizationSkill
from skills.strategy_skill import StrategySkill
from skills.topology_graph import TopologyGraph
from agent.experiment_logger import ExperimentLogger
from agent.prompt_engine import AgentPromptEngine
from agent.plugin_manager import PluginManager
from agent.execution_skill import ExecutionSkill
from agent.evaluation_skill import EvaluationSkill
from agent.report_generator import ReportGenerator
from agent.reasoning_skill import ReasoningSkill
from agent.decision_skill import DecisionSkill
from agent.benchmark_skill import BenchmarkSkill
from agent.experience_store import ExperienceStore
from agent.policy_engine import PolicyEngine
from agent.reflection_skill import ReflectionSkill
from agent.replanning_skill import ReplanningSkill
from agent.planning_skill import PlanningSkill
from agent.explanation_skill import ExplanationSkill


class HCCLAgent:

    SUPPORTED_PRIMITIVES = {
        "AllReduce",
        "AllGather",
        "ReduceScatter",
        "Broadcast",
    }

    def __init__(self):
        self.algorithm_skill = AlgorithmSkill()
        self.topology_skill = TopologySkill()
        self.config_skill = ConfigSkill()
        self.simulator = Simulator()
        self.optimization_skill = OptimizationSkill()
        self.strategy_skill = StrategySkill()
        self.logger = ExperimentLogger()
        self.prompt_engine = AgentPromptEngine()
        self.plugin_manager = PluginManager()
        self.execution_skill = ExecutionSkill()
        self.evaluation_skill = EvaluationSkill()
        self.report_generator = ReportGenerator()
        self.reasoning_skill = ReasoningSkill()
        self.decision_skill = DecisionSkill()
        self.benchmark_skill = BenchmarkSkill(self.execution_skill)
        self.experience_store = ExperienceStore()
        self.reflection_skill = ReflectionSkill()
        self.planning_skill = PlanningSkill()
        self.explanation_skill = ExplanationSkill()

    def run(
        self,
        nodes,
        message_size,
        primitive="AllReduce",
    ):
        primitive = self._normalize_primitive(primitive)

        cluster_info = self.config_skill.load_cluster_info()

        # ---- topology inference ----
        topology = self.topology_skill.analyze(nodes)

        # ---- topology graph ----
        topology_graph = self._build_topology_graph(
            nodes, topology, cluster_info
        )

        # ---- plugin capability discovery ----
        plugin_info = self.plugin_manager.discover()

        # ---- runtime config ----
        runtime_cluster_info = dict(cluster_info)
        runtime_cluster_info["nodes"] = nodes
        runtime_cluster_info["topology"] = topology

        # ---- multi-step planning ----
        plan = self.planning_skill.create_plan(
            nodes, message_size, primitive,
        )

        # ---- algorithm selection ----
        candidate_algorithms = (
            self.algorithm_skill.choose_algorithms(
                nodes,
                message_size,
                primitive=primitive,
            )
        )

        # ---- LLM reasoning (best-effort, degrades gracefully) ----
        reasoning_result = None
        try:
            reasoning_result = self.reasoning_skill.analyze(
                nodes,
                message_size,
                topology,
                candidate_algorithms,
            )
        except Exception as e:
            # API key not set or network unavailable — Agent still
            # functions with the rule-based path alone.
            print(
                "[Reasoning Error]",
                e
            )

        # ---- optimisation / ranking ----
        best_algorithm, best_result, ranking = (
            self.optimization_skill.optimize(
                self.simulator,
                runtime_cluster_info,
                candidate_algorithms,
                nodes,
                message_size,
                primitive=primitive,
            )
        )

        # ---- LLM decision (best-effort, overrides max-score) ----
        decision = None
        try:
            candidate_results = []
            for algo, score in ranking:
                sim_res = self.simulator.evaluate(
                    algo, topology, nodes, message_size,
                    primitive=primitive,
                    bandwidth_gbps=runtime_cluster_info.get("bandwidth_gbps"),
                    latency_ms=runtime_cluster_info.get("latency_ms"),
                )
                candidate_results.append({
                    "algorithm": algo,
                    "score": score,
                    "latency": sim_res["latency"],
                    "bandwidth": sim_res["bandwidth"],
                })
            similar_records = self.experience_store.query_similar(
                nodes, topology, primitive,
            )
            historical = ExperienceStore.aggregate_statistics(
                similar_records,
            ) if similar_records else None
            win_rates = ExperienceStore.get_win_rate_summary(
                similar_records,
            ) if similar_records else None

            # Policy-based ranking (simulation + historical win rates).
            sim_scores = {r["algorithm"]: r["score"] for r in candidate_results}
            policy_ranking = PolicyEngine.rank_algorithms(
                sim_scores, win_rates or {},
            ) if win_rates else None

            decision = self.decision_skill.choose_algorithm(
                nodes, message_size, topology, primitive, candidate_results,
                historical_stats=historical,
                win_rates=win_rates,
            )
        except Exception:
            pass

        # If LLM returned a valid algorithm in our candidate list, use it.
        chosen_algorithm = best_algorithm
        if decision and decision.get("algorithm"):
            for algo, _ in ranking:
                if algo == decision["algorithm"]:
                    chosen_algorithm = algo
                    break

        # ---- benchmark actual execution ----
        benchmark = {"execution_time_ms": 0.0}
        try:
            benchmark_input = [
                float(i + 1) for i in range(nodes)
            ]
            benchmark = self.benchmark_skill.benchmark_execution(
                chosen_algorithm, benchmark_input,
            )
        except Exception:
            pass

        # ---- explanation / decision trace ----
        # Use topology graph summary as proxy for topology_analysis.
        topo_analysis = {
            "topology_type": topology,
            "node_count": nodes,
            "dominant_link": runtime_cluster_info.get("links", [{}])[0].get("type", "HCCS") if runtime_cluster_info.get("links") else "HCCS",
        }
        candidate_scores_list = [
            {"algorithm": algo, "score": score,
             "latency": 0.0, "bandwidth": 0.0}
            for algo, score in ranking
        ]

        # ---- self-reflection ----
        reflection = self.reflection_skill.reflect(
            predicted_score=best_result["score"],
            actual_execution_time_ms=benchmark.get("execution_time_ms", 0.0),
            algorithm=chosen_algorithm,
            candidate_scores=candidate_scores_list,
        )

        # ---- replanning (max 1 iteration) ----
        replanned = False
        replan_algorithm = None
        replan_benchmark = None
        if reflection["need_replan"] and ranking:
            alt = ReplanningSkill.choose_alternative(
                chosen_algorithm, ranking,
            )
            if alt != chosen_algorithm:
                try:
                    replan_benchmark = self.benchmark_skill.benchmark_execution(
                        alt,
                        [float(i + 1) for i in range(nodes)],
                    )
                    chosen_algorithm = alt
                    replanned = True
                    replan_algorithm = alt
                except Exception:
                    pass

        # ---- decision trace ----
        decision_trace = self.explanation_skill.generate_decision_trace(
            topology_analysis=topo_analysis,
            candidate_scores=candidate_scores_list,
            selected_algorithm=chosen_algorithm,
            selection_reason=(
                decision["reason"] if decision and decision.get("reason")
                else f"Highest score among {len(ranking)} candidates"
            ),
            reflection_result=reflection,
        )

        # ---- strategy generation ----
        strategy = self.strategy_skill.generate(
            chosen_algorithm,
            nodes,
            primitive=primitive,
        )

        # ---- prompt logging ----
        prompt_params = {
            "primitive": primitive,
            "nodes": str(nodes),
            "message_size": str(message_size),
            "topology": topology,
            "bandwidth_gbps": str(
                runtime_cluster_info.get("bandwidth_gbps", "N/A")
            ),
            "latency_ms": str(
                runtime_cluster_info.get("latency_ms", "N/A")
            ),
            "device_type": runtime_cluster_info.get(
                "device_type", "Ascend910A"
            ),
        }
        filled_prompt = self.prompt_engine.build_algorithm_selection_prompt(
            prompt_params
        )

        # ---- recommendation reason ----
        reason = self._build_reason(
            primitive,
            topology,
            message_size,
            candidate_algorithms,
            chosen_algorithm,
            best_result,
        )

        # ---- assemble output ----
        output = {
            "plan": plan,
            "plugin": plugin_info,
            "cluster": runtime_cluster_info,
            "primitive": primitive,
            "topology": topology,
            "topology_graph_summary": topology_graph.summary(),
            "message_size_mb": message_size,
            "candidate_algorithms": candidate_algorithms,
            "algorithm": chosen_algorithm,
            "reason": reason,
            "result": best_result,
            "best_algorithm": best_algorithm,
            "best_result": best_result,
            "llm_decision": decision,
            "benchmark": benchmark,
            "reflection": reflection,
            "decision_trace": decision_trace,
            "replanned": replanned,
            "replan_algorithm": replan_algorithm,
            "replan_benchmark": replan_benchmark,
            "policy_ranking": policy_ranking,
            "ranking": ranking,
            "strategy": strategy,
            "prompt_filled": filled_prompt[:200] + "..."
            if len(filled_prompt) > 200 else filled_prompt,
            "reasoning": reasoning_result,
        }

        # Persist this run for reproducible experiment tracking.
        self.logger.log_run(output)

        # Save to experience memory for historical learning.
        self.experience_store.save({
            "nodes": nodes,
            "message_size": message_size,
            "topology": topology,
            "primitive": primitive,
            "algorithm": chosen_algorithm,
            "score": best_result["score"],
            "execution_time_ms": benchmark.get("execution_time_ms", 0.0),
        })

        return output

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def run_execution_demo(self, algorithm="Ring AllReduce",
                           input_data=None):
        """Execute *algorithm* on *input_data* via the C plugin.

        This is a separate entry point from run() — it does not use the
        Simulator or StrategySkill.  It calls the real (CPU-simulated)
        HCCL algorithm implementation through the Execution Engine.

        Parameters
        ----------
        algorithm : str
            Agent display name, e.g. "Ring AllReduce".
        input_data : list[float] or None
            One float per rank.  Defaults to [1, 2, 3, 4].

        Returns
        -------
        dict — ExecutionEngine result.
        """
        if input_data is None:
            input_data = [1.0, 2.0, 3.0, 4.0]

        return self.execution_skill.execute(algorithm, input_data)

    def generate_execution_report(self, algorithm="Ring AllReduce",
                                  input_data=None):
        """Execute *algorithm*, evaluate performance, and return a report.

        Runs the full pipeline:
          1. Execute algorithm via C plugin
          2. Simulate performance (latency / bandwidth / score)
          3. Evaluate the performance result
          4. Generate a text report

        Parameters
        ----------
        algorithm : str
            e.g. "Ring AllReduce".
        input_data : list[float] or None
            One float per rank.  Defaults to [1, 2, 3, 4].

        Returns
        -------
        dict
            {"execution": ..., "evaluation": ..., "report": "..."}
        """
        if input_data is None:
            input_data = [1.0, 2.0, 3.0, 4.0]

        # 1. Execute the algorithm via the C plugin (timed).
        benchmark = self.benchmark_skill.benchmark_execution(
            algorithm, input_data,
        )
        execution = benchmark.get("execution_result",
                                  self.execution_skill.execute(algorithm, input_data))

        # 2. Simulate performance using the Simulator.
        nodes = len(input_data)
        topology = self.topology_skill.analyze(nodes)
        cluster_info = self.config_skill.load_cluster_info()

        sim_result = self.simulator.evaluate(
            algorithm,
            topology,
            nodes,
            128.0,
            primitive="AllReduce",
            bandwidth_gbps=cluster_info.get("bandwidth_gbps"),
            latency_ms=cluster_info.get("latency_ms"),
        )
        sim_result["algorithm"] = algorithm

        # 3. Evaluate the performance.
        evaluation = self.evaluation_skill.evaluate(sim_result)

        # 4. Generate the report.
        plan = self.planning_skill.create_plan(
            nodes, 128.0, "AllReduce",
        )
        report = self.report_generator.generate_report(
            sim_result, evaluation, benchmark=benchmark, plan=plan,
        )

        return {
            "execution": execution,
            "evaluation": evaluation,
            "report": report,
            "benchmark": benchmark,
        }

    def _normalize_primitive(self, primitive):
        if primitive not in self.SUPPORTED_PRIMITIVES:
            supported = ", ".join(
                sorted(self.SUPPORTED_PRIMITIVES)
            )
            raise ValueError(
                f"Unsupported primitive: {primitive}. "
                f"Supported primitives: {supported}"
            )
        return primitive

    def _build_topology_graph(self, nodes, topology, cluster_info):
        """Construct a TopologyGraph matching the inferred topology and
        cluster link parameters.

        Uses the first link entry (typically HCCS) for intra-server
        edges.  Returns the graph instance so path computation is
        available to the caller.
        """
        links = cluster_info.get("links", [])
        if links:
            primary = links[0]
            bw = primary.get("bandwidth_gbps", 100)
            lat = primary.get("latency_ms", 0.002)
            ber = primary.get("ber", 1e-12)
        else:
            bw = cluster_info.get("bandwidth_gbps", 100)
            lat = cluster_info.get("latency_ms", 0.002)
            ber = 1e-12

        kwargs = {
            "bandwidth_gbps": bw,
            "latency_ms": lat,
            "ber": ber,
        }

        if topology == "Full Mesh":
            return TopologyGraph.full_mesh(nodes, **kwargs)
        elif topology == "Ring":
            return TopologyGraph.ring(nodes, **kwargs)
        elif topology == "Fat Tree":
            return TopologyGraph.fat_tree(nodes, **kwargs)
        else:
            # Fallback: full mesh with whatever we have.
            return TopologyGraph.full_mesh(nodes, **kwargs)

    def _build_reason(
        self,
        primitive,
        topology,
        message_size,
        candidate_algorithms,
        best_algorithm,
        best_result,
    ):
        return (
            f"当前集合通信原语为 {primitive}，"
            f"节点规模推断为 {topology} 拓扑，"
            f"消息大小为 {message_size} MB。"
            f"Agent 比较了 {len(candidate_algorithms)} 个候选算法，"
            f"最终选择 {best_algorithm}，"
            f"因为它在当前模拟模型中的 score 最高，"
            f"latency={best_result['latency']} ms，"
            f"bandwidth={best_result['bandwidth']} GB/s，"
            f"score={best_result['score']}。"
        )
