# JobPulse 前端

JobPulse 前端同时承载真实 SaaS 官网、可交互产品后台与作品集案例页。

## 页面入口

- `/`：产品营销页与真实产品录屏
- `/dashboard`：求职数据看板
- `/jobs`、`/jobs/[id]`：岗位发现与详情
- `/saved`：收藏与待投递
- `/applications`、`/applications/[id]`：投递流程、库外投递补录与招聘通知解析
- `/todo`：近期安排
- `/subscriptions`：岗位订阅规则
- `/crawler`：数据来源与采集状态
- `/case-study`：产品设计案例

线上地址：<https://jobpulse-product-demo.tongqtang.chatgpt.site>

## 本地运行

要求 Node.js 22.13+。

```powershell
npm install
npm run dev -- --webpack --hostname 127.0.0.1 --port 3100
```

如需连接本地 FastAPI，在 `.env.local` 中配置：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100/api/v1
```

未配置时使用公开演示 API。

本地后端默认使用 `8100` 端口。关闭前端时在运行终端按 `Ctrl+C`；完整的前后端启动与关闭说明见 [`../docs/operations/LOCAL-DEVELOPMENT.md`](../docs/operations/LOCAL-DEVELOPMENT.md)。

## 验证与构建

```bash
npm run lint
npm run build
npm run build:sites
node scripts/role-walkthrough-26.mjs
```

- `npm run build`：Next.js 生产构建，Windows 中文路径下固定使用 Webpack，规避 Turbopack 路径问题。
- `npm run build:sites`：生成 Codex Sites 所需的 Cloudflare Worker 兼容产物。
- `node scripts/role-walkthrough-26.mjs`：在本地生产前后端运行时，复测四类角色的 26 项预设结果。

## 技术结构

- Next.js 16 + React 19 + TypeScript
- Tailwind CSS + Framer Motion + Lucide
- `next-themes` 双主题
- vinext + Cloudflare Worker 运行时
- `lib/api.ts` 统一处理后端响应与错误
- `components/marketing/` 是官网唯一实现；`components/app/` 承载产品后台共享组件
- `sites-vite-plugin.ts` 负责在 Sites 构建产物中打包托管元数据

## 线上边界

- 公开站点连接 Railway FastAPI。
- 后台为共享演示环境，没有账号隔离。
- 在线采集触发已关闭，避免匿名访客消耗外部资源。
- 邮件功能只解析用户粘贴的文本；线上未配置任何 LLM 或邮件服务密钥，当前使用本地正则降级。
- 侧栏“重置演示数据”可恢复 24 岗位、5 投递、2 收藏、2 待投递和 3 条订阅。

部署记录见 [`../docs/qa/DEPLOYMENT-2026-07-22.md`](../docs/qa/DEPLOYMENT-2026-07-22.md)。
