# HCCL Agent 赛题路线图 v2

本路线图从本轮审计差距出发，目标是把项目从“Python Agent + 数学模拟 + CPU AllReduce 原型”收敛到“可被赛题验收的 HCCL/HCOMM 兼容 Agent 工程”。原则：先补齐赛题硬性要求，再做 Agent 展示与工程优化；先让至少三种 primitive 正确，再谈性能创新；先减少平行模块，再新增功能。

## 总体阶段

```text
Stage A：项目基线收敛与事实修复
Stage B：HCCL/HCOMM 标准接口兼容层闭合
Stage C：三种集合通信原语 CPU 正确性实现
Stage D：高保真拓扑、硬件与成本模型
Stage E：Agent 代码生成-编译-测试-修复闭环
Stage F：可靠性与规模化验证
Stage G：校准、报告与比赛交付
```

## 验证环境分层

后续每个 Batch 应区分三类验证：

1. **Windows CPU 验证**：使用 Conda Python、Visual Studio 2022、MSVC、CMake 和 Windows DLL，验证 Python 逻辑、CPU 算法、接口和单元测试。
2. **Linux CPU 验证**：生成并加载 `libhccl_plugin.so`，验证 Linux 构建、ctypes Bridge 和比赛提交环境兼容性。
3. **CANN/Ascend 验证**：使用官方 SDK、HCOMM/HCCL、Ascend 设备和 Profiling 工具完成最终正确性、性能和可靠性验证。

Windows CPU 验证通过不能替代 Linux `.so` 或 CANN/Ascend 验收。

## Batch A1：基线事实修复与跨平台验证闭环

**优先级：P0**

### 1. Batch 定位

本 Batch 是项目进入后续核心开发前的工程基线修复，不实现新的集合通信算法，不增加新的 Agent Skill，不接入 CANN/HCOMM，也不扩展现有 primitive。

本 Batch 只解决以下问题：

1. 项目文档与当前代码事实不一致；
2. Windows Python 测试中存在 POSIX 路径依赖；
3. Windows CMake 默认构建流程不完整；
4. CTest 未注册现有 C 测试；
5. MSVC 编译存在 UTF-8 编码警告和测试输出乱码；
6. `examples/generated_code/` 中部分 Python 示例存在语法错误或定位不清；
7. Windows、Linux CPU 模式和最终 Ascend 模式的验证边界没有统一说明。

完成本 Batch 后，项目应形成一个稳定、可重复、不会误导后续开发的工程基线。

---

### 2. 对应赛题要求

- 完整、可编译、可运行的 Agent 工程；
- 清晰的运行环境和构建配置说明；
- 可重复执行的验证流程；
- 完整测试与运行记录；
- 项目能力声明与实际实现一致；
- 提交代码、动态库、头文件、CMake 和测试程序时具有明确边界。

本 Batch 不直接增加赛题核心算法能力，但它是后续标准接口、三种 primitive 和 Agent 自动开发闭环的必要前置条件。

---

### 3. 当前事实基线

已完成的 Windows Native 人工验证结果：

- Conda 环境：`hccl-agent`
- Python：3.10
- Windows Python 测试共运行 339 个；
- 出现 17 个 error，未显示 assertion failure；
- 其中 16 个与 loader 固定寻找 Linux `libhccl_plugin.so` 有关；
- 1 个与 `tests/test_calibration_profile.py` 写死 `/tmp/_test_calib.json` 有关；
- Visual Studio 2022、MSVC、CMake 和 MSBuild 可正常使用；
- Windows C 插件能够生成 `hccl_plugin.dll`；
- 增加自动符号导出参数后能够生成 `hccl_plugin.lib`；
- 6 个 C 测试程序能够成功编译；
- 手动执行共 41 个 C 测试用例，41 个通过，0 个失败；
- CTest 当前显示 `No tests were found`；
- MSVC 编译存在 `C4819`；
- 测试控制台中的部分 UTF-8 字符显示乱码；
- FP16 和 PROD 当前明确返回 `NOT_SUPPORTED`；
- Linux `.so`、CANN/HCOMM 和 Ascend 实机尚未验证。

---

### 4. 当前差距

#### 4.1 文档事实不一致

以下文档可能存在过期、冲突或能力声明超前：

```text
README.MD
hcccl/README.md
docs/project_documentation.md
docs/gap_analysis.md
docs/agent_capabilities.md
project_tree.txt
```

需要统一说明：

- 当前系统是 Python Agent + 数学模拟器 + CPU C 插件原型；
- C 插件不是实际 HCCL/CANN 实现；
- 当前已验证的是有限 FP32/SUM AllReduce CPU 模拟；
- AllGather、ReduceScatter 等 primitive 尚未形成完整 C 数据实现；
- FP16、BF16、通用 ReduceOp 尚未完成；
- 当前性能数据不能直接作为真实 HCCL 性能结论；
- Windows C 构建成功不代表 Linux `.so` 或 Ascend 环境已经验证。

#### 4.2 Python 测试路径不兼容

```text
tests/test_calibration_profile.py
```

固定使用：

```text
/tmp/_test_calib.json
```

导致 Windows Native 测试失败。

#### 4.3 Windows 默认构建不完整

当前 Windows 默认构建能够生成 DLL，但默认情况下没有生成测试程序链接所需的导入库。

人工验证需要额外传入：

```text
CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON
```

说明该能力尚未正式写入项目构建配置。

#### 4.4 CTest 未注册测试

虽然已经生成：

```text
test_topology
test_ring
test_butterfly
test_nhr
test_mesh
test_fattree
```

但运行 CTest 时返回：

```text
No tests were found
```

现有测试尚未纳入统一自动测试入口。

#### 4.5 MSVC 编码问题

Windows 编译出现 `C4819`，测试程序标题和箭头字符显示乱码。

需要正式处理 MSVC UTF-8 编译配置，但不得无依据地批量转换全部源码编码。

#### 4.6 生成代码示例定位不清

```text
examples/generated_code/
```

中的部分 `.py` 文件存在语法错误，且容易被误认为已经可运行的 Agent 生成算法实现。

---

### 5. 开发目标

完成以下工程基线：

1. 所有核心文档对当前真实能力使用统一口径；
2. `project_tree.txt` 与当前项目结构一致；
3. Python 测试不再依赖固定 POSIX `/tmp` 路径；
4. Windows 默认 CMake 配置能够生成 DLL 和导入库；
5. CTest 能发现并运行现有 6 个 C 测试程序；
6. 现有 41 个 C 测试用例继续全部通过；
7. MSVC 编译不再出现 `C4819`；
8. 测试输出不再依赖无法稳定显示的特殊字符；
9. `examples/generated_code/*.py` 均可通过 Python 语法解析，或者被明确标注为不可执行伪代码；
10. 建立 Windows CPU、Linux CPU 和 Ascend/CANN 三层验证说明。

---

### 6. 修改范围

本 Batch 允许修改：

```text
README.MD
hcccl/README.md
docs/project_documentation.md
docs/gap_analysis.md
docs/agent_capabilities.md
docs/cann_hccl_interface_guide.md
project_tree.txt
tests/test_calibration_profile.py
hcccl/CMakeLists.txt
examples/generated_code/*.py
```

必要时允许对以下 C 测试文件中的显示文本进行最小修改：

```text
hcccl/tests/test_topology.c
hcccl/tests/test_ring.c
hcccl/tests/test_butterfly.c
hcccl/tests/test_nhr.c
hcccl/tests/test_mesh.c
hcccl/tests/test_fattree.c
```

测试文件只允许修改控制台显示文本或编码兼容内容，不允许改变测试数据、断言条件、期望错误码或算法覆盖范围。

---

### 7. 禁止修改范围

本 Batch 禁止修改：

```text
agent/
skills/
plugin/
simulator/
topology/
hardware/
cost_model/
calibration/       # 测试临时路径对应的生产代码除外
knowledge/
analysis/
hcccl/src/hccl_algorithms.c
hcccl/src/hccl_comm.c
hcccl/include/
config/
prompts/
main.py
```

禁止：

- 实现 AllGather；
- 实现 ReduceScatter；
- 修改 AllReduce 算法逻辑；
- 增加 FP16/BF16；
- 增加新的 ReduceOp；
- 修改 Python loader 的 `.dll`/`.so` 加载逻辑；
- 实现标准 HCCL wrapper；
- 接入 CANN/HCOMM；
- 增加新的 Agent Skill；
- 改变模拟器性能公式；
- 调整赛题完成度以掩盖现有缺口。

`.dll`/`.so` 跨平台加载和标准 C wrapper 留到 Batch B1。

---

### 8. Codex 负责事项

#### 8.1 文档收敛

核验并统一以下事实：

- 当前系统定位；
- 已实现能力；
- CPU 模拟与真实通信的区别；
- 当前 primitive 覆盖；
- 当前数据类型和 ReduceOp 覆盖；
- CANN/HCOMM 接入状态；
- Windows 动态验证结果；
- Linux 和 Ascend 尚未验证的内容；
- 当前性能数据的可信边界；
- 下一阶段 P0 任务。

不得删除历史 Batch 记录，但应明确区分：

```text
历史完成记录
当前代码事实
当前动态验证结果
尚未实现能力
```

#### 8.2 更新项目树

使用 Git 已跟踪文件生成或更新：

```text
project_tree.txt
```

排除：

```text
.git/
third_party/
build/
hcccl/build/
__pycache__/
logs/
.venv/
venv/
```

不得将 Windows 临时构建目录写入项目树。

#### 8.3 修复测试临时路径

将测试中的固定路径：

```text
/tmp/_test_calib.json
```

替换为 Python 标准库提供的跨平台临时目录机制。

优先使用：

```python
tempfile.TemporaryDirectory()
```

要求：

- 测试结束后自动清理；
- 不写入项目仓库；
- 不依赖当前工作目录；
- Windows 和 Linux 均可运行。

#### 8.4 完善 Windows CMake 基线

在 `hcccl/CMakeLists.txt` 中正式处理：

- Windows DLL 符号导出；
- MSVC UTF-8 编译选项；
- Windows、Linux 条件分支；
- 测试目标注册；
- Release/Debug 多配置生成器；
- 不破坏 Linux 默认构建。

Windows 默认构建不得再要求用户手动传入：

```text
CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON
```

但本 Batch不修改 Python动态库加载器。

#### 8.5 注册 CTest

为以下测试目标注册 CTest：

```text
test_topology
test_ring
test_butterfly
test_nhr
test_mesh
test_fattree
```

要求：

- 使用 `enable_testing()`；
- 每个测试程序有明确的 `add_test()`；
- Windows 多配置生成器下可通过 `-C Release` 执行；
- Linux 单配置生成器仍可执行；
- CTest 失败时能够返回非零退出码。

#### 8.6 处理编码与控制台输出

为 MSVC 正式添加 UTF-8 编译选项。

对于仅用于测试展示的特殊字符，例如箭头、破折号或不可稳定显示的符号，可以替换为 ASCII：

```text
->
-
:
```

不得修改算法字符串、接口名称或错误码。

#### 8.7 收敛生成示例

对：

```text
examples/generated_code/*.py
```

采用统一策略：

- 保留为 `.py` 的文件必须通过 Python AST 语法检查；
- 文件顶部明确说明其属于示例生成产物；
- 不得宣称它是可提交的 HCCL/CANN 实现；
- 不增加新的算法功能；
- 不把伪代码错误修饰成真实通信实现。

---

### 9. 用户负责事项

1. 在 VS Code 中检查修改后的文档表述是否符合项目实际情况；
2. 使用 `hccl-agent` Conda 环境执行 Python 验收；
3. 使用 Visual Studio 2022/MSVC 执行 Windows CMake 构建；
4. 确认 CTest 能自动发现并运行全部测试；
5. 检查控制台输出是否仍有乱码；
6. 核验 Git 修改范围；
7. 不在本 Batch 中要求 Codex继续 B1 开发。

---

### 10. Windows 验收命令

在已激活的 Conda 环境中进入：

```cmd
F:
cd \projects\hccl-agent
```

#### 10.1 Python 临时路径测试

```cmd
python -m unittest tests.test_calibration_profile -q
```

通过标准：

```text
退出码为 0
不再访问 /tmp
不在项目中留下临时文件
```

#### 10.2 生成代码语法检查

```cmd
python -c "import ast,pathlib; files=list(pathlib.Path('examples/generated_code').glob('*.py')); errors=[]; [(ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))) for p in files]; print(f'GENERATED_FILES={len(files)}'); print('GENERATED_SYNTAX_ERRORS=0')"
```

通过标准：

```text
GENERATED_SYNTAX_ERRORS=0
```

#### 10.3 Windows CMake 配置

```cmd
set BUILD_DIR=F:\build\hccl-agent-hcccl-a1

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

cmake -S hcccl -B "%BUILD_DIR%" ^
  -G "Visual Studio 17 2022" ^
  -A x64
```

不得额外传入：

```text
CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS
CMAKE_C_FLAGS
```

#### 10.4 Windows 构建

```cmd
cmake --build "%BUILD_DIR%" --config Release
echo CMAKE_BUILD_EXIT_CODE=%ERRORLEVEL%
```

通过标准：

```text
CMAKE_BUILD_EXIT_CODE=0
```

并成功生成：

```text
%BUILD_DIR%\Release\hccl_plugin.dll
%BUILD_DIR%\Release\hccl_plugin.lib
```

#### 10.5 CTest

```cmd
ctest --test-dir "%BUILD_DIR%" -C Release --output-on-failure
echo CTEST_EXIT_CODE=%ERRORLEVEL%
```

通过标准：

```text
发现 6 个测试程序
6 个测试程序全部通过
CTEST_EXIT_CODE=0
```

测试内部应继续保持：

```text
41 个用例
41 个通过
0 个失败
```

#### 10.6 编码验收

构建日志中不应再出现：

```text
warning C4819
```

测试控制台输出中不应再出现明显的乱码序列，例如：

```text
鈥?
鈫?
```

---

### 11. Linux 验收边界

本 Batch 以 Windows Native 验收为主。

如果 Linux/WSL 当前不可用：

- 不阻塞本 Batch 完成；
- 不访问旧 WSL 项目；
- 不将 Windows DLL 验证写成 Linux `.so` 已验证；
- 在文档中保留 Linux 验收待办。

后续 Linux 可用时执行：

```bash
cmake -S hcccl -B /tmp/hccl-agent-hcccl-a1
cmake --build /tmp/hccl-agent-hcccl-a1
ctest --test-dir /tmp/hccl-agent-hcccl-a1 --output-on-failure
```

---

### 12. 明确通过标准

本 Batch 只有同时满足以下条件才算完成：

- [ ] 文档能力声明与当前代码事实一致；
- [ ] 文档明确区分 CPU 模拟、数学模型、Stub、真实实现和未验证内容；
- [ ] `project_tree.txt` 与当前仓库结构一致；
- [ ] calibration 测试不再依赖 `/tmp`；
- [ ] Windows 默认 CMake 配置成功；
- [ ] 默认构建生成 DLL 和导入库；
- [ ] 不再需要额外手工开启 Windows 自动符号导出；
- [ ] CTest 能发现 6 个测试；
- [ ] 现有 41 个 C 用例全部通过；
- [ ] MSVC 不再出现 `C4819`；
- [ ] C 测试控制台无明显乱码；
- [ ] generated Python 示例不存在语法错误；
- [ ] 未修改算法实现、标准接口或 Agent 主流程；
- [ ] 未开始 Batch B1；
- [ ] Git 修改范围仅包含本 Batch 明确允许的文件。

---

### 13. 验收后的 Git 检查

```cmd
git status --short --untracked-files=all
git diff --name-only
git diff --stat
```

不得自动执行：

```text
git add
git commit
git push
```

用户人工确认全部结果后，再决定是否提交。

---

### 14. 依赖、难度与风险

**依赖：**

- 项目审计报告；
- Windows Conda Python 环境；
- Visual Studio 2022 MSVC；
- CMake；
- 当前 41 个 C 测试基线。

**难度：**低—中
**风险：**低
**是否需要真实 Ascend 环境：**否
**是否可以完全通过 CPU 模拟完成：**是

主要风险：

1. 文档修改范围过大，误删历史 Batch；
2. CMake Windows 修复破坏 Linux 构建；
3. 为消除编码警告而批量修改源码编码；
4. 修改测试输出时意外改变断言逻辑；
5. 将 DLL 导出修复扩张为 B1 的插件加载改造。

---

### 15. 交付物

本 Batch 应交付：

1. 统一后的项目能力说明；
2. 更新后的项目树；
3. 跨平台临时路径测试；
4. Windows 默认可构建的 CMake 配置；
5. 可由 CTest 自动运行的 6 个 C 测试程序；
6. 41/41 C 用例通过记录；
7. 无 `C4819` 的 MSVC 构建记录；
8. 无明显乱码的测试输出；
9. 语法有效并明确标注用途的生成代码示例；
10. Windows、Linux CPU 和 Ascend/CANN 三层验证说明。

完成后停止，不自动进入 Batch B1。

## Batch B1：标准 C 接口与跨平台插件加载闭环

优先级：P0  
对应赛题要求：基于 HCOMM/HCCL 风格接口，形成可编译、可调用、可测试的 C/C++ 通信接口层。

### Batch 定位

本 Batch 建立 CPU 模拟层的统一标准 C 接口，以及 Windows/Linux 跨平台动态库调用闭环。

Batch A1 已完成：

- Windows 默认 DLL 构建；
- Windows 导入库生成；
- CTest 注册；
- MSVC UTF-8 编译配置；
- Windows/Linux 基础构建说明；
- 跨平台临时目录修复；
- Windows C/C++ 测试基线。

本 Batch 不重复处理上述工程基线问题。

本 Batch 只负责：

1. 闭合标准 C wrapper；
2. 明确 wrapper 与现有 CPU 算法实现之间的映射；
3. 支持 Windows `.dll` 与 Linux `.so` 的统一 Python 加载；
4. 支持显式指定动态库路径；
5. 建立真实 DLL 加载和 ABI 测试。

本 Batch 不实现完整 AllGather、ReduceScatter 数据算法，不增加混合精度，不接入真实 CANN/HCOMM。

---

### 当前差距

- `hcccl/include/hccl_comm.h` 声明了 `hcclAllReduce`、`hcclAllGather`、`hcclReduceScatter`、`hcclBroadcast` 等接口；
- C 源码当前主要实现算法级函数，标准 wrapper 与算法实现之间尚未完全闭合；
- Python `plugin/hccl_bridge.py` 和 `plugin/execution_engine.py` 当前主要按 Linux `libhccl_plugin.so` 组织动态库发现；
- Windows 已能生成 `hccl_plugin.dll`，但 Python 尚未完成对本轮实际 DLL 的 `ctypes` 集成验证；
- 动态库路径不能通过构造参数或环境变量显式指定，默认候选路径也缺少统一的跨平台解析规则；
- Python 兼容 API、C wrapper 和底层算法函数之间存在接口分裂；
- 部分标准接口可能存在“头文件有声明，但动态库中没有可调用符号”的风险；
- Python Bridge 尚未为全部实际调用的 C 函数明确配置 `argtypes` 和 `restype`；
- 动态库缺失、路径无效或符号缺失时，错误信息不够明确。

---

### 开发目标

#### 1. 闭合统一标准 C wrapper

需要检查并闭合以下接口：

- `hcclAllReduce`
- `hcclAllGather`
- `hcclReduceScatter`
- `hcclBroadcast`

B1 对各 wrapper 的实现边界如下。

##### `hcclAllReduce`

- 必须复用当前 `ExecutionEngine` 或现有调用链已经采用的算法路由；
- 不得在 B1 中新增算法选择策略；
- 如果标准 wrapper 本身没有算法参数，应沿用当前默认路由；
- 必须实际进入已有 CPU AllReduce 实现；
- 不能只返回固定成功状态码；
- 不扩展当前支持的 `count`、数据类型、ReduceOp 或 rank 范围；
- 不修改已有 Ring、Butterfly、Mesh、NHR、Fat-Tree 算法逻辑。

##### `hcclAllGather`

- 必须存在可导出的函数定义；
- 必须完成基础参数校验和错误码闭合；
- 完整数据算法尚未实现时，应明确返回 `HCCL_ERR_NOT_SUPPORTED`；
- 不得返回伪造的成功状态；
- 不得伪造输出数据；
- 完整 AllGather 数据正确性实现留到 Batch C1。

##### `hcclReduceScatter`

- 必须存在可导出的函数定义；
- 必须完成基础参数校验和错误码闭合；
- 完整数据算法尚未实现时，应明确返回 `HCCL_ERR_NOT_SUPPORTED`；
- 不得返回伪造的成功状态；
- 不得伪造输出数据；
- 完整 ReduceScatter 数据正确性实现留到 Batch C2。

##### `hcclBroadcast`

- 必须消除“头文件声明但无符号定义”的问题；
- 必须完成基础参数校验；
- 如果本阶段不实现数据算法，应明确返回 `HCCL_ERR_NOT_SUPPORTED`；
- 不得返回伪造的成功状态或输出结果。

所有未实现的 primitive：

- 不得返回 `HCCL_SUCCESS`；
- 不得修改输出缓冲区；
- 不得伪造数据正确性结果；
- 必须通过明确错误码说明当前不支持。

#### 2. 建立 wrapper 与现有算法函数的映射

- 标准 wrapper 与底层算法函数之间必须有明确、可追踪的调用关系；
- 不得在多个模块中重复实现同一层路由；
- 不得在 wrapper 中重新复制已有算法逻辑；
- 不得改变现有 AllReduce 算法的计算结果和错误码语义；
- CPU wrapper 必须明确标注为 CPU 模拟兼容层，不得宣称是真实 HCCL/HCOMM 实现。

#### 3. 实现统一跨平台动态库加载

Python Bridge 根据运行平台支持：

Windows：

```text
hccl_plugin.dll
```

Linux：

```text
libhccl_plugin.so
```

Windows 和 Linux 必须使用同一套 Python 调用接口。

#### 4. 支持显式动态库路径

支持以下三种动态库定位方式：

1. 构造参数 `library_path`；
2. 环境变量 `HCCL_PLUGIN_PATH`；
3. 项目默认候选路径。

路径解析优先级必须为：

```text
library_path
> HCCL_PLUGIN_PATH
> 项目默认候选路径
```

默认候选路径必须满足：

- 集中定义，避免多个模块分别拼接路径；
- 相对于项目根目录或 Python 模块位置解析；
- 不得写死 `F:\build`；
- 不得写死用户名、盘符或其他机器绝对路径；
- Windows 和 Linux 使用同一个路径解析入口；
- 外部构建目录必须通过 `library_path` 或 `HCCL_PLUGIN_PATH` 传入；
- 不得扫描整个磁盘寻找动态库。

#### 5. 完善动态库加载错误

以下情况必须产生清晰异常：

- 显式指定的动态库路径不存在；
- 环境变量路径不存在；
- 默认候选路径全部不存在；
- 文件存在但无法被 `ctypes` 加载；
- 动态库加载成功但缺少必要符号；
- 动态库架构或依赖不匹配；
- wrapper 调用参数不符合 ABI。

错误信息应包含：

- 尝试加载的路径；
- 已检查的默认候选路径；
- 缺失的符号名称；
- 原始系统错误信息；
- 当前操作系统平台。

#### 6. 保持当前 ABI 边界

- 以 `hcccl/include/hccl_comm.h` 当前声明作为本项目现阶段 ABI 合同；
- 在缺少官方接口证据时，不得擅自修改函数名称；
- 不得擅自改变参数顺序、参数类型或返回值类型；
- 不得擅自改变调用约定；
- Windows 默认 C ABI 使用 `ctypes.CDLL`；
- 只有现有头文件明确声明其他调用约定时，才允许采用其他加载方式。

#### 7. 明确 ctypes 函数签名

Python Bridge 必须为实际调用的 C 函数设置明确的：

```text
argtypes
restype
```

至少覆盖：

- `hcclCommInit`
- `hcclCommDestroy`
- `hcclGetTopology`
- `hcclAllReduce`
- `hcclAllGather`
- `hcclReduceScatter`
- `hcclBroadcast`

不得依赖 `ctypes` 的隐式参数转换。

#### 8. 建立真实 DLL 集成验证

Windows 集成测试必须：

- 使用本轮实际生成的 `hccl_plugin.dll`；
- 通过 `ctypes.CDLL` 真正加载动态库；
- 检查四个标准 wrapper 的实际导出符号；
- 至少实际调用一次 `hcclAllReduce` wrapper；
- 验证未实现 wrapper 返回 `HCCL_ERR_NOT_SUPPORTED`；
- 不得只使用 Mock 证明 DLL 加载成功。

Mock 只允许用于：

- 模拟 Windows/Linux 平台差异；
- 测试路径优先级；
- 测试不存在路径；
- 测试缺失符号异常；
- 测试加载失败异常。

---

### 主要修改文件

允许修改：

```text
hcccl/include/hccl_comm.h
hcccl/src/hccl_comm.c
plugin/hccl_bridge.py
plugin/execution_engine.py
plugin/hccl_api.py
tests/test_plugin_bridge.py
tests/test_execution_engine.py
tests/test_hccl_api.py
hcccl/tests/test_api_wrappers.c
```

仅在确有必要时允许最小修改：

```text
hcccl/src/hccl_algorithms.c
hcccl/CMakeLists.txt
agent/plugin_manager.py
tests/test_plugin_manager.py
```

限制如下：

- `hcccl/src/hccl_algorithms.c` 只允许暴露或复用现有算法入口，不允许改变算法行为；
- `hcccl/CMakeLists.txt` 只允许增加 B1 新测试目标、必要的源文件关系或必要符号导出，不得重新设计 A1 已完成的 CTest、UTF-8 和基础 DLL 构建逻辑；
- `agent/plugin_manager.py` 只允许传递动态库路径或复用统一 Bridge；
- `tests/test_plugin_manager.py` 只允许验证上述最小调用链变更；
- 不得修改其他 Agent 模块；
- 不得修改 A1 已稳定的六个既有 C 测试文件，除非新增 wrapper 后出现真实接口兼容问题，并且修改不得改变原有断言语义。

---

### 禁止事项

本 Batch 禁止：

- 实现完整 AllGather 数据算法；
- 实现完整 ReduceScatter 数据算法；
- 修改现有 AllReduce 算法逻辑；
- 新增 AllReduce 算法选择策略；
- 扩展现有 `count` 范围；
- 增加 FP16；
- 增加 BF16；
- 增加新的 ReduceOp；
- 接入真实 CANN；
- 接入真实 HCOMM；
- 修改 Simulator 性能公式；
- 修改拓扑模型；
- 修改成本模型；
- 增加新的 Agent Skill；
- 修改与本 Batch 无关的文档；
- 扫描整个磁盘寻找动态库；
- 将本机绝对构建路径写入源码；
- 使用 Mock 冒充真实 DLL 集成验证；
- 发送真实 DeepSeek 或其他外部 LLM 网络请求。

AllGather 和 ReduceScatter 的完整数据正确性分别留到 Batch C1 和 Batch C2。

---

### C wrapper 测试要求

建议新增：

```text
hcccl/tests/test_api_wrappers.c
```

至少覆盖：

- 四个 wrapper 符号能够编译并链接；
- `hcclAllReduce` 能进入已有 CPU AllReduce 路径；
- `hcclAllReduce` 在当前支持范围内得到正确结果；
- `hcclAllGather` 未实现时返回 `HCCL_ERR_NOT_SUPPORTED`；
- `hcclReduceScatter` 未实现时返回 `HCCL_ERR_NOT_SUPPORTED`；
- `hcclBroadcast` 未实现时返回 `HCCL_ERR_NOT_SUPPORTED`；
- 未实现 primitive 不修改输出缓冲区；
- 空指针返回正确错误码；
- 无效 communicator 返回正确错误码；
- 无效 count 返回正确错误码；
- 不支持的数据类型返回正确错误码；
- 不支持的 ReduceOp 返回正确错误码；
- A1 已有 41 个 C 用例的预期结果不改变。

新增测试必须注册到 CTest。

CTest 测试程序总数允许从 6 增加，不得将总数固定为 6。

---

### Python 测试要求

至少覆盖：

- 构造参数 `library_path` 优先于环境变量；
- `HCCL_PLUGIN_PATH` 优先于默认候选路径；
- Windows 默认 DLL 文件名；
- Linux 默认 SO 文件名；
- Windows 默认候选路径；
- Linux 默认候选路径；
- 显式路径不存在；
- 环境变量路径不存在；
- 所有默认候选路径均不存在；
- 动态库加载失败；
- 动态库缺少必要符号；
- 异常信息包含尝试路径；
- 异常信息包含缺失符号名称；
- `argtypes` 和 `restype` 已明确配置；
- 实际 Windows DLL 能加载；
- 实际 DLL 中存在四个标准 wrapper；
- `hcclAllReduce` wrapper 能实际调用；
- 未实现 wrapper 返回 `HCCL_ERR_NOT_SUPPORTED`；
- 原有 Plugin Bridge 行为不回归；
- 原有 Execution Engine 行为不回归；
- 如果修改 Plugin Manager，其原有行为不回归。

---

### Windows 验收命令

以下命令在已激活 `hccl-agent` Conda 环境的 CMD 或 Anaconda Prompt 中执行。

#### 1. 创建独立构建目录

```cmd
set BUILD_DIR=F:\build\hccl-agent-hcccl-b1

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
```

#### 2. 配置 Visual Studio 2022 构建

```cmd
cmake -S hcccl -B "%BUILD_DIR%" ^
  -G "Visual Studio 17 2022" ^
  -A x64
```

不得额外传入：

```text
CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS
CMAKE_C_FLAGS
```

这些基础能力已由 Batch A1 的默认 CMake 配置提供。

#### 3. 构建

```cmd
cmake --build "%BUILD_DIR%" --config Release
echo CMAKE_BUILD_EXIT_CODE=%ERRORLEVEL%
```

通过标准：

```text
CMAKE_BUILD_EXIT_CODE=0
```

并生成：

```text
%BUILD_DIR%\Release\hccl_plugin.dll
%BUILD_DIR%\Release\hccl_plugin.lib
```

#### 4. 运行 CTest

```cmd
ctest --test-dir "%BUILD_DIR%" ^
  -C Release ^
  --output-on-failure

echo CTEST_EXIT_CODE=%ERRORLEVEL%
```

通过标准：

- A1 原有 6 个 C 测试程序继续通过；
- 新增 wrapper C 测试通过；
- 原有 41 个 C 测试用例继续全部通过；
- `CTEST_EXIT_CODE=0`。

#### 5. 设置实际 DLL 和关闭真实 LLM Key

必须在同一个 CMD 或 Anaconda Prompt 会话中执行：

```cmd
set HCCL_PLUGIN_PATH=%BUILD_DIR%\Release\hccl_plugin.dll
set DEEPSEEK_API_KEY=
```

#### 6. 验证实际 DLL 和导出符号

```cmd
python -c "import ctypes,os; p=os.environ['HCCL_PLUGIN_PATH']; lib=ctypes.CDLL(p); names=['hcclAllReduce','hcclAllGather','hcclReduceScatter','hcclBroadcast']; missing=[n for n in names if not hasattr(lib,n)]; print('DLL_PATH='+p); print('MISSING_SYMBOLS='+str(missing)); raise SystemExit(1 if missing else 0)"
```

通过标准：

```text
MISSING_SYMBOLS=[]
```

该命令必须加载本轮实际生成的 DLL，不得替换为 Mock。

#### 7. 运行定向 Python 测试

```cmd
python -m unittest ^
  tests.test_plugin_bridge ^
  tests.test_execution_engine ^
  tests.test_hccl_api ^
  -q
```

如果本轮修改了 `agent/plugin_manager.py`，还必须执行：

```cmd
python -m unittest tests.test_plugin_manager -q
```

#### 8. 运行完整 Python 回归

```cmd
python -m unittest discover tests -q
```

完整回归要求：

- `0 failures`；
- `0 errors`；
- 允许存在明确设计的 skipped；
- 不得发送真实网络请求；
- 不得调用真实 DeepSeek API；
- 必须实际加载本轮生成的 Windows DLL；
- 不得仅使用 Mock 结果证明 DLL 集成成功；
- 不得在项目目录留下临时构建文件。

---

### Linux CPU 验收

Linux CPU 验收命令：

```bash
BUILD_DIR=/tmp/hccl-agent-hcccl-b1

rm -rf "$BUILD_DIR"

cmake -S hcccl -B "$BUILD_DIR"
cmake --build "$BUILD_DIR"

ctest \
  --test-dir "$BUILD_DIR" \
  --output-on-failure

export HCCL_PLUGIN_PATH="$BUILD_DIR/libhccl_plugin.so"
unset DEEPSEEK_API_KEY

python -m unittest \
  tests.test_plugin_bridge \
  tests.test_execution_engine \
  tests.test_hccl_api \
  -q

python -m unittest discover tests -q
```

实际 `.so` 输出位置必须以 CMake 构建结果为准。

如果 `.so` 位于其他目录：

- 应使用实际生成路径；
- 不得通过复制或重命名伪造验证结果；
- 不得把 Windows DLL 重命名为 `.so`；
- 不得将未执行的 Linux 验收写成已经通过。

当前 Linux/WSL 环境暂时不可用时：

- 不阻塞 Windows B1 初步完成；
- Linux `.so` 动态验证保持为待办；
- 不得写成 Linux Bridge 已验证；
- 不得写成 Linux CMake 已验证；
- 不得访问旧 WSL 项目。

---

### 通过标准

本 Batch 只有同时满足以下条件才算完成：

- [ ] `hcclAllReduce` 有可导出的定义并能够链接；
- [ ] `hcclAllGather` 有可导出的定义并能够链接；
- [ ] `hcclReduceScatter` 有可导出的定义并能够链接；
- [ ] `hcclBroadcast` 有可导出的定义并能够链接；
- [ ] wrapper 与底层算法函数映射清晰；
- [ ] `hcclAllReduce` 实际进入已有 CPU AllReduce 路径；
- [ ] `hcclAllReduce` 不是固定返回成功；
- [ ] `hcclAllGather` 未实现时返回 `HCCL_ERR_NOT_SUPPORTED`；
- [ ] `hcclReduceScatter` 未实现时返回 `HCCL_ERR_NOT_SUPPORTED`；
- [ ] `hcclBroadcast` 未实现时返回 `HCCL_ERR_NOT_SUPPORTED`；
- [ ] 未实现 primitive 不修改输出缓冲区；
- [ ] 未实现 primitive 不返回伪造成功结果；
- [ ] Windows Python Bridge 能加载本轮实际生成的 `hccl_plugin.dll`；
- [ ] Linux Python Bridge 设计上支持 `libhccl_plugin.so`；
- [ ] 构造参数 `library_path` 可以指定动态库；
- [ ] 环境变量 `HCCL_PLUGIN_PATH` 可以指定动态库；
- [ ] 默认候选路径可正常解析；
- [ ] 路径优先级为构造参数、环境变量、默认候选路径；
- [ ] 默认路径中不存在本机用户名、盘符或 `F:\build` 等绝对路径；
- [ ] 缺失库、错误路径和缺失符号均产生明确异常；
- [ ] 异常信息包含尝试加载的路径或缺失的符号名称；
- [ ] Python Bridge 为实际调用函数设置明确的 `argtypes` 和 `restype`；
- [ ] 实际 DLL 中可以找到四个标准 wrapper；
- [ ] Windows 集成测试不是仅使用 Mock；
- [ ] Windows 路径解析有单元测试；
- [ ] Linux 候选文件名和路径逻辑有单元测试；
- [ ] A1 已有 6 个 C 测试程序继续全部通过；
- [ ] A1 已有 41 个 C 用例继续全部通过；
- [ ] 新增标准 wrapper C 测试全部通过；
- [ ] Plugin Bridge Python 测试通过；
- [ ] Execution Engine Python 测试通过；
- [ ] HCCL API Python 测试通过；
- [ ] 完整 Python 回归为 0 failures、0 errors；
- [ ] 本轮没有真实网络请求；
- [ ] 没有提前实现 C1/C2 的完整 primitive 数据算法；
- [ ] 没有增加 FP16、BF16 或新的 ReduceOp；
- [ ] 没有宣称已经接入真实 HCOMM/CANN；
- [ ] 没有宣称 Linux `.so` 已经验证；
- [ ] 没有修改与 B1 无关的 Agent、Simulator、Topology 或 Cost Model。

---

### 完成后的 Git 检查

执行：

```cmd
git status --short
git diff --name-only
git diff --stat
git diff --check
```

确认：

- 修改文件全部位于 B1 允许范围；
- 不存在意外生成的 DLL、LIB、EXE、OBJ 或构建目录；
- 不存在无关文档修改；
- 不存在算法范围外修改。

不得自动执行：

```text
git add
git commit
git push
```

用户人工确认验收结果后再决定是否提交。

---

### 依赖、难度与风险

依赖：Batch A1。  
难度：中。  
风险：中。  
Ascend 环境：CPU 初版不需要，最终标准兼容验证需要。  
Linux 环境：设计支持必须完成，实际动态验证可暂时保留为待办。  
可完全通过 Windows CPU 模式完成：大部分可以。  
可完全替代 CANN/HCOMM 实机验证：否。

主要风险：

1. B1 越界进入 C1/C2，提前实现完整 primitive；
2. 修改 `hcccl/src/hccl_algorithms.c` 时改变已有算法行为；
3. 将本机外部构建路径写死到 Python 源码；
4. 使用 Mock 代替真实 DLL 集成验证；
5. wrapper 返回成功但没有执行实际算法；
6. 未实现 primitive 返回成功或修改输出缓冲区；
7. 修改 CMake 时破坏 A1 已稳定的构建和 CTest；
8. 将 CPU 模拟接口错误描述为真实 HCOMM/HCCL 兼容实现。

---

### 交付物

本 Batch 应交付：

1. 闭合的四个标准 C wrapper；
2. wrapper 与现有算法实现的明确映射；
3. 新增的标准 wrapper C 测试；
4. Windows `.dll` 与 Linux `.so` 统一路径解析；
5. `library_path` 显式路径支持；
6. `HCCL_PLUGIN_PATH` 环境变量支持；
7. 集中的默认候选路径规则；
8. 明确的动态库加载异常；
9. 完整的 ctypes `argtypes` 和 `restype`；
10. Windows 实际 DLL 加载证据；
11. 四个 wrapper 的实际导出符号检查；
12. CMake、CTest、定向 Python 测试和完整回归结果；
13. Linux `.so` 和 CANN/Ascend 的未验证边界说明。

完成后停止，不自动进入 Batch C1。

## Batch C1：AllGather CPU 数据正确性

优先级：P0  
对应赛题要求：至少 3 种核心集合通信原语正确实现。  
前置基线：

- A1 已完成 CMake、CTest 和 Windows构建基线；
- B1 已完成标准 C wrapper 与 `.dll`/`.so` 加载闭环；
- C1 不再修改通用插件发现机制或基础构建配置。

当前差距：Python `HcclAllGather` 只返回模拟性能指标，C `butterfly_allgather` 是 Stub。  
开发目标：实现 FP32 `count>=1` 的 CPU AllGather，至少支持 Ring 与 Butterfly 两种路径，返回每 rank 拼接结果。  
主要修改文件：`hcccl/src/hccl_algorithms.c`、`hcccl/tests/test_allgather.c`、`plugin/execution_engine.py`、`tests/test_execution_engine.py`。  
Codex 负责：C 实现、ctypes 绑定、正确性测试、非法参数测试。  
用户负责：确认输出 buffer 形态与官方接口约定。  
验收命令：Windows验收命令：

```cmd
set BUILD_DIR=F:\build\hccl-agent-hcccl-c1

cmake -S hcccl -B "%BUILD_DIR%" ^
  -G "Visual Studio 17 2022" ^
  -A x64

cmake --build "%BUILD_DIR%" --config Release

ctest --test-dir "%BUILD_DIR%" ^
  -C Release ^
  --output-on-failure

python -m unittest tests.test_execution_engine -q
```

通过标准：4/8/16 rank、count=1 与 count>1 均通过；非法 dtype/op 正确返回。  
依赖：B1。  
难度：中。  
风险：中。  
Ascend 环境：不需要。  
可完全模拟完成：是。  
交付物：AllGather CPU 正确性证据。

## Batch C2：ReduceScatter CPU 数据正确性

优先级：P0  
对应赛题要求：至少 3 种核心集合通信原语正确实现。  
前置基线：

- A1 已完成构建和测试基线；
- B1 已完成标准 wrapper 与跨平台动态库加载；
- C1 已完成 AllGather 数据正确性；
- C2 只实现 ReduceScatter，不重复修改插件发现和通用 wrapper 架构。

当前差距：C `mesh_reducescatter` 是 Stub，Python 层只模拟指标。  
开发目标：实现 FP32 SUM ReduceScatter，支持每 rank 多元素输入，验证 reduce 后按 rank 切片。  
主要修改文件：`hcccl/src/hccl_algorithms.c`、`hcccl/tests/test_reducescatter.c`、`plugin/execution_engine.py`、`tests/test_execution_engine.py`。  
Codex 负责：C 算法实现、边界测试、Python 调用。  
用户负责：确认 rank 分片规则和测试数据样例。  
验收命令：

```cmd
set BUILD_DIR=F:\build\hccl-agent-hcccl-c2

cmake -S hcccl -B "%BUILD_DIR%" ^
  -G "Visual Studio 17 2022" ^
  -A x64

cmake --build "%BUILD_DIR%" --config Release

ctest --test-dir "%BUILD_DIR%" ^
  -C Release ^
  --output-on-failure

python -m unittest tests.test_execution_engine -q
```

通过标准：

- 结果与 Python reference SUM+scatter 一致，支持 4/8 rank。
- AllReduce、AllGather 和 ReduceScatter 三种 primitive 的既有测试必须同时通过；
- ReduceScatter 结果必须与 Python reference 的 reduce + scatter 结果一致；
- 不得只返回模拟性能指标；
- 不增加 FP16/BF16 和通用 ReduceOp，这些留到 C3。

依赖：B1。  
难度：中。  
风险：中。  
Ascend 环境：不需要。  
可完全模拟完成：是。  
交付物：第三个 primitive 的正确性证据。

## Batch C3：数据类型、ReduceOp 与正确性基准

优先级：P0  
对应赛题要求：FP32/BF16/FP16 混精度，误差 <=1e-6，无 NaN/溢出。  
当前差距：C tests 明确 FP16/PROD 返回 `NOT_SUPPORTED`。  
开发目标：先补 FP32 的 SUM/PROD/MAX/MIN，再设计 FP16/BF16 CPU 表示或模拟策略；建立 reference checker。  
主要修改文件：`hcccl/include/hccl_comm.h`、`hcccl/src/hccl_algorithms.c`、`hcccl/tests/*`、`tests/test_hccl_api.py`。  
Codex 负责：reference 测试、错误码、NaN/Inf/溢出样例。  
用户负责：确认 BF16 表示策略是否可先用 uint16 模拟。  
验收命令：

- 运行完整 CTest；
- 运行 AllReduce、AllGather、ReduceScatter 的 Python correctness suite；
- 对每种 dtype 和 ReduceOp 使用独立 reference checker；
- Windows CPU 模式作为初始验收；
- Linux `.so` 和 Ascend/CANN 精度作为后续最终验收。

通过标准：每种 primitive 至少 FP32 全通过；FP16/BF16 有明确实现或明确跳过说明。  
依赖：C1、C2。  
难度：中-高。  
风险：中。  
Ascend 环境：不需要初版。  
可完全模拟完成：大部分是。  
交付物：正确性报告初版。

C3 不负责重新设计 B1 的动态库加载机制，也不负责 D1 的性能模型和拓扑模型。

## Batch D1：拓扑与成本模型收敛

优先级：P1  
对应赛题要求：自动探测 HCCS/RoCE/PCIe、构建加权有向图、路径和拥塞建模。  
当前差距：存在 `skills/topology_graph.py` 与 `topology/graph_builder.py` 两套平行模型，主 `Simulator.evaluate()` 不充分使用 graph 和 message_size。  
开发目标：确定唯一主拓扑模型；让 Simulator 以 graph/cost model 为主；补 8/64/128/256/1024 场景。  
主要修改文件：`simulator/simulator.py`、`topology/graph_builder.py`、`cost_model/engine.py`、`config/cluster.json`、`experiments/scenarios/*`。  
Codex 负责：模型收敛、测试和报告脚本。  
用户负责：提供或确认可用硬件参数来源。  
验收命令：`python -m unittest tests.test_graph_simulator tests.test_cost_model tests.test_scaling_analysis -q`。  
通过标准：message_size、链路类型、节点规模真实影响 latency/bandwidth。  
依赖：C1/C2。  
难度：高。  
风险：高。  
Ascend 环境：不需要初版。  
可完全模拟完成：是。  
交付物：高保真模拟器 v1。

## Batch E1：Agent 代码生成闭环最小版

优先级：P1  
对应赛题要求：核心算法与代码通过 Agent 生成，过程可复现。  
当前差距：`CodeGenerationSkill` 只产伪代码，不写入、不编译、不测试、不修复。  
开发目标：限定生成目标为一个小型 C 算法函数或测试文件，完成生成 -> 写入隔离目录 -> 编译 -> 运行测试 -> 读取错误 -> 一次修复。  
主要修改文件：`agent/code_generation_skill.py`、新增生成工作区管理模块、`tests/test_code_generation_flow.py`。  
Codex 负责：闭环实现、dry-run、安全写入、日志。  
用户负责：确认是否允许真实 LLM，提供 Key 或选择离线模板模式。  
验收命令：无 Key 模板模式测试；有 Key 时单独人工触发。  
通过标准：从干净目录可复现生成、编译和测试记录。  
依赖：B1。  
难度：高。  
风险：高。  
Ascend 环境：不需要。  
可完全模拟完成：是。  
交付物：Agent 生成闭环 demo。

生成工作区必须使用跨平台临时目录，不得重新引入固定 `/tmp` 路径。

## Batch F1：可靠性验证闭环

优先级：P1  
对应赛题要求：链路健康检测、100ms 切换、CRC32+奇偶校验、重传率 <=0.1%。  
当前差距：只有统计模拟和简单 failover，无 CRC 数据路径和压测。  
开发目标：在模拟器中实现可重复故障场景、CRC/重传统计、failover 时间记录、可靠性报告。  
主要修改文件：`simulator/fault_injector.py`、`simulator/health_monitor.py`、`simulator/retry_policy.py`、`simulator/failover_engine.py`、`experiments/`、`docs/reliability_report.md`。  
Codex 负责：模拟可靠性闭环和报告。  
用户负责：审查报告是否满足赛题材料口径。  
验收命令：`python -m unittest tests.test_reliability_flow tests.test_failover_engine tests.test_retry_policy -q`。  
通过标准：固定 seed 可复现；报告包含故障、切换、重传率。  
依赖：D1。  
难度：中。  
风险：中。  
Ascend 环境：不需要初版。  
可完全模拟完成：是。  
交付物：可靠性报告初版。

## Batch G1：CANN/Ascend 实机适配准备

优先级：P1/P0（拿到实机后升级为 P0）  
对应赛题要求：CANN 8.0+、Ascend 910B/910C 或模拟器编译运行。  
当前差距：无 SDK、无 msprof、无真实 HCOMM 链接。  
开发目标：增加条件编译层：CPU_SIM 与 ASCEND_CANN；准备 CMake 选项、接口适配清单、实机测试手册。  
主要修改文件：`hcccl/CMakeLists.txt`、`hcccl/include/*`、`docs/cann_hccl_interface_guide.md`、`scripts/`。  
Codex 负责：条件编译、文档、测试命令模板。  
用户负责：获取 CANN/Ascend SDK、硬件、管理员安装权限、实机执行。  
验收命令：CPU 模式本地通过；实机模式用户执行 CMake 与 msprof。  
通过标准：无 SDK 时 CPU 模式不破；有 SDK 时能找到头/库并编译到适配层。  
依赖：B1/C1/C2。  
难度：高。  
风险：高。  
Ascend 环境：最终需要。  
可完全模拟完成：否。  
交付物：实机适配包和执行手册。

G1 不得覆盖或替换 CPU_SIM 路径，真实 CANN 模式必须通过独立 CMake 选项启用。

## 推荐顺序与暂停项

推荐的下一个 Batch：`Batch A1：基线事实修复与文档收敛`。原因是当前文档和示例会直接误导后续开发与评审，且成本低、收益高。

前三个 P0 Batch：

1. `A1`：修正文档事实和生成示例。
2. `B1`：闭合标准 C 接口。
3. `C1/C2`：AllGather 与 ReduceScatter CPU 数据正确性实现。

可以暂缓的功能：新的 Agent 顾问模块、更多优化建议文本、更多未校准性能报告、可视化、稀疏通信、量化压缩、端到端大模型训练演示。

应停止继续堆叠的 Agent 模块：新的解释器、评分器、顾问、历史经验加权模块。已有模块足够展示 Agent 架构，短期缺的是可验证核心通信能力。

没有 Ascend 实机时可完成到：标准接口 CPU 模拟闭合、三种 primitive FP32 正确性、可复现模拟器、高保真拓扑模型、Agent 生成闭环最小 demo、模拟性能/可靠性报告。

获得实机后第一批必须执行：CANN/HCOMM 编译、单机 8 卡 AllReduce/AllGather/ReduceScatter 正确性、FP16/BF16/FP32 误差、msprof 带宽/延迟采集、HCCL baseline 对比、故障和长稳测试抽样。

形成比赛可提交版本的关键里程碑：

1. 三种 primitive CPU 正确性通过。
2. 标准 C wrapper 与 Python bridge 闭合。
3. 模拟器参数有来源和校准记录。
4. Agent 生成-编译-测试-修复过程可复现。
5. 完整性能、正确性、可靠性、Agent 专项说明和演示材料齐备。
