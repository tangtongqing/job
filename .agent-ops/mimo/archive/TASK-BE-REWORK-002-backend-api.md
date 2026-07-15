# TASK-BE-REWORK-002 · 后端 API 层契约返工修复

## 背景与目标

Codex 已完成对 `.agent-ops/TASK-BACKEND-API-REPORT.md` 的验收，结论见：

- `.agent-ops/TASK-BACKEND-API-REVIEW.md`

验收结论为：**不通过，暂不建议进入采集层 / AI 层**。

本任务目标是修复 API 层与 `docs/architecture/api-contract.md` 的契约偏差，尤其是：

- `GET /api/v1/dashboard/distribution` 当前 500。
- Dashboard 四端点响应结构和统计口径不符合契约。
- FastAPI 参数/body 校验错误没有统一 `{error}` envelope。
- 非法 `to_status` 未按契约返回 `VALIDATION_ERROR`。
- `batch-transition` 响应字段和每条独立事务语义不符合契约。
- application detail / transition / todo / jobs stats / JobOut 字段存在契约缺口。

返工完成后，API 层应达到「可进入采集层 / AI 层」标准。

## 允许读取的路径

- `.agent-ops/TASK-BACKEND-API-REVIEW.md`
- `.agent-ops/TASK-BACKEND-API-REPORT.md`
- `.agent-ops/TASK-BE-REWORK-001-REVIEW.md`
- `docs/architecture/api-contract.md`
- `docs/architecture/database-schema.md`
- `docs/product/PRD.md`
- `src/`
- `tests/`
- `pyproject.toml`

## 允许修改的路径

- `src/main.py`
- `src/api/responses.py`
- `src/api/routes/app/jobs.py`
- `src/api/routes/app/applications.py`
- `src/api/routes/app/dashboard.py`
- `src/api/routes/app/todo.py`
- `src/schemas/models.py`
- `src/core/statemachine/engine.py`（仅当 transition 需要返回事件或更稳定地定位事件时可小修）
- `src/core/events/service.py`（仅当 todo / funnel 需要小修，不允许破坏地基验收通过项）
- `tests/`
- `.agent-ops/mimo/outbox/TASK-BE-REWORK-002-result.md`

## 禁止操作

- 不进入采集层实现，不新增爬虫适配器、调度器或真实网络采集。
- 不进入 AI 解析层实现，不接入真实 LLM / API Key。
- 不做前端 UI 修改。
- 不删除或重建 `docs/`、`.agent-ops/`、`web/`。
- 不为了让测试通过而放宽状态机、数据库 CHECK 约束或部分唯一索引。
- 不改变已通过的后端地基语义：状态机合法流转、纠错、待办 `occurred_at IS NULL`、事件服务事务边界必须保持。
- 不绕开统一响应契约；成功响应必须 `{data, meta?}`，错误响应必须 `{error}`。

## 实现要求

### 1. 修复 `/dashboard/distribution` 500（P0）

修复 `src/api/routes/app/dashboard.py` 中 `Select` 对象误调用 `.all()` 的问题。

验收要求：

- `GET /api/v1/dashboard/distribution?dimension=job_category` 返回 200。
- 不再出现 `AttributeError: 'Select' object has no attribute 'all'`。
- 新增测试覆盖该端点非空数据和空数据。

### 2. 统一 Dashboard 四端点契约（P1）

对照 `docs/architecture/api-contract.md` 模块 B。

#### `GET /dashboard/kpi`

返回：

```json
{
  "data": {
    "today_new_jobs": 25,
    "total_jobs": 1500,
    "total_applications": 45,
    "pending_applications": 12,
    "by_status": {
      "applied": 8,
      "test": 2,
      "interviewing": 2
    }
  }
}
```

口径建议：

- `today_new_jobs`：当天 `Job.collected_at` 的岗位数。
- `total_jobs`：全部岗位数。
- `total_applications`：全部投递数。
- `pending_applications`：非终态投递数。
- `by_status`：按 `Application.status` 分组统计。

#### `GET /dashboard/funnel`

返回：

```json
{
  "data": {
    "funnel": [
      { "status": "applied", "count": 45, "rate": 1.0 },
      { "status": "test", "count": 20, "rate": 0.444 }
    ],
    "total_applications": 45
  }
}
```

要求：

- 返回对象，不要直接返回列表。
- 按状态机顺序输出：`applied -> test -> interviewing -> offer_pending -> offer_accepted`。
- `rate` = 当前阶段数量 / 上一阶段数量；第一个阶段为 `1.0`。
- 排除 correction 事件。
- API 创建投递时应有可用于漏斗和时间线的 `applied` 初始事件：`event_type=status_change, from_status=None, to_status=applied`。不要破坏 `python -m src.db.init_db` 仍输出 6 条事件的既有验收要求；可只在 API 创建投递路径写初始事件。

#### `GET /dashboard/trend`

返回：

```json
{
  "data": {
    "trend": [
      { "date": "2026-06-16", "count": 2 }
    ],
    "total": 9
  }
}
```

要求：

- 统计有效进展事件，而不是 `Application.applied_at`。
- 有效进展事件：`ApplicationEvent.event_type == status_change` 且 `to_status IN ('test', 'interviewing', 'offer_pending')` 且 `is_correction = false`。
- 支持 `days` 参数，默认按 api-contract 为 7 天；建议补齐 0 值日期，便于前端画折线。

#### `GET /dashboard/distribution`

返回：

```json
{
  "data": {
    "dimension": "job_category",
    "distribution": [
      { "label": "产品", "count": 15, "rate": 0.333 }
    ],
    "total": 45
  }
}
```

要求：

- 支持 `dimension=job_category/location/company_category`。
- `company_category` 可通过 `Job.company == Company.name` 关联 `Company.category`；没有匹配时归为 `"未分类"`。
- `rate` = count / total；total 为参与统计的投递总数。
- 非法 dimension 返回统一 `VALIDATION_ERROR`。

### 3. 统一请求校验错误响应（P1）

当前 FastAPI 参数校验返回默认 `{"detail": ...}`。需要在 `src/main.py` / `src/api/responses.py` 中注册 `RequestValidationError` handler。

要求：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数校验失败",
    "details": { ... }
  }
}
```

验收用例：

- `GET /api/v1/jobs?page=bad` 应返回 `{error}`，业务码 `VALIDATION_ERROR`。
- 缺失必填 body 字段也应返回 `{error}`，业务码 `VALIDATION_ERROR`。

状态码建议按 `api-contract.md` §2.4：请求参数校验失败用 HTTP 400 + `VALIDATION_ERROR`。

### 4. 校验 `to_status` 枚举（P1）

`TransitionRequest.to_status` 和 `BatchTransitionRequest.to_status` 不应接受任意字符串。

要求：

- `to_status` 必须属于 `Application.status` 9 状态英文 code。
- `favorited` / `to_apply` / `not_a_status` 这类值应返回 HTTP 400 + `VALIDATION_ERROR`。
- 合法状态之间但流转非法，仍返回 `INVALID_TRANSITION`。

示例：

- `applied -> favorited`：`VALIDATION_ERROR`
- `offer_accepted -> interviewing`（非纠错）：`INVALID_TRANSITION`

### 5. 修正 batch-transition 契约（P1）

对照 api-contract：

```json
{
  "data": {
    "succeeded": [1, 3],
    "failed": [
      {
        "application_id": 2,
        "error_code": "INVALID_TRANSITION",
        "message": "终态不可流转"
      }
    ],
    "total": 3,
    "success_count": 2,
    "fail_count": 1
  }
}
```

要求：

- 字段名必须为 `succeeded`，不是 `success`。
- failed item 必须包含 `application_id / error_code / message`。
- 返回 `total / success_count / fail_count`。
- 部分失败不中断。
- 每条独立事务：一个 application 失败不影响其他成功项；循环后不要依赖最后统一 commit 才提交所有成功项。
- 不支持批量纠错，保持 `BatchTransitionRequest` 无纠错字段即可。

### 6. 补齐 application 详情与 transition 响应（P2）

#### `GET /applications/{id}`

api-contract 的投递详情包含 `events`。当前只返回 application + job。

要求：

- 响应 `data.events`，按 `occurred_at ASC` 输出完整时间线。
- 保留 `job` 信息。

#### `POST /applications/{id}/transition`

api-contract 的 transition 响应包含本次状态变更事件。

要求：

- 响应 `data.event`，包含 `id/event_type/from_status/to_status/occurred_at/is_correction/correction_reason/note`。
- 普通流转和纠错流转都要返回本次事件。

### 7. 补齐 create application 初始事件（P2，但影响 funnel/detail）

`POST /applications` 创建初始投递时，应同时写入一条 `ApplicationEvent`：

```text
event_type = status_change
from_status = None
to_status = applied
occurred_at = applied_at 或当前时间
is_correction = False
```

要求：

- 与 `Application` 创建在同一事务内。
- `GET /applications/{id}/events` 创建后应能看到初始 applied 事件。
- 不修改 `src.db.init_db` 既有 6 条事件验收输出。

### 8. 补齐 todo 响应契约（P2）

api-contract 要求 `GET /todo` items：

```json
{
  "event_id": 2,
  "application_id": 1,
  "event_type": "interview",
  "scheduled_at": "...",
  "round": 1,
  "note": "一面",
  "job": {
    "company": "字节跳动",
    "title": "产品经理实习"
  },
  "days_left": 3
}
```

要求：

- 使用 `event_id`，不要只返回 `id`。
- 返回嵌套 `job` 对象，至少含 `company/title`。
- 返回 `round`。
- 返回 `days_left`。
- 保持待办查询语义：只查未来 N 天 `scheduled_at IS NOT NULL AND occurred_at IS NULL` 的 interview/test/material_submit。

### 9. 补齐 jobs stats 与 JobOut 字段（P2）

#### `GET /jobs/stats`

api-contract 要求：

```json
{
  "data": {
    "today_new": 25,
    "total": 1500,
    "valid": 1200,
    "invalid": 300
  }
}
```

当前返回 `by_source`，需要调整为契约字段。后续若仍需要 `by_source`，可作为附加字段，但不得缺少契约字段。

#### `JobOut`

补齐：

- `last_verified_at`

不要删除已有字段。

### 10. 扩展 API 测试

在 `tests/test_api.py` 或新增测试文件中补 API contract 回归。至少覆盖：

1. `/dashboard/distribution` 200 且返回 `{dimension, distribution, total}`。
2. `/dashboard/kpi` 含 `today_new_jobs / total_jobs / total_applications / pending_applications / by_status`。
3. `/dashboard/funnel` 含 `funnel / total_applications`，并包含 API 创建投递的 `applied` 初始事件。
4. `/dashboard/trend` 统计有效进展事件，不统计单纯 applied_at。
5. FastAPI 参数校验错误返回 `{error.code=VALIDATION_ERROR}`。
6. `to_status=favorited` 返回 `VALIDATION_ERROR`。
7. 合法状态但非法流转返回 `INVALID_TRANSITION`。
8. `batch-transition` 返回 `succeeded / failed / total / success_count / fail_count`，且部分失败不中断。
9. `GET /applications/{id}` 含 `events`。
10. `POST /applications/{id}/transition` 含本次 `event`。
11. `GET /todo` item 含 `event_id / job / days_left / round`。
12. `GET /jobs/stats` 含 `today_new / total / valid / invalid`。
13. `JobOut` 响应含 `last_verified_at`。

## 验证命令

请至少执行以下命令，并在结果文件中记录完整结果：

```bash
python -m compileall -q src tests
python -m pytest -q
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
```

并额外运行一个 TestClient 验证脚本或 pytest 用例，明确证明：

- `/api/v1/dashboard/distribution` 不再 500。
- `GET /api/v1/jobs?page=bad` 返回 `{error.code=VALIDATION_ERROR}`。
- `POST /api/v1/applications/{id}/transition` 对 `to_status=favorited` 返回 `VALIDATION_ERROR`。
- `batch-transition` 返回契约字段。

## 验收标准

Codex 二次验收时将检查：

- `pytest` 通过，且新增测试覆盖本任务列出的 contract 失败点。
- `compileall` 通过。
- 内存库 `init_db` 仍为 4 公司 / 4 岗位 / 4 投递 / 6 条事件。
- OpenAPI 中核心 15 端点仍存在。
- `/dashboard/distribution` 返回 200。
- Dashboard 四端点响应 shape 与 `api-contract.md` 一致。
- 所有请求参数/body 校验错误统一 `{error}`。
- 非法 `to_status` 是 `VALIDATION_ERROR`，合法状态间非法流转是 `INVALID_TRANSITION`。
- batch-transition 响应字段与失败项格式符合契约。
- application detail / transition / todo / jobs stats / JobOut 字段补齐。

## 结果文件路径

`.agent-ops/mimo/outbox/TASK-BE-REWORK-002-result.md`

## 结果格式（Mimo 必须填写）

- 摘要
- 修改的文件清单
- 关键实现点
- 执行的命令与结果
- 新增测试清单
- 未解决的问题
- 需要 Codex 判断的风险

## 备注

本任务是 API 层返工修复，不是采集层 / AI 层开发。修复完成并通过 Codex 二次验收后，才允许进入采集层与 AI 解析层。
