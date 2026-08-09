from __future__ import annotations

import json
from pathlib import Path

from tools.agent_delivery.registry import validate_registries


ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "docs/submission/agent_delivery"


def test_prompt_and_skill_registries_validate():
    result = validate_registries()
    assert result["status"] == "PASS", result["errors"]
    assert result["sentinels"] == ["PROMPT_REGISTRY_OK", "SKILL_REGISTRY_OK"]


def test_frozen_g3_b2_prompts_are_preserved_and_missing_history_is_explicit():
    current = json.loads((DELIVERY / "prompt_registry.json").read_text(encoding="utf-8"))
    frozen = json.loads((ROOT / "agent/evidence/g3_b2/prompt_registry.json").read_text(encoding="utf-8"))
    indexed = {row["prompt_id"]: row for row in current["prompts"]}
    for row in frozen["prompts"]:
        assert indexed[row["prompt_id"]]["current_canonical_version"] == row["version"]
        assert indexed[row["prompt_id"]]["source_sha256"] == row["sha256"]
    unavailable = [row for row in current["prompts"] if row["historical_version_status"] == "HISTORICAL_TRACE_UNAVAILABLE"]
    assert unavailable
    assert all(row["source_commit"] is None for row in unavailable)


def test_online_prompts_and_skills_are_optional_not_mandatory():
    prompts = json.loads((DELIVERY / "prompt_registry.json").read_text(encoding="utf-8"))["prompts"]
    skills = json.loads((DELIVERY / "skill_registry.json").read_text(encoding="utf-8"))["skills"]
    online_prompts = [row for row in prompts if row["online_offline_classification"] == "ONLINE_LLM_OPTIONAL"]
    online_skills = [row for row in skills if row["online_dependency"]]
    assert online_prompts and online_skills
    assert all("not used by mandatory G3-D replay" in row["limitations"] for row in online_prompts)
    assert all(row["deterministic_classification"] == "OPTIONAL_ONLINE" for row in online_skills)


def test_skill_registry_uses_real_source_and_test_mappings():
    skills = json.loads((DELIVERY / "skill_registry.json").read_text(encoding="utf-8"))["skills"]
    assert skills
    for row in skills:
        assert (ROOT / row["source_path"]).is_file()
        assert all((ROOT / path).is_file() for path in row["tests"])
        if not row["tests"]:
            assert row["status"] == "PARTIAL"
            assert "no focused test mapping discovered" in row["limitations"]

