# Defense Storyline

| Beat | Reviewer question | Primary figure | Evidence-safe answer |
|---|---|---|---|
| Problem | Why is collective optimization hard to audit? | FIG-01 | The system separates Agent proposal, host execution, simulator evidence, Direct readiness, and the hardware gap. |
| System | How do decisions reach executable artifacts? | FIG-02 | Topology/workload inputs flow through proposal, Schedule IR v2, selector/cost model, deterministic evaluation, and evidence-backed gating. |
| Optimization | What quantitative result is frozen? | FIG-03, FIG-04 | G3-C supplies the canonical simulated latency and outcome data; the figures do not rerun benchmarks. |
| Feature completion | What communication and reliability features exist? | FIG-06, FIG-07 | Sparse correctness is host validated; sparse bytes are modeled; CRC/retry are host validated; backpressure is simulated. |
| Agent role | What did the Agent decide? | FIG-08, FIG-09 | Agent proposals and reflections are separated from deterministic evaluation and human-governed gates; normalized traces are not hidden reasoning. |
| Evidence | How broad are the results? | FIG-05, FIG-11, FIG-13 | Logical scale, modeled ablation, and algorithm/topology coverage remain within their stated simulator/host boundaries. |
| Limitations | What was not executed? | FIG-10, FIG-12 | Direct is compile/link-only; real-device execution and acceptance remain blocked by unavailable hardware evidence. |
| Competition value | What is the integrated contribution? | FIG-01, FIG-08 | An evidence-governed Agent workflow connects schedule and feature decisions to reproducible host/simulator delivery without overclaiming hardware results. |

The presentation should stop after this evidence-backed story. Final language, organizer template, license/redistribution, archive rules, and real-device acceptance remain user decisions.
