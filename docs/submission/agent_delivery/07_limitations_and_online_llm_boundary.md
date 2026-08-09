# Limitations and Online LLM Boundary

Report Status: `G3_D_EVIDENCE_DERIVED`  
Execution Identity: `ONLINE_LLM_OPTIONAL`  
Real-device Validated: `false`  
Runtime API Executed: `false`

## Validation Identity

`agent/llm_client.py`, `ReasoningSkill`, and online decision support remain optional. Mandatory G3-D validation does not instantiate them.

## Boundaries

- No real Ascend NPU, ACL/HCCL runtime, communicator, collective, MPI, `hccl_test`, or `msprof` is executed.
- Sparse correctness is host-observed; wire bytes are modeled.
- CRC/retry are host validated; backpressure is simulated.
- Direct source is compile/link-only and runtime calls remain empty.
- INT8 is deferred by its precision gate; PairWise is skipped by its value gate.

## Claim Boundaries

All external wording resolves through the G3-C claim ledger. The weighted optimization result is a simulator result against the frozen baseline.

## Known Limitations

Real-device acceptance remains blocked on hardware evidence. Original historical Prompt/Response data is incomplete.
