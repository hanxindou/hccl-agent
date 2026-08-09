# Figure-to-story Map

| Figure | Class | Audience question | Claims | Truth identity | Limitations |
|---|---|---|---|---|---|
| FIG-01 | MAIN | What is the system and what actually ran? | C-ARCH-001, C-ARCH-002 | HOST_EXECUTED, REAL_DEVICE_NOT_EXECUTED | architecture relation only; not performance evidence |
| FIG-02 | MAIN | What changed in the optimization pipeline? | C-IR-001 | HOST_EXECUTED, SIMULATED_ONLY | optimization outcomes are simulated |
| FIG-03 | MAIN | Where does the optimization improvement appear? | C-PERF-001 | SIMULATED_ONLY | not real NPU or training latency |
| FIG-04 | MAIN | How consistent was the modeled result? | C-PERF-001, C-PERF-002 | SIMULATED_ONLY | 18 frozen simulated scenarios only; 45.59% is canonical display, not hardware speedup |
| FIG-05 | SUPPORTING | What scale was modeled? | C-SCALE-001 | SIMULATED_ONLY | logical/model ranks, not physical NPU cluster |
| FIG-06 | MAIN | When is sparse useful and what was actually validated? | C-SPARSE-001, C-SPARSE-002, C-SPARSE-003 | LOSSLESS_SPARSE_HOST_EXECUTED | host correctness plus modeled/logical bytes; not NIC measurement |
| FIG-07 | MAIN | Which reliability properties were validated at each layer? | C-CRC-001, C-RETRY-001, C-BP-001 | HOST_INTEGRITY_VALIDATED, HOST_RETRY_VALIDATED, SIMULATED_BACKPRESSURE | not NIC/HCCL hardware reliability |
| FIG-08 | MAIN | What did the Agent and humans actually do? | C-PERF-001, C-IR-001 | AGENT_GENERATED, DETERMINISTIC_EVALUATION, HUMAN_INTERVENTION, RECONSTRUCTED_FROM_FROZEN_EVIDENCE | normalized reconstruction is not hidden reasoning or original historical execution |
| FIG-09 | SUPPORTING | Why were INT8 and PairWise not implemented? | C-INT8-001, C-PAIR-001 | RECONSTRUCTED_FROM_FROZEN_EVIDENCE, HISTORICAL_TRACE_UNAVAILABLE | historical Prompt/Response unavailable |
| FIG-10 | MAIN | What does Direct readiness prove? | C-DIRECT-001, C-DIRECT-002, C-ABI-001 | CPU_EXECUTED, DIRECT_COMPILE_LINK_ONLY, REAL_DEVICE_NOT_EXECUTED | no ACL/HCCL runtime, communicator, or device collective execution did not occur |
| FIG-11 | SUPPORTING | Which stages contributed to the modeled result? | C-PERF-001, C-PIPE-001 | SIMULATED_ONLY | modeled ablation, not hardware attribution |
| FIG-12 | MAIN | Which statements are safe at each evidence layer? | C-ARCH-001, C-DIRECT-002, C-MODEL-001 | HOST_EXECUTED, SIMULATED_ONLY, DIRECT_READINESS_ONLY, REAL_DEVICE_NOT_EXECUTED | summary does not replace claim ledger |
| FIG-13 | MAIN | What algorithm/topology breadth is implemented? | C-IR-001 | HOST_EXECUTED, SIMULATED_ONLY | coverage does not imply real-device validation |
