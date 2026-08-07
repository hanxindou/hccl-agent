# G3-B3 data-aware Agent decision

The versioned G3-B3 Agent evaluates every invariant-valid G3-B2 algorithm with dense and, when cost-eligible, lossless `SPARSE_INDEX_VALUE` payload modes. The score includes logical, value, index, sparse metadata, integrity metadata, CRC, expected retry bytes, codec work, and modeled producer blocking.

Selection is permitted only after codec, reconstruction, CRC, retry, credit, memory, drain, and fairness gates pass. The proposal records the selected algorithm, payload mode, chunk and pipeline bounds, credit window, integrity/retry policies, fallback conditions, expected benefit, and the host-model risk boundary.

The Agent does not infer physical wire traffic or Ascend runtime performance from this model.
