"""Run the authoritative G3-B2-E agent chain and frozen A0-A7 ablation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

from agent.g3_b2_optimization_loop import run_chain
from algorithm.ablation_benchmark import AblationBenchmark,STAGES
from algorithm.topology_model import build_topology
from algorithm.topology_schedules import generate_schedule


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical_hash(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def write_json(path:Path,value:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="\n") as stream:stream.write(json.dumps(value,indent=2,sort_keys=True)+"\n")


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--evidence-dir",type=Path,required=True);parser.add_argument("--adjustment-rounds",type=int,default=0);parser.add_argument("--initial-evidence",type=Path);args=parser.parse_args();evidence=args.evidence_dir if args.evidence_dir.is_absolute() else ROOT/args.evidence_dir
    if evidence.exists() and any(evidence.iterdir()):raise RuntimeError(f"refusing to overwrite evidence: {evidence}")
    evidence.mkdir(parents=True,exist_ok=True)
    matrix_path=ROOT/"configs/optimization/g3_b2_benchmark_matrix.json";parameter_path=ROOT/"experiments/optimization/g3_b2_parameter_freeze.json"
    ablation=AblationBenchmark(matrix_path).run()
    topology=build_topology("fat_tree",16);baseline=generate_schedule("Ring","AllReduce",topology,16*1024*1024+3)
    agent_input={"primitive":"AllReduce","message_size":16*1024*1024+3,"rank_size":16,"dtype":"FP32","reduce_op":"SUM","topology":topology,"hardware_profile":"g3-b2-frozen-hardware-v1","memory_budget":64*1024*1024,"reliability_state":{"event":{"event_id":"agent-chain-link-degraded","event_type":"LINK_DEGRADED","source_rank":0,"destination_rank":8}},"optimization_objective":{"p50":"minimize","p95":"minimize","bandwidth":"maximize","memory":"bounded","correctness":"hard_gate"},"baseline_schedule":baseline}
    chain=run_chain(agent_input);run_id="g3-b2-e-authoritative-optimization"+(f"-round{args.adjustment_rounds}" if args.adjustment_rounds else "")
    proposal=chain["proposal"];evaluation={"run_id":run_id,"correctness_hard_gate":chain["correctness_gate"],"multi_objective":chain["evaluation"],"performance_gates":ablation["gates"],"wins":ablation["wins"],"ties":ablation["ties"],"losses":ablation["losses"],"selected":chain["final_selection"]}
    reflection={"run_id":run_id,"performance_target_status":"SATISFIED" if ablation["gates"]["default_performance_gate_met"] else "PARTIALLY_SATISFIED","adjustment_rounds_used":args.adjustment_rounds,"observation":"Every win, tie, loss, regression, and simulator-only pipeline contribution remains explicit.","action":"freeze stable correctness-passing selection" if ablation["gates"]["default_performance_gate_met"] else "retain truthful partial result; no benchmark or parameter changes","model_boundary":"SIMULATED_ONLY"}
    proposal_path=ROOT/f"agent/evidence/g3_b2/proposals/{run_id}.json";evaluation_path=ROOT/f"agent/evidence/g3_b2/evaluations/{run_id}.json";reflection_path=ROOT/f"agent/evidence/g3_b2/reflections/{run_id}.json"
    write_json(proposal_path,proposal);write_json(evaluation_path,evaluation);write_json(reflection_path,reflection)
    trace={"run_id":run_id,"timestamp":"2026-08-07T03:00:00Z","development_agent":"Codex","runtime_agent":"hccl-agent:g3_b2_optimization_loop","prompt_id":"g3-b2-benchmark-evaluation","prompt_version":"1.0.0","input_schema_version":"g3-b2-agent-input-v1","output_schema_version":"g3-b2-evaluation-result-v1","baseline_commit":"44dad2e","input_hash":canonical_hash(agent_input),"proposal_hash":canonical_hash(proposal),"human_decision":"AUTHORIZED_G3_B2_SEQUENCE_NO_ALGORITHM_OVERRIDE","changed_files":["agent/g3_b2_optimization_loop.py","algorithm/ablation_benchmark.py"],"tests":["A0-A7 frozen matrix","agent correctness hard gate","wins/ties/losses audit"],"benchmark_result":{"default_performance_gate_met":ablation["gates"]["default_performance_gate_met"],"weighted_geomean_improvement_percent":ablation["gates"]["weighted_geomean_improvement_percent"]},"reflection":reflection,"selected":chain["final_selection"] is not None,"result_commit":"RESOLVED_BY_COMMIT_MAPPING"}
    write_json(ROOT/f"agent/evidence/g3_b2/runs/{run_id}.json",trace)
    write_json(evidence/"agent_chain.json",chain);write_json(evidence/"ablation_summary.json",{"stages":STAGES,"rows":ablation["stage_rows"]});write_json(evidence/"wins_ties_losses.json",{"wins":ablation["wins"],"ties":ablation["ties"],"losses":ablation["losses"],"scenarios":ablation["comparisons"]});write_json(evidence/"performance_summary.json",ablation["gates"]);write_json(evidence/"agent_trace.json",trace);write_json(evidence/"proposal.json",proposal);write_json(evidence/"evaluation.json",evaluation);write_json(evidence/"reflection.json",reflection)
    write_json(evidence/"result.json",{"checkpoint":"G3-B2-E","checkpoint_status":"COMPLETED","authoritative":args.adjustment_rounds>0 or args.initial_evidence is None,"agent_chain_complete":chain["final_selection"] is not None,"correctness_hard_gate":chain["correctness_gate"],"ablation_stage_count":len(STAGES),"performance_scenario_count":len(ablation["comparisons"]),"wins":ablation["wins"],"ties":ablation["ties"],"losses":ablation["losses"],"performance_target_status":"SATISFIED" if ablation["gates"]["default_performance_gate_met"] else "PARTIALLY_SATISFIED","optimization_adjustment_rounds":args.adjustment_rounds,"initial_evidence":None if args.initial_evidence is None else args.initial_evidence.as_posix(),"frozen_parameters_changed":False,"benchmark_changed":False,"measured_on_real_npu":False,"real_device_api_executed":False,"truth_label":"SIMULATED_ONLY"})
    write_json(evidence/"manifest.json",{"schema_version":"g3-b2-e-evidence-v1","parameter_freeze_sha256":sha(parameter_path),"benchmark_contract_sha256":sha(matrix_path),"seed":20260804,"stages":list(STAGES),"adjustment_rounds":args.adjustment_rounds,"initial_evidence_sha256":None if args.initial_evidence is None else sha((ROOT/args.initial_evidence if not args.initial_evidence.is_absolute() else args.initial_evidence)/"SHA256SUMS"),"prompt_registry_sha256":sha(ROOT/"agent/evidence/g3_b2/prompt_registry.json"),"proposal_sha256":sha(proposal_path),"evaluation_sha256":sha(evaluation_path),"reflection_sha256":sha(reflection_path),"truth_labels":["AGENT_GENERATED_PROPOSAL","AGENT_SELECTED_SCHEDULE","SIMULATED_ONLY","REAL_DEVICE_NOT_EXECUTED"]})
    with (evidence/"README.md").open("w",encoding="utf-8",newline="\n") as stream:stream.write("# G3-B2-E agent optimization and ablation evidence\n\nAuthoritative replayable runtime-agent chain and A0-A7 frozen-matrix simulator ablation. Primary performance excludes pipeline overlap. Results are not real NPU, training, or HCCL runtime measurements.\n")
    files=sorted(path for path in evidence.iterdir() if path.is_file())
    with (evidence/"SHA256SUMS").open("w",encoding="utf-8",newline="\n") as stream:
        for path in files:stream.write(f"{sha(path)}  {path.name}\n")
    anchor=sha(evidence/"SHA256SUMS");(evidence/"EVIDENCE_SHA256").write_text(f"{anchor}  SHA256SUMS\n",encoding="utf-8",newline="\n")
    print(json.dumps({"evidence":evidence.relative_to(ROOT).as_posix(),"sha256":anchor,"wins":ablation["wins"],"ties":ablation["ties"],"losses":ablation["losses"],"improvement":ablation["gates"]["weighted_geomean_improvement_percent"],"gate":ablation["gates"]["default_performance_gate_met"]},sort_keys=True));return 0


if __name__=="__main__":raise SystemExit(main())
