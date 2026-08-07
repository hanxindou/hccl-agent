# G3-B reproduction guide

The default path is host-only `CPU_SIM`; fallback is `NONE`. It neither needs
nor searches for CANN, and it does not execute device APIs.

```text
python -m tools.submission_cli check
python -m tools.submission_cli quick
python -m tools.submission_cli full
python -m tools.submission_cli stage --clean-output --include-selected-evidence --exclude-controlled-docs --exclude-official-assets
python -m tools.submission_cli verify --stage dist/submission-staging
```

`quick` performs a clean CPU_SIM build/install, eleven CTests, representative
three-primitive and dtype correctness, 8-rank/topology/fault scenarios, and
frozen G2-F-5/F-6 checksum validation. `full` performs two independent clean
builds, ABI/ELF/dependency/install/consumer checks, submission-relevant Python
regression, optional direct readiness when the frozen CANN root is present,
staging, and verification. It does not regenerate the expensive simulator
evidence.

Topology and workload overrides are accepted through `--cluster-config`,
`--topology-config`, `--hardware-profile`, `--seed`, `--message-size`,
`--rank-size`, `--primitive`, and `--algorithm`. All included examples retain
`topology_source=SIMULATOR_CONFIG` and are not hardware probes.
