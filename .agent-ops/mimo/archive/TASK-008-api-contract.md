# TASK-008 · API 契约设计

## 背景与目标

TASK-006 系统架构（v2）+ TASK-007 数据库表设计（v2）已完成。本任务把 PRD v3 的 18 个功能点 + 数据库 7 张表，转化为**完整的 REST API 契约**，可直接用于：
- 后端 FastAPI 路由实现（阶段 4）
- 前端 TanStack Query 调用（阶段 4）
- OpenAPI 文档自动生成

**目标**：产出 API 契约文档，覆盖所有端点、请求/响应模型、错误码、状态机流转 API。

## 输入素材（必读）

- `docs/architecture/system-architecture.md` —— **v2**，重点 §3 API 层结构、§4.1 状态机 API
- `docs/architecture/database-schema.md` —— **v2**，重点 §3 表结构、§4 枚举值（英文 code）
- `docs/product/PRD.md` —— v3，§四 18 个功能点

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径

- `docs/architecture/api-contract.md`（**新建**，本任务唯一产出）

## 禁止操作

- 不修改 `src/`、`config/`、`data/`、`scripts/`、`tests/` 下任何文件
- 不修改任何已存在文档
- 不创建实际代码文件

## 实现要求

### 一、文档结构（六个部分）

#### 1. API 设计原则
- RESTful 风格
- 资源命名规范（复数名词、kebab-case）
- 统一响应格式（成功/错误）
- 分页/筛选/排序的统一参数
- 认证说明（Demo 阶段无认证，但说明未来扩展点）

#### 2. 统一约定
**2.1 基础信息**
- Base URL：`http://localhost:8000/api/v1`
- 内容类型：`application/json`
- 字符集：UTF-8

**2.2 统一响应格式**
```json
// 成功
{ "data": {...}, "meta": {"page": 1, "pageSize": 20, "total": 100} }

// 错误
{ "error": {"code": "INVALID_TRANSITION", "message": "...", "details": {...}} }
```

**2.3 统一分页参数**：page / page_size / 排序 sort / 筛选 filter

**2.4 错误码体系**：按 HTTP 状态码 + 业务错误码（如 INVALID_TRANSITION / NOT_FOUND / VALIDATION_ERROR）

#### 3. 端点清单（核心）

按 PRD 18 个功能点组织，**每个端点必须给出**：
- HTTP 方法 + 路径
- 简述（对应 PRD 功能点 F-X.X）
- 请求参数（path / query / body）
- 请求体 Schema（Pydantic 风格）
- 响应 Schema
- 错误码（该端点特有的）
- 示例（请求 + 响应各一个）

**必须覆盖的端点**（按模块）：

**模块 A 岗位（Jobs）**
- `GET /jobs` 岗位列表（筛选/排序/分页）— F-A.3
- `GET /jobs/{id}` 岗位详情 — F-A.4
- `POST /jobs/{id}/verify` 手动触发核验 — F-A.6
- `GET /jobs/stats` 采集统计（今日新增/收录总数）

**模块 B 看板（Dashboard）**
- `GET /dashboard/kpi` KPI 卡片数据 — F-B.1
- `GET /dashboard/funnel` 投递漏斗 — F-B.2
- `GET /dashboard/trend` 有效进展趋势 — F-B.3
- `GET /dashboard/distribution` 分布维度 — F-B.4

**模块 C 投递管理（Applications）**
- `POST /applications` 创建投递（从待投递升级）— F-C.1
- `GET /applications` 投递列表
- `GET /applications/{id}` 投递详情（含时间线）— F-C.2
- `POST /applications/{id}/transition` 状态流转（**核心**）— F-C.1
- `POST /applications/{id}/correction` 状态纠错 — F-C.1
- `GET /applications/{id}/events` 事件时间线 — F-C.2
- `GET /applications/{id}/todo` 该投递的待办 — F-C.6
- `POST /applications/parse-email` AI 解析邮件 — F-C.5

**模块 D 用户-岗位关系（UserJobAction）**
- `POST /jobs/{id}/favorite` 收藏 — F-C.4
- `DELETE /jobs/{id}/favorite` 取消收藏
- `POST /jobs/{id}/to-apply` 标记待投递 — F-C.4
- `GET /user/favorites` 收藏列表
- `GET /user/to-apply` 待投递列表

**模块 E 待办（Todo）**
- `GET /todo` 统一待办视图（所有投递的笔试/面试/材料）— F-C.6

**模块 F 订阅（Subscriptions）**
- `GET /subscriptions` 订阅列表 — F-D.1
- `POST /subscriptions` 创建订阅
- `PUT /subscriptions/{id}` 更新订阅
- `DELETE /subscriptions/{id}` 删除订阅

**模块 G 采集管理（Crawler）**
- `POST /crawler/trigger` 手动触发采集
- `GET /crawler/logs` 采集日志

#### 4. 状态机流转 API（重点，单独详述）

**`POST /applications/{id}/transition`** 是核心端点，必须详细说明：
- 请求体：`{ to_status, note?, is_correction?, correction_reason? }`
- 业务规则：校验流转合法性（基于 PRD §3.3 状态机）
- 成功响应：更新后的 Application + 写入的 ApplicationEvent
- 错误码：INVALID_TRANSITION（含 from/to 详情）
- **重要**：呼应 TASK-006 v2 §4.1 和 TASK-007 v2 §4.3，事务原子性
- 给出 3 个示例：正常流转 / 非法流转被拒 / 纠错流转

#### 5. AI 解析 API（F-C.5，单独详述）

**`POST /applications/parse-email`**：
- 请求体：`{ email_text: string }` 或 `{ screenshot: base64 }`
- 响应：解析结果（公司/岗位/建议状态/置信度）+ 是否降级标志
- 三级降级说明（呼应 TASK-006 v2 §4.4）：
  - LLM 高置信度 → 返回 parsed
  - 正则解析 → 返回 parsed + degraded=true
  - 全失败 → 返回 null（前端走快捷交互层）

#### 6. OpenAPI 集成说明
- FastAPI 自动生成 `/docs` 和 `/openapi.json`
- Pydantic 模型即 Schema
- 给出 1-2 个 Pydantic 模型示例（JobResponse / TransitionRequest）

### 二、质量要求

- **状态枚举值必须用英文 code**（呼应 TASK-007 v2，不能用中文）
- **状态流转 API 必须详细**（3 个示例：正常/非法/纠错）
- **AI 解析 API 必须体现降级链**
- **错误响应格式统一**
- **每个端点对应 PRD 功能点**（可追溯）
- **分页/筛选参数统一**

### 三、与 TASK-006/007 v2 的对齐检查

- [ ] 状态值用英文 code？（applied/test/interviewing/...）
- [ ] action_type 用英文 code？（favorited/to_apply）
- [ ] 状态流转 API 的事务说明是否呼应 TASK-006 v2（非悲观锁）？
- [ ] AI 解析降级链是否三级？
- [ ] 端点是否覆盖 PRD 全部 18 个功能点？

## 验证命令

纯文档任务。自查清单：
- [ ] 六个部分齐全
- [ ] 所有端点列出（约 25-30 个）
- [ ] 每个端点有请求/响应/错误/示例
- [ ] 状态机流转 API 有 3 个示例
- [ ] AI 解析 API 有降级说明
- [ ] 状态/枚举用英文 code

## 结果文件路径

`docs/architecture/api-contract.md`

## 结果格式（写入 outbox）

```markdown
# TASK-008 执行结果

## 摘要
<2-3 句话概述 API 设计核心>

## 修改/新建的文件清单
- docs/architecture/api-contract.md（新建）

## 关键设计决策
- 端点数量：...
- 状态流转 API 设计：...
- AI 解析降级：...

## 与 TASK-006/007 v2 对齐自查
<逐项打勾>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有>
```
