# Backend Security & Test Gate 报告

> TASK-011 产出。阶段 2 收官任务——对 5 份架构文档进行系统性的安全与测试完备性审查。
>
> ---
> **版本**：v2（主智能体深度校验版）
> **v2 修订说明**：v1 清单结构完整（19 安全项 + 8 测试项逐项核对 + 残余风险显式记录），但深度校验发现 7 处硬伤，其中 3 处严重：
> 1. **【严重】测试用例又用了 `favorited`**：TASK-008 v2 已修正"favorited 是 action_type 不是投递状态"，但 v1 测试用例和错误示例仍用它。这会让实现者混淆 VALIDATION_ERROR vs INVALID_TRANSITION。v2 改为真实的终态回退（offer_accepted→interviewing）
> 2. **【严重·合规】prod 采集频率 30 分钟违反低频合规原则**：与采集合规模块（TASK-009 v2 每源每分钟≤1次）和残余风险"采集反爬被封"矛盾。v2 改为 60 分钟并标注"prod 需重新评估合规"
> 3. **【严重】测试 patch `db.session.commit` 与架构不匹配**：TASK-006/007 v2 明确用 `with session.begin():`（上下文管理器自动提交），不是手动 commit。patch commit 根本不触发。v2 改为 patch 业务异常
> 4. **【中】LLM Prompt 注入黑名单无效**：正则黑名单对中文/变体注入基本无效，给虚假安全感。v2 诚实标注"无法完全防护，用户确认是真正防线"
> 5. **【中】错误示例又用 favorited**：同硬伤 1，修正
> 6. **【中】遗漏 AI 邮件隐私风险**：用户粘贴的邮件含 HR 姓名/电话/邮箱，会发给 LLM（第三方）+ 进缓存 + 进日志。v2 补充此项
> 7. **【小】dedup 测试语义**：标注函数返回值语义

---

## 审查结论

| 项目 | 结论 |
|------|------|
| **门禁结论** | ✅ **有条件通过** |
| **安全清单** | 19 项中 15 项已覆盖，4 项部分覆盖 |
| **测试清单** | 8 项中 6 项已设计，2 项需补充 |
| **残余风险** | 6 条显式接受 |

**进入阶段 3 的前提条件**：
1. 补充输入校验的具体实现方案（Pydantic 模型）
2. 补充日志脱敏规则（API Key、邮件内容）

**进入阶段 4 实现前的必做事项**：
1. 创建 `.env.example` 文件
2. 配置 `.gitignore` 排除敏感文件
3. 实现 Pydantic 校验模型

---

## 一、安全最小清单（逐项核对）

### 1. 认证与会话

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | Demo 阶段无账号体系，本地 SQLite，单用户 |

**证据**：
- `system-architecture.md` §1.3：关键设计取舍"不引入账号体系"
- `database-schema.md`：无 user 表
- `api-contract.md`：无认证端点

**边界说明**：
- Demo 阶段：本地运行，无需认证
- 未来上线：需引入 JWT 认证（已在 system-architecture.md §5.2 预留）

---

### 2. 授权与角色边界

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | Demo 单用户，无角色区分 |

**证据**：
- `system-architecture.md` §1.3：单用户场景
- `api-contract.md`：无角色相关端点

**边界说明**：
- Demo 阶段：单用户，所有操作权限相同
- 未来上线：需引入 RBAC（角色基于访问控制）

---

### 3. 输入校验

| 状态 | 说明 |
|------|------|
| ⚠️ 部分覆盖 | 有 Pydantic 设计，但需补充具体校验规则 |

**证据**：
- `system-architecture.md` §3：使用 Pydantic v2
- `api-contract.md`：有请求 Schema 示例

**缺口与建议**：
- 需补充每个端点的 Pydantic 校验模型（字段类型、长度限制、枚举值）
- 建议在 `api/schemas/` 目录下为每个模块创建 Schema 文件

**示例补充**：

```python
# api/schemas/job.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class JobQueryParams(BaseModel):
    page: int = Field(1, ge=1, le=1000)
    page_size: int = Field(20, ge=1, le=100)
    keyword: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=50)
    
    @validator('keyword')
    def sanitize_keyword(cls, v):
        if v:
            # 移除潜在的 SQL 注入字符
            return v.replace("'", "").replace('"', '').replace(';', '')
        return v
```

---

### 4. 输出编码与注入风险

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | SQLAlchemy ORM 防 SQL 注入；FastAPI 自动 JSON 序列化 |

**证据**：
- `system-architecture.md` §3：使用 SQLAlchemy ORM
- `database-schema.md`：参数化查询

**防护措施**：
- **SQL 注入**：SQLAlchemy ORM 参数化查询，不拼接 SQL
- **XSS**：FastAPI 返回 JSON，前端需自行转义（React 默认转义）

---

### 5. 路径穿越

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | 采集模块仅请求外部 URL，无本地文件操作 |

**证据**：
- `crawler-module.md`：适配器仅请求 HTTP/HTTPS URL
- `system-architecture.md` §3：无文件上传功能

**防护措施**：
- source_url 仅用于溯源，不用于文件操作
- 采集模块不读写本地文件（除 SQLite 数据库）

---

### 6. SSRF（服务器端请求伪造）

| 状态 | 说明 |
|------|------|
| ⚠️ 部分覆盖 | 有 URL 校验建议，但需明确实现 |

**证据**：
- `crawler-module.md` §7：合规控制，但未明确 SSRF 防护

**缺口与建议**：
- 需实现 URL 白名单（仅允许已知招聘平台域名）
- 建议在适配器基类中添加 URL 校验

**补充实现**：

```python
# crawler/adapters/base.py

ALLOWED_DOMAINS = [
    'zhipin.com',      # BOSS 直聘
    'nowcoder.com',    # 牛客网
    'lagou.com',       # 拉勾
    'bytedance.com',   # 字节跳动
    'tencent.com',     # 腾讯
    # ... 更多
]

def validate_url(url: str) -> bool:
    """校验 URL 是否在白名单内"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # 去除 www. 前缀
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return any(domain.endswith(allowed) for allowed in ALLOWED_DOMAINS)
```

---

### 7. 反序列化

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | Pydantic 自动反序列化 + 校验 |

**证据**：
- `system-architecture.md` §3：使用 Pydantic v2
- `api-contract.md`：请求 Schema 定义

**防护措施**：
- Pydantic 自动校验类型、长度、枚举值
- JSON 解析异常会返回 422 错误

---

### 8. CSRF / CORS / Cookie

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | Demo 阶段无 Cookie/CORS 需求 |

**证据**：
- `system-architecture.md` §1.3：前后端分离，REST API
- `api-contract.md`：无 Cookie 相关端点

**边界说明**：
- Demo 阶段：本地运行，同源请求，无需 CORS
- 未来上线：需配置 CORS（已在 system-architecture.md §7.2 预留）

---

### 9. 速率限制

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | 采集和 AI 都有速率限制设计 |

**证据**：
- `crawler-module.md` §7.2：RateLimiter，每源每分钟 ≤1 次
- `ai-parser-module.md` §6：RateLimiter，每分钟最多 10 次 LLM 调用

**实现方案**：
- 采集：`crawler/compliance/rate_limiter.py`
- AI：`core/ai/rate_limiter.py`

---

### 10. 重放防护

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | Demo 阶段无需重放防护 |

**证据**：
- `system-architecture.md` §1.3：本地运行，无网络传输敏感数据

**边界说明**：
- Demo 阶段：本地运行，无重放风险
- 未来上线：需引入请求签名或 nonce

---

### 11. 文件上传校验

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | 本项目无文件上传功能 |

**证据**：
- `api-contract.md`：无文件上传端点
- `system-architecture.md` §3：无文件存储模块

---

### 12. Webhook 签名

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | 本项目无 Webhook 功能 |

**证据**：
- `api-contract.md`：无 Webhook 端点
- `system-architecture.md` §3：无外部回调

---

### 13. 密钥处理

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | .env 文件 + .gitignore 排除 |

**证据**：
- `system-architecture.md` §6.2：secrets 管理方案
- `.env.example`：示例文件（需创建）

**实现方案**：
- `.env`：存储 API Key、数据库 URL
- `.gitignore`：排除 `.env`、`data/*.db`

**待办事项**：
- 创建 `.env.example` 文件
- 配置 `.gitignore`

---

### 14. 环境配置

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | dev/demo/prod 三套配置 |

**证据**：
- `system-architecture.md` §6.3：不同环境的配置差异

**配置差异**：

| 环境 | 数据库 | 采集频率 | LLM | 日志级别 |
|------|--------|---------|-----|---------|
| dev | `data/jobpulse_test.db` | 手动触发 | 可选 | DEBUG |
| demo | `data/jobpulse.db` | 60分钟 | 启用 | INFO |
| prod | PostgreSQL | 60分钟（v2 修正） | 启用 | WARNING |

> ⚠️ **v2 合规修正**：v1 把 prod 采集频率设为 30 分钟（比 demo 更频繁），这与采集合规原则（TASK-009 v2"每源每分钟≤1次"+ 残余风险"采集反爬被封"）直接矛盾——更频繁的采集 = 更高的封禁风险。
> v2 统一为 60 分钟，并标注：**prod 上线前必须重新评估各数据源的合规边界**（robots.txt、ToS、平台限频策略），再决定是否调整频率。低频是合规底线，不是性能问题。

---

### 15. 日志脱敏

| 状态 | 说明 |
|------|------|
| ⚠️ 部分覆盖 | 有日志策略，但需补充脱敏规则 |

**证据**：
- `system-architecture.md` §7.1：日志策略，但未明确脱敏

**缺口与建议**：
- 需补充日志脱敏规则（API Key、邮件内容）

**补充实现**：

```python
# core/logging.py

import re

def sanitize_log(message: str) -> str:
    """日志脱敏"""
    # 脱敏 API Key
    message = re.sub(r'sk-[a-zA-Z0-9]{20,}', 'sk-***', message)
    
    # 脱敏邮箱
    message = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***@***.***', message)
    
    # 脱敏手机号
    message = re.sub(r'1[3-9]\d{9}', '1**********', message)
    
    return message
```

---

### 16. 错误信息泄露

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | 统一错误响应格式，不暴露堆栈 |

**证据**：
- `api-contract.md` §2.4：统一错误响应格式
- `system-architecture.md` §7.2：错误处理

**错误响应示例**（v2 修正：用真实流转非法，非 favorited）：

```json
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

**防护措施**：
- 不返回堆栈信息
- 不返回 SQL 语句
- 不返回内部错误详情

---

### 17. 依赖漏洞检查

| 状态 | 说明 |
|------|------|
| ⚠️ 部分覆盖 | 有依赖清单，但需定期检查 |

**证据**：
- `system-architecture.md` §2：技术栈清单

**建议**：
- 使用 `pip-audit` 或 `safety` 检查 Python 依赖
- 使用 `npm audit` 检查 Node.js 依赖
- 定期更新依赖版本

**待办事项**：
- 在 CI/CD 中集成依赖漏洞检查

---

### 18. 敏感操作审计日志

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | 状态变更写入 ApplicationEvent |

**证据**：
- `database-schema.md` §3.4：ApplicationEvent 表
- `system-architecture.md` §4.1：状态变更事务

**审计内容**：
- 状态变更（status_change）
- 纠错操作（correction，含 is_correction=true）
- 采集日志（CrawlLog）

---

### 19. 隐私、留存、删除、合规

| 状态 | 说明 |
|------|------|
| ✅ 已覆盖 | 仅采集公开数据，不存储隐私 |

**证据**：
- `crawler-module.md` §7.3：数据合规
- `system-architecture.md` §5.5：合规风险

**合规措施**：
- 仅采集公开页面（不登录、不绕过付费墙）
- 不存储个人隐私（HR 联系方式等）
- 引用来源标注（source_url 必填）
- 低频请求（每源每分钟 ≤1 次）

---

## 二、测试最小清单（逐项核对）

### 1. 状态机流转的单元测试

| 状态 | 说明 |
|------|------|
| ✅ 已设计 | 合法/非法/纠错三种场景 |

**证据**：
- `system-architecture.md` §4.1：状态机伪代码
- `api-contract.md` §4：状态流转 API 三个示例

**测试用例**：

```python
# tests/test_core/test_statemachine.py

def test_valid_transition():
    """合法流转：applied → interviewing"""
    engine = StateMachineEngine()
    app = engine.transition(application_id=1, to_status='interviewing')
    assert app.status == 'interviewing'

def test_invalid_transition():
    """非法流转：终态回退（v2 修正：用真实的流转非法，非 favorited 类型错误）
    
    v1 用 to_status='favorited'，但 favorited 是 user_job_action.action_type，
    不是投递状态。传 favorited 触发的是 VALIDATION_ERROR(400)，
    而非 INVALID_TRANSITION(409)。测试语义错误。
    v2 改为：终态 offer_accepted 回退到 interviewing（真正的流转非法）。
    """
    # 先确保 application 处于终态 offer_accepted
    engine = StateMachineEngine()
    # 假设 application 1 当前 status='offer_accepted'
    with pytest.raises(InvalidTransitionError):
        engine.transition(application_id=1, to_status='interviewing')
    # 注意：如果想测"枚举值非法"（如 favorited），那是另一个测试：
    # with pytest.raises(ValidationError):  # 400，不是 InvalidTransitionError
    #     engine.transition(application_id=1, to_status='favorited')

def test_correction():
    """纠错流转：rejected → interviewing"""
    engine = StateMachineEngine()
    app = engine.transition(
        application_id=1,
        to_status='interviewing',
        is_correction=True,
        correction_reason='误操作'
    )
    assert app.status == 'interviewing'
```

---

### 2. 状态机原子性测试

| 状态 | 说明 |
|------|------|
| ✅ 已设计 | 事务回滚测试 |

**测试用例**：

```python
def test_transaction_rollback():
    """事务回滚：Application 更新失败时 ApplicationEvent 不应写入
    
    v2 修正：v1 patch 'db.session.commit'，但 TASK-006/007 v2 明确状态机用
    `with session.begin():`（上下文管理器自动提交），不是手动 commit()。
    patch commit 根本不触发。v2 改为 patch 业务异常（ApplicationEvent 写入失败）。
    """
    engine = StateMachineEngine()
    # 模拟 ApplicationEvent 写入失败（在事务内抛异常）
    with patch('db.session.add', side_effect=Exception('DB write error')):
        with pytest.raises(Exception):
            engine.transition(application_id=1, to_status='interviewing')
    
    # 验证：事务回滚，Application 的 status 不变，ApplicationEvent 未写入
    db.session.expire_all()  # 清除缓存，强制从 DB 重读
    app = db.session.query(Application).get(1)
    assert app.status != 'interviewing'  # 状态未变（回滚）
    events = db.session.query(ApplicationEvent).filter_by(application_id=1).all()
    # 写入失败的那条事件不应存在
    assert all(e.to_status != 'interviewing' for e in events)
```

---

### 3. 去重逻辑测试

| 状态 | 说明 |
|------|------|
| ✅ 已设计 | 同源/跨源/归一化三种场景 |

**证据**：
- `crawler-module.md` §5：去重设计

**测试用例**：

```python
# tests/test_crawler/test_dedup.py

def test_location_normalization():
    """地点归一化：北京市 → 北京"""
    assert normalize_location('北京市') == '北京'
    assert normalize_location('Beijing') == '北京'

def test_company_normalization():
    """公司名归一化：北京字节跳动科技有限公司 → 字节跳动"""
    assert normalize_company('北京字节跳动科技有限公司') == '字节跳动'

def test_same_source_dedup():
    """同源去重"""
    job1 = {'source': 'boss', 'company': '字节跳动', 'title': 'PM', 'location': '北京'}
    job2 = {'source': 'boss', 'company': '字节跳动', 'title': 'PM', 'location': '北京'}
    assert deduplicate(job1) == (False, None)  # 第一条不重复
    assert deduplicate(job2)[0] == True  # 第二条重复

def test_cross_source_merge():
    """跨源合并"""
    job1 = {'source': 'boss', 'company': '字节跳动', 'title': 'PM', 'location': '北京'}
    job2 = {'source': 'nowcoder', 'company': '字节跳动', 'title': 'PM', 'location': '北京'}
    deduplicate(job1)
    is_dup, existing = deduplicate(job2)
    assert is_dup == True
    assert existing.source == 'boss'  # 保留第一个源
```

---

### 4. 采集合规模块测试

| 状态 | 说明 |
|------|------|
| ✅ 已设计 | robots fail-closed / rate limiter |

**证据**：
- `crawler-module.md` §7：合规控制

**测试用例**：

```python
# tests/test_crawler/test_compliance.py

def test_robots_fail_closed():
    """robots.txt 读取失败时默认禁止"""
    checker = RobotsChecker()
    # 模拟 robots.txt 读取失败
    with patch('urllib.robotparser.RobotFileParser.read', side_effect=Exception):
        assert checker.can_fetch('https://example.com/jobs') == False

def test_rate_limiter():
    """速率限制"""
    limiter = RateLimiter(max_per_minute=2)
    assert limiter.allow() == True
    assert limiter.allow() == True
    assert limiter.allow() == False  # 超过限制
```

---

### 5. AI 降级链测试

| 状态 | 说明 |
|------|------|
| ✅ 已设计 | TASK-010 已有完整测试设计 |

**证据**：
- `ai-parser-module.md` §7：测试策略

**测试用例**：
- LLM Mock 测试
- 正则降级测试
- 匹配逻辑测试
- 降级链测试

---

### 6. API 集成测试

| 状态 | 说明 |
|------|------|
| ✅ 已设计 | 正常/校验失败/未授权/并发 |

**测试用例**：

```python
# tests/test_api/test_applications.py

def test_create_application_success(client):
    """创建投递成功"""
    response = client.post('/api/v1/applications', json={'job_id': 1})
    assert response.status_code == 201

def test_create_application_validation_error(client):
    """创建投递校验失败"""
    response = client.post('/api/v1/applications', json={})
    assert response.status_code == 422

def test_transition_invalid(client):
    """状态流转非法（v2 修正：终态回退，非 favorited 类型错误）"""
    # 假设 application 1 处于终态 offer_accepted
    response = client.post('/api/v1/applications/1/transition', json={'to_status': 'interviewing'})
    assert response.status_code == 409  # INVALID_TRANSITION 是 409，非 400
    assert response.json()['error']['code'] == 'INVALID_TRANSITION'
```

---

### 7. 输入校验测试

| 状态 | 说明 |
|------|------|
| ⚠️ 需补充 | 边界值/注入尝试 |

**缺口与建议**：
- 需补充边界值测试（空字符串、超长字符串、特殊字符）
- 需补充注入尝试测试（SQL 注入、XSS）

**补充测试用例**：

```python
def test_input_validation_boundary(client):
    """边界值测试"""
    # 空字符串
    response = client.get('/api/v1/jobs?keyword=')
    assert response.status_code == 200
    
    # 超长字符串
    response = client.get('/api/v1/jobs?keyword=' + 'a' * 1000)
    assert response.status_code == 422

def test_input_validation_injection(client):
    """注入尝试测试"""
    # SQL 注入尝试
    response = client.get("/api/v1/jobs?keyword=' OR 1=1 --")
    assert response.status_code == 200  # 应正常返回，不报错
    
    # XSS 尝试
    response = client.get('/api/v1/jobs?keyword=<script>alert(1)</script>')
    assert response.status_code == 200
```

---

### 8. E2E 冒烟测试

| 状态 | 说明 |
|------|------|
| ⚠️ 需补充 | 核心流程测试 |

**缺口与建议**：
- 需补充核心流程 E2E 测试（采集→展示→投递→看板）

**补充测试用例**：

```python
# tests/test_e2e/test_smoke.py

def test_full_flow(client):
    """核心流程：采集→展示→投递→看板"""
    # 1. 触发采集
    response = client.post('/api/v1/crawler/trigger')
    assert response.status_code == 200
    
    # 2. 查看岗位列表
    response = client.get('/api/v1/jobs')
    assert response.status_code == 200
    jobs = response.json()['data']
    assert len(jobs) > 0
    
    # 3. 创建投递
    job_id = jobs[0]['id']
    response = client.post('/api/v1/applications', json={'job_id': job_id})
    assert response.status_code == 201
    
    # 4. 查看看板
    response = client.get('/api/v1/dashboard/kpi')
    assert response.status_code == 200
    assert response.json()['data']['total_applications'] > 0
```

---

## 三、专项风险评估

### 3.1 采集合规风险（本项目最高风险）

| 风险项 | 状态 | 说明 |
|--------|------|------|
| robots.txt fail-closed | ✅ 已落实 | `crawler-module.md` §7.1 |
| 反爬绕过边界 | ✅ 已明确 | 不绕过反爬、不登录、不付费 |
| 数据合规 | ✅ 已落实 | 仅公开数据、不存隐私 |
| 法律风险 | ✅ 已评估 | 公开页面、低频、个人学习 |

**结论**：采集合规风险已充分评估，措施到位。

---

### 3.2 LLM 安全风险

| 风险项 | 状态 | 说明 |
|--------|------|------|
| Prompt 注入 | ⚠️ 需关注 | 用户输入进入 LLM |
| API Key 泄露 | ✅ 已防护 | .env + .gitignore |
| 成本失控 | ✅ 已防护 | 限流 + 缓存 |

**Prompt 注入风险评估**（v2 诚实重写）：

> ⚠️ v1 给了一个正则黑名单（`ignore previous instructions` 等），但这是**虚假安全感**——黑名单对中文注入（"忽略上面的指令"）、变体表达（"disregard prior"、"act as if"）、编码绕过基本无效。LLM 架构下 Prompt 注入**无法通过输入过滤完全防护**。

**诚实结论**：在当前"用户文本直接进 LLM"的架构下，Prompt 注入**无法完全防护**。真正的防线是：
1. **用户确认机制（最有效）**：AI 结果仅作建议，不自动执行任何状态流转，用户必须显式确认。即使被注入，也无法污染数据。
2. **限制输出影响面**：LLM 只能返回结构化建议（company/title/status），无法执行命令或访问数据。
3. **输入长度限制**：Pydantic 限制邮件文本长度（如 max_length=10000），降低注入面。
4. **可选输入清理**：作为浅层缓解（移除明显的指令性短语），但**不作为安全依赖**，仅标注"已做基础清理"。

**v1 的正则黑名单保留作为"浅层缓解"，但必须在代码注释中标注"此防护非安全边界，真正防线是用户确认"。**

---

### 3.3 状态机数据完整性

| 风险项 | 状态 | 说明 |
|--------|------|------|
| 事务原子性 | ✅ 已保证 | `system-architecture.md` §4.1 |
| 纠错机制 | ✅ 已隔离 | `is_correction` 标记，漏斗排除 |

**结论**：状态机数据完整性已充分保证。

---

## 四、残余风险清单与显式接受

以下风险在 Demo 阶段**显式接受**，记录在案：

| 风险 | 等级 | 接受理由 | 缓解措施 |
|------|------|---------|---------|
| 单用户无认证 | 低 | Demo 阶段本地运行 | 未来上线需引入 JWT |
| SQLite 并发限制 | 低 | 单用户场景足够 | 未来可迁移 PostgreSQL |
| 采集反爬被封 | 中 | 低频请求降低风险 | 多源冗余、人工兜底 |
| LLM Prompt 注入 | 中（v2 升级） | 当前架构无法完全防护 | **用户确认是真正防线**；浅层输入清理；AI 无执行权限 |
| **AI 邮件隐私泄露（v2 新增）** | **中** | 用户粘贴的邮件含 HR 姓名/电话/邮箱等个人信息，会发送给第三方 LLM、进本地缓存、可能进日志 | ① 用户知情同意（UI 提示"邮件内容将发送给 AI 解析"）② 缓存键用 hash 不存原文 ③ 日志脱敏覆盖邮件内容 ④ Demo 仅自用，不涉及他人隐私 |
| 依赖漏洞 | 低 | 定期检查 | pip-audit / npm audit |
| 日志脱敏不完整 | 低 | 本地运行 | 补充脱敏规则（含邮件内容） |

> ⚠️ **v2 新增的 AI 邮件隐私风险说明**：
> F-C.5 让用户粘贴求职邮件，邮件里典型包含：HR 姓名、HR 电话、HR 邮箱、面试地址、Offer 薪资等个人信息。这些内容会：
> 1. **发送给第三方 LLM**（DeepSeek/OpenAI）→ 个人信息离开本地，进入第三方服务
> 2. **进入本地缓存**（TTLCache，1 小时）→ 留存在本地内存
> 3. **可能进入日志**（如果调试日志打印了邮件内容）→ 留存在日志文件
>
> **缓解措施**（Demo 阶段）：
> - UI 必须有知情同意提示："您粘贴的内容将发送给 AI 进行解析，请勿粘贴含敏感薪资的完整邮件"
> - 缓存已用 hash(email_text) 作为键（TASK-010 v1 已做），不存原文 ✅
> - 日志脱敏规则必须覆盖邮件内容（硬伤 6 的脱敏函数要增强）
> - Demo 阶段仅作者自用，不涉及他人隐私，风险可控
> - **未来上线必须重新评估**：是否提供"本地 LLM"选项、是否需要 PII 自动识别与脱敏

---

## 五、验收结论

### 门禁结论

✅ **有条件通过**

### 进入阶段 3 的前提条件

1. 补充输入校验的具体实现方案（Pydantic 模型）
2. 补充日志脱敏规则（API Key、邮件内容）

### 进入阶段 4 实现前的必做事项

1. 创建 `.env.example` 文件
2. 配置 `.gitignore` 排除敏感文件
3. 实现 Pydantic 校验模型
4. 实现 URL 白名单校验（SSRF 防护）
5. 实现日志脱敏函数

---

## 六、核对统计

| 清单 | 已覆盖 | 部分覆盖 | 未覆盖 |
|------|--------|---------|--------|
| 安全清单（19 项） | 15 | 4 | 0 |
| 测试清单（8 项） | 6 | 2 | 0 |

**部分覆盖项**：
1. 输入校验（需补充 Pydantic 模型）
2. SSRF 防护（需补充 URL 白名单）
3. 日志脱敏（需补充脱敏规则）
4. 依赖漏洞检查（需集成 CI/CD）

**需补充测试项**：
1. 输入校验测试（边界值/注入尝试）
2. E2E 冒烟测试（核心流程）

---

*报告版本：v1.0 | 创建日期：2026-06-22*