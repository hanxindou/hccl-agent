"""Replayable G3-B2 runtime-agent schedule optimization chain."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from algorithm.replanner import replan
from algorithm.schedule_ir import validate_schedule
from algorithm.schedule_selector import select_schedule
from simulator.collective_correctness import Case, run_case


REQUIRED_INPUTS={"primitive","message_size","rank_size","dtype","reduce_op","topology","hardware_profile","memory_budget","reliability_state","optimization_objective","baseline_schedule"}


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()


def structured_proposal(agent_input: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    if not REQUIRED_INPUTS<=agent_input.keys():raise ValueError(f"missing agent inputs: {sorted(REQUIRED_INPUTS-agent_input.keys())}")
    schedule=decision.get("selected_schedule")
    if schedule is None:
        return {"proposal_id":f"proposal-{_hash(agent_input)[:16]}","algorithm":None,"schedule_parameters":None,"chunk_size":None,"pipeline_depth":None,"routing_policy":None,"expected_benefit":"none","expected_risk":"NO_VALID_CANDIDATE","unsupported_conditions":decision["rejected_reasons"],"required_tests":["no-path semantics"],"proposal_hash":_hash(decision)}
    proposal={"proposal_id":f"proposal-{schedule['schedule_hash'][:16]}","algorithm":decision["selected_algorithm"],"schedule_parameters":{"schedule_hash":schedule["schedule_hash"],"phase_count":len(schedule["phases"]),"rank_size":schedule["rank_size"]},"chunk_size":schedule["chunk_size_bytes"],"pipeline_depth":schedule.get("chunk_selection",{}).get("pipeline_depth",1),"routing_policy":schedule.get("optimization_metadata",{}).get("weight_formula",schedule["algorithm"]),"expected_benefit":"minimum explicit multi-objective analytical score","expected_risk":"simulator model is not hardware calibrated","unsupported_conditions":decision["rejected_reasons"],"required_tests":["schedule invariants","semantic correctness","frozen benchmark","bounded memory","reliability/no-path"]}
    proposal["proposal_hash"]=_hash(proposal);return proposal


def run_chain(agent_input: dict[str, Any]) -> dict[str, Any]:
    decision=select_schedule(agent_input["primitive"],agent_input["topology"],agent_input["message_size"],agent_input["dtype"],agent_input["reduce_op"],agent_input["memory_budget"])
    proposal=structured_proposal(agent_input,decision);schedule=decision.get("selected_schedule")
    if schedule is None:
        return {"input":agent_input,"analysis":{"topology_hash":agent_input["topology"]["topology_hash"],"candidate_count":0},"candidates":decision,"proposal":proposal,"correctness_gate":False,"evaluation":{"selected":False,"reason":"NO_VALID_CANDIDATE"},"reflection":{"action":"retain explicit failure"},"replanning":None,"final_selection":None}
    validate_schedule(schedule)
    topology_name={"full_mesh":"FULL_MESH","ring":"RING","fat_tree":"FAT_TREE","asymmetric":"HETEROGENEOUS"}[agent_input["topology"]["variant"]]
    outcome=run_case(Case(agent_input["primitive"],agent_input["dtype"],None if agent_input["primitive"]=="AllGather" else agent_input["reduce_op"],agent_input["rank_size"],topology_name,"agent_gate",agent_input["message_size"],20260804),exact=True)
    correctness=outcome["exact_match"] and outcome["within_dtype_tolerance"]
    if not correctness:
        return {"input":agent_input,"analysis":{"candidate_count":len(decision["candidate_algorithms"])},"candidates":decision,"proposal":proposal,"correctness_gate":False,"evaluation":{"selected":False,"reason":"CORRECTNESS_HARD_GATE"},"reflection":{"action":"reject candidate regardless of performance"},"replanning":None,"final_selection":None}
    replanning=None
    if agent_input["reliability_state"].get("event"):
        _,replacement,trace=replan(schedule,agent_input["topology"],agent_input["reliability_state"]["event"],memory_budget_bytes=agent_input["memory_budget"]);replanning=trace
        if replacement is not None:schedule=replacement
    return {"input":agent_input,"analysis":{"topology_hash":agent_input["topology"]["topology_hash"],"candidate_count":len(decision["candidate_algorithms"]),"objective":agent_input["optimization_objective"]},"candidates":{key:value for key,value in decision.items() if key!="selected_schedule"},"proposal":proposal,"correctness_gate":True,"correctness_output_hash":outcome["output_hash"],"evaluation":{"selected":True,"multi_objective":{"p50_latency":"minimize","p95_latency":"minimize","effective_bandwidth":"maximize","peak_memory":"bounded","congestion_penalty":"minimize","reliability_penalty":"minimize","correctness_gate":True}},"reflection":{"action":"accept invariant-valid correctness-passing candidate; benchmark before commit","model_boundary":"SIMULATED_ONLY"},"replanning":replanning,"final_selection":{"algorithm":schedule["algorithm"],"schedule_hash":schedule["schedule_hash"]}}
