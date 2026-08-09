# Schedule IR v2

`g3-b3-schedule-ir-v2` extends the frozen G3-B2 v1 schedule with payload transform, integrity, transport, and flow-control policies. V1 inputs remain unchanged; the upgrade creates a copy, recalculates the canonical hash, and preserves dense behavior until a validated selector decision chooses sparse transport.

The extension carries logical and wire byte accounting, CRC/sequence/chunk identity, bounded retry/timeout classification, and credit-window bounds. These fields are internal orchestration contracts and do not change the public plugin ABI.
