# TASK-FE-PRODUCT-001 · 产品面核心前端接入

## 背景与目标

后端核心链路已完成并通过 Codex 验收：

- `.agent-ops/TASK-BE-REWORK-001-REVIEW.md`
- `.agent-ops/TASK-BE-REWORK-002-FINAL-REVIEW.md`
- `.agent-ops/TASK-BE-CRAWLER-001-FINAL-REVIEW.md`
- `.agent-ops/TASK-BE-AI-001-REVIEW.md`

旧任务 `.agent-ops/mimo/archive/TASK-016-craft.md` 是早期 mock 原型任务，要求“不接真实 API”。当前阶段已经不同：后端 API / 采集 / AI 解析均可用，所以本任务替代旧 craft 任务，目标是实现**产品面核心前端**，接入真实后端 API，并保留可演示的产品工作流。

一句话目标：

> 在 `web/` 中落地 JobPulse 产品面应用，让用户可以查看看板、浏览岗位、管理投递、查看待办、粘贴邮件文本获得 AI 状态建议。

## 产品设计原则

按 `docs/design/PRODUCT.md` 的 product register 执行：

- 工具型产品，不做营销页式大 hero。
- 信息密度适中，优先支持扫描、筛选、比较和重复操作。
- 状态机清晰可读，9 个状态要有稳定颜色/标签。
- 产品面要克制、专业、可信赖；避免渐变文字、玻璃态、装饰大卡片堆砌。
- 页面第一屏就是可用工作台，不做介绍型 landing。

## 输入素材（必读）

- `docs/design/PRODUCT.md`
- `docs/design/DESIGN.md`
- `docs/design/shape-dashboard.md`
- `docs/design/shape-jobs.md`
- `docs/design/shape-applications.md`
- `docs/architecture/api-contract.md`
- `.agent-ops/TASK-BE-AI-001-REVIEW.md`
- `.agent-ops/TASK-BE-CRAWLER-001-FINAL-REVIEW.md`
- `web/README.md`
- `web/package.json`

## 允许读取的路径

- `docs/`
- `.agent-ops/`
- `src/api/`
- `src/schemas/`
- `web/`
- `tests/`

## 允许修改的路径

- `web/app/`
- `web/components/`
- `web/lib/`
- `web/README.md`
- `.agent-ops/mimo/outbox/TASK-FE-PRODUCT-001-result.md`

如确需修改 `web/package.json` / `package-lock.json`，必须在结果文件中说明原因。优先不要新增依赖；当前已有 Next.js、Tailwind、lucide-react、framer-motion、next-themes、class-variance-authority、clsx、tailwind-merge。

## 禁止操作

- 不修改后端 `src/`，除非发现阻断性 API bug，且必须先在结果文件中说明。
- 不修改营销页视觉主线：`web/app/page.tsx` 与 `web/components/marketing/` 默认保持可用。
- 不接入真实外部服务、真实招聘网站、真实 LLM Key。
- 不把 mock 数据伪装成真实 API 数据。允许在 API 不可用时显示明确 error/empty state。
- 不实现登录、支付、团队、多租户、简历生成等非 MVP 能力。
- 不删除 `.agent-ops/`、`docs/`。

## API 接入范围

后端 Base URL 建议：

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

缺省时可默认 `http://localhost:8000/api/v1`。

至少接入以下端点：

### Dashboard

- `GET /dashboard/kpi`
- `GET /dashboard/funnel`
- `GET /dashboard/trend`
- `GET /dashboard/distribution`

### Jobs

- `GET /jobs`
- `GET /jobs/{id}`
- `GET /jobs/stats`
- `POST /jobs/{id}/verify`

### Applications

- `GET /applications`
- `POST /applications`
- `GET /applications/{id}`
- `POST /applications/{id}/transition`
- `POST /applications/batch-transition`
- `GET /applications/{id}/events`
- `POST /applications/parse-email`

### Todo / Crawler

- `GET /todo`
- `POST /crawler/trigger`
- `GET /crawler/logs`

Crawler 页面可作为 P1 简版；P0 是 dashboard/jobs/applications/todo/AI parse。

## 页面范围

实现产品面路由，建议使用 Next.js route group：

```text
web/app/(app)/layout.tsx
web/app/(app)/dashboard/page.tsx
web/app/(app)/jobs/page.tsx
web/app/(app)/jobs/[id]/page.tsx
web/app/(app)/applications/page.tsx
web/app/(app)/applications/[id]/page.tsx
web/app/(app)/todo/page.tsx
web/app/(app)/crawler/page.tsx
```

路由实际 URL 应为：

- `/dashboard`
- `/jobs`
- `/jobs/[id]`
- `/applications`
- `/applications/[id]`
- `/todo`
- `/crawler`

## 实现要求

### 1. App Shell

实现产品面布局：

- 左侧导航或顶部导航，包含 Dashboard / Jobs / Applications / Todo / Crawler。
- 顶部区域显示当前页面标题、关键操作、API 连接状态。
- 页面宽度和信息密度适合桌面工作台。
- 不要把页面整体包进大卡片；页面区域用全宽布局，卡片只用于具体数据块。

### 2. API Client

新增 `web/lib/api.ts` 或等价文件：

- 统一处理 `{data, meta}` / `{error}` envelope。
- 给出 typed-ish TypeScript 类型，至少覆盖本任务用到的响应字段。
- fetch 失败时返回可展示的错误状态，不吞异常。
- 不在 build 阶段强依赖后端在线；页面应在浏览器运行时请求，或明确处理服务端 fetch 失败。

### 3. 状态配置

新增 `web/lib/status-config.ts`：

- 9 个 Application status 的 code / 中文 label / terminal / color class。
- Job status `displaying/closed`。
- 合法流转映射，状态流转菜单只展示合法下一状态。
- 颜色必须呼应 `docs/design/DESIGN.md`，其中 `applied` 使用蓝系。

### 4. Dashboard

`/dashboard`：

- KPI：今日新增岗位、岗位总数、投递总数、待处理投递。
- 漏斗：展示 `applied -> test -> interviewing -> offer_pending -> offer_accepted`。
- 趋势：展示有效进展事件趋势。
- 分布：支持至少一个维度，例如 job_category。
- 必须有 loading / error / empty state。
- 图表可用 SVG/CSS/HTML 实现；不要为了图表新增依赖。

### 5. Jobs

`/jobs`：

- 列表支持分页、关键词、公司、地点、类别、状态等基础筛选。
- 每行展示公司、岗位、地点、薪资、来源、有效性、采集时间。
- 支持跳转详情。
- 支持岗位有效性核验按钮，调用 `POST /jobs/{id}/verify`，有 loading/error。

`/jobs/[id]`：

- 展示 JD、requirement、deadline、apply_url、source、last_verified_at。
- 提供“创建投递”入口，调用 `POST /applications`。

### 6. Applications

`/applications`：

- 列表展示岗位公司、岗位名、当前状态、更新时间。
- 状态 badge 清晰。
- 每行可执行合法状态流转，调用 `POST /applications/{id}/transition`。
- 支持批量流转的最小 UI，调用 `POST /applications/batch-transition`。

`/applications/[id]`：

- 展示投递详情、岗位信息、事件时间线。
- 时间线区分历史事件与未来待办。
- 提供状态流转入口。

### 7. AI Parse Email

在投递页或详情页实现 AI 解析入口：

- 用户粘贴邮件/消息文本。
- 调用 `POST /applications/parse-email`。
- 展示 parsed/company/title/suggested_status/confidence/degraded/matched_application_id/reasoning。
- 明确展示“AI 结果仅为建议，确认后才会更新状态”。
- 如果有 `matched_application_id`，允许用户确认后调用 transition；如果没有匹配，引导用户选择投递。
- 禁止 parse-email 返回后自动流转。

### 8. Todo

`/todo`：

- 调用 `GET /todo`。
- 展示面试、笔试、材料提交等未来待办。
- 展示 days_left、round、job company/title。
- 空态要告诉用户“暂无未来 14 天待办”。

### 9. Crawler 简版

`/crawler`：

- 展示采集日志。
- 提供 trigger source 的简单入口。
- 对 disabled source / error envelope 做友好错误提示。
- 不做真实抓取解释，不引导用户绕过反爬。

## 质量要求

- TypeScript 尽量保持严格，避免 `any` 泛滥。
- 不使用浏览器 alert；用页面内状态提示。
- 每个 P0 页面必须有 loading / error / empty。
- 按钮、状态、操作反馈要稳定，不造成布局跳动。
- 移动端至少不崩；桌面体验优先。
- 使用 lucide-react 图标，不手写装饰 SVG 图标。
- 保留营销页 `/` 可访问。

## 验证命令

请至少执行并在结果文件中记录：

```bash
cd web
npm run lint
npm run build
```

如后端可启动，请额外验证：

```bash
python -m uvicorn src.main:app --reload
cd web
npm run dev
```

并用浏览器检查：

- `/dashboard`
- `/jobs`
- `/applications`
- `/todo`
- `/crawler`

如果无法启动后端或浏览器，请在结果文件中说明，并至少保证 build/lint 通过。

## 验收标准

Codex 验收时将检查：

- `web` build/lint 通过。
- 产品面路由存在且不破坏营销页 `/`。
- API client 正确处理 `{data, meta}` / `{error}`。
- Dashboard / Jobs / Applications / Todo / AI Parse 的核心流程可读、可操作。
- parse-email 不自动流转，必须用户确认。
- 状态 badge 和合法流转与后端状态机一致。
- loading / error / empty state 不缺失。
- 无明显 marketing hero 化、玻璃态、模板感卡片堆砌。

## 结果文件路径

`.agent-ops/mimo/outbox/TASK-FE-PRODUCT-001-result.md`

## 结果格式（Mimo 必须填写）

- 摘要
- 修改/新增文件清单
- 页面与路由清单
- API 接入清单
- 关键交互说明
- 执行的命令与结果
- 未完成/降级项
- 需要 Codex 判断的风险

## 备注

本任务是阶段 3/4 的桥接任务：把已完成的产品设计 shape 和后端 API 变成可演示产品面。完成并验收后，进入阶段 5 的 critique/audit、响应式、PWA、异常态和作品集演示数据收口。
