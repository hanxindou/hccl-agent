"""Simulator-only collective/compute pipeline overlap model."""

from __future__ import annotations

from typing import Any


PIPELINE_MODES={"NO_OVERLAP","SIMULATED_PIPELINED_OVERLAP"}


def model_pipeline(schedule: dict[str, Any], mode: str, *, modeled_compute_slot_us: float = 10.0) -> dict[str, Any]:
    if mode not in PIPELINE_MODES or modeled_compute_slot_us < 0:
        raise ValueError("invalid pipeline mode or compute slot")
    chunks=max(1,schedule["chunk_count"]); depth=1 if mode=="NO_OVERLAP" else min(4,chunks)
    costs=schedule["estimated_metrics"].get("phase_costs",[])
    total_communication=sum(row["final_link_time"] for row in costs) if costs else float(schedule["estimated_metrics"]["critical_path_steps"])
    communication_slot=total_communication/chunks
    communication_slots=[round(communication_slot,9)]*chunks
    compute_slots=[round(modeled_compute_slot_us,9)]*chunks
    if mode=="NO_OVERLAP":
        fill=0.0; steady=total_communication+modeled_compute_slot_us*chunks; drain=0.0; overlap=0.0
    else:
        fill=communication_slot
        steady=max(communication_slot,modeled_compute_slot_us)*max(0,chunks-1)
        drain=modeled_compute_slot_us
        serial=total_communication+modeled_compute_slot_us*chunks
        overlap=max(0.0,min(1.0,1.0-(fill+steady+drain)/serial)) if serial else 0.0
    critical=fill+steady+drain
    return {"mode":mode,"pipeline_depth":depth,"fill_time":round(fill,9),"steady_state_time":round(steady,9),"drain_time":round(drain,9),"communication_slots":communication_slots,"modeled_compute_slots":compute_slots,"overlap_ratio":round(overlap,9),"critical_path":round(critical,9),"simulator_only":True,"truth_label":"SIMULATED_ONLY","real_stream_overlap":False,"real_compute_parallelism":False,"real_ub_hbm_reuse":False,"zero_cpu_intervention_claim":False}
