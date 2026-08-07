---
prompt_id: g3-b2-replanning
version: 1.0.0
purpose: Replan a schedule after a structured topology event.
input_schema: g3-b2-replan-request-v1
output_schema: g3-b2-replan-result-v1
---

Invalidate the old schedule, recompute reachable routes, regenerate candidates, validate correctness and invariants, and return the selected replacement or an explicit NO_PATH result.

Guards: preserve bounded memory, chunk coverage, ordering, duplicate-transfer checks, public ABI, frozen parameters, and fallback NONE. Validate pre/post topology and schedule hashes.

Prohibited claims: physical failover timing, actual device recovery, or runtime API execution.
