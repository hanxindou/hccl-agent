# Claim-safe Phrasebook

The G3-C claim ledger is authoritative. Forbidden phrases below are quoted only so reviewers and authors can reject them.

| Claim | Safe wording | Conditional boundary | Forbidden wording | Truth identity |
|---|---|---|---|---|
| C-ABI-001 | project CPU_SIM ABI | Use only with the stated truth identity. | official plugin ABI verified | CPU_EXECUTED |
| C-ARCH-001 | default backend=CPU_SIM; fallback=NONE | Use only with the stated truth identity. | automatic real-device fallback | HOST_EXECUTED |
| C-ARCH-002 | independent validation track | Use only with the stated truth identity. | fourth backend | HISTORICAL_EVIDENCE |
| C-BP-001 | simulated backpressure | Use only with the stated truth identity. | NIC backpressure implemented; HCCL backpressure measured | SIMULATED_BACKPRESSURE |
| C-CRC-001 | host CRC32 integrity | Use only with the stated truth identity. | hardware CRC; NIC CRC; HCCL internal CRC | HOST_INTEGRITY_VALIDATED |
| C-DIRECT-001 | actual official API call expressions; compile/link-only production source readiness | Use only with the stated truth identity. | runtime executed; real collective executed | DIRECT_COMPILE_LINK_ONLY |
| C-DIRECT-002 | loaded=false; executed=false; runtime_api_calls=[]; direct_hccl_api_call=false | Use only with the stated truth identity. | DIRECT_RUNTIME_EXECUTED; REAL_HCCL_COLLECTIVE_EXECUTED | REAL_DEVICE_NOT_EXECUTED |
| C-INT8-001 | DEFERRED_BY_PRECISION_GATE | Use only with the stated truth identity. | INT8 implemented | HISTORICAL_EVIDENCE |
| C-IR-001 | v1 history remains immutable; v2 extension | Use only with the stated truth identity. | v2 replaces G3-B2 evidence | HOST_EXECUTED |
| C-MODEL-001 | real_model_executed=false; training_throughput=null | Use only with the stated truth identity. | real model throughput | REAL_DEVICE_NOT_EXECUTED |
| C-PAIR-001 | SKIPPED_BY_VALUE_GATE | Use only with the stated truth identity. | PairWise implemented | HISTORICAL_EVIDENCE |
| C-PERF-001 | weighted simulated collective-time improvement; relative to frozen fixed-Ring baseline | communication simulator only | real HCCL speedup; NPU speedup; training speedup | SIMULATED_ONLY |
| C-PERF-002 | 18 wins, 0 ties, 0 losses against fixed Ring | Use only with the stated truth identity. | all real workloads win | SIMULATED_ONLY |
| C-PIPE-001 | SIMULATED_PIPELINED_OVERLAP | Use only with the stated truth identity. | hardware stream overlap verified | SIMULATED_ONLY |
| C-PROFILE-001 | profiling_source=SIMULATOR_TRACE; msprof_executed=false | Use only with the stated truth identity. | msprof profile | SIMULATED_ONLY |
| C-RETRY-001 | logical timeout; bounded retry | Use only with the stated truth identity. | real HCCL transport retransmission; real network timeout | HOST_RETRY_VALIDATED |
| C-SCALE-001 | 1024 logical ranks | not a physical cluster | 1024 real devices; 1024-card validation | SIMULATED_ONLY |
| C-SPARSE-001 | lossless sparse host correctness | Use only with the stated truth identity. | real sparse network speedup | LOSSLESS_SPARSE_HOST_EXECUTED |
| C-SPARSE-002 | modeled wire bytes; modeled payload-byte reduction | Use only with the stated truth identity. | physically measured NIC bytes; real wire reduction measured | LOSSLESS_SPARSE_HOST_EXECUTED |
| C-SPARSE-003 | dense fallback | Use only with the stated truth identity. | sparse always wins | HOST_EXECUTED |
| C-TRAIN-001 | TRAINING_LINEAR_SPEEDUP_NOT_VERIFIED=true | Use only with the stated truth identity. | 90% training scale achieved | REAL_DEVICE_NOT_EXECUTED |

## Agent/autonomy wording

Use: `Agent-assisted`, `Agent-generated proposal`, `deterministically evaluated`, `human-governed`, `offline replayable`, and `evidence-backed`.

Do not assert full autonomy. G3-B3 historical Prompt/Response is unavailable; normalized trace material is reconstructed from frozen evidence and is not hidden chain-of-thought.
