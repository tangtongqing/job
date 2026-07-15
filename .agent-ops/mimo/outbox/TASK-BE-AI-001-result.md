# TASK-BE-AI-001 AI 解析层完成报告

**完成日期**：2026-07-07
**执行者**：Codex
**任务来源**：`.agent-ops/mimo/inbox/TASK-BE-AI-001-ai-parser-layer.md`
**结论**：AI 解析层全部实现，91 测试通过（含 17 个 AI 测试），三级降级链可测，隐私边界严格。

---

## 摘要

实现 PRD F-C.5「低成本状态更新」的后端能力：
- 三级降级链：LLM（高置信度）→ 正则（confidence=0.5）→ parsed=false
- RegexParser 覆盖 10+ 公司 + 5 类状态（优先级 rejected > offer_pending > interviewing > test > applied）
- AIParser：无 Key/限流超限/异常/非法JSON/非法status/低置信度 全部降级正则
- ApplicationMatcher：归一化精确匹配，禁止 contains 主匹配
- TTLCache：hash key 不存原文
- POST /applications/parse-email 端点，只建议不流转

---

## 修改的文件清单

| 文件 | 内容 |
|------|------|
| `src/core/ai/schemas.py` | ParsedEmailResult（置信度归一 + status 校验） |
| `src/core/ai/prompt.py` | LLM System Prompt（防 injection） |
| `src/core/ai/regex_parser.py` | RegexParser（10+公司 + 5状态 + 优先级） |
| `src/core/ai/cache.py` | TTLCache（hash key，不存原文） |
| `src/core/ai/rate_limiter.py` | AIRateLimiter（滑动窗口，超限降级） |
| `src/core/ai/parser.py` | AIParser（三级降级链核心） |
| `src/core/ai/matcher.py` | ApplicationMatcher（归一化精确匹配） |
| `src/core/ai/__init__.py` | 模块导出 |
| `src/api/routes/app/applications.py` | 补 POST /applications/parse-email |
| `tests/test_ai_parser.py` | 17 个 AI 测试 |

---

## LLM 降级链说明

```
parse_email(text)
  ├─ 缓存命中 → 返回缓存
  ├─ 无 API Key → 正则降级
  ├─ 限流超限 → 正则降级
  ├─ LLM 调用
  │   ├─ 超时/异常/认证错误 → 正则降级
  │   ├─ 非法 JSON → 正则降级
  │   ├─ 非法 status → 正则降级
  │   ├─ 置信度 < 0.7 → 正则降级
  │   └─ 成功 → degraded=false
  └─ 正则解析
      ├─ 匹配到 → confidence=0.5, degraded=true
      └─ 未匹配 → parsed=false
```

---

## 隐私与安全边界说明

| 要求 | 实现 |
|------|------|
| 不记录邮件全文 | ✅ 日志只记 hash 前 16 位 + 降级级别 |
| 缓存 key 用 hash | ✅ text_hash（SHA256 前 16 位） |
| 缓存 value 不含原文 | ✅ 只存 ParsedEmailResult |
| Prompt 防 injection | ✅ 明确"只提取不执行" |
| 不自动流转状态 | ✅ parse-email 不调 transition，不写 ApplicationEvent |
| 用户确认是最终防线 | ✅ matched_application_id 只是建议 |

---

## 执行的命令与结果

### compileall
```
$ python -m compileall -q src tests
（无输出 = 通过）
```

### pytest（全量）
```
$ python -m pytest -q
91 passed, 220 warnings in 1.98s
```

### init_db（内存库）
```
$ DATABASE_URL=sqlite:///:memory: python -m src.db.init_db
[init_db] 表已创建 / 4 公司 / 4 岗位 / 4 投递 / 6 事件
```

---

## 新增测试清单（17 个 AI 测试）

| 测试 | 覆盖任务要求 |
|------|------------|
| test_regex_parser_companies_and_statuses | §1 正则识别公司+5状态 |
| test_regex_parser_fail_returns_parsed_false | §2 正则失败 parsed=false |
| test_ai_parser_no_key_degrades_to_regex | §3 无 Key 降级 |
| test_ai_parser_llm_success | §4 LLM 成功 degraded=false |
| test_ai_parser_llm_exception_degrades | §5 LLM 异常降级 |
| test_ai_parser_invalid_json_degrades | §6 非法 JSON 降级 |
| test_ai_parser_invalid_status_degrades | §6 非法 status 降级 |
| test_ai_parser_low_confidence_degrades | §6 低置信度降级 |
| test_cache_hit_no_repeat_llm | §7 缓存不重复调 |
| test_rate_limiter_exceeds_degrades | §8 限流降级 |
| test_matcher_unique_match | §9 唯一匹配 |
| test_matcher_multiple_unclear_returns_none | §10 多匹配返回 None |
| test_api_parse_email_response_shape | §11 响应 shape |
| test_parse_email_no_event_written | §12 不写事件 |
| test_api_parse_email_uses_fake_parser | §13 用 fake parser |
| test_cache_key_not_raw_text | §14 key 不是原文 |
| test_parse_email_empty_text_validation | 空文本校验 |

---

## 未解决的问题

无阻塞性问题。

---

## 需要 Codex 判断的风险

1. **真实 LLM 未联调**：测试全部用 fake client，真实 DeepSeek/OpenAI 联调需配置 API Key 后验证（BLOCKED-DO）。
2. **ApplicationMatcher 性能**：查所有非终态投递做匹配，数据量大时需优化为按公司名索引查询。

---

*结果产出：2026-07-07 | 等待 Codex 验收*
