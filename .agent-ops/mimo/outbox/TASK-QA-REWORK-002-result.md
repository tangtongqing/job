# TASK-QA-REWORK-002 返工结果（N+1 修复）

**完成日期**：2026-07-10
**执行者**：Codex
**验收来源**：`.agent-ops/TASK-QA-REWORK-002-REVIEW.md`（Not accepted，N+1 回归）

---

## 摘要

修复 `GET /applications` 的 events N+1 懒加载问题。根因：列表端点用 `ApplicationOut.model_validate(a)` 序列化，触发 `events` 关系懒加载，每个 application 额外一次 SELECT。

修复：列表端点改用显式 dict 构造 + `ApplicationListItem` schema（不含 events），回归测试验证 N+1 消除。

---

## 修改的文件清单

| 文件 | 修改 |
|------|------|
| `src/schemas/models.py` | 新增 `JobSummary` + `ApplicationListItem`（列表专用，不含 events） |
| `src/api/routes/app/applications.py` | `list_applications` 改用显式 dict 构造，不用 ORM 序列化 |
| `tests/test_api.py` | 新增 2 个回归测试 |

---

## 关键实现点

### 根因
`ApplicationOut` schema 含 `events: list[ApplicationEventOut] | None`。调用 `model_validate(app)` 时 Pydantic 会访问 ORM 对象的 `events` 属性 → 触发 SQLAlchemy 懒加载 → 每个 application 一次 `SELECT FROM application_event`。

### 修复
列表端点不再用 `ApplicationOut.model_validate()`，改为显式构造 dict（只取标量字段 + job 摘要）：
```python
result.append({
    "id": a.id, "job_id": a.job_id, "status": a.status,
    "applied_at": a.applied_at.isoformat(), "updated_at": a.updated_at.isoformat(),
    "notes": a.notes,
    "job": {"id": job.id, "company": job.company, "title": job.title} if job else None,
})
```

详情端点 `GET /applications/{id}` 仍用 `ApplicationOut`（需要 events 时间线），不受影响。

---

## 执行的命令与结果

### 全量测试
```
$ python -m pytest -q
93 passed, 228 warnings in 1.07s
```
（91 原有 + 2 个新增 N+1 回归测试）

### 新增回归测试

| 测试 | 验证 |
|------|------|
| `test_applications_list_has_job_summary` | 列表返回 job.company + job.title |
| `test_applications_list_no_n1_events_query` | 3 个投递的列表请求，application_event 表查询次数 = 0 |

N+1 测试用 `before_cursor_execute` 事件监听器计数 `application_event` 表查询，断言列表请求期间该表查询为 0。

---

## 对照验收要求

| 验收要求 | 状态 |
|---------|------|
| 用列表专用 schema 排除 events | ✅ ApplicationListItem |
| 保留批量 job lookup + job 摘要 | ✅ 一次 IN 查询 |
| 回归测试含 query-count/懒加载防护 | ✅ before_cursor_execute 计数 |
| 全量测试通过 | ✅ 93 passed |
| 列表端点实际响应证据 | ✅ test_applications_list_has_job_summary 验证 company/title |

---

*结果产出：2026-07-10 | 等待 Codex 重新验收*
