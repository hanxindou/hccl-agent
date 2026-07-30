# G2-E Official HCCL-VM Suite Evidence

This suite references per-primitive subprocess-driven official HCCL-VM evidence. It does not copy raw logs, call HCCL directly, or claim real Ascend NPU validation.

- Status: `COMPLETED`
- Passed: `True`

## Primitive References

- `AllReduce`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_allreduce_20260730T095559.079796Z`, SHA256SUMS SHA256 `c6fbca64efd6b3b67421e76fdb4eb1c8e3045d04d8247480ac017e3a8aaedd65`
- `AllGather`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_allgather_20260730T095612.112602Z`, SHA256SUMS SHA256 `09ceb0f3f13b0424cee21ea0712a3892db595e9cb1247e1b459b25b782e66c2e`
- `ReduceScatter`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_reducescatter_20260730T095626.920392Z`, SHA256SUMS SHA256 `55fae7d44f235241e66c86b5ec3b3aa3b6f2ada0df368973fa6e0c0822ac25b3`

Use `SHA256SUMS` to verify every suite file.
