# Scenario: single_node_8gpu

## Scenario Information
- **Name:** single_node_8gpu
- **Nodes:** 8
- **Topology:** Full Mesh
- **Primitive:** AllReduce
- **Message Size:** 128 MB

## Selected Algorithm
- **Algorithm:** Butterfly
- **Score:** 90.4
- **Latency:** 0.0060 ms
- **Bandwidth:** 10.62 GB/s

## Decision Quality
- **Selected:** Butterfly
- **Best Alternative:** Ring AllReduce
- **Score Gap:** -11.2
- **Verdict:** Selection is near-optimal.

## Reflection
- **Status:** GOOD
- **Need Replan:** False

## Decision Trace

- [1] Detected topology: Full Mesh  Nodes: 8  Dominant Link: HCCS
- [2] Generated candidates: Butterfly, Ring AllReduce, Mesh
- [3] Simulation results:  Butterfly Score: 90.4  |  Ring AllReduce Score: 79.2  |  Mesh Score: 73.3
- [4] Cost Evaluation:  latency=0.0000ms  bandwidth=0.00GB/s
- [5] Selected: Butterfly
-      Reason: Butterfly achieves the highest score (90.40) with the lowest latency (0.0060 ms) and high bandwidth (10.62 GB/s), and has a 100% historical win rate in similar scenarios.
- [6] Reflection: status=good  need_replan=False
