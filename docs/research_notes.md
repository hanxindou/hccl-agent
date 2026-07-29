# HCCL Agent 外部参考与 License 记录

## Stage C2：ReduceScatter CPU 正确性

访问日期：2026-07-29
状态：未使用外部网络参考

### 参考来源

- 赛题原始 DOCX：本地文件 `docs/2026年中国研究生人工智能大赛--华为赛题.docx`
- 自主执行计划：本地文件 `docs/autonomous_goal_plan.md`
- 项目路线图：本地文件 `docs/roadmap_v2.md`
- 项目审计报告：本地文件 `docs/project_audit.md`

### License

未引入外部代码，未复制第三方实现，因此无新增第三方 License 义务。

### 借鉴内容

ReduceScatter CPU_SIM 语义来自本项目自主计划：`send[N][N][C] -> recv[N][C]`，按目标 rank 分片并对所有 source rank 求和。

### 是否直接复制代码

否。

## Stage D1：拓扑与成本模型收敛

访问日期：2026-07-29
状态：未使用外部网络参考

### 参考来源

- 自主执行计划：本地文件 `docs/autonomous_goal_plan.md`
- 项目主拓扑模型：`topology/graph_builder.py`
- 项目硬件相对参数：`hardware/profile.py`
- 项目已有 cost model：`cost_model/engine.py`

### License

未引入外部代码，未复制第三方实现，因此无新增第三方 License 义务。

### 借鉴内容

D1 只按自主计划中的可解释近似公式收敛项目内部模型：startup cost、通信步数、传输字节、有效带宽和 contention penalty。未复制 ASTRA-sim、SimAI、NCCL 或 HCCL 外部代码。

### 是否直接复制代码

否。

## Stage E1：Agent 自动代码开发最小闭环

访问日期：2026-07-29
状态：未使用外部网络参考

### 参考来源

- 自主执行计划：本地文件 `docs/autonomous_goal_plan.md`
- 当前项目代码生成相关模块：`agent/code_generation_skill.py`

### License

未引入外部代码，未复制第三方实现，因此无新增第三方 License 义务。

### 借鉴内容

E1 使用项目内离线模板实现最小闭环：生成临时 reference checker、执行 `py_compile`、读取确定性语法错误、模板修复、再次编译并运行自测。

### 是否直接复制代码

否。

## Stage C3-B：FP16/BF16 CPU 软件模拟

访问日期：2026-07-29
状态：未使用外部网络参考

### 参考来源

- 赛题原始 DOCX：本地文件 `docs/2026年中国研究生人工智能大赛--华为赛题.docx`
- 自主执行计划：本地文件 `docs/autonomous_goal_plan.md`
- 项目路线图：本地文件 `docs/roadmap_v2.md`
- C3-A 当前实现与测试

### License

未引入外部代码，未复制第三方实现，因此无新增第三方 License 义务。

### 借鉴内容

FP16/BF16 仅实现为本项目 CPU 软件模拟：输入和输出使用 16-bit 编码，CPU 内部转换到 FP32 完成累加，再按 dtype 重新编码。该实现用于正确性测试和后续实机迁移准备，不声明 Ascend 硬件混合精度行为。

### 是否直接复制代码

否。

## Stage C3-A：FP32 ReduceOp 与统一正确性基准

访问日期：2026-07-29
状态：未使用外部网络参考

### 参考来源

- 赛题原始 DOCX：本地文件 `docs/2026年中国研究生人工智能大赛--华为赛题.docx`
- 自主执行计划：本地文件 `docs/autonomous_goal_plan.md`
- 项目路线图：本地文件 `docs/roadmap_v2.md`
- C2 已提交实现：`4109491 feat: complete C2 ReduceScatter correctness`

### License

未引入外部代码，未复制第三方实现，因此无新增第三方 License 义务。

### 借鉴内容

FP32 ReduceOp 语义使用本项目已有 `hcclRedOp_t` 枚举：`HCCL_SUM`、`HCCL_PROD`、`HCCL_MAX`、`HCCL_MIN`。实现保持 CPU_SIM 单进程 buffer 语义，不声明真实 HCCL/CANN 行为。

### 是否直接复制代码

否。

## Stage F1：可靠性模拟验证闭环

访问日期：2026-07-29
状态：未使用外部网络参考

### 参考来源

- 自主执行计划：本地文件 `docs/autonomous_goal_plan.md`
- 当前项目可靠性模块：`simulator/fault_injector.py`
- 当前项目健康检测模块：`simulator/health_monitor.py`
- 当前项目重试模块：`simulator/retry_policy.py`
- 当前项目故障切换模块：`simulator/failover_engine.py`

### License

未引入外部代码，未复制第三方实现，因此无新增第三方 License 义务。

### 借鉴内容

F1 只使用 Python 标准库 `zlib.crc32` 对模拟 payload 计算 CRC32，并将项目已有 fault injection、health monitor、retry policy 和 failover engine 串成固定 seed 的 CPU_SIM 可靠性验证流。

### 是否直接复制代码

否。

## Stage G1：CANN/Ascend 适配准备

访问日期：2026-07-29
状态：未使用外部网络参考

### 参考来源

- 自主执行计划：本地文件 `docs/autonomous_goal_plan.md`
- 当前 CMake 配置：`hcccl/CMakeLists.txt`
- 当前接口指南：`docs/cann_hccl_interface_guide.md`
- 当前用户待办：`docs/user_actions.md`

### License

未引入外部代码，未复制第三方实现，因此无新增第三方 License 义务。

### 借鉴内容

G1 只建立项目内 `CPU_SIM` 与 `ASCEND_CANN` 的条件编译边界、缺 SDK 快速失败提示和用户实机验证模板。未复制 CANN/HCCL 源码，未链接本地不存在的 SDK，未使用 Stub 库冒充真实 CANN。

### 是否直接复制代码

否。
