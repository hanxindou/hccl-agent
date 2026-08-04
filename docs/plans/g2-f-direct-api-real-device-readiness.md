# G2-F：官方 HCCL/HCOMM 直接 API 集成与真实设备验证就绪计划

## 0. 本计划的结论、范围和起始审计

本计划把 G2-F 明确拆为两个不可互相替代的交付：

- **G2-F Readiness**：在当前无 NPU 的环境完成 API/ABI 冻结、可构建及可链接的原生 adapter、诊断、无 mock 的单元测试和现有后端回归。
- **G2-F Real-device Acceptance**：仅在真实 Ascend NPU 上完成 communicator、stream、device buffer 和三种集合通信的直接调用、数据正确性、性能、规模与可靠性证据。

本轮开始时已只读确认：

| 检查                   | 结果                                            |
| ---------------------- | ----------------------------------------------- |
| 当前分支               | `main`                                          |
| `main` / `origin/main` | 同为 `bd3b91fb072d99b6135ba1ca0529926dd1b20dec` |
| 工作区                 | clean（创建本计划前）                           |
| G2-E                   | 已在 `main`；`b9438c6` 是 `main` 的祖先         |
| 旧功能分支             | 未在 G2-D/G2-E 分支工作                         |

本计划只定义未来工作；不修改业务实现、不会重写 G2-D/G2-E evidence，也不把 HCCL-VM 或 CPU_SIM 的结果表述为 direct API 或真实设备结果。

## 1. 当前架构与不可混淆边界

当前有三条不同的路径，必须继续独立命名、独立测试、独立出证：

| 路径                          | 当前入口/实现                                                                           | 可以证明                                        | 绝不能证明                              |
| ----------------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------- | --------------------------------------- |
| `CPU_SIM`                     | `hcccl/` 的项目自有 C ABI，`plugin/hccl_bridge.py` ctypes，`plugin/execution_engine.py` | CPU 内存布局、FP32/FP16/BF16 模拟结果和项目回归 | CANN/HCCL ABI、NPU 通信、性能           |
| `ASCEND_HCCL_VM`              | `main.py` → `plugin/hccl_vm_backend.py` → 官方 `hccl_test` subprocess                   | 官方 HCCL-VM 的固定 2-rank INT32 checker 合约   | 本进程直接 HCCL 调用或真实 NPU          |
| **未来 `ASCEND_HCCL_DIRECT`** | 新的独立 native direct adapter → `libhccl.so` / `libhcomm.so` / ACL runtime             | 编译与运行的进程直接调用正式导出 API            | 除非有实机 evidence，否则不宣称设备成功 |

G2-E 汇总 evidence 已固定 `execution_mode=subprocess_hccl_test`、`direct_hccl_api_call=false`、`real_ascend_npu_validated=false`。G2-F 不得改写这些字段，也不得复用其 `COMPLETED` 作为 direct API 完成依据。

当前 `hcccl/CMakeLists.txt` 的 `ASCEND_CANN` 只是 `STUB_UNVERIFIED` 的探测/链接边界；`plugin/hccl_api.py` 的同名 Python 函数仍是 simulator/CPU_SIM 兼容层。因此两者均不得被重命名为 direct API 实现。

## 2. 实际发现的官方安装、仓库与 ABI

### 2.1 安装与源码固定点

| 项目                 | 实际发现                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------ |
| CANN root            | `/home/workspace/Ascend/cann-9.1.0`                                                                          |
| 公开 include / lib64 | `include -> x86_64-linux/include`、`lib64 -> x86_64-linux/lib64`                                             |
| CANN/HCCL 版本       | `9.1.0`（`version/hccl_version.h` 的 `HCCL_VERSION_STR`）                                                    |
| 环境脚本             | `/home/workspace/Ascend/cann-9.1.0/set_env.sh`；只在子 shell 中设置 `LD_LIBRARY_PATH`、`ASCEND_HOME_PATH` 等 |
| HCOMM                | `competition/campus-2026@c8a3dc68a37315aa1e908a971fa706abe612f6ee`，tracked worktree clean                   |
| HCCL                 | `competition/campus-2026@2c87cc1937bab23b8574ef24017c03572d3340e2`，tracked worktree clean                   |

公开候选头文件是 `hccl/hccl.h`、`hccl/hccl_comm.h`、`hccl/hccl_types.h`、`acl/acl.h`、`acl/acl_rt.h`。`hcomm/hcomm_primitives.h` 等也存在，但本计划的 host-side collective ABI 以安装包中上述 `hccl/` 公开头为准；不得直接依赖 HCOMM 私有源码头。

| 库          | 路径                                  | SONAME         | 关键依赖/用途                                                                                              |
| ----------- | ------------------------------------- | -------------- | ---------------------------------------------------------------------------------------------------------- |
| HCCL facade | `.../x86_64-linux/lib64/libhccl.so`   | `libhccl.so`   | 依赖 `libhcomm.so`、`libhccl_compat.so`、`libacl_rt.so`；导出三种集合通信                                  |
| HCOMM       | `.../x86_64-linux/lib64/libhcomm.so`  | `libhcomm.so`  | 依赖 `libhccl_alg.so`、`libhccl_plf.so`、`libhccl_v2.so`、`libacl_rt.so`；导出 communicator/root-info 管理 |
| ACL runtime | `.../x86_64-linux/lib64/libacl_rt.so` | `libacl_rt.so` | 依赖 `libruntime.so` 等；导出 runtime、device、stream、内存 API                                            |

没有执行中的 toolkit 环境时，`ldd` 不会从系统缓存解析这些库；在**仅影响子 shell 环境**地 `source set_env.sh` 后，三者依赖均解析到该 CANN root。这是依赖解析结果，不是 `dlopen`、`aclInit` 或设备调用成功。

### 2.2 已确认的正式直接调用链

下面的名称、签名和符号均来自实际安装头文件和 `nm -D --defined-only`；没有由记忆推测。

| 阶段               | 正式 API（精确签名）                                                                                                                       | 头文件             | 导出库/符号              | 合约与前置条件                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ | ------------------------ | ---------------------------------------------------------------------------------------------------- |
| runtime            | `aclError aclInit(const char *configPath)` / `aclError aclFinalize()`                                                                      | `acl/acl_rt.h`     | `libacl_rt.so`，均为 `T` | 每进程 `aclInit` 仅一次；退出前 `aclFinalize`；是否可在无设备环境调用尚未由头文件证明为无副作用      |
| device/context     | `aclrtSetDevice(int32_t)`，`aclrtCreateContext(aclrtContext *, int32_t)`，`aclrtDestroyContext(aclrtContext)`，`aclrtResetDevice(int32_t)` | `acl/acl_rt.h`     | `libacl_rt.so`，均为 `T` | `SetDevice` 可隐式创建默认 context；显式 context 只能销毁自己创建的对象；这些都是实机步骤            |
| stream             | `aclrtCreateStream(aclrtStream *)`，`aclrtSynchronizeStream(aclrtStream)`，`aclrtDestroyStream(aclrtStream)`                               | `acl/acl_rt.h`     | `libacl_rt.so`，均为 `T` | 销毁前必须同步；stream 是三原语的最后一个参数                                                        |
| device memory      | `aclrtMalloc(void **, size_t, aclrtMemMallocPolicy)`，`aclrtFree(void *)`                                                                  | `acl/acl_rt.h`     | `libacl_rt.so`，均为 `T` | `aclrtMalloc` 返回 device memory；只能由 `aclrtFree` 释放                                            |
| transfer           | `aclrtMemcpy(void *, size_t, const void *, size_t, aclrtMemcpyKind)`；`aclrtMemcpyAsync(..., aclrtMemcpyKind, aclrtStream)`                | `acl/acl_rt.h`     | `libacl_rt.so`，均为 `T` | count 是字节；异步拷贝需 stream 同步；使用 `ACL_MEMCPY_HOST_TO_DEVICE` / `ACL_MEMCPY_DEVICE_TO_HOST` |
| rank-table comm    | `HcclCommInitClusterInfo(const char *, uint32_t, HcclComm *)`                                                                              | `hccl/hccl_comm.h` | `libhcomm.so`，`W`       | `clusterInfo` 是含文件名的路径，rank 为当前 rank；返回的 `HcclComm` 由调用方销毁                     |
| root-info comm     | `HcclGetRootInfo(HcclRootInfo *)`；`HcclCommInitRootInfo(uint32_t, const HcclRootInfo *, uint32_t, HcclComm *)`                            | `hccl/hccl_comm.h` | `libhcomm.so`，`W`       | `HcclRootInfo` 长度为 4108 字节；root-info 的进程间分发、rank 启动和超时策略必须在 G2-F-1 冻结       |
| comm destroy/error | `HcclCommDestroy(HcclComm)`；`const char *HcclGetErrorString(HcclResult)`                                                                  | `hccl/hccl_comm.h` | `libhcomm.so`，`W`       | 先完成/同步使用，再销毁 comm；保留原始 `HcclResult` 与字符串                                         |
| AllReduce          | `HcclAllReduce(void *, void *, uint64_t count, HcclDataType, HcclReduceOp, HcclComm, aclrtStream)`                                         | `hccl/hccl.h`      | `libhccl.so`，`T`        | count 是输出元素数；dtype 支持列表含 FP16/FP32/FP64/BFP16 和整型；op 为 SUM/PROD/MAX/MIN             |
| AllGather          | `HcclAllGather(void *, void *, uint64_t sendCount, HcclDataType, HcclComm, aclrtStream)`                                                   | `hccl/hccl.h`      | `libhccl.so`，`T`        | sendCount 是每 rank 输入元素数；输出容量必须按 world size 计算                                       |
| ReduceScatter      | `HcclReduceScatter(void *, void *, uint64_t recvCount, HcclDataType, HcclReduceOp, HcclComm, aclrtStream)`                                 | `hccl/hccl.h`      | `libhccl.so`，`T`        | recvCount 是每 rank 输出元素数；输入容量必须按 world size 计算                                       |

`HcclDataType` 的已确认枚举包括 `HCCL_DATA_TYPE_FP16=3`、`FP32=4`、`FP64=10`、`BFP16=11`；`HcclReduceOp` 为 `SUM=0`、`PROD=1`、`MAX=2`、`MIN=3`；成功码是 `HCCL_SUCCESS=0`。adapter 必须使用这些官方枚举，不能复用项目 CPU_SIM 的数值定义或字符串映射。

**buffer 位置的结论：** ACL 头文件明确把 `aclrtMalloc` 的结果定义为 device memory，且 `aclrtMemcpy` 的 kind 区分 host/device；`hccl.h` 的三原语参数说明只称为 data address，未在该声明中明确 buffer locality。因此 G2-F-1 必须将“collective buffer 必须为 ACL device memory”作为待官方实例/实机契约复核项；在证据确认前，adapter 必须拒绝把 host 指针传给三原语，不能以 CPU 指针试错。

### 2.3 生命周期和清理顺序

未来实机 harness 的唯一允许顺序是：

```text
aclInit
  -> aclrtSetDevice
  -> [可选：aclrtCreateContext；记录是否使用显式 context]
  -> aclrtCreateStream
  -> HcclCommInitClusterInfo 或 HcclGetRootInfo + HcclCommInitRootInfo
  -> aclrtMalloc(send/recv)
  -> H2D aclrtMemcpy[/Async]
  -> HcclAllReduce | HcclAllGather | HcclReduceScatter
  -> aclrtSynchronizeStream
  -> D2H aclrtMemcpy
  -> 比对数据和检查异步 HCCL 错误
  -> aclrtFree(all buffers)
  -> HcclCommDestroy
  -> aclrtDestroyStream
  -> [若创建：aclrtDestroyContext]
  -> aclrtResetDevice
  -> aclFinalize
```

在任何失败分支，只清理已经取得所有权的对象，按反序执行；保留每个 ACL/HCCL 返回码、`HcclGetErrorString`、清理返回码和首个业务错误。不得用强制 destroy/reset 覆盖证据中的原始失败，也不得在一个进程内把已 `aclFinalize` 的 runtime 再次用于其他测试。

## 3. 当前环境分类

### A. 现在可以完成（Readiness）

可安全完成官方头/库/符号 inventory、ABI manifest 和文件哈希、原生 adapter 的接口设计、CMake configure、build-only 编译、链接审计、`readelf`/`nm`/`ldd` 符号发现、以及不触发 runtime 的 diagnose。也可完成纯本地无 mock 单元测试、CPU_SIM CTest/Python 回归和 G2-E 回归。

可记录的成功状态只有 `BUILD_ONLY_PASS`、`LINK_PASS`、`SYMBOL_DISCOVERY_PASS`，以及对无设备 preflight 的 `NO_DEVICE_EXPECTED`。这些状态都不表示 communicator 或集合通信已运行。

### B. 可以考虑，但必须先证明无设备安全

`dlopen`/`LoadLibrary`、版本查询、导出符号查询、以及不创建 communicator 的诊断可在以后考虑；当前只完成了静态 ELF/依赖审计，**没有**执行 library load。任何实际调用（包括 `aclInit`）都必须先有该版本官方契约证明其不会创建设备 context、访问驱动或改变系统状态。没有该证明，就保持 `NO_DEVICE_EXPECTED` 或 `ENV_BLOCKED`，不以“试一下”决定安全性。

### C. 当前 `HARDWARE_BLOCKED`

WSL 中 `command -v npu-smi` 无结果、`/dev` 无 `davinci`/`ascend` 节点、`/proc`/`/sys/module` 无 Ascend 驱动指示，系统 `ldconfig` 也没有已安装的 ACL/HCCL/HCOMM runtime 条目。当前无 NPU 的事实是 `HARDWARE_BLOCKED`，不是代码失败。

以下工作必须等真实 NPU：device/context/stream 创建、communicator 和多 rank 建立、device memory 和拷贝、三原语调用/同步/正确性、拓扑、性能、扩缩容、故障注入和恢复。它们不得用 CPU_SIM、mock、HCCL-VM、`hccl_test` 或编译通过替代。

## 4. 推荐 adapter 架构

1. **语言和 ABI：** 使用 C++17 实现一个小型 RAII native adapter，但对 Python 暴露独立、稳定、异常不穿透的 `extern "C"` ABI。理由是官方 host API 是 C ABI，而 C++ RAII 最适合精确管理 runtime/context/stream/comm/buffer 的部分构造与失败反向清理。不要将 C++ 类型暴露给 ctypes。
2. **链接策略：** production adapter 采用直接链接 `libhccl.so`、`libhcomm.so`、`libacl_rt.so`，以便 build/link evidence 确认正式 API。另建不链接业务路径的 `hccl_direct_diagnose` 工具，必要时可 `dlopen` 仅做符号发现；它不是运行时 fallback，也不是 direct-call 证据。
3. **Python 边界：** 保留 Python `ctypes` 作为上层控制平面的短期入口，但仅加载项目自己的 `libhccl_direct_adapter.so`，绝不从 Python 直接绑定官方 HCCL/ACL。旧 `HCCLBridge` 继续只服务 CPU_SIM。这样能重用现有选择/报告框架，又使官方调用位置唯一、可审计。
4. **名称与 feature flag：** 新后端名为 `ASCEND_HCCL_DIRECT`；新增默认关闭的 `-DHCCL_ENABLE_ASCEND_HCCL_DIRECT=OFF`。不要把它塞进 `HCCL_BACKEND=CPU_SIM|ASCEND_CANN` 的同一 shared target；新增独立 target `hccl_direct_adapter`，避免含相同符号的 CPU_SIM 库冒充 direct 实现。
5. **ABI 隔离：** 保留现有 CPU_SIM C ABI 完全不变，但建立独立 direct ABI，例如 `hccl_direct_session_create` / `hccl_direct_collective` / `hccl_direct_session_destroy`。不导出 CPU_SIM 的 `hcclCommInit`/`hcclSetRank` 兼容符号，不能以“同名函数”隐藏实现差异。
6. **版本冻结：** CMake 必须要求单一绝对 `HCCL_CANN_ROOT`，读取并记录 CANN 9.1.0 版本宏、`readelf` SONAME、真实路径、SHA-256、HCOMM/HCCL branch+commit+clean 状态；拒绝 root 未设置、版本不符或依赖无法解析的构建。不得下载、安装或修改官方目录。
7. **所有权：** `DirectSession` 独占 process-scoped runtime lease、每 rank 绑定的 device/context/stream、`HcclComm`、send/recv device allocations；host 输入/输出由调用者拥有。API 阻止跨线程/跨 device 使用 session，禁止在未同步时释放 buffer/stream/comm。
8. **rank 启动：** 首选经用户批准的外部 launcher + rank-table 文件路径，使用 `HcclCommInitClusterInfo`，每进程一个 rank；root-info 路径作为单机/控制面实验，必须有显式 launcher、root-info 安全分发、rank-size/rank-id 和超时契约。不得沿用 HCCL-VM 的 `mpirun + hccl_test` subprocess。
9. **错误模型：** C ABI 返回项目定义的稳定状态和原始 `aclError`/`HcclResult`；Python 转为结构化异常/结果，不丢弃原始枚举、函数名、API 调用序号和 HCCL 错误字符串。
10. **无设备 diagnose：** 只返回具体缺失项（例如 `NO_DEVICE_EXPECTED`、缺库、版本漂移）；不创建 context、communicator、buffer 或 stream。只有按照官方契约证明安全的操作才能运行。

## 5. 证明“真正直接调用”的证据规则

`direct_hccl_api_call=true` 不是单独可信的断言。每个 real-device evidence 必须同时包含：

- `backend=ASCEND_HCCL_DIRECT`、`execution_mode=in_process_direct_api`、`direct_hccl_api_call=true`、`real_ascend_npu_validated=true`；
- adapter source revision、binary SHA-256、CMake cache、编译器、完整 link line、`readelf -d` 的 NEEDED/SONAME、`nm -D` 的三原语与 communicator 符号；
- 官方库 canonical realpath、SHA-256、CANN/HCOMM/HCCL 版本/commit/clean 状态；
- adapter 内生成的、按 rank 和单调序号记录的 API trace：`aclInit`、device/context/stream、comm init、alloc/copy、精确 `HcclAllReduce`/`HcclAllGather`/`HcclReduceScatter`、同步、D2H、destroy 的实参摘要与全部返回码；
- 已解析的 dtype/op/count、输入/输出字节、device ids、rank table/root-info digest（不保存秘密）、stream/session 归属；
- `hccl_test_subprocess_invocations=[]` 和进程审计；代码级测试必须证明 direct backend 不导入或调用 `plugin.hccl_vm_runner`，运行记录中不得出现 `hccl_test`、HCCL-VM 或 MPI launcher；
- per-rank 输入种子、host reference、D2H 输出哈希/误差、通过准则、`npu-smi info` 摘要、驱动/固件、拓扑和 profile 摘要；
- 清理 trace 与每个对象的 owner/release 状态。

建议 schema 为 `g2-f-direct-device-v1`，目录为 `experiments/direct_api/evidence/g2_f_<primitive>_<timestamp>/`，含 `manifest.json`、`result.json`、`api_trace.jsonl`、`build_link.json`、`environment.json`、`correctness.json`、`concise.log`、`SHA256SUMS`。只在三个 primitive 都有同一冻结环境、同一 schema、完整 trace 和 `REAL_DEVICE_PASS` 时，才可写 `G2-F Real-device Acceptance: COMPLETED`。

## 6. 统一状态语义

| 状态                    | 精确含义                                                          | 不表示                      |
| ----------------------- | ----------------------------------------------------------------- | --------------------------- |
| `BUILD_ONLY_PASS`       | direct target 在冻结头文件下编译成功                              | 链接、加载、设备调用        |
| `LINK_PASS`             | 直接链接的目标/可执行体解析所需官方库                             | device runtime 或 API 成功  |
| `SYMBOL_DISCOVERY_PASS` | 静态/已证明安全的动态发现看到预期 SONAME/导出符号                 | 签名可运行、comm 成功       |
| `NO_DEVICE_EXPECTED`    | preflight 确认设备/驱动不存在且未尝试实机 API                     | 实现失败或成功              |
| `HARDWARE_BLOCKED`      | 需要真实 Ascend 设备的步骤因无硬件停止                            | `ENV_BLOCKED` 或代码失败    |
| `ENV_BLOCKED`           | CANN root、版本、依赖、权限、rank-table/launcher 或官方环境不满足 | hardware pass               |
| `REAL_DEVICE_PASS`      | 在真实 NPU 上的直接 API、同步、D2H 正确性和证据全部通过           | 其他规模/primitive 自动通过 |
| `FAIL`                  | 前置条件已满足但构建、契约、调用、数据、清理或回归失败            | 可改写为 block 以掩盖缺陷   |

## 7. Checkpoints

每个 checkpoint 仅在新的用户批准实施轮次中进行；“建议 commit”仅是未来粒度，不授权当前创建提交。所有回滚为 `git revert` 单个 checkpoint 的项目提交，绝不删除或重写 evidence，也绝不修改官方仓库。

### G2-F-1：官方 API/ABI 契约冻结

- **目标：** 写入可机读的 CANN 9.1.0 manifest，冻结本计划第 2 节 API、签名、枚举、SONAME、导出符号、路径、哈希与已知未决 buffer 契约。
- **修改文件：** 新增 `docs/direct_api_contract.md`、`cmake/cann_direct_api_manifest.cmake` 或 JSON manifest、契约测试；不改 CPU_SIM/HCCL-VM。
- **非目标：** 不编译 adapter，不加载库，不调用 ACL/HCCL。
- **API 契约：** 三原语、`HcclCommInitClusterInfo`/root-info/Destroy、ACL runtime/device/context/stream/memory/copy/sync；未由头证明的 buffer locality 明确为未决。
- **构建/测试：** `cmake -S hcccl -B /tmp/hccl-g2f-contract -DHCCL_ENABLE_ASCEND_HCCL_DIRECT=OFF`；运行 manifest/header/symbol 一致性测试。
- **当前环境：** 可执行；成功为 `SYMBOL_DISCOVERY_PASS`，配置可为 `BUILD_ONLY_PASS`。
- **完成条件：** 每个候选函数均有头、签名、库、导出符号、参数/所有权/前置条件/清理和环境状态；版本漂移被拒绝。
- **HARDWARE_BLOCKED：** 不适用。
- **ENV_BLOCKED：** CANN root、头、库、符号、依赖解析、HCOMM/HCCL commit 或 clean 状态不符。
- **evidence：** 只读 inventory、`readelf`、`nm`、哈希和 Git metadata，schema `g2-f-readiness-v1`。
- **建议 commit / 回滚：** `G2-F-1 freeze official direct API ABI contract`；revert 该项目提交。

### G2-F-2：build-only 原生 direct adapter

- **目标：** 新增 C++ RAII adapter 与独立 C ABI target，不改变 `hccl_plugin` 的 CPU_SIM ABI。
- **修改文件：** `hcccl/CMakeLists.txt`、`hcccl/direct/include/`、`hcccl/direct/src/`、build-only tests、文档；不改 HCOMM/HCCL/CANN。
- **非目标：** 不加载官方库，不运行 direct adapter，不接入 Agent。
- **API 契约：** 只编译对正式头的静态类型检查；C ABI 的 handle/错误/所有权与 CPU_SIM 分离。
- **构建/测试：** `cmake -S hcccl -B /tmp/hccl-g2f-build -DHCCL_ENABLE_ASCEND_HCCL_DIRECT=ON -DHCCL_CANN_ROOT=/home/workspace/Ascend/cann-9.1.0`；`cmake --build ... --target hccl_direct_adapter`；ABI compile tests。
- **当前环境：** 可执行；完成为 `BUILD_ONLY_PASS`。
- **完成条件：** direct target 使用官方头成功编译，默认 CPU_SIM 构建不带 CANN 依赖。
- **HARDWARE_BLOCKED：** 不适用。
- **ENV_BLOCKED：** CMake/编译器/SDK header 不满足、版本 manifest 不符。
- **evidence：** `compile_commands.json`、CMakeCache 摘要、目标哈希、默认 CPU_SIM link audit。
- **建议 commit / 回滚：** `G2-F-2 add build-only direct HCCL adapter`；revert 该项目提交。

### G2-F-3：正式链接、符号审计与无设备诊断

#### 目标

在不执行任何 ACL runtime、device、communicator 或 collective API 的前提下，将 G2-F-2 的 build-only adapter 推进到可审计的正式链接状态，并建立严格的无设备诊断边界。

本 checkpoint 必须证明：

1. 项目生成的 direct linked artifact 确实依赖冻结的官方库；
2. 链接使用的库全部来自唯一冻结的 CANN 9.1.0 root；
3. ELF `NEEDED`、官方库 `SONAME`、导出符号和传递依赖与 G2-F-1 manifest 一致；
4. 当前环境没有真实 Ascend 设备时，诊断稳定返回 `NO_DEVICE_EXPECTED`；
5. 任何 direct collective 执行请求都在调用 ACL/HCCL runtime 之前被拒绝；
6. CPU_SIM 和 ASCEND_HCCL_VM 的构建、运行和 evidence 语义保持不变。

成功状态只能是：

- `LINK_PASS`
- `SYMBOL_DISCOVERY_PASS`
- `NO_DEVICE_EXPECTED`

这些状态不表示已经加载 runtime、创建 communicator 或执行集合通信。

#### 前置条件

开始前必须确认：

- G2-F-1、G2-F-2 和 evidence 清理提交已进入 `main`；
- 工作区 clean；
- CANN root 为 `/home/workspace/Ascend/cann-9.1.0`；
- CANN/HCCL 版本为 9.1.0；
- HCOMM 为 `competition/campus-2026@c8a3dc68a37315aa1e908a971fa706abe612f6ee`；
- HCCL 为 `competition/campus-2026@2c87cc1937bab23b8574ef24017c03572d3340e2`；
- HCOMM/HCCL tracked worktree clean；
- G2-F-1 manifest 和最终 F1/F2 evidence 的 SHA256 校验仍通过。

任一冻结条件漂移时返回 `ENV_BLOCKED`，不得静默使用其他安装、其他版本或系统同名库。

#### 修改范围

预计修改或新增：

- `hcccl/CMakeLists.txt`
- `hcccl/direct/` 下的链接边界、诊断工具和必要接口
- `plugin/direct_api_backend.py`
- direct link、symbol、diagnose 相关测试
- G2-F-3 readiness evidence
- 必要的项目文档和状态说明

不得修改：

- HCOMM/HCCL/CANN 官方文件；
- CPU_SIM 的公开 ABI 和加载路径；
- G2-E HCCL-VM runner、Checker 和 evidence 语义；
- 已存在的 G2-D/G2-E/G2-F-1/F2 evidence。

#### 正式链接契约

production direct 路径必须直接链接：

- `libhccl.so`
- `libhcomm.so`
- `libacl_rt.so`

链接必须满足：

1. `HCCL_CANN_ROOT` 是唯一 SDK root；
2. 必须使用绝对 canonical path 或受 `NO_DEFAULT_PATH` 限制的精确搜索；
3. 不得从系统默认目录或其他 CANN 安装解析同名库；
4. 必须验证实际 canonical realpath；
5. 必须记录三个库的 SHA256；
6. 必须记录三个库的 `SONAME`；
7. 必须生成至少一个可由 `readelf -d` 和 `ldd` 审计的 linked ELF artifact；
8. 必须保存完整或可复现的 link line；
9. 必须验证 G2-F-1 manifest 要求的三原语、communicator 和 ACL runtime 导出符号；
10. 不得把静态 archive 的生成误写成 `LINK_PASS`。

如果实现保留 G2-F-2 的静态 compile-only target，应额外建立独立 linked artifact；不得删除 build-only 验证能力。

`HCCL_ENABLE_ASCEND_HCCL_DIRECT` 必须继续默认 `OFF`。默认 CPU_SIM configure/build 不得要求 CANN root，也不得产生 ACL/HCCL 依赖。

#### 动态加载边界

实际 `dlopen` 不是本 checkpoint 的强制完成条件。

只有 G2-F-1 合约或该 CANN 版本的官方材料明确证明“仅加载共享库不会初始化 runtime、访问设备或改变系统状态”时，才允许执行动态加载诊断。

缺少该安全证明时：

- 不执行 `dlopen`；
- 输出 `DYNAMIC_LOAD_NOT_EXECUTED`；
- 使用 `readelf`、`nm`、`ldd` 和 manifest 完成静态发现；
- 不因此将 G2-F-3 标记为失败；
- 不允许以试运行方式判断其安全性。

即使执行了安全的动态发现，也不得把它作为 production fallback，更不得把 library load 写成 direct API 调用成功。

#### 无设备诊断契约

新增的 diagnose 必须是纯 preflight，不调用任何 ACL/HCCL runtime 函数。

允许检查：

- CANN root 和版本；
- manifest 一致性；
- 头文件和库文件存在性；
- canonical realpath；
- SHA256；
- `SONAME`；
- ELF `NEEDED`；
- 导出符号；
- `ldd` 传递依赖；
- `npu-smi` 是否存在；
- `/dev` 下 Ascend/Davinci device nodes；
- `/proc`、`/sys/module` 中的只读驱动指示；
- 当前平台和环境变量。

当前环境确认无设备时，结构化结果必须包含：

```text
backend=ASCEND_HCCL_DIRECT
status=NO_DEVICE_EXPECTED
direct_hccl_api_call=false
real_ascend_npu_validated=false
runtime_initialized=false
device_opened=false
communicator_created=false
collective_executed=false
```

无设备不是 `FAIL`，也不是 `LINK_PASS` 本身；链接结果和硬件 preflight 必须分别记录。

#### 执行防线

本 checkpoint 必须保证所有 collective 或 lifecycle 请求在 native runtime 边界之前被拒绝。

禁止实际调用：

- `aclInit`
- `aclFinalize`
- `aclrtSetDevice`
- `aclrtCreateContext`
- `aclrtCreateStream`
- `aclrtMalloc`
- `aclrtMemcpy`
- `HcclGetRootInfo`
- `HcclCommInitRootInfo`
- `HcclCommInitClusterInfo`
- `HcclCommDestroy`
- `HcclAllReduce`
- `HcclAllGather`
- `HcclReduceScatter`

允许在 manifest、函数类型、静态签名检查、symbol inventory 和测试期望中出现这些名称，但不得存在可执行调用路径。

不得运行：

- `hccl_test`
- HCCL-VM
- MPI launcher

来生成 direct evidence。

direct backend 不得导入或调用 `plugin.hccl_vm_runner`。

#### 测试要求

目标测试必须覆盖：

1. feature flag 默认 `OFF`；
2. direct linked artifact 仅使用冻结 CANN root；
3. 缺少 CANN root 时配置明确失败；
4. CANN 版本、库、SONAME、符号或哈希漂移时明确失败；
5. linked ELF 的 `NEEDED` 包含预期官方库；
6. `ldd` 在仅对子 shell 生效的 CANN 环境中完整解析；
7. manifest 中的要求符号均存在；
8. no-device diagnose 返回 `NO_DEVICE_EXPECTED`；
9. diagnose 不调用 runtime；
10. direct collective 请求在 runtime 之前拒绝；
11. Windows 导入相关 Python 模块时不要求本地存在 CANN/WSL；
12. 默认 CPU_SIM configure/build/CTest 不包含 CANN 依赖；
13. G2-E registry、dry-run、parser 和 evidence 回归不变；
14. G2-F-1/F2 evidence SHA256 仍通过；
15. HCOMM/HCCL tracked worktree 仍 clean。

不得删除、弱化测试或增加无理由 skip 来获得通过。

#### Evidence

只保留一份权威的最终 evidence：

```text
experiments/direct_api/evidence/g2_f_3_<timestamp>/
```

至少包含：

- `README.md`
- `manifest.json`
- `result.json`
- `build_link.json`
- `symbol_inventory.json`
- `dependency_audit.json`
- `no_device_diagnose.json`
- `regression.json`
- `SHA256SUMS`

Evidence 必须记录：

- adapter source commit；
- linked artifact SHA256；
- CMake 配置和编译器；
- link line；
- CANN root 和版本；
- 官方库 canonical realpath、SHA256 和 SONAME；
- `readelf -d` 的 `NEEDED`；
- `ldd` 解析结果；
- required/missing symbol 集合；
- 是否执行过 `dlopen` 及其安全依据；
- device/driver/npu-smi preflight；
- `direct_hccl_api_call=false`；
- `real_ascend_npu_validated=false`；
- `runtime_api_calls=[]`；
- CPU_SIM 和 G2-E 回归结果；
- HCOMM/HCCL branch、commit 和 clean 状态。

不得提交多个未说明用途的中间 evidence。失败调试输出保留在临时构建目录，或明确标记为 superseded 后再决定是否入库。

#### 完成条件

只有以下条件全部满足时，G2-F-3 才可标记 `COMPLETED`：

- direct linked artifact 构建成功；
- 实际链接到冻结的三个官方库；
- link line、NEEDED、SONAME、SHA256 和路径全部可审计；
- 传递依赖完整解析；
- required symbols 全部存在；
- no-device diagnose 返回 `NO_DEVICE_EXPECTED`；
- collective 请求在 runtime 前拒绝；
- 未调用任何 ACL/HCCL runtime API；
- CPU_SIM 和 G2-E 无回归；
- evidence SHA256 全部通过；
- HCOMM/HCCL tracked worktree clean；
- 工作区 clean；
- 未 push、未 merge。

最终状态：

```text
G2-F-3: COMPLETED
G2-F Readiness: PARTIAL
G2-F Real-device Acceptance: HARDWARE_BLOCKED
G2-F Overall: PARTIAL
```

#### 阻塞与失败分类

`ENV_BLOCKED`：

- CANN root、版本、头文件或库缺失；
- 官方库路径或 SHA256 漂移；
- SONAME、导出符号或依赖与 manifest 不符；
- HCOMM/HCCL commit 或 clean 状态不符；
- 编译器、CMake、权限或 evidence 路径不满足。

`HARDWARE_BLOCKED`：

- 仅适用于用户要求进入 lifecycle 或真实设备调用，而当前无设备；
- 不影响本 checkpoint 的静态链接、符号和 diagnose 完成。

`FAIL`：

- 前置环境满足但 CMake、链接、审计、诊断、guard、测试或 evidence 实现错误；
- 不得将代码缺陷改写为 `HARDWARE_BLOCKED`。

#### 建议 commit 与回滚

建议 commit：

```text
G2-F-3 add direct API link and no-device diagnostics
```

回滚使用该项目提交的 `git revert`，不得重写历史或删除既有 evidence。

### G2-F-4：受保护的 lifecycle 状态机与资源所有权 harness

#### 目标

在当前没有真实 Ascend NPU 的环境中，完成 `ASCEND_HCCL_DIRECT` 生命周期控制面的工程就绪验证。

本 checkpoint 不执行真实 ACL/HCCL 生命周期，而是通过：

- 显式状态机；
- C++17 RAII 所有权模型；
- 独立 C ABI；
- 参数和容量契约；
- 失败注入；
- 反向清理验证；
- 无设备 guard；
- opt-in 实机入口模板；

证明未来真实设备路径具有明确、可审计、不会越权执行的生命周期框架。

本 checkpoint 验证的是：

```text
lifecycle control-plane readiness
```

不是：

```text
real-device lifecycle execution
```

#### 执行前状态假设与额度控制

进入本 checkpoint 前，用户已经人工确认：

- G2-F-3 已通过 PR 合并进入 `main`；
- 本地 `main` 与 `origin/main` 已同步；
- 工作区 clean；
- G2-F-1/F2/F3 已完成并有有效 evidence。

因此，执行 G2-F-4 时不得重新进行完整 Git 历史审计、PR 审计、所有旧 commit 祖先检查或全量旧 evidence 复核。

开始时只允许进行一次轻量确认：

```text
git branch --show-current
git status --short
```

只需确认：

- 当前分支为 `main`；
- 除本次尚未提交的 G2-F-4 计划细化外无其他修改。

除非实际命令出现矛盾、缺失文件或版本漂移，不得重复扫描历史提交或重新审计 G2-F-1/F2/F3。

HCOMM/HCCL branch、commit 和 tracked worktree clean 只需在最终审计时检查一次。

#### 当前环境边界

当前环境没有：

- `npu-smi`；
- Ascend/Davinci device node；
- 可用 Ascend driver；
- 可分配真实 NPU；
- 获批准的 real-device launcher；
- 可执行的多 rank direct API 环境。

因此：

```text
real lifecycle execution = HARDWARE_BLOCKED
```

这不是代码失败，也不影响本 checkpoint 的状态机、所有权、guard 和失败清理测试。

#### 修改范围

预计修改或新增：

- `hcccl/direct/include/`
- `hcccl/direct/src/`
- direct adapter 的状态机、session 和错误模型
- 必要的独立 C ABI
- lifecycle、guard、容量和失败注入测试
- opt-in real-device harness 使用说明
- G2-F-4 readiness evidence
- 必要的契约和项目状态文档

允许按实际架构调整文件位置，但必须保持：

- CPU_SIM ABI 不变；
- `hccl_plugin` 行为不变；
- `ASCEND_HCCL_VM` 行为不变；
- G2-E evidence 语义不变；
- `ASCEND_HCCL_DIRECT` 独立隔离；
- `HCCL_ENABLE_ASCEND_HCCL_DIRECT` 默认 `OFF`。

不得修改：

- CANN 安装；
- HCOMM/HCCL 官方源码；
- G2-D/G2-E/G2-F-1/F2/F3 已有 evidence；
- CPU_SIM 的公开符号和加载路径。

#### 生命周期状态机

必须建立显式、可查询、不可跳步的 session 状态机。

建议状态至少包括：

```text
CREATED
CONFIGURED
PREFLIGHT_CHECKED
NO_DEVICE_EXPECTED
RUNTIME_READY
DEVICE_READY
CONTEXT_READY
STREAM_READY
COMM_READY
BUFFERS_READY
COLLECTIVE_SUBMITTED
SYNCHRONIZED
COMPLETED
CLEANING
DESTROYED
FAILED
```

当前无设备环境中，实际允许执行的路径只能到：

```text
CREATED
  -> CONFIGURED
  -> PREFLIGHT_CHECKED
  -> NO_DEVICE_EXPECTED
  -> DESTROYED
```

以下状态只能通过纯状态机和所有权测试验证，不得实际进入官方 runtime：

```text
RUNTIME_READY
DEVICE_READY
CONTEXT_READY
STREAM_READY
COMM_READY
BUFFERS_READY
COLLECTIVE_SUBMITTED
SYNCHRONIZED
COMPLETED
```

必须拒绝：

- 跳过前置状态；
- 重复初始化；
- 在错误状态提交 collective；
- 未同步时释放资源；
- destroy 后继续使用 session；
- rank、device 或线程归属不一致；
- 同一 session 同时选择 rank-table 和 root-info；
- 未完成 preflight 时尝试进入 runtime。

无效转换必须返回稳定的项目状态码，并保留当前合法状态。

#### 资源所有权模型

未来 `DirectSession` 必须明确拥有或引用：

- process-scoped runtime lease；
- device id；
- 可选显式 context；
- stream；
- `HcclComm`；
- send device buffer；
- receive device buffer；
- rank 配置；
- primitive、dtype、op 和 count 契约。

当前 checkpoint 不实际取得这些官方资源，但必须冻结其所有权规则。

要求：

1. 每个资源只有一个明确 owner；
2. 未成功取得的资源不得进入清理队列；
3. 已取得资源按反向顺序释放；
4. 不允许 double free、double destroy 或 use-after-destroy；
5. host input/output 的所有权仍属于调用者；
6. device buffer 未来只允许由 adapter 管理；
7. C++ 异常不得穿过 C ABI；
8. session 不得跨 device 或跨未授权线程使用；
9. 首个业务错误必须保留；
10. cleanup 错误单独记录，不得覆盖首个业务错误。

未来真实清理顺序固定为：

```text
synchronize stream
  -> release device buffers
  -> destroy communicator
  -> destroy stream
  -> destroy explicit context（若由本 session 创建）
  -> reset device
  -> release runtime lease
  -> finalize runtime（仅由最后一个合法 lease owner 执行）
```

本 checkpoint 只验证该顺序的逻辑，不执行对应官方 API。

#### Runtime lease 契约

必须建立 process-scoped runtime lease 模型：

- 同一进程内不得由多个 session 独立重复初始化和 finalize runtime；
- 首个未来 session 取得 runtime lease；
- 后续 session 增加引用或被策略拒绝；
- 只有最后一个合法 owner 可以释放最终 lease；
- session 失败不得错误释放其他 session 的 runtime ownership；
- runtime 已 finalize 后不得被旧 session 重用。

当前无设备环境只测试 lease 状态机，不调用 `aclInit` 或 `aclFinalize`。

#### Rank 初始化契约

未来 communicator 初始化支持两种互斥配置：

1. rank-table：
   - 外部 launcher；
   - rank-table 文件；
   - `rank_id`；
   - `rank_size`；
   - 未来调用 `HcclCommInitClusterInfo`。

2. root-info：
   - root rank；
   - root-info 安全分发；
   - `rank_id`；
   - `rank_size`；
   - 未来调用 `HcclGetRootInfo` 和 `HcclCommInitRootInfo`。

本项目首个真实设备路径仍优先：

```text
external launcher + rank-table + HcclCommInitClusterInfo
```

G2-F-4 必须验证：

- 两种模式不能同时设置；
- rank id 必须小于 rank size；
- rank size 必须大于 1；
- rank-table 路径不能为空；
- 不读取或执行未经批准的 launcher；
- 当前无设备时只验证配置，不初始化 communicator。

#### 三原语容量契约

必须以溢出安全的整数运算冻结三原语容量公式。

AllReduce：

```text
input_elements_per_rank  = count
output_elements_per_rank = count
input_bytes_per_rank     = count * dtype_size
output_bytes_per_rank    = count * dtype_size
```

AllGather：

```text
input_elements_per_rank  = send_count
output_elements_per_rank = send_count * rank_size
input_bytes_per_rank     = send_count * dtype_size
output_bytes_per_rank    = send_count * rank_size * dtype_size
```

ReduceScatter：

```text
input_elements_per_rank  = recv_count * rank_size
output_elements_per_rank = recv_count
input_bytes_per_rank     = recv_count * rank_size * dtype_size
output_bytes_per_rank    = recv_count * dtype_size
```

必须拒绝：

- 乘法溢出；
- 超过 `size_t` 或 adapter 上限；
- 无效 dtype；
- AllGather 指定 reduce op；
- AllReduce/ReduceScatter 缺少合法 reduce op；
- rank size 与 buffer 容量不一致；
- null pointer 与非零容量组合；
- 未确认 buffer locality 时传入 host pointer 执行 direct collective。

当前 checkpoint 只计算和验证容量，不分配 device memory。

#### 失败注入模型

失败注入只用于验证项目自身的状态机和所有权逻辑，不得模拟或伪造官方 ACL/HCCL 的真实行为。

允许注入的抽象失败点包括：

- runtime lease acquisition；
- device binding；
- context creation；
- stream creation；
- communicator creation；
- send buffer acquisition；
- receive buffer acquisition；
- collective submission；
- synchronization；
- cleanup 的每一个阶段。

对每个失败点必须验证：

1. session 进入预期失败状态；
2. 只清理此前已经取得所有权的资源；
3. 清理顺序严格反向；
4. 未取得的资源不会被释放；
5. 首个业务错误不会被 cleanup 错误覆盖；
6. cleanup 错误仍完整记录；
7. session 最终不能再次执行 collective；
8. 不发生逻辑资源泄漏；
9. 不产生真实 ACL/HCCL 调用。

这些测试属于 deterministic state-machine tests，不得将其描述为真实驱动故障测试。

#### 无设备 guard

G2-F-4 必须继承 G2-F-3 的纯 preflight diagnose。

当前环境中，任何 lifecycle 或 collective 执行请求都必须在 native runtime 边界之前返回：

```text
NO_DEVICE_EXPECTED
```

或在用户明确请求真实执行但硬件不存在时返回：

```text
HARDWARE_BLOCKED
```

结果必须明确包含：

```text
direct_hccl_api_call=false
real_ascend_npu_validated=false
runtime_initialized=false
device_opened=false
context_created=false
stream_created=false
communicator_created=false
device_buffer_allocated=false
collective_executed=false
runtime_api_calls=[]
```

单独设置环境变量不能绕过 guard。

`HCCL_DIRECT_REAL_DEVICE=1` 只能作为未来 G2-F-5 的 opt-in 模板条件之一，本 checkpoint 不实现真实执行路径。

#### C ABI 要求

在 G2-F-2 独立 ABI 基础上，按实际需要增加最小接口，用于：

- session 创建；
- session 配置；
- preflight；
- 当前状态查询；
- primitive 容量计算；
- guard 结果查询；
- 错误信息查询；
- session 销毁。

不得：

- 暴露 C++ 类型；
- 让异常穿过 C ABI；
- 复用 CPU_SIM 的同名符号伪装 direct backend；
- 让 Python 直接加载或调用官方 ACL/HCCL；
- 在 C ABI 内隐藏真实执行行为；
- 在没有 real-device evidence 时设置 `direct_hccl_api_call=true`。

Python 只能调用项目自己的 direct adapter ABI。

#### 禁止调用

G2-F-4 中禁止实际调用：

- `aclInit`
- `aclFinalize`
- `aclrtSetDevice`
- `aclrtResetDevice`
- `aclrtCreateContext`
- `aclrtDestroyContext`
- `aclrtCreateStream`
- `aclrtSynchronizeStream`
- `aclrtDestroyStream`
- `aclrtMalloc`
- `aclrtFree`
- `aclrtMemcpy`
- `aclrtMemcpyAsync`
- `HcclGetRootInfo`
- `HcclCommInitRootInfo`
- `HcclCommInitClusterInfo`
- `HcclCommDestroy`
- `HcclAllReduce`
- `HcclAllGather`
- `HcclReduceScatter`

允许这些名称出现在：

- manifest；
- 函数类型；
- 静态签名断言；
- 状态机动作名称；
- 测试期望；
- symbol inventory；
- opt-in 文档模板。

但不得存在当前环境可到达的执行路径。

不得使用：

- `hccl_test`
- HCCL-VM
- MPI launcher
- CPU_SIM collective

来伪造 direct lifecycle evidence。

#### 构建与测试

至少覆盖：

1. direct adapter build/link 回归；
2. feature flag 默认 `OFF`；
3. CPU_SIM 默认构建不依赖 CANN；
4. session 合法状态转换；
5. 每一种非法状态转换；
6. runtime lease 引用和释放；
7. rank-table/root-info 互斥配置；
8. rank id/rank size 参数校验；
9. 三原语容量公式；
10. dtype size 映射；
11. 整数溢出和超大容量；
12. 每个资源获取阶段的失败注入；
13. 每个 cleanup 阶段的失败注入；
14. 反向清理顺序；
15. 首个业务错误保留；
16. cleanup 错误附加记录；
17. double destroy 行为；
18. destroy 后使用拒绝；
19. thread/device ownership guard；
20. 无设备 preflight；
21. lifecycle/collective 请求在 runtime 前拒绝；
22. `runtime_api_calls=[]`；
23. C ABI 编译和异常边界；
24. Windows 导入安全；
25. Python 全量回归；
26. CPU_SIM CTest；
27. G2-E registry、dry-run、parser 和 evidence 回归；
28. G2-F-1/F2/F3 evidence SHA256 回归；
29. 最终 HCOMM/HCCL tracked worktree clean。

不得：

- 删除或弱化测试；
- 新增无理由 skip；
- 用 mock runtime 成功替代 guard；
- 把状态机 PASS 描述成真实设备 PASS。

#### Evidence

只保留一份权威最终 evidence：

```text
experiments/direct_api/evidence/g2_f_4_<timestamp>/
```

至少包含：

- `README.md`
- `manifest.json`
- `result.json`
- `state_machine.json`
- `ownership_audit.json`
- `failure_injection.json`
- `capacity_contract.json`
- `guard_audit.json`
- `regression.json`
- `SHA256SUMS`

Evidence 必须记录：

```text
checkpoint=G2-F-4
checkpoint_status=COMPLETED
lifecycle_harness_readiness=COMPLETED
preflight_status=NO_DEVICE_EXPECTED
hardware_lifecycle_status=HARDWARE_BLOCKED
direct_hccl_api_call=false
real_ascend_npu_validated=false
runtime_initialized=false
device_opened=false
context_created=false
stream_created=false
communicator_created=false
device_buffer_allocated=false
collective_executed=false
runtime_api_calls=[]
```

还必须记录：

- adapter source revision；
- state transition coverage；
- invalid transition coverage；
- failure injection 点；
- cleanup 顺序；
- ownership audit；
- 三原语容量测试；
- C ABI 测试；
- CPU_SIM/G2-E/F1-F3 回归；
- HCOMM/HCCL branch、commit 和 clean 状态；
- evidence 文件 SHA256。

不得生成 device-pass、performance 或真实 collective evidence。

#### 完成条件

只有以下条件全部满足时，G2-F-4 才能标记 `COMPLETED`：

- lifecycle 状态机实现并测试通过；
- 所有非法转换均被拒绝；
- runtime lease 模型通过；
- rank 配置契约通过；
- 三原语容量和溢出测试通过；
- 每个资源阶段的失败注入通过；
- 反向清理顺序通过；
- 首个业务错误和 cleanup 错误均被保留；
- C ABI 编译和异常边界通过；
- no-device guard 稳定返回 `NO_DEVICE_EXPECTED`；
- 所有执行请求均在 runtime 前拒绝；
- 未调用任何 ACL/HCCL runtime API；
- `runtime_api_calls=[]`；
- CPU_SIM、G2-E 和 G2-F-1/F2/F3 无回归；
- evidence SHA256 全部通过；
- HCOMM/HCCL tracked worktree clean；
- 工作区 clean；
- 未 push、未 merge；
- 未开始 G2-F-5。

最终状态必须为：

```text
G2-F-4: COMPLETED
Lifecycle Harness Readiness: COMPLETED
G2-F Readiness: PARTIAL
G2-F Real-device Acceptance: HARDWARE_BLOCKED
G2-F Overall: PARTIAL
```

`G2-F Readiness` 在 G2-F-7 完成 Agent 接入和最终审计前保持 `PARTIAL`。

#### 阻塞和失败分类

`HARDWARE_BLOCKED`：

- 请求进入真实 runtime/device/communicator/collective；
- 当前没有真实 NPU、driver、device node 或实机授权。

这不影响 G2-F-4 的状态机完成。

`ENV_BLOCKED`：

- G2-F-3 链接基础、CANN manifest、编译器或必要构建环境失效；
- 必要文件或依赖缺失；
- evidence 无法生成；
- HCOMM/HCCL 冻结状态漂移。

`FAIL`：

- 状态机、所有权、清理、容量、guard、ABI、测试或 evidence 本身存在缺陷；
- 前置环境满足但实现无法通过；
- 不得将代码错误改写为 `HARDWARE_BLOCKED`。

#### 建议 commit 与回滚

建议 commit：

```text
G2-F-4 add guarded direct API lifecycle harness
```

完成该 commit 后必须停止，不得开始 G2-F-5。

回滚使用该项目提交的 `git revert`，不得重写历史、删除旧 evidence 或修改官方仓库。

### G2-F-5：模拟器三原语数据正确性验收（真实设备验收保持 HARDWARE_BLOCKED）

#### 目标

在当前没有真实 Ascend NPU 的条件下，建立可追溯、可复现、具备独立正确性基准的模拟器三原语验收流程，验证：

- AllReduce；
- AllGather；
- ReduceScatter；

在不同 rank 数、数据类型、归约操作、消息规模和模拟拓扑下的数据语义与结果正确性。

本 checkpoint 属于：

```text
SIMULATOR CORRECTNESS ACCEPTANCE
```

不是：

```text
REAL-DEVICE DIRECT API ACCEPTANCE
```

不得将 CPU_SIM、分析 simulator、已有 HCCL-VM 或 host reference 的结果描述为真实 NPU direct API 执行结果。

真实设备 direct API 验收继续保持：

```text
G2-F Real-device Acceptance: HARDWARE_BLOCKED
```

#### 执行前状态与额度控制

进入本 checkpoint 前，用户已经人工确认：

- G2-F-4 已通过 PR 合并进入 `main`；
- 本地 `main` 与 `origin/main` 已同步；
- 工作区除尚未提交的 G2-F-5 计划细化外无其他修改；
- G2-F-1 至 G2-F-4 已完成。

执行开始时只允许进行一次轻量确认：

```text
git branch --show-current
git status --short
```

只需确认：

- 当前分支为 `main`；
- 除 G2-F-5 计划细化外没有其他未提交修改。

除非实际发现文件缺失、版本矛盾或构建失败，不得重复进行完整 Git 历史审计、旧 PR 审计或全部旧 checkpoint 人工复核。

#### 验证轨道隔离

项目必须明确区分以下轨道：

```text
CPU_SIM
ASCEND_HCCL_VM
ASCEND_HCCL_DIRECT
SIMULATOR_ACCEPTANCE
```

本 checkpoint 使用：

```text
SIMULATOR_ACCEPTANCE
```

并可调用项目已有 CPU_SIM 或分析 simulator 作为执行引擎和交叉验证对象。

不得：

- 将 CPU_SIM 重命名或伪装为 `ASCEND_HCCL_DIRECT`；
- 通过 direct adapter C ABI 声称执行了真实 collective；
- 修改 G2-E 的 HCCL-VM evidence；
- 用已有 HCCL-VM 结果生成 direct API evidence；
- 设置 `direct_hccl_api_call=true`；
- 设置 `real_ascend_npu_validated=true`；
- 生成 `REAL_DEVICE_PASS`。

#### 修改范围

允许按项目现有架构新增或修改：

- simulator correctness harness；
- 三原语输入生成和 host reference；
- dtype 编解码和误差统计；
- rank/topology/message-size 测试矩阵；
- 大消息分块或流式验证；
- simulator backend 适配；
- correctness evidence writer；
- Python contract tests；
- 必要的 CPU_SIM 隔离回归；
- 使用说明和结果报告；
- G2-F-5 simulator evidence。

不得改变：

- CPU_SIM 已有公开 ABI 和默认语义；
- G2-E subprocess、parser、checker 和 evidence 语义；
- direct adapter lifecycle 状态机的安全边界；
- `HCCL_ENABLE_ASCEND_HCCL_DIRECT` 默认 `OFF`；
- HCOMM、HCCL 和 CANN 官方文件；
- G2-D、G2-E、G2-F-1 至 G2-F-4 的既有 evidence。

#### 三原语数据语义

AllReduce：

```text
每个 rank 输入 count 个元素
所有 rank 对相同位置执行指定 reduce op
每个 rank 输出 count 个相同归约结果
```

AllGather：

```text
每个 rank 输入 send_count 个元素
每个 rank 输出 rank_size * send_count 个元素
输出按 rank 顺序拼接
AllGather 不接受 reduce op
```

ReduceScatter：

```text
每个 rank 输入 rank_size * recv_count 个元素
先对所有 rank 的完整输入执行逐元素归约
再按 rank 顺序切分
每个 rank 输出 recv_count 个元素
```

必须显式记录：

- primitive；
- rank size；
- rank id；
- count、send_count 或 recv_count；
- dtype；
- reduce op；
- 每 rank 输入元素数；
- 每 rank 输出元素数；
- 输入字节数；
- 输出字节数；
- rank 拼接或切分顺序；
- topology；
- message size；
- random seed。

#### 独立 Host Reference

必须实现与被测算法逻辑隔离的独立 host reference。

Host reference 不得：

- 调用被测算法；
- 复用被测算法的通信步骤；
- 复用被测算法的 rank 调度；
- 仅检查 shape 或 checksum 而不检查实际数值；
- 只比较总和而忽略元素顺序。

每个 primitive 必须比较：

- 每个 rank 的完整输出；
- 元素数量；
- dtype；
- rank 顺序；
- 最大绝对误差；
- 最大相对误差；
- NaN/Inf；
- output hash。

整数数据要求逐元素完全一致。

浮点数据必须同时提供：

1. **精确可表示验收数据集**
   - 输入和值选择为目标 dtype 可精确表示；
   - 用于验证赛题要求的严格数值一致性；
   - 要求零误差或明确记录是否满足 `1e-6`。

2. **随机压力数据集**
   - 用于观察 FP16、BF16、FP32 累积误差；
   - 记录 dtype-aware absolute/relative tolerance；
   - 不得将放宽后的压力阈值冒充赛题严格精度结论。

#### 数据类型与归约操作

至少覆盖：

```text
FP32
FP16
BF16
INT32
```

AllReduce 和 ReduceScatter 至少覆盖：

```text
SUM
MAX
MIN
```

AllGather 不允许 reduce op。

如果当前底层模拟器缺少 BF16 原生存储，允许实现项目内明确、可测试的 BF16 编码、舍入和解码逻辑，但必须：

- 记录舍入方式；
- 测试边界值；
- 测试正负数；
- 测试零、subnormal、最大有限值；
- 不依赖真实 NPU 行为；
- 不宣称与 Ascend 硬件内部累加路径完全一致。

#### Rank 与规模矩阵

至少覆盖代表性 rank 数：

```text
2
4
8
16
64
```

其中：

- 8 ranks 对应单机多卡模拟场景；
- 64 ranks 对应多机多卡模拟场景；
- 不要求默认 CI 为所有 dtype、op、size、topology 做全笛卡尔积；
- 应采用明确、可审计的代表性矩阵或 pairwise coverage；
- 每一种 primitive、dtype、reduce op 和关键 rank 数必须至少被有效覆盖一次。

必须额外覆盖：

- rank size 非法；
- rank id 越界；
- 空输入；
- 单元素输入；
- 非整齐分块；
- count 乘法溢出；
- buffer 大小不一致；
- rank 顺序错误；
- 重复或缺失 rank 输入。

#### 消息规模

至少覆盖：

```text
1 element
1 KB
64 KB
1 MB
16 MB
logical >= 1 GB
```

`logical >= 1 GB` 场景不得要求在普通 CI 中为每个 rank 实际分配完整 1 GB 内存。

允许使用：

- chunked execution；
- streaming reference；
- incremental hash；
- 分块逐元素或逐窗口验证；
- 可配置 opt-in 大内存模式。

Evidence 必须分别记录：

```text
logical_message_bytes
materialized_message_bytes
chunk_bytes
chunk_count
full_or_sampled_validation
```

不得将逻辑大消息测试描述为真实 NPU 的 1 GB 性能测量。

#### 拓扑与场景

正确性测试至少覆盖项目中已有的代表性模拟拓扑：

- Full Mesh；
- Ring；
- hierarchical / Fat-Tree；
- heterogeneous / asymmetric-link scenario。

正确性结果原则上不应因拓扑变化而改变；拓扑只允许影响：

- 调度顺序；
- 路径；
- 分块策略；
- 模拟时延或带宽；
- 故障路由。

如果同一输入在不同拓扑得到不同数值结果，应标记为 `FAIL`，不得解释为性能差异。

#### 确定性与可复现性

每个用例必须记录：

- 固定 random seed；
- 输入生成规则；
- simulator 配置；
- topology 配置；
- dtype/op；
- rank count；
- message bytes；
- host reference revision；
- 项目 commit；
- output hash。

同一 commit、配置和 seed 重复执行必须得到相同：

- 测试状态；
- output hash；
- 错误统计；
- evidence schema。

不得使用未记录的随机源。

#### 跨后端交叉验证

在语义兼容的测试子集上，应比较：

```text
SIMULATOR_ACCEPTANCE
CPU_SIM
independent host reference
```

已有 G2-E HCCL-VM 结果可以作为受支持子集的历史交叉验证依据，但只能：

- 读取既有 summary/evidence；
- 验证 registry、parser 和 evidence 未回归；
- 对比相同 primitive 的语义字段。

不得：

- 重写 G2-E evidence；
- 将 HCCL-VM 结果并入 direct evidence；
- 声称 HCCL-VM 等同真实 NPU direct API；
- 使用 `hccl_test` 生成本 checkpoint 的主要正确性证据。

#### 模拟参数与数据支撑说明

Evidence 必须明确区分：

1. 数据正确性参数：
   - 输入数据；
   - dtype；
   - op；
   - rank；
   - host reference；
   - 误差阈值。

2. 性能模型参数：
   - 带宽；
   - 延迟；
   - 拥塞；
   - 拓扑链路；
   - 协议开销。

本 checkpoint 只验收数据正确性，不验收真实性能。

若性能参数未经过真实 Ascend 集群校准，必须记录：

```text
real_device_calibration_status=UNAVAILABLE_NO_REAL_DEVICE
performance_claim=false
measured_on_real_npu=false
```

不得用模拟器内部公式的输出证明：

- 实际 HCCS/RoCE/PCIe 带宽；
- 真实 p50/p95 延迟；
- 实际线性加速比；
- 真实 NPU 利用率；
- 真实通信计算重叠率。

#### Direct API 安全边界

本 checkpoint 不执行任何真实 ACL/HCCL API。

不得调用：

- `aclInit`
- `aclFinalize`
- device/context/stream API
- device memory allocation/copy API
- communicator init/destroy API
- `HcclAllReduce`
- `HcclAllGather`
- `HcclReduceScatter`
- `dlopen` 或 Python `ctypes.CDLL` 加载官方 runtime
- MPI real-device launcher
- `hccl_test`

结果必须保持：

```text
direct_hccl_api_call=false
real_ascend_npu_validated=false
runtime_initialized=false
device_opened=false
context_created=false
stream_created=false
communicator_created=false
device_buffer_allocated=false
collective_executed=false
runtime_api_calls=[]
```

G2-F-4 的 lifecycle harness 只做隔离回归，不用于执行本 checkpoint 的模拟 collective。

#### 构建与测试

至少覆盖：

1. 三原语独立 host reference；
2. 三原语基本正确性；
3. FP32、FP16、BF16、INT32；
4. SUM、MAX、MIN；
5. 2/4/8/16/64 ranks 的代表性覆盖；
6. small、medium 和 logical large message；
7. Full Mesh、Ring、hierarchical、heterogeneous 场景；
8. rank 顺序和切分；
9. buffer 容量；
10. overflow；
11. NaN/Inf 检查；
12. deterministic seed；
13. output hash；
14. 不同拓扑结果一致性；
15. CPU_SIM 交叉验证；
16. Windows 导入安全；
17. Python 全量回归；
18. CPU_SIM CTest；
19. G2-F-4 host-only lifecycle CTest；
20. G2-E registry/parser/evidence regression；
21. direct build/link/guard regression；
22. 最终 HCOMM/HCCL tracked worktree clean。

不得：

- 删除或弱化已有测试；
- 新增无理由 skip；
- 将错误结果标记为近似通过；
- 以 simulator performance score 替代数据正确性；
- 将测试矩阵缺失归类为硬件阻塞。

#### Evidence

只保留一份权威最终 evidence：

```text
experiments/simulator/evidence/g2_f_5_simulator_<timestamp>/
```

至少包含：

- `README.md`
- `manifest.json`
- `result.json`
- `test_matrix.json`
- `allreduce_correctness.json`
- `allgather_correctness.json`
- `reducescatter_correctness.json`
- `precision_audit.json`
- `large_message_audit.json`
- `cross_backend_audit.json`
- `simulation_assumptions.json`
- `regression.json`
- `SHA256SUMS`

Evidence 必须记录：

```text
checkpoint=G2-F-5
validation_track=SIMULATOR_ACCEPTANCE
checkpoint_status=COMPLETED
simulator_correctness_status=SIMULATOR_CORRECTNESS_PASS
real_device_acceptance=HARDWARE_BLOCKED
real_device_calibration_status=UNAVAILABLE_NO_REAL_DEVICE
performance_claim=false
measured_on_real_npu=false
direct_hccl_api_call=false
real_ascend_npu_validated=false
collective_executed_on_real_device=false
runtime_api_calls=[]
```

还必须记录：

- 三原语结果；
- rank 和消息规模矩阵；
- dtype/op 覆盖；
- host reference；
- error metrics；
- output hashes；
- random seeds；
- simulator 配置；
- topology 配置；
- logical large-message 策略；
- CPU_SIM 交叉验证；
- 已知模拟局限；
- 未经实机校准的参数；
- 测试和回归结果；
- 项目 revision；
- evidence SHA256。

不得在此目录生成：

```text
REAL_DEVICE_PASS
direct_hccl_api_call=true
real_ascend_npu_validated=true
```

#### 完成条件

只有以下条件全部满足时，本 checkpoint 才可标记 `COMPLETED`：

- AllReduce 模拟正确性通过；
- AllGather 模拟正确性通过；
- ReduceScatter 模拟正确性通过；
- 每个 primitive 均与独立 host reference 比较；
- FP32、FP16、BF16、INT32 均有有效覆盖；
- SUM、MAX、MIN 均有有效覆盖；
- 8-rank 和 64-rank 模拟场景通过；
- small、medium 和 logical large-message 场景通过；
- 不同拓扑不会改变正确性；
- deterministic replay 通过；
- output hash 和 error metrics 完整；
- CPU_SIM 交叉验证通过；
- 无真实 ACL/HCCL runtime 调用；
- direct 相关真实性字段全部为 false；
- ordinary regression 无回归；
- evidence SHA256 全部通过；
- HCOMM/HCCL tracked worktree clean；
- 工作区 clean；
- 未 push、未 merge；
- 未开始 G2-F-6。

最终状态必须为：

```text
G2-F-5 Simulator Correctness: COMPLETED
Simulator Correctness Acceptance: COMPLETED
Competition Simulator Track: PARTIAL
G2-F Readiness: PARTIAL
G2-F Real-device Acceptance: HARDWARE_BLOCKED
G2-F Overall: PARTIAL
```

`Competition Simulator Track` 在 G2-F-6 的模拟性能、规模和可靠性评估以及 G2-F-7 最终集成完成前保持 `PARTIAL`。

#### 阻塞与失败分类

`HARDWARE_BLOCKED`：

- 仅用于真实 NPU direct API 验收；
- 不影响当前模拟器正确性 checkpoint 完成。

`ENV_BLOCKED`：

- 项目构建环境、Python/CMake 依赖、必要配置或已有 simulator 无法正常运行；
- 必须保留原始错误和恢复命令。

`FAIL`：

- 三原语结果错误；
- host reference 不独立；
- dtype/op/rank/message 覆盖不满足；
- 不同拓扑产生不一致结果；
- evidence 不完整；
- 测试或代码缺陷。

不得将模拟器实现错误、测试缺失或错误结果标记为 `HARDWARE_BLOCKED`。

#### 建议 commit 与回滚

建议 commit：

```text
G2-F-5 add simulator collective correctness acceptance
```

完成该 commit 后必须停止，不得开始 G2-F-6。

回滚使用该项目提交的 `git revert`，不得重写历史、删除已有 evidence 或修改官方仓库。

### G2-F-6：真实设备拓扑、性能、规模与可靠性

- **目标：** 在 G2-F-5 的正确性基线上收集拓扑、延迟/带宽、多设备/多节点规模和可控故障恢复证据。
- **修改文件：** opt-in benchmark/topology/reliability harness、evidence/report schema、阈值策略；不替换任何 G2-E evidence。
- **非目标：** 不把分析 simulator 分数写成测量结果；不通过伪设备或 hccl_test 补数据。
- **API 契约：** 仅复用 G2-F-5 已验 direct API；每项拓扑/故障 API 的可用性另行从实际头/符号冻结。
- **构建/测试：** opt-in real-device commands，默认 CI 只做 schema/parser 测试。
- **当前环境：** `HARDWARE_BLOCKED`。
- **完成条件：** 每个规模点具备硬件拓扑、直接调用 trace、重复统计、性能单位、故障/恢复行为和 cleanup 证据；不满足即局部 `FAIL` 或 block。
- **HARDWARE_BLOCKED：** 无足够 NPU/跨节点网络或无批准的故障演练窗口。
- **ENV_BLOCKED：** 集群调度、rank-table/network、权限、profiling 工具或一致性环境不满足。
- **evidence：** schema 扩展记录 device topology、message bytes、warm-up、iteration、p50/p95、带宽算法、恢复 trace；不得覆盖 G2-F-5 原始 evidence。
- **建议 commit / 回滚：** `G2-F-6 add direct device scale and reliability evidence`；revert 项目代码，保留 evidence。

### G2-F-7：Agent 接入、全量回归和最终审计

- **目标：** 在明确 opt-in 下将 Agent 选择到 `ASCEND_HCCL_DIRECT`，完成三后端隔离回归与最终可审计报告。
- **修改文件：** `main.py`、backend selection/报告模块、direct backend tests、文档；不得把 CPU_SIM 默认值或 HCCL-VM 行为改成 direct。
- **非目标：** 不扩大三原语以外范围，不重跑/重写 G2-E 作为 direct evidence。
- **API 契约：** Python 只调用独立 adapter C ABI；`direct_hccl_api_call=true` 只能由 native real-device result 设置，非 direct backend 固定 false。
- **构建/测试：** 普通 CI：Python 全量、CPU_SIM CTest、G2-E dry-run/parser/evidence regression、direct build/link/symbol tests；opt-in CI：G2-F-5/6 实机 suite。
- **当前环境：** 普通回归可执行；direct acceptance `HARDWARE_BLOCKED`。
- **完成条件：** CPU_SIM 默认和 G2-E subprocess 合约均无回归；direct 仅在真实 evidence 完整时可用；报告按 backend 隔离汇总。
- **HARDWARE_BLOCKED：** 实机 suite 无设备/环境。
- **ENV_BLOCKED：** ordinary CI 依赖、CANN manifest、官方环境或 evidence 完整性不足。
- **evidence：** 三后端分别出具 summaries；最终审计只有 G2-F Readiness 与 Real-device Acceptance 都满足时才将全 G2-F 标记完成。
- **建议 commit / 回滚：** `G2-F-7 integrate audited direct backend`；revert 项目提交，保留 evidence。

## 8. CI、回归与官方目录保护

普通 CI 仅包括 Python unit tests、CPU_SIM CTest、`ASCEND_HCCL_DIRECT` build/link/symbol/diagnose tests、以及 G2-E parser/dry-run/evidence regression。real-device lifecycle、correctness、benchmark、topology 和 fault tests 必须通过明确环境开关、受控 runner 和专用硬件池 opt-in；缺硬件返回 `HARDWARE_BLOCKED`，不得 skip 后伪装为 pass。

每个 checkpoint 前后都检查官方 repo 的 branch/commit/`status --short`，仅使用：

```text
git -c safe.directory=/home/workspace/hcomm -C /home/workspace/hcomm ...
git -c safe.directory=/home/workspace/hccl -C /home/workspace/hccl ...
```

不 checkout/reset/rebuild 官方仓库；不修改 CANN、驱动、固件、全局 Git 配置或 remote。所有构建在项目外临时 build 目录进行；所有 runtime 证据只写入本仓库新增的 direct evidence 目录。

## 9. 实机阶段最低条件与待用户确认项

**最低条件：** 受支持的真实 Ascend NPU（最少两个可分配逻辑 device 或等效的多-rank 官方部署方式）、匹配驱动/固件、CANN 9.1.0 与本计划冻结的 `libhccl/libhcomm/libacl_rt`、可访问的 device nodes、可执行的 `npu-smi`、干净且固定的 HCOMM/HCCL checkout、已批准的 rank-table 或 root-info launcher、可写 project evidence 目录、足够的进程/网络权限。多节点性能和恢复还要求统一 CANN/驱动、时间同步、连通网络及受控故障窗口。

开始实现前需要用户确认：

1. 接受推荐的 **C++17 内部 + 独立 C ABI**，而不是扩展现有 CPU_SIM ABI；
2. 接受 production **直接链接** 官方库，`dlopen` 仅限诊断；
3. 接受 `ASCEND_HCCL_DIRECT` 与 `HCCL_ENABLE_ASCEND_HCCL_DIRECT=OFF` 的默认隔离；
4. 首个实机 communicator 采用 rank-table 还是 root-info，以及谁提供/启动多 rank；
5. 允许的首批 device 型号、rank 数、dtype/op 测试矩阵和可接受误差；
6. 是否授权在具备条件的实机环境执行 G2-F-5 及之后的 opt-in 调用。

## 10. 启动判断

当前适合立即启动 **G2-F Readiness**，因为官方头文件、库、SONAME、符号和依赖解析均已定位且 CPU_SIM/G2-E 边界清晰。当前不适合启动或宣称完成 **G2-F Real-device Acceptance**：它处于 `HARDWARE_BLOCKED`，直到满足第 9 节的真实设备与多-rank 条件。
