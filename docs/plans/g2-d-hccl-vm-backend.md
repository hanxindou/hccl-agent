# G2-D HCCL-VM 官方验证后端适配计划

## 0. 审查基线

本计划基于 2026-07-30 当前仓库和 WSL 只读检查结果制定。仓库根目录未发现 `AGENTS.md`。

已阅读的本仓库材料：

- `docs/project_documentation.md`
- `docs/project_audit.md`
- `experiments/hccl_vm/evidence/g2_official_baseline/g2_official_baseline.md`
- `experiments/hccl_vm/evidence/g2_official_baseline/environment_manifest.txt`
- `experiments/hccl_vm/evidence/g2_official_baseline/baseline_result.txt`
- 当前 CPU_SIM、HCCL API、插件、配置、CLI、测试与报告相关代码

已通过 WSL 只读检查的官方侧材料：

- `/home/workspace/hcomm/test/hccl_vm/README-Competition.md`
- `/home/workspace/hcomm/test/hccl_vm/hccl_vm_install/`
- `/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/`
- `/home/workspace/hcomm` 与 `/home/workspace/hccl` 当前分支和 commit

WSL 检查结果：

- WSL 发行版：`Ubuntu-22.04`
- CANN：`/home/workspace/Ascend/cann-9.1.0`
- HCCL-VM：`/home/workspace/hcomm/test/hccl_vm/hccl_vm_install`
- hccl_test：`/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin`
- HCOMM：`competition/campus-2026`，`c8a3dc68a37315aa1e908a971fa706abe612f6ee`
- HCCL：`competition/campus-2026`，`2c87cc1937bab23b8574ef24017c03572d3340e2`
- HCCL-VM 二进制存在：`bin/hccl-vm`
- HCCL-VM checker 插件存在：`plugin/checker/checker`
- HCCL-VM runner 插件存在：`plugin/runner/runner`
- 可用 topology profile 包括：`ascend950_cluster_32_server_normal.yaml` 等
- 可用 mock-comm profile 包括：`112.yaml` 等
- hccl_test 二进制包括：`all_reduce_test`、`all_gather_test`、`reduce_scatter_test` 等

G2 官方基线证据：

- AllGather INT32：`Checker Success`，进程退出码 0，`PASS_WITH_WARNING`
- AllReduce INT32 SUM：`Checker Success`，进程退出码 0，`PASS_WITH_WARNING`
- ReduceScatter INT32 SUM：`Checker Success`，进程退出码 0，`PASS_WITH_WARNING`
- 已知 warning：`ErrorCode: 103 - CCU post/local-post tasks were never consumed by a Wait task`
- 该 warning 不等于失败；只有 checker success 且退出码 0 才可视为通过。

## 1. 当前后端、插件和入口架构清单

当前入口是 `main.py`：

- `--nodes`
- `--message-size`
- `--primitive`
- 未暴露 `--backend`
- 未暴露 `diagnose`、`dry-run` 或官方验证子命令

当前主流程是 `agent/hccl_agent.py::HCCLAgent.run()`：

- 加载 `config/cluster.json`
- 推断拓扑并构造 `TopologyGraph`
- 构造硬件静态分析
- 调用 `PluginManager.discover()`
- 进行 planning、experience、knowledge、algorithm selection、LLM best-effort reasoning、simulator ranking、benchmark、reflection、auto-tuning、optimization loop、code generation、strategy、prompt logging
- 写入 `logs/runs.jsonl`、`logs/summary.json`、`logs/knowledge_base.jsonl`、`logs/experience.jsonl`

当前插件链路：

- `agent/plugin_manager.py` 包装 `plugin/hccl_bridge.py`
- `plugin/hccl_bridge.py` 使用 `ctypes.CDLL` 加载 `hcccl/build/libhccl_plugin.so` 或 Windows `hccl_plugin.dll`
- `HCCL_PLUGIN_PATH` 优先级高于默认候选路径
- 加载时绑定 `hcclPluginGetVersion`、`hcclPluginGetAlgorithms`、`hcclCommInit`、`hcclAllReduce`、`hcclAllGather`、`hcclReduceScatter`、`hcclBroadcast`
- `plugin/execution_engine.py` 通过 ctypes 调用 CPU_SIM C 插件数据路径
- `agent/execution_skill.py` 与 `agent/benchmark_skill.py` 是 Agent 侧执行和计时包装

当前 C 后端：

- `hcccl/CMakeLists.txt` 默认 `HCCL_BACKEND=CPU_SIM`
- 已有 `ASCEND_CANN` 配置探测边界，但它是 CANN/HCCL SDK 头库探测，不是 HCCL-VM 官方验证后端
- `CPU_SIM` 不依赖 CANN
- Windows 构建已配置导出符号和 UTF-8 编译选项
- `enable_testing()` 已存在，C 测试已注册

当前 HCCL-like C API：

- `hcccl/include/hccl_comm.h`
- `hcccl/include/hccl_algorithms.h`
- `hcccl/src/hccl_comm.c`
- `hcccl/src/hccl_algorithms.c`

当前 CPU_SIM 数据正确性边界：

- AllReduce：标准 wrapper 接入 Ring CPU_SIM；算法函数覆盖 Ring、Butterfly、Mesh、NHR、Fat-Tree
- AllGather：标准 wrapper 接入 Ring CPU_SIM；算法函数覆盖 Ring、Butterfly
- ReduceScatter：标准 wrapper 接入 Mesh CPU_SIM
- Broadcast：明确返回 `HCCL_ERR_NOT_SUPPORTED`
- dtype：C enum 中已有 `HCCL_INT32`，但 Python CPU_SIM helper 当前重点是 FP32/FP16/BF16 软件模拟；G2-D 官方闭环必须单独使用 hccl_test `int32`

当前报告链路：

- `agent/report_generator.py` 生成文本 report
- `scripts/generate_report.py` 从 `logs/runs.jsonl` 生成 Markdown performance report
- 尚无官方 HCCL-VM 验证结果结构、checker 解析、环境 manifest 生成和证据归档模块

## 2. G2-D 准确范围和非目标

目标：

- 在不修改官方 HCOMM/HCCL/CANN 的前提下，为 hccl-agent 增加 `ASCEND_HCCL_VM` 官方验证后端。
- 该后端通过 WSL 中的官方 HCCL-VM、mock-comm、hccl_test 和 checker 完成验证。
- 最小闭环为：由 hccl-agent 触发一个 2-rank INT32 SUM AllReduce 官方验证，checker 输出 `Checker Success`，整体命令退出码 0。
- 记录可复现证据：环境 manifest、执行命令、stdout/stderr 摘要、checker 解析、状态 JSON、原始日志引用或副本。
- CPU_SIM 保持默认后端，且 Windows 或无 CANN 环境下导入模块不失败。

非目标：

- 不实现真实 Ascend NPU 硬件执行。
- 不修改 `/home/workspace/hcomm` 或 `/home/workspace/hccl` 官方源码。
- 不重新安装、升级或覆盖 CANN。
- 不下载新依赖。
- 不复制整个 CANN/HCCL/HCOMM 仓库到 hccl-agent。
- 不把 subprocess 驱动 `hccl_test` 描述为“直接调用真实 HCCL API”。
- 不修改或伪造现有 G2-C/G2 官方基线原始证据。
- 不把 warning 103 当作失败，也不把未取得 checker success 的结果标记为完成。

## 3. CPU_SIM 与 ASCEND_HCCL_VM 双后端边界

后端定义建议：

- `CPU_SIM`：默认；现有 `hcccl` C 插件、ctypes、Simulator 和 Python Agent 流程；可在 Windows 和 Linux 无 CANN 环境运行。
- `ASCEND_HCCL_VM`：新增官方验证后端；只负责通过 WSL subprocess 驱动官方 HCCL-VM 工具链运行 hccl_test 并解析 checker；不加载 `libhccl_plugin.so`；不修改 CMake C 插件后端。
- `ASCEND_CANN`：保留现有 G1 CMake 探测边界；不在 G2-D 中扩展为真实 CANN 直连。

边界要求：

- `import agent.hccl_agent`、`import plugin.hccl_bridge`、`import plugin.execution_engine` 在无 CANN/无 WSL 环境下不能失败。
- 选择 `ASCEND_HCCL_VM` 前不得构造会立即加载官方库的对象。
- `ASCEND_HCCL_VM` 的返回结构必须标明 `execution_mode=subprocess_hccl_test`。
- `CPU_SIM` 的 benchmark 仍走 `ExecutionSkill`/`ExecutionEngine`。
- `ASCEND_HCCL_VM` 的 benchmark/verification 走新增官方验证 runner，不与 CPU_SIM 的 `ctypes` result 混用。

## 4. 环境发现机制

新增模块建议：

- `plugin/hccl_vm_backend.py`
- `plugin/hccl_vm_env.py`
- `plugin/hccl_vm_runner.py`
- `plugin/hccl_vm_checker.py`

默认路径：

- `HCCL_VM_WSL_DISTRO=Ubuntu-22.04`
- `HCCL_VM_CANN_PATH=/home/workspace/Ascend/cann-9.1.0`
- `HCCL_VM_INSTALL_DIR=/home/workspace/hcomm/test/hccl_vm/hccl_vm_install`
- `HCCL_VM_HCCL_TEST_BIN=/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin`
- `HCCL_VM_TOPOLOGY=ascend950_cluster_32_server_normal.yaml`
- `HCCL_VM_MOCK_COMM=112`
- `HCCL_VM_EXPANSION_MODE=CCU_SCHED`

发现步骤：

1. Windows 侧确认 `wsl.exe` 可执行，并可进入指定 distro。
2. WSL 侧确认 CANN `set_env.sh` 存在。
3. WSL 侧确认 `hccl-vm` 可执行。
4. WSL 侧确认 topology yaml 存在。
5. WSL 侧确认 mock-comm yaml 存在。
6. WSL 侧确认 `all_reduce_test`、`all_gather_test`、`reduce_scatter_test` 至少目标二进制存在。
7. WSL 侧加载 CANN env 后确认 `LD_LIBRARY_PATH` 能解析 `libhccl.so`，不要只检查文件存在。
8. WSL 侧记录 HCOMM/HCCL 分支和 commit。
9. WSL 侧记录 `mpirun` 路径和类型；OpenMPI 使用 `--allow-run-as-root --oversubscribe`，MPICH 不使用这两个参数。
10. 生成 `environment_manifest.txt` 或 JSON，写入新的 G2-D evidence 目录。

ENV_BLOCKED 条件：

- WSL 不可用或 distro 不存在。
- CANN 路径缺失。
- CANN env 加载后仍无法解析 hccl_test 依赖库。
- HCCL-VM `bin/hccl-vm` 缺失或不可执行。
- topology profile 缺失。
- mock-comm profile 缺失。
- hccl_test 目标二进制缺失。
- checker 插件缺失。
- HCOMM/HCCL 分支不是预期分支，除非用户显式确认继续。

## 5. 环境变量、配置项和 CLI 设计

新增配置文件建议：

- `config/hccl_vm.json`

建议字段：

```json
{
  "backend": "CPU_SIM",
  "wsl_distro": "Ubuntu-22.04",
  "cann_path": "/home/workspace/Ascend/cann-9.1.0",
  "hccl_vm_install_dir": "/home/workspace/hcomm/test/hccl_vm/hccl_vm_install",
  "hccl_test_bin": "/home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin",
  "topology": "ascend950_cluster_32_server_normal.yaml",
  "mock_comm": "112",
  "expansion_mode": "CCU_SCHED",
  "check_only": true,
  "output_dir": "experiments/hccl_vm/evidence/g2_d_latest"
}
```

环境变量优先级建议：

1. CLI 参数
2. 环境变量
3. `config/hccl_vm.json`
4. 内置默认值

新增 CLI 建议：

- `python main.py --backend CPU_SIM ...`
- `python main.py --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16 --official-verify`
- `python main.py diagnose --backend ASCEND_HCCL_VM`
- `python main.py dry-run --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16`
- `python main.py verify-official --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16`

兼容性要求：

- 不传 `--backend` 时行为必须等价于当前 CPU_SIM。
- 现有 `--nodes`、`--message-size`、`--primitive` 保持兼容。
- `diagnose` 和 `dry-run` 不启动 HCCL-VM。
- `verify-official` 才允许启动 HCCL-VM、mock-comm、mpirun 和 checker。

## 6. diagnose 与 dry-run 能力

`diagnose` 输出：

- backend
- host OS
- WSL distro 是否可用
- CANN path、set_env.sh、ASCEND_HOME_PATH
- HCCL-VM install dir、hccl-vm path
- topology profile path
- mock-comm yaml path
- hccl_test 二进制 path
- checker plugin path
- mpirun path/type
- HCOMM/HCCL branch 与 commit
- 每项状态：`OK`、`WARN`、`ENV_BLOCKED`

`dry-run` 输出：

- 将要执行的 WSL 命令，不启动 HCCL-VM。
- 将要设置的环境变量。
- 将要运行的 hccl_test 命令。
- 将要解析的成功条件。
- 预计 evidence 输出目录。

dry-run 不能写入成功证据，最多写入 dry-run manifest，并标明 `not_executed=true`。

## 7. 2-rank INT32 SUM AllReduce 官方验证最小闭环

最小闭环输入：

- backend：`ASCEND_HCCL_VM`
- primitive：`AllReduce`
- ranks：2
- dtype：`int32`
- reduce op：`sum`
- elements：16
- bytes：64
- topology：`ascend950_cluster_32_server_normal.yaml`
- mock-comm：`112`
- checker：Checker V3 默认配置

官方执行命令形态：

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc "<generated bash script>"
```

WSL 内部脚本逻辑：

```bash
set -o pipefail
export ASCEND_HOME_PATH=/home/workspace/Ascend/cann-9.1.0
source /home/workspace/Ascend/cann-9.1.0/set_env.sh
cd /home/workspace/hcomm/test/hccl_vm/hccl_vm_install
export LD_LIBRARY_PATH=$ASCEND_HOME_PATH/lib64:$ASCEND_HOME_PATH/devlib:$LD_LIBRARY_PATH
export RANK_TABLE_FILE=$(pwd)/data/ranktable.json
export HCCL_OP_EXPANSION_MODE=CCU_SCHED
cd /home/workspace/hcomm/test/hccl_vm/hccl_vm_install/bin
./hccl-vm start ascend950_cluster_32_server_normal.yaml --check-only
```

进入 `(hvm)$>` 后按序发送：

```text
hccl-vm mock-comm 112
mpirun --allow-run-as-root --oversubscribe -np 2 /home/workspace/Ascend/cann-9.1.0/tools/hccl_test/bin/all_reduce_test -b 64 -e 64 -d int32 -o sum -w 0 -n 1 -c 1
hccl-vm plugin run @checker
exit
```

成功判定：

- WSL 命令退出码为 0。
- checker 输出至少一个 `Checker Success`。
- 无 Checker stage failure。
- 无 fatal error。
- 如果出现 warning 103，记录为 `PASS_WITH_WARNING`，不当作失败。
- 未满足上述条件时状态只能是 `FAIL` 或 `ENV_BLOCKED`，不能是 `PASS`。

## 8. 启动、执行、checker、退出与解析

实现建议：

- 使用 `subprocess.Popen` 启动 `wsl.exe -d Ubuntu-22.04 -- bash -lc ...`。
- HCCL-VM 是交互式 shell，不建议用多层 shell 字符串拼接业务命令；应由 Python runner 写入 stdin，并持续收集 stdout/stderr。
- runner 必须设置总超时和分阶段超时。
- 每一步输出结构化事件：
  - `start_hccl_vm`
  - `mock_comm`
  - `run_hccl_test`
  - `run_checker`
  - `exit_hccl_vm`
  - `parse_result`
- 无论成功失败都必须尝试发送 `exit` 并等待进程退出。
- 超时后只终止由 runner 启动的 HCCL-VM 进程，不执行广泛清理命令。

checker 解析规则：

- `Checker Success`：成功信号。
- `RunChecker`、`GenGraph`、`SingleTaskCheck`、`MemConflict`、`SemanticCheck`：记录阶段信息。
- `[error]`、`Checker Failed`、`stage failed`、`fatal`：失败信号。
- `ErrorCode: 103`：已知 warning，记录到 `warnings`。
- `check_result: success`：runner 数据校验信号；G2-D 最小闭环以 checker 为准。

结果结构建议：

```json
{
  "backend": "ASCEND_HCCL_VM",
  "execution_mode": "subprocess_hccl_test",
  "primitive": "AllReduce",
  "rank_count": 2,
  "dtype": "int32",
  "reduce_op": "sum",
  "elements": 16,
  "bytes": 64,
  "checker_success": true,
  "exit_code": 0,
  "warnings": ["103"],
  "status": "PASS_WITH_WARNING"
}
```

## 9. Windows 原生 Codex 通过 wsl.exe 验证

所有 Linux 侧验证必须从 Windows 项目中通过以下形态触发：

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && <command>"
```

建议验证命令：

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python -m unittest tests.test_hccl_vm_env -q"
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python -m unittest tests.test_hccl_vm_checker -q"
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py diagnose --backend ASCEND_HCCL_VM"
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py dry-run --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py verify-official --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
```

Windows 原生回归命令：

```powershell
python -m unittest tests.test_g1_cann_backend_config tests.test_plugin_bridge tests.test_execution_engine -q
python main.py --nodes 4 --message-size 128 --primitive AllReduce
```

## 10. 测试、回归和日志证据

单元测试：

- `tests/test_hccl_vm_env.py`
  - 默认路径解析
  - 环境变量覆盖
  - 缺路径返回 `ENV_BLOCKED`
  - 无 WSL 不影响模块导入
- `tests/test_hccl_vm_checker.py`
  - 解析 `Checker Success`
  - 解析 warning 103
  - stage failure 判定失败
  - exit code 非 0 判定失败
- `tests/test_hccl_vm_runner_dry_run.py`
  - dry-run 不启动 subprocess
  - 命令参数和 evidence path 正确
- `tests/test_backend_selection.py`
  - 默认 CPU_SIM
  - `ASCEND_HCCL_VM` 分支不构造 CPU plugin loader
  - 未知 backend 报清晰错误

集成测试：

- WSL 环境诊断：`python main.py diagnose --backend ASCEND_HCCL_VM`
- WSL dry-run：`python main.py dry-run --backend ASCEND_HCCL_VM ...`
- 官方最小闭环：`python main.py verify-official --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16`

全量回归：

- Windows：现有 Python unittest 子集和 CPU_SIM CLI smoke。
- Linux/WSL：CPU_SIM CMake + CTest；Python unit tests；官方 HCCL-VM verify。
- 不要求真实 Ascend NPU 验证。

日志证据建议目录：

- `experiments/hccl_vm/evidence/g2_d_<timestamp>/environment_manifest.txt`
- `experiments/hccl_vm/evidence/g2_d_<timestamp>/commands.txt`
- `experiments/hccl_vm/evidence/g2_d_<timestamp>/official_verify_stdout.log`
- `experiments/hccl_vm/evidence/g2_d_<timestamp>/official_verify_stderr.log`
- `experiments/hccl_vm/evidence/g2_d_<timestamp>/checker_result.json`
- `experiments/hccl_vm/evidence/g2_d_<timestamp>/summary.md`

不得修改：

- `experiments/hccl_vm/evidence/g2_official_baseline/*`
- `/home/workspace/hcomm/*`
- `/home/workspace/hccl/*`
- `/home/workspace/Ascend/cann-9.1.0/*`

## 11. Checkpoints

### G2-D-1 后端枚举与配置

文件范围：

- 新增 `config/hccl_vm.json`
- 新增或修改 backend 选择相关 Python 模块
- 修改 `main.py` CLI 解析
- 新增 `tests/test_backend_selection.py`

验证命令：

```powershell
python -m unittest tests.test_backend_selection -q
python main.py --nodes 4 --message-size 128 --primitive AllReduce
```

建议 commit：

- `G2-D-1 backend selection config and CLI`

### G2-D-2 HCCL-VM 环境发现与 diagnose

文件范围：

- 新增 `plugin/hccl_vm_env.py`
- 修改 `main.py`
- 新增 `tests/test_hccl_vm_env.py`

验证命令：

```powershell
python -m unittest tests.test_hccl_vm_env -q
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py diagnose --backend ASCEND_HCCL_VM"
```

建议 commit：

- `G2-D-2 diagnose official hccl-vm environment`

### G2-D-3 dry-run 命令生成

文件范围：

- 新增 `plugin/hccl_vm_runner.py`
- 新增 `tests/test_hccl_vm_runner_dry_run.py`
- 修改 `main.py`

验证命令：

```powershell
python -m unittest tests.test_hccl_vm_runner_dry_run -q
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py dry-run --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
```

建议 commit：

- `G2-D-3 dry run official validation command`

### G2-D-4 checker 解析

文件范围：

- 新增 `plugin/hccl_vm_checker.py`
- 新增 `tests/test_hccl_vm_checker.py`

验证命令：

```powershell
python -m unittest tests.test_hccl_vm_checker -q
```

建议 commit：

- `G2-D-4 parse hccl-vm checker output`

### G2-D-5 官方 AllReduce 最小闭环

文件范围：

- 完成 `plugin/hccl_vm_runner.py`
- 修改 `main.py`
- 新增 `tests/test_hccl_vm_official_flow.py`，默认跳过真实环境，检测到 WSL/CANN 后可运行

验证命令：

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py verify-official --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
```

建议 commit：

- `G2-D-5 verify allreduce through official hccl-vm`

### G2-D-6 Agent 报告与证据归档

文件范围：

- 修改 `agent/report_generator.py`
- 修改或新增 evidence writer
- 新增 `tests/test_hccl_vm_report.py`

验证命令：

```powershell
python -m unittest tests.test_hccl_vm_report -q
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py verify-official --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
```

建议 commit：

- `G2-D-6 record official validation evidence`

### G2-D-7 全量回归与完成判定

文件范围：

- 只允许修复 G2-D 相关测试、文档和后端适配文件

验证命令：

```powershell
python -m unittest discover -s tests -q
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && cmake -S hcccl -B /tmp/hccl-agent-hcccl-cpu -DHCCL_BACKEND=CPU_SIM && cmake --build /tmp/hccl-agent-hcccl-cpu && ctest --test-dir /tmp/hccl-agent-hcccl-cpu --output-on-failure"
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/f/projects/hccl-agent && python main.py verify-official --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
```

建议 commit：

- `G2-D-7 official backend regression evidence`

## 12. 阻塞条件和 ENV_BLOCKED 处理

阻塞分类：

- `ENV_BLOCKED_WSL`: Windows 无法启动 WSL 或 distro 不存在。
- `ENV_BLOCKED_CANN`: CANN 路径、`set_env.sh` 或 `libhccl.so` 解析失败。
- `ENV_BLOCKED_HCCL_VM`: `hccl-vm`、topology 或 mock-comm 缺失。
- `ENV_BLOCKED_HCCL_TEST`: hccl_test 目标二进制缺失或无法加载。
- `ENV_BLOCKED_CHECKER`: checker 插件缺失或无法运行。
- `ENV_BLOCKED_BRANCH`: HCOMM/HCCL 分支或 commit 与预期不一致。
- `ENV_BLOCKED_TIMEOUT`: HCCL-VM 交互超时且无法确认 checker 结果。

处理要求：

- `ENV_BLOCKED` 必须携带缺失项、检查命令、退出码和 stdout/stderr 摘要。
- `ENV_BLOCKED` 不得写成 PASS。
- `ENV_BLOCKED` 可以写 evidence manifest，标明未完成官方验证。
- 用户修复环境后可以重复执行同一命令。

## 13. 风险、回滚策略和完成标准

风险：

- HCCL-VM 交互式 shell 输出格式变化，导致 prompt 等待逻辑不稳定。
- hccl_test `-h` 在无真实设备上下文中会打印 `aclrtGetSocName failed`，不能简单按字符串 `failed` 判定环境失败。
- warning 103 是当前官方基线已知 warning，不能当作失败，也不能忽略不记录。
- Windows PowerShell、WSL bash、HCCL-VM 交互 shell 三层 quoting 容易出错。
- `HCCLAgent.run()` 当前有日志副作用；官方验证 CLI 应避免普通 dry-run 写入历史经验。
- 全量 `unittest discover` 可能依赖已构建 CPU_SIM 插件；测试需要明确 skip 或前置说明。

回滚策略：

- 所有 G2-D 新代码集中在新增 VM 后端模块、CLI 分支、测试和报告扩展。
- CPU_SIM 默认路径保留原行为；若 G2-D 出现问题，可移除 `ASCEND_HCCL_VM` CLI 分支和新增模块，不影响 `hcccl/` CPU_SIM。
- 不修改官方目录，因此官方侧无需回滚。
- 不修改 G2 官方基线证据，因此证据链不会被覆盖。

完成标准：

- `python main.py --nodes 4 --message-size 128 --primitive AllReduce` 默认 CPU_SIM 行为保持可用。
- 无 CANN/无 WSL 环境下导入模块和 CPU_SIM 单元测试不失败。
- `diagnose --backend ASCEND_HCCL_VM` 能清晰输出 OK/WARN/ENV_BLOCKED。
- `dry-run --backend ASCEND_HCCL_VM` 能输出完整命令但不启动官方工具。
- `verify-official --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16` 由 hccl-agent 触发官方 HCCL-VM、mock-comm、hccl_test、checker、exit 全链路。
- checker 解析得到 `Checker Success`。
- 外层命令退出码为 0。
- evidence 目录记录环境、命令、日志和结构化结果。
- 未取得 Checker Success 和退出码 0 时，不标记 G2-D 完成。
