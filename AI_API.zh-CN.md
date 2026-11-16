# 可选 API 辅助 · v0.4

[English](AI_API.md) | **简体中文**

**建议新用户先配置 API，再开始复杂任务。** 它可以在分析设计、数据格式、字体和排版问题上提供诊断、缺失信息清单和解决建议。常规分析仍能完全离线运行；API 不负责凭空补数据或把失败结果改成成功。

## 1. 建立配置

先安装本项目。API 功能只使用 Python 标准库；科学分析仍需 `.[science]`。

```sh
figureflow ai-setup --model YOUR_MODEL_ID
```

把 `YOUR_MODEL_ID` 换成你的服务商实际提供且账号可访问的模型 ID。默认配置创建到被 Git 忽略的 `local/ai-config.json`，使用 `https://api.openai.com/v1` 和 Responses 协议。配置不保存密钥、不联网、不覆盖已有文件。

其他兼容服务商可以明确指定：

```sh
figureflow ai-setup --config local/provider.json \
  --base-url https://YOUR_PROVIDER_HOST/v1 \
  --protocol chat_completions --model YOUR_MODEL_ID \
  --chat-token-parameter max_tokens
```

URL 示例不是实际服务地址。应使用服务商的 HTTPS API 基础地址，程序追加 `/responses` 或 `/chat/completions`。Chat Completions 默认用 `max_completion_tokens`；只有服务商要求旧参数时才选择 `max_tokens`，不会因报错自动换模型或换参数。实现了这两种协议的基础文本子集，不保证每个标为“兼容”的服务商都接受所有字段。

## 2. 在本机设置密钥并检查

密钥默认从 `FIGUREFLOW_API_KEY` 环境变量读取。不要把密钥发给聊天助手、填进 JSON、作为命令参数或提交 GitHub。

macOS 默认 zsh 可使用隐藏输入，避免把密钥正文写入命令历史：

```zsh
read -rs 'FIGUREFLOW_API_KEY?API key: '
export FIGUREFLOW_API_KEY
printf '\n'
figureflow ai-doctor
```

Bash 对应 `read -rs -p 'API key: ' FIGUREFLOW_API_KEY`，然后 export。环境变量只对这个 shell 及子进程有效；关闭 shell 后需要重新设置，或使用你自己的密钥管理器。不要将真实值写进 shell 启动文件。也可通过 `--api-key-env OPENAI_API_KEY` 指定已有的密钥变量名。

`ai-doctor` 只检查配置及密钥是否存在，报告 `live_api_verified=false`；它不会验证模型权限、余额或真实连通性，也不会发起收费请求。

## 3. 手动请求建议：先预览，再发送

```sh
figureflow ai-prepare \
  --problem '同一设备在多个时间点重复测量，还有缺失值，应如何选择模型和验证？' \
  --out local/request.json

figureflow ai-ask local/request.json
# 阅读输出中的 endpoint、model 与完整请求正文后：
figureflow ai-ask local/request.json --send --out local/advice.json
```

需要更多信息时，先自行写一份不含敏感信息的纯文本摘要，用 `ai-prepare --context local/reviewed-summary.txt` 明确附加。程序不会扫描项目目录或自动读取数据表、Prism/AI 文件、聊天记录和日志。`--context` 的全文会进入请求，密钥替换机制不等于匿名化：发送前仍须核对全文。输入上限 16,000 字符。

`ai-ask` 不加 `--send` 时只预览，甚至不需要密钥。加 `--send` 才发送一次可能计费的调用。请求与配置用指纹绑定；改变服务地址、模型、限制或请求结构后需重新准备，防止无意把已审阅请求送到另一个服务。预览文件可以包含私有信息，始终放在忽略目录。

首次真实验证建议只发“请简述如何核对一张散点图的单位和样本量”这样的合成问题。成功后检查 `advice`、`incomplete` 和 `usage`。测试框架使用模拟服务响应和合成密钥，不代表已替用户完成真实服务验证。

## 4. 分析失败时自动请求一次建议

```sh
figureflow analyze local/analysis.json --output-dir local/new-run \
  --ai-help --ai-config local/ai-config.json --error-format json
```

只有此次分析失败才调用。这个标志明确启用一次 API 请求；成功分析不调用，也没有后台循环。发送内容仅包含固定错误类别，例如“配对 ID 不齐”“不支持的设计”“文字超出画布”，不附带源数据、路径、标签或原始报错。详细问题请用手动模式整理必要背景。

原分析仍以退出码 2 失败，stderr JSON 中的 `ai_advice` 只是建议。如果 API 自身失败，保留原分析错误，再附上 `ai_assistance_error`。不加 `--ai-help` 时绝不联网，只给配置/求助提示。

建议的实际处理顺序：

1. 保存原始错误和数据版本，明确缺失的是数据、设计信息、软件功能还是格式设置。
2. 审阅 API 的诊断、建议依据、下一步和验证条件；未知信息先向数据提供者确认。
3. 对可执行的修改先做工作副本和测试。改变统计方法必须有设计依据及授权；不根据星号数量选检验。
4. 重新运行原检查、数值验证与视觉核验。只有这些检查实际通过，才认定问题解决。

模型返回内容视为不可信建议，程序不执行其中的 shell/Python、工具调用或文件修改。也不请求或保存模型的私有思维链；要求的是可审阅的结论依据与操作步骤。AI 建议不能传给 `summary` 冒充分析通过证据。

## 配置与资源限制

完整配置字段：

```json
{
  "schema_version": 1,
  "base_url": "https://api.openai.com/v1",
  "protocol": "responses",
  "model": "YOUR_MODEL_ID",
  "api_key_env": "FIGUREFLOW_API_KEY",
  "timeout_seconds": 30,
  "max_output_tokens": 2048,
  "chat_token_parameter": "max_completion_tokens"
}
```

- 每次最多一次请求，不自动重试；401/403/404/429、TLS/超时、非法 JSON、拒绝或工具执行要求会明确报告。
- HTTPS 校验开启，禁止重定向转发密钥；URL 不允许账号密码、查询参数或片段。网络代理按 Python/系统配置工作，代理信任由用户管理。
- I/O 超时可设 1–60 秒；输出上限 256–8,192 tokens；响应体上限 1 MiB。tokens 限制不是货币预算，也可能包含模型不可见的推理用量；费用和额度按服务商设置。
- 返回文本被截断会标记 `incomplete=true`；不能当作完整方案。记录请求哈希、模型、协议和可用的用量字段，凭据不进入报告。
- 请求设置 `store=false`，但这不承诺零保留，也不能替代服务商的数据政策。兼容服务商若拒绝该字段，调用会报错，需要按其官方文档评估兼容性。
- 未发送任务图片、未启用联网搜索、工具执行、自动代码补丁、长期记忆或跨次对话状态；每次请求独立。

接口按官方 [Responses](https://developers.openai.com/api/reference/resources/responses/methods/create) 和 [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) 文档实现。服务商、模型权限、计费和可用功能可能变化，以实际服务为准。
