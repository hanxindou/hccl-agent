# Chunk and pipeline design

Chunk choice searches finite candidates under the frozen 64 MiB budget. Logical message size is separate from transport chunk size. The bounded-memory audit uses streaming materialization and records chunk buffers, temporary buffers, materialized depth, peak bytes, and the logical-to-materialized ratio; the 1 GiB and 2 GiB logical cases remain bounded.

The pipeline model has two explicit modes: `NO_OVERLAP` and `SIMULATED_PIPELINED_OVERLAP`. The latter models exposed critical-path overlap only. It is not an implementation or measurement of device-side compute/communication overlap, UB/HBM reuse, zero-CPU execution, or training acceleration.
