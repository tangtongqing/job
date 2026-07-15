# 后端 API 层验收报告

**验收日期**：2026-07-03  
**验收对象**：`.agent-ops/TASK-BACKEND-API-REPORT.md`  
**验收结论**：不通过，暂不建议进入采集层 / AI 层

---

## 一、验收摘要

| 项目 | 结论 | 说明 |
|------|------|------|
| A. 实跑验证 | ⚠️ 部分通过 | `pytest` 42 passed、`compileall` 通过、内存库 `init_db` 通过 |
| B. 端到端验证 | ❌ 未通过 | `GET /api/v1/dashboard/distribution` 返回 500 |
| C. 对照 api-contract 检查 | ❌ 未通过 | 看板、批量流转、校验错误、详情/待办响应与契约不一致 |

**是否可进入下一轮（采集层 / AI 层）**：否。API 层需要先返工，否则后续模块会基于错误响应结构和错误码继续叠加。

---

## 二、通过项

### 1. 测试通过

```text
python -m pytest -q
42 passed, 129 warnings in 1.53s
```

warnings 主要是 `datetime.utcnow()`、SQLAlchemy `Query.get()`、TestClient / pytest cache 警告，不影响本次结论。

### 2. 编译通过

```text
python -m compileall -q src tests
# 无输出，通过
```

### 3. 干净内存库种子通过

```text
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

### 4. OpenAPI 注册端点存在

`/openapi.json` 中可看到报告声明的核心端点，包括：

- `/api/v1/jobs`
- `/api/v1/applications`
- `/api/v1/applications/batch-transition`
- `/api/v1/dashboard/kpi`
- `/api/v1/dashboard/funnel`
- `/api/v1/dashboard/trend`
- `/api/v1/dashboard/distribution`
- `/api/v1/todo`

---

## 三、阻断问题

### P0：`GET /dashboard/distribution` 当前直接 500

**位置**：`src/api/routes/app/dashboard.py`

当前实现：

```python
rows = db.execute(
    select(col, func.count(Application.id))
    .join(Application, Application.job_id == Job.id)
    .group_by(col)
    .all()
)
```

问题是 `.all()` 被调用在 `Select` 对象上，而不是 `db.execute(...)` 的结果上，运行时报：

```text
AttributeError: 'Select' object has no attribute 'all'
```

复现结果：

```text
GET /api/v1/dashboard/distribution?dimension=job_category
distribution_status=500
distribution_body_prefix=Internal Server Error
```

影响：
- 报告声明的 15 个端点里至少 1 个不可用。
- `tests/test_api.py` 没有覆盖 distribution 端点，因此 42 passed 未发现此问题。

### P1：Dashboard 四个端点与 api-contract 响应结构 / 统计口径不一致

**位置**：`src/api/routes/app/dashboard.py`

对照 `docs/architecture/api-contract.md`：

- `GET /dashboard/kpi` 应返回 `today_new_jobs / total_jobs / total_applications / pending_applications / by_status`。当前只返回 `total_applications / testing / interviewing / offers`。
- `GET /dashboard/funnel` 应返回 `{ "funnel": [...], "total_applications": n }`，当前直接返回列表；且当前漏斗基于 `ApplicationEvent`，创建投递时没有写入 `applied` 初始事件，导致 API 创建的投递不会进入 applied 漏斗基数。
- `GET /dashboard/trend` 文档要求统计进入 `test/interviewing/offer_pending` 的有效进展事件，当前统计的是 `Application.applied_at`。
- `GET /dashboard/distribution` 文档要求返回 `{dimension, distribution, total}`，且支持 `job_category/location/company_category`；当前返回列表，并支持 `job_category/source/company`。

复现输出：

```text
/api/v1/dashboard/kpi 200 {'data': {'total_applications': 1, 'testing': 0, 'interviewing': 1, 'offers': 0}}
/api/v1/dashboard/funnel 200 {'data': [{'status': 'interviewing', 'count': 1, 'rate': 1.0}, {'status': 'test', 'count': 1, 'rate': 1.0}]}
/api/v1/dashboard/trend 200 {'data': [{'date': '2026-07-03', 'count': 1}]}
```

影响：
- 前端按契约读取看板数据会缺字段或读错结构。
- 漏斗和趋势的分析含义与 PRD / api-contract 不一致。

### P1：批量流转响应字段与事务语义不符合契约

**位置**：`src/api/routes/app/applications.py`

api-contract 要求：

```json
{
  "data": {
    "succeeded": [1, 3],
    "failed": [
      { "application_id": 2, "error_code": "INVALID_TRANSITION", "message": "终态不可流转" }
    ],
    "total": 3,
    "success_count": 2,
    "fail_count": 1
  }
}
```

当前实际返回：

```text
batch_json={
  'data': {
    'success': [1],
    'failed': [
      {'id': 2, 'reason': '不允许从 offer_accepted 流转到 test'},
      {'id': 999, 'reason': 'not_found'}
    ]
  }
}
```

同时文档要求「每条独立事务」，当前实现是循环内用 `transition()` 的 nested transaction，最后统一 `db.commit()`。非法流转场景下能部分成功，但不是契约要求的每条独立提交；如果循环后半段出现非预期异常，前面成功项仍可能随外层事务回滚。

影响：
- 前端无法按 `succeeded / application_id / error_code / total` 等契约字段消费。
- 批量操作失败隔离语义不够明确。

### P1：请求参数校验错误没有统一 `{error}` 响应

**位置**：`src/main.py` / `src/api/responses.py`

api-contract §2.2 要求错误响应统一：

```json
{ "error": { "code": "...", "message": "...", "details": {...} } }
```

当前只注册了自定义 `APIError` handler，没有处理 FastAPI `RequestValidationError`。参数校验错误返回默认 422：

```text
GET /api/v1/jobs?page=bad
validation_status=422
validation_json={
  'detail': [
    {
      'type': 'int_parsing',
      'loc': ['query', 'page'],
      'msg': 'Input should be a valid integer, unable to parse string as an integer',
      'input': 'bad'
    }
  ]
}
```

影响：
- 错误 envelope 不统一。
- api-contract §2.4 的 `VALIDATION_ERROR` 无法覆盖 FastAPI 参数/body 校验失败。

### P1：非法 `to_status` 未按契约返回 `VALIDATION_ERROR`

**位置**：`src/schemas/models.py` / `src/api/routes/app/applications.py`

api-contract §四明确：`favorited` / `to_apply` 是 `UserJobAction.action_type`，不属于投递状态，前端误传时返回 `VALIDATION_ERROR`。

当前 `TransitionRequest.to_status` 是任意 `str`，误传会走状态机并返回 `INVALID_TRANSITION`：

```text
favorited_transition=400 {
  'error': {
    'code': 'INVALID_TRANSITION',
    'message': '不允许从 applied 流转到 favorited',
    'details': {'from_status': 'applied', 'to_status': 'favorited'}
  }
}
```

影响：
- 类型错误和业务流转错误混在一起。
- 前端无法区分「传错字段类型/枚举」与「合法状态间流转非法」。

---

## 四、其他契约偏差

### P2：`GET /applications/{id}` 未包含时间线 events

api-contract 的投递详情响应包含 `events`，当前只返回 application + job：

```text
application_detail_keys=['applied_at', 'id', 'job', 'job_id', 'notes', 'status', 'updated_at']
application_detail_has_events=False
```

虽然有单独的 `GET /applications/{id}/events`，但这与当前详情端点契约不一致。

### P2：`POST /applications/{id}/transition` 未返回 event

api-contract 的 transition response schema 包含本次状态变更事件；当前只返回 application：

```text
transition_keys=['applied_at', 'id', 'job', 'job_id', 'notes', 'status', 'updated_at']
transition_has_event=False
```

### P2：`GET /todo` 响应 shape 与契约不同

api-contract 要求字段包括 `event_id`、`round`、`job` 对象、`days_left`。当前 `TodoOut` 返回 `id/application_id/event_type/scheduled_at/occurred_at/note/company/title`。

### P2：`GET /jobs/stats` 响应 shape 与契约不同

api-contract 要求 `today_new / total / valid / invalid`；当前实现返回 `total / valid / by_source`。

### P2：`JobOut` 缺少 `last_verified_at`

ORM 有 `Job.last_verified_at`，api-contract 的 Job 响应也包含该字段；当前 `JobOut` 未暴露。

---

## 五、测试覆盖缺口

当前 42 个测试能验证基本 happy path，但没有覆盖以下验收关键点：

- `/dashboard/distribution` 不 500。
- dashboard 四个端点的响应 shape 与统计口径。
- FastAPI 参数/body 校验错误统一 `{error}`。
- `favorited/to_apply/not_a_status` 返回 `VALIDATION_ERROR`。
- batch-transition 的契约字段与部分失败格式。
- application detail / transition response 是否包含事件。
- todo response 是否含 `event_id/job/days_left`。

建议将这些补成 API contract tests，避免后续模块继续依赖错误结构。

---

## 六、建议返工顺序

1. 修复 `/dashboard/distribution` 的 500，并补测试。
2. 统一 dashboard 四端点响应 shape 与统计口径，尤其是 funnel/trend。
3. 给 `RequestValidationError` 注册统一错误 handler，返回 `{error}`。
4. 用枚举或 Pydantic validator 限制 `to_status`，非法枚举返回 `VALIDATION_ERROR`。
5. 修正 batch-transition 响应字段与每条独立事务语义。
6. 按契约补齐 application detail / transition / todo / jobs stats / JobOut 字段。
7. 扩展 `tests/test_api.py`，把上述失败用例纳入回归。

---

## 七、最终结论

API 层的基本路径已经可以跑通，地基测试也保持通过。但本轮目标是「端点响应符合 api-contract.md，可进入采集层/AI 层」，当前仍存在一个已声明端点 500，以及多处核心契约偏差。

**结论：验收不通过。修复 P0/P1 后再进入采集层 / AI 层。**
