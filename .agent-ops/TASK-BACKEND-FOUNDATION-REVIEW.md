# 后端地基验收报告

**验收日期**：2026-07-02  
**验收对象**：`.agent-ops/TASK-BACKEND-FOUNDATION-REPORT.md`  
**验收结论**：不通过，暂不建议进入 API 层

---

## 一、验收摘要

| 项目 | 结论 | 说明 |
|------|------|------|
| A. 代码审查（对照设计文档） | ❌ 未通过 | 状态机流转规则、数据库约束/部分索引、事件待办写入存在偏差 |
| B. 实跑验证 | ✅ 部分通过 | 模型导入、建表、种子数据、6 条状态事件通过；pytest 环境缺失 |
| C. 状态机校验 | ✅ 通过基础场景 | 终态纠错无原因拦截、终态常规流转拦截、终态带原因纠错均通过 |
| D. 已知限制 | ⚠️ 部分成立 | SQLite 不用 SELECT FOR UPDATE 属设计决策；但当前问题超出已知限制 |

**是否可进入下一轮（API 层）**：否。建议先修复 P0/P1 问题，再进入 API 路由实现，否则 API 层会固化错误状态机和查询语义。

---

## 二、发现的问题

### P0：状态机流转规则与 API 契约不一致

**位置**：`src/core/statemachine/transitions.py`

对照 `docs/architecture/api-contract.md` §四「状态机流转 API 详细说明」，当前 `TRANSITIONS` 缺少合法流转，并额外允许了非法回退：

| from_status | 缺少的合法流转 | 多出的非法流转 |
|-------------|----------------|----------------|
| `applied` | `offer_pending` | - |
| `test` | `offer_pending` | - |
| `interviewing` | `interviewing` | `test` |
| `offer_pending` | `rejected`, `no_response` | - |

影响：
- `applied/test -> offer_pending` 的「直接发 Offer」场景会被 API 误拒。
- `interviewing -> interviewing` 多轮面试自环会被误拒，违反 PRD F-C.1 AC「面试中→面试中支持，并记录轮次」。
- `interviewing -> test` 是回退流转，和「求职进度不可逆」规则冲突。
- `offer_pending -> rejected/no_response` 在 API 契约中属于所有进行中状态可进入的终态，但当前会被拒绝。

实跑对照输出：

```text
applied: missing=['offer_pending'], extra=[]
test: missing=['offer_pending'], extra=[]
interviewing: missing=['interviewing'], extra=['test']
offer_pending: missing=['no_response', 'rejected'], extra=[]
```

### P1：ORM 未落地文档要求的 CHECK 约束

**位置**：`src/db/models.py`

`database-schema.md` v2 明确要求以下字段有 CHECK 约束：
- `job.status`
- `user_job_action.action_type`
- `application.status`
- `application_event.event_type`
- `crawl_log.status`

当前模型没有 `CheckConstraint`，内存 SQLite 建表后所有表 DDL 均无 CHECK。非法枚举值可被写入：

```text
invalid_job_status: NOT_BLOCKED
invalid_application_status: NOT_BLOCKED
invalid_event_type: NOT_BLOCKED
invalid_action_type: NOT_BLOCKED
invalid_crawl_status: NOT_BLOCKED
```

影响：
- 数据库层无法保证「枚举值全部英文 code 且取值合法」。
- 后续 API、采集、AI 解析只要绕过应用层校验，就可能污染核心状态数据。

### P1：多个应为部分索引的索引被建成普通索引

**位置**：`src/db/models.py`

`database-schema.md` v2 要求多处部分索引：
- `idx_job_deadline WHERE deadline IS NOT NULL`
- `idx_job_category WHERE job_category IS NOT NULL`
- `idx_uja_active WHERE ended_at IS NULL`
- `idx_event_funnel WHERE is_correction = FALSE`
- `idx_event_todo WHERE scheduled_at IS NOT NULL AND occurred_at IS NULL`
- `idx_event_correction WHERE is_correction = TRUE`
- `idx_sub_keyword` / `idx_sub_company` 按文档为部分索引

当前实际 DDL 中这些索引大多为普通索引，只有 `idx_app_one_active_per_job` 正确带 WHERE。

影响：
- 与「全部索引按 schema 文档落地」不一致。
- 查询计划和数据规模增长后的性能特征会偏离设计。

### P1：事件服务写入未来待办后无法被待办查询命中

**位置**：`src/core/events/service.py`

`get_upcoming_todos()` 查询条件要求：

```python
ApplicationEvent.scheduled_at.isnot(None)
ApplicationEvent.occurred_at.is_(None)
```

但 `add_interview()` / `add_test()` / `add_material_submit()` 在调用方没有传 `occurred_at` 时，会默认写入 `datetime.utcnow()`。因此创建一个未来 `scheduled_at` 的待办事件后，立刻变成「已发生」，查询结果为 0。

实跑结果：

```text
probe_future_todo_count_after_add_test=0
```

影响：
- PRD F-C.6「下一步待办视图」无法正常工作。
- 事件服务的写入语义和查询语义相互冲突。

### P2：事件服务函数内部直接 `commit()`，不利于组合事务

**位置**：`src/core/events/service.py`

`add_interview()` / `add_test()` / `add_material_submit()` / `add_offer()` / `add_note()` 都在函数内部 `session.commit()`。这会让调用方难以把「状态流转 + 事件补充 + 其他业务变更」放进同一事务。

验收探针中，外层事务因 `add_test()` 内部提交而无法整体回滚，说明当前服务层事务边界偏硬。

建议：
- 服务函数只 `session.add()` / `flush()` 并返回对象。
- 由 API handler 或上层 use case 统一提交/回滚。

---

## 三、通过项

### B. 实跑验证

```text
python -c "from src.db.models import Job, Application, ApplicationEvent; print('models import OK')"
models import OK

python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

补充验证：

```text
python -m compileall -q src
# 通过，无输出
```

未完成项：

```text
python -m pytest
No module named pytest
```

当前环境未安装 `pytest`，且 `tests/` 目录为空，本轮未能执行自动化测试。

### C. 状态机基础校验

```text
scenario1 OK: 纠错必须填写原因
scenario2 OK: 不允许从 offer_accepted 流转到 interviewing
scenario3 OK: corrected status=interviewing
```

验收后已将本地演示库恢复到种子状态：

```text
application_statuses={'applied': 1, 'interviewing': 1, 'offer_accepted': 1, 'test': 1}
application_event_count=6
```

---

## 四、建议修复顺序

1. 修正 `TRANSITIONS`，以 `docs/architecture/api-contract.md` §四为准，并补状态机单元测试。
2. 给 ORM 增加 `CheckConstraint`，覆盖所有枚举字段。
3. 按 `database-schema.md` v2 给部分索引补 `sqlite_where` / `postgresql_where`。
4. 调整事件服务：未来待办默认 `occurred_at=None`；已发生事件才写实际发生时间。
5. 去掉事件服务内部 `commit()`，由上层统一管理事务。
6. 补 `tests/`：状态机合法/非法/纠错、约束、部分唯一索引、待办查询。

---

## 五、最终结论

后端地基已经具备可导入、可建表、可跑种子的基础形态，状态机的三个基础保护场景也通过。但它还没有达到「可安全进入 API 层」的标准：状态机规则和契约不一致，数据库无法防止非法枚举落库，事件待办功能存在可复现逻辑错误。

**结论：验收不通过。修复上述 P0/P1 后再进入 API 层。**
