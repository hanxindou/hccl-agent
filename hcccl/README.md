# CPU_SIM reference collective plugin

`libhccl_plugin.so` is the project-owned `CPU_SIM_REFERENCE_PLUGIN`. It is
useful for deterministic host algorithm and bridge testing, but it is not an
official HCCL loader plugin and is not a CANN/HCOMM/Ascend runtime artifact.

## What Is Real

- `hcclCommInit`, `hcclCommDestroy`, `hcclGetTopology`, and
  `hcclFreeTopology` are implemented as CPU-only simulation helpers.
- `ring_allreduce`, `butterfly_allreduce`, `mesh_allreduce`,
  `nhr_allreduce`, and `fattree_allreduce` execute FP32/SUM
  AllReduce-style CPU simulations for `count == 1`.
- `CMakeLists.txt` builds a shared library and six C test programs in
  CPU mode on Windows/MSVC and Linux-like toolchains.
- CTest registers eleven CPU_SIM test executables covering topology,
  algorithms, wrappers, collectives, reduce operations, and dtype emulation.

## Truthfulness boundary

- This build does not link CANN, HCOMM, Ascend drivers, RDMA, or real
  device communication libraries.
- No ACL/HCCL runtime API is called, no device memory is used, and no real
  communicator or collective is created.
- The project-local CPU_SIM ABI, the direct control-plane ABI, and the
  unverified official plugin ABI are separate contracts.
- The direct package under `direct/` is readiness-only and is not loaded by
  the Python CPU_SIM bridge.

## Windows CPU Build

```cmd
set BUILD_DIR=F:\build\hccl-agent-hcccl-a1
cmake -S hcccl -B "%BUILD_DIR%" -G "Visual Studio 17 2022" -A x64
cmake --build "%BUILD_DIR%" --config Release
ctest --test-dir "%BUILD_DIR%" -C Release --output-on-failure
```

The default Windows configuration enables symbol export so the build
produces both:

```text
Release\hccl_plugin.dll
Release\hccl_plugin.lib
```

## Linux CPU Build

When Linux or WSL is available, use an external build directory:

```bash
cmake -S hcccl -B /tmp/hccl-agent-hcccl-a1
cmake --build /tmp/hccl-agent-hcccl-a1 --config Release
ctest --test-dir /tmp/hccl-agent-hcccl-a1 --output-on-failure
cmake --install /tmp/hccl-agent-hcccl-a1 --prefix /tmp/hccl-agent-install/native
```

Do not treat a Windows DLL build as proof that Linux `.so` or Ascend
deployment has been verified.

## Ascend/CANN Boundary

Direct readiness requires a locally licensed CANN 9.1.0 root explicitly
passed to CMake. Official SDK files are never installed or staged. Real-device
acceptance remains `HARDWARE_BLOCKED`.

## Structure

```text
hcccl/
├── CMakeLists.txt           # CPU simulation CMake build
├── README.md                # This file
├── include/
│   ├── hccl_comm.h          # HCCL-like declarations
│   └── hccl_algorithms.h    # Algorithm entry points
├── src/
│   ├── hccl_comm.c          # CPU-simulated comm init/finalize/topology
│   └── hccl_algorithms.c    # CPU-simulated AllReduce family + stubs
└── tests/                   # C test executables registered with CTest
```

## Interface Provenance

The declarations are HCCL-like project declarations inspired by public
HCOMM/HCCL concepts. Full HCOMM/CANN ABI compatibility is not claimed
until the dedicated interface-compatibility batch is completed.
