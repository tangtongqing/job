# TASK-BE-REWORK-002 返工结果

**执行日期**：2026-07-02
**执行者**：Codex
**任务来源**：`.agent-ops/mimo/inbox/TASK-BE-REWORK-002-backend-api.md`
**结论**：10 项契约偏差全部修复，46 测试通过（地基31 + API15），4 个验证命令全绿。

---

## 摘要

逐项对照 api-contract.md 修复 API 层契约偏差：
- P0 distribution 500：修复 `select_from` 拼写（误写 selectfrom）+ 重写查询逻辑
- P1 Dashboard 四端点：kpi/funnel/trend/distribution 全部对齐契约响应结构
- P1 校验错误统一：注册 RequestValidationError handler，返回 {error.code=VALIDATION_ERROR}
- P1 to_status 枚举：Literal 校验，favorited 等非法值返回 VALIDATION_ERROR
- P1 batch-transition：succeeded/failed/total/计数 + 每条独立事务
- P2 详情含 events + transition 返回 event + create 写初始 applied 事件
- P2 todo 契约：event_id/job/days_left/round
- P2 jobs stats：today_new/total/valid/invalid + JobOut.last_verified_at
- 新增 15 个 API 契约测试

---

## 修改的文件清单

| 文件 | 修改 |
|------|------|
| `src/api/routes/app/dashboard.py` | P0+P1 四端点完全重写（kpi/funnel/trend/distribution 契约对齐） |
| `src/api/routes/app/applications.py` | P1 batch 契约 + P2 详情含events + transition返回event + 初始applied事件 |
| `src/api/routes/app/todo.py` | P2 契约字段（event_id/job/days_left/round） |
| `src/api/routes/app/jobs.py` | P2 stats 契约字段（today_new/total/valid/invalid） |
| `src/api/responses.py` | P1 加 validation_error_handler |
| `src/main.py` | P1 注册 RequestValidationError handler |
| `src/schemas/models.py` | P1 to_status Literal 校验 + JobOut.last_verified_at + TransitionResponse + TodoOut 重写 |
| `tests/test_api.py` | 15 个契约测试覆盖 13 项要求 |

---

## 关键实现点

### 1. P0 distribution 500
根因：`select_from` 拼成 `selectfrom`，且原查询结构混乱。重写为 `select_from(Application).join(Job).group_by()`，支持 job_category/location/company_category 三维度。

### 2. P1 Dashboard 四端点契约
- **kpi**: today_new_jobs（当天collected_at）/ total_jobs / total_applications / pending_applications（非终态）/ by_status
- **funnel**: 按状态机顺序输出，rate=当前/上一阶段，第一个=1.0，返回 {funnel, total_applications}
- **trend**: 统计有效进展事件（status_change to test/interviewing/offer_pending），补齐0值日期，返回 {trend, total}
- **distribution**: {dimension, distribution:[{label,count,rate}], total}，非法 dimension 返回 VALIDATION_ERROR

### 3. P1 校验错误统一
注册 `RequestValidationError` handler → HTTP 400 + {error:{code:VALIDATION_ERROR, message, details:{errors}}。覆盖参数校验 + body 校验。

### 4. P1 to_status 枚举
`VALID_TO_STATUSES = Literal[9个英文code]`，Pydantic 自动校验。favorited/to_apply/not_a_status → 422 被 handler 转 400 VALIDATION_ERROR。

### 5. P1 batch-transition
- succeeded/failed（含 application_id/error_code/message）
- total/success_count/fail_count
- 每条独立事务（sm.transition + commit/rollback）
- 部分失败不中断

### 6. P2 详情/transition/初始事件
- GET /applications/{id} 返回 data.events（时间线）+ data.job
- POST transition 返回 data.application + data.event（本次变更事件）
- POST /applications 创建时同事务写初始 applied 事件（from_status=None, to_status=applied）

### 7. P2 todo 契约
item 含 event_id/application_id/event_type/scheduled_at/round/note/job{company,title}/days_left

### 8. P2 jobs stats + JobOut
stats 返回 today_new/total/valid/invalid（+ by_source 额外字段）。JobOut 补 last_verified_at。

---

## 执行的命令与结果

### compileall
```
$ python -m compileall -q src tests
（无输出 = 通过）
```

### pytest
```
$ python -m pytest -q
46 passed, 153 warnings in 0.91s
```
（地基31 + API15，全过；warnings 均为 datetime.utcnow DeprecationWarning）

### init_db（文件库）
```
$ python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

### init_db（内存库，任务要求）
```
$ DATABASE_URL=sqlite:///:memory: python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

### 4 个关键修复证明（pytest 子集）
```
$ python -m pytest tests/test_api.py -k "distribution or validation_error or invalid_to_status or batch_transition"
6 passed, 9 deselected
```
覆盖：distribution 200 + 非法维度 / 校验错误 envelope / to_status=favorited / batch 契约字段

---

## 新增测试清单（15 个 API 契约测试）

| 测试 | 覆盖要求 |
|------|---------|
| test_distribution_returns_200_with_contract | §1 distribution 200 + 结构 |
| test_distribution_invalid_dimension_validation_error | 非法 dimension |
| test_kpi_contract_fields | §2 kpi 5字段 |
| test_funnel_contract_and_initial_event | §3 funnel + applied初始事件 |
| test_trend_counts_progress_events | §4 trend 统计进展事件 |
| test_validation_error_envelope | §5 ?page=bad |
| test_body_validation_error_envelope | §5 body 校验 |
| test_invalid_to_status_enum | §6 favorited |
| test_invalid_transition_code | §7 终态→非终态 |
| test_batch_transition_contract | §8 succeeded/failed/计数 |
| test_application_detail_includes_events | §9 详情含 events |
| test_transition_returns_event | §10 transition 返回 event |
| test_todo_contract_fields | §11 todo event_id/job/days_left/round |
| test_jobs_stats_contract | §12 stats 4字段 |
| test_jobout_has_last_verified_at | §13 JobOut last_verified_at |

---

## 未解决的问题

无阻塞性问题。两个非阻塞观察（与返工001一致）：
1. datetime.utcnow() DeprecationWarning（全栈统一，不影响功能）
2. 测试 fixture 用 StaticPool 共享内存连接（TestClient 跨线程需要）

---

## 需要 Codex 判断的风险

1. **funnel 统计口径**：本版用 Application.status 当前分布（而非事件累计）。理由：funnel 反映"当前各阶段有多少投递"，更符合看板直觉。若验收认为应按事件累计，可切回 get_funnel。请 Codex 确认口径。
2. **batch-transition 事务**：每条独立 commit/rollback。若未来要全成功或全失败的原子语义，需改设计。当前符合契约"部分失败不中断"。

---

## 对照验收标准自查

| 验收标准 | 状态 |
|---------|------|
| pytest 通过 + 新增测试覆盖失败点 | ✅ 46 passed（含15新契约测试）|
| compileall 通过 | ✅ |
| init_db 4/4/4/6 | ✅（文件库+内存库都通过）|
| OpenAPI 15 端点存在 | ✅（未删端点）|
| distribution 200 | ✅ |
| Dashboard 响应 shape 对齐契约 | ✅ |
| 校验错误统一 {error} | ✅ |
| 非法 to_status=VALIDATION_ERROR，非法流转=INVALID_TRANSITION | ✅ |
| batch 契约字段 | ✅ |
| 详情/transition/todo/stats/JobOut 补齐 | ✅ |

---

*结果产出：2026-07-02 | 等待 Codex 二次验收*
