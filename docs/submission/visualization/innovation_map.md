# Evidence-backed Innovation Map

These are competition-facing technical differentiators, not unsupported novelty or production claims.

## INNOV-01 — Topology-aware Schedule IR optimization pipeline

Problem: Collective selection must expose auditable topology, chunking, dependency, and cost decisions instead of hiding them inside a monolithic algorithm call.

Mechanism: A shared Schedule IR v2 carries phases and reliability metadata into topology-aware schedule generation, selector scoring, deterministic evaluation, and replanning.

Agent role: The Agent proposes and replans schedules; deterministic gates evaluate them; human governance freezes accepted scope.

Validation: Python/C schedule parity, schema and invariant audits, frozen simulator comparison, and offline trace replay.

Truth identity: `HOST_EXECUTED, SIMULATED_ONLY, AGENT_GENERATED, DETERMINISTIC_EVALUATION`

Claims: `C-IR-001, C-PIPE-001, C-PERF-001`; figures: `FIG-02, FIG-03, FIG-11, FIG-13`.

Limitations: performance results are simulator/model outcomes; no real-device collective was executed.

## INNOV-02 — Evidence-governed Agent optimization and feature loop

Problem: Agent proposals are difficult to trust when proposal, evaluation, human intervention, and evidence provenance are not separable.

Mechanism: Normalized proposal/evaluation/reflection/replanning records map prompts and skills through deterministic gates to sources, commits, evidence, figures, and claim boundaries.

Agent role: The Agent supplies proposals and reflections; deterministic evaluators and explicit human gates control decisions.

Validation: Mandatory offline replay verifies hashes, schemas, decision flow, human-intervention fields, and frozen source pointers without API keys.

Truth identity: `AGENT_GENERATED, DETERMINISTIC_EVALUATION, HUMAN_INTERVENTION, OFFLINE_REPLAY, RECONSTRUCTED_FROM_FROZEN_EVIDENCE`

Claims: `C-PERF-001, C-IR-001, C-INT8-001, C-PAIR-001`; figures: `FIG-08, FIG-09`.

Limitations: normalized traces are not hidden chain-of-thought; G3-B3 historical Prompt/Response is unavailable.

## INNOV-03 — Lossless sparse collective path with wire-aware fallback

Problem: Sparse communication can add index overhead and lose value unless density, encoding, reconstruction, and dense fallback share one accounting boundary.

Mechanism: A lossless index/value codec, sparse reconstruction, modeled wire-byte accounting, break-even decision, and dense fallback integrate with collective and schedule paths.

Agent role: The Agent feature loop proposed sparse delivery and recorded its evidence-gated implementation decision.

Validation: Host-executed correctness/parity cases plus frozen logical byte, compression-ratio, and break-even accounting.

Truth identity: `LOSSLESS_SPARSE_HOST_EXECUTED`

Claims: `C-SPARSE-001, C-SPARSE-002, C-SPARSE-003`; figures: `FIG-06`.

Limitations: wire bytes are modeled/logical accounting, not NIC measurement; sparse path is not real-device validated.

## INNOV-04 — Layered integrity, retry, and backpressure contract

Problem: Reliability claims become misleading when host corruption checks, retry policy, and simulator flow control are blended into one hardware claim.

Mechanism: CRC32 sequence/chunk integrity metadata and retry budgets execute on host paths, while credit/backpressure semantics remain a Schedule IR and simulator layer.

Agent role: The feature Agent proposed reliability work; deterministic gates split implemented host semantics from simulator-only backpressure.

Validation: C/Python CRC parity, corruption injection/detection, retry recovery/exhaustion cases, and simulated credit-window scenarios.

Truth identity: `HOST_INTEGRITY_VALIDATED, HOST_RETRY_VALIDATED, SIMULATED_BACKPRESSURE`

Claims: `C-CRC-001, C-RETRY-001, C-BP-001`; figures: `FIG-07, FIG-12`.

Limitations: no NIC or HCCL hardware reliability validation; backpressure is simulated rather than host-runtime executed.

## INNOV-05 — Layered CPU_SIM ABI and Direct production readiness

Problem: A submission plugin needs reproducible CPU validation while retaining a credible path toward official ACL/HCCL integration without pretending hardware execution.

Mechanism: The frozen CPU_SIM plugin preserves SONAME and 19-symbol ABI; a default-OFF Direct adapter expresses official calls and supports compile/link/lifecycle readiness artifacts.

Agent role: Agent and report layers describe capability boundaries; no runtime Agent action invokes ACL/HCCL in the mandatory path.

Validation: Linux CPU_SIM ABI/CTest/pytest validation plus Direct declaration, expression, compile, link, and lifecycle readiness checks.

Truth identity: `CPU_EXECUTED, DIRECT_COMPILE_LINK_ONLY, REAL_DEVICE_NOT_EXECUTED`

Claims: `C-ABI-001, C-DIRECT-001, C-DIRECT-002`; figures: `FIG-01, FIG-10, FIG-12`.

Limitations: Direct artifact is readiness-only; real-device acceptance remains HARDWARE_BLOCKED.
