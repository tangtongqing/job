# TASK-010 · AI 解析模块设计

## 背景与目标

TASK-006/007/008/009 已完成。本任务是阶段 2 的**亮点模块**——F-C.5 低成本状态更新的 AI 解析层，是产品的差异化竞争力。但也是**风险点**（LLM 不可用、成本、准确性）。

**目标**：产出 AI 解析模块的详细设计，覆盖 LLM 调用、三级降级链、成本控制、Prompt 工程、匹配逻辑，可直接指导阶段 4 实现。

## 输入素材（必读）

- `docs/architecture/system-architecture.md` —— **v2**，重点 §4.4 AI 降级链（openai 1.0+ API）、§6 配置（LLM 相关）
- `docs/architecture/api-contract.md` —— **v2**，重点 `POST /applications/parse-email` 端点 + matched_application_id 匹配逻辑
- `docs/product/PRD.md` —— v3，F-C.5 低成本状态更新

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径

- `docs/architecture/ai-parser-module.md`（**新建**，本任务唯一产出）

## 禁止操作

- 不修改 `src/`、`config/`、`data/`、`scripts/`、`tests/` 下任何文件
- 不修改任何已存在文档
- 不创建实际代码文件
- 不实际调用 LLM API（本任务是设计文档）

## 实现要求

### 一、文档结构（七个部分）

#### 1. 模块总览
- 一句话定位（F-C.5 的 AI 解析层，是低成本状态更新的"亮点 + 降级"双角色）
- 模块边界：解析邮件/截图文本 → 返回结构化建议（不直接写库，用户确认后才流转）
- 与其他模块关系：被 api/ 调用，调用外部 LLM，匹配 db/Application

#### 2. 三级降级链（核心，呼应 TASK-006 v2 §4.4）

详细说明每一级的触发条件、输入输出、置信度、成本：

| 级别 | 触发条件 | 输入 | 输出 | 置信度 | 成本 |
|------|---------|------|------|--------|------|
| L1 LLM | LLM 可用 + 限流未触发 | 邮件文本 | 结构化解析 | ≥0.7 | 高 |
| L2 正则 | LLM 不可用/超时/限流/低置信度 | 邮件文本 | 简单匹配 | 0.5 | 零 |
| L3 None | 正则也失败 | - | null | 0 | 零 |

每级给出：
- 触发条件（哪些异常/状态降级）
- 输入输出 Schema
- 降级日志记录

#### 3. LLM 调用设计（核心）

**3.1 API 选型与调用**
- DeepSeek（默认，成本低）vs OpenAI（备选）
- openai SDK 1.0+ 的 AsyncOpenAI 用法（呼应 TASK-006 v2 §4.4，不能用 0.x API）
- 强制 JSON 输出（response_format）

**3.2 Prompt 工程**
- System Prompt 设计（角色定义 + 任务说明 + 输出格式约束）
- Few-shot 示例（2-3 个典型邮件样例）
- 输出 JSON Schema：`{ company, title, suggested_status, confidence, reasoning }`

**3.3 调用伪代码**（呼应 TASK-006 v2 §4.4）
- 异步调用 + 超时
- 异常分类（超时/限流/认证/其他）

#### 4. 正则降级设计（L2）
- 关键词词典：公司名（常见公司列表）、状态关键词（笔试/面试/Offer/拒绝）
- 提取规则（正则 + 关键词匹配）
- 置信度固定 0.5（标注为 degraded）

#### 5. 匹配逻辑（呼应 TASK-008 v2 parse-email 的 matched_application_id）

**5.1 匹配流程**
- 解析出 company + title 后，查询 Application 表
- 匹配规则（呼应 TASK-008 v2）：公司名模糊匹配 + 岗位名相似度
- 多匹配时的处理（返回 null 让用户选）

**5.2 匹配伪代码**
- 模糊匹配实现（SQLAlchemy contains 或应用层相似度）
- 多结果/无结果的处理

**5.3 用户确认机制**（关键）
- AI 结果仅作**建议**，不自动流转
- 前端展示建议 + 用户确认按钮
- 确认后才调用 transition API

#### 6. 成本控制（呼应 TASK-006 v2 §4.4）

| 控制点 | 策略 | 参数 |
|--------|------|------|
| 缓存 | TTLCache，相同邮件 1 小时内不重复调用 | ttl=3600 |
| 限流 | 每分钟最多 10 次 LLM 调用 | max_per_minute=10 |
| 超时 | 单次调用 5 秒超时 | timeout=5 |
| 模型选择 | 默认 DeepSeek（便宜），OpenAI 备选 | - |

给出 RateLimiter + TTLCache 的伪代码。

#### 7. 测试策略（呼应 TASK-011）
- LLM Mock 测试（不实际调用，mock 返回）
- 正则降级测试（确定性）
- 匹配逻辑测试（边界：无匹配/多匹配/精确匹配）
- 降级链测试（LLM 不可用 → 正则 → None）

### 二、质量要求

- **必须用 openai SDK 1.0+ API**（AsyncOpenAI，呼应 TASK-006 v2，不能用 0.x）
- **三级降级链必须完整**（触发条件清晰）
- **Prompt 必须强制 JSON 输出**（response_format）
- **成本控制必须具体**（缓存/限流/超时/模型）
- **匹配逻辑必须呼应 TASK-008 v2**（matched_application_id + 用户确认）
- **LLM 异步但入库同步**（呼应 TASK-006 v2 的同步策略，LLM 是唯一例外）

### 三、与前置任务的对齐检查

- [ ] openai SDK 1.0+ API（AsyncOpenAI）？
- [ ] 三级降级链完整（LLM/正则/None）？
- [ ] 强制 JSON 输出（response_format）？
- [ ] 成本控制四点（缓存/限流/超时/模型）？
- [ ] 匹配逻辑呼应 TASK-008 v2（matched_application_id + 用户确认）？
- [ ] LLM 异步入库同步？

## 验证命令

纯文档任务。自查清单（对照上面"对齐检查"）。

## 结果文件路径

`docs/architecture/ai-parser-module.md`

## 结果格式（写入 outbox）

```markdown
# TASK-010 执行结果

## 摘要
<2-3 句话概述 AI 解析模块设计核心>

## 修改/新建的文件清单
- docs/architecture/ai-parser-module.md（新建）

## 关键设计决策
- LLM 选型：...
- 降级链：...
- 成本控制：...
- 匹配逻辑：...

## 与前置任务对齐自查
<逐项打勾>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有，特别是 Prompt 设计、成本预算、匹配准确性>
```
