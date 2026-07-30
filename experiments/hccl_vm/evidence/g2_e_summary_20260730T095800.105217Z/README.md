# G2-E Official HCCL-VM Suite Evidence

This suite references per-primitive subprocess-driven official HCCL-VM evidence. It does not copy raw logs, call HCCL directly, or claim real Ascend NPU validation.

- Status: `COMPLETED`
- Passed: `True`

## Primitive References

- `AllReduce`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_allreduce_20260730T095729.013876Z`, SHA256SUMS SHA256 `3a3c4a36f64a256df9daddb189809ba1ba2f745ee8adbb89411dd63ddb19ecd2`
- `AllGather`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_allgather_20260730T095743.054148Z`, SHA256SUMS SHA256 `5bf367673397eef1df150b56e13f219d22ff2da73204b2b64c1be2f8ae2baab4`
- `ReduceScatter`: `PASS_WITH_WARNING`, evidence `experiments/hccl_vm/evidence/g2_e_reducescatter_20260730T095759.140241Z`, SHA256SUMS SHA256 `8c3a79873d82ae3d4462b3a7f58b8a313dc6492d9a31f0d5db225ed99596a5c0`

Use `SHA256SUMS` to verify every suite file.
