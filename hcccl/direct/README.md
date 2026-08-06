# Direct readiness package

This directory is an **OFFICIAL-ABI DIRECT READINESS ADAPTER** source package.
It freezes official CANN/HCCL 9.1.0 signatures, a project-owned direct
control-plane ABI, capacity and lifecycle contracts, failure injection, and a
non-executed link-audit artifact. It is not an official collective plugin and
does not execute ACL/HCCL runtime calls.

Configure it only with an explicit, locally licensed canonical SDK root:

```bash
cmake -S hcccl -B build/direct-readiness \
  -DHCCL_BACKEND=CPU_SIM \
  -DHCCL_ENABLE_ASCEND_HCCL_DIRECT=ON \
  -DHCCL_CANN_ROOT=/home/workspace/Ascend/cann-9.1.0
cmake --build build/direct-readiness
ctest --test-dir build/direct-readiness -R hccl_direct_lifecycle --output-on-failure
```

The SDK and official DSOs are not redistributed. The link-audit executable is
for ELF inspection only and must never be run. With no device, the supported
preflight result is `NO_DEVICE_EXPECTED`; real-device acceptance remains
`HARDWARE_BLOCKED`.
