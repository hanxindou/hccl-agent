# HCCL Plugin - CPU Simulation Baseline

This directory contains the C CPU-simulated plugin baseline used by the
HCCL-Agent project. It is useful for local algorithm and bridge testing,
but it is not a real CANN/HCOMM/Ascend implementation.

## What Is Real

- `hcclCommInit`, `hcclCommDestroy`, `hcclGetTopology`, and
  `hcclFreeTopology` are implemented as CPU-only simulation helpers.
- `ring_allreduce`, `butterfly_allreduce`, `mesh_allreduce`,
  `nhr_allreduce`, and `fattree_allreduce` execute FP32/SUM
  AllReduce-style CPU simulations for `count == 1`.
- `CMakeLists.txt` builds a shared library and six C test programs in
  CPU mode on Windows/MSVC and Linux-like toolchains.
- CTest registers the six C test executables: `test_topology`,
  `test_ring`, `test_butterfly`, `test_nhr`, `test_mesh`, and
  `test_fattree`.

## What Is Stub or Not Yet Implemented

- This build does not link CANN, HCOMM, Ascend drivers, RDMA, or real
  device communication libraries.
- FP16, BF16, and ReduceOps other than SUM are not implemented.
- Multi-element collective data paths are not implemented in the current
  C simulation.
- `butterfly_allgather` and `mesh_reducescatter` are still stubs.
- Standard HCCL wrapper closure and Python loader changes are intentionally
  left for a later batch.

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
cmake --build /tmp/hccl-agent-hcccl-a1
ctest --test-dir /tmp/hccl-agent-hcccl-a1 --output-on-failure
```

Do not treat a Windows DLL build as proof that Linux `.so` or Ascend
deployment has been verified.

## Ascend/CANN Boundary

Real competition deployment still requires CANN 8.0+ / HCOMM headers and
libraries, Ascend hardware or an approved simulator, and validation
against HCCL-compatible baselines. That work is outside Batch A1.

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
