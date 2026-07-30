# G2 Official HCCL-VM Baseline

## Environment

- CANN Toolkit: 9.1.0
- HCOMM branch: competition/campus-2026
- HCCL branch: competition/campus-2026
- Backend: official HCCL-VM
- Topology profile: ascend950_cluster_32_server_normal.yaml
- mock-comm profile: 112
- Rank count: 2

## Results

| Primitive | DType | Elements | ReduceOp | Checker | Process | Status |
|---|---|---:|---|---|---|---|
| AllGather | INT32 | 8 | N/A | Checker Success | exit 0 | PASS_WITH_WARNING |
| AllReduce | INT32 | 16 | SUM | Checker Success | exit 0 | PASS_WITH_WARNING |
| ReduceScatter | INT32 | 8 | SUM | Checker Success | exit 0 | PASS_WITH_WARNING |

## Checker stages

The following CheckerV3 stages completed successfully:

- GenGraph
- SingleTaskCheck
- MemConflict
- SemanticCheck

Both recorded operation indices completed with `Checker Success`.

## Known warning

All three official baseline runs emitted:

`ErrorCode: 103 - CCU post/local-post tasks were never consumed by a Wait task`

The warning did not cause Checker failure:

- all CheckerV3 stages reported success;
- the final operation result was `Checker Success`;
- HCCL-VM shut down normally;
- script command exit code was zero.

The baseline is therefore recorded as `PASS_WITH_WARNING`, not
`PASS_CLEAN`.

## Scope boundary

This baseline proves that the official CANN/HCCL/HCOMM/HCCL-VM toolchain
can execute and validate the three collective primitives in the current
simulator environment.

It does not yet prove:

- hccl-agent integration with the official backend;
- correctness of Agent-generated HCCL code;
- real Ascend NPU execution;
- real multi-device performance;
- FP16/BF16 correctness in the official backend;
- large-message or large-rank scalability.
