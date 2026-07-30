# G2-E Official HCCL-VM Primitive Validation Evidence

This archive records a subprocess-driven run of the official HCCL-VM, hccl_test, and checker tools. It is not a direct HCCL API integration and does not claim validation on a real Ascend NPU.

- Status: `PASS_WITH_WARNING`
- Passed: `True`
- Primitive: `ReduceScatter`
- Checker Success: `True`
- ErrorCode 103 warnings: `4`
- Outer exit code: `0`
- HCCL-VM normal shutdown: `True`

## Agent Report

```text
Official HCCL-VM Validation Report
==================================
Validation Class: OFFICIAL_HCCL_VM_SIMULATOR
Integration: subprocess-driven official hccl_test and checker
Direct HCCL API Call: No
Real Ascend NPU Validated: No
Status: PASS_WITH_WARNING
Passed: True
Primitive: ReduceScatter
Rank Count: 2
Data Type: int32
Reduce Operation: sum
Element Count: 8
Byte Count: 64
Input Bytes Per Rank: 64
Output Bytes Per Rank: 32
Checker Success: True
Metadata Match: True
ErrorCode 103 Warnings: 4
Warning Regression: False
Test Exit Code: 0
Checker Exit Code: 0
HCCL-VM Exit Code: 0
Outer Exit Code: 0
HCCL-VM Normal Shutdown: True
Evidence Directory: experiments/hccl_vm/evidence/g2_e_reducescatter_20260730T095759.140241Z
Checker Operation Summaries:
  opIndex=0, collectiveType=ReduceScatter, rankCount=2, dataType=INT32, elementCount=8, reduceType=SUM
  opIndex=1, collectiveType=ReduceScatter, rankCount=2, dataType=INT32, elementCount=8, reduceType=SUM
```

Use `SHA256SUMS` to verify every archived evidence file.
