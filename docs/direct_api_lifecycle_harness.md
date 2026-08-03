# G2-F-4 Guarded Lifecycle Harness

The direct adapter has a host-only lifecycle model for deterministic contract
tests. It owns no ACL/HCCL resource and its C ABI never invokes an official
runtime API in this checkpoint. The only permitted current-environment flow is
`CREATED → CONFIGURED → PREFLIGHT_CHECKED → NO_DEVICE_EXPECTED → DESTROYED`.

The model-only test API verifies prospective runtime/device/context/stream/
communicator/buffer ownership, reverse cleanup, lease accounting, capacity and
failure injection. Those transitions are abstract control-plane records only;
they do not represent real device state or API results.

Future real-device execution remains out of scope. A future launcher must be
explicitly opt-in with `HCCL_DIRECT_REAL_DEVICE=1`, an approved rank-table,
real devices and the G2-F-5 acceptance procedure. Setting that environment
variable cannot bypass the G2-F-4 guard.
