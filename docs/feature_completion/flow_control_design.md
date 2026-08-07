# G3-B3 bounded credit flow control

The G3-B3 model uses a deterministic credit window to bound materialized chunks. A producer consumes one credit per enqueued chunk, pauses at the high watermark, resumes after the queue reaches the low watermark, and receives credit only when the consumer completes a chunk.

The hard invariants are non-negative credit, conserved credit, bounded in-flight chunks, bounded memory, FIFO fairness, eventual drain, and no deadlock. Normal load, temporary congestion, sustained congestion, and recovery are replayed with fixed consumer-capacity patterns.

This is a host/simulator backpressure model. It is not HCCL, NIC, RoCE, or real-device flow control.
