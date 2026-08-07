# Topology-aware hierarchical design

The topology model records directed links, bandwidth, latency, groups, leaders, oversubscription, degradation, and failures. Candidate schedules calculate base link cost, congestion penalty, and final cost separately, so selector decisions are auditable.

Butterfly uses recursive-doubling partners. NHR derives a weighted order with a deterministic symmetric fallback. Mesh serializes physical-edge conflicts. Hierarchical AllReduce emits intra-group reduction, inter-leader AllReduce, and intra-group distribution phases with explicit group and leader metadata. The selector returns candidate algorithms, schedule hashes, scores, rejection reasons, the selected schedule hash, and `fallback=NONE`.

This is a simulator-side topology model. It is not real HCCS, RoCE, PCIe, fabric discovery, or measured congestion evidence.
