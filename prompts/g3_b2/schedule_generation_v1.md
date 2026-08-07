---
prompt_id: g3-b2-schedule-generation
version: 1.0.0
purpose: Generate bounded collective Schedule IR candidates.
input_schema: g3-b2-schedule-request-v1
output_schema: g3-b2-schedule-proposal-v1
---

Use only the supplied primitive, topology, hardware profile, frozen parameters, and candidate allowlist. Return canonical Schedule IR candidates with explicit phases, transfers, dependencies, memory plan, failure policy, and estimated metrics.

Guards: correctness is a hard gate; preserve CPU_SIM as the default backend and NONE as fallback; do not change public ABI or frozen parameters. Validate schema, topology reachability, dependency order, rank coverage, chunk coverage, byte accounting, and the canonical schedule hash.

Prohibited claims: real NPU measurement, real HCCL runtime execution, real training throughput, or real-device acceptance.
