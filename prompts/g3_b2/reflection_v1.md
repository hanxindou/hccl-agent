---
prompt_id: g3-b2-reflection
version: 1.0.0
purpose: Explain benchmark outcomes and propose one bounded adjustment round.
input_schema: g3-b2-evaluation-result-v1
output_schema: g3-b2-reflection-v1
---

Attribute changes to schedule, selection, routing, chunking, hierarchy, congestion handling, replanning, or simulated pipeline behavior. Preserve failures and regressions. Recommend at most one evidence-based code change per reflection.

Guards: correctness remains a hard gate; frozen parameters, scenarios, weights, seed, statistics, ABI, and claims remain unchanged. Validate referenced run and schedule hashes.

Prohibited claims: real-device validation or causal claims unsupported by simulator traces.
