# TASK-QA-001 返工结果（REWORK-001 + REWORK-002）

**完成日期**：2026-07-10
**执行者**：Codex
**决策来源**：`.agent-ops/TASK-QA-001-FINAL-REVIEW.md` Codex Decisions 1-4

---

## 摘要

按验收决策执行了两个 P1 返工：
- REWORK-001：营销页 CTA 链接到 `/dashboard` + 新增 PWA manifest
- REWORK-002：后端 `GET /applications` 返回 job 摘要（company/title），前端列表已对接

前端 build 通过（含 manifest.webmanifest 路由），后端 91 测试通过。

---

## REWORK-001：营销页 CTA + PWA manifest

### 改动

| 文件 | 改动 |
|------|------|
| `web/components/marketing/Hero.tsx` | "免费开始"和"看产品演示"按钮包 `<a href="/dashboard">` |
| `web/components/marketing/Navbar.tsx` | "免费开始"按钮包 `<a href="/dashboard">` |
| `web/app/manifest.ts` | 🆕 PWA manifest（name/short_name/start_url=/dashboard/display=standalone/icons） |
| `web/app/layout.tsx` | metadata 加 `manifest: "/manifest.webmanifest"` |

### 验证
build 输出新增路由 `/manifest.webmanifest`（0 B，static），证明 PWA manifest 生效。

---

## REWORK-002：GET /applications 返回 job 摘要

### 改动

| 文件 | 改动 |
|------|------|
| `src/api/routes/app/applications.py` | `list_applications` 批量 join Job（一次查询避免 N+1），返回 `job: {id, company, title}` |
| 前端 `applications/page.tsx` | 已用 `app.job?.company` 显示（验收智能体已小修对接） |

### 验证
后端全量 `91 passed`。前端 build 通过。

### 不回归证据
- API 测试 17 passed（含 list/transition/batch/events 等核心端点）
- list_applications 响应结构：新增 `job` 摘要字段，不破坏原有字段

---

## 执行的命令与结果

```
# 后端
$ python -m pytest -q
91 passed, 220 warnings in 1.17s

# 前端
$ cd web && npm run build
✓ Generating static pages (11/11)
新增路由：/manifest.webmanifest
```

---

## REWORK-003（P2）状态

未执行。按验收决策，P2 独立安排，需含桌面/移动浏览器截图验证。当前环境无浏览器能力，建议交高级智能体处理。

---

## 需要后续处理

1. **REWORK-002 后端 API 需重新验收**：`GET /applications` 响应结构变了（新增 job 摘要），验收方需确认契约一致性。
2. **REWORK-003 P2 待安排**：含字体/移动导航/趋势/crawler按钮/错误通知 + 截图验证。
3. **后端联调验证**：前端 build 通过但真实后端联调需本地启动确认。

---

*结果产出：2026-07-10 | 等待 REWORK-002 API 验收 + REWORK-003 安排*
