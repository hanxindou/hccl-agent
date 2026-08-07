import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))

from agent.g3_b2_optimization_loop import REQUIRED_INPUTS,run_chain,structured_proposal
from algorithm.ablation_benchmark import AblationBenchmark,STAGES
from algorithm.topology_model import build_topology
from algorithm.topology_schedules import generate_schedule


def test_structured_agent_chain_and_proposal_contract():
    topology=build_topology("fat_tree",16);baseline=generate_schedule("Ring","AllReduce",topology,1048579)
    agent_input={"primitive":"AllReduce","message_size":1048579,"rank_size":16,"dtype":"FP32","reduce_op":"SUM","topology":topology,"hardware_profile":"g3-b2-frozen-hardware-v1","memory_budget":64*1024*1024,"reliability_state":{},"optimization_objective":{"p50":"minimize"},"baseline_schedule":baseline}
    assert REQUIRED_INPUTS<=agent_input.keys();chain=run_chain(agent_input);proposal=chain["proposal"]
    required={"proposal_id","algorithm","schedule_parameters","chunk_size","pipeline_depth","routing_policy","expected_benefit","expected_risk","unsupported_conditions","required_tests"}
    assert required<=proposal.keys();assert chain["correctness_gate"] is True;assert chain["final_selection"]["schedule_hash"]
    assert chain["evaluation"]["multi_objective"]["correctness_gate"] is True


def test_authoritative_ablation_has_fixed_matrix_all_stages_and_complete_outcomes():
    roots=sorted((ROOT/"experiments/optimization/evidence").glob("g3_b2_e_agent_*"));evidence=next(root for root in roots if json.loads((root/"result.json").read_text(encoding="utf-8")).get("authoritative"))
    ablation=json.loads((evidence/"ablation_summary.json").read_text(encoding="utf-8"));outcomes=json.loads((evidence/"wins_ties_losses.json").read_text(encoding="utf-8"));result=json.loads((evidence/"result.json").read_text(encoding="utf-8"))
    assert set(ablation["stages"])==set(STAGES);assert len(ablation["rows"])==8*18
    assert outcomes["wins"]+outcomes["ties"]+outcomes["losses"]==18
    assert len(outcomes["scenarios"])==18
    assert all({"baseline","candidate","absolute_difference_us","relative_difference_percent","p50","p95","bandwidth","memory","phase_count","schedule_hash","correctness"}<=row.keys() for row in outcomes["scenarios"])
    assert result["frozen_parameters_changed"] is False and result["benchmark_changed"] is False


def test_performance_gates_and_hashes_are_truthful():
    evidence=next(root for root in (ROOT/"experiments/optimization/evidence").glob("g3_b2_e_agent_*") if json.loads((root/"result.json").read_text(encoding="utf-8")).get("authoritative"));gates=json.loads((evidence/"performance_summary.json").read_text(encoding="utf-8"));result=json.loads((evidence/"result.json").read_text(encoding="utf-8"))
    assert gates["all_correctness"] and gates["memory_gate"] and gates["logical_1024_gate"] and gates["p95_gate"]
    expected="SATISFIED" if gates["default_performance_gate_met"] else "PARTIALLY_SATISFIED";assert result["performance_target_status"]==expected
    assert result["optimization_adjustment_rounds"]<=2


if __name__=="__main__":
    test_structured_agent_chain_and_proposal_contract()
    test_authoritative_ablation_has_fixed_matrix_all_stages_and_complete_outcomes()
    test_performance_gates_and_hashes_are_truthful()
    print("3 passed")
