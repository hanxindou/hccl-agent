# Claim Boundary Matrix

- Total claims: 14

| ID | Claim | Allowed wording | Prohibited wording | Source | Evidence level | Report | Demo | Limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLM-001 | 1024 ranks | 在指定 Fat-Tree simulator model 下完成 logical 1024-rank 预测 | 真实支持或验证 1024 卡 | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C scale report | 可展示并固定显示 SIMULATED_ONLY | 无真实设备、传输或训练 workload |
| CLM-002 | 1 GB | logical 1 GB 使用分析记账和最大 4 MB 有界物化 | 实机传输了 1 GB 或完成真实 1 GB collective | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C correctness/performance report | 可演示 logical 配置与 evidence | 非真实链路传输 |
| CLM-003 | 72h | 事件驱动 logical 72h，模拟时长 259200 秒、wall-clock 0 秒 | 完成真实 72 小时稳定性压测 | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C reliability report | 可展示事件时间线 | 无真实长稳运行 |
| CLM-004 | 100 ms failover | 11 个可恢复模拟场景达到模型化 100 ms 目标 | 真实集群 100 ms 内完成故障切换 | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C reliability report | 可展示模拟 fault trace | 模型结果，另有 1 个预期无路失败 |
| CLM-005 | retry rate | 模拟故障场景 retry rate=0.00025，低于模型目标 0.001 | 真实 RoCE/HCCL 重传率低于 0.1% | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C reliability report | 可展示并注明统计分母 | 非真实协议重传 |
| CLM-006 | BERT/LLaMA | 提供 BERT/LLaMA communication trace，不执行模型训练且吞吐为空 | 完成 BERT/LLaMA 端到端训练验证 | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C performance report | 仅可展示通信 trace | real_model_executed=false |
| CLM-007 | HCCS/RoCE/PCIe | 基于项目参数来源的相对链路 profile 进行模拟 | 测得真实 HCCS/RoCE/PCIe 带宽或利用率 | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C topology report | 可展示参数卡片 | 未硬件校准 |
| CLM-008 | direct API | 官方 ABI/build/link/guard/lifecycle readiness 已静态或 host 验证 | direct HCCL collective 成功或 runtime 已初始化 | ASCEND_HCCL_DIRECT | E3_HOST_EXECUTED | G3-C direct appendix | 只可展示 readiness 状态 | direct_hccl_api_call=false |
| CLM-009 | NPU performance | 当前没有真实 NPU 性能数据 | 真实 NPU latency/bandwidth/utilization 已测量 | REAL_DEVICE_NOT_EXECUTED | E0_NONE | claim boundary section | 显示 HARDWARE_BLOCKED | measured_on_real_npu=false |
| CLM-010 | msprof | simulator profiling trace 可用，msprof 未执行 | 已运行 msprof 或获得真实 profiling | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C performance report | 仅展示 simulator trace | msprof_executed=false |
| CLM-011 | zero CPU intervention | 仅为赛题目标/设计方向，当前未验证 | 实现或测得零 CPU 介入 | DIRECT_READINESS_ONLY | E1_DOCUMENTED | known limitations | 不得作为成果画面 | 无 C/C++ 实现或设备 evidence |
| CLM-012 | performance target achievement | G2-F-6 simulator performance/scale/reliability gates通过；赛题 90% 线性加速目标未验证 | 性能目标全部达成 | SIMULATOR_ACCEPTANCE | E5_SIMULATOR_VALIDATED | G3-C performance report | 可展示分项状态 | 缺 compute workload 与真实训练吞吐 |
| CLM-013 | C/C++ plugin | CPU_SIM C .so 可构建；direct C++ 为静态 compile-only readiness | 已交付官方 HCCL direct plugin .so | CPU_SIM_AND_DIRECT_READINESS | E3_HOST_EXECUTED | G3-C plugin appendix | 可展示两条轨道对比 | 最终插件 ABI/包装层未完成 |
| CLM-014 | Agent-generated code | 仓库包含 Agent/Skills/Prompt 与代码生成工具，但历史核心代码生成链不可用 | 全部核心代码已由 Agent 生成且可完整复现 | AGENT_ENGINEERING | E2_STATIC_VERIFIED | G3-D Agent report | 必须显示 HISTORICAL_RECORD_UNAVAILABLE | 缺原始 Prompt、run log、commit mapping 与人工披露 |
