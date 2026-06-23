# Benchmark Summary

| Scenario | Algorithm | Score | Latency (ms) | Bandwidth (GB/s) | Decision Quality |
|----------|-----------|-------|--------------|------------------|------------------|
| single_node_8gpu | Butterfly | 90.4 | 0.0060 | 10.62 | Selection is near-optimal. |
| dual_node_16gpu | NHR | 61.2 | 0.0600 | 11.62 | Selection is near-optimal. |
| fattree_32gpu | NHR | 37.2 | 0.1240 | 11.62 | Selection is near-optimal. |
| hierarchical_64gpu | Fat-Tree | 36.0 | 0.2520 | 11.25 | Selection is near-optimal. |
| heterogeneous_cluster | NHR | 42.0 | 0.0920 | 11.62 | Selection is near-optimal. |
