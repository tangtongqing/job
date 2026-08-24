# JobPulse 文档中心

从这里找文档。产品定义、研发设计、验收与作品集材料各自只有一个稳定入口；过程任务、临时截图和可再生成产物不进入文档中心。

## 30 秒导航

| 想找什么 | 唯一入口 | 回答的问题 |
|---|---|---|
| 项目章程 / BRD | [PROJECT-CHARTER.md](product/PROJECT-CHARTER.md) | 为什么做、交付形态、投入边界是什么 |
| MRD | [MRD.md](product/MRD.md) | 市场是否存在、目标用户是谁、机会在哪里 |
| M0 当前实现 PRD | [PRD.md](product/PRD.md) / [Word](product/PRD.docx) | 当前已实现产品的流程、状态、功能与 AC 是什么 |
| M1 成熟产品 PRD | [PRD-M1.md](product/PRD-M1.md) | 从共享 Demo 演进为个人 SaaS 需要交付什么 |
| 项目重构与后续修改计划 | [PROJECT-RESTRUCTURE-PLAN.md](product/PROJECT-RESTRUCTURE-PLAN.md) | PRD、架构、Figma、QA 和作品集按什么顺序收口 |
| M1 实施计划 | [M1-IMPLEMENTATION-PLAN.md](product/M1-IMPLEMENTATION-PLAN.md) | 公共招聘雷达、账号、隔离、迁移和私人能力按什么顺序实施 |
| 国内校招数据源策略 | [DATA-SOURCE-STRATEGY.md](product/DATA-SOURCE-STRATEGY.md) | 国内校招分类、官方来源覆盖、公众号和平台边界是什么 |
| 国内校招采集工程记录 | [DOMESTIC-CAMPUS-INGESTION.md](engineering/DOMESTIC-CAMPUS-INGESTION.md) | 首批 10 家来源核验、招商银行适配器和当前阻塞是什么 |
| Figma 高保真原型 | [原型索引](design/HIGH-FIDELITY-PROTOTYPE-INDEX.md) | 设计系统、14 张画面、交互主链与设计缺口 |
| 用户画像 | [PERSONAS.md](product/PERSONAS.md) | 先服务哪类行为人群 |
| 痛点与 JTBD | [JTBD.md](product/JTBD.md) | 用户在什么情境下要完成什么任务 |
| 产品路线图 | [ROADMAP.md](product/ROADMAP.md) | M0 Demo 如何演进到 M1/M2 |
| 系统架构 | [system-architecture.md](architecture/system-architecture.md) | 前后端、数据、部署如何连接 |
| 国内校招采集架构 | [domestic-campus-ingestion.md](architecture/domestic-campus-ingestion.md) | 来源注册表、活动/公告/岗位模型和采集管道如何落地 |
| API 契约 | [api-contract.md](architecture/api-contract.md) | 接口、请求响应和错误语义是什么 |
| 数据库设计 | [database-schema.md](architecture/database-schema.md) | 实体、关系和约束是什么 |
| 设计基线 | [REDESIGN-BRIEF.md](design/REDESIGN-BRIEF.md) | 当前产品与营销面的设计原则 |
| 当前验收结论 | [ACCEPTANCE-REPORT.md](qa/ACCEPTANCE-REPORT.md) | 当前版本是否可演示、还剩什么问题 |
| 安全与测试门禁 | [SECURITY-TEST-GATE.md](qa/SECURITY-TEST-GATE.md) | 安全检查、测试门禁与残余风险是什么 |
| 缺陷台账 | [DEFECT-REGISTER.md](qa/DEFECT-REGISTER.md) | 已知缺陷和技术债是什么 |
| 当前阶段收口快照 | [M1-FOUNDATION-CHECKPOINT-2026-08-24.md](archive/M1-FOUNDATION-CHECKPOINT-2026-08-24.md) | 当前到底完成了什么、没有完成什么、如何恢复 |
| 本地开发 | [LOCAL-DEVELOPMENT.md](operations/LOCAL-DEVELOPMENT.md) | 如何安装、启动、验证和关闭 |
| 简历与面试手册 | [PROJECT-EXPERIENCE-JD-ALIGNED.md](portfolio/PROJECT-EXPERIENCE-JD-ALIGNED.md) | 产品经理 / AI 产品经理项目投递、追问与证据边界 |
| 其他作品集材料 | [portfolio/](portfolio/) | 案例页材料与可复用提示词 |

## 目录职责

```text
docs/
├─ product/       产品定义：章程、MRD、PRD、画像、JTBD、路线图
├─ research/      原始研究、竞品分析、访谈与情景走查
├─ assets/        文档使用的研究证据与 PRD 原型导出；不放验收中间截图
├─ design/        设计系统、页面简报与交互规范
├─ architecture/  系统架构、API、数据库、采集与 AI 模块
├─ engineering/   已完成专项的范围、决策、实施与结果
├─ qa/            验收基线、测试方案、缺陷与部署记录
├─ operations/    本地开发和运维说明
├─ portfolio/     简历、面试、案例页材料；可复用提示词放 prompts/
└─ archive/       仍有决策价值、但不再指导当前实现的历史记录，见 archive/README.md
```

## 文档维护规则

1. PRD、MRD、项目章程和路线图使用固定文件名，不再追加 `final`、`v2`、日期后缀。
2. 当前结论直接更新稳定入口；修订历史写在文件顶部或由 Git 保存。
3. 同一专项不再拆成 `RESEARCH / IMPLEMENTATION / PROGRESS` 三份短文档，统一写成一份工程记录。
4. 自动化截图、浏览器录像、数据库和部署压缩包写入 `output/`，该目录不纳入版本控制。
5. 只有被正式研究报告引用的证据图片才进入 `docs/assets/`；产品运行所需媒体继续放在 `web/public/`。
6. 文档之间使用链接，不复制大段相同内容。

M0 当前实现的可编辑需求源是 [PRD.md](product/PRD.md)，正式 Word 交付是
[PRD.docx](product/PRD.docx)；M1 目标需求源是 [PRD-M1.md](product/PRD-M1.md)。
M1 功能正式发布后，已生效规则需合并回唯一主 PRD。历史版本和重构审计统一进入
[archive/prd/](archive/prd/)，不再与当前版本并列。

2026-08-24 之后的跨文档重构统一由
[PROJECT-RESTRUCTURE-PLAN.md](product/PROJECT-RESTRUCTURE-PLAN.md) 管理；阶段事实以
[M1 公共数据底座收口快照](archive/M1-FOUNDATION-CHECKPOINT-2026-08-24.md)为边界。

## 代码目录

| 目录 | 职责 |
|---|---|
| `src/` | FastAPI 后端：API、领域逻辑、采集、数据库与模型 |
| `web/` | Next.js 前端：官网、产品后台与案例页 |
| `tests/` | 后端自动化测试 |
| `config/` | 采集源配置 |
| `data/` | 本地数据库与运行数据，不纳入版本控制 |
| `output/` | 可再生成的验收/构建产物，不纳入版本控制 |

前端只保留一个 `web/components/marketing/` 实现；带版本后缀的旧目录已删除，避免两套官网组件并存。
