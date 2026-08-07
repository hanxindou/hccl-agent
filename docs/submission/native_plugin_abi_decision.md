# Native plugin ABI decision

Decision states:

- `CPU_SIM_PLUGIN_SELECTED_FOR_HOST_REPRODUCTION`
- `OFFICIAL_PLUGIN_ABI_UNVERIFIED`

## Executable shared object

The host-reproducible shared object is `libhccl_plugin.so`. Its role is
`CPU_SIM_REFERENCE_PLUGIN`, its execution environment is `HOST_CPU`, and its
ABI is the project-local C ABI declared by `hcccl/include/hccl_comm.h` and
`hcccl/include/hccl_algorithms.h`. It is built with target `hccl_plugin` in the
default `CPU_SIM` mode, installed by CMake, and tested by eleven CTest cases,
the installed-package consumer, and the Python bridge.

The exact allowlisted exports are recorded in
`hcccl/submission/native_plugin_abi_manifest.json`; the linker version script
prevents accidental C or C++ symbol leakage. The expected SONAME is
`libhccl_plugin.so`, and the expected runtime dependency is the host C library.
The G3-B evidence records the observed values and hashes from two independent
clean builds.

This artifact cannot prove official HCCL loader ABI compatibility, CANN/HCOMM
runtime execution, device memory use, real communication, or real NPU
correctness/performance.

## Direct readiness artifact

`libhccl_direct_adapter.a` is a
`STATIC_BUILD_LIFECYCLE_READINESS_ARTIFACT`. It exposes only the project-owned
`hccl_direct_*` control-plane ABI. With an explicit canonical local CANN 9.1.0
root it statically freezes official `Hccl*` signatures, creates a non-executed
link-audit ELF, and runs the host-only lifecycle model. It never calls or loads
the official runtime during the G3-B workflow and is not a collective plugin.

The tracks cannot be merged: CPU_SIM accepts host buffers and executes project
collective semantics, while direct readiness freezes a future device control
boundary. Neither establishes the undocumented competition loader ABI.

## Evaluator verification

Run `python -m tools.submission_cli quick` for the host CPU_SIM artifact. Run
`python -m tools.submission_cli build --direct-readiness --cann-root <path>`
only with a locally licensed frozen SDK; inspect the direct archive and
link-audit ELF, and run only the lifecycle CTest. Do not run the link-audit
executable.

Future direct acceptance requires supported Ascend NPU hardware, authorized
runtime execution, communicator/bootstrap inputs, device buffers, per-rank API
and cleanup traces, independent D2H host references, and dedicated evidence.
