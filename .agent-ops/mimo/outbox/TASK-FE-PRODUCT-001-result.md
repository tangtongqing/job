# TASK-FE-PRODUCT-001 产品面前端完成报告

**完成日期**：2026-07-08
**执行者**：Codex
**任务来源**：`.agent-ops/mimo/inbox/TASK-FE-PRODUCT-001-app-core.md`
**结论**：产品面 7 个页面全部实现，接入 16 个后端端点，build/lint 零错误。

---

## 摘要

在 `web/` 落地 JobPulse 产品面应用：看板、岗位列表/详情、投递管理/详情、待办、采集管理，全部接入真实后端 API，保留营销页 `/` 可访问。

---

## 修改/新增文件清单

| 文件 | 内容 |
|------|------|
| `web/lib/api.ts` | API Client（统一 {data,meta}/{error}，typed 类型，16 端点） |
| `web/lib/status-config.ts` | 9 状态配置（code/label/terminal/color/nextStatuses + 漏斗顺序） |
| `web/components/app/shared.tsx` | StatusBadge/Loading/ErrorState/EmptyState/useApi Hook |
| `web/app/(app)/layout.tsx` | App Shell（左侧导航 + 顶部栏 + 主题切换） |
| `web/app/(app)/dashboard/page.tsx` | 看板（KPI 4 卡 + 漏斗 + 趋势柱状图 + 分布） |
| `web/app/(app)/jobs/page.tsx` | 岗位列表（筛选 + 分页 + 核验按钮） |
| `web/app/(app)/jobs/[id]/page.tsx` | 岗位详情（JD/要求 + 创建投递） |
| `web/app/(app)/applications/page.tsx` | 投递列表（状态流转 + 批量流转） |
| `web/app/(app)/applications/[id]/page.tsx` | 投递详情（时间线 + AI邮件解析 + 状态流转） |
| `web/app/(app)/todo/page.tsx` | 待办（未来14天 + days_left） |
| `web/app/(app)/crawler/page.tsx` | 采集管理（触发 + 日志 + 合规提示） |

---

## 页面与路由清单

| 路由 | 类型 | 功能 |
|------|------|------|
| `/dashboard` | Static | KPI/漏斗/趋势/分布 |
| `/jobs` | Static | 岗位列表筛选分页 |
| `/jobs/[id]` | Dynamic | 岗位详情+创建投递 |
| `/applications` | Static | 投递列表+流转+批量 |
| `/applications/[id]` | Dynamic | 详情+时间线+AI解析 |
| `/todo` | Static | 未来待办 |
| `/crawler` | Static | 采集触发+日志 |

---

## API 接入清单

| 端点 | 接入页面 |
|------|---------|
| GET /dashboard/kpi | 看板 |
| GET /dashboard/funnel | 看板 |
| GET /dashboard/trend | 看板 |
| GET /dashboard/distribution | 看板 |
| GET /jobs | 岗位列表 |
| GET /jobs/{id} | 岗位详情 |
| GET /jobs/stats | （已接入 api.ts，页面可扩展） |
| POST /jobs/{id}/verify | 岗位列表核验 |
| GET /applications | 投递列表 |
| POST /applications | 岗位详情创建投递 |
| GET /applications/{id} | 投递详情 |
| POST /applications/{id}/transition | 投递列表+详情 |
| POST /applications/batch-transition | 投递列表批量 |
| GET /applications/{id}/events | 投递详情（含在 getApplication 响应） |
| POST /applications/parse-email | 投递详情 AI 解析 |
| GET /todo | 待办 |
| POST /crawler/trigger | 采集管理 |
| GET /crawler/logs | 采集管理 |

---

## 关键交互说明

1. **AI 邮件解析**：粘贴文本 → AI 返回建议（公司/状态/置信度/降级标记）→ 显示"仅为建议"警告 → 用户确认后才调 transition。**禁止自动流转**。
2. **状态流转**：每行只展示合法下一状态（getNextStatuses），终态显示"终态"不可流转。
3. **批量流转**：多选 → 选目标状态 → 一次批量调用。
4. **时间线**：区分状态变更（primary 色）/ 纠错（orange 色），含 correction_reason。
5. **loading/error/empty**：每个 P0 页面都有三种状态。

---

## 执行的命令与结果

### npm run build
```
✓ Generating static pages (10/10)

Route (app)                              Size     First Load JS
┌ ○ /                                    64.7 kB         152 kB
├ ○ /applications                        4.72 kB        99.2 kB
├ ƒ /applications/[id]                   2.99 kB        94.2 kB
├ ○ /crawler                             1.81 kB          93 kB
├ ○ /dashboard                           5.38 kB        92.5 kB
├ ○ /jobs                                4.93 kB        99.4 kB
├ ƒ /jobs/[id]                           5.21 kB        92.3 kB
└ ○ /todo                                4.4 kB         98.8 kB
```

### npm run lint
```
✔ No ESLint warnings or errors
```

---

## 未完成/降级项

- 后端未启动时页面会显示"无法连接到后端服务"错误态（设计如此，API client 明确处理网络错误）。
- 趋势图用 CSS 柱状图实现（任务允许，不新增图表库依赖）。
- 订阅 CRUD / favorite 端点未接入（不在本任务范围）。

---

## 需要 Codex 判断的风险

1. **SSR fetch**：页面标记 "use client"，在浏览器运行时请求 API。build 阶段不强依赖后端（设计如此）。如果需要 SSR 数据预取，需要改造为 server component + fetch。
2. **API 错误处理**：useApi Hook 捕获 ApiRequestError 显示错误态，但没有全局 toast/notification 系统。如果需要更友好的错误反馈，需加 notification 组件。

---

*结果产出：2026-07-08 | 等待 Codex 验收*
