# JobPulse 项目全量交接任务书 · 高级智能体迁移指南

> **本文档是项目从 Codex+验收循环迁移到高级智能体独立接管的完整交接。**
> 高级智能体读此文档 + `PROGRESS.md` 即可恢复全部项目认知，无需对话历史。

---

## 一、项目一句话

JobPulse：面向高频求职大学生的招聘信息聚合 + 投递管理工具。Python FastAPI 后端 + Next.js 16/React 19 前端。阶段 1-7 已完成，项目已公开部署并通过线上验收。

---

## 二、当前完成状态（截至 2026-07-27）

### 线上交付—— ✅ 已公开部署

- 官网 / 产品 / 案例：<https://jobpulse-product-demo.tongqtang.chatgpt.site>
- 后端健康检查：<https://jobpulse-api-production.up.railway.app/health>
- 部署拓扑：Codex Sites 前端 + Railway FastAPI + SQLite 持久化卷
- 公开版本为共享演示环境；在线采集触发关闭，Demo 重置保留
- Railway 无活动付费订阅；线上未配置 LLM 或邮件服务密钥
- 详细记录：`docs/qa/DEPLOYMENT-2026-07-22.md`

### 后端（src/）—— ✅ 四大模块全部完成并验收

| 模块 | 文件 | 测试数 | 验收 |
|------|------|--------|------|
| 地基（数据库+状态机+事件） | `src/db/` + `src/core/statemachine/` + `src/core/events/` | 31 | ✅ |
| API 层（jobs/applications/dashboard/todo） | `src/api/routes/app/` + `src/main.py` | 17 | ✅ |
| 采集层（合规+Greenhouse 公共 API+normalizer+dedup+service） | `src/crawler/` | 32 | ✅ |
| AI 解析层（三级降级+正则+缓存+匹配+parse-email） | `src/core/ai/` | 17 | ✅ |
| **合计** | | **109 passed** | |

本地完整验收数据集可达到 56 条岗位：24 条确定性演示快照 + 32 条来自 Figma、Webflow、Intercom、Stripe 公开 Greenhouse API 的真实岗位。线上固定为 24 条可恢复快照，JD、官方投递链接和来源链接完整，并避免匿名访客触发外部采集。

### 前端（web/）—— ✅ 营销面 + 产品面完成

| 面 | 路由 | 状态 |
|----|------|------|
| 营销面 | `/`（7 屏落地页 + 双主题） | ✅ build/lint 通过 |
| 产品面 | `/dashboard` `/jobs` `/jobs/[id]` `/saved` `/applications` `/applications/[id]` `/todo` `/subscriptions` `/crawler` | ✅ build/lint 通过 |
| PWA | manifest + icon | ✅ |
| Sites 部署 | vinext + Cloudflare Worker 入口 + OG 分享图 | ✅ 公开上线 |

### 文档（docs/）—— ✅ 阶段 1-3 文档齐全

| 类别 | 文件数 | 内容 |
|------|--------|------|
| 产品定义 | 6 | PROJECT/PRD/画像/痛点/市场分析/演进路线 |
| 架构设计 | 6 | 系统架构/数据库/API契约/采集/AI/安全门禁 |
| 设计 | 7 | PRODUCT/BRAND/DESIGN/3份shape/参考映射 |
| 竞品研究 | 4 | 6竞品+Offerbiu首页+内页+市场分析 |

---

## 三、当前未完成 / 待处理事项

### 🔴 高优先级

| # | 事项 | 原因 | 负责方 |
|---|------|------|--------|
| 1 | **长期自动调度** | 线上演示关闭采集触发；尚未产品化受控定时刷新、过期下架与通知 | 后续版本 |
| 2 | **用户访谈** | 路径 B 验证窗口仍需真人样本 | 用户亲自 |

### 🟡 中优先级

| # | 事项 | 说明 |
|---|------|------|
| 3 | 一键启动脚本 | 可补 `npm run demo` 统一启动后端、前端和种子数据 |
| 4 | AI 真实解析 | 三级降级已实现；线上故意不配置付费 API，当前使用正则路径 |
| 5 | 暗色模式回归 | 后续视觉迭代时继续做截图对比 |

### 🟢 低优先级

| # | 事项 |
|---|------|
| 9 | favicon PNG 变体（192/512/apple-touch-icon） |
| 10 | datetime.utcnow() → datetime.now(UTC)（Python 3.12 Deprecation） |

---

## 四、项目文件全景

### 后端结构（src/）

```
src/
├── main.py                     # FastAPI 入口，注册路由+异常+中间件
├── config.py                   # Settings（pydantic-settings，从 .env 读）
├── api/
│   ├── responses.py            # 统一响应封装 + 6种异常 + validation handler
│   └── routes/app/             # 5个路由模块（jobs/applications/dashboard/todo/crawler）
├── core/
│   ├── statemachine/           # 9状态机 + 流转规则 + 原子事务引擎
│   ├── events/                 # ApplicationEvent 写入 + 漏斗/待办查询
│   └── ai/                     # AI解析层（8文件：schemas/prompt/regex/cache/rate_limiter/parser/matcher）
├── crawler/
│   ├── compliance/             # robots(fail-closed) + rate_limiter + retry
│   ├── adapters/               # base + company + boss + nowcoder + factory
│   ├── normalizer.py           # 7类字段规范化
│   ├── dedup.py                # 同源/跨源精确去重
│   ├── service.py              # CrawlService 8步流程
│   ├── verifier.py             # 岗位核验
│   └── scheduler.py            # APScheduler 懒加载
├── db/
│   ├── models.py               # 7表 ORM + CHECK约束 + 部分索引
│   ├── session.py              # engine + SessionLocal + get_db
│   └── init_db.py              # 建表 + 种子数据
└── schemas/
    └── models.py               # Pydantic schemas（含 ApplicationListItem 无N+1）
```

### 前端结构（web/）

```
web/
├── app/
│   ├── (app)/                  # 产品面路由组
│   │   ├── layout.tsx          # App Shell（侧边导航+hamburger+toast）
│   │   ├── dashboard/          # 看板
│   │   ├── jobs/ + [id]/       # 岗位列表+详情
│   │   ├── applications/ + [id]/  # 投递列表+详情(AI解析+时间线)
│   │   ├── todo/               # 待办
│   │   └── crawler/            # 采集管理
│   ├── globals.css             # CSS变量（双主题+状态色+keyframes）
│   ├── layout.tsx              # 根布局（next/font + ThemeProvider）
│   ├── manifest.ts             # PWA
│   └── page.tsx                # 营销落地页
├── components/
│   ├── app/                    # shared(Badge/Loading/Error/Empty/useApi) + toast
│   ├── marketing/              # 10个营销页组件
│   ├── theme-provider/toggle   # 亮暗主题
│   └── ui/button.tsx
├── lib/
│   ├── api.ts                  # API Client（16端点，统一envelope）
│   ├── status-config.ts        # 9状态配置（code/label/color/nextStatuses）
│   ├── dashboard-data.ts       # 演示数据（可配置）
│   └── utils.ts                # cn() 类名合并
├── worker/index.ts              # Codex Sites Cloudflare Worker 入口
└── [配置] package.json / next.config.ts / vite.config.ts / tailwind.config.ts / tsconfig.json
```

---

## 五、如何运行

### 后端

```powershell
# 安装依赖
python -m pip install -e ".[dev]"

# 建表 + 种子数据
python -m src.db.init_db

# 启动
python -m uvicorn src.main:app --host 127.0.0.1 --port 8100 --reload

# 测试
python -m pytest
```

### 前端

```powershell
Set-Location web
npm install
npm run dev -- --webpack --hostname 127.0.0.1 --port 3100
npm run build    # 生产构建
npm run lint     # 检查
npm run build:sites  # Codex Sites 构建
```

### 前后端联调

```powershell
# 终端1：后端
python -m uvicorn src.main:app --host 127.0.0.1 --port 8100 --reload

# 终端2：前端
Set-Location web
npm run dev -- --webpack --hostname 127.0.0.1 --port 3100

# 浏览器访问
# 前端：http://127.0.0.1:3100
# 后端健康检查：http://127.0.0.1:8100/health
# API文档：http://127.0.0.1:8100/docs
```

关闭时分别在两个运行终端按 `Ctrl+C`。若终端已关闭但端口仍被占用，请按 [`docs/operations/LOCAL-DEVELOPMENT.md`](../docs/operations/LOCAL-DEVELOPMENT.md) 中的安全关闭步骤处理。

---

## 六、关键设计决策（不要推翻）

| 决策 | 理由 |
|------|------|
| SQLite 优先 | 零配置本地优先，为 PG 迁移预留抽象层 |
| 9 状态机 + 5 终态 | 投递全流程精确管理，终态可纠错回流 |
| robots fail-closed | 合规优先，无法确认允许时禁止抓取 |
| BOSS/牛客不抓取 | 合规骨架，不做登录/验证码/反爬 |
| AI 三级降级 | LLM→正则→parsed=false，无 Key 也能用 |
| AI 不自动流转 | parse-email 只建议，用户确认才 transition |
| 双主题（亮+暗） | CSS 变量切换，next-themes |
| 营销面 vs 产品面隔离 | brand register vs product register |
| Offerbiu 差异化 | 不做简历/AI匹配，深化采集+状态机+看板 |

---

## 七、给高级智能体的建议工作顺序

1. **面试前巡检**：确认公开站点与 Railway 在线，执行 Demo 重置并走一次主链路。
2. **长期使用设计**：若用户确认长期使用，再实现账号隔离、数据库迁移、定时刷新、失败重试与通知。
3. **扩展公开来源**：只接入有官方公共 API/明确许可的 ATS；继续保持 BOSS/牛客关闭。
4. **AI 真实解析**：只有用户明确接受费用与隐私影响后才配置 API Key；保留用户确认门槛。
5. **成本管理**：Railway 免费试用结束前决定停止服务或升级，并在付费计划设置用量上限。

---

## 八、已知限制（诚实说明）

| 限制 | 影响 | 解法 |
|------|------|------|
| 自动调度未产品化 | 本地真实岗位由采集页手动触发；公开版已关闭采集触发 | 后续加入持久化调度、刷新策略与权限控制 |
| 公开版本共享数据 | 访客操作会互相影响 | 长期版增加登录与用户数据隔离 |
| Railway 免费试用 | 额度或试用期结束后服务可能暂停 | 面试前巡检；长期版明确预算 |
| 公开来源覆盖有限 | 当前只有四个 Greenhouse 来源 | 逐个验证官方 ATS 接口后扩展 |
| 1 条真实岗位无结构化要求 | 原始 JD 没有独立要求标题 | 保留完整 JD，不推测或伪造 |
| datetime.utcnow() 弃用 | DeprecationWarning（非错误） | 批量换 datetime.now(UTC) |
| ApplicationMatcher 全表查 | 数据量大时性能差 | 加公司名索引 |
| Google Fonts 已改 next/font | build 时需联网下载字体 | 离线环境需预缓存 |

---

*最后更新：2026-07-22 | 维护方：Codex（主智能体）*
