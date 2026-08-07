import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from algorithm.chunk_policy import CHUNK_CANDIDATES, select_chunk
from algorithm.schedule_selector import select_schedule
from algorithm.schedule_ir import validate_schedule
from algorithm.topology_model import build_topology
from algorithm.topology_schedules import SUPPORT_MATRIX, UnsupportedAlgorithmPrimitivePair, generate_schedule, nhr_order
from simulator.collective_correctness import Case, run_case


def test_algorithm_support_matrix_and_structured_rejection():
    assert SUPPORT_MATRIX == {
        "Ring":{"AllReduce","AllGather","ReduceScatter"},
        "Butterfly":{"AllReduce","AllGather"},
        "Mesh":{"AllReduce","ReduceScatter"},
        "NHR":{"AllReduce"},
        "Hierarchical":{"AllReduce"},
    }
    topology = build_topology("full_mesh", 8)
    try:
        generate_schedule("NHR", "AllGather", topology, 65536)
    except UnsupportedAlgorithmPrimitivePair as error:
        assert error.code == "UNSUPPORTED_ALGORITHM_PRIMITIVE_PAIR"
    else:
        raise AssertionError("unsupported pair did not fail")


def test_butterfly_recursive_doubling_and_power_of_two_boundary():
    schedule = generate_schedule("Butterfly", "AllReduce", build_topology("full_mesh", 8), 262147)
    assert validate_schedule(schedule)
    assert len(schedule["phases"]) == 3
    for step, phase in enumerate(schedule["phases"]):
        assert all(transfer["destination_rank"] == transfer["source_rank"] ^ (1 << step) for transfer in phase["transfers"])
        assert all(transfer["operation"] == "REDUCE" for transfer in phase["transfers"])
    try:
        generate_schedule("Butterfly", "AllReduce", build_topology("full_mesh", 6), 65536)
    except ValueError as error:
        assert str(error) == "BUTTERFLY_REQUIRES_POWER_OF_TWO"
    else:
        raise AssertionError("non-power-of-two Butterfly was accepted")


def test_nhr_uses_weighted_non_uniform_order_and_symmetric_explanation():
    symmetric = build_topology("full_mesh", 8)
    order, segments = nhr_order(symmetric, 65536)
    assert order == list(range(8))
    assert len(segments) == 8
    asymmetric = build_topology("asymmetric", 16)
    schedule = generate_schedule("NHR", "AllReduce", asymmetric, 1048579)
    assert validate_schedule(schedule)
    metadata = schedule["optimization_metadata"]
    assert sorted(metadata["non_uniform_ring_order"]) == list(range(16))
    assert metadata["weight_formula"] == "latency_cost + transfer_bytes/effective_bandwidth + congestion_penalty + reliability_penalty"
    assert all("estimated_cost" in segment for segment in metadata["segment_costs"])


def test_hierarchical_schedule_uses_explicit_node_metadata():
    topology = build_topology("fat_tree", 64)
    schedule = generate_schedule("Hierarchical", "AllReduce", topology, 16 * 1024 * 1024 + 3)
    assert validate_schedule(schedule)
    assert [phase["phase_type"] for phase in schedule["phases"]] == ["INTRA_GROUP_REDUCE","INTER_GROUP_ALLREDUCE","INTRA_GROUP_DISTRIBUTE"]
    metadata = schedule["optimization_metadata"]
    assert metadata["group_source"] == "explicit node metadata"
    assert metadata["leaders"] == list(range(0,64,8))
    assert metadata["fallback_condition"] == "NONE; structured failure"


def test_mesh_fanout_conflict_and_non_full_mesh_constraints():
    full = generate_schedule("Mesh", "ReduceScatter", build_topology("full_mesh", 8), 1048583)
    assert full["optimization_metadata"]["fanout_limit"] == 4
    for phase in full["phases"]:
        links = [transfer["link_id"] for transfer in phase["transfers"]]
        assert len(links) > len(set(links))  # chunks share one route intentionally
        assert len(set(links)) <= 8 * 4
    constrained = generate_schedule("Mesh", "AllReduce", build_topology("fat_tree", 16), 262147)
    assert constrained["optimization_metadata"]["fanout_limit"] == 2
    assert constrained["optimization_metadata"]["detected_conflicts_serialized"] > 0
    assert validate_schedule(constrained)


def test_chunk_candidates_are_finite_versioned_and_cost_is_auditable():
    decision = select_chunk(128*1024*1024,64,6,25.0,0.014,8,64*1024*1024)
    assert tuple(row["chunk_size"] for row in decision["candidate_scores"]) == CHUNK_CANDIDATES
    assert decision["chunk_size"] in CHUNK_CANDIDATES
    schedule = generate_schedule("Hierarchical","AllReduce",build_topology("asymmetric",16),4*1024*1024+3)
    assert all({"base_link_time","congestion_penalty","final_link_time"} <= phase["cost"].keys() for phase in schedule["phases"])


def test_selector_returns_explicit_candidates_hashes_scores_and_none_fallback():
    result = select_schedule("AllReduce",build_topology("asymmetric",16),1048579)
    assert result["selected_algorithm"] in result["candidate_algorithms"]
    assert result["selected_schedule_hash"] in result["candidate_schedule_hashes"]
    assert result["candidate_scores"]
    assert result["fallback"] == "NONE"
    unsupported = select_schedule("AllGather",build_topology("fat_tree",16),65539)
    assert {row["algorithm"] for row in unsupported["rejected_reasons"]} >= {"Mesh","NHR","Hierarchical"}


def test_every_supported_candidate_passes_semantic_correctness_gate():
    for algorithm, primitives in SUPPORT_MATRIX.items():
        for primitive in primitives:
            rank_size = 16 if algorithm == "Hierarchical" else 8
            topology = build_topology("fat_tree" if algorithm == "Hierarchical" else "full_mesh", rank_size)
            schedule = generate_schedule(algorithm, primitive, topology, 65539)
            assert validate_schedule(schedule)
            outcome = run_case(Case(primitive,"FP32",None if primitive=="AllGather" else "SUM",rank_size,"FAT_TREE" if algorithm=="Hierarchical" else "FULL_MESH","schedule_gate",65539,20260804),exact=True)
            assert outcome["exact_match"] and outcome["within_dtype_tolerance"]


if __name__ == "__main__":
    test_algorithm_support_matrix_and_structured_rejection()
    test_butterfly_recursive_doubling_and_power_of_two_boundary()
    test_nhr_uses_weighted_non_uniform_order_and_symmetric_explanation()
    test_hierarchical_schedule_uses_explicit_node_metadata()
    test_mesh_fanout_conflict_and_non_full_mesh_constraints()
    test_chunk_candidates_are_finite_versioned_and_cost_is_auditable()
    test_selector_returns_explicit_candidates_hashes_scores_and_none_fallback()
    test_every_supported_candidate_passes_semantic_correctness_gate()
    print("8 passed")
