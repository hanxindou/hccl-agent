# Trace and Provenance Index

Report Status: `G3_D_EVIDENCE_DERIVED`  
Execution Identity: `RECONSTRUCTED_FROM_FROZEN_EVIDENCE`  
Real-device Validated: `false`  
Runtime API Executed: `false`

## Validation Identity

The index contains 2 normalized evidence lines: G3-B2 optimization and G3-B3 feature completion. Normalization preserves source pointers/hashes and does not rewrite frozen history.

## Provenance

- G3-B2 retains historical proposal/evaluation/reflection/human records and simulated performance identity.
- G3-B3 retains 20 proposal, 20 evaluation, and 20 reflection records; its historical Prompt/Response relationship remains unavailable.
- New replay output is `REPLAYED_FROM_FROZEN_TRACE`, never historical execution.

## Claim Boundaries

G3-B2 performance remains `SIMULATED_ONLY`; G3-B3 host/simulator identities remain separated.

## Known Limitations

Normalized traces are reconstructions, not original raw Agent logs. Hidden reasoning is not included.
