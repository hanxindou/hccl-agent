# Offline Replay Guide

Report Status: `G3_D_EVIDENCE_DERIVED`  
Execution Identity: `OFFLINE_REPLAY`  
Real-device Validated: `false`  
Runtime API Executed: `false`

## Validation Identity

Mandatory replay requires Python and repository files only. It does not read model API keys and does not access a network.

## Commands

```bash
python -m tools.agent_delivery_cli describe
python -m tools.agent_delivery_cli verify
python -m tools.agent_delivery_cli replay --trace g3-b2-optimization-authoritative-round1
python -m tools.agent_delivery_cli replay --trace g3-b3-feature-completion-agent-flow
```

A successful replay emits canonical JSON with `historical_execution=false`, `offline=true`, `network_used=false`, `api_keys_used=[]`, `runtime_api_calls=[]`, and a stable replay SHA256.

## Claim Boundaries

Replay verifies and renders frozen decision flow; it does not rerun performance benchmarks or create historical evidence.

## Known Limitations

Replay requires frozen repository evidence. Online DeepSeek functionality is optional and deliberately outside this path.
