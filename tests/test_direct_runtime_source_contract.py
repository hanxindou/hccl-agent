import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hcccl/direct/src/hccl_direct_runtime_source.cpp"
CMAKE = ROOT / "hcccl/CMakeLists.txt"
REQUIRED_CALLS = (
    "aclInit", "aclrtSetDevice", "aclrtCreateContext", "aclrtCreateStream",
    "aclrtMalloc", "aclrtMemcpy", "HcclCommInitClusterInfo",
    "HcclAllReduce", "HcclAllGather", "HcclReduceScatter",
    "aclrtSynchronizeStream", "HcclCommDestroy", "aclrtFree",
    "aclrtDestroyStream", "aclrtDestroyContext", "aclrtResetDevice", "aclFinalize",
)


def test_source_contains_actual_official_calls_and_runtime_guard():
    source = SOURCE.read_text(encoding="utf-8")
    for name in REQUIRED_CALLS:
        assert re.search(rf"\b{re.escape(name)}\s*\(", source), name
    assert "int main(" not in source
    assert source.index("execution_authorization_token != kRuntimeAuthorizationToken") < source.index("aclInit(nullptr)")
    assert "THIS SOURCE IS NOT EXECUTED IN HOST-ONLY ACCEPTANCE" in source


def test_cleanup_order_first_error_and_no_double_free_guards():
    source = SOURCE.read_text(encoding="utf-8")
    expressions = (
        "HcclCommDestroy(comm)", "aclrtFree(device_recv)", "aclrtFree(device_send)",
        "aclrtDestroyStream(stream)", "aclrtDestroyContext(context)",
        "aclrtResetDevice(request->device_id)", "aclFinalize()",
    )
    offsets = [source.index(expression) for expression in expressions]
    assert offsets == sorted(offsets)
    assert "result->first_failed_api == nullptr" in source
    for marker in (
        "comm_created = false", "recv_allocated = false", "send_allocated = false",
        "stream_created = false", "context_created = false", "device_set = false",
        "runtime_initialized = false",
    ):
        assert marker in source


def test_cmake_target_is_default_off_isolated_and_not_a_test():
    cmake = CMAKE.read_text(encoding="utf-8")
    assert re.search(r"option\(HCCL_ENABLE_ASCEND_HCCL_RUNTIME_SOURCE[\s\S]*?\n\s*OFF\)", cmake)
    assert "add_library(hccl_direct_runtime_source SHARED" in cmake
    assert "add_test(NAME hccl_direct_runtime_source" not in cmake
    source_block = cmake[cmake.index("set(SOURCES"):cmake.index("set(HEADERS")]
    assert "hccl_direct_runtime_source" not in source_block


def test_submission_cli_cannot_execute_direct_runtime_source():
    for path in (ROOT / "tools/submission_cli").rglob("*.py"):
        assert "hccl_direct_runtime_source" not in path.read_text(encoding="utf-8")


def test_g3_b3_e_authority_evidence_is_complete_and_hash_valid():
    roots = sorted((ROOT / "experiments/feature_completion/evidence").glob("g3_b3_e_direct_runtime_*"))
    assert len(roots) == 1
    evidence = roots[0]
    required = {
        "direct_runtime_source_manifest.json", "official_api_call_expression_audit.json",
        "compile_result.json", "link_result.json", "elf_needed.json", "symbol_audit.json",
        "execution_guard_audit.json", "cleanup_path_audit.json", "cpu_sim_isolation_audit.json",
        "truth_boundary_audit.json", "SHA256SUMS",
    }
    assert required <= {path.name for path in evidence.iterdir()}
    for line in (evidence / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == expected
    result = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
    calls = json.loads((evidence / "official_api_call_expression_audit.json").read_text(encoding="utf-8"))
    isolation = json.loads((evidence / "cpu_sim_isolation_audit.json").read_text(encoding="utf-8"))
    truth = json.loads((evidence / "truth_boundary_audit.json").read_text(encoding="utf-8"))
    assert result["checkpoint_status"] == "COMPLETED"
    assert result["official_api_call_expressions"] == "PRESENT"
    assert result["execution"] == "NOT_EXECUTED"
    assert calls["status"] == "PASS" and all(row["matches"] for row in calls["calls"])
    assert isolation["exact_19_symbol_allowlist"] is True
    assert isolation["needed"] == ["libc.so.6"]
    assert truth["runtime_api_calls"] == []
    assert truth["real_device_api_executed"] is False
