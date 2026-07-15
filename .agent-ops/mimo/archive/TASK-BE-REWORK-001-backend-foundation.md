# TASK-BE-REWORK-001 · 后端地基返工修复

## 背景与目标

Codex 已完成对 `.agent-ops/TASK-BACKEND-FOUNDATION-REPORT.md` 的验收，结论见：

- `.agent-ops/TASK-BACKEND-FOUNDATION-REVIEW.md`

验收结论为：**不通过，暂不建议进入 API 层**。

本任务目标是修复后端地基中的 P0/P1 问题，使配置/数据库/状态机/事件服务达到可进入 API 层的质量标准。修复完成后，Mimo 需要提供可复现的命令结果与风险说明，供 Codex 二次验收。

## 允许读取的路径

- `.agent-ops/TASK-BACKEND-FOUNDATION-REVIEW.md`
- `.agent-ops/TASK-BACKEND-FOUNDATION-REPORT.md`
- `docs/architecture/database-schema.md`
- `docs/architecture/api-contract.md`
- `docs/product/PRD.md`
- `src/`
- `tests/`
- `pyproject.toml`
- `.env.example`

## 允许修改的路径

- `src/db/models.py`
- `src/core/statemachine/transitions.py`
- `src/core/statemachine/engine.py`（仅当测试或事务边界需要小修）
- `src/core/events/service.py`
- `tests/`
- `pyproject.toml`（仅允许补充测试依赖或 pytest 配置，不允许更换技术栈）
- `.agent-ops/mimo/outbox/TASK-BE-REWORK-001-result.md`

## 禁止操作

- 不进入 API 层开发，不新增 FastAPI 路由。
- 不做采集层、AI 解析层、前端 UI 或营销页面修改。
- 不删除或重建用户已有资料；不要删除 `docs/`、`.agent-ops/`、`web/`。
- 不引入未批准的外部服务、真实 API Key、真实爬取请求。
- 不为了让测试通过而放宽业务规则。
- 不把中文状态值写入数据库枚举字段；数据库持久化枚举必须为英文 code。
- 不把事件服务里的待办查询条件改成绕过 `occurred_at IS NULL`；正确做法是修复写入语义。

## 实现要求

### 1. 修复状态机流转规则（P0）

以 `docs/architecture/api-contract.md` §四「状态机流转 API 详细说明」为准，修正 `src/core/statemachine/transitions.py`。

期望规则：

```python
applied -> test, interviewing, offer_pending, withdrawn, rejected, no_response
test -> interviewing, offer_pending, withdrawn, rejected, no_response
interviewing -> interviewing, offer_pending, withdrawn, rejected, no_response
offer_pending -> offer_accepted, offer_declined, withdrawn, rejected, no_response
terminal statuses -> no normal transition
```

必须修复：
- 增加 `applied -> offer_pending`
- 增加 `test -> offer_pending`
- 增加 `interviewing -> interviewing`
- 删除 `interviewing -> test`
- 增加 `offer_pending -> rejected`
- 增加 `offer_pending -> no_response`

终态纠错仍通过 `is_correction=True` 完成，不应放进常规 `TRANSITIONS`。

### 2. 补齐 ORM CHECK 约束（P1）

在 `src/db/models.py` 中使用 SQLAlchemy `CheckConstraint` 落地 schema 文档要求。

至少覆盖：

- `Job.status IN ('displaying', 'closed')`
- `UserJobAction.action_type IN ('favorited', 'to_apply')`
- `Application.status IN ('applied', 'test', 'interviewing', 'offer_pending', 'offer_accepted', 'offer_declined', 'rejected', 'no_response', 'withdrawn')`
- `ApplicationEvent.event_type IN ('status_change', 'interview', 'test', 'material_submit', 'offer', 'note', 'correction')`
- `CrawlLog.status IN ('success', 'failed', 'skipped')`

要求：
- 约束名要清晰，例如 `chk_app_status`、`chk_event_type`。
- 不要引入中文枚举。
- 内存 SQLite 建表后，非法枚举写入必须抛出 `IntegrityError`。

### 3. 补齐部分索引（P1）

对照 `docs/architecture/database-schema.md` v2，把应为部分索引的索引补上 `sqlite_where` / `postgresql_where`。

至少覆盖：

- `idx_job_deadline`: `deadline IS NOT NULL`
- `idx_job_category`: `job_category IS NOT NULL`
- `idx_uja_active`: `ended_at IS NULL`
- `idx_event_funnel`: `is_correction = FALSE`
- `idx_event_todo`: `scheduled_at IS NOT NULL AND occurred_at IS NULL`
- `idx_event_correction`: `is_correction = TRUE`
- `idx_sub_keyword`: `keyword IS NOT NULL`
- `idx_sub_company`: `company IS NOT NULL`

`idx_app_one_active_per_job` 已有部分唯一索引，保留并确认不回退。

### 4. 修复事件服务待办语义（P1）

修复 `src/core/events/service.py`：

- `add_interview()` / `add_test()` / `add_material_submit()` 如果传入 `scheduled_at` 且未传 `occurred_at`，应创建未来待办，`occurred_at` 保持 `None`。
- 只有明确传入 `occurred_at`，或调用的是表示已发生的事件，才写实际发生时间。
- `get_upcoming_todos()` 仍应按 `scheduled_at IS NOT NULL AND occurred_at IS NULL` 查询未来待办。

建议设计：
- 对面试/笔试/材料事件，`scheduled_at` 表示计划时间，`occurred_at` 表示实际完成时间。
- 如果没有 `scheduled_at` 也没有 `occurred_at`，可按当前业务默认写 `occurred_at=datetime.utcnow()`，但必须保证「有未来 scheduled_at 时不会自动填 occurred_at」。

### 5. 调整事件服务事务边界（P2）

当前事件服务内部直接 `session.commit()`，不利于组合事务。

要求：
- `add_interview()` / `add_test()` / `add_material_submit()` / `add_offer()` / `add_note()` 不再内部 `commit()`。
- 函数只负责构造对象、`session.add()`，必要时 `session.flush()` 以便返回对象可用。
- 提交/回滚交给上层调用方。
- 更新或新增测试证明外层事务可以 rollback 掉事件服务写入。

注意：如果 `init_db.py` 或其他调用方依赖原内部 commit，需要同步调整调用方，但不要扩大到 API 层。

### 6. 补充测试

在 `tests/` 中补充聚焦测试，至少覆盖：

1. 状态机合法流转：
   - `applied -> offer_pending`
   - `test -> offer_pending`
   - `interviewing -> interviewing`
   - `offer_pending -> rejected`
   - `offer_pending -> no_response`
2. 状态机非法流转：
   - `interviewing -> test` 必须被拒绝。
   - 终态常规流转必须被拒绝。
3. 纠错：
   - 终态纠错无原因抛 `CorrectionValidationError`。
   - 终态带原因纠错成功，写入 `ApplicationEvent(event_type='correction', is_correction=True)`。
4. CHECK 约束：
   - 非法 `Application.status`、`ApplicationEvent.event_type`、`UserJobAction.action_type`、`Job.status`、`CrawlLog.status` 写入应失败。
5. 部分唯一索引：
   - 同一 `job_id` 同时只能有一个非终态 `Application`。
   - 终态后允许再次创建新的非终态投递。
6. 待办查询：
   - 创建未来 `scheduled_at` 的 interview/test/material 事件后，`get_upcoming_todos()` 能查到。
   - 设置 `occurred_at` 后，不再出现在待办中。
7. 事件服务事务：
   - 外层事务 rollback 后，事件不应落库。

测试应优先使用临时 SQLite 或内存 SQLite，不依赖真实 `data/jobpulse.db`。

## 验证命令

请至少执行以下命令，并在结果文件中记录完整结果：

```bash
python -c "from src.db.models import Job, Application, ApplicationEvent; print('models import OK')"
python -m src.db.init_db
python -m compileall -q src tests
python -m pytest
```

如果当前环境缺少 `pytest`：
- 不要静默跳过。
- 在结果文件中明确写出 `python -m pytest` 的失败原因。
- 仍需提交 pytest 测试文件。
- 额外运行一个临时 Python 验证脚本，证明状态机规则、CHECK 约束、待办查询、事务 rollback 四类核心修复可复现。

## 验收标准

Codex 二次验收时将检查：

- `TRANSITIONS` 与 `api-contract.md` §四一致。
- 内存 SQLite DDL 中能看到关键 CHECK 约束。
- 非法枚举写入会失败。
- 文档要求的部分索引实际带 WHERE 子句。
- 未来待办事件能被 `get_upcoming_todos()` 查到。
- 事件服务不再内部提交，外层事务可统一回滚。
- `python -m src.db.init_db` 仍能输出 4 公司 / 4 岗位 / 4 投递 / 6 条事件。
- 测试或替代验证脚本有明确通过证据。

## 结果文件路径

`.agent-ops/mimo/outbox/TASK-BE-REWORK-001-result.md`

## 结果格式（Mimo 必须填写）

- 摘要
- 修改的文件清单
- 关键实现点
- 执行的命令与结果
- 未解决的问题
- 需要 Codex 判断的风险

## 备注

本任务是返工修复，不是新功能开发。修复完成并通过 Codex 二次验收后，才允许进入后端 API 层。
