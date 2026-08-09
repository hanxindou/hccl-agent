# Competition Narrative

Status: `EVIDENCE_BACKED_SUBMISSION_NARRATIVE`

## 30-second layer

HCCL Agent is an Agent-assisted collective-communication optimization and delivery system. It turns topology and workload constraints into an auditable Schedule IR, proposes schedules and feature decisions, evaluates them deterministically, and preserves explicit human governance. Against the frozen fixed-Ring baseline, its communication simulator records a weighted collective-time improvement of 45.59% with 18 wins, 0 ties, and 0 losses across the frozen scenario inventory. This is `SIMULATED_ONLY`; it is not Ascend/NPU or training performance.

## 3-minute layer

1. **Problem.** Collective optimization spans topology, algorithm selection, scheduling, reliability, and delivery constraints. A useful competition system must expose those decisions and their evidence rather than present one opaque result.
2. **System.** Schedule IR v2 connects topology-aware proposal, selector and cost-model evaluation, CPU_SIM validation, simulator acceptance, and a separate Direct readiness track. CPU_SIM remains the default project-owned host backend; simulator acceptance is an independent validation track.
3. **Optimization.** The Agent proposes and replans; deterministic evaluation checks frozen scenario outcomes; human-governed gates decide what is accepted. The canonical outcome is 45.59% weighted simulated collective-time improvement and 18/0/0 wins/ties/losses against fixed Ring.
4. **Feature completion.** The lossless sparse codec is host validated and paired with modeled byte accounting and dense fallback. CRC32 integrity and bounded retry are host validated. Credit flow control and backpressure remain simulator modeled.
5. **Negative decisions.** INT8 is `DEFERRED_BY_PRECISION_GATE`; PairWise is `SKIPPED_BY_VALUE_GATE`. These decisions remain visible because the evidence gate is part of the contribution.
6. **Delivery.** The mandatory Agent replay path is offline and API-key-free. The project CPU_SIM ABI remains frozen. Official ACL/HCCL calls exist in a compile/link-only Direct source path that was not loaded or executed.
7. **Boundary.** Logical scale is not a physical device cluster; modeled wire bytes are not NIC measurements; real-device acceptance remains `HARDWARE_BLOCKED`.

## Technical-defense layer

The defensible chain is `Prompt → Skill → normalized Agent trace → implementation source → source commit → frozen evidence → G3-C claim → G3-E figure`. Proposal, deterministic evaluation, human intervention, replay, and reconstruction are separately labeled. G3-E introduces no new algorithm, benchmark, metric, or claim; it renders and narrates frozen G3-C/G3-D authorities.

The optimization result must always be described as communication-simulator evidence. The sparse contribution combines host-observed lossless correctness with modeled/logical byte accounting. Reliability evidence is intentionally split into host integrity, host retry, and simulated backpressure. Direct readiness proves source-expression and compile/link preparation only; no ACL/HCCL runtime, communicator, collective, MPI, profiling, or real device was executed in G3-E.
