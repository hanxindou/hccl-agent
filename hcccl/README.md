# HCCL Plugin — C/C++ Skeleton

This directory contains the C/C++ HCCL plugin skeleton required by the
competition.  **It cannot currently be compiled** — the CANN 8.0 SDK is
required.

## What is REAL

- **Interface declarations** in `include/hccl_comm.h` and
  `include/hccl_algorithms.h` match the HCOMM open-source public API
  (Gitee: ascend/cann-hcomm).
- **Algorithm descriptions** in the `src/*.c` comments document the
  intended implementation for each algorithm (Ring, Butterfly, Mesh,
  NHR, Fat-Tree).
- **CMakeLists.txt** is a valid CMake build that will work once the
  CANN SDK paths are configured.

## What is STUB

- All function bodies in `src/*.c` return `HCCL_ERR_NOT_SUPPORTED` and
  log a message to stderr.  They are placeholders.

## What you need to make this real

1. **CANN 8.0 SDK** — installed on a machine with Ascend NPU drivers.
   Download from https://www.hiascend.com/.
2. **HCOMM headers & libraries** — part of the CANN SDK.
3. **Ascend NPU hardware** (910A2/910A3/910B/910C) or the Ascend
   simulator for verification.

## Build (once SDK is available)

```bash
cd hcccl
mkdir build && cd build
cmake -DCANN_HOME=/usr/local/Ascend/ascend-toolkit/latest ..
make -j$(nproc)
# Output: libhccl_plugin.so
```

## Structure

```
hcccl/
├── CMakeLists.txt           # CMake build (valid, needs SDK)
├── README.md                # This file
├── include/
│   ├── hccl_comm.h          # Comm lifecycle, topology, primitives
│   └── hccl_algorithms.h    # Algorithm entry points
├── src/
│   ├── hccl_comm.c          # STUB — comm init/finalize/topology
│   └── hccl_algorithms.c    # STUB — AllReduce/AllGather/ReduceScatter
└── tests/                   # Reserved for future test code
```

## Interface provenance

The following interfaces are declared based on the public HCOMM
repository (Gitee: ascend/cann-hcomm):

| Function | Source |
|----------|--------|
| `hcclCommInit` | HCOMM public API |
| `hcclCommDestroy` | HCOMM public API |
| `hcclGetTopology` | HCOMM public API |
| `hcclAllReduce` | HCOMM public API |
| `hcclAllGather` | HCOMM public API |
| `hcclReduceScatter` | HCOMM public API |
| `hcclBroadcast` | HCOMM public API |
