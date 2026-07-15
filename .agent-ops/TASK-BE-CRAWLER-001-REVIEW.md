# TASK-BE-CRAWLER-001 验收报告

**验收日期**：2026-07-07  
**验收对象**：后端采集层基础设施实现  
**结果文件**：`.agent-ops/mimo/outbox/TASK-BE-CRAWLER-001-result.md`  
**验收结论**：不通过，暂不建议进入 AI 解析层

---

## 一、阻断问题

### P1：`config/sources.yaml` 未接入运行链路，高风险来源 `enabled:false` 不生效

位置：

- `config/sources.yaml:16-22`
- `src/api/routes/app/crawler.py:40-50`
- `src/crawler/service.py:67-72`
- `src/crawler/adapters/boss.py:31-37`

任务要求高风险来源默认 `enabled:false`，并且 crawler trigger 在未指定 source 时按配置触发 enabled sources；manual robots override、batch_size 等也应由配置控制。当前实现只创建了配置文件，但源码中没有任何地方读取 `config/sources.yaml`。`POST /api/v1/crawler/trigger` 未指定 source 时硬编码为 `"company"`；指定 `"boss"` 时即使配置里 `boss.enabled=false`，仍会创建 `BossAdapter` 并尝试读取 `https://www.zhipin.com/robots.txt`。

独立探针结果：

```text
httpx_get_url= https://www.zhipin.com/robots.txt
boss_trigger_status= 200
boss_trigger_json= {'data': {'source': 'boss', 'status': 'skipped', 'count': 0, 'error': None}}
boss_trigger_httpx_get_calls= 1
```

影响：

- 配置文件目前只是静态文档，不能约束运行行为。
- 禁用的高风险源仍可被 API 触发。
- 任务要求的 `manual_robots_override:false`、`batch_size`、enabled sources 等核心安全边界没有实际生效。

建议返工：

- 增加配置加载器，统一读取 `config/sources.yaml`，缺失时使用安全默认值。
- `trigger` 未传 source 时只触发 enabled sources。
- `trigger` 传入 disabled source 时返回统一 `{error}`，建议 `VALIDATION_ERROR` 或业务错误码 `SOURCE_DISABLED`。
- `CrawlService` 从配置获得 batch_size、source adapter、base_urls、manual_robots_override。

### P1：robots manual override 默认关闭但仍可绕过 fail-closed

位置：

- `src/crawler/compliance/robots.py:48-57`
- `src/crawler/compliance/robots.py:64-66`
- `src/crawler/compliance/robots.py:97-101`

`RobotsChecker.__init__` 接收 `manual_override=False`，但 `_manual_override_global` 从未被使用。`mark_allowed_manually()` 不检查该开关，任何调用都可以把不可读 robots 的站点加入 allowlist，并在之后 `can_fetch()` 中直接返回 True。

独立探针结果：

```text
robots_manual_override_disabled_first= False
robots_manual_override_disabled_after_mark= True
```

这与任务要求冲突：manual override 必须由配置显式开启，默认关闭。

建议返工：

- `mark_allowed_manually()` 在 `manual_override=False` 时应拒绝操作，或 `can_fetch()` 在全局开关关闭时忽略 `_manual_allowed`。
- 增加测试：`RobotsChecker(fetcher=fail, manual_override=False)` 调用 `mark_allowed_manually()` 后仍然不能抓取。
- 增加测试：只有 `manual_override=True` 时人工 allow 才生效。

### P1：`POST /jobs/{id}/verify` 端点没有 fake 注入路径，测试实际会走默认 HTTP fetcher

位置：

- `src/api/routes/app/jobs.py:146-155`
- `src/crawler/verifier.py:29-35`
- `src/crawler/verifier.py:61-75`
- `tests/test_crawler.py:345-360`

任务要求 `POST /api/v1/jobs/{id}/verify` 使用 fake verifier 时不触网。当前端点直接调用 `verify_job(db, job_id)`，没有依赖注入或测试 override；`verify_job()` 在未传 fetcher 时使用 `_default_fetcher`，内部执行 `httpx.head(url, timeout=10, follow_redirects=True)`。

现有测试名为“用 fake verifier 不触网”，但测试没有 monkeypatch 或依赖注入，只验证 endpoint shape。独立探针将 `httpx.head` 替换为计数器后确认端点会调用它：

```text
verify_status= 200
verify_httpx_head_calls= 1
```

影响：

- 测试隔离声明不成立。
- 在允许网络的环境中，测试或手动验收会对外部 URL 发起 HEAD 请求。
- 结果文件中“所有测试用注入/fake，严格不触网”的自查结论不准确。

建议返工：

- 为 verify endpoint 增加可注入 verifier/fetcher 依赖，测试通过 dependency override 注入 fake。
- 或提供受控的 `set_verifier_for_testing`，并在测试 teardown 中恢复。
- 修改 `test_api_jobs_verify`，断言 fake verifier 被调用，且 `httpx.head` 未被调用。

---

## 二、已通过项

- 采集层目录结构完整，包含 adapters、compliance、normalizer、dedup、service、scheduler、verifier。
- `CrawlService` 对 success/skipped/failed 写入 `CrawlLog`，并在 `finally` 中关闭 adapter。
- BOSS / 牛客 adapter 没有登录、验证码绕过、代理池或反爬绕过逻辑。
- normalizer、dedup、batch save、CrawlLog 三态都有基础测试覆盖。
- `compileall`、全量 pytest、内存库初始化均通过。

---

## 三、验证记录

### 编译

```text
python -m compileall -q src tests
# 通过，无输出
```

### 全量测试

```text
python -m pytest -q
72 passed, 208 warnings in 1.96s
```

### 内存库初始化

```text
$env:DATABASE_URL='sqlite:///:memory:'; python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```

### 独立探针

```text
robots_manual_override_disabled_first= False
robots_manual_override_disabled_after_mark= True

verify_status= 200
verify_httpx_head_calls= 1

httpx_get_url= https://www.zhipin.com/robots.txt
boss_trigger_status= 200
boss_trigger_json= {'data': {'source': 'boss', 'status': 'skipped', 'count': 0, 'error': None}}
boss_trigger_httpx_get_calls= 1
```

---

## 四、返工范围建议

本轮不需要推翻采集层整体结构，建议小范围返工：

1. 接入 `config/sources.yaml`，让 enabled、batch_size、manual_robots_override、adapter/base_urls 真正影响运行。
2. 禁止 disabled source 被 trigger；未指定 source 时只触发 enabled source。
3. 修复 robots manual override 开关，默认关闭时人工 allow 不应生效。
4. 为 verify endpoint 增加 fake 注入路径，并修改测试证明不触网。
5. 增加独立回归测试覆盖上述 3 个阻断点。

返工完成后，请输出：

`.agent-ops/mimo/outbox/TASK-BE-CRAWLER-001-rework-result.md`
