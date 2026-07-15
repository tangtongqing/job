# TASK-009 · 采集模块设计

## 背景与目标

TASK-006/007/008 已完成架构/数据库/API。本任务是阶段 2 的**高复杂度核心模块**——采集是系统的命脉（没有数据就没有产品），且涉及**合规风险**（反爬、robots.txt、ToS），是 TASK-011 安全门禁的重点审查对象。

**目标**：产出采集模块的详细设计文档，覆盖适配器架构、调度、清洗、去重、核验、合规控制，可直接指导阶段 4 实现。

## 输入素材（必读）

- `docs/architecture/system-architecture.md` —— **v2**，重点 §3 crawler 目录结构、§4.3 采集事务（批量提交）、§6 配置、§7 合规
- `docs/architecture/database-schema.md` —— **v2**，重点 §3.1 Job 表、§3.7 CrawlLog 表、去重唯一索引限制
- `docs/product/PRD.md` —— v3，F-A.1~A.6 采集相关功能点
- `docs/product/PROJECT.md` —— v3，§7 数据源策略

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径

- `docs/architecture/crawler-module.md`（**新建**，本任务唯一产出）

## 禁止操作

- 不修改 `src/`、`config/`、`data/`、`scripts/`、`tests/` 下任何文件
- 不修改任何已存在文档
- 不创建实际代码文件
- 不调用真实爬虫（本任务是设计文档，不实际采集）

## 实现要求

### 一、文档结构（八个部分）

#### 1. 采集模块总览
- 一句话定位
- 模块边界（做什么、不做什么）
- 与其他模块的关系（依赖 db/，被 api/ 调用）

#### 2. 适配器架构（核心）
**2.1 适配器基类设计**
- 抽象基类 `BaseAdapter` 的接口定义（Python abc 或 Protocol）
- 必须实现的方法：`fetch()` / `parse()` / `should_crawl()`
- 通用辅助方法：HTTP 请求、重试、User-Agent 轮换

**2.2 各源适配器**
为每个数据源设计一个适配器，至少覆盖 3 个（呼应 PRD F-A.1 AC）：
- `CompanyWebsiteAdapter`（企业官网，合规风险最低，Demo 首选）
- `BossAdapter`（BOSS 直聘，反爬强）
- `NowcoderAdapter`（牛客网）

每个适配器说明：
- 目标 URL / 列表页 / 详情页结构
- 抓取方式（httpx 同步 / Playwright 动态渲染，呼应 TASK-006 v2 全同步）
- 字段选择器（CSS/XPath）
- 反爬应对（User-Agent / 频率 / 验证码检测）
- **合规评估**：robots.txt 是否允许、ToS 是否禁止、数据是否公开

**2.3 适配器注册与配置驱动**
- 适配器如何注册（工厂模式 / 配置文件）
- `config/sources.yaml` 的结构示例
- 启用/禁用源的开关

#### 3. 调度设计
- APScheduler 集成方式（内嵌 FastAPI，呼应 TASK-006 §5.1）
- 调度策略：每小时一次（默认，可配置）
- 手动触发（对应 API `POST /crawler/trigger`）
- 并发控制：≤3 个源同时（CRAWL_MAX_CONCURRENT）
- 调度日志写入 CrawlLog 表

#### 4. 清洗与字段提取
**4.1 字段映射**
- 每个源的原始字段 → Job 表标准字段的映射表
- 缺失字段的默认值/标记策略

**4.2 硬条件提取（呼应 PRD F-A.2 v3）**
- graduation_year / education / experience 的提取规则
- 正则 + 关键词匹配
- 未知时标记"未识别"（不丢弃）

**4.3 应届/实习标签**
- is_intern / is_fresh 的判断规则

#### 5. 去重设计（重点）
**5.1 去重挑战**
- 呼应 TASK-007 v2 §3.1 的已知限制：location 字符串不一致
- 跨源重复（BOSS 和牛客同一岗位）

**5.2 去重策略（分层）**
- **第一层（入库前）**：采集层归一化
  - location 归一化（"北京市"→"北京"，"Beijing"→"北京"）
  - 公司名归一化（去除"有限公司""科技"等后缀）
- **第二层（入库时）**：数据库唯一索引（source+company+title+location）
- **第三层（跨源）**：跨源合并（不同 source 的同一岗位，保留信息最全版本）

**5.3 去重伪代码**
给出归一化 + 去重的实现示例

#### 6. 有效性核验（呼应 PRD F-A.6）
- 核验方式：HTTP HEAD / GET 检查投递链接
- 失效判定：HTTP 404、超时、页面结构变更
- 核验频率：低于采集频率（如每天一次）
- last_verified_at 更新策略
- 误判恢复（用户手动重新核验）

#### 7. 合规控制（重点，TASK-011 会严查）
**7.1 robots.txt 尊重**
- 抓取前检查 robots.txt
- 遵守 Disallow 规则
- robots.py 模块的接口设计

**7.2 速率限制**
- rate_limiter.py 模块设计
- 每源每分钟 ≤1 次（PROJECT.md §5.4 安全要求）
- 指数退避重试

**7.3 数据合规**
- 仅采集公开页面（不登录、不绕过付费墙）
- 不存储个人隐私（HR 联系方式等）
- 引用来源标注（source_url 必填）

**7.4 合规风险评估表**
为每个数据源给出合规风险等级（高/中/低）+ 对策

#### 8. 与 TASK-006/007/008 的对齐
明确本设计如何落地前面三个任务的决策。

### 二、质量要求

- **必须呼应 TASK-006 v2 的全同步策略**（httpx.Client / sync_playwright，非 async）
- **必须呼应 TASK-006 v2 的批量提交**（每批 20 条，呼应 §4.3）
- **必须呼应 TASK-007 v2 的去重限制**（location 归一化交由采集层）
- **合规控制必须有具体方案**（robots.py / rate_limiter.py 的接口设计）
- **适配器至少 3 个**，每个含合规评估
- **去重必须分层**（归一化 + 唯一索引 + 跨源合并）

### 三、与前置任务的对齐检查

- [ ] 全同步（httpx.Client / sync_playwright）？
- [ ] 批量提交事务（每批 20 条）？
- [ ] location 归一化（解决 TASK-007 v2 已知限制）？
- [ ] robots.py + rate_limiter.py 合规模块？
- [ ] 至少 3 个适配器 + 合规评估？
- [ ] 写入 CrawlLog 表？

## 验证命令

纯文档任务。自查清单（对照上面"对齐检查"）。

## 结果文件路径

`docs/architecture/crawler-module.md`

## 结果格式（写入 outbox）

```markdown
# TASK-009 执行结果

## 摘要
<2-3 句话概述采集模块设计核心>

## 修改/新建的文件清单
- docs/architecture/crawler-module.md（新建）

## 关键设计决策
- 适配器数量：...
- 去重策略：...
- 合规方案：...

## 与前置任务对齐自查
<逐项打勾>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有，特别是合规边界、反爬应对、去重准确性>
```
