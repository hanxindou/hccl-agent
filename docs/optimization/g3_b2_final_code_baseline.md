# G3-B2 final code baseline

The final algorithm source baseline is commit `efd946c47ec626d996667ab941a1acf598157ce0`; the enclosing G3-B2-F freeze commit is self-referential and is reported in the final handoff. Frozen interfaces are `g3-b2-topology-hierarchical-v1`, `g3-b2-schedule-ir-v1`, `g3-b2-benchmark-selector-v1`, and `g2-f-6-simulator-acceptance-v1`.

The default backend remains CPU_SIM with fallback `NONE`. `libhccl_plugin.so` remains the CPU_SIM reference plugin with SONAME `libhccl_plugin.so` and the unchanged 19-symbol allowlist. The direct archive remains a static build/lifecycle readiness artifact and was not runtime-executed.

The authoritative machine-readable baseline is `experiments/optimization/g3_b2_final_baseline.json`; the authoritative evidence is the single `g3_b2_f_final_20260807T040000Z` directory.
