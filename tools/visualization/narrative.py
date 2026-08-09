"""Claim-safe competition narrative and defense materials for G3-E-D."""

from __future__ import annotations

from typing import Any

from .common import CLAIM_LEDGER, DATA_LEDGER, OUTPUT_ROOT, ROOT, load_json, write_json, write_text


NARRATIVE_FILES = [
    "competition_narrative.md",
    "defense_storyline.md",
    "figure_story_map.md",
    "claim_safe_phrasebook.md",
    "defense_question_map.md",
]


def _metric_map() -> dict[str, dict[str, Any]]:
    return {row["metric_id"]: row for row in load_json(DATA_LEDGER)["metrics"]}


def _claim_map() -> dict[str, dict[str, Any]]:
    return {row["claim_id"]: row for row in load_json(CLAIM_LEDGER)["claims"]}


def _competition_narrative(metrics: dict[str, dict[str, Any]]) -> str:
    improvement = metrics["g3b2.performance.weighted_geomean_improvement_percent"]["display_value"]
    wins = metrics["g3b2.outcomes.wins"]["display_value"]
    ties = metrics["g3b2.outcomes.ties"]["display_value"]
    losses = metrics["g3b2.outcomes.losses"]["display_value"]
    return f"""# Competition Narrative

Status: `EVIDENCE_BACKED_SUBMISSION_NARRATIVE`

## 30-second layer

HCCL Agent is an Agent-assisted collective-communication optimization and delivery system. It turns topology and workload constraints into an auditable Schedule IR, proposes schedules and feature decisions, evaluates them deterministically, and preserves explicit human governance. Against the frozen fixed-Ring baseline, its communication simulator records a weighted collective-time improvement of {improvement} with {wins} wins, {ties} ties, and {losses} losses across the frozen scenario inventory. This is `SIMULATED_ONLY`; it is not Ascend/NPU or training performance.

## 3-minute layer

1. **Problem.** Collective optimization spans topology, algorithm selection, scheduling, reliability, and delivery constraints. A useful competition system must expose those decisions and their evidence rather than present one opaque result.
2. **System.** Schedule IR v2 connects topology-aware proposal, selector and cost-model evaluation, CPU_SIM validation, simulator acceptance, and a separate Direct readiness track. CPU_SIM remains the default project-owned host backend; simulator acceptance is an independent validation track.
3. **Optimization.** The Agent proposes and replans; deterministic evaluation checks frozen scenario outcomes; human-governed gates decide what is accepted. The canonical outcome is {improvement} weighted simulated collective-time improvement and {wins}/{ties}/{losses} wins/ties/losses against fixed Ring.
4. **Feature completion.** The lossless sparse codec is host validated and paired with modeled byte accounting and dense fallback. CRC32 integrity and bounded retry are host validated. Credit flow control and backpressure remain simulator modeled.
5. **Negative decisions.** INT8 is `DEFERRED_BY_PRECISION_GATE`; PairWise is `SKIPPED_BY_VALUE_GATE`. These decisions remain visible because the evidence gate is part of the contribution.
6. **Delivery.** The mandatory Agent replay path is offline and API-key-free. The project CPU_SIM ABI remains frozen. Official ACL/HCCL calls exist in a compile/link-only Direct source path that was not loaded or executed.
7. **Boundary.** Logical scale is not a physical device cluster; modeled wire bytes are not NIC measurements; real-device acceptance remains `HARDWARE_BLOCKED`.

## Technical-defense layer

The defensible chain is `Prompt → Skill → normalized Agent trace → implementation source → source commit → frozen evidence → G3-C claim → G3-E figure`. Proposal, deterministic evaluation, human intervention, replay, and reconstruction are separately labeled. G3-E introduces no new algorithm, benchmark, metric, or claim; it renders and narrates frozen G3-C/G3-D authorities.

The optimization result must always be described as communication-simulator evidence. The sparse contribution combines host-observed lossless correctness with modeled/logical byte accounting. Reliability evidence is intentionally split into host integrity, host retry, and simulated backpressure. Direct readiness proves source-expression and compile/link preparation only; no ACL/HCCL runtime, communicator, collective, MPI, profiling, or real device was executed in G3-E.
"""


def _defense_storyline() -> str:
    return """# Defense Storyline

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
"""


def _figure_story_map(registry: dict[str, Any]) -> str:
    lines = ["# Figure-to-story Map", "", "| Figure | Class | Audience question | Claims | Truth identity | Limitations |", "|---|---|---|---|---|---|"]
    candidates = {row["figure_id"]: row for row in load_json(OUTPUT_ROOT / "chart_candidate_inventory.json")["candidates"]}
    for figure in registry["figures"]:
        candidate = candidates[figure["figure_id"]]
        limitations = "; ".join(figure["limitations"]).replace("real collective executed", "device collective execution did not occur")
        lines.append(f"| {figure['figure_id']} | {figure['classification']} | {candidate['audience_question']} | {', '.join(figure['claim_refs'])} | {', '.join(figure['truth_identity'])} | {limitations} |")
    return "\n".join(lines) + "\n"


def _phrasebook(claims: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Claim-safe Phrasebook",
        "",
        "The G3-C claim ledger is authoritative. Forbidden phrases below are quoted only so reviewers and authors can reject them.",
        "",
        "| Claim | Safe wording | Conditional boundary | Forbidden wording | Truth identity |",
        "|---|---|---|---|---|",
    ]
    for claim_id in sorted(claims):
        claim = claims[claim_id]
        safe = "; ".join(claim["allowed_wording"])
        conditional = "; ".join(claim["limitations"]) or "Use only with the stated truth identity."
        forbidden = "; ".join(claim["prohibited_wording"])
        lines.append(f"| {claim_id} | {safe} | {conditional} | {forbidden} | {claim['truth_label']} |")
    lines.extend([
        "", "## Agent/autonomy wording", "",
        "Use: `Agent-assisted`, `Agent-generated proposal`, `deterministically evaluated`, `human-governed`, `offline replayable`, and `evidence-backed`.", "",
        "Do not assert full autonomy. G3-B3 historical Prompt/Response is unavailable; normalized trace material is reconstructed from frozen evidence and is not hidden chain-of-thought.", "",
    ])
    return "\n".join(lines)


def _defense_questions(metrics: dict[str, dict[str, Any]]) -> str:
    improvement = metrics["g3b2.performance.weighted_geomean_improvement_percent"]["display_value"]
    return f"""# Defense Question Map

## Q1. Is the {improvement} improvement measured on Ascend NPUs?

No. It is the G3-C canonical display of a frozen weighted communication-simulator comparison against fixed Ring. No real model, device collective, or training throughput was executed.

## Q2. Does the 1024-rank result mean 1024 physical devices?

No. It is logical simulator scale and must not be presented as a physical cluster.

## Q3. Are sparse byte reductions NIC measurements?

No. Lossless sparse reconstruction/correctness is host observed; the wire-byte and compression accounting is modeled/logical, with dense fallback when modeled sparse cost is unfavorable.

## Q4. Did Direct execute official ACL/HCCL calls?

No. Official call expressions exist in a default-OFF compile/link source path. The source was not loaded or executed, and runtime API calls remain empty.

## Q5. Is the CPU_SIM 19-symbol ABI the official loader ABI?

No. It is the frozen project CPU_SIM ABI and SONAME contract.

## Q6. Is the Agent fully autonomous?

No such claim is supported. The delivery is Agent-assisted, deterministically evaluated, human-governed, and offline replayable. Human goals, constraints, approvals, and frozen gates are disclosed.

## Q7. Are normalized traces original historical model conversations?

No. Replay is not historical execution. G3-B2/G3-B3 normalized traces are reconstructed from frozen evidence where stated; unavailable historical Prompt/Response relationships remain explicitly unavailable.

## Q8. Why are INT8 and PairWise missing?

They are evidence-gated decisions rather than hidden omissions: INT8 is deferred by its precision gate and PairWise is skipped by its value gate.

## Q9. Is reliability validated on a real network?

No. CRC32 integrity and bounded retry semantics are host validated. Backpressure and bounded inflight behavior are simulator modeled. No NIC/HCCL hardware reliability result is claimed.

## Q10. What remains blocked or requires organizer/user action?

Real-device acceptance remains `HARDWARE_BLOCKED`. License/copyright, controlled artifact redistribution, submission archive/size rules, precision interpretation, final language, and final organizer template remain `USER_ACTION_REQUIRED`.
"""


def build_narrative() -> dict[str, Any]:
    metrics, claims = _metric_map(), _claim_map()
    registry = load_json(OUTPUT_ROOT / "chart_registry.json")
    write_text(OUTPUT_ROOT / "competition_narrative.md", _competition_narrative(metrics))
    write_text(OUTPUT_ROOT / "defense_storyline.md", _defense_storyline())
    write_text(OUTPUT_ROOT / "figure_story_map.md", _figure_story_map(registry))
    write_text(OUTPUT_ROOT / "claim_safe_phrasebook.md", _phrasebook(claims))
    write_text(OUTPUT_ROOT / "defense_question_map.md", _defense_questions(metrics))
    contract = {
        "schema_version": "g3-e-narrative-contract-v1",
        "status": "CLAIM_SAFE",
        "layers": ["30-second", "3-minute", "technical-defense"],
        "story_order": ["Problem", "System", "Optimization", "Feature completion", "Agent role", "Evidence", "Limitations", "Competition value"],
        "claim_authority": "docs/submission/report_claim_ledger.json",
        "numeric_authority": "docs/submission/report_data_ledger.json",
        "agent_provenance_authority": "docs/submission/agent_delivery",
        "documents": NARRATIVE_FILES,
        "final_language": "USER_ACTION_REQUIRED",
        "final_template": "USER_ACTION_REQUIRED",
        "real_device_acceptance": "HARDWARE_BLOCKED",
    }
    write_json(OUTPUT_ROOT / "narrative_contract.json", contract)
    return validate_narrative()


def validate_narrative() -> dict[str, Any]:
    errors: list[str] = []
    claims = _claim_map()
    registry = load_json(OUTPUT_ROOT / "chart_registry.json")
    contract = load_json(OUTPUT_ROOT / "narrative_contract.json")
    documents = {}
    for name in NARRATIVE_FILES:
        path = OUTPUT_ROOT / name
        if not path.is_file():
            errors.append(f"missing narrative document: {name}")
            continue
        documents[name] = path.read_text(encoding="utf-8")
    non_phrasebook = "\n".join(text for name, text in documents.items() if name != "claim_safe_phrasebook.md").lower()
    for claim_id, claim in claims.items():
        for phrase in claim["prohibited_wording"]:
            if phrase.lower() in non_phrasebook:
                errors.append(f"forbidden overclaim outside phrasebook: {claim_id} {phrase}")
    required_boundaries = ["simulated_only", "hardware_blocked", "host_integrity_validated", "host_retry_validated", "simulated_backpressure", "direct_compile_link_only", "real_device_not_executed"]
    aggregate = "\n".join(documents.values()).lower()
    for boundary in required_boundaries:
        if boundary not in aggregate:
            errors.append(f"missing narrative boundary: {boundary}")
    story_map = documents.get("figure_story_map.md", "")
    for figure in registry["figures"]:
        if figure["figure_id"] not in story_map:
            errors.append(f"unmapped figure: {figure['figure_id']}")
    phrasebook = documents.get("claim_safe_phrasebook.md", "")
    for claim_id in claims:
        if claim_id not in phrasebook:
            errors.append(f"claim absent from phrasebook: {claim_id}")
    for text in documents.values():
        lowered = text.lower()
        if "f:\\" in lowered or "c:\\users\\" in lowered or "file://" in lowered:
            errors.append("local absolute path in narrative")
        if "deepseek_api_key=" in lowered or "openai_api_key=" in lowered or "anthropic_api_key=" in lowered:
            errors.append("secret-like assignment in narrative")
    if contract.get("real_device_acceptance") != "HARDWARE_BLOCKED":
        errors.append("hardware boundary mismatch")
    return {
        "schema_version": "g3-e-narrative-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "document_count": len(documents),
        "claim_count": len(claims),
        "figure_count": len(registry["figures"]),
        "layers": contract.get("layers"),
        "final_language": contract.get("final_language"),
        "final_template": contract.get("final_template"),
        "benchmark_rerun": False,
        "runtime_api_calls": [],
        "sentinel": "G3_E_NARRATIVE_OK" if not errors else None,
    }
