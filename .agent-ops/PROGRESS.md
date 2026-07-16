# 项目进度总览 · PROGRESS

> **本文件是跨上下文窗口的单一事实源（Single Source of Truth）。**
> 任何工作完成后，必须立即更新本文件，防止上下文超限导致新窗口失忆。
> 新窗口开启时，**第一件事读本文件**，即可恢复全部进度认知。
>
> 维护规则：
> 1. 每完成一个有意义的单元（一个 TASK、一次用户决策、一次文档版本升级），立即更新
> 2. "当前状态"区块永远反映**此刻**在哪
> 3. "下一步"区块永远指向**下一个动作**
> 4. 不记录过程细节，只记录"完成/未完成/阻塞/待决策"四态 + 一句话说明

---

## 一、当前状态（一句话）

> **三表面与完整数据演示已通过正式验收：24 条确定性快照 + 32 条公开 API 真实岗位可用，核心求职闭环、双端响应式与数据恢复均验证通过。**

**最后更新**：2026-07-16（完整演示验收通过，详见 `docs/qa/ACCEPTANCE-2026-07-16.md`）
**当前执行者**：高级智能体（Codex）
**交接文件**：`.agent-ops/HANDOVER-TO-ADVANCED-AGENT.md`
**设计基线**：`docs/design/REDESIGN-BRIEF.md`
**当前焦点**：用户体验确认与稳定版本提交

---

## 二、阶段总览

| 阶段 | 状态 | 产出 |
|------|------|------|
| 阶段 1 产品定义 | ✅ 完成（v3，经评审修订） | 画像/痛点/PRD/市场分析 |
| 阶段 2 架构设计 | ✅ 完成（v3，含安全测试门禁） | 架构/数据库/API/采集/AI/安全报告 |
| 阶段 3 UI/UX 设计 | ✅ 完成 | 第二版居中产品舞台、持续状态轨迹与三表面设计已落地 |
| 阶段 4 实现 | ✅ 完成 | 收藏/待投递、订阅、Demo 重置、核心产品页面、官网与案例页已实现 |
| 阶段 5 质量 | ✅ 完成 | 107 项后端测试、前端 lint 与 14 路由生产构建通过；数据与关键路由联调通过 |
| 阶段 6 作品集 | ✅ 完成 | 独立 `/case-study` 与 59.4 秒真实 Demo 视频已接入 |

> **并行进行中**：
> - 阶段 3 营销页视觉（TASK-VISUAL-APPLE-GRADE）交 GPT
> - 阶段 4 后端 + 产品面核心实现已验收
> - Offerbiu 对标已完成，战略决策：差异化，不模仿简历/AI 线

---

## 三、文档版本台账

| 文档 | 当前版本 | 最后更新 | 说明 |
|------|---------|---------|------|
| `docs/product/PROJECT.md` | **v5** | 2026-06-30 | 营销面转真实营销型（v4→v5） |
| `docs/product/evolution-roadmap.md` | v1.1 | 2026-06-30 | §5 定价转真实营销型 |
| `docs/product/PRD.md` | v3 | 阶段1 | 9 状态机/18 功能点 |
| `docs/product/user-personas.md` | v3 | 阶段1 | 3 画像 |
| `docs/product/pain-points-jtbd.md` | v3 | 阶段1 | 20 Job Stories |
| `docs/product/stage1-review-recommendations.md` | - | 阶段1 | 用户评审 |
| `docs/research/competitor-analysis.md` | v2 | 阶段1 | 6 竞品 |
| `docs/research/competitor-offerbiu.md` | v1.1 🆕 | 2026-07-01 | Offerbiu 对标+战略决策（差异化） |
| `docs/research/competitor-offerbiu-innerpages.md` | v1.0 🆕 | 2026-07-01 | Offerbiu 内页 16 屏深度分析 |
| `docs/research/market-analysis.md` | v3 | 阶段1 | TAM/路径B验证 |
| `docs/architecture/system-architecture.md` | v3 | 2026-06-24 | +§九演进预留+营销面路由 |
| `docs/architecture/database-schema.md` | v2 | 阶段2 | 7 表 |
| `docs/architecture/api-contract.md` | v2 | 阶段2 | 26 端点 |
| `docs/architecture/crawler-module.md` | v2 | 阶段2 | 3 适配器 |
| `docs/architecture/ai-parser-module.md` | v2 | 阶段2 | 三级降级 |
| `docs/architecture/security-test-gate-report.md` | v2 | 阶段2 | 19安全+8测试 |
| `docs/design/PRODUCT.md` | v1.0 | 阶段3 | 产品面寄存器 |
| `docs/design/BRAND.md` | **v5** | 2026-06-30 | 营销面转真实营销型（v1→v5） |
| `docs/design/DESIGN.md` | v2 | 阶段3 | 9 状态色/反AI模板 |
| `docs/design/shape-dashboard.md` | v2 | 阶段3 | 漏斗/趋势 |
| `docs/design/shape-jobs.md` | v2 | 阶段3 | 列表/详情 |
| `docs/design/shape-applications.md` | v2 | 阶段3 | 状态机/时间线 |
| `docs/design/REFERENCE-MAPPING.md` | v2 | 2026-06-24 | +§六营销面参考 |
| `docs/design/REDESIGN-BRIEF.md` | **v1.0 🆕** | 2026-07-15 | 三表面重构基线、设计方案与决策日志 |
| `docs/credible-job-ingestion/` | **v1.0 🆕** | 2026-07-16 | 公开 ATS 调研、实施决策与验证记录 |
| `.agent-ops/PROGRESS.md` | 本文件 | 2026-07-01 | 进度SSOT |
| `.agent-ops/TASK-PIPELINE.md` | ✅ 已更新 | 2026-07-01 | 全阶段状态（含阶段3完成+后端启动） |
| `.agent-ops/STAGE3-PIPELINE.md` | v3 | 2026-07-01 | TASK-016b 完成+视觉优化 |
| `.agent-ops/BLOCKED-LIST.md` | v3 | 2026-07-01 | 营销页已完成，更新阻塞项 |
| `.agent-ops/TASK-VISUAL-OPTIMIZATION-REPORT.md` | v1.0 | 2026-06-30 | 营销页视觉优化完成报告 |
| `.agent-ops/TASK-VISUAL-APPLE-GRADE.md` | v1.0 🆕 | 2026-06-30 | Apple级视觉任务（交GPT） |
| `.agent-ops/TASK-COMPETITOR-ANALYSIS.md` | v1.0 🆕 | 2026-07-01 | Offerbiu内页分析任务（已完成） |

---

## 四、阶段 3 任务状态

| ID | 任务 | 寄存器 | 状态 | 说明 |
|----|------|--------|------|------|
| TASK-012 | 设计初始化 | product | ✅ 完成 | PRODUCT.md / DESIGN.md |
| TASK-013 | 看板 shape | product | ✅ 完成 | |
| TASK-014 | 岗位 shape | product | ✅ 完成 | |
| TASK-015 | 投递 shape | product | ✅ 完成 | |
| **TASK-DESIGN-ALIGN** 🆕 | **设计样式对齐** | 两面 | 🔄 进行中 | **当前焦点**。产品面+营销面样式均未对齐，不能直接 craft |
| TASK-016a | 产品面 craft / 核心前端 | product | ✅ 完成 | TASK-FE-PRODUCT-001 已验收通过，真实 API 接入 |
| TASK-016b | 营销面 craft | brand | ✅ 完成 | 营销页 7 屏骨架已完成，P0 视觉优化和截图验证已补齐 |
| TASK-VISUAL-OPTIMIZATION | 营销页视觉优化 | brand | ✅ 完成 | 内容丰富度、桌面/移动、亮/暗主题、截图验证完成 |
| TASK-017 | critique + audit | 两面 | 🔜 下一步 | 前后端核心闭环后进入质量审查 |
| TASK-018 | polish + harden | 两面 | ⏸️ | 等 017 |

---

## 五、待决策清单（需用户拍板）

| # | 决策项 | 状态 | 背景 |
|---|--------|------|------|
| 1 | 营销面定位语气 | ✅ 已定 | 真实 SaaS 官网；作品集改为独立 `/case-study` |
| 2 | 配色基调 | ✅ 已定 | **双主题（亮+暗可切换）**。亮色默认精调，暗色基于 HSL 推导+9状态色微调 |
| 3 | 设计样式对齐（剩余 8 维度） | ✅ 方向已定 | 统一品牌 Token；官网、产品、案例按不同密度使用 |
| 4 | 产品面参考 | ✅ 已补研究 | Apple/Tesla/Linear/Framer/Stripe/Notion + Huntr/Teal/Simplify/Jobscan |
| 5 | 营销面 hero 方向 | ✅ 已定 | 单一价值主张 + 真实产品循环视频 + 双 CTA |
| 6 | 暗色是否纳入 Demo 范围 | ✅ 已定 | 纳入。走 CSS 变量+next-themes 架构 |

---

## 六、BLOCKED 清单摘要

> 详见 `.agent-ops/BLOCKED-LIST.md`

**BLOCKED-VERIFY**（Codex 做了，需高级智能体/用户验收）：
- craft 渲染效果（产品面+营销面）
- critique 视觉审查
- 响应式 + PWA 验证

**BLOCKED-DO**（需要外部输入）：
- AI 解析真实验证（需 API Key）
- 用户访谈（路径 B 验证窗口）

---

## 七、下一步动作

**当前焦点**：验收已通过，等待用户确认是否提交稳定版本。

1. 修复非阻塞的空订阅表单反馈，或纳入下一轮体验优化。
2. 按用户要求提交稳定版本。
3. 长期自动调度、链接复核、账户同步与通知进入未来路线图。

---

*本文件是活的文档。任何进展，先改这里。*
