import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))

from algorithm.memory_model import attach_memory_report, memory_report
from algorithm.pipeline_model import model_pipeline
from algorithm.replanner import EVENT_TYPES, replan
from algorithm.topology_model import build_topology
from algorithm.topology_schedules import generate_schedule


def test_dynamic_replan_event_matrix_and_trace_contract():
    cases=[
        ("LINK_DEGRADED",build_topology("fat_tree",16),{"source_rank":0,"destination_rank":8}),
        ("LINK_DOWN",build_topology("full_mesh",8),{"source_rank":0,"destination_rank":1}),
        ("LINK_RECOVERED",build_topology("full_mesh",8),{"source_rank":0,"destination_rank":1}),
        ("RANK_REMOVED",build_topology("fat_tree",16),{"rank":15}),
        ("RANK_RECOVERED",build_topology("fat_tree",15),{"rank":15}),
    ]
    assert {row[0] for row in cases}|{"NO_ALTERNATE_PATH"}==EVENT_TYPES
    required={"event_id","event_type","old_topology_hash","new_topology_hash","old_schedule_hash","new_schedule_hash","affected_links","candidate_count","selected_algorithm","replan_reason","simulated_replan_time_ms","correctness_after_replan","final_status"}
    for index,(event_type,topology,fields) in enumerate(cases):
        old=generate_schedule("Hierarchical","AllReduce",topology,4*1024*1024+3) if topology["variant"]=="fat_tree" and topology["rank_size"]>=9 else generate_schedule("Ring","AllReduce",topology,4*1024*1024+3)
        updated,schedule,trace=replan(old,topology,{"event_id":f"event-{index}","event_type":event_type,**fields})
        assert required<=trace.keys()
        assert trace["old_topology_hash"]!=trace["new_topology_hash"] or event_type=="LINK_RECOVERED"
        assert trace["schedule_invalidated"] is True
        assert trace["final_status"]=="REPLANNED"
        assert trace["correctness_after_replan"] is True
        assert schedule is not None and trace["new_schedule_hash"]==schedule["schedule_hash"]
        assert all(trace["post_replan_checks"].values())


def test_no_alternate_path_is_explicit_failure_without_fallback():
    topology=build_topology("ring",8); old=generate_schedule("Ring","AllReduce",topology,1048579)
    _,schedule,trace=replan(old,topology,{"event_id":"event-no-path","event_type":"NO_ALTERNATE_PATH","rank":0})
    assert schedule is None
    assert trace["final_status"]=="EXPECTED_NO_PATH_FAILURE"
    assert trace["new_schedule_hash"] is None
    assert trace["fallback"]=="NONE"
    assert trace["candidate_count"]==0


def test_logical_one_gib_uses_bounded_materialization():
    logical=1024**3
    report=memory_report(logical,16*1024*1024,64*1024*1024,pipeline_depth=4)
    assert report["logical_message_bytes"]==logical
    assert report["materialized_bytes"]<logical
    assert report["peak_materialized_bytes"]<=report["memory_budget_bytes"]
    assert report["within_budget"] and report["bounded_materialization"]
    schedule=generate_schedule("Hierarchical","AllReduce",build_topology("fat_tree",64),logical)
    schedule=attach_memory_report(schedule,64*1024*1024)
    assert schedule["memory_plan"]["logical_to_materialized_ratio"]>1
    assert schedule["memory_plan"]["within_budget"]


def test_pipeline_modes_are_explicit_and_simulator_only():
    schedule=generate_schedule("Hierarchical","AllReduce",build_topology("fat_tree",16),128*1024*1024)
    serial=model_pipeline(schedule,"NO_OVERLAP",modeled_compute_slot_us=20.0)
    overlap=model_pipeline(schedule,"SIMULATED_PIPELINED_OVERLAP",modeled_compute_slot_us=20.0)
    required={"pipeline_depth","fill_time","steady_state_time","drain_time","communication_slots","modeled_compute_slots","overlap_ratio","critical_path"}
    assert required<=serial.keys() and required<=overlap.keys()
    assert serial["overlap_ratio"]==0.0 and overlap["overlap_ratio"]>=0.0
    assert overlap["critical_path"]<=serial["critical_path"]
    assert overlap["simulator_only"] and not overlap["real_stream_overlap"] and not overlap["real_compute_parallelism"] and not overlap["real_ub_hbm_reuse"] and not overlap["zero_cpu_intervention_claim"]


if __name__=="__main__":
    test_dynamic_replan_event_matrix_and_trace_contract()
    test_no_alternate_path_is_explicit_failure_without_fallback()
    test_logical_one_gib_uses_bounded_materialization()
    test_pipeline_modes_are_explicit_and_simulator_only()
    print("4 passed")
