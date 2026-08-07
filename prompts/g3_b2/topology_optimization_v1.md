---
prompt_id: g3-b2-topology-optimization
version: 1.0.0
purpose: Propose topology-aware hierarchical non-uniform schedules.
input_schema: g3-b2-topology-optimization-input-v1
output_schema: g3-b2-schedule-proposal-v1
---

Analyze weighted links, placement groups, fanout, contention, and finite chunk candidates. Propose only supported algorithm/primitive pairs and include rejected candidates with structured reasons.

Guards: use frozen link parameters and benchmark scenarios; preserve correctness, bounded memory, schedule invariants, public ABI, and fallback NONE. Validate routes and canonical hashes.

Prohibited claims: hardware calibration or any real-device performance result.
