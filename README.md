# JobPulse

JobPulse 是一个招聘信息聚合与投递管理 SaaS Beta：把分散岗位、收藏决策、投递状态和近期安排收进同一个求职工作台。

## 文档入口

产品文档使用固定文件名，统一从 [`docs/README.md`](docs/README.md) 查找：

| 文档 | 入口 |
|---|---|
| 项目章程 / BRD | [`docs/product/PROJECT-CHARTER.md`](docs/product/PROJECT-CHARTER.md) |
| MRD | [`docs/product/MRD.md`](docs/product/MRD.md) |
| PRD | [`docs/product/PRD.md`](docs/product/PRD.md) / [`PRD.docx`](docs/product/PRD.docx) |
| Figma 高保真原型 | [`docs/design/HIGH-FIDELITY-PROTOTYPE-INDEX.md`](docs/design/HIGH-FIDELITY-PROTOTYPE-INDEX.md) |
| 用户画像 | [`docs/product/PERSONAS.md`](docs/product/PERSONAS.md) |
| JTBD | [`docs/product/JTBD.md`](docs/product/JTBD.md) |
| 路线图 | [`docs/product/ROADMAP.md`](docs/product/ROADMAP.md) |
| 系统架构 | [`docs/architecture/system-architecture.md`](docs/architecture/system-architecture.md) |
| 当前验收报告 | [`docs/qa/ACCEPTANCE-REPORT.md`](docs/qa/ACCEPTANCE-REPORT.md) |

## 在线体验

- SaaS 官网：<https://jobpulse-product-demo.tongqtang.chatgpt.site>
- 产品后台：<https://jobpulse-product-demo.tongqtang.chatgpt.site/dashboard>
- 作品集案例：<https://jobpulse-product-demo.tongqtang.chatgpt.site/case-study>
- 后端健康检查：<https://jobpulse-api-production.up.railway.app/health>

站点已开放为公开访问。线上后台使用共享演示数据，访客操作会影响同一份数据；侧栏可二次确认后恢复标准场景。

项目包含三个彼此独立的界面：

- `/`：面向真实用户的 SaaS 官网，含真实产品录屏。
- `/dashboard`：可完整操作的产品 Demo。
- `/case-study`：面向作品集阅读者的产品设计案例。

## 当前可演示闭环

`发现岗位 → 收藏 / 待投递 → 创建投递 → 更新状态 → 近期安排 → 看板复盘`

同时支持：岗位订阅 CRUD、事件时间线、AI 邮件解析建议（用户确认后才更新）、公开招聘 API 数据采集，以及一键恢复确定性的 Demo 数据。

数据层支持两部分：24 条可离线复现的完整演示快照，以及来自 Figma、Webflow、Intercom、Stripe 公开 Greenhouse Job Board API 的真实岗位。线上公开演示固定使用 24 条快照，并关闭匿名采集触发；本地可按需运行公开来源采集。岗位保留完整 JD、任职要求和官方投递链接；BOSS、牛客等受限平台默认关闭，不绕过登录、验证码或反爬限制。

“邮件解析”是粘贴招聘邮件文本后给出状态建议，不负责收发邮件。线上没有配置 OpenAI、DeepSeek、SMTP、SendGrid 或 Resend 等付费 API；无密钥时自动使用本地正则降级解析，且任何状态变化仍需用户确认。

## 本地启动

要求 Python 3.10+ 与 Node.js 22.13+。

在项目根目录启动后端：

```powershell
python -m pip install -e ".[dev]"
python -m src.db.init_db
python -m uvicorn src.main:app --host 127.0.0.1 --port 8100 --reload
```

另开终端：

```powershell
Set-Location web
npm install
npm run dev -- --webpack --hostname 127.0.0.1 --port 3100
```

打开：

- 官网：[http://127.0.0.1:3100](http://127.0.0.1:3100)
- 产品 Demo：[http://127.0.0.1:3100/dashboard](http://127.0.0.1:3100/dashboard)
- 案例页：[http://127.0.0.1:3100/case-study](http://127.0.0.1:3100/case-study)
- 后端健康检查：[http://127.0.0.1:8100/health](http://127.0.0.1:8100/health)
- API 文档：[http://127.0.0.1:8100/docs](http://127.0.0.1:8100/docs)

关闭服务时，分别在前端和后端终端按 `Ctrl+C`。完整的首次安装、启动、验证、关闭和端口占用处理方式见 [`docs/operations/LOCAL-DEVELOPMENT.md`](docs/operations/LOCAL-DEVELOPMENT.md)。

产品侧栏的“重置演示数据”需要连续点击两次确认。部署到非演示环境时，在 `.env` 中设置：

```env
DEMO_RESET_ENABLED=false
```

未配置环境变量时，前端默认连接线上演示 API。如需联调本地后端，在 `web/.env.local` 配置：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100/api/v1
```

## 验证

```bash
python -m pytest -q
cd web
npm run lint
npm run build
npm run build:sites
node scripts/role-walkthrough-26.mjs
```

当前基线：120 项后端测试通过，前端 ESLint 零错误，14 个 Next.js 路由完成 Next.js 与 Codex Sites 生产构建；26 项专家模拟走查在修复后达到核心 19/23、边界 1/3、全部 20/26。该结果用于产品路径验收，不是用户任务完成率。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、SQLite（可演进 PostgreSQL）
- 前端：Next.js 16、React 19、TypeScript、Tailwind CSS、Framer Motion、Lucide、vinext
- 数据采集：httpx、Playwright、APScheduler
- 演示视频：Playwright 自动操作真实产品并录制 WebM
- 部署：Codex Sites（公开前端）+ Railway（FastAPI 与 SQLite 持久化卷）

## 项目结构

```text
src/       FastAPI 后端与领域逻辑
web/       Next.js 官网、产品后台与案例页
tests/     后端自动化测试
config/    岗位采集源配置
docs/      产品、研究、设计、架构、工程、验收与作品集文档
data/      本地运行数据（不纳入版本控制）
output/    可再生成的验收与构建产物（不纳入版本控制）
```

## 关键设计约束

- 收藏与待投递是两种不同意图；创建投递后自动结束待投递标记。
- 投递状态变化同时写入事件，支持时间线、漏斗、待办与纠错。
- AI 解析只给建议；明确时间经用户确认后，状态和计划事件在同一事务内写入。
- 岗位库之外的投递可以用最小字段补录，一次建立岗位、投递和初始时间线。
- 官网不展示虚构用户数、收入、转化、客户 Logo 或付费权益。

设计基线见 [`docs/design/REDESIGN-BRIEF.md`](docs/design/REDESIGN-BRIEF.md)，API 契约见 [`docs/architecture/api-contract.md`](docs/architecture/api-contract.md)。
线上部署、成本和验收记录见 [`docs/qa/DEPLOYMENT-2026-07-22.md`](docs/qa/DEPLOYMENT-2026-07-22.md)。

## 合规边界

确定性快照用于 Demo 与作品集展示，并在界面中明确标记；真实数据只通过无需登录的公开招聘 API 采集。公开版本没有用户账号隔离，数据为共享演示数据；长期自动调度、通知、账号同步与商业化仍属于后续验证范围。
