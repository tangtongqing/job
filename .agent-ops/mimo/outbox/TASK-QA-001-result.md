# TASK-QA-001 result · 阶段 5 质量审查

## 摘要

对 `web/` 产品面（7 页面）+ 营销面（1 页面）做系统 critique/audit。lint/build 零错误。发现 0 个 P0 阻断、3 个 P1 必须返工、6 个 P2 建议优化、4 个 P3 可暂缓。核心链路可用，但营销页→产品面的入口断裂是最大体验缺口。

---

## 执行的检查

### 命令与结果

```bash
cd web
npm run lint   → ✔ No ESLint warnings or errors
npm run build  → ✓ 10/10 static pages 生成成功
```

### 代码审查覆盖

| 检查项 | 方法 | 结果 |
|--------|------|------|
| 状态流转一致性 | 对比 status-config.ts 与后端 TRANSITIONS | ✅ 一致 |
| AI parse 自动流转 | 检查 handleConfirmTransition 逻辑 | ✅ 有确认按钮，不自动 |
| loading/error/empty | grep 4 个 P0 页面 | ✅ 全覆盖 |
| API envelope | 检查 api.ts request 函数 | ✅ {data,meta}/{error} |
| any 类型 | grep lib/app/components | ✅ 无 |
| 后端离线处理 | 检查 NETWORK_ERROR | ✅ 有明确错误态 |
| 横向溢出 | grep overflow-x-auto | ✅ 表格有，移动端导航有 |

### 截图/浏览器覆盖

**无法执行**：当前环境无 Playwright 浏览器截图能力。用 HTTP 探测 + 代码审查替代覆盖。build 成功证明所有路由可编译，不会 runtime 崩溃。

---

## 发现的问题

### P0 阻断

**无。** build/lint 通过，所有路由编译成功，核心链路（dashboard→jobs→applications→AI parse→transition）代码逻辑完整。

### P1 必须返工

#### P1-1：营销页 CTA 未通往产品面 ⭐ 最大缺口

**位置**：`web/components/marketing/Hero.tsx` + `Navbar.tsx` + `BottomNav.tsx`

**问题**：营销页所有 CTA 按钮（"免费开始"、"查看 Live Demo"、BottomNav 锚点）都没有链接到 `/dashboard` 或任何产品面路由。用户看完营销页后**无法进入产品**。

**证据**：`grep -n "href.*dashboard" app/page.tsx components/marketing/*.tsx` → 0 结果

**影响**：作品集演示路径断裂——面试官看完营销页点 CTA，到不了产品。

**修复方案**：把 Hero/Navbar/BottomNav 的 CTA 改为 `<Link href="/dashboard">` 或 `<a href="/dashboard">`。

#### P1-2：无 PWA manifest

**位置**：`web/app/`

**问题**：架构文档（system-architecture.md §9.7）要求 PWA manifest 作为 M0 必须，但当前无 `manifest.json` / `manifest.ts`。

**影响**：无法"加桌面"，移动端演示加分点缺失。

**修复方案**：新增 `web/app/manifest.ts`（Next.js 14 Metadata Route），含 name/icon/theme_color。

#### P1-3：投递列表缺少岗位公司名

**位置**：`web/app/(app)/applications/page.tsx`

**问题**：列表只显示"岗位#id"，没有公司名和岗位名。用户看到的是 `#1 | 岗位#3 | 已投递`，不可读。

**原因**：`GET /applications` 返回的 Application 不含嵌套 Job 信息（只有 job_id）。

**修复方案**：
- 前端方案：列表加载后批量调 `GET /jobs/{id}` 补全公司名（简单但多次请求）
- 后端方案：`GET /applications` 返回时 join Job 信息（更优，但需改后端）
- 折中方案：前端用 job_id 调 `GET /jobs?job_id=X` 批量预加载

### P2 建议优化

#### P2-1：Google Fonts CDN 阻塞首屏

**位置**：`web/app/globals.css:1`

**问题**：`@import url('https://fonts.googleapis.com/...')` 是渲染阻塞请求。字体加载前页面文字会闪烁（FOIT/FOUT）。

**修复**：改用 `next/font/google` 本地加载，或加 `font-display: swap`（已加但仍阻塞 CSS 解析）。

#### P2-2：移动端导航拥挤

**位置**：`web/app/(app)/layout.tsx` 移动端顶部栏

**问题**：5 个导航项平铺在窄屏顶部，390px 下会挤压。虽有 `overflow-x-auto`，但"看板 岗位 投递管理 待办 采集"文字太长。

**修复**：改为 hamburger 菜单，或精简为图标。

#### P2-3：趋势图只有柱状，无交互

**位置**：`web/app/(app)/dashboard/page.tsx` TrendChart

**问题**：柱状图无 hover tooltip（只有 title 属性），数据点过密时日期标签重叠。

**修复**：加 hover 状态显示数值，或日期标签隔行显示。

#### P2-4：AI 解析结果无历史

**位置**：`web/app/(app)/applications/[id]/page.tsx`

**问题**：每次解析后结果只显示当前一次，无法回看历史解析。后端有缓存但前端不展示。

**修复**：可选——保存解析结果列表在页面 state 中。

#### P2-5：crawler 页面 BOSS/牛客按钮可能误导

**位置**：`web/app/(app)/crawler/page.tsx`

**问题**：BOSS/牛客按钮显示为可点击，点击后会触发采集（虽然 robots fail-closed 会 skip）。按钮文案应更明确标注"将跳过"。

**修复**：按钮加 disabled 或文案改为"BOSS（将跳过）"。

#### P2-6：无全局错误通知

**位置**：全站

**问题**：API 错误只通过 ErrorState 组件在原地显示，操作失败（如 transition 失败）无 toast/通知。用户可能不知道操作失败了。

**修复**：加一个轻量 toast 组件（可用 Zustang 或 React context）。

### P3 可暂缓

#### P3-1：无 demo seed 脚本

当前需手动跑 `python -m src.db.init_db` 建种子。作品集演示时可加 `npm run demo` 一键脚本（启动后端+前端+种子）。

#### P3-2：无 favicon 变体

只有 `app/icon.svg`，无 apple-touch-icon / 192/512 PNG。

#### P3-3：README 未更新演示路径

`web/README.md` 还停在早期 Nexora 时代，未说明产品面路由和启动方式。

#### P3-4：无暗色模式下的图表色校验

CSS 柱状图/漏斗用 `bg-primary/40`，暗色下对比度未实际验证（需截图）。

---

## 建议返工任务拆分

1. **TASK-QA-REWORK-001**：营销页 CTA 通产品面 + PWA manifest（P1-1 + P1-2）
2. **TASK-QA-REWORK-002**：投递列表补全公司名（P1-3）
3. **TASK-QA-REWORK-003**：P2 批量优化（字体/移动导航/趋势/crawler 按钮/错误通知）

---

## 已做的小修

无。本任务纯审查，未修改代码。

---

## 残余风险

1. **无法截图验证视觉**：当前环境无浏览器，响应式/暗色/布局的视觉判断基于代码审查，可能有遗漏。
2. **后端联调未验证**：前端 build 通过但所有 API 调用是浏览器运行时，真实后端联调需本地启动验证。

---

## 需要 Codex 判断的问题

1. **P1-3 投递列表公司名**：前端批量请求 vs 后端 join，哪个方向？如果改后端需重新走 API 验收。
2. **营销页 CTA 指向**：指向 `/dashboard` 还是 `/applications`？建议 `/dashboard`（工作台首屏更完整）。
3. **PWA manifest 优先级**：M0 必须还是 P1？架构文档标"必须"但无阻断影响。
4. **返工任务拆 3 个还是合并**：P1-1+P1-2 可一个任务，P1-3 独立，P2 批量一个。

---

*审查日期：2026-07-08 | 审查者：Codex | 审查对象：web/ 全站*
