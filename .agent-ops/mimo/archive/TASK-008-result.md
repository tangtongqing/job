# TASK-008 执行结果

## 摘要
完成了 API 契约设计文档，覆盖 PRD v3 的 18 个功能点，转化为 25+ 个 REST API 端点，包含统一响应格式、分页筛选参数、状态机流转 API（含 3 个示例）、AI 解析 API（含三级降级），可直接用于 FastAPI 路由实现和前端 TanStack Query 调用。

## 修改/新建的文件清单
- docs/architecture/api-contract.md（新建）

## 关键设计决策

### 端点数量
- **25+ 个端点**，覆盖 7 个模块（Jobs/Dashboard/Applications/UserJobAction/Todo/Subscriptions/Crawler）

### 状态流转 API 设计
- `POST /applications/{id}/transition` 核心端点
- 3 个示例：正常流转 / 非法流转被拒 / 纠错流转
- 事务原子性呼应 TASK-006 v2（应用层校验，非悲观锁）

### AI 解析降级
- `POST /applications/parse-email` 端点
- 三级降级：LLM 高置信度 → 正则解析 → null（前端走快捷交互层）
- `degraded` 标志区分是否降级

## 与 TASK-006/007 对齐自查

- [x] 状态值用英文 code（applied/test/interviewing/...）
- [x] action_type 用英文 code（favorited/to_apply）
- [x] 状态流转 API 的事务说明呼应 TASK-006 v2（非悲观锁）
- [x] AI 解析降级链三级
- [x] 端点覆盖 PRD 全部 18 个功能点

## 自查清单

- [x] 六个部分齐全（原则/约定/端点清单/状态机/AI解析/OpenAPI）
- [x] 所有端点列出（25+ 个）
- [x] 每个端点有请求/响应/错误/示例
- [x] 状态机流转 API 有 3 个示例
- [x] AI 解析 API 有降级说明
- [x] 状态/枚举用英文 code

## 未解决的问题
- 无

## 需要 Codex 判断的风险
- 端点设计是否合理（如是否需要批量操作 API）
- 分页筛选参数是否足够