# TASK-BE-AI-001 验收报告

**验收日期**：2026-07-08  
**验收对象**：后端 AI 邮件解析层实现  
**结果文件**：`.agent-ops/mimo/outbox/TASK-BE-AI-001-result.md`  
**验收结论**：通过，可进入产品面前端接入 / 高保真实现阶段

---

## 一、验收结论

AI 解析层已满足 `TASK-BE-AI-001` 的核心要求：

- `POST /api/v1/applications/parse-email` 已补齐，返回 `{data}` envelope。
- LLM → 正则 → `parsed=false` 三级降级链可测。
- 无 API Key 时不调用 LLM。
- 测试通过 fake client / fake parser 隔离真实 LLM。
- parse-email 只返回建议，不写 `ApplicationEvent`，不改变 `Application.status`。
- matcher 使用公司名归一化后的完全相等作为主匹配逻辑，未使用 contains 主匹配。
- 缓存 key 使用 hash，未发现邮件原文进入日志或缓存 key。

---

## 二、验证结果

### AI 专项测试

```text
python -m pytest tests/test_ai_parser.py -q
17 passed
```

### 编译

```text
python -m compileall -q src tests
# 通过，无输出
```

### 全量测试

```text
python -m pytest -q
91 passed, 221 warnings in 1.88s
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

### parse-email 不触 LLM / 不写事件 / 不改状态

```text
parse_status= 200
parse_data= {
  'parsed': True,
  'company': '字节跳动',
  'title': None,
  'suggested_status': 'interviewing',
  'confidence': 0.5,
  'degraded': True,
  'matched_application_id': None,
  'reasoning': '公司匹配：字节跳动；关键词匹配：面试+面试邀请'
}
events_before_after= 0 0
status_after= applied
```

说明：使用 `AIParser(api_key='')` + fake LLM，LLM 未被调用；API 正常降级到正则；没有写事件，也没有修改投递状态。

### matcher 归一化精确匹配

```text
norm_job= 字节跳动
norm_target= 字节跳动
match= 1
```

说明：`字节跳动有限公司` 与 `字节跳动` 经归一化后精确相等，可以匹配唯一非终态投递。

### 缓存 key 非原文

```text
hash_equals_raw= False
hash_len= 16
```

---

## 四、非阻塞风险

1. **真实 LLM 未联调**：当前任务按要求用 fake client 验证，不访问真实 DeepSeek/OpenAI。真实 API Key 联调仍属于后续 BLOCKED-DO。
2. **LLM base_url 建议后续显式配置**：当前 `AIParser` 支持传入 `base_url`，但默认 DeepSeek/OpenAI 的选择依赖 key 形态；真实联调时建议在 `src/config.py` 增加显式 `llm_base_url`，减少误配风险。
3. **RegexParser 不提取岗位名**：符合任务降级设计，但前端展示时需允许 `title=null`，由用户确认/选择投递。

---

## 五、最终判断

本任务完成度达到验收标准。后端核心链路已经覆盖：

```text
数据库 / 状态机 / 事件服务 / API / Dashboard / 采集 / AI parse-email
```

**结论：验收通过，可回到产品面 craft / 前端接入阶段。**
