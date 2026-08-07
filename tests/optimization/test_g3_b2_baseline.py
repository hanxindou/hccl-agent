import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.g3_b2_baseline import FREEZE_PATH, MATRIX_PATH, PROMPT_ROOT, ROOT, frozen_parameters


def test_benchmark_contract_is_frozen_and_complete():
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    performance = matrix["performance_scenarios"]
    reliability = matrix["reliability_scenarios"]
    assert matrix["frozen"] is True
    assert 12 <= len(performance) <= 20
    assert 3 <= len(reliability) <= 6
    assert {row["primitive"] for row in performance} == {"AllReduce", "AllGather", "ReduceScatter"}
    assert {row["dtype"] for row in performance} == {"FP32", "FP16", "BF16"}
    assert {row["topology_variant"] for row in performance} >= {"full_mesh_8", "ring_8", "ring_16", "fat_tree_64", "asymmetric_16", "asymmetric_64", "logical_1024"}
    assert max(row["message_size_bytes"] for row in performance) >= 1024**3
    required = {"scenario_id", "primitive", "baseline_algorithm", "topology", "ranks", "message_size_bytes", "dtype", "reduce_op", "seed", "iterations", "warmup", "metric_set", "weight"}
    assert all(required <= row.keys() for row in performance)
    assert len({row["scenario_id"] for row in performance + reliability}) == len(performance) + len(reliability)


def test_parameter_freeze_matches_sources_and_is_immutable():
    actual = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert actual == frozen_parameters()
    assert actual["frozen"] is True
    assert all(row["mutable"] is False for row in actual["parameters"])
    for row in actual["parameters"]:
        digest = hashlib.sha256((ROOT / row["source_path"]).read_bytes()).hexdigest()
        assert row["sha256"] == digest


def test_prompt_and_trace_contracts_are_versioned():
    registry = json.loads((ROOT / "agent/evidence/g3_b2/prompt_registry.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "agent/evidence/g3_b2/trace_manifest.json").read_text(encoding="utf-8"))
    assert len(registry["prompts"]) == 5
    for row in registry["prompts"]:
        path = ROOT / row["path"]
        assert path.parent == PROMPT_ROOT
        assert row["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    required = {"run_id", "timestamp", "development_agent", "runtime_agent", "prompt_id", "prompt_version", "input_schema_version", "output_schema_version", "baseline_commit", "input_hash", "proposal_hash", "human_decision", "changed_files", "tests", "benchmark_result", "reflection", "selected", "result_commit"}
    assert set(manifest["required_record_fields"]) == required


def test_phase_a_evidence_integrity():
    roots = sorted((ROOT / "experiments/optimization/evidence").glob("g3_b2_a_baseline_*"))
    assert len(roots) == 1
    evidence = roots[0]
    for line in (evidence / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == expected
    anchor = (evidence / "EVIDENCE_SHA256").read_text(encoding="utf-8").split()[0]
    assert hashlib.sha256((evidence / "SHA256SUMS").read_bytes()).hexdigest() == anchor
    result = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
    assert result["checkpoint_status"] == "COMPLETED"
    assert result["correctness_passed"] is True
    assert result["real_device_api_executed"] is False


if __name__ == "__main__":
    test_benchmark_contract_is_frozen_and_complete()
    test_parameter_freeze_matches_sources_and_is_immutable()
    test_prompt_and_trace_contracts_are_versioned()
    test_phase_a_evidence_integrity()
    print("4 passed")
