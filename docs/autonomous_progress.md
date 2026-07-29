# HCCL Agent 自主执行进度

## Stage C2：ReduceScatter CPU 正确性

开始时间：2026-07-29 18:00:00 +08:00
结束时间：2026-07-29 18:10:43 +08:00
状态：COMPLETED

### 修改文件

- `hcccl/src/hccl_algorithms.c`
- `hcccl/src/hccl_comm.c`
- `hcccl/CMakeLists.txt`
- `hcccl/tests/test_reducescatter.c`
- `plugin/execution_engine.py`
- `plugin/hccl_api.py`
- `tests/test_execution_engine.py`
- `tests/test_hccl_api.py`
- `tests/test_reducescatter.py`

### 验收结果

- CMake：Visual Studio 17 2022 x64，Release 配置成功，`CMAKE_BUILD_EXIT_CODE=0`
- CTest：`F:\build\hccl-agent-hcccl-c2`，9/9 passed，`CTEST_EXIT_CODE=0`
- 定向 Python：`tests.test_reducescatter tests.test_execution_engine tests.test_hccl_api tests.test_allgather`，45 tests，OK
- 完整 Python：`python -m unittest discover tests -q`，425 tests，OK
- DLL/SO：实际加载 `F:\build\hccl-agent-hcccl-c2\Release\hccl_plugin.dll`；Linux `.so` 未验证

### 外部参考

- 本阶段未使用外部网络参考，依据赛题 DOCX、`docs/autonomous_goal_plan.md` 和当前代码完成。

### 遇到的问题

- 赛题 DOCX 在 PowerShell 终端显示存在编码乱码，但核心要求已由自主计划和路线图交叉确认。
- B1 既有 2-rank 标量 ReduceScatter 回归测试仍要求 `HCCL_ERR_NOT_SUPPORTED`。C2 因此将 2-rank CPU_SIM 数据路径暂保留为不支持；C2 正确性覆盖自主计划要求的 1、4、8、16 rank。

### 降级方案

- ReduceScatter 状态：`CPU_SIMULATED`，仅 FP32/SUM、单进程扁平 buffer。
- FP16/BF16、PROD/MAX/MIN 仍保持 `STUB_UNVERIFIED` 或后续 C3 范围。

### 用户待办

- Linux `.so`、CANN/HCOMM、Ascend 实机和 msprof 验证见 `docs/user_actions.md`。

### 本地提交

- commit：待创建
- message：`feat: complete C2 ReduceScatter correctness`

### 未验证边界

- 未验证 Linux `.so`。
- 未接入 CANN SDK、真实 HCOMM 或 Ascend 设备。
- 未验证真实多进程、多设备 ReduceScatter。
- 当前结果不得描述为真实 HCCL 性能或 Ascend 实机正确性。
