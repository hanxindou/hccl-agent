# Scenario: heterogeneous_cluster

## Scenario Information
- **Name:** heterogeneous_cluster
- **Nodes:** 24
- **Topology:** Heterogeneous
- **Primitive:** AllReduce
- **Message Size:** 256 MB

## Selected Algorithm
- **Algorithm:** NHR
- **Score:** 42.0
- **Latency:** 0.0920 ms
- **Bandwidth:** 11.62 GB/s

## Decision Quality
- **Selected:** NHR
- **Best Alternative:** Ring AllReduce
- **Score Gap:** -1.2
- **Verdict:** Selection is near-optimal.

## Reflection
- **Status:** GOOD
- **Need Replan:** False

## Decision Trace

- [1] Detected topology: Ring  Nodes: 24  Dominant Link: HCCS
- [2] Generated candidates: NHR, Ring AllReduce
- [3] Simulation results:  NHR Score: 42.0  |  Ring AllReduce Score: 40.8
- [4] Cost Evaluation:  latency=0.0000ms  bandwidth=0.00GB/s
- [5] Selected: NHR
-      Reason: NHR achieves higher bandwidth (11.62 GB/s) and a better score (42.00) than Ring AllReduce, with a 100% historical win rate in similar scenarios.
- [6] Reflection: status=good  need_replan=False
