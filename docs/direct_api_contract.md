# G2-F-1 Direct API ABI Contract

The machine-readable contract is [cann_hccl_9.1.0.json](../hcccl/direct/manifest/cann_hccl_9.1.0.json). It freezes the actual CANN 9.1.0 x86_64-linux headers, libraries, hashes, SONAMEs, dependencies, exported symbols, HCOMM/HCCL source revisions, and candidate host-side API signatures.

The contract is a `SYMBOL_DISCOVERY_PASS` artifact only. Its verifier uses file hashing, `readelf`, `nm`, and command-scoped Git metadata reads. It never loads a shared library and never calls `aclInit`, ACL device APIs, communicator APIs, or collective APIs.

The public collective declarations do not state whether their buffer pointers are host or device pointers. This remains `UNRESOLVED`; the future adapter must reject host pointers for a collective until an official example or real-device contract proves the accepted locality.

The frozen lifecycle for a future real-device stage is runtime → device/context → stream → communicator → device buffers → copy → collective → synchronize → copy-back → reverse cleanup. None of those steps is implemented or executed in G2-F-1.

## G2-F-3 link and no-device boundary

With `-DHCCL_ENABLE_ASCEND_HCCL_DIRECT=ON` and an explicit frozen
`HCCL_CANN_ROOT`, CMake retains the F2 `hccl_direct_adapter` static
compile-only target and also creates `hccl_direct_link_audit`. The latter is an
ELF inspection artifact, not an executable test: it directly links the exact
canonical `libhccl.so`, `libhcomm.so`, and `libacl_rt.so` paths and retains
their `NEEDED` entries for `readelf`/`ldd` auditing. It must never be run in
G2-F-3.

`plugin.direct_api_backend` is a standard-library-only preflight/guard. Its
no-device result has `backend=ASCEND_HCCL_DIRECT`, `status=NO_DEVICE_EXPECTED`,
and all runtime/device/communicator/collective claims false. It imports no
CANN bindings and rejects lifecycle or collective requests before a native
runtime call can exist. Dynamic loading remains `DYNAMIC_LOAD_NOT_EXECUTED`:
there is no approved proof that merely loading the official DSOs is
side-effect-free.
