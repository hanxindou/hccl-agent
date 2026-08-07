# G3-B3 final feature baseline

Status: `COMPLETED` for G3-B3 feature implementation and host-only evidence; overall competition delivery remains `PARTIAL` and real-device acceptance remains `HARDWARE_BLOCKED`.

Frozen contracts:

- CPU_SIM public ABI, `libhccl_plugin.so` SONAME, exact 19-symbol allowlist, default backend, and fallback policy are unchanged.
- G3-B2 evidence remains immutable: 18 performance scenarios, zero correctness failures, zero invalid runs, and 45.59283008% best simulated improvement.
- Schedule IR v2 and Agent proposal v2 integrate sparse wire accounting, CRC32 integrity, bounded retry/timeout, and bounded credit/backpressure.
- The official ACL/HCCL runtime-source target is default OFF, isolated, compile/link-only, and not executed.

Truth boundary: host-executed CPU_SIM correctness is not real NPU validation; simulator metrics are not measured device performance; direct source call expressions are readiness evidence only.
