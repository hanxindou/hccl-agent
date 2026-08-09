# G3-B3 known limitations

- No ACL/HCCL runtime, device, communicator, collective, MPI, `hccl_test`, or `msprof` operation was executed.
- Sparse and integrity behavior is host-executed CPU_SIM evidence; performance and large-scale claims remain simulator-model evidence.
- Flow control and backpressure are deterministic bounded models, not measured transport pressure on Ascend hardware.
- The direct official API source path is compile/link/static-inspection readiness only.
- INT8 quantization is deferred by the precision gate; PairWise is skipped by the value gate.
- License, official-asset redistribution, controlled competition materials, final archive constraints, and supported real-device acceptance remain external actions.
