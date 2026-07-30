# G2-F：官方 HCCL/HCOMM 直接 API 集成与真实设备验证就绪计划

## 0. 本计划的结论、范围和起始审计

本计划把 G2-F 明确拆为两个不可互相替代的交付：

- **G2-F Readiness**：在当前无 NPU 的环境完成 API/ABI 冻结、可构建及可链接的原生 adapter、诊断、无 mock 的单元测试和现有后端回归。
- **G2-F Real-device Acceptance**：仅在真实 Ascend NPU 上完成 communicator、stream、device buffer 和三种集合通信的直接调用、数据正确性、性能、规模与可靠性证据。

本轮开始时已只读确认：

| 检查 | 结果 |
| --- | --- |
| 当前分支 | `main` |
| `main` / `origin/main` | 同为 `bd3b91fb072d99b6135ba1ca0529926dd1b20dec` |
| 工作区 | clean（创建本计划前） |
| G2-E | 已在 `main`；`b9438c6` 是 `main` 的祖先 |
| 旧功能分支 | 未在 G2-D/G2-E 分支工作 |

本计划只定义未来工作；不修改业务实现、不会重写 G2-D/G2-E evidence，也不把 HCCL-VM 或 CPU_SIM 的结果表述为 direct API 或真实设备结果。

## 1. 当前架构与不可混淆边界

当前有三条不同的路径，必须继续独立命名、独立测试、独立出证：

| 路径 | 当前入口/实现 | 可以证明 | 绝不能证明 |
| --- | --- | --- | --- |
| `CPU_SIM` | `hcccl/` 的项目自有 C ABI，`plugin/hccl_bridge.py` ctypes，`plugin/execution_engine.py` | CPU 内存布局、FP32/FP16/BF16 模拟结果和项目回归 | CANN/HCCL ABI、NPU 通信、性能 |
| `ASCEND_HCCL_VM` | `main.py` → `plugin/hccl_vm_backend.py` → 官方 `hccl_test` subprocess | 官方 HCCL-VM 的固定 2-rank INT32 checker 合约 | 本进程直接 HCCL 调用或真实 NPU |
| **未来 `ASCEND_HCCL_DIRECT`** | 新的独立 native direct adapter → `libhccl.so` / `libhcomm.so` / ACL runtime | 编译与运行的进程直接调用正式导出 API | 除非有实机 evidence，否则不宣称设备成功 |

G2-E 汇总 evidence 已固定 `execution_mode=subprocess_hccl_test`、`direct_hccl_api_call=false`、`real_ascend_npu_validated=false`。G2-F 不得改写这些字段，也不得复用其 `COMPLETED` 作为 direct API 完成依据。

当前 `hcccl/CMakeLists.txt` 的 `ASCEND_CANN` 只是 `STUB_UNVERIFIED` 的探测/链接边界；`plugin/hccl_api.py` 的同名 Python 函数仍是 simulator/CPU_SIM 兼容层。因此两者均不得被重命名为 direct API 实现。

## 2. 实际发现的官方安装、仓库与 ABI

### 2.1 安装与源码固定点

| 项目 | 实际发现 |
| --- | --- |
| CANN root | `/home/workspace/Ascend/cann-9.1.0` |
| 公开 include / lib64 | `include -> x86_64-linux/include`、`lib64 -> x86_64-linux/lib64` |
| CANN/HCCL 版本 | `9.1.0`（`version/hccl_version.h` 的 `HCCL_VERSION_STR`） |
| 环境脚本 | `/home/workspace/Ascend/cann-9.1.0/set_env.sh`；只在子 shell 中设置 `LD_LIBRARY_PATH`、`ASCEND_HOME_PATH` 等 |
| HCOMM | `competition/campus-2026@c8a3dc68a37315aa1e908a971fa706abe612f6ee`，tracked worktree clean |
| HCCL | `competition/campus-2026@2c87cc1937bab23b8574ef24017c03572d3340e2`，tracked worktree clean |

公开候选头文件是 `hccl/hccl.h`、`hccl/hccl_comm.h`、`hccl/hccl_types.h`、`acl/acl.h`、`acl/acl_rt.h`。`hcomm/hcomm_primitives.h` 等也存在，但本计划的 host-side collective ABI 以安装包中上述 `hccl/` 公开头为准；不得直接依赖 HCOMM 私有源码头。

| 库 | 路径 | SONAME | 关键依赖/用途 |
| --- | --- | --- |
| HCCL facade | `.../x86_64-linux/lib64/libhccl.so` | `libhccl.so` | 依赖 `libhcomm.so`、`libhccl_compat.so`、`libacl_rt.so`；导出三种集合通信 |
| HCOMM | `.../x86_64-linux/lib64/libhcomm.so` | `libhcomm.so` | 依赖 `libhccl_alg.so`、`libhccl_plf.so`、`libhccl_v2.so`、`libacl_rt.so`；导出 communicator/root-info 管理 |
| ACL runtime | `.../x86_64-linux/lib64/libacl_rt.so` | `libacl_rt.so` | 依赖 `libruntime.so` 等；导出 runtime、device、stream、内存 API |

没有执行中的 toolkit 环境时，`ldd` 不会从系统缓存解析这些库；在**仅影响子 shell 环境**地 `source set_env.sh` 后，三者依赖均解析到该 CANN root。这是依赖解析结果，不是 `dlopen`、`aclInit` 或设备调用成功。

### 2.2 已确认的正式直接调用链

下面的名称、签名和符号均来自实际安装头文件和 `nm -D --defined-only`；没有由记忆推测。

| 阶段 | 正式 API（精确签名） | 头文件 | 导出库/符号 | 合约与前置条件 |
| --- | --- | --- | --- | --- |
| runtime | `aclError aclInit(const char *configPath)` / `aclError aclFinalize()` | `acl/acl_rt.h` | `libacl_rt.so`，均为 `T` | 每进程 `aclInit` 仅一次；退出前 `aclFinalize`；是否可在无设备环境调用尚未由头文件证明为无副作用 |
| device/context | `aclrtSetDevice(int32_t)`，`aclrtCreateContext(aclrtContext *, int32_t)`，`aclrtDestroyContext(aclrtContext)`，`aclrtResetDevice(int32_t)` | `acl/acl_rt.h` | `libacl_rt.so`，均为 `T` | `SetDevice` 可隐式创建默认 context；显式 context 只能销毁自己创建的对象；这些都是实机步骤 |
| stream | `aclrtCreateStream(aclrtStream *)`，`aclrtSynchronizeStream(aclrtStream)`，`aclrtDestroyStream(aclrtStream)` | `acl/acl_rt.h` | `libacl_rt.so`，均为 `T` | 销毁前必须同步；stream 是三原语的最后一个参数 |
| device memory | `aclrtMalloc(void **, size_t, aclrtMemMallocPolicy)`，`aclrtFree(void *)` | `acl/acl_rt.h` | `libacl_rt.so`，均为 `T` | `aclrtMalloc` 返回 device memory；只能由 `aclrtFree` 释放 |
| transfer | `aclrtMemcpy(void *, size_t, const void *, size_t, aclrtMemcpyKind)`；`aclrtMemcpyAsync(..., aclrtMemcpyKind, aclrtStream)` | `acl/acl_rt.h` | `libacl_rt.so`，均为 `T` | count 是字节；异步拷贝需 stream 同步；使用 `ACL_MEMCPY_HOST_TO_DEVICE` / `ACL_MEMCPY_DEVICE_TO_HOST` |
| rank-table comm | `HcclCommInitClusterInfo(const char *, uint32_t, HcclComm *)` | `hccl/hccl_comm.h` | `libhcomm.so`，`W` | `clusterInfo` 是含文件名的路径，rank 为当前 rank；返回的 `HcclComm` 由调用方销毁 |
| root-info comm | `HcclGetRootInfo(HcclRootInfo *)`；`HcclCommInitRootInfo(uint32_t, const HcclRootInfo *, uint32_t, HcclComm *)` | `hccl/hccl_comm.h` | `libhcomm.so`，`W` | `HcclRootInfo` 长度为 4108 字节；root-info 的进程间分发、rank 启动和超时策略必须在 G2-F-1 冻结 |
| comm destroy/error | `HcclCommDestroy(HcclComm)`；`const char *HcclGetErrorString(HcclResult)` | `hccl/hccl_comm.h` | `libhcomm.so`，`W` | 先完成/同步使用，再销毁 comm；保留原始 `HcclResult` 与字符串 |
| AllReduce | `HcclAllReduce(void *, void *, uint64_t count, HcclDataType, HcclReduceOp, HcclComm, aclrtStream)` | `hccl/hccl.h` | `libhccl.so`，`T` | count 是输出元素数；dtype 支持列表含 FP16/FP32/FP64/BFP16 和整型；op 为 SUM/PROD/MAX/MIN |
| AllGather | `HcclAllGather(void *, void *, uint64_t sendCount, HcclDataType, HcclComm, aclrtStream)` | `hccl/hccl.h` | `libhccl.so`，`T` | sendCount 是每 rank 输入元素数；输出容量必须按 world size 计算 |
| ReduceScatter | `HcclReduceScatter(void *, void *, uint64_t recvCount, HcclDataType, HcclReduceOp, HcclComm, aclrtStream)` | `hccl/hccl.h` | `libhccl.so`，`T` | recvCount 是每 rank 输出元素数；输入容量必须按 world size 计算 |

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

| 状态 | 精确含义 | 不表示 |
| --- | --- | --- |
| `BUILD_ONLY_PASS` | direct target 在冻结头文件下编译成功 | 链接、加载、设备调用 |
| `LINK_PASS` | 直接链接的目标/可执行体解析所需官方库 | device runtime 或 API 成功 |
| `SYMBOL_DISCOVERY_PASS` | 静态/已证明安全的动态发现看到预期 SONAME/导出符号 | 签名可运行、comm 成功 |
| `NO_DEVICE_EXPECTED` | preflight 确认设备/驱动不存在且未尝试实机 API | 实现失败或成功 |
| `HARDWARE_BLOCKED` | 需要真实 Ascend 设备的步骤因无硬件停止 | `ENV_BLOCKED` 或代码失败 |
| `ENV_BLOCKED` | CANN root、版本、依赖、权限、rank-table/launcher 或官方环境不满足 | hardware pass |
| `REAL_DEVICE_PASS` | 在真实 NPU 上的直接 API、同步、D2H 正确性和证据全部通过 | 其他规模/primitive 自动通过 |
| `FAIL` | 前置条件已满足但构建、契约、调用、数据、清理或回归失败 | 可改写为 block 以掩盖缺陷 |

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

### G2-F-3：链接、动态发现和无设备诊断

- **目标：** 验证 direct link line、SONAME/导出符号和严格的 `NO_DEVICE_EXPECTED` diagnose。
- **修改文件：** direct CMake link 逻辑、`hccl_direct_diagnose`、`plugin/direct_api_backend.py` 的纯诊断边界、单元测试。
- **非目标：** 不调用 `aclInit`，不 `dlopen` 除非 G2-F-1 已提供无设备安全证明；不创建 NPU 对象。
- **API 契约：** `libhccl.so` 三原语为 `T`，`libhcomm.so` communicator API 为 `W`，`libacl_rt.so` lifecycle API 为 `T`；动态加载仅可做 discovery，不能变为 fallback。
- **构建/测试：** 构建 direct target；`readelf -d`、`nm -D`、经子 shell `source set_env.sh; ldd`；运行不触发 runtime 的 diagnose tests。
- **当前环境：** 静态验证可执行；结果为 `LINK_PASS` + `SYMBOL_DISCOVERY_PASS` + `NO_DEVICE_EXPECTED`。
- **完成条件：** 依赖全解析且 diagnose 明确无设备；任何试图执行 direct collective 的调用在 native 边界前拒绝。
- **HARDWARE_BLOCKED：** 不适用到静态步骤；若用户请求 lifecycle harness，报告 `HARDWARE_BLOCKED`。
- **ENV_BLOCKED：** 未 source 环境导致依赖未解析、SONAME/symbol/version 漂移、无安全契约的 library-load 请求。
- **evidence：** ELF/linker 报告、环境差异、诊断 JSON；没有 `direct_hccl_api_call=true`。
- **建议 commit / 回滚：** `G2-F-3 add direct API link and no-device diagnostics`；revert 该项目提交。

### G2-F-4：lifecycle harness 边界

- **目标：** 以状态机、RAII 和失败注入测试实现 communicator/stream/buffer 生命周期 harness；当前仅运行已证明安全的 preflight 边界。
- **修改文件：** direct adapter session/state machine、C ABI、错误映射、无 mock 单元测试、opt-in harness 文档。
- **非目标：** 无 NPU 时不执行 `aclInit`、device/context/stream/comm/allocation/collective；不使用 hccl_test。
- **API 契约：** 固定第 2.3 节顺序、反向清理、单 runtime lease、rank table/root info 互斥选择和输出 buffer 容量公式。
- **构建/测试：** build-only + 生命周期状态机单测；实机命令只作为 `HCCL_DIRECT_REAL_DEVICE=1` opt-in 模板。
- **当前环境：** 状态机测试可执行；实际 lifecycle 为 `HARDWARE_BLOCKED`。
- **完成条件：** 错误分支不泄漏已拥有的资源；测试证明无设备不会越过 guard。
- **HARDWARE_BLOCKED：** 无 device node/driver/NPU 或未获实机授权。
- **ENV_BLOCKED：** rank table、launcher、CANN 环境、权限、版本或库依赖错误。
- **evidence：** state-transition log；无设备只有 `NO_DEVICE_EXPECTED`，不得生成 device-pass evidence。
- **建议 commit / 回滚：** `G2-F-4 add guarded direct API lifecycle harness`；revert 该项目提交。

### G2-F-5：真实设备三原语数据正确性

- **目标：** 每个 primitive 在真实 NPU、多 rank、ACL device buffer 上经直接 API 得到正确 D2H 结果。
- **修改文件：** real-device launcher/harness、direct backend 适配、correctness tests/evidence writer；CPU_SIM 与 HCCL-VM 文件只增加隔离回归，不改其语义。
- **非目标：** 不以性能结论、故障恢复或多节点规模宣告完成。
- **API 契约：** AllReduce `count`、AllGather `sendCount`、ReduceScatter `recvCount`；dtype/op、输入/输出字节与 rank-size 显式记录；device pointer 是强制前置条件。
- **构建/测试：** 先 build/link/symbol；由批准 launcher 启动每 rank 进程执行 `ASCEND_HCCL_DIRECT`；普通 CI 不运行。
- **当前环境：** `HARDWARE_BLOCKED`。
- **完成条件：** 三种 primitive 各有同步、D2H、独立 host reference、误差阈值、API trace 和清理通过的 `REAL_DEVICE_PASS`。
- **HARDWARE_BLOCKED：** 缺真实受支持 Ascend NPU、驱动/设备节点或至少 2 ranks 所需设备/进程环境。
- **ENV_BLOCKED：** rank table/root info、launcher、CANN env、权限、版本或网络配置不满足。
- **evidence：** `g2-f-direct-device-v1` per primitive；必须满足第 5 节所有 direct proof 字段。
- **建议 commit / 回滚：** `G2-F-5 validate direct collectives on real Ascend device`；revert 代码提交，保留 evidence。

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

