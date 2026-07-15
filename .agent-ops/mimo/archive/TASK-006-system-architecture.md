# TASK-006 · 系统架构设计

## 背景与目标

阶段 1（产品定义）已完成并通过评审修订（v3）。本任务是阶段 2（架构设计）的**地基**——后续数据库、API、采集、AI 模块全部依赖本任务的架构决策。

**目标**：产出一份系统架构设计文档，明确分层、技术选型细化、部署拓扑、目录结构落地，可直接指导 TASK-007~011。

## 输入素材（必读）

- `docs/product/PRD.md` —— v3，重点 §三状态机、§四功能点（18 个）、§六数据模型
- `docs/product/PROJECT.md` —— v3，§6 技术栈决策、§5 MVP 范围
- `docs/research/market-analysis.md` —— v3，§5.4 路径 B（本地 Demo + 验证窗口）
- `.agent-ops/STAGE2-PIPELINE.md` —— 阶段 2 关键设计原则（必读）

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径

- `docs/architecture/system-architecture.md`（**新建**，本任务唯一产出）
- 可在 `docs/architecture/` 下新建辅助图片（如需架构图，用 ASCII 或 Mermaid）

## 禁止操作

- 不修改 `src/`、`config/`、`data/`、`scripts/`、`tests/` 下任何文件
- 不修改任何已存在文档（PRD/PROJECT/画像/Job Story/调研/总结）
- 不创建实际代码文件（本任务只产出架构文档，代码在阶段 4）
- 不引入外部依赖

## 实现要求

### 一、文档结构（七个部分）

#### 1. 架构总览
- 一句话架构定位（如"单体应用，模块化分层，本地 Demo 优先"）
- **架构图**（Mermaid 或 ASCII）：展示用户层 / 前端 / 后端 API / 业务模块 / 数据层 / 外部服务（采集源、LLM）
- 关键设计取舍说明（为什么单体不微服务、为什么 SQLite 不 PG 等）

#### 2. 技术栈细化
基于 PROJECT.md §6，细化到具体版本与库：

| 层 | 技术 | 版本 | 关键库 | 选型理由 |
|----|------|------|-------|---------|
| 前端 | Next.js | 14.x (App Router) | shadcn/ui, Tailwind, TanStack Query, Recharts | ... |
| 后端 | FastAPI | 0.110+ | Pydantic v2, SQLAlchemy 2.x, APScheduler | ... |
| 采集 | Playwright + httpx | 最新 | beautifulsoup4/lxml, APScheduler | ... |
| 数据库 | SQLite | 3.x | SQLAlchemy ORM | ... |
| AI | OpenAI/通义/DeepSeek API | - | 官方 SDK | F-C.5 解析 |

> 每个库要写明"为什么选它"和"替代方案"。

#### 3. 系统分层与模块划分

```
src/
├── crawler/          # 采集层
│   ├── adapters/     # 各源适配器（BOSS/牛客/官网）
│   ├── scheduler.py  # APScheduler 调度
│   ├── parser.py     # 清洗与字段提取
│   └── dedup.py      # 去重
├── api/              # API 层（FastAPI 路由）
│   ├── routes/       # 按模块分路由（jobs/applications/dashboard/...）
│   ├── schemas/      # Pydantic 请求/响应模型
│   └── deps.py       # 依赖注入（DB session 等）
├── core/             # 核心业务层
│   ├── statemachine/ # 投递状态机（重点）
│   ├── events/       # ApplicationEvent 写入逻辑
│   └── ai/           # LLM 解析（F-C.5）
├── db/               # 数据层
│   ├── models.py     # SQLAlchemy ORM
│   ├── session.py    # 连接管理
│   └── migrations/   # Alembic 迁移
├── config.py         # 配置（采集频率/LLM Key/阈值）
└── main.py           # 入口
```

**模块职责边界**（每个模块写清"做什么、不做什么、依赖谁"）。

#### 4. 关键流程的架构实现（重点）

针对 PRD 的核心流程，说明**架构层如何落地**：

**4.1 状态机流转的原子性**
- Application.status 更新 + ApplicationEvent 写入必须在**同一事务**内
- 给出伪代码或时序图
- 并发冲突如何处理（乐观锁/时间戳）

**4.2 ApplicationEvent 的写入策略**
- 每次状态变更触发事件写入
- 纠错事件如何标记（is_correction=true）
- 漏斗查询如何排除纠错（索引设计预告）

**4.3 采集流程的事务边界**
- 单次采集：抓取 → 清洗 → 去重 → 入库，哪些步骤事务化
- 失败重试策略

**4.4 AI 解析的降级链**
- LLM 可用 → 解析 → 用户确认 → 入库
- LLM 不可用 → 降级到快捷交互层
- 成本控制（缓存、限流）

#### 5. 部署拓扑

**5.1 本地 Demo（当前路径 B）**
- 前后端如何启动（dev server）
- SQLite 文件位置
- 采集调度如何运行（后台进程 / cron / APScheduler 内嵌）
- 画一个本地部署图

**5.2 未来上线（路径 C，仅预留抽象，不实现）**
- Vercel（前端）+ 云服务器（后端+采集）+ 云数据库
- 抽象层设计：配置切换即可迁移

#### 6. 配置与 secrets 管理
- 配置项清单（采集频率/无回应阈值/LLM 模型/每页条数等）
- secrets 如何管理（.env 文件，不提交 git）
- 不同环境（dev/demo/prod）的配置差异

#### 7. 跨切面关注点
- **日志策略**：采集日志/状态变更日志/AI 调用日志的格式与级别
- **错误处理**：统一异常体系、API 错误响应格式
- **可观测性**：Demo 阶段最小监控（采集成功率、API 响应时间）
- **数据迁移**：SQLite → PostgreSQL 的预留抽象

### 二、质量要求

- **架构图必须清晰**（Mermaid 优先），能用于面试讲述
- **每个技术选型要有理由**，不能只列名字
- **状态机原子性必须给出具体方案**（伪代码或时序图），这是 TASK-007/011 的依据
- **目录结构要落到文件级**，阶段 4 可直接照着建文件
- **Demo 边界要明确**——本地能跑、面试能演示，不为未来过度设计

### 三、与后续任务的衔接说明

在文档末尾，明确本任务为以下任务提供什么输入：
- TASK-007 数据库：依据 §3 目录结构 + §4.1/4.2 事务方案
- TASK-008 API：依据 §3 API 层结构
- TASK-009 采集：依据 §3 crawler 层 + §4.3 采集事务
- TASK-010 AI：依据 §4.4 降级链
- TASK-011 安全门禁：依据 §4 + §7 跨切面

## 验证命令

纯文档任务。自查清单：

- [ ] 七个部分齐全（总览/技术栈/分层/关键流程/部署/配置/跨切面）
- [ ] 架构图存在（Mermaid 或 ASCII）
- [ ] 技术栈细化到版本和库，每个有选型理由
- [ ] 目录结构落到文件级
- [ ] 状态机原子性有具体方案（伪代码/时序图）
- [ ] AI 降级链完整
- [ ] 本地 Demo 部署图清晰
- [ ] 与后续任务的衔接说明存在

## 结果文件路径

`docs/architecture/system-architecture.md`

## 结果格式（写入 outbox）

将以下内容写入 `.agent-ops/mimo/outbox/TASK-006-result.md`：

```markdown
# TASK-006 执行结果

## 摘要
<2-3 句话概述架构核心决策>

## 修改/新建的文件清单
- docs/architecture/system-architecture.md（新建）

## 关键架构决策
- 应用形态：...
- 分层方式：...
- 状态机原子性方案：...
- AI 降级策略：...
- 部署形态：...

## 各部分完成情况
<对照自查清单>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有，特别是技术选型分歧、事务方案细节、AI 成本控制>
```
