"""Generate G3-B2-D dynamic replan, memory, and pipeline evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))

from algorithm.memory_model import attach_memory_report, memory_report
from algorithm.pipeline_model import model_pipeline
from algorithm.replanner import replan
from algorithm.topology_model import build_topology
from algorithm.topology_schedules import generate_schedule


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path:Path,value:Any)->None:
    with path.open("w",encoding="utf-8",newline="\n") as stream:stream.write(json.dumps(value,indent=2,sort_keys=True)+"\n")


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--evidence-dir",type=Path,required=True);args=parser.parse_args();evidence=args.evidence_dir if args.evidence_dir.is_absolute() else ROOT/args.evidence_dir
    if evidence.exists():raise RuntimeError(f"refusing to overwrite evidence: {evidence}")
    evidence.mkdir(parents=True)
    event_specs=[
        ("LINK_DEGRADED",build_topology("fat_tree",16),{"source_rank":0,"destination_rank":8}),
        ("LINK_DOWN",build_topology("full_mesh",8),{"source_rank":0,"destination_rank":1}),
        ("LINK_RECOVERED",build_topology("full_mesh",8),{"source_rank":0,"destination_rank":1}),
        ("RANK_REMOVED",build_topology("fat_tree",16),{"rank":15}),
        ("RANK_RECOVERED",build_topology("fat_tree",15),{"rank":15}),
        ("NO_ALTERNATE_PATH",build_topology("ring",8),{"rank":0}),
    ]
    traces=[];schedule_summary=[]
    for index,(event_type,topology,fields) in enumerate(event_specs):
        old=generate_schedule("Hierarchical","AllReduce",topology,4*1024*1024+3) if topology["variant"]=="fat_tree" else generate_schedule("Ring","AllReduce",topology,4*1024*1024+3)
        updated,schedule,trace=replan(old,topology,{"event_id":f"g3-b2-d-{index:02d}","event_type":event_type,**fields});traces.append(trace)
        schedule_summary.append({"event_id":trace["event_id"],"event_type":event_type,"old_rank_size":topology["rank_size"],"new_rank_size":updated["rank_size"],"old_schedule_hash":old["schedule_hash"],"new_schedule_hash":None if schedule is None else schedule["schedule_hash"],"final_status":trace["final_status"],"memory_plan":None if schedule is None else schedule["memory_plan"]})
    with (evidence/"replan_trace.jsonl").open("w",encoding="utf-8",newline="\n") as stream:
        for trace in traces:stream.write(json.dumps(trace,sort_keys=True)+"\n")
    memory=[]
    for logical in (1024**3,2*1024**3):
        schedule=attach_memory_report(generate_schedule("Hierarchical","AllReduce",build_topology("fat_tree",64),logical),64*1024*1024)
        memory.append({"schedule_hash":schedule["schedule_hash"],**schedule["memory_plan"]})
    pipeline_schedule=generate_schedule("Hierarchical","AllReduce",build_topology("fat_tree",16),128*1024*1024)
    pipeline=[model_pipeline(pipeline_schedule,"NO_OVERLAP",modeled_compute_slot_us=20.0),model_pipeline(pipeline_schedule,"SIMULATED_PIPELINED_OVERLAP",modeled_compute_slot_us=20.0)]
    reliability={"events":[{"event_id":row["event_id"],"event_type":row["event_type"],"status":row["final_status"],"correctness":row["correctness_after_replan"],"post_replan_checks":row["post_replan_checks"]} for row in traces],"no_path_status":next(row["final_status"] for row in traces if row["event_type"]=="NO_ALTERNATE_PATH"),"fallback":"NONE"}
    write_json(evidence/"schedule_replan_summary.json",schedule_summary);write_json(evidence/"memory_summary.json",memory);write_json(evidence/"pipeline_summary.json",pipeline);write_json(evidence/"reliability_summary.json",reliability)
    successful=[row for row in traces if row["final_status"]=="REPLANNED"]
    write_json(evidence/"result.json",{"checkpoint":"G3-B2-D","checkpoint_status":"COMPLETED","event_count":len(traces),"successful_replans":len(successful),"expected_no_path_failures":sum(row["final_status"]=="EXPECTED_NO_PATH_FAILURE" for row in traces),"correctness_after_successful_replan":all(row["correctness_after_replan"] for row in successful),"bounded_memory":all(row["within_budget"] and row["materialized_bytes"]<row["logical_message_bytes"] for row in memory),"pipeline_modes":[row["mode"] for row in pipeline],"pipeline_truth":"SIMULATED_ONLY","public_abi_changed":False,"measured_on_real_npu":False,"real_device_api_executed":False})
    write_json(evidence/"manifest.json",{"schema_version":"g3-b2-d-evidence-v1","frozen_parameter_sha256":sha(ROOT/"experiments/optimization/g3_b2_parameter_freeze.json"),"benchmark_contract_sha256":sha(ROOT/"configs/optimization/g3_b2_benchmark_matrix.json"),"event_types":[row[0] for row in event_specs],"memory_budget_bytes":64*1024*1024,"fallback_policy":"NONE","truth_labels":["SIMULATED_ONLY","REAL_DEVICE_NOT_EXECUTED"]})
    with (evidence/"README.md").open("w",encoding="utf-8",newline="\n") as stream:stream.write("# G3-B2-D replan, memory, and pipeline evidence\n\nSimulator-only topology events, bounded logical-message materialization, and analytical pipeline modes. No real stream, compute kernel, UB/HBM, device, or HCCL runtime behavior is claimed.\n")
    files=sorted(path for path in evidence.iterdir() if path.is_file())
    with (evidence/"SHA256SUMS").open("w",encoding="utf-8",newline="\n") as stream:
        for path in files:stream.write(f"{sha(path)}  {path.name}\n")
    anchor=sha(evidence/"SHA256SUMS");(evidence/"EVIDENCE_SHA256").write_text(f"{anchor}  SHA256SUMS\n",encoding="utf-8",newline="\n")
    print(json.dumps({"evidence":evidence.relative_to(ROOT).as_posix(),"sha256":anchor,"events":len(traces),"replanned":len(successful)},sort_keys=True));return 0


if __name__=="__main__":raise SystemExit(main())
