# API 契约设计

> TASK-008 产出。基于 PRD v3 的 18 个功能点 + 数据库 7 张表，转化为完整的 REST API 契约。
>
> ---
> **版本**：v2（主智能体校准版）
> **v2 修订说明**：v1 结构完整（25+ 端点 + 状态机 3 示例 + AI 三级降级），但存在 8 处硬伤，v2 集中修订：
> 1. **【严重】岗位 status 枚举值 `active` 不存在**：v1 响应示例用了 `"status": "active"`，但 TASK-007 v2 枚举只有 `displaying` / `closed`。这是数据契约不一致，后端校验会失败。v2 全部改为 `displaying`
> 2. **【中】transition 示例 2 用 `favorited` 当 to_status**：这是类型错误（favorited 是 action_type 不是投递状态）。v2 改为"终态回退"的合法非法示例（offer_accepted→applied）
> 3. **【中】transition 端点没说事务原子性**：补充呼应 TASK-006 v2 §4.1 + TASK-007 v2 §4.3
> 4. **【小】CONFLICT 错误码缺 HTTP 状态码**：补 409
> 5. **【小】`/correction` 端点与 transition 冗余**：标注为废弃别名，统一用 transition
> 6. **【小】GET /jobs 的 status 参数中文注释**：改为英文 code
> 7. **【小】parse-email 的 matched_application_id 匹配逻辑未说明**：补充
> 8. **【小】缺批量 transition 端点**：F-C.5 需要，补充 `POST /applications/batch-transition`

---

## 一、API 设计原则

| 原则 | 说明 |
|------|------|
| RESTful 风格 | 资源导向，HTTP 方法语义化 |
| 资源命名 | 复数名词、kebab-case（如 `/api/v1/applications`） |
| 统一响应 | 成功 `{data, meta}` / 错误 `{error}` |
| 分页筛选 | 统一参数 `page / page_size / sort / filter` |
| 认证 | Demo 阶段无认证，未来可扩展 JWT |

---

## 二、统一约定

### 2.1 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://127.0.0.1:8100/api/v1` |
| 内容类型 | `application/json` |
| 字符集 | UTF-8 |

### 2.2 统一响应格式

```json
// 成功响应
{
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}

// 错误响应
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "不允许从 applied 流转到 favorited",
    "details": {
      "from_status": "applied",
      "to_status": "favorited"
    }
  }
}
```

### 2.3 统一分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页条数（最大 100） |
| sort | string | `-updated_at` | 排序字段（前缀 `-` 表示降序） |
| filter | string | - | 筛选条件（JSON 格式） |

### 2.4 错误码体系

| HTTP 状态码 | 业务错误码 | 说明 |
|-------------|-----------|------|
| 400 | VALIDATION_ERROR | 请求参数校验失败 |
| 400 | INVALID_TRANSITION | 状态流转非法 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 冲突（如重复投递） |
| 422 | UNPROCESSABLE_ENTITY | 业务规则校验失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 三、端点清单

### 模块 A：岗位（Jobs）

#### GET /jobs — 岗位列表

**对应 PRD**：F-A.3 岗位列表与筛选

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | int | 否 | 页码 |
| page_size | query | int | 否 | 每页条数 |
| sort | query | string | 否 | 排序（默认 `-collected_at`） |
| keyword | query | string | 否 | 关键词搜索 |
| company | query | string | 否 | 公司筛选 |
| location | query | string | 否 | 地点筛选 |
| salary_min | query | int | 否 | 最低薪资 |
| salary_max | query | int | 否 | 最高薪资 |
| job_category | query | string | 否 | 岗位方向 |
| graduation_year | query | string | 否 | 毕业年份 |
| education | query | string | 否 | 学历要求 |
| is_intern | query | bool | 否 | 是否实习 |
| is_fresh | query | bool | 否 | 是否应届 |
| source | query | string | 否 | 来源平台 |
| status | query | string | 否 | 岗位状态英文 code：`displaying` / `closed` |
| is_valid | query | bool | 否 | 是否有效 |

**响应 Schema**：

```json
{
  "data": [
    {
      "id": 1,
      "company": "字节跳动",
      "title": "产品经理实习",
      "location": "北京",
      "salary": "200-250/天",
      "job_category": "product",
      "graduation_year": "2025",
      "education": "本科",
      "is_intern": true,
      "is_fresh": true,
      "source": "boss",
      "collected_at": "2026-06-22T10:00:00Z",
      "deadline": "2026-07-15T23:59:59Z",
      "last_verified_at": "2026-06-22T08:00:00Z",
      "is_valid": true,
      "status": "displaying",
      "user_action": {
        "action_type": "favorited",
        "created_at": "2026-06-22T12:00:00Z"
      }
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150
  }
}
```

**示例**：

```bash
GET /api/v1/jobs?page=1&page_size=10&company=字节跳动&is_intern=true
```

---

#### GET /jobs/{id} — 岗位详情

**对应 PRD**：F-A.4 岗位详情页

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 岗位 ID |

**响应 Schema**：

```json
{
  "data": {
    "id": 1,
    "company": "字节跳动",
    "title": "产品经理实习",
    "location": "北京",
    "salary": "200-250/天",
    "jd": "负责抖音电商产品...",
    "requirement": "1. 本科及以上学历...",
    "apply_url": "https://jobs.bytedance.com/...",
    "source": "boss",
    "source_url": "https://www.zhipin.com/job_detail/...",
    "job_category": "product",
    "graduation_year": "2025",
    "education": "本科",
    "experience": "无经验要求",
    "collected_at": "2026-06-22T10:00:00Z",
    "published_at": "2026-06-20T00:00:00Z",
    "deadline": "2026-07-15T23:59:59Z",
    "last_verified_at": "2026-06-22T08:00:00Z",
    "is_valid": true,
    "is_intern": true,
    "is_fresh": true,
    "status": "displaying",
    "user_action": {
      "action_type": "favorited",
      "created_at": "2026-06-22T12:00:00Z"
    },
    "application": {
      "id": 1,
      "status": "applied",
      "applied_at": "2026-06-22T14:00:00Z"
    }
  }
}
```

---

#### POST /jobs/{id}/verify — 手动触发核验

**对应 PRD**：F-A.6 岗位有效性核验

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 岗位 ID |

**响应 Schema**：

```json
{
  "data": {
    "id": 1,
    "is_valid": true,
    "last_verified_at": "2026-06-22T15:00:00Z"
  }
}
```

---

#### GET /jobs/stats — 采集统计

**对应 PRD**：F-B.1 KPI 卡片

**响应 Schema**：

```json
{
  "data": {
    "today_new": 25,
    "total": 1500,
    "valid": 1200,
    "invalid": 300
  }
}
```

---

### 模块 B：看板（Dashboard）

#### GET /dashboard/kpi — KPI 卡片数据

**对应 PRD**：F-B.1 核心 KPI 卡片

**响应 Schema**：

```json
{
  "data": {
    "today_new_jobs": 25,
    "total_jobs": 1500,
    "total_applications": 45,
    "pending_applications": 12,
    "by_status": {
      "applied": 8,
      "test": 2,
      "interviewing": 2
    }
  }
}
```

---

#### GET /dashboard/funnel — 投递漏斗

**对应 PRD**：F-B.2 投递转化漏斗

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| date_from | query | string | 否 | 开始日期（ISO 格式） |
| date_to | query | string | 否 | 结束日期（ISO 格式） |

**响应 Schema**：

```json
{
  "data": {
    "funnel": [
      { "status": "applied", "count": 45, "rate": 1.0 },
      { "status": "test", "count": 20, "rate": 0.444 },
      { "status": "interviewing", "count": 10, "rate": 0.5 },
      { "status": "offer_pending", "count": 3, "rate": 0.3 },
      { "status": "offer_accepted", "count": 2, "rate": 0.667 }
    ],
    "total_applications": 45
  }
}
```

**说明**：
- `rate` = 当前阶段数量 / 上一阶段数量（第一个为 1.0）
- 排除纠错记录（`is_correction = false`）

---

#### GET /dashboard/trend — 有效进展趋势

**对应 PRD**：F-B.3 有效进展趋势

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| days | query | int | 否 | 天数（默认 7） |

**响应 Schema**：

```json
{
  "data": {
    "trend": [
      { "date": "2026-06-16", "count": 2 },
      { "date": "2026-06-17", "count": 0 },
      { "date": "2026-06-18", "count": 3 },
      { "date": "2026-06-19", "count": 1 },
      { "date": "2026-06-20", "count": 2 },
      { "date": "2026-06-21", "count": 0 },
      { "date": "2026-06-22", "count": 1 }
    ],
    "total": 9
  }
}
```

**说明**：只统计进入 test/interviewing/offer_pending 的事件

---

#### GET /dashboard/distribution — 分布维度

**对应 PRD**：F-B.4 分布维度

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| dimension | query | string | 是 | 维度（job_category/location/company_category） |
| date_from | query | string | 否 | 开始日期 |
| date_to | query | string | 否 | 结束日期 |

**响应 Schema**：

```json
{
  "data": {
    "dimension": "job_category",
    "distribution": [
      { "label": "产品", "count": 15, "rate": 0.333 },
      { "label": "技术", "count": 20, "rate": 0.444 },
      { "label": "设计", "count": 5, "rate": 0.111 },
      { "label": "运营", "count": 5, "rate": 0.111 }
    ],
    "total": 45
  }
}
```

---

### 模块 C：投递管理（Applications）

#### POST /applications — 创建投递

**对应 PRD**：F-C.1 投递状态机

**请求体**：

```json
{
  "job_id": 1,
  "notes": "通过 BOSS 直聘投递"
}
```

**响应 Schema**：

```json
{
  "data": {
    "id": 1,
    "job_id": 1,
    "status": "applied",
    "applied_at": "2026-06-22T14:00:00Z",
    "updated_at": "2026-06-22T14:00:00Z",
    "notes": "通过 BOSS 直聘投递"
  }
}
```

**错误码**：
- `NOT_FOUND`（404）：岗位不存在
- `CONFLICT`（409）：该岗位已有非终态投递（呼应 TASK-007 v2 的 `idx_app_one_active_per_job` 唯一约束）
  - 响应 details 包含 `existing_application_id`，前端可引导用户跳转到已有投递

---

#### POST /applications/manual — 补录岗位库外投递

**对应需求**：跨平台投递统一管理

**请求体**：

```json
{
  "company": "Linear",
  "title": "Product Manager, Core Experience",
  "location": "Remote",
  "source_url": "https://linear.app/careers/example",
  "applied_at": "2026-07-28T12:00:00Z",
  "notes": "官网投递，英文简历 v3"
}
```

`company`、`title` 必填；其余字段可选。`source_url` 必须使用 `http://` 或 `https://`。

**响应**：返回新建的投递详情，关联岗位的 `source` 固定为 `manual`。

**原子性保证**：

- 单次请求创建手动岗位、`applied` 投递和初始状态事件；
- 任一步失败时整次回滚，不留下孤立岗位或无时间线的投递；
- 同一手动岗位已有非终态投递时返回 `CONFLICT`。

---

#### GET /applications — 投递列表

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | int | 否 | 页码 |
| page_size | query | int | 否 | 每页条数 |
| status | query | string | 否 | 状态筛选（逗号分隔多个） |
| sort | query | string | 否 | 排序（默认 `-updated_at`） |

**响应 Schema**：

```json
{
  "data": [
    {
      "id": 1,
      "job_id": 1,
      "job": {
        "company": "字节跳动",
        "title": "产品经理实习",
        "location": "北京"
      },
      "status": "interviewing",
      "applied_at": "2026-06-20T10:00:00Z",
      "updated_at": "2026-06-22T15:00:00Z",
      "notes": null
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 45
  }
}
```

---

#### GET /applications/{id} — 投递详情（含时间线）

**对应 PRD**：F-C.2 投递时间线

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 投递 ID |

**响应 Schema**：

```json
{
  "data": {
    "id": 1,
    "job_id": 1,
    "job": {
      "company": "字节跳动",
      "title": "产品经理实习",
      "location": "北京",
      "salary": "200-250/天"
    },
    "status": "interviewing",
    "applied_at": "2026-06-20T10:00:00Z",
    "updated_at": "2026-06-22T15:00:00Z",
    "notes": null,
    "events": [
      {
        "id": 1,
        "event_type": "status_change",
        "from_status": null,
        "to_status": "applied",
        "occurred_at": "2026-06-20T10:00:00Z",
        "is_correction": false,
        "note": null
      },
      {
        "id": 2,
        "event_type": "status_change",
        "from_status": "applied",
        "to_status": "test",
        "occurred_at": "2026-06-21T09:00:00Z",
        "is_correction": false,
        "note": "收到笔试邀请"
      },
      {
        "id": 3,
        "event_type": "status_change",
        "from_status": "test",
        "to_status": "interviewing",
        "occurred_at": "2026-06-22T15:00:00Z",
        "is_correction": false,
        "note": "笔试通过，进入面试"
      }
    ]
  }
}
```

---

#### POST /applications/{id}/transition — 状态流转 ⭐ 核心端点

**对应 PRD**：F-C.1 投递状态机

**请求体**：

```json
{
  "to_status": "interviewing",
  "note": "由招聘通知确认",
  "scheduled_at": "2026-08-02T10:30:00+08:00",
  "scheduled_event_type": "interview",
  "round": 1
}
```

`scheduled_at` 与 `scheduled_event_type` 必须同时出现；目标状态为 `interviewing` 时事件类型必须为 `interview`，目标状态为 `test` 时必须为 `test`。

**响应 Schema**：

```json
{
  "data": {
    "application": {
      "id": 1,
      "status": "interviewing",
      "updated_at": "2026-08-02T02:00:00Z"
    },
    "event": {
      "id": 3,
      "event_type": "status_change",
      "from_status": "applied",
      "to_status": "interviewing",
      "occurred_at": "2026-08-02T02:00:00Z",
      "is_correction": false
    },
    "scheduled_event": {
      "id": 4,
      "event_type": "interview",
      "scheduled_at": "2026-08-02T02:30:00Z",
      "occurred_at": null,
      "round": 1,
      "note": "由招聘通知确认"
    }
  }
}
```

**错误码**：
- `INVALID_TRANSITION`：非法状态流转（含 from/to 详情）
- `VALIDATION_ERROR`：计划时间缺少事件类型，或状态与事件类型不匹配
- `NOT_FOUND`：投递不存在

> ⚠️ **v2 补充：事务原子性保证**（呼应 TASK-006 v2 §4.1 + TASK-007 v2 §4.3）
> - 本端点保证 **Application.status 更新 + 状态事件 + 可选计划事件在同一事务内**，要么全部成功，要么全部回滚
> - 使用**应用层校验**（非悲观锁，SQLite 不支持行级锁）
> - 前端**无需重试逻辑**——失败时数据库状态不变，可安全重试

**示例 1：正常流转**

```bash
POST /api/v1/applications/1/transition
{
  "to_status": "interviewing",
  "note": "收到面试邀请"
}

# 成功响应
{
  "data": {
    "id": 1,
    "status": "interviewing",
    "updated_at": "2026-06-22T15:00:00Z"
  }
}
```

**示例 2：非法流转被拒（v2 修正：用真实的流转非法，而非类型错误）**

```bash
# 场景：用户想把已接受的 Offer 回退到面试中（终态不可流转，除非纠错）
POST /api/v1/applications/1/transition
{
  "to_status": "interviewing"
}
# 此时 application.status = "offer_accepted"

# 错误响应（409 Conflict）
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "终态不可流转，如需纠正请使用纠错模式",
    "details": {
      "from_status": "offer_accepted",
      "to_status": "interviewing",
      "is_terminal": true,
      "hint": "设置 is_correction=true 可执行纠错"
    }
  }
}
```

**示例 3：纠错流转**

```bash
POST /api/v1/applications/1/transition
{
  "to_status": "interviewing",
  "is_correction": true,
  "correction_reason": "误操作标记为拒绝"
}

# 成功响应
{
  "data": {
    "id": 1,
    "status": "interviewing",
    "updated_at": "2026-06-22T15:00:00Z",
    "event": {
      "id": 4,
      "event_type": "correction",
      "from_status": "rejected",
      "to_status": "interviewing",
      "occurred_at": "2026-06-22T15:30:00Z",
      "is_correction": true,
      "correction_reason": "误操作标记为拒绝"
    }
  }
}
```

---

#### POST /applications/batch-transition — 批量状态流转（v2 新增）

**对应 PRD**：F-C.5 低成本状态更新（批量操作）

**请求体**：
```json
{
  "application_ids": [1, 2, 3],
  "to_status": "applied",
  "note": "批量标记已投递"
}
```

**响应 Schema**：
```json
{
  "data": {
    "succeeded": [1, 3],
    "failed": [
      { "application_id": 2, "error_code": "INVALID_TRANSITION", "message": "终态不可流转" }
    ],
    "total": 3,
    "success_count": 2,
    "fail_count": 1
  }
}
```

**说明**：
- **部分失败不中断**：合法的流转成功，非法的返回失败原因
- **每条独立事务**：避免一个失败导致整批回滚
- **不支持纠错批量**：纠错需逐条执行（避免误操作放大）

---

#### POST /applications/{id}/correction — 状态纠错（v2 标注：废弃别名）

> ⚠️ **v2 决策**：本端点与 `POST /applications/{id}/transition` + `is_correction=true` **功能完全重叠**，造成 API 冗余和前端困惑。
> **统一用 transition 端点**，本端点保留仅为向后兼容，文档中标注废弃。
> 前端**不应**调用此端点，统一用 transition。

**对应 PRD**：F-C.1 状态纠错机制

**请求体**：
```json
{
  "to_status": "interviewing",
  "correction_reason": "误操作标记为拒绝"
}
```

**说明**：等价于 `POST /applications/{id}/transition` + `is_correction=true`。**已废弃，请用 transition。**

---

#### GET /applications/{id}/events — 事件时间线

**对应 PRD**：F-C.2 投递时间线

**响应 Schema**：

```json
{
  "data": [
    {
      "id": 1,
      "event_type": "status_change",
      "from_status": null,
      "to_status": "applied",
      "round": null,
      "scheduled_at": null,
      "occurred_at": "2026-06-20T10:00:00Z",
      "is_correction": false,
      "correction_reason": null,
      "note": null
    },
    {
      "id": 2,
      "event_type": "interview",
      "from_status": null,
      "to_status": null,
      "round": 1,
      "scheduled_at": "2026-06-25T14:00:00Z",
      "occurred_at": null,
      "is_correction": false,
      "correction_reason": null,
      "note": "一面"
    }
  ]
}
```

---

#### POST /applications/parse-email — AI 解析邮件 ⭐ 亮点端点

**对应 PRD**：F-C.5 低成本状态更新

**请求体**：

```json
{
  "email_text": "您好，恭喜您通过字节跳动产品经理实习的笔试，现邀请您参加面试..."
}
```

**响应 Schema（三级降级）**：

```json
// LLM 高置信度
{
  "data": {
    "parsed": true,
    "company": "字节跳动",
    "title": "产品经理实习",
    "suggested_status": "interviewing",
    "interview_time": "2026-08-02T10:30:00+08:00",
    "confidence": 0.92,
    "degraded": false,
    "matched_application_id": 1
  }
}

// 正则解析（降级）
{
  "data": {
    "parsed": true,
    "company": "字节跳动",
    "title": null,
    "suggested_status": "interviewing",
    "interview_time": "2026-08-02T10:30:00+08:00",
    "confidence": 0.5,
    "degraded": true,
    "matched_application_id": 1
  }
}

// 全失败
{
  "data": {
    "parsed": false,
    "company": null,
    "title": null,
    "suggested_status": null,
    "interview_time": null,
    "confidence": 0,
    "degraded": true,
    "matched_application_id": null
  }
}
```

**三级降级说明**：
1. **LLM 高置信度**：`degraded=false`，`confidence >= 0.7`
2. **正则解析**：`degraded=true`，`confidence=0.5`
3. **全失败**：`parsed=false`，前端走快捷交互层

> ⚠️ **v2 补充：matched_application_id 匹配逻辑**
> `matched_application_id` 的生成规则：
> 1. AI/正则解析出 `company` + `title` 后，后端按**模糊匹配**查询 `application` 表
> 2. 匹配规则：公司名包含关系 + 岗位名相似度（如 `字节跳动` 匹配 `字节`）
> 3. 返回最匹配的 application_id；无匹配或多个匹配时返回 `null`
> 4. 前端拿到 `matched_application_id` 后：
>    - 有值：展示"是否更新这家公司的投递状态？"供用户确认
>    - 为 null：在投递详情页使用当前投递作为确认对象，不允许解析结果自行新建未知投递
>
> **重要**：解析结果仅作**建议**，最终流转必须用户确认；存在明确计划时间时，确认操作会把状态事件和计划事件一起写入（防止 AI 误判或部分写入污染数据）。

---

### 模块 D：用户-岗位关系（UserJobAction）

#### POST /jobs/{id}/favorite — 收藏

**对应 PRD**：F-C.4 收藏与待投递区分

**响应 Schema**：

```json
{
  "data": {
    "id": 1,
    "job_id": 1,
    "action_type": "favorited",
    "created_at": "2026-06-22T12:00:00Z"
  }
}
```

**错误码**：
- `NOT_FOUND`：岗位不存在
- `CONFLICT`：已收藏

---

#### DELETE /jobs/{id}/favorite — 取消收藏

**响应**：`204 No Content`

---

#### POST /jobs/{id}/to-apply — 标记待投递

**对应 PRD**：F-C.4 收藏与待投递区分

**响应 Schema**：

```json
{
  "data": {
    "id": 2,
    "job_id": 1,
    "action_type": "to_apply",
    "created_at": "2026-06-22T13:00:00Z"
  }
}
```

#### DELETE /jobs/{id}/to-apply — 移出待投递

**响应**：`204 No Content`。重复调用保持幂等。

创建该岗位的投递记录后，系统也会自动结束活跃的 `to_apply` 标记；收藏状态不受影响。

---

#### GET /user/favorites — 收藏列表

**响应 Schema**：

```json
{
  "data": [
    {
      "id": 1,
      "job_id": 1,
      "job": {
        "company": "字节跳动",
        "title": "产品经理实习",
        "location": "北京",
        "is_valid": true
      },
      "created_at": "2026-06-22T12:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 15
  }
}
```

---

#### GET /user/to-apply — 待投递列表

**响应 Schema**：同收藏列表

---

### 模块 E：待办（Todo）

#### GET /todo — 统一待办视图

**对应 PRD**：F-C.6 下一步待办视图

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| days | query | int | 否 | 未来天数（默认 7） |

**响应 Schema**：

```json
{
  "data": [
    {
      "event_id": 2,
      "application_id": 1,
      "event_type": "interview",
      "scheduled_at": "2026-06-25T14:00:00Z",
      "round": 1,
      "note": "一面",
      "job": {
        "company": "字节跳动",
        "title": "产品经理实习"
      },
      "days_left": 3
    },
    {
      "event_id": 3,
      "application_id": 2,
      "event_type": "test",
      "scheduled_at": "2026-06-23T10:00:00Z",
      "round": null,
      "note": "笔试",
      "job": {
        "company": "腾讯",
        "title": "产品策划实习"
      },
      "days_left": 1
    }
  ],
  "meta": {
    "total": 2
  }
}
```

---

### 模块 F：订阅（Subscriptions）

#### GET /subscriptions — 订阅列表

**对应 PRD**：F-D.1 订阅规则

**响应 Schema**：

```json
{
  "data": [
    {
      "id": 1,
      "keyword": "产品经理",
      "company": "字节跳动",
      "location": "北京",
      "created_at": "2026-06-22T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 5
  }
}
```

---

#### POST /subscriptions — 创建订阅

**请求体**：

```json
{
  "keyword": "产品经理",
  "company": "字节跳动",
  "location": "北京"
}
```

**响应**：`201 Created`

---

#### PUT /subscriptions/{id} — 更新订阅

**请求体**：同创建

**响应**：`200 OK`

---

#### DELETE /subscriptions/{id} — 删除订阅

**响应**：`204 No Content`

---

### 模块 F.1：演示环境（Demo）

#### POST /demo/reset — 恢复完整演示场景

创建缺失的数据库结构，清空产品数据并写入确定性的岗位、收藏/待投递、投递时间线、未来待办与订阅。生产或长期使用环境应通过 `DEMO_RESET_ENABLED=false` 关闭。

```json
{
  "data": {
    "message": "Demo 数据已重置",
    "jobs": 8,
    "applications": 5,
    "saved_jobs": 4,
    "subscriptions": 3
  }
}
```

---

### 模块 G：采集管理（Crawler）

#### POST /crawler/trigger — 手动触发采集

**响应 Schema**：

```json
{
  "data": {
    "message": "采集任务已触发",
    "triggered_at": "2026-06-22T15:00:00Z"
  }
}
```

---

#### GET /crawler/logs — 采集日志

**请求参数**：

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | int | 否 | 页码 |
| page_size | query | int | 否 | 每页条数 |
| source | query | string | 否 | 采集源筛选 |
| status | query | string | 否 | 状态筛选 |

**响应 Schema**：

```json
{
  "data": [
    {
      "id": 1,
      "source": "boss",
      "status": "success",
      "count": 50,
      "error": null,
      "started_at": "2026-06-22T10:00:00Z",
      "finished_at": "2026-06-22T10:05:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

---

## 四、状态机流转 API 详细说明

### 流转规则

**进行中 → 进行中**：

| from_status | to_status | 说明 |
|-------------|-----------|------|
| applied | test | 收到笔试 |
| applied | interviewing | 收到面试（跳过笔试） |
| applied | offer_pending | 直接发 Offer（少见） |
| test | interviewing | 笔试通过 |
| test | offer_pending | 笔试后直接发 Offer（少见） |
| interviewing | interviewing | 进入下一轮 |
| interviewing | offer_pending | 面试通过 |
| offer_pending | offer_accepted | 用户接受 |
| offer_pending | offer_declined | 用户婉拒 |

**进行中 → 终态**（v2 补全：所有进行中状态均可流转到三个"用户/公司侧终态"）：

| from_status | to_status | 说明 |
|-------------|-----------|------|
| applied / test / interviewing / offer_pending | withdrawn | 用户主动撤回（任何非终态均可） |
| applied / test / interviewing / offer_pending | rejected | 公司拒绝（任何非终态均可） |
| applied / test / interviewing / offer_pending | no_response | 无回应关闭（系统建议+用户确认） |

**禁止的流转**（v2 修正措辞）：
- **终态 → 任何其他状态**：禁止（offer_accepted/offer_declined/rejected/no_response/withdrawn 都是终态）
  - 例外：可通过 `is_correction=true` 纠错（写入 correction 事件，漏斗排除）
- **回退流转**：禁止（如 interviewing → applied，求职进度不可逆）
  - 例外：纠错模式

> 注：`favorited` / `to_apply` 是 `user_job_action.action_type`，**不属于投递状态**，不会出现在 transition 的 to_status 中。若前端误传，返回 `VALIDATION_ERROR`（400）。

---

## 五、OpenAPI 集成说明

FastAPI 自动生成 OpenAPI 文档：

| 端点 | 说明 |
|------|------|
| `/docs` | Swagger UI |
| `/openapi.json` | OpenAPI JSON |

**Pydantic 模型示例**：

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransitionRequest(BaseModel):
    to_status: str
    note: Optional[str] = None
    is_correction: bool = False
    correction_reason: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    status: str
    applied_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None
```

---

## 六、与 TASK-006/007 对齐自查

- [x] 状态值用英文 code（applied/test/interviewing/...）
- [x] action_type 用英文 code（favorited/to_apply）
- [x] 状态流转 API 的事务说明呼应 TASK-006 v2（非悲观锁）
- [x] AI 解析降级链三级（LLM → 正则 → null）
- [x] 端点覆盖 PRD 全部 18 个功能点
- [x] 统一响应格式
- [x] 统一分页参数

---

*文档版本：v1.0 | 创建日期：2026-06-22*
