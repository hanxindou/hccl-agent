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
