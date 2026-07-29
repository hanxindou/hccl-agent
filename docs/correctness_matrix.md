# HCCL Agent 正确性矩阵

更新时间：2026-07-29 23:10:00 +08:00

## 状态标记

| 标记 | 含义 |
| ---- | ---- |
| `CPU_SIMULATED` | 通过本项目 C 插件在单进程 CPU buffer 上执行，非真实 HCCL/CANN 通信。 |
| `CPU_EMULATED_FP16` | 输入/输出使用 16-bit FP16 编码，CPU 内部转 FP32 累加后再编码回 FP16。 |
| `CPU_EMULATED_BF16` | 输入/输出使用 16-bit BF16 编码，CPU 内部转 FP32 累加后再编码回 BF16。 |
| `REFERENCE_VERIFIED` | 结果与独立 Python reference 或 C reference 逐元素一致。 |
| `NOT_SUPPORTED` | 当前接口明确返回 `HCCL_ERR_NOT_SUPPORTED`。 |
| `UNVERIFIED` | 代码或声明存在，但本轮未验证。 |
| `PENDING` | 后续 Batch 范围。 |

## FP32 Primitive / ReduceOp 矩阵

| Primitive | DType | ReduceOp | 状态 | 环境 | 测试证据 |
| --------- | ----- | -------- | ---- | ---- | -------- |
| AllReduce | FP32 | SUM | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py`, H1 full regression 454 OK |
| AllReduce | FP32 | PROD | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py`, overflow case verified |
| AllReduce | FP32 | MAX | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py`, negative/zero/decimal data |
| AllReduce | FP32 | MIN | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py`, negative/zero/decimal data |
| AllGather | FP32 | N/A | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_allgather.c`, `tests/test_allgather.py`, C3-A regression unchanged |
| ReduceScatter | FP32 | SUM | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reducescatter.c`, `tests/test_reducescatter.py`, 1/4/8/16 rank coverage |
| ReduceScatter | FP32 | PROD | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py`, zero and negative data |
| ReduceScatter | FP32 | MAX | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py`, non-zero identity coverage |
| ReduceScatter | FP32 | MIN | `CPU_SIMULATED`, `REFERENCE_VERIFIED` | Windows DLL | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py`, non-zero identity coverage |
| Broadcast | FP32 | N/A | `NOT_SUPPORTED` | Windows DLL | `hcccl/tests/test_api_wrappers.c` |

## DType 矩阵

| Primitive | DType | 当前状态 | 说明 |
| --------- | ----- | -------- | ---- |
| AllReduce | FP32 | `CPU_SIMULATED` | `count=1` 标量路径；SUM/PROD/MAX/MIN 已验证。 |
| AllGather | FP32 | `CPU_SIMULATED` | `[N][C] -> [N][N*C]` 扁平布局；无 ReduceOp。 |
| ReduceScatter | FP32 | `CPU_SIMULATED` | `[N][N][C] -> [N][C]` 扁平布局；SUM/PROD/MAX/MIN 已验证；2-rank legacy 标量形状仍返回 `NOT_SUPPORTED`。 |
| AllReduce | FP16 | `CPU_EMULATED_FP16`, `REFERENCE_VERIFIED` | 16-bit encoded buffer；CPU FP32 累加；`tests/test_dtype_emulation.py` 和 `hcccl/tests/test_dtype_emulation.c`。 |
| AllGather | FP16 | `CPU_EMULATED_FP16`, `REFERENCE_VERIFIED` | 16-bit encoded buffer；按元素宽度 gather；`tests/test_allgather.py` 和 `hcccl/tests/test_dtype_emulation.c`。 |
| ReduceScatter | FP16 | `CPU_EMULATED_FP16`, `REFERENCE_VERIFIED` | 16-bit encoded buffer；CPU FP32 reduce 后 scatter；`tests/test_dtype_emulation.py`。 |
| AllReduce | BF16 | `CPU_EMULATED_BF16`, `REFERENCE_VERIFIED` | 16-bit encoded buffer；CPU FP32 累加；`tests/test_dtype_emulation.py` 和 `hcccl/tests/test_dtype_emulation.c`。 |
| AllGather | BF16 | `CPU_EMULATED_BF16`, `REFERENCE_VERIFIED` | 16-bit encoded buffer；按元素宽度 gather；`tests/test_allgather.py`。 |
| ReduceScatter | BF16 | `CPU_EMULATED_BF16`, `REFERENCE_VERIFIED` | 16-bit encoded buffer；CPU FP32 reduce 后 scatter；`tests/test_dtype_emulation.py`。 |

## 数值边界

| 场景 | 当前证据 | 状态 |
| ---- | -------- | ---- |
| 正数、负数、零、小数 | `tests/test_reduce_ops.py` 和 `hcccl/tests/test_reduce_ops.c` | 已覆盖 |
| PROD 零和负数 | `tests/test_reduce_ops.py` ReduceScatter/AllReduce 数据集 | 已覆盖 |
| MAX/MIN 非零初始化 | C 层使用 `-FLT_MAX` / `FLT_MAX`，测试覆盖负数场景 | 已覆盖 |
| Inf | `tests/test_reduce_ops.py::test_inf_nan_and_overflow_behavior` | FP32/SUM 已覆盖 |
| NaN | `tests/test_reduce_ops.py::test_inf_nan_and_overflow_behavior` | FP32/SUM 已覆盖 |
| FP32 overflow | `hcccl/tests/test_reduce_ops.c`, `tests/test_reduce_ops.py` | PROD 溢出为 Inf 已覆盖 |
| FP16/BF16 roundtrip | `tests/test_dtype_emulation.py::test_roundtrip_boundaries` | 正负数、零、小数、大小值、NaN、Inf 已覆盖 |
| FP16/BF16 tolerance | `tests/test_dtype_emulation.py` | FP16 `1e-3`，BF16 `2e-2` |
| FP16/BF16 overflow | `tests/test_dtype_emulation.py::test_inf_nan_and_overflow` | PROD 溢出为 Inf 已覆盖 |

## 未验证边界

- Linux `.so` 未验证。
- CANN/HCOMM 未接入。
- Ascend 实机正确性、性能和 profiling 未验证。
- FP16/BF16 为 CPU 软件模拟，不代表 Ascend 混合精度硬件行为。
- 当前正确性结论仅适用于 CPU_SIM 单进程扁平 buffer，不代表真实多进程 HCCL 通信。
