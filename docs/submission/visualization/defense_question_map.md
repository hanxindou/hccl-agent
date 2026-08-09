# Defense Question Map

## Q1. Is the 45.59% improvement measured on Ascend NPUs?

No. It is the G3-C canonical display of a frozen weighted communication-simulator comparison against fixed Ring. No real model, device collective, or training throughput was executed.

## Q2. Does the 1024-rank result mean 1024 physical devices?

No. It is logical simulator scale and must not be presented as a physical cluster.

## Q3. Are sparse byte reductions NIC measurements?

No. Lossless sparse reconstruction/correctness is host observed; the wire-byte and compression accounting is modeled/logical, with dense fallback when modeled sparse cost is unfavorable.

## Q4. Did Direct execute official ACL/HCCL calls?

No. Official call expressions exist in a default-OFF compile/link source path. The source was not loaded or executed, and runtime API calls remain empty.

## Q5. Is the CPU_SIM 19-symbol ABI the official loader ABI?

No. It is the frozen project CPU_SIM ABI and SONAME contract.

## Q6. Is the Agent fully autonomous?

No such claim is supported. The delivery is Agent-assisted, deterministically evaluated, human-governed, and offline replayable. Human goals, constraints, approvals, and frozen gates are disclosed.

## Q7. Are normalized traces original historical model conversations?

No. Replay is not historical execution. G3-B2/G3-B3 normalized traces are reconstructed from frozen evidence where stated; unavailable historical Prompt/Response relationships remain explicitly unavailable.

## Q8. Why are INT8 and PairWise missing?

They are evidence-gated decisions rather than hidden omissions: INT8 is deferred by its precision gate and PairWise is skipped by its value gate.

## Q9. Is reliability validated on a real network?

No. CRC32 integrity and bounded retry semantics are host validated. Backpressure and bounded inflight behavior are simulator modeled. No NIC/HCCL hardware reliability result is claimed.

## Q10. What remains blocked or requires organizer/user action?

Real-device acceptance remains `HARDWARE_BLOCKED`. License/copyright, controlled artifact redistribution, submission archive/size rules, precision interpretation, final language, and final organizer template remain `USER_ACTION_REQUIRED`.
