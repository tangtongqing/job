# TASK-007 · 数据库表设计

## 背景与目标

TASK-006 系统架构（v2）已完成，明确了：
- SQLite + SQLAlchemy 2.x 同步 ORM
- 状态机原子性方案（事务隔离 + 应用层校验，非悲观锁）
- ApplicationEvent 是漏斗/待办/纠错的共同命脉
- 全同步策略（避免 async/sync 混用）

本任务把 PRD v3 §六数据模型 + TASK-006 架构决策，落地为**完整的数据库物理设计**，可直接用于阶段 4 的 ORM 实现。

**目标**：产出 SQL DDL + SQLAlchemy ORM 模型 + 索引/约束设计 + 迁移脚本说明，可直接照着写代码。

## 输入素材（必读）

- `docs/architecture/system-architecture.md` —— **v2**，重点 §4.1 状态机原子性、§4.2 索引设计、§7.4 迁移预留
- `docs/product/PRD.md` —— v3，重点 §3.3 状态机、§3.3.2 ApplicationEvent、§六数据模型
- `docs/product/PROJECT.md` —— v3，§6 技术栈

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径

- `docs/architecture/database-schema.md`（**新建**，本任务唯一产出）

## 禁止操作

- 不修改 `src/`、`config/`、`data/`、`scripts/`、`tests/` 下任何文件
- 不修改任何已存在文档
- 不创建实际 .py/.sql 代码文件（本任务只产出设计文档）
- 不引入外部依赖

## 实现要求

### 一、文档结构（六个部分）

#### 1. 设计原则与约束
- 基于 SQLite（v2 已确认不用悲观锁）
- 同步 SQLAlchemy Session（v2 已确认）
- 为 PostgreSQL 迁移预留（类型选择要兼容两者）
- 列出从 PRD/架构继承的硬约束（如状态机原子性、事件表分离）

#### 2. 完整 ER 图
- 用 Mermaid `erDiagram` 画出所有实体及关系
- 包含：Job / UserJobAction / Application / ApplicationEvent / Subscription / Company / CrawlLog（采集日志，建议新增）

#### 3. 表结构详细设计（核心）

**每张表必须给出**：
- 表名 + 中文名 + 用途
- 完整字段表（字段名 / SQLite 类型 / PG 对应类型 / 约束 / 默认值 / 说明）
- 主键、外键、唯一约束、检查约束
- 索引（基于 TASK-006 §4.2 的查询模式设计）
- 关系说明（一对多/多对多）

**必须覆盖的表**（基于 PRD v3 §六）：

- **Job**（岗位）—— 注意 v3 新增字段：graduation_year/education/experience/last_verified_at/is_valid/job_category
- **UserJobAction**（用户-岗位关系）—— v3 收窄：只存收藏/待投递，加 ended_at
- **Application**（投递记录）—— v3 删除 offer_result 和 current_round
- **ApplicationEvent**（统一事件表）—— v3 新增，重点表
- **Subscription**（订阅）
- **Company**（公司，可选）
- **CrawlLog**（采集日志，**建议新增**，TASK-006 §7.1 提到的采集日志结构化存储）

#### 4. 状态机与事件表的物理实现（重点）

**4.1 状态枚举值定义**
- 给出 9 个状态的字符串常量（中文 vs 英文 code 的取舍，建议用英文 code 存储中文展示）
- 给出 5 个终态的判断逻辑

**4.2 事件类型枚举**
- status_change / interview / test / material_submit / offer / note / correction
- 每种类型的字段填充规则（哪些字段必填、哪些可空）

**4.3 状态流转的事务实现**（呼应 TASK-006 §4.1）
- 给出具体的 SQL 层面事务伪代码（INSERT ApplicationEvent + UPDATE Application 在同一 BEGIN/COMMIT）
- **重要**：不能用 SELECT FOR UPDATE（v2 已明确 SQLite 不支持），说明用应用层校验

**4.4 漏斗/待办/纠错的查询模式**
- 漏斗查询：从 ApplicationEvent 取 status_change 且非 correction
- 待办查询：从 ApplicationEvent 取未发生的 interview/test/material_submit
- 纠错查询：is_correction=true 的记录
- 每种给出索引建议和示例 SQL

#### 5. 索引策略
- 基于 TASK-006 §4.2 的索引设计，细化每张表的索引
- 特别注意 ApplicationEvent 的索引（它是命脉表，查询频繁）
- SQLite 部分索引（WHERE 子句）的使用说明

#### 6. 初始化与迁移

**6.1 初始化 SQL**
- 给出创建所有表的完整 DDL（SQLite 方言）
- 包含种子数据（如默认配置、状态枚举）

**6.2 Alembic 迁移说明**
- 迁移目录结构（TASK-006 §3 已定 db/migrations/）
- 首次迁移命令
- 未来加字段的迁移示例

**6.3 SQLite → PostgreSQL 迁移注意事项**
- 类型映射（TEXT→VARCHAR、DATETIME→TIMESTAMP、BOOLEAN→BOOLEAN）
- 自增主键差异
- 部分索引语法差异

### 二、质量要求

- **ER 图必须完整**，所有外键关系清晰
- **字段类型要兼容 SQLite 和 PostgreSQL**（避免 SQLite 特有类型）
- **状态枚举要有明确定义**，不能让 status 字段变成自由文本
- **索引设计要有依据**（基于查询模式，不是拍脑袋）
- **事务伪代码要呼应 TASK-006 v2**（不能用悲观锁，用应用层校验）
- **必须包含 CrawlLog 表**（采集日志结构化，TASK-011 安全门禁要用）
- Markdown 格式，SQL 用代码块，中文说明

### 三、与 TASK-006 v2 的对齐检查

产出后必须自查：
- [ ] 是否用了 SELECT FOR UPDATE？（应该**没有**，v2 已删除）
- [ ] ApplicationEvent 表是否完整？（7 种 event_type）
- [ ] UserJobAction 是否只存收藏/待投递？（v3 收窄）
- [ ] Application 是否已删除 offer_result 和 current_round？（v3 删除）
- [ ] 是否新增了 CrawlLog 表？
- [ ] 索引是否覆盖漏斗/待办/纠错三种查询？

## 验证命令

纯文档任务。自查清单（对照上面"与 TASK-006 v2 的对齐检查"）：

- [ ] 六个部分齐全（原则/ER图/表结构/状态机实现/索引/迁移）
- [ ] ER 图完整（7 张表）
- [ ] 每张表字段、约束、索引齐全
- [ ] 状态枚举和事件类型枚举明确定义
- [ ] 事务伪代码用应用层校验（非悲观锁）
- [ ] 漏斗/待办/纠错查询有索引和示例 SQL
- [ ] 初始化 DDL 完整

## 结果文件路径

`docs/architecture/database-schema.md`

## 结果格式（写入 outbox）

```markdown
# TASK-007 执行结果

## 摘要
<2-3 句话概述数据库设计核心决策>

## 修改/新建的文件清单
- docs/architecture/database-schema.md（新建）

## 关键设计决策
- 表数量：...
- ApplicationEvent 索引数：...
- 状态/事件枚举定义方式：...
- 事务方案（呼应 v2）：...

## 与 TASK-006 v2 对齐自查
<逐项打勾>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有，特别是索引选择、枚举设计、迁移兼容性>
```
