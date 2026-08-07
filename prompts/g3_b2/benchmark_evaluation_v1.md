---
prompt_id: g3-b2-benchmark-evaluation
version: 1.0.0
purpose: Evaluate candidates against the immutable G3-B2 benchmark contract.
input_schema: g3-b2-evaluation-input-v1
output_schema: g3-b2-evaluation-result-v1
---

Reject every correctness failure. Compare the retained scenarios with identical seeds, warmups, iterations, parameters, and percentile rules. Report every win, tie, loss, regression, weighted geometric mean, p50, p95, bandwidth, congestion, and memory metric.

Guards: do not delete scenarios, change weights, tune frozen constants, or hide regressions. Validate all input and output hashes.

Prohibited claims: measured NPU speedup, real training acceleration, or real HCCL performance.
