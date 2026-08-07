# G3-B3 feature-completion ablation

G3-B3 defines B0–B6 for dense baseline, sparse codec, wire-aware cost, Agent payload selection, CRC, retry, and credit flow-control. These stages are separate from and do not alter G3-B2 A0–A7 scheduling-optimization evidence.

Every stage retains the frozen sparse scenarios, including dense fallbacks and unfavorable cases. Correctness is a hard gate; modeled cost never overrides a codec, integrity, retry, or flow invariant failure.
