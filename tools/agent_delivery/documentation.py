"""Build and validate G3-D provenance and submission documentation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .authority import PROVENANCE_VOCABULARY
from .common import OUTPUT_ROOT, ROOT, assert_relative_repository_paths, load_json, sha256_file, write_json


REQUIRED_DOCUMENTS = (
    "README.md",
    "01_agent_architecture_and_workflow.md",
    "02_prompt_registry_and_version_reference.md",
    "03_skill_inventory.md",
    "04_trace_and_provenance_index.md",
    "05_offline_replay_guide.md",
    "06_human_intervention_and_autonomy_disclosure.md",
    "07_limitations_and_online_llm_boundary.md",
    "08_source_commit_evidence_claim_mapping.md",
)

REQUIRED_HEADINGS = ("## Validation Identity", "## Claim Boundaries", "## Known Limitations")
FORBIDDEN_WORDING = (
    "fully autonomous",
    "real HCCL speedup",
    "NPU speedup",
    "real collective executed",
    "real sparse network speedup",
    "NIC backpressure implemented",
    "hardware CRC verified",
)


def _header(title: str, identity: str) -> str:
    return f"# {title}\n\nReport Status: `G3_D_EVIDENCE_DERIVED`  \nExecution Identity: `{identity}`  \nReal-device Validated: `false`  \nRuntime API Executed: `false`\n\n"


def _tail(claims: str, limitations: str) -> str:
    return f"\n## Claim Boundaries\n\n{claims}\n\n## Known Limitations\n\n{limitations}\n"


def _relationship(
    relationship_id: str,
    from_type: str,
    from_id: str,
    to_type: str,
    to_id: str | None,
    *,
    authority: str,
    pointer: str,
    sha256: str | None,
    provenance: str,
    confidence: str,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "relationship_id": relationship_id,
        "from_type": from_type,
        "from_id": from_id,
        "to_type": to_type,
        "to_id": to_id,
        "authority_level": authority,
        "source_pointer": pointer,
        "source_sha256": sha256,
        "provenance": provenance,
        "confidence": confidence,
        "limitations": limitations or [],
    }


def build_mapping() -> dict[str, Any]:
    prompts = load_json(OUTPUT_ROOT / "prompt_registry.json")["prompts"]
    skills = load_json(OUTPUT_ROOT / "skill_registry.json")["skills"]
    index = load_json(OUTPUT_ROOT / "trace_index.json")["traces"]
    traces = {row["trace_id"]: load_json(ROOT / row["path"]) for row in index}
    relationships: list[dict[str, Any]] = []
    counter = 1
    prompt_path = "docs/submission/agent_delivery/prompt_registry.json"
    prompt_sha = sha256_file(ROOT / prompt_path)
    skill_path = "docs/submission/agent_delivery/skill_registry.json"
    skill_sha = sha256_file(ROOT / skill_path)
    trace_index_path = "docs/submission/agent_delivery/trace_index.json"
    trace_index_sha = sha256_file(ROOT / trace_index_path)
    for prompt in prompts:
        for skill in prompt["referenced_skills"]:
            relationships.append(_relationship(
                f"REL-{counter:04d}", "PROMPT", prompt["prompt_id"], "SKILL", skill,
                authority="L1" if prompt["historical_version_status"] == "HISTORICAL_TRACE_UNAVAILABLE" else "L4",
                pointer=prompt_path, sha256=prompt_sha, provenance=prompt["provenance"], confidence="HIGH",
                limitations=["source registry relationship; historical invocation is unavailable"] if prompt["historical_version_status"] == "HISTORICAL_TRACE_UNAVAILABLE" else [],
            )); counter += 1
    for trace_id, trace in traces.items():
        if trace["prompt_id"] is None:
            relationships.append(_relationship(
                f"REL-{counter:04d}", "TRACE", trace_id, "PROMPT", None,
                authority="L3", pointer=trace_index_path, sha256=trace_index_sha,
                provenance="HISTORICAL_TRACE_UNAVAILABLE", confidence="HIGH",
                limitations=["no historical Prompt/Response relationship is asserted"],
            )); counter += 1
        for skill in trace["skills"]:
            relationships.append(_relationship(
                f"REL-{counter:04d}", "SKILL", skill, "TRACE", trace_id,
                authority="L3" if trace["source_checkpoint"] == "G3-B3" else "L4",
                pointer=trace_index_path, sha256=trace_index_sha,
                provenance="RECONSTRUCTED_FROM_FROZEN_EVIDENCE", confidence="HIGH",
            )); counter += 1
        for ref in trace["source_refs"]:
            relationships.append(_relationship(
                f"REL-{counter:04d}", "TRACE", trace_id, "SOURCE", ref["path"],
                authority="L3" if trace["source_checkpoint"] == "G3-B3" else "L4",
                pointer=ref["path"], sha256=ref["sha256"], provenance="HISTORICAL_EVIDENCE", confidence="HIGH",
            )); counter += 1
        for ref in trace["commit_refs"]:
            relationships.append(_relationship(
                f"REL-{counter:04d}", "TRACE", trace_id, "COMMIT", ref["commit"],
                authority="L3" if trace["source_checkpoint"] == "G3-B3" else "L4",
                pointer=trace["source_evidence_path"], sha256=trace["source_evidence_sha256"],
                provenance=ref["provenance"], confidence="HIGH" if ref["commit_validity"] == "VALID" else "UNAVAILABLE",
                limitations=[] if ref["commit_validity"] == "VALID" else [f"recorded value {ref['recorded_value']} is not asserted as a commit"],
            )); counter += 1
        for claim in trace["claim_refs"]:
            relationships.append(_relationship(
                f"REL-{counter:04d}", "TRACE", trace_id, "G3_C_CLAIM", claim,
                authority="L2", pointer="docs/submission/report_claim_ledger.json",
                sha256=sha256_file(ROOT / "docs/submission/report_claim_ledger.json"),
                provenance="RECONSTRUCTED_FROM_FROZEN_EVIDENCE", confidence="HIGH",
            )); counter += 1
    return {
        "schema_version": "g3-d-source-commit-evidence-claim-mapping-v1",
        "status": "EVIDENCE_DERIVED",
        "relationship_count": len(relationships),
        "relationships": relationships,
        "unmapped_claim_policy": "claim_refs may be empty only with an explicit reason; no Agent claim is invented",
    }


def human_disclosure() -> dict[str, Any]:
    b2 = load_json(OUTPUT_ROOT / "traces/g3_b2_optimization_trace.json")
    return {
        "schema_version": "g3-d-human-intervention-disclosure-v1",
        "status": "HUMAN_GOVERNED_WITH_HISTORICAL_LIMITATIONS",
        "g3_b2": {
            "status": "HUMAN_INTERVENTION",
            "records": b2["human_intervention_refs"],
            "source": "agent/evidence/g3_b2/human_intervention.json",
            "provenance": "HISTORICAL_EVIDENCE",
        },
        "g3_b3": {
            "status": "HISTORICAL_TRACE_UNAVAILABLE",
            "records": [],
            "source": None,
            "provenance": "HISTORICAL_TRACE_UNAVAILABLE",
            "limitations": ["frozen feature evidence does not contain a complete historical human-intervention log"],
        },
        "autonomy_claim": "Agent-assisted, deterministically evaluated, human-governed, and offline replayable",
        "hidden_chain_of_thought_included": False,
    }


def _documents(mapping: dict[str, Any], disclosure: dict[str, Any]) -> dict[str, str]:
    prompts = load_json(OUTPUT_ROOT / "prompt_registry.json")["prompts"]
    skills = load_json(OUTPUT_ROOT / "skill_registry.json")["skills"]
    traces = load_json(OUTPUT_ROOT / "trace_index.json")["traces"]
    readme = _header("G3-D Agent / Prompt Reproducible Delivery", "OFFLINE_REPLAY") + "## Validation Identity\n\nThis directory is the canonical submission-facing Agent/Prompt delivery. It derives current source identity from merged Final Feature Freeze source and historical decisions from frozen G3-B2/G3-B3 evidence.\n\n## Deliverables\n\n" + "\n".join(f"- [{name}]({name})" for name in REQUIRED_DOCUMENTS[1:]) + _tail("All external language is constrained by `../report_claim_ledger.json`.", "Real-device acceptance remains `HARDWARE_BLOCKED`. Historical Prompt/Response records that cannot be proven remain unavailable.")
    architecture = _header("Agent Architecture and Workflow", "AGENT_ASSISTED_OFFLINE_REPLAY") + "## Validation Identity\n\nThe current system separates the `HCCLAgent` orchestrator, optional online reasoning, deterministic G3-B2/G3-B3 loops, Prompt loading, Skills, CPU_SIM execution, simulator evaluation, and evidence/reporting layers. Mandatory delivery replay reads normalized frozen evidence and does not invoke `HCCLAgent.run()`.\n\n## Workflow\n\n`input → proposal → deterministic evaluation → reflection/replanning → final decision → evidence/claim reference`\n\n`AGENT_GENERATED` identifies recorded proposals; `DETERMINISTIC_EVALUATION` identifies code/schema/correctness/cost gates; `HUMAN_INTERVENTION` identifies an explicit actor decision. These identities do not imply unsupervised development.\n" + _tail("The architecture is Agent-assisted and human-governed. CPU_SIM and simulator evidence do not establish real-device execution.", "Optional provider reasoning is not part of mandatory replay. Existing ignored local logs are not authority evidence.")
    prompt_doc = _header("Prompt Registry and Version Reference", "CURRENT_CANONICAL_AND_HISTORICAL_EVIDENCE") + f"## Validation Identity\n\nThe machine-readable registry contains {len(prompts)} entries. Five G3-B2 Prompt identities retain frozen version `1.0.0` and source hashes. Current template/inline prompts use source-hash versions; they do not receive invented historical versions.\n\n## Version Rules\n\n- `AVAILABLE_IN_FROZEN_EVIDENCE`: historical id/version/hash is proven.\n- `HISTORICAL_TRACE_UNAVAILABLE`: only current canonical source is proven.\n- `ONLINE_LLM_OPTIONAL`: never required by mandatory replay.\n" + _tail("Prompt text is not evidence that a capability was implemented or executed. Missing provider responses are not reconstructed.", "G3-B3 has no asserted historical Prompt/Response relationship. Several current templates contain aspirational language and are bounded by the claim ledger.")
    skill_doc = _header("Skill Inventory", "CURRENT_SOURCE_REGISTRY") + f"## Validation Identity\n\nThe machine-readable registry contains {len(skills)} source-backed entries from `agent/` and `skills/`. Each entry records source SHA, public callable inventory, stage, deterministic classification, tests, evidence, and limitations.\n\n## Classification\n\n- `DETERMINISTIC`: source behavior can run without an external model.\n- `OPTIONAL_ONLINE`: provider/key/network dependent and excluded from mandatory replay.\n- `HOST_EXECUTED`: project host/CPU_SIM execution only.\n- `SIMULATOR_MODEL`: modeled rather than physical execution.\n- `PARTIAL`: no focused test mapping was discovered.\n" + _tail("A registered Skill is a current source fact, not a real-device validation claim.", "Registry coverage does not promote untested modules. Roadmap and Prompt-only capabilities are excluded from implementation claims.")
    trace_doc = _header("Trace and Provenance Index", "RECONSTRUCTED_FROM_FROZEN_EVIDENCE") + f"## Validation Identity\n\nThe index contains {len(traces)} normalized evidence lines: G3-B2 optimization and G3-B3 feature completion. Normalization preserves source pointers/hashes and does not rewrite frozen history.\n\n## Provenance\n\n- G3-B2 retains historical proposal/evaluation/reflection/human records and simulated performance identity.\n- G3-B3 retains 20 proposal, 20 evaluation, and 20 reflection records; its historical Prompt/Response relationship remains unavailable.\n- New replay output is `REPLAYED_FROM_FROZEN_TRACE`, never historical execution.\n" + _tail("G3-B2 performance remains `SIMULATED_ONLY`; G3-B3 host/simulator identities remain separated.", "Normalized traces are reconstructions, not original raw Agent logs. Hidden reasoning is not included.")
    replay_doc = _header("Offline Replay Guide", "OFFLINE_REPLAY") + "## Validation Identity\n\nMandatory replay requires Python and repository files only. It does not read model API keys and does not access a network.\n\n## Commands\n\n```bash\npython -m tools.agent_delivery_cli describe\npython -m tools.agent_delivery_cli verify\npython -m tools.agent_delivery_cli replay --trace g3-b2-optimization-authoritative-round1\npython -m tools.agent_delivery_cli replay --trace g3-b3-feature-completion-agent-flow\n```\n\nA successful replay emits canonical JSON with `historical_execution=false`, `offline=true`, `network_used=false`, `api_keys_used=[]`, `runtime_api_calls=[]`, and a stable replay SHA256.\n" + _tail("Replay verifies and renders frozen decision flow; it does not rerun performance benchmarks or create historical evidence.", "Replay requires frozen repository evidence. Online DeepSeek functionality is optional and deliberately outside this path.")
    human_doc = _header("Human Intervention and Autonomy Disclosure", "HUMAN_INTERVENTION") + f"## Validation Identity\n\nG3-B2 exposes {len(disclosure['g3_b2']['records'])} frozen intervention records with actor, decision, scope, and algorithm-choice fields. G3-B3 has no complete frozen historical intervention log and is marked `HISTORICAL_TRACE_UNAVAILABLE`.\n\n## Disclosure\n\nThe supported description is: Agent-assisted proposals, deterministic evaluation, human governance, and offline replay. Human authorization is not automatically an algorithm choice. The G3-B2 record explicitly distinguishes the user, Codex development work, and the hccl-agent runtime decision path.\n" + _tail("No unsupported autonomy claim is made. Only frozen intervention records are treated as historical evidence.", "Missing historical raw conversations, provider responses, or intervention detail cannot be reconstructed. No hidden reasoning is included.")
    limitations_doc = _header("Limitations and Online LLM Boundary", "ONLINE_LLM_OPTIONAL") + "## Validation Identity\n\n`agent/llm_client.py`, `ReasoningSkill`, and online decision support remain optional. Mandatory G3-D validation does not instantiate them.\n\n## Boundaries\n\n- No real Ascend NPU, ACL/HCCL runtime, communicator, collective, MPI, `hccl_test`, or `msprof` is executed.\n- Sparse correctness is host-observed; wire bytes are modeled.\n- CRC/retry are host validated; backpressure is simulated.\n- Direct source is compile/link-only and runtime calls remain empty.\n- INT8 is deferred by its precision gate; PairWise is skipped by its value gate.\n" + _tail("All external wording resolves through the G3-C claim ledger. The weighted optimization result is a simulator result against the frozen baseline.", "Real-device acceptance remains blocked on hardware evidence. Original historical Prompt/Response data is incomplete.")
    mapping_doc = _header("Source, Commit, Evidence, and Claim Mapping", "EVIDENCE_BACKED_MAPPING") + f"## Validation Identity\n\nThe machine-readable mapping contains {mapping['relationship_count']} evidence-derived relationships across Prompt, Skill, Trace, Source, Commit, Evidence, and G3-C Claim identities. Valid commit objects are resolved explicitly; placeholders remain unavailable and are not guessed.\n\n## Mapping Rules\n\n- L1 identifies current source.\n- L2 controls public claim language.\n- L3/L4 preserve G3-B3/G3-B2 historical decisions.\n- Null historical Prompt targets are explicit unavailable relationships.\n" + _tail("A relationship proves only the stated edge and authority level. It does not imply full production-code generation provenance.", "Some G3-B2 final self-commit placeholders and G3-B3 historical Prompt relationships cannot be asserted as original records.")
    return {
        "README.md": readme,
        "01_agent_architecture_and_workflow.md": architecture,
        "02_prompt_registry_and_version_reference.md": prompt_doc,
        "03_skill_inventory.md": skill_doc,
        "04_trace_and_provenance_index.md": trace_doc,
        "05_offline_replay_guide.md": replay_doc,
        "06_human_intervention_and_autonomy_disclosure.md": human_doc,
        "07_limitations_and_online_llm_boundary.md": limitations_doc,
        "08_source_commit_evidence_claim_mapping.md": mapping_doc,
    }


def build_documentation() -> dict[str, Any]:
    mapping = build_mapping()
    disclosure = human_disclosure()
    write_json(OUTPUT_ROOT / "source_commit_evidence_claim_mapping.json", mapping)
    write_json(OUTPUT_ROOT / "human_intervention_disclosure.json", disclosure)
    for name, content in _documents(mapping, disclosure).items():
        (OUTPUT_ROOT / name).write_text(content, encoding="utf-8", newline="\n")
    return validate_documentation()


def validate_documentation() -> dict[str, Any]:
    errors: list[str] = []
    mapping = load_json(OUTPUT_ROOT / "source_commit_evidence_claim_mapping.json")
    disclosure = load_json(OUTPUT_ROOT / "human_intervention_disclosure.json")
    prompt_ids = {row["prompt_id"] for row in load_json(OUTPUT_ROOT / "prompt_registry.json")["prompts"]}
    skill_ids = {row["skill_id"] for row in load_json(OUTPUT_ROOT / "skill_registry.json")["skills"]}
    trace_ids = {row["trace_id"] for row in load_json(OUTPUT_ROOT / "trace_index.json")["traces"]}
    claim_ids = {row["claim_id"] for row in load_json(ROOT / "docs/submission/report_claim_ledger.json")["claims"]}
    for name in REQUIRED_DOCUMENTS:
        path = OUTPUT_ROOT / name
        if not path.is_file(): errors.append(f"missing document: {name}"); continue
        text = path.read_text(encoding="utf-8")
        for heading in REQUIRED_HEADINGS:
            if heading not in text: errors.append(f"missing heading {heading}: {name}")
        lowered = text.lower()
        for phrase in FORBIDDEN_WORDING:
            if phrase.lower() in lowered: errors.append(f"forbidden wording {phrase}: {name}")
        if re.search(r"(?:[A-Za-z]:\\|/home/|/Users/|/mnt/)", text): errors.append(f"absolute path: {name}")
        if re.search(r"\b(?:sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]+)\b", text): errors.append(f"secret-like token: {name}")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if "://" not in target and not (path.parent / target.split("#", 1)[0]).resolve().is_file(): errors.append(f"broken link {target}: {name}")
    relationships = mapping.get("relationships", [])
    if mapping.get("relationship_count") != len(relationships): errors.append("mapping count mismatch")
    for row in relationships:
        if row.get("provenance") not in PROVENANCE_VOCABULARY: errors.append(f"invalid mapping provenance: {row.get('relationship_id')}")
        if row["from_type"] == "PROMPT" and row["from_id"] not in prompt_ids: errors.append(f"unknown mapping prompt: {row['from_id']}")
        if row["from_type"] == "SKILL" and row["from_id"] not in skill_ids: errors.append(f"unknown mapping skill: {row['from_id']}")
        if row["from_type"] == "TRACE" and row["from_id"] not in trace_ids: errors.append(f"unknown mapping trace: {row['from_id']}")
        if row["to_type"] == "G3_C_CLAIM" and row["to_id"] not in claim_ids: errors.append(f"unknown mapping claim: {row['to_id']}")
        if row["to_type"] == "PROMPT" and row["to_id"] is None and row["provenance"] != "HISTORICAL_TRACE_UNAVAILABLE": errors.append("null Prompt relationship not unavailable")
    if disclosure.get("g3_b3", {}).get("status") != "HISTORICAL_TRACE_UNAVAILABLE": errors.append("G3-B3 human history boundary mismatch")
    if disclosure.get("hidden_chain_of_thought_included") is not False: errors.append("hidden chain disclosure invalid")
    try:
        assert_relative_repository_paths(mapping)
        assert_relative_repository_paths(disclosure)
    except ValueError as exc:
        errors.append(str(exc))
    return {
        "schema_version": "g3-d-documentation-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "document_count": len(REQUIRED_DOCUMENTS),
        "relationship_count": len(relationships),
        "human_intervention_records": len(disclosure.get("g3_b2", {}).get("records", [])),
        "sentinels": ["PROVENANCE_OK", "CLAIM_BOUNDARIES_OK"] if not errors else [],
    }

