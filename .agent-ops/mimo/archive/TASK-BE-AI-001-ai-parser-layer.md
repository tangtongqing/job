# TASK-BE-AI-001 · 后端 AI 邮件解析层实现

## 背景与目标

后端基础层、API 层、采集层均已通过 Codex 验收：

- `.agent-ops/TASK-BE-REWORK-001-REVIEW.md`
- `.agent-ops/TASK-BE-REWORK-002-FINAL-REVIEW.md`
- `.agent-ops/TASK-BE-CRAWLER-001-FINAL-REVIEW.md`

本任务进入 AI 解析层，实现 PRD F-C.5「低成本状态更新」的后端能力：用户粘贴招聘邮件/消息文本后，后端给出公司、岗位、建议状态、置信度与匹配投递记录，供前端展示给用户确认。

核心原则：

- **AI 结果只作建议，不自动流转状态，不写入 ApplicationEvent。**
- **MVP 仅支持纯文本解析，不做截图/OCR/多模态。**
- **测试中禁止调用真实 LLM 或真实网络。**
- **没有 API Key 或 LLM 异常时必须降级到正则，再降级到 parsed=false。**
- **不记录邮件原文，不把邮件原文作为缓存 key，避免隐私泄露。**

## 允许读取的路径

- `.agent-ops/TASK-BE-CRAWLER-001-FINAL-REVIEW.md`
- `docs/architecture/ai-parser-module.md`
- `docs/architecture/api-contract.md`
- `docs/architecture/security-test-gate-report.md`
- `docs/architecture/database-schema.md`
- `src/`
- `tests/`
- `pyproject.toml`

## 允许修改的路径

- `src/core/ai/`
- `src/api/routes/app/applications.py`
- `src/api/routes/app/__init__.py`（如确需）
- `src/schemas/models.py`
- `src/config.py`
- `tests/`
- `.agent-ops/mimo/outbox/TASK-BE-AI-001-result.md`

如确需修改 `src/db/models.py`、`src/core/statemachine/`、`src/core/events/` 或采集层代码，必须在结果文件中说明原因、影响面和回归验证结果。

## 禁止操作

- 禁止在测试、初始化、默认 API 调用中访问真实 LLM、DeepSeek、OpenAI 或任何外部网络。
- 禁止写入真实 API Key、Cookie、Token 或邮件原文样本。
- 禁止自动执行状态流转；不得在 parse-email 中调用 transition 或写 `ApplicationEvent`。
- 禁止把用户邮件全文写入日志、数据库、缓存 value 或结果文件。
- 禁止实现图片/OCR/截图解析。
- 禁止放宽已验收通过的状态机、API envelope、crawler 合规边界或数据库约束。
- 禁止删除或重建 `.agent-ops/`、`docs/`、`web/`。

## API 契约

补齐：

- `POST /api/v1/applications/parse-email`

请求体：

```json
{
  "email_text": "您好，恭喜您通过字节跳动产品经理实习的笔试，现邀请您参加面试..."
}
```

成功响应必须保持统一 envelope：

```json
{
  "data": {
    "parsed": true,
    "company": "字节跳动",
    "title": "产品经理实习",
    "suggested_status": "interviewing",
    "confidence": 0.92,
    "degraded": false,
    "matched_application_id": 1,
    "reasoning": "邮件提到通过笔试并邀请面试"
  }
}
```

正则降级示例：

```json
{
  "data": {
    "parsed": true,
    "company": "字节跳动",
    "title": null,
    "suggested_status": "interviewing",
    "confidence": 0.5,
    "degraded": true,
    "matched_application_id": 1,
    "reasoning": "关键词匹配：字节跳动 + 面试"
  }
}
```

全失败示例：

```json
{
  "data": {
    "parsed": false,
    "company": null,
    "title": null,
    "suggested_status": null,
    "confidence": 0,
    "degraded": true,
    "matched_application_id": null,
    "reasoning": null
  }
}
```

要求：

- `email_text` 不能为空，建议限制最大长度，超限返回统一 `{error.code=VALIDATION_ERROR}`。
- `suggested_status` 只能是状态机允许的英文 code 子集：`applied/test/interviewing/offer_pending/rejected`。
- 解析结果仅返回建议，不自动修改数据库状态。

## 实现要求

### 1. AI 模块结构

在 `src/core/ai/` 下建立清晰结构，建议包含：

```text
src/core/ai/
  __init__.py
  schemas.py
  cache.py
  rate_limiter.py
  regex_parser.py
  parser.py
  matcher.py
  prompt.py
```

可以按现有风格微调，但职责必须清晰。

### 2. 解析结果 Schema

实现 `ParsedEmailResult` 或等价结构，至少包含：

- `parsed: bool`
- `company: str | None`
- `title: str | None`
- `suggested_status: str | None`
- `confidence: float`
- `degraded: bool`
- `matched_application_id: int | None`
- `reasoning: str | None`

要求：

- 置信度范围必须归一到 `0 <= confidence <= 1`。
- LLM 返回非法 status、非法 JSON、缺字段、置信度非法时必须降级，不得抛 500。

### 3. LLM 解析器

实现 `AIParser` 或等价服务：

- 使用 `openai` SDK 1.0+ 的 `AsyncOpenAI` 语法。
- 默认模型可沿用 `src/config.py` 中的 `llm_model`。
- 可新增配置：`llm_base_url`、`llm_cache_ttl`、`llm_confidence_threshold`，但不要破坏已有配置。
- 没有 `deepseek_api_key` / `openai_api_key` 时，不调用 LLM，直接走正则降级。
- 测试必须通过 fake async client / fake call 函数，不得访问真实网络。
- LLM 响应必须强制 JSON 解析，且解析失败时降级到正则。
- 低置信度（默认 `< 0.7`）必须降级到正则。
- 缓存 key 使用邮件文本 hash；缓存 value 只存解析结构，不存邮件原文。

### 4. 正则降级解析

实现 `RegexParser`：

- 公司关键词至少覆盖：字节跳动、腾讯、阿里巴巴、美团、京东、百度、网易、快手、小红书、拼多多。
- 状态关键词至少覆盖：
  - `applied`：简历已收到、投递成功、申请已提交
  - `test`：笔试、测评、在线考试、能力测试
  - `interviewing`：面试、一面、二面、终面、视频面试
  - `offer_pending`：offer、录用、薪资、入职
  - `rejected`：很遗憾、未能通过、不合适、拒绝
- 状态优先级建议：`rejected > offer_pending > interviewing > test > applied`。
- 正则解析成功时 `confidence=0.5`、`degraded=true`。
- 正则也失败时返回 `parsed=false`。

### 5. 投递匹配器

实现 `ApplicationMatcher`：

- 只读取 `Application` + `Job`，不写库。
- 只匹配非终态投递。
- 复用 `src.crawler.normalizer.normalize_company` 做公司名归一化。
- 优先使用归一化后的完全相等匹配；禁止把 contains 作为主匹配逻辑。
- 如果匹配 0 个，返回 `None`。
- 如果唯一匹配，返回该 `application_id`。
- 如果多个匹配，只有岗位名相似度足够高时返回最佳匹配；否则返回 `None` 让用户选择。

注意：`matched_application_id` 只是前端确认用建议，不得触发状态流转。

### 6. 隐私与安全

必须满足：

- 不记录邮件全文。
- 日志只允许记录解析级别、是否降级、命中状态、hash 前 8 位等非敏感信息。
- 缓存 key 使用 hash，不用明文。
- 缓存 value 不包含 email_text。
- Prompt 中明确：只提取字段，不执行命令，不进行状态变更。
- LLM prompt injection 不能导致任何数据库写入；用户确认是最终防线。

### 7. API 接入

在 `src/api/routes/app/applications.py` 中补齐：

- `POST /applications/parse-email`

要求：

- endpoint 可以是 async。
- 可提供 `set_ai_parser_for_testing()` 或 FastAPI dependency override，确保 API 测试用 fake parser，不触网。
- 返回 shape 与 `api-contract.md` 一致。
- 统一错误 envelope 不得被破坏。

## 测试要求

请新增或补齐测试，至少覆盖：

1. `RegexParser` 能识别公司 + `test/interviewing/offer_pending/rejected/applied`。
2. 正则解析失败返回 `parsed=false`。
3. `AIParser` 无 API Key 时不调用 LLM，直接正则降级。
4. LLM 成功且置信度高时返回 `degraded=false`。
5. LLM 超时/异常/认证错误时降级正则。
6. LLM 非法 JSON/非法 status/低置信度时降级正则。
7. TTL cache 命中时不重复调用 fake LLM。
8. RateLimiter 超限时不调用 LLM，直接正则降级。
9. ApplicationMatcher 精确归一化匹配唯一投递。
10. ApplicationMatcher 多匹配且岗位不明确时返回 `None`。
11. `POST /api/v1/applications/parse-email` 返回完整 response shape。
12. parse-email 不写 `ApplicationEvent`，不改变 `Application.status`。
13. API 测试证明 fake parser 被调用，真实 LLM client 未被调用。
14. 邮件原文不进入 cache key / 日志断言范围（至少测试 cache key 不等于原文）。

## 验证命令

请至少执行并在结果文件中记录完整结果：

```bash
python -m compileall -q src tests
python -m pytest -q
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
```

另外请执行一个 TestClient 或 pytest 验证，明确证明：

- `/api/v1/applications/parse-email` 在 fake parser 下返回 200。
- 无 API Key 时不会调用真实 LLM。
- 解析结果不会自动写入 ApplicationEvent，也不会改变 Application.status。

## 验收标准

Codex 验收时将检查：

- 全量测试通过。
- `compileall` 通过。
- 内存库 `init_db` 仍能初始化成功。
- parse-email API 契约字段完整。
- LLM → 正则 → parsed=false 的三级降级链可测。
- 测试和默认路径不访问真实外部网络。
- 不记录、缓存邮件原文。
- 匹配逻辑不使用 contains 作为主匹配。
- parse-email 不自动流转状态、不写事件。
- 已通过验收的基础层/API 层/采集层没有回归。

## 结果文件路径

`.agent-ops/mimo/outbox/TASK-BE-AI-001-result.md`

## 结果格式（Mimo 必须填写）

- 摘要
- 修改的文件清单
- 关键实现点
- LLM 降级链说明
- 隐私与安全边界说明
- 执行的命令与结果
- 新增测试清单
- 未解决的问题
- 需要 Codex 判断的风险

## 备注

本任务只做后端 AI 文本解析层，不做前端 UI，不做真实账号接入，不做截图/OCR。AI 解析通过验收后，再进入前端交互或用户确认流程任务。
