# G2-D HCCL-VM 官方验证后端完成报告

审计日期：2026-07-30
分支：`g2-hccl-vm-integration`
总体状态：`COMPLETED`

## 1. 总体状态

G2-D 已完成。`ASCEND_HCCL_VM` 是显式启用、与默认 `CPU_SIM` 隔离的外部验证后端。它通过 subprocess 驱动官方 HCCL-VM、mock-comm、hccl_test 和 checker；这不是 hccl-agent 直接链接或直接调用真实 HCCL API，也不代表真实 Ascend NPU 验证。

## 2. Checkpoint 状态

| Checkpoint | 状态 | 结果 |
|---|---|---|
| G2-D-1 | COMPLETED | 后端、配置、环境变量和 CLI |
| G2-D-2 | COMPLETED | 环境发现和 diagnose |
| G2-D-3 | COMPLETED | shell-safe dry-run |
| G2-D-4 | COMPLETED | Checker 和退出码严格解析 |
| G2-D-5 | COMPLETED | 2-rank INT32 SUM AllReduce 官方闭环 |
| G2-D-6 | COMPLETED | Agent 报告和 evidence 归档 |
| G2-D-7 | COMPLETED | Windows/Linux CPU_SIM、全量测试和最终审计 |

## 3. Commits

| Checkpoint | Commit |
|---|---|
| baseline | `700ff0e` |
| G2-D-1 | `b760cfc` |
| G2-D-2 | `7fc614b` |
| G2-D-3 | `8bf1956` |
| G2-D-4 | `0d61584` |
| G2-D-5 | `d39f0d5` |
| G2-D-6 | `819c4dc` |
| G2-D-7 | 本报告所在 commit，message 为 `G2-D-7 official backend regression evidence` |

未执行 push、merge 或远端修改。

## 4. 修改文件

实现集中在 `main.py`、`config/hccl_vm.json`、`plugin/hccl_vm_backend.py`、`plugin/hccl_vm_env.py`、`plugin/hccl_vm_runner.py`、`plugin/hccl_vm_checker.py`、`plugin/hccl_vm_evidence.py` 和 `agent/report_generator.py`。新增或扩展了对应的 `tests/test_backend_selection.py`、`tests/test_hccl_vm_*.py`、计划、完成报告和一份 G2-D evidence。未修改 `/home/workspace/hcomm`、`/home/workspace/hccl` 或 CANN 安装内容。

## 5. 双后端架构

- `CPU_SIM`：默认后端，继续走既有 `HCCLAgent`、Python 模型和 CPU C 插件。
- `ASCEND_HCCL_VM`：仅由 `diagnose`、`dry-run`、`verify-official` 显式进入。
- 官方后端在 Windows 通过 `wsl.exe` 传输，在 Linux/WSL 内通过 `bash` 执行；模块导入不要求 WSL、CANN 或 HCCL-VM 存在。
- HCOMM/HCCL Git 元数据使用每次命令局部的 `git -c safe.directory=<精确配置路径>`，未修改全局或系统 Git 配置。

## 6. CLI 示例

```text
python main.py diagnose --backend ASCEND_HCCL_VM
python main.py dry-run --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16
python main.py verify-official --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16
python main.py --nodes 4 --message-size 128 --primitive AllReduce
```

## 7. Diagnose 摘要

正式 root 验证前 diagnose 返回 `OK`。CANN 版本为 9.1.0；HCCL-VM、all_reduce_test、checker、topology、mock-comm 112、Open MPI、`timeout` 和 `script` 均可用。HCOMM 为 `competition/campus-2026@c8a3dc68a37315aa1e908a971fa706abe612f6ee`，HCCL 为 `competition/campus-2026@2c87cc1937bab23b8574ef24017c03572d3340e2`，两个已跟踪工作树均为 clean。

## 8. Dry-run 摘要

dry-run 返回 `DRY_RUN` 和 `not_executed=true`，输出 shell-safe startup script、WSL/bash transport argv、mock-comm、mpirun/all_reduce_test、checker、exit 和成功条件。它不探测环境、不启动 HCCL-VM、不执行测试。

## 9. 官方验证命令

```powershell
wsl.exe -d Ubuntu-22.04 -u root -- bash -lc "cd /mnt/f/projects/hccl-agent && python3 main.py verify-official --backend ASCEND_HCCL_VM --primitive AllReduce --nodes 2 --dtype int32 --op sum --elements 16"
```

外层退出码：`0`。

## 10. AllReduce 与 Checker 结果

结果为 `PASS_WITH_WARNING`。hccl_config、mock-comm、all_reduce_test、checker、HCCL-VM 和外层退出码均为 0。两个 checker op summary 均为 `AllReduce / rankCount=2 / INT32 / SUM / elementCount=16`。观察到两次 `Checker Success`，五个 checker stage 均为 success；未观察到 Segmentation fault、MPI_ABORT、undefined symbol 或 fatal failure；观察到 HCCL-VM 正常关闭。

## 11. ErrorCode 103

记录到 4 条 `ErrorCode: 103` warning，摘要为 CCU post/local-post task 未被 Wait task 消费。该已知 warning 未单独导致失败，但结果严格标记为 `PASS_WITH_WARNING`，没有标记为 `PASS_CLEAN`。

## 12. Windows CPU_SIM 回归

- 默认 CPU_SIM CLI：PASS，退出码 0。
- 新后端模块在 Windows 无 WSL/CANN 导入要求：PASS，输出 `WINDOWS_IMPORT_OK`。
- Windows Release CTest：11/11 PASS。
- Windows 全量 Python：507 tests，OK，1 项 opt-in 真实环境测试 skipped。

## 13. Linux CPU_SIM 回归

- 独立构建目录：`/tmp/hccl-agent-g2d7-20260730T0820Z`。
- GCC 11.4.0，`HCCL_BACKEND=CPU_SIM` 配置和构建：PASS。
- Linux CTest：11/11 PASS。
- 使用新构建 `libhccl_plugin.so` 的默认 CPU_SIM CLI：PASS。
- Linux 全量 Python：507 tests，OK，1 项 opt-in 真实环境测试 skipped。

## 14. 全量测试数

Windows 和 Linux 分别运行 507 个 Python tests，均为 OK；数量高于既有 461 PASS 基线。默认跳过的是必须显式设置环境变量才执行的真实 HCCL-VM 集成测试，正式官方闭环已通过单独授权命令实际执行。

## 15. Evidence 与 SHA256

目录：

`experiments/hccl_vm/evidence/g2_d_20260730T081052.668860Z`

`SHA256SUMS` 文件自身 SHA256：

`bc8e82663a989e458311ccbbbb1b23a951635f4d19d4707ab6f71bbc1a8c70dc`

`sha256sum -c SHA256SUMS` 对 README、命令、精简日志、manifest、gzip 原始日志、报告和结果全部返回 `OK`。原始日志以 `raw.log.gz` 保存，没有提交大型未压缩日志。

## 16. 官方源码工作区证明

官方验证后执行：

```text
git -C /home/workspace/hcomm status --porcelain=v1 --untracked-files=no
git -C /home/workspace/hccl status --porcelain=v1 --untracked-files=no
```

两项输出均为空，退出码均为 0。随后对 `hccl-vm`、`hccl_test`、`all_reduce_test`、`checker` 和 `mpirun` 的精确进程名检查无输出。

## 17. 已知限制

- 只验证固定的 AllReduce、2 ranks、INT32、SUM、16 elements。
- 结果来自官方 HCCL-VM 模拟器和 checker，不是实际 NPU、真实多设备性能或可靠性证明。
- 后端通过 subprocess 驱动 hccl_test，不是 hccl-agent 直接 HCCL API 集成。
- ErrorCode 103 warning 仍存在，故结果不是 `PASS_CLEAN`。
- HCCL-VM 官方 `hccl_config.sh` 含环境特定历史路径；runner 记录其退出码并重新 source 已配置 CANN 环境。

## 18. 完成条件审计

CPU_SIM 默认兼容、显式后端隔离、无环境导入安全、路径覆盖、diagnose、dry-run、固定官方闭环、严格 metadata/Checker/退出码/致命错误判定、warning 保留、正常关闭、evidence、双平台 C/Python 回归、官方源码清洁和无残留进程均有实际命令或归档证据支持。G2-D 满足完成条件。

## 19. G2-E 技术入口

G2-E 应从官方工具的真实命令契约发现开始，而不是直接泛化当前 AllReduce 参数。先分别读取当前版本 hccl_test 的 AllGather、ReduceScatter 帮助和 checker 实际输出，冻结可执行文件、参数、metadata 和退出码契约；再把 `OfficialAllReduceRequest` 收敛为受白名单约束的 collective request/registry，每个 primitive 使用独立 command builder 和严格 parser 期望；最后按单 primitive、单 evidence、单 checkpoint 的顺序增加官方闭环。CPU_SIM 继续默认，真实 NPU 验证仍作为独立里程碑。
