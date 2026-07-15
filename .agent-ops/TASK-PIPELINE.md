# 阶段 1 任务流水线 · Stage 1 Task Pipeline

> 主智能体（Codex）维护，定义 Mimo 任务的下发顺序与依赖关系。
> Mimo 一次只执行一个任务（inbox 中编号最新的），完成后 Codex 验收并归档，再下发下一个。

---

## 任务总览

| ID | 任务 | 依赖 | 状态 | 说明 |
|----|------|------|------|------|
| TASK-001 | 竞品调研 | 无 | ✅ 已验收（Codex 补强 v2） | 6 个竞品的标准调研，v2 已附实证 |
| TASK-002 | 痛点与 JTBD | TASK-001 | ✅ 已验收（Codex 裁决 P-03 优先级） | 12 痛点 / 15 Job Stories / 7 假设 |
| TASK-003 | 市场分析总论 | TASK-001 | ✅ 已验收（Codex 补强 v2：数据溯源/时间窗口/路径区分） | TAM855万 / 竞争定位图 / 做不做清单 / 冷启动 |
| TASK-004 | PRD 初稿 | TASK-001/002/003 | ✅ 已验收（Codex 补强 v2：状态机/AC/数据模型/范围边界 8 处） | 8状态机/15功能点/数据模型/漏斗日志 |

---

## ✅ 阶段 1（产品定义）初版完成 → 用户提交评审 → 进入修订

**评审修订通过后**，才进入阶段 2（架构设计），触发 Backend Security & Test Gate。

---

## 阶段 1 评审修订（用户提交 `docs/product/stage1-review-recommendations.md`）

| ID | 任务 | 依赖 | 状态 | 说明 |
|----|------|------|------|------|
| TASK-005 | 阶段1评审修订包（5 子任务 A-E） | 用户评审 + Codex 确认取舍 | ✅ 已验收（Codex 校准 4 处跨文档不一致） | 9状态机/6新增JS/3新增功能/路径B验证窗口/优先级统一 |

---

## ✅ 阶段 2（架构设计）进行中

详见 `.agent-ops/STAGE2-PIPELINE.md`。

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| TASK-006 | 系统架构设计 | ✅ 已验收（Codex 补强 v2：7 处硬伤） | 单体分层 / SQLite同步 / 状态机原子性 / AI降级链 / 部署拓扑 |
| TASK-007 | 数据库表设计 | ✅ 已验收（Codex 补强 v2：6 处硬伤） | 7表 / 英文枚举 / 事务原子性 / 部分唯一索引 |
| TASK-008 | API 契约设计 | ✅ 已验收（Codex 补强 v2：8 处硬伤） | 26端点 / 英文枚举 / 事务说明 / 批量端点 |
| TASK-009 | 采集模块设计 | ✅ 已验收（Codex 补强 v2：8 处硬伤） | 3适配器 / fail-closed robots / 批量提交 / 跨源完全相等 / Playwright生命周期 |
| TASK-010 | AI 解析模块设计 | ✅ 已验收（Codex 补强 v2：归一化匹配/边界澄清） | 三级降级 / openai 1.0+ / 成本控制 / 用户确认 |
| TASK-011 | Backend Security & Test Gate | ✅ 已验收（Codex 深度校验 v2：7 处硬伤，含 Prompt 注入诚实重写 + AI 邮件隐私新增） | 19 安全项 + 8 测试项 + 7 残余风险，有条件通过 |

---

## ✅ 阶段 2（架构设计）全部完成

**进入阶段 3（UI/UX 设计）**——使用 impeccable（shape → craft）做高保真页面。

---

## 🔄 阶段 3（UI/UX 设计）进展（2026-07-01 更新）

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| TASK-012~015 | 设计初始化 + 3 个 shape | ✅ 完成 | PRODUCT/DESIGN/BRAND + 看板/岗位/投递 shape |
| TASK-016b | 营销面 craft | ✅ 完成 | 7 屏滚动叙事 + 两轮视觉优化（见 TASK-VISUAL-OPTIMIZATION-REPORT）|
| TASK-016a | 产品面 craft | ⏸️ 暂停 | 等后端完成有真实数据后再做 |
| TASK-017 | critique + audit | ⏸️ | 等 016a |
| TASK-018 | polish + harden | ⏸️ | 等 017 |

**营销面视觉**：TASK-VISUAL-APPLE-GRADE 交 GPT 进行中（Apple 级设计美感：屏级配色+滚动动画质感）。

---

## 🔄 阶段 4（实现）后端开发启动（2026-07-01）

Offerbiu 对标完成（见 `competitor-offerbiu.md` + `competitor-offerbiu-innerpages.md`），战略决策：**差异化，不做简历/AI 匹配**，深化采集+状态机+看板主线。架构无需改动。

后端开发顺序（按依赖）：
1. 项目初始化 + 配置层
2. 数据库层（7 表 ORM）
3. 核心层（状态机 + 事件服务）
4. API 层
5. 采集层
6. AI 解析层
7. main 入口 + 中间件
8. 测试

详见架构文档 v3（`docs/architecture/`）。

### ✅ 阶段 4 核心实现收口（2026-07-09）

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| TASK-BACKEND-FOUNDATION | 后端地基 | ✅ 已验收 | ORM / 状态机 / 事件服务完成，经返工后通过 |
| TASK-BACKEND-API | 后端 API | ✅ 已验收 | Dashboard / Jobs / Applications / Todo / Crawler API 完成，经返工后通过 |
| TASK-BE-CRAWLER-001 | 采集层 | ✅ 已验收 | robots fail-closed、静态采集、日志链路通过 |
| TASK-BE-AI-001 | AI 邮件解析 | ✅ 已验收 | parse-email 只建议不流转，通过 |
| TASK-FE-PRODUCT-001 | 产品面核心前端 | ✅ 已验收（Codex 小修） | 7 页产品面、API client、状态配置、App Shell，build/lint/HTTP 路由探测通过 |

**下一阶段**：阶段 5 critique/audit、响应式、PWA、异常态、演示数据和作品集路径收口。

---

## 🔄 阶段 5（质量收口）启动（2026-07-09）

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| TASK-QA-001 | 产品面 + 营销面 critique/audit | 🔄 已下发 | 先审查，不大改；输出严重度分级问题清单和返工拆分 |

阶段 5 目标：
1. 发现并收口影响作品集可信度的体验/响应式/异常态问题。
2. 补齐 PWA、演示数据、启动说明和截图证据。
3. 为阶段 6 作品集包装准备稳定的演示路径。

---

### TASK-005 子任务（顺序执行，统一 v3 版本号）

- **A** 画像重构：P1 行为分群 / P2 降级+能力边界 / P3 并入 P1 生命周期
- **B** Job Stories：删 JS-05 / 降 JS-04,07,12 / 重写 JS-08,09,14' / 收窄 JS-01 / 新增 JS-16~21（6条）
- **C** PRD：9 状态机（5 终态）+ 终态可纠错 + ApplicationEvent 表 + 删 offer_result + UserJobAction 收窄 + 新增 F-C.5/F-C.6/F-A.6
- **D** 路径 B：改为"不赶增长窗口，必须赶验证窗口"，补 2026 秋招访谈/原型/本人记录
- **E** 优先级统一：PROJECT.md 新增 P0/P1/P2 定义，5 文档全局一致

---

## 依赖关系图

```
TASK-001 竞品调研
   ├─→ TASK-003 市场分析总论（强依赖，必须等 001 验收）
   └─→ TASK-002 JTBD（弱依赖，可与 001 并行，但建议 001 后做以校准）
                              ↓
                       TASK-004 PRD 初稿（依赖 001/002/003 全部完成）
```

**并行机会**：TASK-002 与 TASK-001 理论上可并行，但因画像已含痛点素材，让 002 在 001 之后做能借助竞品结论校准优先级，质量更高。**默认串行**。

---

## 执行节奏（Codex 调度）

1. **现在**：TASK-001 在 inbox，等 Mimo 执行
2. Mimo 完成 → Codex 验收（对照 TASK-001 简报的验收清单）→ 归档到 archive
3. 验收通过后，Codex 下发 TASK-002
4. 依次推进至 TASK-004
5. TASK-004 验收通过 → 阶段 1 结束 → 进入阶段 2（架构设计）

---

## Codex 在每阶段的"指挥动作"

- **下发**：把任务简报写入 inbox，通知 Mimo
- **等待**：Mimo 执行期间，Codex 不抢活，可做策略思考或不干预
- **验收**：检查产出是否符合简报、是否在授权范围、质量是否达标
- **决策**：不合格 → 打回（写 correction 任务）；遇到模糊 → 自己判断或问用户
- **整合**：阶段末把多个产出串成连贯叙事，更新 PROJECT.md

---

## 备注

- 用户已交付的 `docs/product/user-personas.md` 作为 TASK-002 的输入素材（Mimo 可参考但应产出独立的 JTBD 文档）
- 所有任务简报需遵循 `.agent-ops/COLLABORATING_AGENT_WORKFLOW.md` 的格式与安全门禁
