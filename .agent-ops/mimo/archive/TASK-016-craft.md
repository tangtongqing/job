# TASK-016 · impeccable craft · 高保真实现

## 背景与目标

shape 阶段（TASK-012~015）全部完成，5 份设计文档就绪。本任务执行 `impeccable craft`——把设计简报落地为**生产级高保真前端实现**。

craft 是 impeccable 工作流的核心交付——从设计简报到可运行的真实组件，可在浏览器中迭代验证。

**目标**：产出高保真前端代码（Next.js + shadcn/ui + Tailwind），覆盖 5 个核心页面的核心组件，可在浏览器中查看。

## 输入素材（必读）

- `docs/design/PRODUCT.md` —— 产品定位、页面层级
- `docs/design/DESIGN.md` —— **v2**，色彩系统（9 状态语义色）、排版、组件库、反 AI 模板
- `docs/design/shape-dashboard.md` —— **v2**，看板设计简报
- `docs/design/shape-jobs.md` —— **v2**，岗位列表+详情
- `docs/design/shape-applications.md` —— **v2**，投递管理
- `docs/architecture/system-architecture.md` —— **v2**，§3 web/ 目录结构、技术栈

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径（实际前端代码）

**本次 craft 只产出"高保真原型组件"，不是完整可运行应用**（完整应用在阶段 4）。允许：
- `web/components/ui/` —— shadcn/ui 基础组件（如需自定义）
- `web/components/dashboard/` —— 看板组件
- `web/components/jobs/` —— 岗位组件
- `web/components/applications/` —— 投递组件
- `web/app/(prototype)/` —— 高保真原型页面（用 Mock 数据，不接真实 API）
- `web/lib/mock-data.ts` —— Mock 数据
- `web/lib/status-config.ts` —— 9 状态配置（颜色/图标/标签映射）

## 禁止操作

- 不修改后端代码（src/api, src/core, src/crawler, src/db）
- 不修改任何设计文档（docs/design/, docs/architecture/, docs/product/）
- 不接入真实 API（用 Mock 数据）
- 不修改 package.json 依赖（用已定技术栈：Next.js + shadcn/ui + Tailwind + Recharts + Zustand + lucide-react）

## 实现要求

### 一、核心产出（按优先级）

#### 1. 状态配置层（基础，必做）
`web/lib/status-config.ts`：
- 9 状态的完整配置映射（呼应 DESIGN.md v2 §2.2 色调分组）
- 每个状态：英文 code / 中文展示 / 颜色 / 背景色 / 文字色 / 图标 / 是否终态
- Badge 变体生成函数
- 合法流转规则（基于 PRD §3.3 状态机）

#### 2. Mock 数据层
`web/lib/mock-data.ts`：
- 岗位 Mock（10-15 条，含各状态）
- 投递 Mock（20 条，覆盖 9 状态）
- 事件 Mock（含纠错、未来待办）
- 看板数据 Mock（KPI/漏斗/趋势/分布）

#### 3. 核心组件（按页面）

**共享组件**：
- StatusBadge（状态标签，9 状态语义色）
- JobCard / JobRow（岗位卡片/行）
- ApplicationRow（投递行）
- EmptyState / LoadingSkeleton / ErrorState（三态）

**看板组件**（shape-dashboard）：
- KpiCard（KPI 卡片，无 count-up 动画）
- ActionReminder（行动提醒）
- FunnelChart（投递漏斗）
- TrendChart（有效进展趋势）
- DistributionChart（分布）

**岗位组件**（shape-jobs）：
- JobTable（含 checkbox 批量、投递状态列）
- JobFilter（默认收起的高级筛选）
- JobDetail（结构化 requirement）
- SavedTabs（收藏/待投递 Tabs）

**投递组件**（shape-applications）：
- ApplicationTable（状态 Badge + 快捷流转）
- StatusTransitionMenu（只显示合法下一状态）
- CorrectionDialog（纠错，完整 9 状态选择）
- EventTimeline（即将到来 + 历史 分区）
- AiParseDialog（三级降级 UI）
- TodoView（待办，含标记完成）

#### 4. 原型页面
`web/app/(prototype)/` 下创建可访问的页面：
- `/prototype/dashboard` —— 看板
- `/prototype/jobs` —— 岗位列表
- `/prototype/jobs/[id]` —— 岗位详情
- `/prototype/applications` —— 投递列表
- `/prototype/applications/[id]` —— 投递详情/时间线
- `/prototype/todo` —— 待办

### 二、质量要求

- **9 状态语义色严格按 DESIGN.md v2**（不能自创颜色，applied 用蓝系 #3B82F6）
- **状态流转只显示合法下一状态**（status-config 的流转规则）
- **不用反 AI 模板**（无 count-up 动画、无装饰玻璃态、无等大卡片网格堆砌）
- **每个组件有三态**（空/加载/错误）
- **响应式 ≥1024px**（桌面优先）
- **Mock 数据真实可信**（用真实公司名/岗位，不用 Lorem ipsum）

### 三、验证

实现后需能在浏览器查看：
```bash
cd web
npm install
npm run dev
# 访问 http://localhost:3000/prototype/dashboard
```

自查：
- [ ] 9 状态 Badge 颜色与 DESIGN.md v2 一致
- [ ] 状态流转菜单只显示合法下一状态
- [ ] 三态（空/加载/错误）每个核心组件都有
- [ ] 无反 AI 模板（无 count-up/玻璃态/等大卡片）
- [ ] 看板漏斗/趋势/分布用 Recharts
- [ ] 投递时间线分"即将到来"+"历史"

## 结果文件路径

代码在 `web/` 目录。结果报告写入：
`.agent-ops/mimo/outbox/TASK-016-result.md`

## 结果格式（写入 outbox）

```markdown
# TASK-016 执行结果

## 摘要
<2-3 句话概述 craft 产出>

## 修改/新建的文件清单
<列出 web/ 下新建的文件>

## 关键实现点
- 状态配置：status-config.ts 覆盖 9 状态
- 核心组件数：...
- 原型页面数：6
- Mock 数据：...

## 验证命令与结果
- npm run dev → 访问 /prototype/dashboard 等
- 浏览器查看截图（如有）

## 自查清单结果
<逐项打勾>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有，特别是组件实现与设计简报的偏差>
```
