# Scenario: fattree_32gpu

## Scenario Information
- **Name:** fattree_32gpu
- **Nodes:** 32
- **Topology:** Fat Tree
- **Primitive:** AllReduce
- **Message Size:** 512 MB

## Selected Algorithm
- **Algorithm:** NHR
- **Score:** 37.2
- **Latency:** 0.1240 ms
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

- [1] Detected topology: Ring  Nodes: 32  Dominant Link: HCCS
- [2] Generated candidates: NHR, Ring AllReduce
- [3] Simulation results:  NHR Score: 37.2  |  Ring AllReduce Score: 36.0
- [4] Cost Evaluation:  latency=0.0000ms  bandwidth=0.00GB/s
- [5] Selected: NHR
-      Reason: NHR achieves higher bandwidth (11.62 GB/s) and a better score (37.20) than Ring AllReduce, with a 100% historical win rate in similar scenarios.
- [6] Reflection: status=good  need_replan=False
