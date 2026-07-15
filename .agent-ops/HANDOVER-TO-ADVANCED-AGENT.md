# JobPulse 项目全量交接任务书 · 高级智能体迁移指南

> **本文档是项目从 Codex+验收循环迁移到高级智能体独立接管的完整交接。**
> 高级智能体读此文档 + `PROGRESS.md` 即可恢复全部项目认知，无需对话历史。

---

## 一、项目一句话

JobPulse：面向高频求职大学生的招聘信息聚合 + 投递管理工具。Python FastAPI 后端 + Next.js 14 前端。当前处于阶段 5（质量收口），核心链路已完成。

---

## 二、当前完成状态（截至 2026-07-11）

### 后端（src/）—— ✅ 四大模块全部完成并验收

| 模块 | 文件 | 测试数 | 验收 |
|------|------|--------|------|
| 地基（数据库+状态机+事件） | `src/db/` + `src/core/statemachine/` + `src/core/events/` | 31 | ✅ |
| API 层（jobs/applications/dashboard/todo） | `src/api/routes/app/` + `src/main.py` | 17 | ✅ |
| 采集层（合规+适配器+normalizer+dedup+service） | `src/crawler/` | 24 | ✅ |
| AI 解析层（三级降级+正则+缓存+匹配+parse-email） | `src/core/ai/` | 17 | ✅ |
| **合计** | | **93 passed** | |

### 前端（web/）—— ✅ 营销面 + 产品面完成

| 面 | 路由 | 状态 |
|----|------|------|
| 营销面 | `/`（7 屏落地页 + 双主题） | ✅ build/lint 通过 |
| 产品面 | `/dashboard` `/jobs` `/jobs/[id]` `/applications` `/applications/[id]` `/todo` `/crawler` | ✅ build/lint 通过 |
| PWA | manifest + icon | ✅ |
| P2 polish | next/font + hamburger + toast + crawler disabled | ✅ build 通过 |

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
| 1 | **TASK-QA-REWORK-003 截图缺失** | Codex 无浏览器，无法截 1366×768/390×844 视口 | 高级智能体 |
| 2 | **后端联调未验证** | 前端 build 通过但真实 API 调用需本地启动前后端 | 高级智能体/用户 |
| 3 | **真实爬虫运行** | Codex 无执行环境，需本地配 .env + 跑采集 | 用户本地 |
| 4 | **用户访谈** | Codex 不能和真人对话，路径 B 验证窗口 | 用户亲自 |

### 🟡 中优先级

| # | 事项 | 说明 |
|---|------|------|
| 5 | 订阅 CRUD + favorite/to-apply 端点 | API 契约有定义，后端未实现 |
| 6 | 演示数据脚本 | 需 `npm run demo` 一键启动后端+前端+种子 |
| 7 | README 更新 | web/README.md 还停在早期状态 |
| 8 | 暗色模式视觉验证 | 需截图确认状态色对比度 |

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
└── [配置] package.json / next.config.js / tailwind.config.ts / tsconfig.json
```

---

## 五、如何运行

### 后端

```bash
# 安装依赖
pip install -e .

# 建表 + 种子数据
python -m src.db.init_db

# 启动
uvicorn src.main:app --reload --port 8000

# 测试
python -m pytest
```

### 前端

```bash
cd web
npm install
npm run dev      # 开发
npm run build    # 生产构建
npm run lint     # 检查
```

### 前后端联调

```bash
# 终端1：后端
uvicorn src.main:app --reload --port 8000

# 终端2：前端
cd web && npm run dev

# 浏览器访问
# 前端：http://localhost:3000
# API文档：http://localhost:8000/docs
```

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

1. **补截图**（TASK-QA-REWORK-003 收尾）：启动前后端，截 8 张图（/ + /dashboard + /crawler + /applications，桌面+移动）
2. **前后端联调验证**：确认所有 API 调用真实工作（特别是 AI parse-email + transition 闭环）
3. **补缺端点**：订阅 CRUD + favorite/to-apply（API 契约已定义）
4. **演示数据脚本**：写 `npm run demo` 一键启动
5. **README + 作品集叙事**：更新 web/README.md，写完整的项目故事
6. **真实爬虫**（需用户配合）：配 .env API Key，跑真实采集验证

---

## 八、已知限制（诚实说明）

| 限制 | 影响 | 解法 |
|------|------|------|
| 后端联调未验证 | API 可能有不兼容 | 本地启动前后端实测 |
| 截图未提供 | 视觉问题可能遗漏 | 高级智能体补截图 |
| 真实爬虫未跑 | 采集层只测了 fake | 用户本地配 Key 跑 |
| datetime.utcnow() 弃用 | DeprecationWarning（非错误） | 批量换 datetime.now(UTC) |
| ApplicationMatcher 全表查 | 数据量大时性能差 | 加公司名索引 |
| Google Fonts 已改 next/font | build 时需联网下载字体 | 离线环境需预缓存 |

---

*交接日期：2026-07-11 | 交接方：Codex（主智能体）| 接收方：高级智能体*
