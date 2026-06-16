# DeepSeek API Setup

本文档说明如何配置 DeepSeek API 以便 HCCL Agent 使用 LLM 推理能力。

## 方式一：环境变量（推荐）

```bash
export DEEPSEEK_API_KEY=sk-your-api-key-here
```

持久化配置（添加到 `~/.bashrc` 或 `~/.zshrc`）：

```bash
echo 'export DEEPSEEK_API_KEY=sk-your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

## 方式二：.env 文件

在项目根目录创建 `.env` 文件（已被 `.gitignore` 排除，不会提交到仓库）：

```
DEEPSEEK_API_KEY=sk-your-api-key-here
```

在运行 Agent 前加载：

```bash
export $(grep -v '^#' .env | xargs)
python3 main.py --nodes 8 --message-size 128
```

## 获取 API Key

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册 / 登录
3. 在 API Keys 页面创建新 Key
4. 复制 Key（以 `sk-` 开头）

## 验证配置

```bash
python3 -c "
from agent.llm_client import LLMClient
client = LLMClient()
print(client.ask('Say hello in one word.'))
"
```

预期输出：模型返回的问候语。

## 注意事项

- API Key 是敏感信息，**不要** hard-code 到源代码中
- `.env` 文件已在 `.gitignore` 中排除
- 未设置 API Key 时 Agent 仍可正常运行（LLM 推理步骤静默跳过，规则系统照常工作）
- DeepSeek API 使用 OpenAI 兼容接口，`agent/llm_client.py` 不依赖任何第三方 SDK
