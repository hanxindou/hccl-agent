# G3-B3 integrity, CRC32, timeout, and retry

The private CPU_SIM transport validates every dense or sparse payload chunk before the existing collective semantic kernel accepts it. Metadata contains transfer, sequence, chunk, attempt, payload-length, and CRC32 identity. CRC32 uses the standard IEEE polynomial and is cross-checked between C and Python with published check vectors.

Fault injection is test-only and deterministic. Supported cases include bit and byte corruption, CRC tampering, logical timeout, transient transfer failure, duplicate sequence, missing chunk, reordered sequence, invalid input, and no alternate path. The production default contains no injected fault.

CRC mismatch, logical timeout, and transient transfer failure are retryable. Invalid arguments are non-retryable. Retry exhaustion, sequence failure, and no alternate path are terminal. No-path is not rewritten as timeout and does not trigger blind retry.

Timeouts use logical event ticks; tests never sleep. `attempt_count` is bounded by `max_retries + 1`, and retransmitted payload bytes are accounted explicitly. Chunk verification uses a bounded temporary buffer.

All evidence is host execution. It does not represent hardware CRC, NIC/HCCL retransmission, real network timeout, failover, or device-runtime execution.
