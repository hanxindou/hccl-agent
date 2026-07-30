# G2-E HCCL-VM Official Collective Contract

## Scope and evidence source

This document freezes the G2-E contract for the official HCCL-VM simulated
validation backend. It is an implementation contract, not evidence of a real
Ascend NPU run and not a claim that hccl-agent directly calls a real HCCL API.
The backend drives the official `hccl_test` executables through subprocesses.

The contract is derived from the immutable G2-C raw logs listed below and from
the installed CANN 9.1.0 `hccl_test` binaries. The source logs are outside this
repository and must not be edited, copied as replacement evidence, or used to
rewrite G2-C or G2-D evidence.

| Primitive | Raw G2-C log |
| --- | --- |
| AllReduce | `/home/workspace/evidence/logs/allreduce_baseline_20260730_135904.log` |
| AllGather | `/home/workspace/evidence/logs/allgather_baseline_20260730_140015.log` |
| ReduceScatter | `/home/workspace/evidence/logs/reducescatter_baseline_20260730_140432.log` |

The required official source state is CANN `9.1.0`, HCOMM branch
`competition/campus-2026` at
`c8a3dc68a37315aa1e908a971fa706abe612f6ee`, and HCCL branch
`competition/campus-2026` at
`2c87cc1937bab23b8574ef24017c03572d3340e2`. HCOMM and HCCL tracked working
trees must be clean. Root-mode metadata probes use only command-scoped,
exact-path Git trust:

```text
git -c safe.directory=/home/workspace/hcomm -C /home/workspace/hcomm ...
git -c safe.directory=/home/workspace/hccl -C /home/workspace/hccl ...
```

No global or system Git configuration is part of this contract.

## Supported collective whitelist

Only the following canonical names are supported by G2-E:

| Canonical | Accepted aliases | Fixed executable basename |
| --- | --- | --- |
| `AllReduce` | `allreduce`, `all_reduce`, `all-reduce` | `all_reduce_test` |
| `AllGather` | `allgather`, `all_gather`, `all-gather` | `all_gather_test` |
| `ReduceScatter` | `reducescatter`, `reduce_scatter`, `reduce-scatter` | `reduce_scatter_test` |

Normalization is trim, case folding, and exact alias lookup only. It must not
strip arbitrary punctuation. The executable is a registry constant, not a
request or CLI parameter, and is joined only below
`<cann_path>/tools/hccl_test/bin`.

All three contracts are limited to two ranks and `int32`. AllReduce and
ReduceScatter require an explicitly supplied `sum` reduction. AllGather
rejects any supplied reduction option. Invalid primitive, reduction, dtype,
rank count, or element count is rejected before any environment probe, WSL
launch, HCCL-VM launch, MPI launcher, or subprocess creation.

## Frozen official argv

The MPI prefix is:

```text
mpirun --allow-run-as-root --oversubscribe -np 2
```

The exact G2-E `hccl_test` argv contracts are:

```text
/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/all_reduce_test \
  -b 64 -e 64 -d int32 -o sum -w 0 -n 1 -c 1

/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/all_gather_test \
  -b 64 -e 64 -d int32 -w 0 -n 1 -c 1

/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/reduce_scatter_test \
  -b 64 -e 64 -d int32 -o sum -w 0 -n 1 -c 1
```

`-i`, `-f`, `-r`, `-p`, `-m`, `-z`, `-s`, and `-t` are not part of this
contract. The installed binary help can print `aclrtGetSocName failed` when no
device context is present while still exiting zero; diagnose must not treat that
string alone as a failure.

## Element and byte contract

All commands use `-b 64 -e 64`, but their meanings differ. A registry entry
must retain every field below instead of applying a single shared formula.

| Primitive | Request element meaning | Checker `elementCount` | Input per rank | Output per rank | hccl_test bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| AllReduce | input and output elements per rank | 16 | 64 B (16 x 4) | 64 B (16 x 4) | 64 B |
| AllGather | input elements per rank | 8 | 32 B (8 x 4) | 64 B (8 x 2 x 4) | 64 B |
| ReduceScatter | output elements per rank | 8 | 64 B (8 x 2 x 4) | 32 B (8 x 4) | 64 B |

The corresponding request values are therefore `AllReduce --elements 16`,
`AllGather --elements 8`, and `ReduceScatter --elements 8`.

## Checker metadata contract

At least one Op summary and at least one `Checker Success` are required. Every
observed target Op summary must match the selected primitive contract. G2-E does
not require exactly two summaries or consecutive `opIndex` values.

| Primitive | collectiveType | rankCount | dataType | elementCount | reduceType |
| --- | --- | ---: | --- | ---: | --- |
| AllReduce | `AllReduce` | 2 | `INT32` | 16 | must be `SUM` |
| AllGather | `AllGather` | 2 | `INT32` | 8 | record only; do not compare |
| ReduceScatter | `ReduceScatter` | 2 | `INT32` | 8 | must be `SUM` |

The AllGather raw log may report `reduceType=SUM` even though its frozen argv
does not pass `-o`; that observed value is not a successful AllGather contract
condition.

Checker output is partitioned from each Op summary until the next summary or
end of output. For each operation block, all four required CheckerV3 stages
must be present and successful:

```text
GenGraph
SingleTaskCheck
MemConflict
SemanticCheck
```

Additional observed stages are allowed, but every observed stage must be
successful. A missing required stage or any failed observed stage fails the
result. A generic `check_result: failed` table from G2-C hccl_test check-only
output is neither a pass signal nor a fatal condition by itself.

## Verdict, warning, and cleanup contract

The following must all be true to pass:

- `hccl_config`, mock-comm, hccl_test, checker, HCCL-VM, and outer exit codes
  are captured and zero.
- Op summaries and required stages satisfy the selected contract.
- At least one Checker Success is present.
- The normal HCCL-VM shutdown marker is present.
- No `Segmentation fault`, `MPI_ABORT`, `undefined symbol`, or fatal failure is
  observed.
- Postflight finds no HCCL-VM, MPI launcher, selected hccl_test, or checker
  process owned by this run.

`ErrorCode: 103` has a fixed expected baseline count of four for each
primitive. The parser stores the count and normalized warning summaries. A
count other than four, or an unexpected normalized warning summary, sets
`warning_regression=true` with reasons but does not independently fail an
otherwise valid run. Count zero may produce `PASS_CLEAN`; any positive count
produces `PASS_WITH_WARNING`, never `PASS_CLEAN`.

No result may be marked complete without Checker Success and outer exit code
zero. Cleanup uncertainty is a failure or an explicit environment block, never
a pass.

## Evidence contract

Per-primitive G2-E evidence uses the directory patterns:

```text
experiments/hccl_vm/evidence/g2_e_allreduce_<timestamp>/
experiments/hccl_vm/evidence/g2_e_allgather_<timestamp>/
experiments/hccl_vm/evidence/g2_e_reducescatter_<timestamp>/
```

Each contains `README.md`, `command.txt`, `manifest.json`, `result.json`,
`concise.log`, `raw.log.gz`, `report.txt`, and `SHA256SUMS`. It records the
resolved contract, argv, observed stages, warning fields, exit codes, cleanup
audit, environment commits, and these fixed boundaries:

```text
execution_mode=subprocess_hccl_test
direct_hccl_api_call=false
real_ascend_npu_validated=false
```

The suite summary directory is
`experiments/hccl_vm/evidence/g2_e_summary_<timestamp>/`. It references the
three per-primitive evidence digests without copying their raw logs.
