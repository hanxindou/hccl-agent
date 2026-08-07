# Sparse collective semantics

AllReduce accepts different sparse patterns on every rank. The effective index set is the union of all rank indices; a missing value is an implicit numeric zero. SUM, MAX, and MIN therefore include zero correctly, including negative-only and positive-only inputs.

AllGather preserves source-rank ordering and per-rank payload boundaries. Reconstruction produces the same dense rank-major result as the existing CPU_SIM reference.

ReduceScatter first applies the reduction across source ranks, then maps each global reduced index to the owning destination segment. Sparse encoding never changes owner-rank or segment boundaries.

Positive and negative floating-point zero are both represented by the canonical implicit zero. NaN and infinity remain explicit values. Correctness is evaluated after source-dtype quantization for FP32, FP16, and BF16.
