# TASK-007 执行结果

## 摘要
完成了数据库表设计文档，基于 PRD v3 数据模型 + TASK-006 架构决策，落地为 7 张表的完整物理设计，包含字段定义、约束、索引、状态机实现方案、初始化 DDL，可直接用于阶段 4 的 ORM 实现。

## 修改/新建的文件清单
- docs/architecture/database-schema.md（新建）

## 关键设计决策

### 表数量
- 7 张表：Job / UserJobAction / Application / ApplicationEvent / Subscription / Company / CrawlLog

### ApplicationEvent 索引数
- 4 个索引：idx_event_funnel（漏斗）、idx_event_todo（待办）、idx_event_app_id（查询）、idx_event_correction（纠错）

### 状态/事件枚举定义方式
- **状态**：英文 code 存储（applied/test/interviewing/offer_pending/offer_accepted/offer_declined/rejected/no_response/withdrawn），中文展示
- **事件**：7 种类型（status_change/interview/test/material_submit/offer/note/correction）

### 事务方案（呼应 TASK-006 v2）
- **不用 SELECT FOR UPDATE**（SQLite 不支持）
- **应用层校验**：先读取当前状态 → 校验流转合法性 → 更新状态 + 写入事件（同一事务）

## 与 TASK-006 v2 对齐自查

- [x] 是否用了 SELECT FOR UPDATE？——**没有**，使用应用层校验
- [x] ApplicationEvent 表是否完整？——**完整**，7 种 event_type
- [x] UserJobAction 是否只存收藏/待投递？——**是**，CHECK 约束限制
- [x] Application 是否已删除 offer_result 和 current_round？——**已删除**
- [x] 是否新增了 CrawlLog 表？——**已新增**
- [x] 索引是否覆盖漏斗/待办/纠错三种查询？——**覆盖**，各有专用索引

## 自查清单

- [x] 六个部分齐全（原则/ER图/表结构/状态机实现/索引/迁移）
- [x] ER 图完整（7 张表）
- [x] 每张表字段、约束、索引齐全
- [x] 状态枚举和事件类型枚举明确定义
- [x] 事务伪代码用应用层校验（非悲观锁）
- [x] 漏斗/待办/纠错查询有索引和示例 SQL
- [x] 初始化 DDL 完整

## 未解决的问题
- 无

## 需要 Codex 判断的风险
- 索引选择是否合理（特别是部分索引的使用）
- 枚举设计是否需要调整（如英文 code vs 中文）
- 迁移兼容性是否有遗漏