# G2-E Multi-Primitive Official HCCL-VM Validation Report

## Status

`COMPLETED` for the G2-E external official HCCL-VM simulated-validation
contract. This is subprocess-driven execution of official HCCL-VM,
mock-comm, `hccl_test`, and checker tools. It is not a direct HCCL API call,
does not modify official HCOMM/HCCL/CANN sources, and does not claim real
Ascend NPU validation or hardware performance.

## Checkpoints

| Checkpoint | Commit | Result |
| --- | --- | --- |
| G2-E-1 | `e468797` | Frozen argv, byte, Checker, stage, and warning contracts |
| G2-E-2 | `3a3fe16` | Immutable primitive registry and strict generic request |
| G2-E-3 | `534ab88` | AllReduce official closure and strict parser migration |
| G2-E-4 | `31b936f` | AllGather official closure without `-o` |
| G2-E-5 | `9a46623` | ReduceScatter official closure with strict SUM |
| G2-E-6 | `33b8827` | Suite orchestration, evidence summary, and report |
| G2-E-7 | this checkpoint | Cross-platform regression and final audit |

## Final Official Suite Evidence

Command:

```text
python3 main.py verify-official --backend ASCEND_HCCL_VM --suite g2-e
```

Latest completed suite:

```text
experiments/hccl_vm/evidence/g2_e_summary_20260730T095800.105217Z
```

| Primitive | Evidence | Status | Checker Success | Warning 103 | Cleanup |
| --- | --- | --- | ---: | ---: | --- |
| AllReduce | `g2_e_allreduce_20260730T095729.013876Z` | PASS_WITH_WARNING | 2 | 4 | CLEAN |
| AllGather | `g2_e_allgather_20260730T095743.054148Z` | PASS_WITH_WARNING | 2 | 4 | CLEAN |
| ReduceScatter | `g2_e_reducescatter_20260730T095759.140241Z` | PASS_WITH_WARNING | 2 | 4 | CLEAN |

All three runs had rankCount=2, dataType=INT32, outer exit code 0, HCCL-VM
normal shutdown, no Segmentation fault, MPI_ABORT, undefined symbol, or fatal
failure, and every required CheckerV3 stage succeeded for every observed Op
block: GenGraph, SingleTaskCheck, MemConflict, and SemanticCheck.

The suite records CANN 9.1.0, HCOMM
`competition/campus-2026@c8a3dc68a37315aa1e908a971fa706abe612f6ee`, HCCL
`competition/campus-2026@2c87cc1937bab23b8574ef24017c03572d3340e2`, and
registry version `g2-e-v1` identically for all three runs.

`SHA256SUMS` file SHA256:

```text
42e12f11293419ee2866709068a249452529dedec1c34117c827608a48f804d4
```

## Regression Evidence

| Environment | Python | CTest | CPU_SIM |
| --- | --- | --- | --- |
| Windows | 531 passed, 1 opt-in skipped | 11/11 passed | `python main.py --nodes 4 --message-size 128 --primitive AllReduce` succeeded |
| WSL Ubuntu-22.04 | 531 passed, 1 opt-in skipped | 11/11 passed | configured and built `/tmp/hccl-agent-g2e-cpu` with `HCCL_BACKEND=CPU_SIM` |

## Remaining Limits and G2-F Entry

CPU_SIM remains the default backend. G2-E verifies only the external official
HCCL-VM simulation workflow and fixed 2-rank INT32 contracts. It does not
validate real NPU devices, hardware performance, larger rank counts, additional
dtypes, or direct HCCL API integration.

G2-F may define a separately approved real-device/direct-API boundary with
explicit CANN/HCOMM compile and link contracts, device topology discovery,
correctness data validation, and hardware performance baselines. It must retain
the G2-E evidence and the CPU_SIM default path.
