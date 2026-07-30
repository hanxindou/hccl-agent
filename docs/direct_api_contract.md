# G2-F-1 Direct API ABI Contract

The machine-readable contract is [cann_hccl_9.1.0.json](../hcccl/direct/manifest/cann_hccl_9.1.0.json). It freezes the actual CANN 9.1.0 x86_64-linux headers, libraries, hashes, SONAMEs, dependencies, exported symbols, HCOMM/HCCL source revisions, and candidate host-side API signatures.

The contract is a `SYMBOL_DISCOVERY_PASS` artifact only. Its verifier uses file hashing, `readelf`, `nm`, and command-scoped Git metadata reads. It never loads a shared library and never calls `aclInit`, ACL device APIs, communicator APIs, or collective APIs.

The public collective declarations do not state whether their buffer pointers are host or device pointers. This remains `UNRESOLVED`; the future adapter must reject host pointers for a collective until an official example or real-device contract proves the accepted locality.

The frozen lifecycle for a future real-device stage is runtime → device/context → stream → communicator → device buffers → copy → collective → synchronize → copy-back → reverse cleanup. None of those steps is implemented or executed in G2-F-1.
