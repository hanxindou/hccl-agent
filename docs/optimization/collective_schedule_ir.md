# Collective Schedule IR

G3-B2 freezes `g3-b2-schedule-ir-v1`. A schedule explicitly identifies the primitive, algorithm, rank size, chunks, phases, transfers, dependencies, topology hash, metadata, and canonical SHA256. Canonical JSON excludes the hash field while computing that hash and is deterministic across Python and the internal C dump tool.

The invariant audit covers schema identity, rank and chunk bounds, dependencies, duplicate writers, ownership, completeness, phase ordering, and stable replay. Ring AllReduce is ReduceScatter followed by AllGather; Ring AllGather and ReduceScatter have distinct phase semantics. Divisible and non-divisible messages at ranks 2, 4, 8, 16, and 64 are recorded in evidence.

The C schedule representation is internal. It does not change the public plugin ABI.
