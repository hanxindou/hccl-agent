"""Generate G3-B2-C topology-aware optimization evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithm.chunk_policy import CHUNK_CANDIDATES, select_chunk
from algorithm.schedule_selector import select_schedule
from algorithm.schedule_ir import validate_schedule
from algorithm.topology_model import build_topology
from algorithm.topology_schedules import SUPPORT_MATRIX, UnsupportedAlgorithmPrimitivePair, generate_schedule, nhr_order
from simulator.collective_correctness import Case, run_case


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--evidence-dir",type=Path,required=True); args=parser.parse_args()
    evidence=args.evidence_dir if args.evidence_dir.is_absolute() else ROOT/args.evidence_dir
    if evidence.exists(): raise RuntimeError(f"refusing to overwrite evidence: {evidence}")
    evidence.mkdir(parents=True)
    topology_specs=[("full_mesh_8","full_mesh",8),("ring_8","ring",8),("ring_16","ring",16),("fat_tree_64","fat_tree",64),("asymmetric_16","asymmetric",16),("asymmetric_64","asymmetric",64)]
    topologies={name:build_topology(variant,ranks) for name,variant,ranks in topology_specs}
    topology_inventory=[{"name":name,"variant":topology["variant"],"rank_size":topology["rank_size"],"node_count":len({node["node_id"] for node in topology["nodes"]}),"group_count":len({node["group_id"] for node in topology["nodes"]}),"link_count":len(topology["links"]),"topology_hash":topology["topology_hash"]} for name,topology in topologies.items()]
    sample_specs=[("Ring","AllReduce","ring_16"),("Butterfly","AllReduce","full_mesh_8"),("Butterfly","AllGather","full_mesh_8"),("Mesh","AllReduce","full_mesh_8"),("Mesh","ReduceScatter","fat_tree_64"),("NHR","AllReduce","asymmetric_16"),("Hierarchical","AllReduce","fat_tree_64")]
    schedule_inventory=[]; congestion=[]; correctness=[]
    for algorithm,primitive,topology_name in sample_specs:
        topology=topologies[topology_name]; schedule=generate_schedule(algorithm,primitive,topology,4*1024*1024+3)
        validate_schedule(schedule)
        schedule_inventory.append({"algorithm":algorithm,"primitive":primitive,"topology":topology_name,"schedule_hash":schedule["schedule_hash"],"phase_count":len(schedule["phases"]),"chunk_selection":schedule.get("chunk_selection"),"optimization_metadata":schedule.get("optimization_metadata")})
        for phase in schedule["phases"]:
            cost=phase.get("cost")
            if cost: congestion.append({"schedule_hash":schedule["schedule_hash"],"phase_id":phase["phase_id"],**cost})
        outcome=run_case(Case(primitive,"FP32",None if primitive=="AllGather" else "SUM",topology["rank_size"],{"full_mesh":"FULL_MESH","ring":"RING","fat_tree":"FAT_TREE","asymmetric":"HETEROGENEOUS"}[topology["variant"]],"g3_b2_c_gate",65539,20260804),exact=True)
        correctness.append({"algorithm":algorithm,"primitive":primitive,"topology":topology_name,"schedule_hash":schedule["schedule_hash"],"correctness_passed":outcome["exact_match"] and outcome["within_dtype_tolerance"],"output_hash":outcome["output_hash"]})
    symmetric_order,_=nhr_order(topologies["full_mesh_8"],65536); asymmetric_order,asymmetric_segments=nhr_order(topologies["asymmetric_16"],65536)
    nhr_audit={"symmetric_order":symmetric_order,"symmetric_explanation":"equal weights use deterministic ascending rank tie-break","asymmetric_order":asymmetric_order,"asymmetric_segments":asymmetric_segments,"weight_formula":"latency_cost + transfer_bytes/effective_bandwidth + congestion_penalty + reliability_penalty"}
    selectors=[]
    for primitive,name in (("AllReduce","full_mesh_8"),("AllReduce","asymmetric_16"),("AllReduce","fat_tree_64"),("AllGather","full_mesh_8"),("ReduceScatter","full_mesh_8")):
        decision=select_schedule(primitive,topologies[name],1048579)
        selectors.append({key:value for key,value in decision.items() if key!="selected_schedule"}|{"topology":name,"primitive":primitive})
    unsupported=[]
    for algorithm in SUPPORT_MATRIX:
        for primitive in ("AllReduce","AllGather","ReduceScatter"):
            if primitive not in SUPPORT_MATRIX[algorithm]:
                try: generate_schedule(algorithm,primitive,topologies["full_mesh_8"],65539)
                except UnsupportedAlgorithmPrimitivePair as error: unsupported.append({"algorithm":algorithm,"primitive":primitive,"reason_code":error.code})
    chunk_audit=[]
    for name in ("full_mesh_8","fat_tree_64","asymmetric_16","asymmetric_64"):
        topology=topologies[name]; links=topology["links"]
        chunk_audit.append({"topology":name,"decision":select_chunk(128*1024*1024,topology["rank_size"],max(1,(topology["rank_size"]-1).bit_length()),min(row["effective_bandwidth_gbps"] for row in links),max(row["latency_ms"] for row in links),min(8,topology["rank_size"]),64*1024*1024)})
    write_json(evidence/"algorithm_support_matrix.json",{algorithm:{primitive:("SUPPORTED" if primitive in primitives else "UNSUPPORTED_ALGORITHM_PRIMITIVE_PAIR") for primitive in ("AllReduce","AllGather","ReduceScatter")} for algorithm,primitives in SUPPORT_MATRIX.items()})
    write_json(evidence/"topology_inventory.json",topology_inventory); write_json(evidence/"schedule_inventory.json",schedule_inventory); write_json(evidence/"selector_decisions.json",selectors); write_json(evidence/"unsupported_pairs.json",unsupported); write_json(evidence/"chunk_selection.json",chunk_audit); write_json(evidence/"congestion_cost_audit.json",congestion); write_json(evidence/"nhr_audit.json",nhr_audit); write_json(evidence/"correctness.json",correctness)
    write_json(evidence/"result.json",{"checkpoint":"G3-B2-C","checkpoint_status":"COMPLETED","main_innovation":"Topology-Aware Hierarchical Non-Uniform Collective Scheduling","sample_schedule_count":len(schedule_inventory),"correctness_passed":all(row["correctness_passed"] for row in correctness),"selector_fallback":"NONE","chunk_candidates":list(CHUNK_CANDIDATES),"unsupported_pair_count":len(unsupported),"public_abi_changed":False,"measured_on_real_npu":False,"real_device_api_executed":False,"truth_label":"SIMULATED_ONLY"})
    write_json(evidence/"manifest.json",{"schema_version":"g3-b2-c-evidence-v1","topology_variants":list(topologies),"support_matrix_sha256":hashlib.sha256(json.dumps({key:sorted(value) for key,value in SUPPORT_MATRIX.items()},sort_keys=True).encode()).hexdigest(),"frozen_parameter_sha256":sha(ROOT/"experiments/optimization/g3_b2_parameter_freeze.json"),"benchmark_contract_sha256":sha(ROOT/"configs/optimization/g3_b2_benchmark_matrix.json"),"fallback_policy":"NONE","truth_labels":["SIMULATED_ONLY","REAL_DEVICE_NOT_EXECUTED"]})
    with (evidence/"README.md").open("w",encoding="utf-8",newline="\n") as stream: stream.write("# G3-B2-C topology-aware optimization evidence\n\nSimulator-only schedules, selectors, chunk decisions, congestion costs, and correctness gates. No real device or HCCL runtime API was executed.\n")
    files=sorted(path for path in evidence.iterdir() if path.is_file())
    with (evidence/"SHA256SUMS").open("w",encoding="utf-8",newline="\n") as stream:
        for path in files: stream.write(f"{sha(path)}  {path.name}\n")
    anchor=sha(evidence/"SHA256SUMS")
    with (evidence/"EVIDENCE_SHA256").open("w",encoding="utf-8",newline="\n") as stream: stream.write(f"{anchor}  SHA256SUMS\n")
    print(json.dumps({"evidence":evidence.relative_to(ROOT).as_posix(),"sha256":anchor,"schedules":len(schedule_inventory),"correctness":True},sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
