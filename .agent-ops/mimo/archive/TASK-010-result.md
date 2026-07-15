# TASK-010 执行结果

## 摘要
完成了 AI 解析模块设计文档，覆盖 LLM 调用设计（DeepSeek + openai SDK 1.0+）、三级降级链（LLM → 正则 → None）、成本控制（缓存/限流/超时/模型）、Prompt 工程（System Prompt + Few-shot）、匹配逻辑（模糊匹配 + 用户确认），可直接指导阶段 4 实现。

## 修改/新建的文件清单
- docs/architecture/ai-parser-module.md（新建）

## 关键设计决策

### LLM 选型
- **默认 DeepSeek**（成本低，中文能力强，兼容 OpenAI 接口）
- **备选 OpenAI**（gpt-3.5-turbo）

### 降级链
- **L1 LLM**：高置信度（≥0.7），成本 ~$0.001/次
- **L2 正则**：关键词匹配，置信度 0.5，成本零
- **L3 None**：返回 null，前端走快捷交互层

### 成本控制
- **缓存**：TTLCache，相同邮件 1 小时内不重复调用
- **限流**：RateLimiter，每分钟最多 10 次 LLM 调用
- **超时**：asyncio.wait_for，5 秒超时
- **模型选择**：DeepSeek 默认（~$0.001/次）

### 匹配逻辑
- **ApplicationMatcher**：模糊匹配公司名 + 岗位名相似度
- **用户确认**：AI 结果仅作建议，用户确认后才调用 transition API

## 与前置任务对齐自查

- [x] openai SDK 1.0+ API（AsyncOpenAI）？
- [x] 三级降级链完整（LLM/正则/None）？
- [x] 强制 JSON 输出（response_format）？
- [x] 成本控制四点（缓存/限流/超时/模型）？
- [x] 匹配逻辑呼应 TASK-008 v2（matched_application_id + 用户确认）？
- [x] LLM 异步入库同步？

## 未解决的问题
- DeepSeek API 的稳定性需要验证
- Prompt 可能需要根据实际邮件格式迭代优化

## 需要 Codex 判断的风险
- Prompt 设计是否需要更多 Few-shot 示例
- 成本预算是否合理（Demo 阶段 ~$0.30/月）
- 匹配准确性是否足够（特别是公司名模糊匹配）