import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_single_g3_b3_final_evidence_is_complete_and_hash_valid():
    roots = sorted((ROOT / "experiments/feature_completion/evidence").glob("g3_b3_f_final_*"))
    assert len(roots) == 1
    evidence = roots[0]
    required = {
        "README.md", "manifest.json", "result.json", "g3_b2_baseline_reference.json",
        "g3_b3_baseline_reference.json", "schedule_ir_v2_audit.json", "agent_proposal_v2_audit.json",
        "sparse_support_matrix.json", "sparse_correctness.json", "sparse_c_python_parity.json",
        "sparse_benchmark.json", "sparse_break_even.json", "dense_fallback_audit.json",
        "bounded_sparse_memory.json", "integrity_manifest.json", "crc_audit.json",
        "corruption_audit.json", "retry_audit.json", "timeout_audit.json",
        "failure_classification.json", "flow_control_audit.json", "backpressure_audit.json",
        "agent_trace_inventory.json", "feature_ablation.json", "direct_runtime_source_manifest.json",
        "official_api_call_expression_audit.json", "direct_compile_link_audit.json",
        "cpu_sim_isolation_audit.json", "native_elf_audit.json", "reproducible_build.json",
        "submission_regression.json", "staging_verification.json", "claim_boundary_audit.json",
        "requirement_delta.json", "user_action_required.json", "SHA256SUMS",
    }
    assert required <= {path.name for path in evidence.iterdir()}
    for line in (evidence / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == expected
    result = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
    assert result["checkpoint_status"] == "COMPLETED"
    assert result["real_device_acceptance"] == "HARDWARE_BLOCKED"
    assert result["real_device_api_executed"] is False
    assert result["runtime_api_calls"] == []


def test_final_baseline_preserves_public_and_g3_b2_contracts():
    baseline = json.loads((ROOT / "experiments/feature_completion/g3_b3_final_baseline.json").read_text(encoding="utf-8"))
    assert baseline["frozen_contracts"]["exported_symbol_count"] == 19
    assert baseline["frozen_contracts"]["soname"] == "libhccl_plugin.so"
    assert baseline["g3_b2_preserved"] == {
        "performance_scenarios": 18,
        "correctness_failures": 0,
        "invalid_runs": 0,
        "best_simulated_improvement_percent": 45.59283008,
    }
