# G3-B3 lossless sparse design

The G3-B3 sparse path is an internal `SPARSE_INDEX_VALUE` payload transform. It preserves the source FP32, FP16, or BF16 representation of every nonzero element, orders indices canonically, rejects duplicate or out-of-range indices, and reconstructs a dense payload before the existing CPU_SIM semantic kernel consumes it.

Selection is cost based. The implementation compares index bytes, value bytes, fixed metadata, detection cost, encoding cost, and decoding cost with the dense payload cost. Low-sparsity and metadata-dominated payloads remain dense and carry an explicit fallback reason. No public function, public structure, enum value, SONAME, or exported symbol is added.

`wire_bytes` means modeled or host payload bytes. The implementation does not observe physical NIC traffic and does not execute ACL or HCCL runtime APIs.

Logical payloads of at least 1 GiB use chunked accounting with a bounded peak materialization contract. The large-message evidence does not allocate a full logical tensor.
