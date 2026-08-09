from __future__ import annotations

import json
from pathlib import Path
import urllib.request

import pytest

from tools.agent_delivery.common import G3_B2_ROOT, G3_B3_ROOT, sha256_file
from tools.agent_delivery.trace import replay_trace, validate_traces


ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "docs/submission/agent_delivery"


def test_normalized_trace_index_and_authority_links_validate():
    result = validate_traces()
    assert result["status"] == "PASS", result["errors"]
    assert result["trace_count"] == 2
    assert result["sentinels"] == ["TRACE_INDEX_OK", "OFFLINE_REPLAY_OK"]


@pytest.mark.parametrize("trace_id", ["g3-b2-optimization-authoritative-round1", "g3-b3-feature-completion-agent-flow"])
def test_offline_replay_is_keyless_networkless_and_deterministic(monkeypatch, trace_id):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")))
    first = replay_trace(trace_id)
    second = replay_trace(trace_id)
    assert first == second
    assert first["status"] == "PASS"
    assert first["provenance_identity"] == "REPLAYED_FROM_FROZEN_TRACE"
    assert first["historical_execution"] is False
    assert first["network_used"] is False
    assert first["api_keys_used"] == []
    assert first["runtime_api_calls"] == []
    assert first["hidden_chain_of_thought_included"] is False


def test_g3_b2_performance_and_g3_b3_optional_gates_remain_frozen():
    b2 = json.loads((DELIVERY / "traces/g3_b2_optimization_trace.json").read_text(encoding="utf-8"))
    b3 = json.loads((DELIVERY / "traces/g3_b3_feature_completion_trace.json").read_text(encoding="utf-8"))
    assert b2["final_decision"]["weighted_simulated_improvement_raw_percent"] == 45.59283008
    assert b2["final_decision"]["weighted_simulated_improvement_display"] == "45.59%"
    assert [b2["final_decision"][key] for key in ("wins", "ties", "losses")] == [18, 0, 0]
    assert b2["execution_identity"] == "SIMULATED_ONLY"
    assert b3["final_decision"]["record_counts"] == {"proposal": 20, "evaluation": 20, "reflection": 20}
    assert b3["final_decision"]["int8_quantization"] == "DEFERRED_BY_PRECISION_GATE"
    assert b3["final_decision"]["pairwise"] == "SKIPPED_BY_VALUE_GATE"
    assert b3["prompt_relationship_status"] == "HISTORICAL_TRACE_UNAVAILABLE"


def test_replay_does_not_mutate_frozen_evidence():
    before = (sha256_file(G3_B2_ROOT / "SHA256SUMS"), sha256_file(G3_B3_ROOT / "SHA256SUMS"))
    replay_trace("g3-b2-optimization-authoritative-round1")
    replay_trace("g3-b3-feature-completion-agent-flow")
    after = (sha256_file(G3_B2_ROOT / "SHA256SUMS"), sha256_file(G3_B3_ROOT / "SHA256SUMS"))
    assert before == after


def test_unknown_trace_is_rejected():
    with pytest.raises(ValueError, match="unknown trace_id"):
        replay_trace("fabricated-history")

