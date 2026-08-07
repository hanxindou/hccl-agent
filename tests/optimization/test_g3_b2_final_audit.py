from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_final_evidence_contract() -> None:
    required = {
        "README.md", "manifest.json", "result.json", "baseline_reference.json", "parameter_freeze.json",
        "benchmark_contract.json", "algorithm_support_matrix.json", "schedule_schema.json", "schedule_inventory.json",
        "schedule_invariant_audit.json", "c_python_parity_audit.json", "correctness_summary.json",
        "performance_summary.json", "scale_summary.json", "memory_summary.json", "pipeline_summary.json",
        "reliability_summary.json", "replan_trace.jsonl", "ablation_summary.json", "wins_ties_losses.json",
        "agent_trace_inventory.json", "human_intervention.json", "commit_mapping.json", "submission_regression.json",
        "claim_boundary_audit.json", "SHA256SUMS",
    }
    assert {path.name for path in EVIDENCE.iterdir() if path.is_file()} == required
    result = json.loads((EVIDENCE / "result.json").read_text(encoding="utf-8"))
    assert result["checkpoint_status"] == "COMPLETED"
    assert result["performance_target_achievement"] == "PARTIALLY_SATISFIED"
    assert result["real_device_acceptance"] == "HARDWARE_BLOCKED"
    assert result["runtime_api_calls"] == []
    assert result["parameter_set_modified"] is False
    for line in (EVIDENCE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(None, 1)
        assert _sha256(EVIDENCE / name.lstrip(" *")) == digest


def test_final_baseline_and_delta_truth_boundary() -> None:
    baseline = json.loads((ROOT / "experiments/optimization/g3_b2_final_baseline.json").read_text(encoding="utf-8"))
    assert baseline["freeze_status"] == "FROZEN"
    assert baseline["final_source_commit"] == "efd946c47ec626d996667ab941a1acf598157ce0"
    assert len(baseline["final_exported_symbols"]) == 19
    delta = json.loads((ROOT / "docs/submission/g3_b2_requirement_delta.json").read_text(encoding="utf-8"))
    assert delta["base_matrix_modified"] is False
    assert len(delta["deltas"]) == 9
    assert {row["suggested_status"] for row in delta["deltas"]} == {"PARTIALLY_SATISFIED"}


if __name__ == "__main__":
    test_final_evidence_contract()
    test_final_baseline_and_delta_truth_boundary()
    print("2 passed")
