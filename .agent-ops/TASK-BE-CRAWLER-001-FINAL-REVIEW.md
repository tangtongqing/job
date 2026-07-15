# TASK-BE-CRAWLER-001 最终验收报告

**验收日期**：2026-07-07  
**验收对象**：采集层基础设施 + Codex 小范围修复  
**验收结论**：通过，可进入 AI 解析层

---

## 一、修复范围

Codex 直接修复了 `.agent-ops/TASK-BE-CRAWLER-001-REVIEW.md` 中剩余的 3 个 P1 小范围问题：

1. 接入 `config/sources.yaml` 到运行链路，`enabled:false` 的高风险来源不再能被 trigger。
2. 修复 robots manual override 开关，默认关闭时人工 allow 不生效。
3. 为 `POST /jobs/{id}/verify` 增加测试注入 fetcher，端点测试不再触网。

修改文件：

- `src/crawler/config.py`
- `src/crawler/service.py`
- `src/crawler/compliance/robots.py`
- `src/api/routes/app/crawler.py`
- `src/api/routes/app/jobs.py`
- `tests/test_crawler.py`

---

## 二、关键验收探针

```text
robots_manual_override_disabled_first= False
robots_manual_override_disabled_marked= False
robots_manual_override_disabled_after_mark= False

verify_status= 200
verify_httpx_head_calls= 0

boss_trigger_status= 400
boss_trigger_json= {'error': {'code': 'VALIDATION_ERROR', 'message': '采集源已禁用: boss', 'details': {'source': 'boss', 'enabled': False}}}
boss_trigger_httpx_get_calls= 0
```

说明：

- robots 不可读时仍 fail-closed。
- `manual_robots_override:false` 下人工放行不会生效。
- verify endpoint 可通过 fake fetcher 测试，不调用默认 HTTP HEAD。
- `boss.enabled:false` 下 API 直接返回统一错误，不再读取 `zhipin.com/robots.txt`。

---

## 三、验证命令

### 采集层测试

```text
python -m pytest tests/test_crawler.py -q
26 passed
```

### 编译

```text
python -m compileall -q src tests
# 通过，无输出
```

### 全量测试

```text
python -m pytest -q
74 passed, 209 warnings in 1.15s
```

### 内存库初始化

```text
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

---

## 四、最终结论

采集层基础设施的阻断问题已清零。配置、合规边界、测试隔离、crawler API、verify endpoint 均达到本任务验收标准。

**结论：验收通过，可进入 AI 解析层。**
