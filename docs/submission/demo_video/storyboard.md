# G3-F Storyboard

No screen recording or video binary has been created.

## SCENE-01 — Problem

Frame the collective-optimization and evidence-delivery problem

- Visual: `TEXT_CARD` / `[]`
- Truth badge: `EVIDENCE_SCOPE_DECLARED`
- Fallback: `TEXT-CARD-PROBLEM`
- Limitations: project value is bounded by frozen evidence

## SCENE-02 — System architecture

Show execution, simulation, Agent, and readiness layers

- Visual: `ARCHITECTURE_DIAGRAM` / `docs/submission/visualization/assets/diagrams/fig-01-system-execution-and-validation-architecture.svg`
- Truth badge: `LAYERED_TRUTH_BOUNDARY`
- Fallback: `FIG-01`
- Limitations: layers have different evidence identities

## SCENE-03 — Why static selection is insufficient

Explain schedule/topology-aware choice

- Visual: `ARCHITECTURE_DIAGRAM` / `docs/submission/visualization/assets/diagrams/fig-02-schedule-ir-and-topology-aware-optimization-pipeline.svg`
- Truth badge: `SIMULATED_ONLY`
- Fallback: `FIG-02`
- Limitations: selection evidence uses a frozen analytical simulator

## SCENE-04 — Schedule and topology optimization

Present the frozen 18/0/0 result and 45.59% simulated improvement

- Visual: `REGISTERED_FIGURE` / `docs/submission/visualization/assets/charts/fig-04-18-wins-0-ties-0-losses.svg`
- Truth badge: `SIMULATED_ONLY`
- Fallback: `FIG-04`
- Limitations: 45.59283008% raw / 45.59% display is frozen simulated evidence

## SCENE-05 — Agent-assisted decision loop

Replay proposal, deterministic evaluation, reflection, replanning, and selection

- Visual: `LIVE_TERMINAL` / `['DEMO-AGENT-REPLAY']`
- Truth badge: `OFFLINE_REPLAY`
- Fallback: `FALLBACK-AGENT-REPLAY`
- Limitations: replay is not original historical execution; human governance remains disclosed

## SCENE-06 — Frozen simulated evidence

Show logical scale trends with visible model boundary

- Visual: `REGISTERED_FIGURE` / `docs/submission/visualization/assets/charts/fig-05-logical-scale-trend.svg`
- Truth badge: `SIMULATED_ONLY, LOGICAL_MODEL_SCALE`
- Fallback: `FIG-05`
- Limitations: 1024 ranks is logical/model scale

## SCENE-07 — Sparse and reliability

Separate host sparse/integrity/retry evidence from simulator backpressure

- Visual: `REGISTERED_FIGURE` / `docs/submission/visualization/assets/charts/fig-07-integrity-retry-and-backpressure-layers.svg`
- Truth badge: `HOST_VALIDATED, SIMULATED_BACKPRESSURE`
- Fallback: `FIG-07`
- Limitations: sparse wire bytes are modeled; backpressure is simulator-only; no NIC/HCCL hardware reliability validation

## SCENE-08 — Direct readiness boundary

Explain the official ACL/HCCL production source path without executing it

- Visual: `ARCHITECTURE_DIAGRAM` / `docs/submission/visualization/assets/diagrams/fig-10-direct-readiness-validation-ladder.svg`
- Truth badge: `DIRECT_COMPILE_LINK_ONLY, REAL_DEVICE_NOT_EXECUTED`
- Fallback: `FIG-10`
- Limitations: 17 official call expressions are compile/link-only readiness; runtime execution remains absent

## SCENE-09 — Offline reproducibility and live demo

Execute the project-owned CPU_SIM path and verify figures offline

- Visual: `LIVE_TERMINAL` / `['DEMO-CPU-SIM', 'DEMO-VISUAL-VERIFY']`
- Truth badge: `HOST_VALIDATED, REAL_DEVICE_NOT_EXECUTED`
- Fallback: `FALLBACK-CPU-SIM`
- Limitations: CPU_SIM host execution only; visual verification does not rerun benchmarks

## SCENE-10 — Limitations

Make all execution and evidence boundaries explicit before the closing claim

- Visual: `ARCHITECTURE_DIAGRAM` / `docs/submission/visualization/assets/diagrams/fig-12-truth-and-evidence-boundary-matrix.svg`
- Truth badge: `REAL_DEVICE_NOT_EXECUTED`
- Fallback: `FIG-12`
- Limitations: real-device acceptance remains HARDWARE_BLOCKED; no ACL/HCCL runtime was executed

## SCENE-11 — Competition value

Close with evidence-backed engineering value and reproducibility

- Visual: `REGISTERED_FIGURE` / `docs/submission/visualization/assets/charts/fig-13-algorithm-and-topology-coverage.svg`
- Truth badge: `EVIDENCE_BACKED, REAL_DEVICE_NOT_EXECUTED`
- Fallback: `FIG-13`
- Limitations: competition innovation wording is project-scoped, not a global novelty claim
