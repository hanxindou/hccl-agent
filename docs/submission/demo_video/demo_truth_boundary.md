# Demo Truth Boundary

- `LIVE_DEMO_CPU_SIM` is host execution, not Ascend/NPU validation.
- `DEMO_REPLAY` is an offline replay, not original historical Agent execution.
- `SIMULATED_ONLY` performance values remain simulated; 45.59% is never an NPU measurement.
- Direct remains `DIRECT_COMPILE_LINK_ONLY` and `REAL_DEVICE_NOT_EXECUTED`.
- Fallback output is `PRERECORDED_DETERMINISTIC_OUTPUT`; it must never impersonate a live command.
