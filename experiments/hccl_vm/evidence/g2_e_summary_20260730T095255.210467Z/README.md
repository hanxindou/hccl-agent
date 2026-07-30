# G2-E Official HCCL-VM Suite Evidence

This suite references per-primitive subprocess-driven official HCCL-VM evidence. It does not copy raw logs, call HCCL directly, or claim real Ascend NPU validation.

- Status: `COMPLETED`
- Passed: `True`

## Primitive References

- `AllReduce`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_allreduce_20260730T095231.274525Z`, SHA256SUMS SHA256 `43eab9b04781d3870ac14c1cf925971174be0cebd57b57ae4fc0d525eff6f2c3`
- `AllGather`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_allgather_20260730T095242.135368Z`, SHA256SUMS SHA256 `baa7e6b45baf1c5a881527bdc3f1459c4e85c1f8f019dd4fe633314dfe7e6ebd`
- `ReduceScatter`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_reducescatter_20260730T095254.776939Z`, SHA256SUMS SHA256 `1cfe46f0e8df2d8ba7ad6932f460d97a977eb79ccbbccabfa7a861fdfe0201c2`

Use `SHA256SUMS` to verify every suite file.
