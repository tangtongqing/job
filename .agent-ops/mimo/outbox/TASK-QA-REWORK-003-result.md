# TASK-QA-REWORK-003 result

## Summary

完成 5 项 P2 polish：next/font 字体加载、移动端 hamburger 菜单、趋势图标签/hover、crawler disabled 控制、全局 toast 通知。lint/build 零错误。**截图无法执行**（环境无浏览器），诚实报告此限制。

## Modified Files

| 文件 | 改动 |
|------|------|
| `web/app/globals.css` | 移除 Google Fonts @import（P2-1） |
| `web/app/layout.tsx` | 改用 next/font Inter + Instrument Serif（P2-1） |
| `web/app/(app)/layout.tsx` | 移动端导航改 hamburger 菜单（P2-2）+ 集成 ToastProvider（P2-5） |
| `web/components/app/toast.tsx` | 🆕 全局 toast 通知组件（P2-5） |
| `web/app/(app)/applications/page.tsx` | transition + batch 集成 toast（P2-5） |
| `web/app/(app)/jobs/[id]/page.tsx` | create application 集成 toast（P2-5） |
| `web/app/(app)/crawler/page.tsx` | trigger 集成 toast（P2-5） |

> P2-3（趋势图）和 P2-4（crawler disabled）在此前编辑中已完成。

## Requirement-by-Requirement Evidence

### 1. Font loading
- 移除 `@import url('https://fonts.googleapis.com/...')`
- 改用 `next/font/google` 的 `Inter` + `Instrument_Serif`，设置 CSS 变量 `--font-body`/`--font-display`
- `display: "swap"` 保证 FOUT 友好
- **build 通过，字体不再阻塞渲染**

### 2. Mobile app navigation
- 移动端横向滚动文字导航替换为 hamburger 菜单（Menu/X 图标）
- 菜单含全部 5 个路由 + 返回首页
- 键盘可访问（aria-label, aria-expanded, role=menu/menuitem）
- 选中路由后自动关闭（onClick setMenuOpen(false)）

### 3. Dashboard trend
- 每个柱有 hover tooltip（显示 count + date）
- 日期标签隔行显示（390px 下可读）
- build 通过

### 4. Crawler safety clarity
- BOSS/牛客按钮 `disabled` + `cursor-not-allowed` + 文案"不可用，将跳过"
- 不触发 crawl 请求
- 企业官网源正常可用

### 5. Operation feedback
- 🆕 `ToastProvider` + `useToast` context（零依赖）
- 集成到 App Shell（ToastProvider 包 children）
- transition/batch/create application/crawler trigger 都有 success/error toast
- 现有 inline error 保留，不静默失败

## Commands and Results

```
$ cd web && npm run lint
✔ No ESLint warnings or errors

$ cd web && npm run build
✓ 11/11 static pages
Route /applications 4.8 kB, /crawler 2.56 kB, /dashboard 5.75 kB
```

## Visual Evidence

| file | route | viewport | verified behavior |
|---|---|---|---|
| — | — | — | **无法截图** |

**截图无法执行的真实原因**：当前执行环境无浏览器/Playwright 截图能力。无法启动 `npm run dev` + 浏览器捕获 1366×768 和 390×844 视口。

代码改动已通过 build 验证（所有路由编译成功）。但按任务要求，**不声称视觉证据已完成**。如需截图，需交具备浏览器能力的智能体或本地手动验证。

## Remaining Risks or Blockers

1. **截图未提供**：任务明确要求截图才能验收通过。建议交高级智能体补截图。
2. **Toast 动画**：用了 `animate-in` class，如 Tailwind 未启用 `tailwindcss-animate` 插件的 `animate-in`，toast 不会有入场动画（不影响功能）。
3. **后端联调**：toast 的真实 success/error 反馈需后端在线验证。
