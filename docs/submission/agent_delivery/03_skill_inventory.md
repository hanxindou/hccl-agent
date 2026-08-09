# Skill Inventory

Report Status: `G3_D_EVIDENCE_DERIVED`  
Execution Identity: `CURRENT_SOURCE_REGISTRY`  
Real-device Validated: `false`  
Runtime API Executed: `false`

## Validation Identity

The machine-readable registry contains 31 source-backed entries from `agent/` and `skills/`. Each entry records source SHA, public callable inventory, stage, deterministic classification, tests, evidence, and limitations.

## Classification

- `DETERMINISTIC`: source behavior can run without an external model.
- `OPTIONAL_ONLINE`: provider/key/network dependent and excluded from mandatory replay.
- `HOST_EXECUTED`: project host/CPU_SIM execution only.
- `SIMULATOR_MODEL`: modeled rather than physical execution.
- `PARTIAL`: no focused test mapping was discovered.

## Claim Boundaries

A registered Skill is a current source fact, not a real-device validation claim.

## Known Limitations

Registry coverage does not promote untested modules. Roadmap and Prompt-only capabilities are excluded from implementation claims.
