# Report Source Index

| Report | Source code/config | Frozen evidence | Metric groups | Claim IDs |
|---|---|---|---|---|
| [01_system_architecture_and_algorithm_design.md](01_system_architecture_and_algorithm_design.md) | `agent/; algorithm/; topology/` | `algorithm_support_matrix; agent_trace_inventory` | `algorithm_support, agent` | `C-ARCH-001, C-ARCH-002, C-PAIR-001` |
| [02_collective_schedule_ir_and_algorithm_evolution.md](02_collective_schedule_ir_and_algorithm_evolution.md) | `algorithm/schedule_ir.py; feature_completion/contracts.py` | `c_python_parity; schedule_ir_v2_audit` | `schedule_ir` | `C-IR-001` |
| [03_topology_and_hardware_model.md](03_topology_and_hardware_model.md) | `topology/; hardware/; configs/` | `scale_summary` | `g3_b2_scale` | `—` |
| [04_dense_and_sparse_correctness_report.md](04_dense_and_sparse_correctness_report.md) | `simulator/; feature_completion/sparse.py` | `correctness_summary; sparse_correctness` | `correctness, correctness_coverage` | `C-SPARSE-001` |
| [05_sparse_communication_and_wire_accounting_report.md](05_sparse_communication_and_wire_accounting_report.md) | `feature_completion/sparse.py; hcccl/src/internal/sparse_codec.c` | `sparse_benchmark; sparse_break_even` | `sparse, sparse_break_even` | `C-SPARSE-002, C-SPARSE-003` |
| [06_simulator_performance_and_scale_report.md](06_simulator_performance_and_scale_report.md) | `algorithm/; simulator/` | `performance_summary; wins_ties_losses; ablation` | `g3_b2_performance, g3_b2_scenarios, g3_b2_ablation` | `C-MODEL-001, C-PERF-001, C-PERF-002, C-PIPE-001, C-PROFILE-001, C-SCALE-001, C-TRAIN-001` |
| [07_integrity_retry_and_reliability_report.md](07_integrity_retry_and_reliability_report.md) | `feature_completion/reliability.py; flow_control.py` | `crc; retry; timeout; flow_control` | `integrity, retry, backpressure` | `C-BP-001, C-CRC-001, C-RETRY-001` |
| [08_simulator_user_manual.md](08_simulator_user_manual.md) | `tools/submission_cli/; simulator/` | `submission_regression` | `regression` | `—` |
| [09_native_plugin_and_abi_appendix.md](09_native_plugin_and_abi_appendix.md) | `hcccl/; native ABI manifest` | `native_elf; reproducible_build` | `native_abi, regression` | `C-ABI-001` |
| [10_direct_compile_link_readiness_appendix.md](10_direct_compile_link_readiness_appendix.md) | `hcccl/direct/src/hccl_direct_runtime_source.cpp` | `official_api_call_expression; direct_compile_link` | `direct` | `C-DIRECT-001, C-DIRECT-002` |
| [11_known_limitations_and_future_hardware_plan.md](11_known_limitations_and_future_hardware_plan.md) | `risk/claim documents` | `result; claim_boundary` | `feature_gates` | `C-INT8-001` |

All source paths are repository-relative. Numeric values resolve through `../report_data_ledger.json`; claims resolve through `../report_claim_ledger.json`.
