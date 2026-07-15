# TASK-BE-CRAWLER-001 · 后端采集层基础设施实现

## 背景与目标

Codex 已完成后端基础层与 API 层验收，结论见：

- `.agent-ops/TASK-BE-REWORK-001-REVIEW.md`
- `.agent-ops/TASK-BE-REWORK-002-FINAL-REVIEW.md`

当前后端 API 层已达到「可进入采集层 / AI 层」标准。本任务进入 Stage 2 的采集模块落地，目标是实现一个**合规优先、可测试、可扩展**的采集层基础设施，而不是直接进行真实站点大规模抓取。

重点要求：

- 采集必须默认低风险、默认不触网或可控触网，测试中禁止依赖真实外部网站。
- robots.txt 必须 fail-closed；无法确认允许时不得抓取。
- BOSS / 牛客等站点只做合规骨架与安全降级，不做登录、验证码绕过、反爬绕过。
- 采集结果必须先规范化，再去重/合并，避免重复写入职位。
- 采集任务必须写入 `CrawlLog`，便于后续验收与后台展示。

## 允许读取的路径

- `.agent-ops/TASK-BE-REWORK-001-REVIEW.md`
- `.agent-ops/TASK-BE-REWORK-002-FINAL-REVIEW.md`
- `docs/architecture/crawler-module.md`
- `docs/architecture/security-test-gate-report.md`
- `docs/architecture/api-contract.md`
- `docs/architecture/database-schema.md`
- `src/`
- `tests/`
- `pyproject.toml`

## 允许修改的路径

- `src/crawler/`
- `src/api/routes/app/crawler.py`
- `src/api/routes/app/jobs.py`（仅用于补齐 `POST /jobs/{id}/verify`，如已有实现则不要重写）
- `src/api/routes/app/__init__.py`
- `src/main.py`（仅用于挂载 crawler 路由或 scheduler 生命周期）
- `src/schemas/models.py`（仅用于新增/补齐 crawler API schema）
- `config/sources.yaml`
- `config/sources.example.yaml`
- `tests/`
- `.agent-ops/mimo/outbox/TASK-BE-CRAWLER-001-result.md`

如确需修改 `src/db/models.py`、`src/db/init_db.py` 或已通过验收的 API 语义，必须在结果文件中说明原因、影响面和回归验证结果。

## 禁止操作

- 禁止真实登录招聘网站、绕过验证码、绕过反爬、使用代理池或任何规避访问控制的手段。
- 禁止在测试中访问真实 BOSS、牛客、公司官网或其他外部网站。
- 禁止 robots.txt 读取失败后默认允许抓取。
- 禁止写入真实账号、Cookie、Token、API Key 或任何私密信息。
- 禁止采集、存储 HR 私人联系方式、候选人隐私、聊天内容等非岗位公开信息。
- 禁止为通过测试而放宽已经验收通过的状态机、事件、API envelope 或数据库约束。
- 禁止删除或重建 `.agent-ops/`、`docs/`、`web/`。

## 实现要求

### 1. 采集模块结构

在 `src/crawler/` 下建立清晰结构，建议包含：

```text
src/crawler/
  adapters/
    base.py
    company.py
    boss.py
    nowcoder.py
    factory.py
  compliance/
    robots.py
    rate_limiter.py
    retry.py
  normalizer.py
  dedup.py
  service.py
  scheduler.py
  verifier.py
```

可以根据现有代码风格微调，但必须保持职责清晰。

### 2. Adapter 基类与安全适配器

实现 `BaseAdapter`：

- 初始化不得发生真实网络请求。
- HTTP client 必须 lazy 创建，并提供 `close()`。
- 至少暴露 `should_crawl()`、`fetch()`、`parse()`、`crawl()` 或等价方法。
- 支持注入 fake client / fake fetcher，方便测试不触网。

实现三个适配器骨架：

- `CompanyWebsiteAdapter`
- `BossAdapter`
- `NowcoderAdapter`

验收重点不是抓取真实页面数量，而是：

- 公司官网适配器可以解析本地 HTML / fixture / fake response，产出规范化岗位数据。
- BOSS / 牛客适配器遇到验证码、登录页、403、robots 禁止时必须安全跳过或失败记录，不得尝试绕过。
- Playwright 如未安装，不得导致整个测试套件失败；对应能力应降级为 skipped / unavailable。

### 3. 合规控制

实现 robots 与限频基础能力：

- robots.txt 读取失败、超时、解析失败时默认 forbid，并记录原因。
- 支持显式 manual override，但必须由配置开启，默认关闭。
- 每个 source 独立限频，避免全局互相影响。
- retry/backoff 必须可测试，支持注入 sleeper/random，测试中不得真实长时间 sleep。

### 4. 配置文件

新增 `config/sources.yaml` 或 `config/sources.example.yaml`，建议结构：

```yaml
global:
  crawl_interval_minutes: 60
  max_concurrent: 2
  batch_size: 20
  manual_robots_override: false

sources:
  company_website:
    enabled: true
    adapter: company
    base_urls: []
  boss:
    enabled: false
    adapter: boss
  nowcoder:
    enabled: false
    adapter: nowcoder
```

要求：

- 高风险来源默认 `enabled: false`。
- 配置缺失时应有安全默认值。
- 不要在配置中写入真实 Cookie / Token。

### 5. 采集服务与日志

实现 `CrawlService` 或等价服务，核心流程建议为：

1. 根据 source 创建 adapter。
2. 调用 `should_crawl()`；如不允许，写入 `CrawlLog(status='skipped')`。
3. fetch + parse 得到岗位原始数据。
4. 规范化 company/location/category/requirement 等字段。
5. 去重/合并后批量写入 `Job`。
6. 成功写入 `CrawlLog(status='success', count=N)`。
7. 异常写入 `CrawlLog(status='failed', error=...)`。
8. 无论成功失败都必须 `adapter.close()`。

要求：

- 批量提交默认 20 条，可配置。
- 单批失败时不得造成数据库会话悬空。
- 日志字段使用既有 `CrawlLog` 模型；不要随意改数据库 schema。

### 6. 规范化与去重

实现 normalizer，至少覆盖：

- `normalize_location`
- `normalize_company`
- `extract_graduation_year`
- `extract_education`
- `extract_experience`
- `classify_job`

实现 dedup/merge：

- 同来源去重：优先使用 `(source, company, title, location)` 的规范化精确匹配。
- 跨来源去重：只能在 normalized company/title/location 精确相等时合并；禁止使用 contains/substring 作为合并依据。
- 合并时只补齐缺失字段，例如 `salary`、`requirement`、`deadline`、`source_url`，不得覆盖已有更可靠字段。

### 7. 岗位有效性验证

实现 `verify_job` 或等价能力：

- 支持通过可注入 client/fetcher 检查岗位链接，不在测试中触网。
- 无效岗位应设置 `is_valid=False`、`status='closed'`、`last_verified_at=当前时间`。
- 有效岗位应更新 `last_verified_at`，保持 `is_valid=True`。
- `status` 使用数据库约束允许的英文 code，不要写中文状态。

如 API 尚未实现，补齐：

- `POST /api/v1/jobs/{id}/verify`

响应必须保持现有统一 envelope：成功 `{data: ...}`，错误 `{error: ...}`。

### 8. Crawler API

补齐最小可用 crawler API：

- `POST /api/v1/crawler/trigger`
- `GET /api/v1/crawler/logs`

要求：

- trigger 支持指定 source；未指定时可按配置触发 enabled sources。
- API 测试中必须使用 fake adapter/source，不得触网。
- logs 支持分页或 limit 参数，返回最近采集日志。
- 响应结构保持 API 层已验收的 `{data, meta?}` / `{error}` envelope。

### 9. Scheduler

实现 scheduler 基础结构即可：

- 可以使用 APScheduler 或轻量自有封装。
- 不要求测试中真实启动后台循环。
- 如挂载 FastAPI lifespan，必须保证测试环境不会产生不可控后台任务。
- 应支持按配置注册 source 的 interval job。

## 测试要求

请新增或补齐测试，至少覆盖：

1. robots 读取失败时 fail-closed；manual override 开启时才允许。
2. rate limiter 按 source 独立工作，测试不真实长时间 sleep。
3. retry/backoff 可注入 sleeper，失败重试次数与最终异常可断言。
4. normalizer 对城市、公司后缀、学历、经验、毕业年份、岗位分类的基本提取。
5. 同来源重复岗位不重复写入。
6. 跨来源 exact normalized match 才合并；substring/contains 不得误合并。
7. `crawl_source` success/skipped/failed 都写入 `CrawlLog`，并确保 adapter 被 close。
8. 批量写入按 batch size 工作，重复项合并不破坏已有数据。
9. `verify_job` 对有效/无效岗位正确更新 `is_valid/status/last_verified_at`。
10. `POST /api/v1/crawler/trigger` 使用 fake adapter 返回成功 envelope。
11. `GET /api/v1/crawler/logs` 返回日志列表。
12. `POST /api/v1/jobs/{id}/verify` 不触网地完成验证。

## 验证命令

请至少执行并在结果文件中记录完整结果：

```bash
python -m compileall -q src tests
python -m pytest -q
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
```

另外请执行一个 TestClient 或 pytest 验证，明确证明：

- `POST /api/v1/crawler/trigger` 在 fake source 下返回 200 且写入 CrawlLog。
- `GET /api/v1/crawler/logs` 能读到刚写入的日志。
- robots unreadable 时不会触发抓取，日志为 skipped 或 failed。
- `POST /api/v1/jobs/{id}/verify` 使用 fake verifier 时不触网且更新字段正确。

## 验收标准

Codex 验收时将检查：

- 全量测试通过。
- `compileall` 通过。
- 内存库 `init_db` 仍能初始化成功。
- 采集模块职责清楚，不把真实站点访问写死到测试路径。
- robots 合规为 fail-closed。
- BOSS / 牛客无登录、验证码绕过或反爬规避逻辑。
- 去重/合并只基于规范化后的精确匹配，不使用 contains 误合并。
- `CrawlLog` 对 success/skipped/failed 都有可验收记录。
- `verify_job` 使用英文状态 code，并更新 `last_verified_at`。
- crawler API 维持统一响应 envelope。
- 已通过验收的基础层/API 层核心行为没有回归。

## 结果文件路径

`.agent-ops/mimo/outbox/TASK-BE-CRAWLER-001-result.md`

## 结果格式（Mimo 必须填写）

- 摘要
- 修改的文件清单
- 关键实现点
- 合规与安全边界说明
- 执行的命令与结果
- 新增测试清单
- 未解决的问题
- 需要 Codex 判断的风险

## 备注

本任务是采集层基础设施任务，不是 AI 解析层任务。不要接入真实 LLM，不要新增 API Key 配置。采集层验收通过后，再进入 AI 解析/摘要/岗位匹配能力。
