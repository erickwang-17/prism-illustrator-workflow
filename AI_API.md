# Optional API assistance · v0.4

**English** | [简体中文](AI_API.zh-CN.md)

**New users are encouraged to configure the optional API before complex tasks.** It can suggest diagnoses, missing information and next steps for design, data, fonts and layout. Routine analysis remains offline; advice cannot invent data or convert failed checks to success.

## 1. Configure a provider

Install this project first. API commands use only the standard library; scientific analysis still requires `.[science]`.

```sh
figureflow ai-setup --model YOUR_MODEL_ID
```

Replace the model placeholder with an ID available to your provider account. The default creates ignored `local/ai-config.json`, using `https://api.openai.com/v1` and Responses. It stores no key, makes no request and refuses to overwrite existing files.

For another compatible provider:

```sh
figureflow ai-setup --config local/provider.json \
  --base-url https://YOUR_PROVIDER_HOST/v1 \
  --protocol chat_completions --model YOUR_MODEL_ID \
  --chat-token-parameter max_tokens
```

The URL is a placeholder. Supply the provider's HTTPS API base; the program appends `/responses` or `/chat/completions`. Chat defaults to `max_completion_tokens`; choose `max_tokens` only when required. Errors never trigger automatic parameter/model substitution. Support covers basic text requests, not every feature or every provider advertising compatibility.

## 2. Set a local key and check configuration

The default key variable is `FIGUREFLOW_API_KEY`. Do not send keys in chat, JSON, command arguments or GitHub commits.

On macOS zsh, hidden input avoids putting the key in command history:

```zsh
read -rs 'FIGUREFLOW_API_KEY?API key: '
export FIGUREFLOW_API_KEY
printf '\n'
figureflow ai-doctor
```

For Bash, use `read -rs -p 'API key: ' FIGUREFLOW_API_KEY`, then export. The variable lasts for that shell and its children. Set it again after closing the shell or use your own key manager; do not put real values in startup files. `--api-key-env OPENAI_API_KEY` selects an existing variable by name.

`ai-doctor` checks local configuration and key presence only, reporting `live_api_verified=false`. It does not check permissions, credit or connectivity and incurs no API charge.

## 3. Review a request, then send it

```sh
figureflow ai-prepare \
  --problem 'The same device is measured repeatedly with missing observations. How should I choose and validate a model?' \
  --out local/request.json

figureflow ai-ask local/request.json
# Review the endpoint, model and full request before sending:
figureflow ai-ask local/request.json --send --out local/advice.json
```

For additional context, write a reviewed plain-text summary and explicitly attach it with `ai-prepare --context local/reviewed-summary.txt`. The program does not scan directories or automatically read data, Prism/AI files, chats or logs. The entire context is sent: key substitution is not anonymization. Review all text. Input is limited to 16,000 characters. Questions may be written in Chinese or English.

Without `--send`, `ai-ask` only previews and needs no key. With it, one potentially billable call is made. Configuration/request fingerprints prevent silently sending a reviewed request to a different endpoint or model; re-prepare after relevant configuration or payload changes. Keep previews in ignored directories because they may contain private content.

For initial live verification, use a synthetic question such as “How can I check a scatter plot's units and sample counts?” Inspect `advice`, `incomplete` and `usage`. Mocked tests and synthetic keys do not verify your live provider.

## 4. Request one suggestion after an analysis failure

```sh
figureflow analyze local/analysis.json --output-dir local/new-run \
  --ai-help --ai-config local/ai-config.json --error-format json
```

This explicitly enables one request only if analysis fails. Successful analysis never calls the API; there is no background loop. The payload contains only a fixed error category, such as missing paired IDs, unsupported design or text outside the canvas. It excludes source values, paths, labels and raw exception text. Use manual mode for necessary detail.

Analysis still fails with exit code 2. `ai_advice` in stderr JSON remains advisory; API failure preserves the original error and adds `ai_assistance_error`. Without `--ai-help`, failure handling stays offline and only suggests setup/help commands.

1. Preserve the original error/data version and identify whether information, functionality or formatting is missing.
2. Review the diagnosis, basis, next steps and validation conditions. Confirm unknown facts with the data provider.
3. Make a working copy and test proposed changes. Method changes need design justification and authorization; never choose a test by star count.
4. Repeat the original checks, numerical validation and visual review before declaring resolution.

Model output is untrusted advice. The program does not execute shell/Python, tool calls or edits from it. It requests reviewable reasoning summaries and steps, not private chain-of-thought. AI advice cannot be passed to `summary` as successful analysis evidence.

## Configuration and resource limits

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

- One request, no automatic retries. HTTP 401/403/404/429, TLS/timeouts, invalid JSON, refusals and tool-execution requirements are reported.
- HTTPS verification stays enabled; redirects cannot forward keys. Credentials, query strings and fragments are forbidden in the base URL. Python/system proxy configuration applies; users manage proxy trust.
- I/O timeout: 1–60 seconds. Output: 256–8,192 tokens. Response body: at most 1 MiB. Token limits are not monetary budgets and may include invisible reasoning usage; provider billing settings apply.
- Truncation sets `incomplete=true`. Reports record request hashes, model, protocol and available usage, without credentials.
- Requests use `store=false`; this is not a zero-retention guarantee or a substitute for provider policy. A provider rejecting that field produces an error requiring compatibility review against its documentation.
- No task images, web search, tool execution, automatic patches, long-term memory or conversation persistence are enabled. Each request is independent.

Implemented against official [Responses](https://developers.openai.com/api/reference/resources/responses/methods/create) and [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) documentation. Actual access, pricing and availability depend on the provider and account.
