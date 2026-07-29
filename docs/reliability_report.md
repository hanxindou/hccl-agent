# Reliability Simulation Report

## Model Scope

- Status: `CPU_SIMULATED / RELIABILITY_MODEL`
- Interpretation: 模拟器在给定模型和固定 seed 下的统计结果。
- Seed: `20260729`
- Scale: `8` ranks, `64.0` MB message

## Fault Summary

| Metric | Value |
| --- | ---: |
| Injection count | 4 |
| Detection count | 4 |
| Retry count | 4 |
| Recovery count | 1 |
| Success count | 2 |
| Failure count | 0 |
| Dropped/lost packets | 0 |
| Model failover time ms | 4.1 |
| Wall-clock elapsed ms | 0.327 |

- Wall-clock note: wall-clock is observational only; not a hardware failover SLA

## Fault Types

- link_down
- timeout
- corruption
- congestion

## CRC32

- Reference CRC32: `836705243`
- Candidate CRC32: `807236076`
- Corruption detected: `True`
- Payload source: `simulated payload`

## Event Sequence

| # | Fault | Link | Model time ms | Duration ms |
| ---: | --- | --- | ---: | ---: |
| 1 | link_down | 0->1 | 0 | 40 |
| 2 | timeout | 1->2 | 1 | 15 |
| 3 | corruption | 2->3 | 2 | 0 |
| 4 | congestion | 3->4 | 3 | 25 |

## Failover

- Triggered: `True`
- Found: `True`
- Hops: `2`
- Route: `[0, 2, 1]`

## Failed Cases

- None in this fixed-seed CPU_SIM scenario.

## Gap To Real Competition Acceptance

- No real Ascend hardware CRC path is exercised.
- Failover time is model time, not measured wall-clock failover.
- Retry and packet loss are simulated with fixed-seed CPU logic.
