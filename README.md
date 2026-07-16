# JobPulse

JobPulse 是一个招聘信息聚合与投递管理 SaaS Beta：把分散岗位、收藏决策、投递状态和近期安排收进同一个求职工作台。

项目包含三个彼此独立的界面：

- `/`：面向真实用户的 SaaS 官网，含真实产品录屏。
- `/dashboard`：可完整操作的产品 Demo。
- `/case-study`：面向作品集阅读者的产品设计案例。

## 当前可演示闭环

`发现岗位 → 收藏 / 待投递 → 创建投递 → 更新状态 → 近期安排 → 看板复盘`

同时支持：岗位订阅 CRUD、事件时间线、AI 邮件解析建议（用户确认后才更新）、公开招聘 API 数据采集，以及一键恢复确定性的 Demo 数据。

当前数据层由两部分组成：24 条可离线复现的完整演示快照，以及来自 Figma、Webflow、Intercom、Stripe 公开 Greenhouse Job Board API 的真实岗位。真实岗位保留完整 JD、任职要求（原网页有明确标题时）和官方投递链接；BOSS、牛客等受限平台默认关闭，不绕过登录、验证码或反爬限制。

## 本地启动

要求 Python 3.10+ 与 Node.js 18+。

```bash
python -m pip install -e ".[dev]"
python -m src.db.init_db
python -m uvicorn src.main:app --reload
```

另开终端：

```bash
cd web
npm install
npm run dev
```

打开：

- 官网：[http://localhost:3000](http://localhost:3000)
- 产品 Demo：[http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- 案例页：[http://localhost:3000/case-study](http://localhost:3000/case-study)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

产品侧栏的“重置演示数据”需要连续点击两次确认。部署到非演示环境时，在 `.env` 中设置：

```env
DEMO_RESET_ENABLED=false
```

前端默认请求 `http://127.0.0.1:8000/api/v1`；如后端使用其他端口，在 `web/.env.local` 配置：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100/api/v1
```

## 验证

```bash
python -m pytest -q
cd web
npm run lint
npm run build
```

当前基线：107 项后端测试通过，前端 ESLint 零警告，14 个 Next.js 路由完成生产构建。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、SQLite（可演进 PostgreSQL）
- 前端：Next.js 14、TypeScript、Tailwind CSS、Framer Motion、Lucide
- 数据采集：httpx、Playwright、APScheduler
- 演示视频：Playwright 自动操作真实产品并录制 WebM

## 关键设计约束

- 收藏与待投递是两种不同意图；创建投递后自动结束待投递标记。
- 投递状态变化同时写入事件，支持时间线、漏斗、待办与纠错。
- AI 解析只给建议，不自动改变投递状态。
- 官网不展示虚构用户数、收入、转化、客户 Logo 或付费权益。

设计基线见 [`docs/design/REDESIGN-BRIEF.md`](docs/design/REDESIGN-BRIEF.md)，API 契约见 [`docs/architecture/api-contract.md`](docs/architecture/api-contract.md)。

## 合规边界

确定性快照用于本地 Demo 与作品集展示，并在界面中明确标记；真实数据只通过无需登录的公开招聘 API 采集。长期自动调度、通知、账号同步与商业化仍属于后续验证范围。
