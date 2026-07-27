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

> **JobPulse 已公开部署：Codex Sites 承载官网、产品后台与案例页，Railway 承载 FastAPI 和持久化 SQLite；线上共享演示闭环已验收。**

**最后更新**：2026-07-27（4 个 P2 问题已修复；Codex Sites 与 Railway 已发布，本地和线上复验通过）
**当前执行者**：高级智能体（Codex）
**交接文件**：`.agent-ops/HANDOVER-TO-ADVANCED-AGENT.md`
**设计基线**：`docs/design/REDESIGN-BRIEF.md`
**当前焦点**：保持面试演示稳定；长期个人使用能力继续保留在未来路线图

**公开入口**：<https://jobpulse-product-demo.tongqtang.chatgpt.site>

**产品后台**：<https://jobpulse-product-demo.tongqtang.chatgpt.site/dashboard>

---

## 二、阶段总览

| 阶段 | 状态 | 产出 |
|------|------|------|
| 阶段 1 产品定义 | ✅ 完成（v3，经评审修订） | 画像/痛点/PRD/市场分析 |
| 阶段 2 架构设计 | ✅ 完成（v3，含安全测试门禁） | 架构/数据库/API/采集/AI/安全报告 |
| 阶段 3 UI/UX 设计 | ✅ 完成 | 第二版居中产品舞台、持续状态轨迹与三表面设计已落地 |
| 阶段 4 实现 | ✅ 完成 | 收藏/待投递、订阅、Demo 重置、核心产品页面、官网与案例页已实现 |
| 阶段 5 质量 | ✅ 完成 | 113 项后端测试、前端 lint、Next.js 14 路由与 Sites 构建通过；完整产品链路回归通过 |
| 阶段 6 作品集 | ✅ 完成 | 独立 `/case-study` 与 59.4 秒真实 Demo 视频已接入 |
| 阶段 7 线上部署 | ✅ 完成 | Codex Sites 公开前端 + Railway 后端与持久化卷；线上核心流程验收通过 |

> **当前结论**：阶段 1-7 已全部收口；后续仅做面试前巡检，以及登录隔离、定时采集等长期能力。

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
| `docs/qa/DEPLOYMENT-2026-07-22.md` | **v1.0 🆕** | 2026-07-22 | 线上地址、拓扑、成本、付费 API 状态与验收证据 |
| `docs/qa/PRODUCT-WEBSITE-ACCEPTANCE-PLAN.md` | **v1.0 🆕** | 2026-07-27 | 产品功能、网站体验、异常路径、回归与展示彩排的标准验收方案 |
| `docs/qa/ACCEPTANCE-2026-07-27.md` | **v1.0 🆕** | 2026-07-27 | 113 项测试、真实采集、核心链路、移动端与修复回归结论 |
| `docs/qa/TEST-CASES-PRODUCT-WEBSITE.md` | **v1.0 🆕** | 2026-07-27 | 24 项产品与网站核心测试用例及执行结果 |
| `docs/qa/DEFECT-REGISTER.md` | **v1.0 🆕** | 2026-07-27 | 4 个 P2 修复项与 3 个非阻塞技术债 |
| `docs/portfolio/PROJECT-EXPERIENCE-JD-ALIGNED.md` | **v2.5 🆕** | 2026-07-23 | 单一简历与面试手册：截图式能力模块简历版、完整产品流程、产品理论、技术实现、话术与问答 |
| `README.md` / `web/README.md` | 当前版 | 2026-07-22 | 在线入口、本地运行、Sites 构建与公开演示边界 |
| `.agent-ops/PROGRESS.md` | 本文件 | 2026-07-23 | 进度 SSOT |
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
| **TASK-DESIGN-ALIGN** | **设计样式对齐** | 两面 | ✅ 完成 | 品牌 Token 与三表面设计已统一并上线 |
| TASK-016a | 产品面 craft / 核心前端 | product | ✅ 完成 | TASK-FE-PRODUCT-001 已验收通过，真实 API 接入 |
| TASK-016b | 营销面 craft | brand | ✅ 完成 | 营销页 7 屏骨架已完成，P0 视觉优化和截图验证已补齐 |
| TASK-VISUAL-OPTIMIZATION | 营销页视觉优化 | brand | ✅ 完成 | 内容丰富度、桌面/移动、亮/暗主题、截图验证完成 |
| TASK-017 | critique + audit | 两面 | ✅ 完成 | 完整演示与线上流程均已验收 |
| TASK-018 | polish + harden | 两面 | ✅ 完成 | 响应式、视频播放、部署安全与公开访问已收口 |

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

**当前无部署阻塞。**

**需要外部输入的未来事项**：
- 用户访谈（路径 B 验证窗口）
- 若启用真实 LLM 解析，需要用户明确提供密钥并接受费用与隐私影响；当前线上保持无付费 API
- 若转为长期个人使用，需要决定账号体系、数据库与长期托管预算

---

## 七、下一步动作

**当前焦点**：公开演示版本已完成发布与复验，不再扩张当前演示范围。

1. 面试前检查公开站点与 Railway 免费额度状态，并执行一次 Demo 重置。
2. 长期自动调度、账号隔离、数据库迁移、通知与 E2E CI 继续保留在未来路线图。

---

*本文件是活的文档。任何进展，先改这里。*
