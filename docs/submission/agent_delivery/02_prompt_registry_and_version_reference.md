# Prompt Registry and Version Reference

Report Status: `G3_D_EVIDENCE_DERIVED`  
Execution Identity: `CURRENT_CANONICAL_AND_HISTORICAL_EVIDENCE`  
Real-device Validated: `false`  
Runtime API Executed: `false`

## Validation Identity

The machine-readable registry contains 12 entries. Five G3-B2 Prompt identities retain frozen version `1.0.0` and source hashes. Current template/inline prompts use source-hash versions; they do not receive invented historical versions.

## Version Rules

- `AVAILABLE_IN_FROZEN_EVIDENCE`: historical id/version/hash is proven.
- `HISTORICAL_TRACE_UNAVAILABLE`: only current canonical source is proven.
- `ONLINE_LLM_OPTIONAL`: never required by mandatory replay.

## Claim Boundaries

Prompt text is not evidence that a capability was implemented or executed. Missing provider responses are not reconstructed.

## Known Limitations

G3-B3 has no asserted historical Prompt/Response relationship. Several current templates contain aspirational language and are bounded by the claim ledger.
