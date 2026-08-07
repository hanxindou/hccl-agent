# G3-B3-E official runtime source boundary

`hccl_direct_runtime_source` is a default-OFF, compile/link-only shared build artifact containing actual frozen CANN/HCCL 9.1.0 call expressions. It is independent from both `libhccl_plugin.so` and the existing `libhccl_direct_adapter.a` readiness model.

The target has no executable entry point, is not registered with CTest or the submission CLI, and rejects calls unless an explicit internal authorization token is supplied. Host-only acceptance compiles, links, and inspects it with `file`, `readelf`, `nm`, and `ldd`; it never loads or executes the artifact.

Compilation and linking prove source/API compatibility only. They do not prove ACL initialization, device/context/stream creation, communicator creation, collective execution, synchronization, cleanup behavior on hardware, or official plugin-loader acceptance. Those remain `HARDWARE_BLOCKED`.
