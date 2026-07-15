# 后端地基完成报告 + 验收委托

**完成日期**：2026-07-01
**执行者**：Codex（主智能体）
**范围**：后端核心层（配置/数据库/状态机/事件服务）——所有后续模块的地基
**验证状态**：✅ 已通过实跑验证（建表+种子数据+状态机 3 场景校验）

---

## 一、本次完成的内容

### 1. 项目初始化与配置层
| 文件 | 内容 |
|------|------|
| `pyproject.toml` | 依赖清单（fastapi/sqlalchemy2/pydantic2/alembic/apscheduler/httpx/openai1.0+等）|
| `.env.example` | 环境变量模板（占位符，非真实 Key）|
| `src/config.py` | Settings 类（pydantic-settings 自动加载 .env）|

### 2. 数据库层（7 表 ORM）
| 文件 | 内容 |
|------|------|
| `src/db/session.py` | engine + SessionLocal + get_db 依赖注入 + SQLite 外键 PRAGMA |
| `src/db/models.py` | **7 表 ORM**：Job/UserJobAction/Application/ApplicationEvent/Subscription/Company/CrawlLog |

**严格遵循 database-schema.md v2**：
- ✅ 所有枚举用英文 code 存储（中文映射在 STATUS_LABEL_CN）
- ✅ 9 状态 + 5 终态定义
- ✅ Application 部分唯一索引（同一岗位同时只能有一个非终态投递）
- ✅ updated_before_update 钩子（SQLite 无原生 ON UPDATE）
- ✅ 全部索引按 schema 文档落地（去重/漏斗/待办/纠错）

### 3. 状态机引擎（核心业务逻辑）
| 文件 | 内容 |
|------|------|
| `src/core/statemachine/transitions.py` | 9 状态合法流转规则（TRANSITIONS 字典）|
| `src/core/statemachine/engine.py` | `transition()` 原子事务 + 异常体系 |

**严格遵循 database-schema.md §4.3 v2**：
- ✅ 读取+校验+写入在同一事务（v2 关键修正，v1 把读取放 try 外破坏原子性）
- ✅ 不用 SELECT FOR UPDATE（SQLite 不支持，应用层校验替代）
- ✅ 终态常规流转拦截 / 终态纠错需原因 / 纠错允许任意流转

### 4. 事件服务
| 文件 | 内容 |
|------|------|
| `src/core/events/service.py` | 面试/笔试/材料/Offer/备注 事件写入 + 待办/漏斗查询 |

---

## 二、验证结果（实跑，非纸面）

### 验证 1：7 表模型导入
```
$ python -c "from src.db.models import Job, Application, ..."
7 models import OK
```

### 验证 2：建表 + 种子数据 + 状态机流转
```
$ python -m src.db.init_db
[init_db] 表已创建
[init_db] 种子数据已插入：4 公司 / 4 岗位 / 4 投递
[init_db] ApplicationEvent 记录：6 条
```
6 条事件 = 字节1 + 美团1 + 腾讯0 + 小米4（小米经历了 applied→test→interviewing→offer_pending→offer_accepted 多轮流转，验证多轮流转事件记录正确）

### 验证 3：状态机 3 个关键校验场景
```
测试1 通过：终态纠错无原因被拦截 - 纠错必须填写原因
测试2 通过：终态常规流转被拦截 - 不允许从 offer_accepted 流转到 interviewing
测试3 通过：终态纠错成功，新状态=interviewing
```

---

## 三、文件清单（本次产出）

```
pyproject.toml                           # 依赖
.env.example                             # 环境变量模板
src/__init__.py + 所有子包 __init__.py    # 包结构
src/config.py                            # Settings
src/db/session.py                        # engine/session
src/db/models.py                         # 7 表 ORM（核心）
src/db/init_db.py                        # 建表+种子脚本
src/core/statemachine/transitions.py     # 流转规则
src/core/statemachine/engine.py          # 状态机引擎（核心）
src/core/statemachine/__init__.py
src/core/events/service.py               # 事件服务
src/core/events/__init__.py
```

---

## 四、委托验收任务（给验收智能体）

### 验收目标
确认后端核心层（配置/数据库/状态机/事件）实现正确，可安全进入下一轮（API 层）。

### 验收清单

#### A. 代码审查（对照设计文档）
- [ ] `src/db/models.py` 的 7 表字段/索引/约束是否与 `docs/architecture/database-schema.md` v2 完全一致
- [ ] `src/core/statemachine/engine.py` 的事务边界是否与 database-schema §4.3 v2 一致（读取+校验+写入同事务）
- [ ] `src/core/statemachine/transitions.py` 的流转规则是否覆盖 PRD v3 §3.3 的所有合法路径
- [ ] 枚举值是否全部英文 code 存储（无中英文混用）

#### B. 实跑验证（环境：Python 3.10+）
```bash
cd <项目根目录>
pip install sqlalchemy pydantic-settings
python -c "from src.db.models import Job, Application, ApplicationEvent"  # 应无报错
python -m src.db.init_db                                                  # 应输出"表已创建+种子数据+6条事件"
```

#### C. 状态机校验（实跑）
```python
from src.db.session import SessionLocal
from src.db.models import Application, APP_APPLIED, APP_INTERVIEWING
from src.core.statemachine import transition, InvalidTransitionError, CorrectionValidationError

db = SessionLocal()
# 终态纠错无原因 → 应抛 CorrectionValidationError
# 终态常规流转 → 应抛 InvalidTransitionError
# 终态带原因纠错 → 应成功
```

#### D. 已知限制（非缺陷，设计决策）
- SQLite 不支持 SELECT FOR UPDATE，用应用层校验替代（单用户 Demo 足够，PG 迁移后升级）
- location 字符串不一致可能漏去重（交由采集层模糊去重，非数据库职责）
- 部分索引的 sqlite_where/postgresql_where 双写（迁移兼容）

### 验收结论模板
请在 `.agent-ops/TASK-BACKEND-FOUNDATION-REVIEW.md` 产出：
1. A/B/C/D 各项通过/失败
2. 发现的问题清单（如有）
3. 是否可进入下一轮（API 层）

---

## 五、下一轮计划（Codex 待做，等验收通过）

| 顺序 | 模块 | 依赖 |
|------|------|------|
| 后端-4 | API 层（jobs/applications/dashboard/subscriptions/crawler 路由）| 本次地基 |
| 后端-5 | 采集层（3 适配器+调度+去重+合规）| API 层 |
| 后端-6 | AI 解析层（邮件解析三级降级）| 事件服务 |
| 后端-7 | main 入口 + 中间件 | API 层 |
| 后端-8 | 测试（pytest）| 全部 |

---

*报告产出：2026-07-01 | 上游：architecture/database-schema.md v2 | 验收目标：可进入 API 层*
