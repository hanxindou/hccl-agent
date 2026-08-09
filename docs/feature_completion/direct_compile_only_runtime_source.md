# Direct compile-only runtime source

`HCCL_ENABLE_ASCEND_HCCL_RUNTIME_SOURCE` is default OFF and requires the existing direct-readiness option plus an explicit frozen CANN root. It builds a separate shared inspection artifact containing guarded official ACL/HCCL call expressions and reverse-order cleanup.

The target is not linked into `libhccl_plugin.so`, has no executable entry point, is not registered with CTest, and is never loaded or executed by the submission CLI. Its result is `DIRECT_READINESS_ONLY`, not real-device validation.
