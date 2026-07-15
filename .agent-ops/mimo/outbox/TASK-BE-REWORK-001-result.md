# TASK-BE-REWORK-001 返工结果

**执行日期**：2026-07-02
**执行者**：Codex（承接返工任务）
**任务来源**：`.agent-ops/mimo/inbox/TASK-BE-REWORK-001-backend-foundation.md`
**结论**：全部 6 项修复完成，31 个测试通过，4 个验证命令全绿。

---

## 摘要

针对验收报告的 P0/P1/P2 问题逐项修复：
- P0 状态机流转规则：对照 api-contract.md §四 重写，已验证 missing/extra 清零
- P1 CHECK 约束：5 个枚举字段全部加 CheckConstraint，已验证非法值被拦截
- P1 部分索引：8 个部分索引补齐 sqlite_where/postgresql_where
- P1 待办语义：未来 scheduled_at 不再误填 occurred_at，已验证查询命中
- P2 事务边界：事件服务去掉内部 commit，已验证外层 rollback 不落库
- 补 31 个测试覆盖 7 类场景

---

## 修改的文件清单

| 文件 | 修改内容 |
|------|---------|
| `src/core/statemachine/transitions.py` | P0 重写流转规则，对照 api-contract §四 |
| `src/db/models.py` | P1 加 CheckConstraint + 部分索引 sqlite_where/postgresql_where |
| `src/core/events/service.py` | P1 待办语义 + P2 去掉内部 commit |
| `tests/conftest.py` | 新增，内存 SQLite fixtures |
| `tests/test_statemachine.py` | 新增，合法/非法/纠错流转 |
| `tests/test_constraints.py` | 新增，5 类 CHECK 约束 |
| `tests/test_partial_unique.py` | 新增，部分唯一索引 |
| `tests/test_events.py` | 新增，待办查询 + 事务回滚 |

---

## 关键实现点

### 1. P0 状态机（transitions.py 重写）
以 api-contract.md §四为权威来源，结构改为"前进流转 ∪ 任意进行中→终态"：
- `applied/test/interviewing → offer_pending` 已补
- `interviewing → interviewing` 多轮自环已补
- `interviewing → test` 回退已删除
- `offer_pending → rejected/no_response` 已补
- 终态常规流转无出路（纠错走 is_correction）

### 2. P1 CHECK 约束
5 个 CheckConstraint，命名清晰：chk_job_status / chk_uja_action_type / chk_app_status / chk_event_type / chk_crawl_status。

### 3. P1 部分索引
8 个部分索引补 WHERE：idx_job_deadline / idx_job_category / idx_uja_active / idx_event_funnel / idx_event_todo / idx_event_correction / idx_sub_keyword / idx_sub_company。idx_app_one_active_per_job 保持不变。

### 4. P1 待办语义
add_interview/add_test/add_material_submit 的 occurred_at 默认逻辑：
- 只传 scheduled_at → occurred_at=None（未来待办）
- 传 occurred_at → 记录已发生
- 都不传 → occurred_at=now（即时事件）

### 5. P2 事务边界
所有 add_* 函数改为 session.add() + flush()，不 commit。init_db.py 不受影响（它用状态机 transition 自带事务，不直接调事件服务 add_*）。

---

## 执行的命令与结果

### 验证1：models import
```
$ python -c "from src.db.models import Job, Application, ApplicationEvent; print('models import OK')"
models import OK
```

### 验证2：init_db
```
$ python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```
（与返工前一致，种子数据未回退）

### 验证3：compileall
```
$ python -m compileall -q src tests
（无输出 = 通过）
```

### 验证4：pytest
```
$ python -m pytest -v
======================= 31 passed, 91 warnings in 0.47s =======================
```
31 个测试全部通过。warnings 均为 datetime.utcnow() 的 DeprecationWarning（非失败，models/engine/tests 全用同一写法保持一致）。

### 补充验证：CHECK 约束真实拦截
```
job.status 非法: OK 已拦截
app.status 非法: OK 已拦截
event_type 非法: OK 已拦截
action_type 非法: OK 已拦截
crawl.status 非法: OK 已拦截
```

### 补充验证：待办语义 + 事务回滚
```
测试1（未来待办查询）: OK 查到
测试2（发生后排除）: OK 排除
测试3（外层rollback不落库）: OK 未落库
```

---

## 未解决的问题

无阻塞性问题。两个非阻塞观察：

1. **datetime.utcnow() DeprecationWarning**：Python 3.12+ 弃用。当前 models/engine/tests 统一用 utcnow()，保持一致。未来可批量换为 datetime.now(UTC)。不影响功能，不影响迁移。
2. **SQLAlchemy Query.get() LegacyAPIWarning**：engine.py 用 session.query(Application).get(id)。功能正常，未来可换 Session.get()。不影响状态机正确性。

两项均不影响验收标准，可在后续 API 层开发时顺手清理。

---

## 需要 Codex 判断的风险

1. **事务嵌套**：engine.py 的 transition 用 `begin_nested() if in_transaction() else begin()` 兼容嵌套调用。如果 API 层在已有事务里调 transition，会用 SAVEPOINT；否则开新事务。请 Codex 确认 API 层事务策略是否兼容此设计。
2. **init_db 种子数据的事务**：种子数据用 transition（自带事务），4 个投递的多轮流转各开独立事务。与验收时"6 条事件"一致。

---

## 对照验收标准自查

| 验收标准 | 状态 |
|---------|------|
| TRANSITIONS 与 api-contract.md §四一致 | ✅ missing/extra 清零 |
| 内存 SQLite DDL 有 CHECK 约束 | ✅ 5 个 CheckConstraint |
| 非法枚举写入失败 | ✅ 5 类全部 IntegrityError |
| 部分索引带 WHERE | ✅ 8 个补齐 |
| 未来待办能被 get_upcoming_todos 查到 | ✅ |
| 事件服务不内部提交，外层可回滚 | ✅ |
| init_db 输出 4/4/4/6 | ✅ |
| pytest 有通过证据 | ✅ 31 passed |

---

*结果产出：2026-07-02 | 等待 Codex 二次验收*
