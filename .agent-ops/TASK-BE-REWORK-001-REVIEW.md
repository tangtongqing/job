# TASK-BE-REWORK-001 二次验收报告

**验收日期**：2026-07-03  
**验收对象**：`.agent-ops/mimo/outbox/TASK-BE-REWORK-001-result.md`  
**验收结论**：通过，可进入后端 API 层

---

## 一、验收摘要

| 项目 | 结论 | 说明 |
|------|------|------|
| P0 状态机流转规则 | ✅ 通过 | 与 `api-contract.md` §四一致，missing/extra 清零 |
| P1 CHECK 约束 | ✅ 通过 | 5 类枚举字段非法值均被数据库拦截 |
| P1 部分索引 | ✅ 通过 | 返工要求的 8 个部分索引和 active application 唯一索引均带 WHERE |
| P1 待办语义 | ✅ 通过 | 未来 `scheduled_at` 事件可被待办查询命中 |
| P2 事务边界 | ✅ 通过 | 事件服务不再内部 commit，外层 rollback 后不落库 |
| 测试与实跑 | ✅ 通过 | `pytest` 31 passed，内存库 init_db 输出 4/4/4/6 |

**是否可进入下一轮（API 层）**：可以。

---

## 二、实跑验证

### 1. 导入验证

```text
python -c "from src.db.models import Job, Application, ApplicationEvent; print('models import OK')"
models import OK
```

### 2. 内存库初始化

为避免本地已有 `data/jobpulse.db` 影响结果，使用 `DATABASE_URL=sqlite:///:memory:` 验证干净建表与种子：

```text
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

本地实际 `data/jobpulse.db` 当前也保持种子状态：

```text
job_count=4
company_count=4
application_statuses={'applied': 1, 'interviewing': 1, 'offer_accepted': 1, 'test': 1}
application_event_count=6
```

### 3. 编译与测试

```text
python -m compileall -q src tests
# 通过，无输出
```

```text
python -m pytest -q
31 passed, 92 warnings in 1.73s
```

warnings 主要是 `datetime.utcnow()` 的 Python 3.12 deprecation、SQLAlchemy `Query.get()` legacy warning，以及 pytest cache 写入 `.pytest_cache` 权限警告；均不影响本次返工验收。

---

## 三、独立探针结果

### 状态机规则

```text
transition_diffs=[]
```

### CHECK 约束

```text
check_tables={
  'application': True,
  'application_event': True,
  'company': False,
  'crawl_log': True,
  'job': True,
  'subscription': False,
  'user_job_action': True
}
```

`company` / `subscription` 无枚举字段，不需要 CHECK。

非法枚举写入全部被拦截：

```text
invalid_job_status=BLOCKED
invalid_application_status=BLOCKED
invalid_event_type=BLOCKED
invalid_action_type=BLOCKED
invalid_crawl_status=BLOCKED
```

### 部分索引

```text
required_where_indexes={
  'idx_job_deadline': True,
  'idx_job_category': True,
  'idx_uja_active': True,
  'idx_event_funnel': True,
  'idx_event_todo': True,
  'idx_event_correction': True,
  'idx_sub_keyword': True,
  'idx_sub_company': True,
  'idx_app_one_active_per_job': True
}
```

### 待办与事务

```text
future_todos_count=1
rollback_note_count=0
```

---

## 四、残余风险

1. `datetime.utcnow()` 在 Python 3.12 有弃用警告，可后续统一替换为 timezone-aware 写法。
2. `session.query(Application).get()` 是 SQLAlchemy 2.x legacy API，可后续替换为 `session.get(Application, id)`。
3. pytest 尝试写 `.pytest_cache` 时出现权限警告，但测试执行与结果不受影响。

上述均为非阻塞项，不影响进入 API 层。

---

## 五、最终结论

返工任务已修复首次验收阻断项：状态机规则、数据库约束、部分索引、事件待办语义与事务边界均通过二次验证。

**结论：验收通过，可进入后端 API 层。**
