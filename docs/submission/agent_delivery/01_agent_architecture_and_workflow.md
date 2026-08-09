# Agent Architecture and Workflow

Report Status: `G3_D_EVIDENCE_DERIVED`  
Execution Identity: `AGENT_ASSISTED_OFFLINE_REPLAY`  
Real-device Validated: `false`  
Runtime API Executed: `false`

## Validation Identity

The current system separates the `HCCLAgent` orchestrator, optional online reasoning, deterministic G3-B2/G3-B3 loops, Prompt loading, Skills, CPU_SIM execution, simulator evaluation, and evidence/reporting layers. Mandatory delivery replay reads normalized frozen evidence and does not invoke `HCCLAgent.run()`.

## Workflow

`input → proposal → deterministic evaluation → reflection/replanning → final decision → evidence/claim reference`

`AGENT_GENERATED` identifies recorded proposals; `DETERMINISTIC_EVALUATION` identifies code/schema/correctness/cost gates; `HUMAN_INTERVENTION` identifies an explicit actor decision. These identities do not imply unsupervised development.

## Claim Boundaries

The architecture is Agent-assisted and human-governed. CPU_SIM and simulator evidence do not establish real-device execution.

## Known Limitations

Optional provider reasoning is not part of mandatory replay. Existing ignored local logs are not authority evidence.
