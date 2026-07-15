# TASK-BE-REWORK-002 最终验收报告

**验收日期**：2026-07-06  
**验收对象**：API 层契约返工 + dashboard 小范围修复  
**验收结论**：通过，可进入采集层 / AI 层

---

## 一、修复范围

本次由 Codex 直接完成 `.agent-ops/TASK-BE-REWORK-002-REVIEW.md` 中剩余的两个小范围问题：

1. `GET /dashboard/funnel` 从当前状态分布改为基于 `ApplicationEvent` 的累计到达漏斗。
2. `GET /dashboard/trend?days=N` 修正为返回正好 N 个日期点。

修改文件：

- `src/api/routes/app/dashboard.py`
- `tests/test_api.py`

---

## 二、验证结果

### API 测试

```text
python -m pytest tests/test_api.py -q
17 passed
```

### 全量测试

```text
python -m pytest -q
48 passed, 163 warnings in 1.10s
```

### 编译

```text
python -m compileall -q src tests
# 无输出，通过
```

### 内存库初始化

```text
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

---

## 三、独立探针

创建一个投递并流转到 `interviewing` 后，漏斗累计到达数正确：

```text
funnel_after_one_app_reaches_interviewing=[
  {'status': 'applied', 'count': 1, 'rate': 1.0},
  {'status': 'test', 'count': 1, 'rate': 1.0},
  {'status': 'interviewing', 'count': 1, 'rate': 1.0},
  {'status': 'offer_pending', 'count': 0, 'rate': 0.0},
  {'status': 'offer_accepted', 'count': 0, 'rate': 0.0}
]
```

`days` 参数返回精确点数：

```text
trend_days_1_len=1
trend_days_7_len=7
```

---

## 四、最终结论

API 层返工阻断项已清零。Dashboard 漏斗、趋势边界和上一轮所有 API 契约问题均已通过验证。

**结论：验收通过，可进入采集层 / AI 层。**
