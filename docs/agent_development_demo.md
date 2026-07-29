# Stage E1 Agent 自动代码开发最小闭环演示

更新时间：2026-07-29

## 结论

Stage E1 已完成 `OFFLINE_TEMPLATE` 模式的受控、可复现开发闭环。该闭环不调用真实 DeepSeek、OpenAI 或其他外部 LLM API，不访问网络，不读取 API Key，也不直接写入生产源码目录。

## 输入需求

```text
Generate a small AllReduce SUM reference checker with tests.
```

## 生成计划

| 步骤 | 说明 |
| ---- | ---- |
| 1 | 使用离线模板生成一个小型 AllReduce SUM reference checker。 |
| 2 | 写入 `tempfile.TemporaryDirectory()` 创建的隔离工作区。 |
| 3 | 使用命令白名单执行 `python -m py_compile <generated_file>`。 |
| 4 | 读取第一次编译错误。 |
| 5 | 最多两轮模板修复；本次只修复一轮。 |
| 6 | 再次编译并运行生成文件自带测试。 |
| 7 | 返回 stdout、stderr、exit code、修复记录和临时目录清理状态。 |

## 生成文件

| 文件 | 位置策略 | 是否进入仓库 |
| ---- | -------- | ------------ |
| `generated_reference_checker.py` | Windows 临时目录，前缀 `hccl-agent-e1-` | 否 |

## 命令白名单

允许的命令仅包括：

```text
<python_executable> -m py_compile <temporary_generated_file>
<python_executable> <temporary_generated_file>
```

实现使用 `subprocess.run(..., shell=False, timeout=10)`，并校验命令目标必须位于临时工作区内。

## 第一次编译命令

```text
python -m py_compile generated_reference_checker.py
```

结果：

| 字段 | 值 |
| ---- | -- |
| exit code | 1 |
| stdout | 空 |
| stderr 摘要 | `SyntaxError: '(' was never closed` |

## 修复理由

离线模板故意生成一个确定性语法错误：

```text
return sum(values
```

修复动作：

```text
return sum(values)
```

修复轮次：1。
最大允许修复轮次：2。

## 第二次结果

```text
python -m py_compile generated_reference_checker.py
```

结果：

| 字段 | 值 |
| ---- | -- |
| exit code | 0 |
| stdout | 空 |
| stderr | 空 |

## 测试结果

```text
python generated_reference_checker.py
```

结果：

| 字段 | 值 |
| ---- | -- |
| exit code | 0 |
| stdout | `offline reference checker passed` |
| stderr | 空 |

## 工作区路径策略

- 使用 `tempfile.TemporaryDirectory(prefix="hccl-agent-e1-")`。
- 不使用固定 `/tmp`。
- 不写入生产目录。
- 运行结束后临时目录已删除。

## 模式边界

| 模式 | 当前状态 | 说明 |
| ---- | -------- | ---- |
| `OFFLINE_TEMPLATE` | 已验证 | 默认模式，无 API Key 可运行。 |
| `EXTERNAL_LLM` | 未启用 | 只有用户明确提供 Key 并人工触发时才允许。 |

## 真实 LLM 与离线模板区别

- 离线模板：确定性输入、确定性失败、确定性修复，可在无网络和无 Key 条件下复现。
- 真实 LLM：可能产生非确定性输出，可能涉及外部 API、凭据和代码外传风险；自主 Goal 中禁止调用。

## 验收证据

| 验收项 | 证据 |
| ------ | ---- |
| 无 Key 模板模式可运行 | `tests/test_autonomous_development_loop.py` |
| 从干净临时目录执行 | `workspace_strategy=tempfile.TemporaryDirectory` |
| 至少一次成功编译和测试 | 第二次 `py_compile` exit code 0，运行测试 exit code 0 |
| 可控失败-修复演示 | 第一次 `py_compile` exit code 1，修复后成功 |
| 最多两轮修复 | `max_fix_attempts=2`，实际 `fix_attempts=1` |
| 命令白名单 | `_validate_command` 限制 Python 编译和执行生成文件 |
| 不影响三种 primitive | CTest 和完整 Python 回归仍需作为阶段闸门验证 |

## 未验证边界

- 该闭环是最小离线演示，不代表真实 LLM 自动开发能力。
- 未执行真实 C/C++ 代码生成到生产目录。
- 未调用真实编译器修复大型 C 工程错误。
- 未接入 DeepSeek、OpenAI 或其他外部模型。
