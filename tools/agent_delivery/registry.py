"""Build and validate current canonical Prompt and Skill registries."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .authority import PROVENANCE_VOCABULARY
from .common import OUTPUT_ROOT, ROOT, assert_relative_repository_paths, load_json, sha256_file, tracked_files, write_json


PROMPT_SCHEMA = "g3-d-prompt-registry-v1"
SKILL_SCHEMA = "g3-d-skill-registry-v1"
SKILL_CLASSIFICATIONS = {"DETERMINISTIC", "OPTIONAL_ONLINE", "HOST_EXECUTED", "SIMULATOR_MODEL", "DELIVERY_ONLY"}


def _prompt(
    prompt_id: str,
    source_path: str,
    *,
    version: str,
    historical: str,
    purpose: str,
    owner: str,
    input_contract: Any,
    output_contract: Any,
    skills: list[str],
    classification: str,
    provenance: str,
    source_commit: str | None,
    evidence: list[str],
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "prompt_id": prompt_id,
        "current_canonical_version": version,
        "historical_version_status": historical,
        "purpose": purpose,
        "source_path": source_path,
        "source_sha256": sha256_file(ROOT / source_path),
        "owning_stage": owner,
        "owning_module": source_path,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "referenced_skills": skills,
        "online_offline_classification": classification,
        "provenance": provenance,
        "source_commit": source_commit,
        "evidence_pointer": evidence,
        "tests": [],
        "limitations": limitations or [],
    }


def prompt_registry() -> dict[str, Any]:
    frozen = load_json(ROOT / "agent/evidence/g3_b2/prompt_registry.json")
    frozen_details = {
        "g3-b2-schedule-generation": ("Generate bounded collective Schedule IR candidates.", "g3-b2-schedule-request-v1", "g3-b2-schedule-proposal-v1", ["g3-b2-loop"]),
        "g3-b2-topology-optimization": ("Propose topology-aware hierarchical non-uniform schedules.", "g3-b2-topology-optimization-input-v1", "g3-b2-schedule-proposal-v1", ["g3-b2-loop"]),
        "g3-b2-benchmark-evaluation": ("Evaluate candidates against the immutable G3-B2 benchmark contract.", "g3-b2-evaluation-input-v1", "g3-b2-evaluation-result-v1", ["g3-b2-loop", "benchmark-skill"]),
        "g3-b2-reflection": ("Explain benchmark outcomes and one bounded adjustment round.", "g3-b2-evaluation-result-v1", "g3-b2-reflection-v1", ["reflection-skill"]),
        "g3-b2-replanning": ("Replan after a structured topology event.", "g3-b2-replan-request-v1", "g3-b2-replan-result-v1", ["replanning-skill"]),
    }
    prompts: list[dict[str, Any]] = []
    for row in frozen["prompts"]:
        purpose, input_contract, output_contract, skills = frozen_details[row["prompt_id"]]
        prompts.append(_prompt(
            row["prompt_id"], row["path"], version=row["version"],
            historical="AVAILABLE_IN_FROZEN_EVIDENCE", purpose=purpose,
            owner="G3-B2", input_contract=input_contract, output_contract=output_contract,
            skills=skills, classification="OFFLINE_REPLAY", provenance="HISTORICAL_EVIDENCE",
            source_commit="efd946c47ec626d996667ab941a1acf598157ce0",
            evidence=["experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/agent_trace_inventory.json"],
        ))

    algorithm_source = "prompts/algorithm_prompt.txt"
    algorithm_version = "sha256:" + sha256_file(ROOT / algorithm_source)[:16]
    current_sections = (
        ("current-algorithm-selection", "Current algorithm-selection template section.", ["algorithm-skill", "optimization-skill"], "scenario parameters", "recommendation fields"),
        ("current-code-generation", "Current code-generation template section.", ["code-generation-skill"], "algorithm specification", "C/C++ text"),
        ("current-test-generation", "Current test-generation template section.", ["code-generation-skill"], "generated code and primitive", "test source text"),
        ("current-performance-analysis", "Current performance-analysis template section.", ["benchmark-skill", "evaluation-skill"], "logs and baseline", "analysis text"),
        ("current-reliability-generation", "Current reliability template section.", ["reasoning-skill"], "algorithm and link parameters", "reliability design text"),
    )
    for prompt_id, purpose, skills, input_contract, output_contract in current_sections:
        prompts.append(_prompt(
            prompt_id, algorithm_source, version=algorithm_version,
            historical="HISTORICAL_TRACE_UNAVAILABLE", purpose=purpose,
            owner="CURRENT_CANONICAL", input_contract=input_contract,
            output_contract=output_contract, skills=skills,
            classification="TEMPLATE_ONLY", provenance="HISTORICAL_TRACE_UNAVAILABLE",
            source_commit=None, evidence=[],
            limitations=["current canonical source only; no original historical invocation record", "template wording is not evidence of implemented or real-device capability"],
        ))

    for prompt_id, path, purpose, owner_skill in (
        ("current-online-reasoning-inline", "agent/reasoning_skill.py", "Optional DeepSeek scenario reasoning prompt.", "reasoning-skill"),
        ("current-online-decision-inline", "agent/decision_skill.py", "Optional DeepSeek candidate decision prompt.", "decision-skill"),
    ):
        prompts.append(_prompt(
            prompt_id, path, version="sha256:" + sha256_file(ROOT / path)[:16],
            historical="HISTORICAL_TRACE_UNAVAILABLE", purpose=purpose,
            owner="CURRENT_CANONICAL", input_contract="runtime scenario dictionary",
            output_contract="provider text parsed into an advisory result", skills=[owner_skill],
            classification="ONLINE_LLM_OPTIONAL", provenance="ONLINE_LLM_OPTIONAL",
            source_commit=None, evidence=[],
            limitations=["not used by mandatory G3-D replay", "no historical raw provider response is asserted"],
        ))
    return {
        "schema_version": PROMPT_SCHEMA,
        "status": "CURRENT_CANONICAL_WITH_FROZEN_G3_B2_HISTORY",
        "historical_version_policy": "never invent missing historical versions",
        "prompts": sorted(prompts, key=lambda row: row["prompt_id"]),
    }


def _public_callables(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            values.append(node.name)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            values.append(node.name)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_"):
                    values.append(f"{node.name}.{child.name}")
    return values


def _doc_purpose(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    doc = ast.get_docstring(tree) or "Current repository module; purpose derived from source symbols."
    return doc.splitlines()[0].strip()


def _test_mappings(source_path: str, callables: list[str]) -> list[str]:
    stem = Path(source_path).stem
    candidates = []
    for test in tracked_files(("tests",)):
        if not test.endswith(".py"):
            continue
        if stem in Path(test).stem:
            candidates.append(test)
            continue
        text = (ROOT / test).read_text(encoding="utf-8", errors="ignore")
        module = source_path[:-3].replace("/", ".")
        if module in text or any(name.split(".", 1)[0] in text for name in callables):
            candidates.append(test)
    return sorted(set(candidates))


def _skill_id(path: str) -> str:
    return Path(path).stem.replace("_", "-")


def _classification(path: str, text: str) -> str:
    if "LLMClient" in text or ".client.ask(" in text:
        return "OPTIONAL_ONLINE"
    if any(token in path for token in ("execution_skill", "benchmark_skill")):
        return "HOST_EXECUTED"
    if path.startswith("skills/") and any(token in path for token in ("performance", "topology", "optimization", "strategy")):
        return "SIMULATOR_MODEL"
    return "DETERMINISTIC"


def skill_registry(prompts: dict[str, Any]) -> dict[str, Any]:
    paths = [path for path in tracked_files(("agent", "skills")) if path.endswith("_skill.py") or path in ("agent/g3_b2_optimization_loop.py", "agent/g3_b3_feature_loop.py", "agent/autonomous_development_loop.py")]
    prompt_dependencies: dict[str, list[str]] = {}
    for prompt in prompts["prompts"]:
        for skill in prompt["referenced_skills"]:
            prompt_dependencies.setdefault(skill, []).append(prompt["prompt_id"])
    skills = []
    for source_path in paths:
        path = ROOT / source_path
        text = path.read_text(encoding="utf-8")
        callables = _public_callables(path)
        classification = _classification(source_path, text)
        skill_id = _skill_id(source_path)
        tests = _test_mappings(source_path, callables)
        evidence: list[str] = []
        if source_path == "agent/g3_b2_optimization_loop.py":
            evidence = ["experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z/agent_trace_inventory.json"]
        elif source_path == "agent/g3_b3_feature_loop.py":
            evidence = ["experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z/agent_trace_inventory.json"]
        stage = "reasoning" if "reasoning" in source_path else "reflection" if "reflection" in source_path else "replanning" if "replanning" in source_path else "evaluation" if "evaluation" in source_path else "execution" if "execution" in source_path else "planning" if "planning" in source_path else "support"
        skills.append({
            "skill_id": skill_id,
            "name": callables[0] if callables else Path(source_path).stem,
            "source_path": source_path,
            "source_sha256": sha256_file(path),
            "purpose": _doc_purpose(path),
            "inputs": {"contract_source": "public callable signatures", "callables": callables},
            "outputs": {"contract_source": "source implementation and mapped tests"},
            "deterministic_classification": classification,
            "side_effects": ["see authority inventory"] if source_path in ("agent/benchmark_skill.py",) else [],
            "online_dependency": classification == "OPTIONAL_ONLINE",
            "agent_stage": stage,
            "prompt_dependency": sorted(prompt_dependencies.get(skill_id, [])),
            "tests": tests,
            "frozen_evidence": evidence,
            "status": "CURRENT_IMPLEMENTED" if tests else "PARTIAL",
            "provenance": "ONLINE_LLM_OPTIONAL" if classification == "OPTIONAL_ONLINE" else "DETERMINISTIC_EVALUATION",
            "limitations": (["not part of mandatory offline replay"] if classification == "OPTIONAL_ONLINE" else []) + (["no focused test mapping discovered"] if not tests else []),
        })
    return {
        "schema_version": SKILL_SCHEMA,
        "status": "CURRENT_SOURCE_REGISTRY",
        "implementation_rule": "source and tests, never roadmap or filename alone",
        "skills": sorted(skills, key=lambda row: row["skill_id"]),
    }


def build_registries() -> dict[str, Any]:
    prompts = prompt_registry()
    skills = skill_registry(prompts)
    write_json(OUTPUT_ROOT / "prompt_registry.json", prompts)
    write_json(OUTPUT_ROOT / "skill_registry.json", skills)
    prompt_lines = ["# G3-D Prompt Registry", "", "Current canonical Prompt sources and frozen G3-B2 Prompt identities. Missing history remains `HISTORICAL_TRACE_UNAVAILABLE`.", "", "| Prompt ID | Version | Classification | Historical status | Source |", "| --- | --- | --- | --- | --- |"]
    for row in prompts["prompts"]:
        prompt_lines.append(f"| `{row['prompt_id']}` | `{row['current_canonical_version']}` | `{row['online_offline_classification']}` | `{row['historical_version_status']}` | `{row['source_path']}` |")
    (OUTPUT_ROOT / "prompt_registry.md").write_text("\n".join(prompt_lines) + "\n", encoding="utf-8", newline="\n")
    skill_lines = ["# G3-D Skill Registry", "", "Only current source-backed modules are listed. `PARTIAL` means no focused test mapping was discovered; it is not upgraded by roadmap text.", "", "| Skill ID | Classification | Status | Source | Tests |", "| --- | --- | --- | --- | --- |"]
    for row in skills["skills"]:
        skill_lines.append(f"| `{row['skill_id']}` | `{row['deterministic_classification']}` | `{row['status']}` | `{row['source_path']}` | {len(row['tests'])} |")
    (OUTPUT_ROOT / "skill_registry.md").write_text("\n".join(skill_lines) + "\n", encoding="utf-8", newline="\n")
    return validate_registries()


def validate_registries() -> dict[str, Any]:
    prompts = load_json(OUTPUT_ROOT / "prompt_registry.json")
    skills = load_json(OUTPUT_ROOT / "skill_registry.json")
    errors: list[str] = []
    if prompts.get("schema_version") != PROMPT_SCHEMA: errors.append("prompt schema mismatch")
    if skills.get("schema_version") != SKILL_SCHEMA: errors.append("skill schema mismatch")
    prompt_ids = [row.get("prompt_id") for row in prompts.get("prompts", [])]
    skill_ids = [row.get("skill_id") for row in skills.get("skills", [])]
    if len(prompt_ids) != len(set(prompt_ids)): errors.append("duplicate prompt_id")
    if len(skill_ids) != len(set(skill_ids)): errors.append("duplicate skill_id")
    frozen = {row["prompt_id"]: row for row in load_json(ROOT / "agent/evidence/g3_b2/prompt_registry.json")["prompts"]}
    registered = {row["prompt_id"]: row for row in prompts.get("prompts", [])}
    for prompt_id, row in frozen.items():
        current = registered.get(prompt_id)
        if not current: errors.append(f"missing frozen prompt: {prompt_id}"); continue
        if current["current_canonical_version"] != row["version"] or current["source_sha256"] != row["sha256"]: errors.append(f"frozen prompt mismatch: {prompt_id}")
    for row in prompts.get("prompts", []):
        path = ROOT / row.get("source_path", "")
        if not path.is_file() or sha256_file(path) != row.get("source_sha256"): errors.append(f"prompt source/hash mismatch: {row.get('prompt_id')}")
        if not row.get("input_contract") or not row.get("output_contract"): errors.append(f"prompt contract missing: {row.get('prompt_id')}")
        if row.get("provenance") not in PROVENANCE_VOCABULARY: errors.append(f"prompt provenance invalid: {row.get('prompt_id')}")
        if row.get("online_offline_classification") == "ONLINE_LLM_OPTIONAL" and "not used by mandatory G3-D replay" not in row.get("limitations", []): errors.append(f"online boundary missing: {row.get('prompt_id')}")
    for row in skills.get("skills", []):
        path = ROOT / row.get("source_path", "")
        if not path.is_file() or sha256_file(path) != row.get("source_sha256"): errors.append(f"skill source/hash mismatch: {row.get('skill_id')}")
        if row.get("deterministic_classification") not in SKILL_CLASSIFICATIONS: errors.append(f"skill classification invalid: {row.get('skill_id')}")
        if row.get("provenance") not in PROVENANCE_VOCABULARY: errors.append(f"skill provenance invalid: {row.get('skill_id')}")
        for test in row.get("tests", []):
            if not (ROOT / test).is_file(): errors.append(f"skill test missing: {test}")
        if row.get("online_dependency") and row.get("deterministic_classification") != "OPTIONAL_ONLINE": errors.append(f"online classification mismatch: {row.get('skill_id')}")
    try:
        assert_relative_repository_paths(prompts)
        assert_relative_repository_paths(skills)
    except ValueError as exc:
        errors.append(str(exc))
    return {
        "schema_version": "g3-d-registry-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "prompt_count": len(prompt_ids),
        "skill_count": len(skill_ids),
        "sentinels": ["PROMPT_REGISTRY_OK", "SKILL_REGISTRY_OK"] if not errors else [],
    }

