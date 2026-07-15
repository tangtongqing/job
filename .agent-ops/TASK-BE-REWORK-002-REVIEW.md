# TASK-BE-REWORK-002 二次验收报告

**验收日期**：2026-07-06  
**验收对象**：`.agent-ops/mimo/outbox/TASK-BE-REWORK-002-result.md`  
**验收结论**：不通过，需小范围返工

---

## 一、验收摘要

| 项目 | 结论 | 说明 |
|------|------|------|
| compileall | ✅ 通过 | `python -m compileall -q src tests` 无输出 |
| pytest | ✅ 通过 | `46 passed, 154 warnings in 2.35s` |
| init_db | ✅ 通过 | 内存库仍输出 4 公司 / 4 岗位 / 4 投递 / 6 条事件 |
| distribution 500 | ✅ 修复 | `/dashboard/distribution` 返回 200 |
| 统一错误 envelope | ✅ 通过 | 参数/body 校验均返回 `{error.code=VALIDATION_ERROR}` |
| to_status 枚举 | ✅ 通过 | `favorited` 返回 `VALIDATION_ERROR` |
| batch-transition 契约 | ✅ 通过 | 字段与部分失败格式已对齐 |
| detail / transition / todo / stats / JobOut 字段 | ✅ 通过 | 上轮列出的字段缺口已补齐 |
| dashboard funnel 口径 | ❌ 未通过 | 当前用 `Application.status` 当前分布，不是累计转化漏斗 |
| trend days 边界 | ❌ 未通过 | `days=1` 返回 2 天，`days=7` 返回 8 天 |

**是否可进入采集层 / AI 层**：暂不建议。剩余问题集中在 dashboard 口径，范围很小，但看板是后续前端与作品集叙事核心，建议修完再推进。

---

## 二、通过项实跑记录

### 1. 测试通过

```text
python -m pytest -q
46 passed, 154 warnings in 2.35s
```

### 2. 编译通过

```text
python -m compileall -q src tests
# 无输出，通过
```

### 3. 内存库初始化通过

```text
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

### 4. 上轮失败点已修复

独立 TestClient 探针确认：

```text
/api/v1/dashboard/distribution?dimension=job_category 200
GET /api/v1/jobs?page=bad -> 400 VALIDATION_ERROR
POST transition to_status=favorited -> 400 VALIDATION_ERROR
batch-transition -> succeeded/failed/total/success_count/fail_count
GET /applications/{id} -> includes events
POST /applications/{id}/transition -> includes event
GET /todo -> includes event_id/job/days_left/round
GET /jobs/stats -> includes today_new/total/valid/invalid
JobOut -> includes last_verified_at
```

---

## 三、剩余阻断问题

### P1：`GET /dashboard/funnel` 统计口径仍不符合“转化漏斗”

**位置**：`src/api/routes/app/dashboard.py`

当前实现按 `Application.status` 当前状态分布统计：

```python
rows = db.execute(
    select(Application.status, func.count(Application.id)).group_by(Application.status)
).all()
```

这会导致一个已从 `applied -> test -> interviewing` 的投递，不再计入 `applied` / `test` 阶段。复现结果：

```text
funnel_after_one_app_reaches_interviewing=[
  {'status': 'applied', 'count': 0, 'rate': 1.0},
  {'status': 'test', 'count': 0, 'rate': 0.0},
  {'status': 'interviewing', 'count': 1, 'rate': 0.0},
  {'status': 'offer_pending', 'count': 0, 'rate': 0.0},
  {'status': 'offer_accepted', 'count': 0, 'rate': 0.0}
]
```

这不是转化漏斗，而是“当前状态分布”。它会让“投递→笔试→面试”的转化率失真：一个已经进入面试的投递，理论上必然曾经进入 applied 和 test，但当前 applied/test 计数为 0。

**返工要求**：

- 用 `ApplicationEvent` 累计统计各阶段到达数，而不是当前 `Application.status`。
- 只统计 `event_type='status_change'` 且 `is_correction=false`。
- 按 `to_status` 聚合，阶段顺序：`applied -> test -> interviewing -> offer_pending -> offer_accepted`。
- API 创建投递时已经写入初始 `applied` 事件，可以作为漏斗基数。
- `rate = 当前阶段数量 / 上一阶段数量`，第一个阶段为 `1.0`；上一阶段为 0 时当前 rate 为 0。

验收用例应覆盖：

```text
创建投递 -> transition test -> transition interviewing
GET /dashboard/funnel
期望 applied=1, test=1, interviewing=1
```

### P2：`GET /dashboard/trend?days=N` 返回天数多 1

**位置**：`src/api/routes/app/dashboard.py`

当前代码：

```python
start = datetime.utcnow() - timedelta(days=days)
...
while cur <= today:
```

这会产生 `days + 1` 个点：

```text
trend_days_1_len=2
trend_days_7_len=8
```

**返工要求**：

- `days=1` 返回 1 个日期点（今天）。
- `days=7` 返回 7 个日期点。
- 建议 `start_date = today - timedelta(days=days - 1)`。

验收用例应覆盖：

```text
GET /dashboard/trend?days=1 -> len(trend) == 1
GET /dashboard/trend?days=7 -> len(trend) == 7
```

---

## 四、测试覆盖建议

当前新增 contract tests 很有价值，但漏斗测试只检查了返回里有 `applied`，没有检查“投递进入后续阶段后 applied/test 是否仍计入累计漏斗”。

请补两条精确回归：

1. `test_funnel_counts_reached_stages_from_events`
   - 创建投递并流转到 `interviewing`
   - 断言 `applied/test/interviewing` count 都为 1
2. `test_trend_days_returns_exact_number_of_points`
   - `days=1` 返回 1 点
   - `days=7` 返回 7 点

---

## 五、最终结论

TASK-BE-REWORK-002 已修复上一轮绝大多数 API 契约问题，质量明显提升。但 dashboard funnel 的核心统计口径仍会误导转化分析，trend 的 days 参数也有边界偏差。

**结论：二次验收不通过。请做小范围返工：只修 dashboard funnel/trend 与对应测试。**
