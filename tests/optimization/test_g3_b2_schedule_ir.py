import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from algorithm.ring_schedule import generate_ring_schedule
from algorithm.schedule_ir import canonical_schedule_json, invariant_results, schedule_hash, validate_schedule


def test_ring_schedule_matrix_and_non_divisible_boundaries():
    for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
        for ranks in (2, 4, 8, 16, 64):
            for size in (ranks * 4, ranks * 4 + 3):
                schedule = generate_ring_schedule(primitive, ranks, size)
                assert validate_schedule(schedule)
                assert schedule["chunk_count"] == ranks
                assert schedule["schedule_hash"] == schedule_hash(schedule)
                expected_phases = 2 * (ranks - 1) if primitive == "AllReduce" else ranks - 1
                assert len(schedule["phases"]) == expected_phases
                assert all(row["passed"] for row in invariant_results(schedule))


def test_allreduce_has_explicit_reduce_scatter_then_all_gather():
    schedule = generate_ring_schedule("AllReduce", 8, 65539, dtype="BF16")
    kinds = [phase["phase_type"] for phase in schedule["phases"]]
    assert kinds == ["REDUCE_SCATTER"] * 7 + ["ALL_GATHER"] * 7
    assert schedule["reduce_op"] == "SUM"
    assert schedule["memory_plan"]["peak_materialized_bytes"] < schedule["message_size_bytes"]


def test_c_python_schedule_parity():
    executable = ROOT / "build/g3_b2_b/schedule_ir_dump"
    if sys.platform == "win32":
        executable = executable.with_suffix(".exe")
    if not executable.exists():
        return
    for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
        for ranks, size in ((2, 9), (4, 19), (8, 65539), (16, 1048583), (64, 4194313)):
            completed = subprocess.run([str(executable), primitive, str(ranks), str(size), "FP32", "SUM"], check=True, capture_output=True, text=True)
            observed = json.loads(completed.stdout)
            expected = generate_ring_schedule(primitive, ranks, size)
            assert observed == expected
            assert canonical_schedule_json(observed) == canonical_schedule_json(expected)


if __name__ == "__main__":
    test_ring_schedule_matrix_and_non_divisible_boundaries()
    test_allreduce_has_explicit_reduce_scatter_then_all_gather()
    test_c_python_schedule_parity()
    print("3 passed")
