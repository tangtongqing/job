# JobPulse M1 公共数据底座收口快照

| 属性 | 内容 |
|---|---|
| 快照日期 | 2026-08-24 |
| 快照性质 | M1 公共招聘雷达数据底座阶段收口，不再在本文继续迭代 |
| Git 分支 | `codex/credible-job-ingestion` |
| Git 标签 | `archive/2026-08-24-m1-foundation` |
| 后续入口 | [项目重构与后续修改计划](../product/PROJECT-RESTRUCTURE-PLAN.md) |

## 1. 本次收口结论

本快照保存“项目从 M0 求职工作台转向国内校招公司招聘雷达”之后，已经完成且可以验证的事实。它不是新 PRD，也不把尚未实现的目标能力描述为现状。

当前可以确认：

- M0 的岗位发现、收藏/待投递、投递状态、事件时间线、近期安排和看板仍可作为演示闭环；
- 海外 Greenhouse 默认来源已经停用，BOSS、猎聘、牛客等受限平台保持关闭；
- 首批 10 家国内目标公司已进入版本化官方来源注册表，所有正式来源仍按 `fail-closed` 保持停用；
- 招商银行应届生和实习生公开接口适配器完成技术验证、完整分页和源端总数对账，但尚未获得“可进入后台调度”的最终结论；
- 公司、招聘活动、多届别、轻量岗位引用、来源快照和公司变化事件的数据模型已经建立；
- Alembic M0 基线与 M1 revision 已建立，旧 SQLite 的严格结构接管、备份恢复、重复运行和跨进程迁移互斥已有测试；
- Windows 本地启动和容器启动已切换到安全迁移入口；
- 公共招聘雷达的快照写入、前后差分、分类、公共 API 和前端页面尚未形成端到端闭环。

## 2. 已完成范围

### 2.1 产品与数据源规则

- 国内校招、春招、秋招、正式校招、暑期实习、日常实习和毕业届别进入正式产品分类；
- 公司官方招聘网站和公开官方接口是优先来源；
- 生产来源禁止通过关键词或数量上限静默截断岗位；
- 来源发现、技术可访问和允许自动调度是三个不同状态；
- 公共层只保存公司、招聘活动、轻量岗位引用和变化证据，完整 JD 仅在用户主动收藏后进入私人工作区。

### 2.2 工程底座

- `config/company_sources.json`：首批公司和官方来源事实源；
- `src/crawler/source_registry.py`：来源注册、配置校验和双重启用门禁；
- `src/crawler/adapters/cmb_campus.py`：招商银行公开接口技术验证适配器；
- `src/db/models.py`：M1 公共招聘雷达模型；
- `alembic/`：现有 M0 schema 基线与 M1 公共模型迁移；
- `src/db/schema_migrations.py`：旧库识别、备份、接管、恢复与迁移互斥；
- `start.ps1`、`Dockerfile`：启动前安全迁移入口；
- 对应来源、适配器、模型、迁移和启动契约测试。

### 2.3 文档底座

- [国内校招数据源策略](../product/DATA-SOURCE-STRATEGY.md)；
- [M1 PRD](../product/PRD-M1.md)；
- [M1 实施计划](../product/M1-IMPLEMENTATION-PLAN.md)；
- [国内校招采集架构](../architecture/domestic-campus-ingestion.md)；
- [国内校招采集工程记录](../engineering/DOMESTIC-CAMPUS-INGESTION.md)。

## 3. 明确未完成范围

以下内容不属于本快照的已交付能力：

1. 招商银行列表结果写入 `SourceSnapshot` 和 `ObservedPositionRef`；
2. 首次基线、重复运行、岗位新增、关闭和重开的幂等差分；
3. 2027/2028 届、正式校招、暑期/日常实习与岗位类别的轻量分类器；
4. 全站今日指标、公司变化流、公司库和公司详情公共 API；
5. 招聘动态首页、公司库、公司详情和数据源健康页面；
6. 浏览器插件收藏与公共轻岗位转私人完整岗位；
7. 账号、个人数据隔离、PostgreSQL 生产执行和真实用户私测；
8. 100 家公司扩展、BOSS/猎聘合作接入和任何访问控制绕过方案。

## 4. 验证基线

本轮收口结果：

- 后端全量测试：`171 passed`；
- M1 模型、迁移与启动安全定向验证包含在全量测试中；
- 前端 ESLint：通过，零错误；
- Next.js 16 生产构建：通过，13 个页面入口完成构建；
- Codex Sites / vinext 生产构建：通过；
- Alembic 当前 revision 与 SQLAlchemy metadata 一致；
- `git diff --check`：通过；
- 本地 Git Bundle 可验证、源码 ZIP 可列出；
- 云端分支和归档标签指向同一收口提交。

测试仍报告 428 条弃用类 warning，主要来自 `datetime.utcnow()` 和依赖兼容提示。它们不阻断本次阶段存档，但应进入后续缺陷与技术债台账，不能视为已经解决。

具体命令和结果由归档目录中的 `RESTORE.md`、`SHA256SUMS.txt` 以及 Git 提交共同保存，本文不复制易变化的绝对路径和哈希值。

## 5. 存档与恢复方式

### Git 权威历史

- 云端分支：`origin/codex/credible-job-ingestion`；
- 不可变标签：`archive/2026-08-24-m1-foundation`；
- GitHub 保存代码、文档、迁移和测试，不保存数据库、密钥、构建缓存和临时验收产物。

### 本地离线存档

本地存档目录保存：

- `jobpulse-2026-08-24-m1-foundation.bundle`：包含版本历史和标签，可恢复 Git 仓库；
- `jobpulse-2026-08-24-m1-foundation-source.zip`：只包含收口提交中的版本化项目文件；
- `SHA256SUMS.txt`：两个归档文件的 SHA-256；
- `RESTORE.md`：恢复与验证步骤。

本地运行数据库位于 `data/` 且不纳入代码存档。数据库需要单独备份时，应在应用停止后使用数据库迁移工具的备份流程，不应把运行中的 SQLite 直接打包进源码快照。

## 6. 继续工作的唯一入口

从本快照之后，不直接在本文追加进度。产品定义、架构、Figma 原型和后续实施的修改顺序统一由[项目重构与后续修改计划](../product/PROJECT-RESTRUCTURE-PLAN.md)管理；功能开发仍以[M1 实施计划](../product/M1-IMPLEMENTATION-PLAN.md)中的故事和验收标准为准。
