# TASK-011 · Backend Security & Test Gate（安全门禁）

## 背景与目标

这是阶段 2（架构设计）的**收官任务**，按 `product-design-workflow` 与 `.agent-ops/COLLABORATING_AGENT_WORKFLOW.md` 的 Backend Security & Test Gate 要求**强制执行**。

阶段 2 已产出 5 份架构文档（TASK-006~010），本任务对它们做**系统性的安全与测试完备性审查**，确保进入阶段 3/4 之前没有遗留的安全风险和测试盲区。

**目标**：产出一份安全与测试门禁报告，覆盖安全最小清单 + 测试最小清单的逐项核对，标注未决发现与残余风险。

## 输入素材（全部必读，这是审查对象）

- `docs/architecture/system-architecture.md` —— v2（系统架构）
- `docs/architecture/database-schema.md` —— v2（数据库）
- `docs/architecture/api-contract.md` —— v2（API 契约）
- `docs/architecture/crawler-module.md` —— v2（采集模块）
- `docs/architecture/ai-parser-module.md` —— v2（AI 解析）
- `.agent-ops/COLLABORATING_AGENT_WORKFLOW.md` —— §5 安全/测试门禁标准

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径

- `docs/architecture/security-test-gate-report.md`（**新建**，本任务唯一产出）

## 禁止操作

- 不修改 `src/`、`config/`、`data/`、`scripts/`、`tests/` 下任何文件
- 不修改任何已存在文档（本任务是审查，不改动被审查文档）
- 不创建实际代码文件

## 实现要求

### 一、安全最小清单（逐项核对）

对照 WORKFLOW.md §5 的安全清单，**逐项**核对 5 份架构文档是否覆盖。每项给出：
- 状态：✅ 已覆盖 / ⚠️ 部分覆盖 / ❌ 未覆盖
- 证据：在哪份文档的哪一节
- 缺口与建议：如未覆盖，如何补

**必须核对的项**：
1. 认证与会话（Demo 无账号，说明边界）
2. 授权与角色边界（Demo 单用户）
3. 输入校验（API 参数、Pydantic 校验）
4. 输出编码与注入风险（SQL 注入、XSS）
5. 路径穿越（采集模块文件操作、source_url）
6. SSRF（采集模块请求外部 URL）
7. 反序列化（JSON 解析）
8. CSRF / CORS / Cookie（Demo 边界）
9. 速率限制（采集 + AI）
10. 重放防护
11. 文件上传校验（如有）
12. Webhook 签名（本项目无，说明）
13. 密钥处理（.env / .gitignore）
14. 环境配置（dev/demo/prod 差异）
15. 日志脱敏（API Key、邮件内容）
16. 错误信息泄露（堆栈、SQL）
17. 依赖漏洞检查
18. 敏感操作审计日志
19. 隐私、留存、删除、合规

### 二、测试最小清单（逐项核对）

对照 WORKFLOW.md §5 的测试清单，核对测试策略完备性：
1. 状态机流转的单元测试（合法/非法/纠错）
2. 状态机原子性测试（事务回滚）
3. 去重逻辑测试（同源/跨源/归一化）
4. 采集合规模块测试（robots fail-closed / rate limiter）
5. AI 降级链测试（TASK-010 已有，核对完整性）
6. API 集成测试（正常/校验失败/未授权/并发）
7. 输入校验测试（边界值/注入尝试）
8. E2E 冒烟测试（核心流程：采集→展示→投递→看板）

每项标注：✅ 已设计 / ⚠️ 需补充 / ❌ 缺失

### 三、专项风险评估（本项目特有）

**3.1 采集合规风险**（本项目最高风险）
- robots.txt fail-closed 是否落实
- 反爬绕过的边界（明确"不做"的部分）
- 数据合规（是否存储隐私、是否仅公开数据）
- 法律风险评估（仅公开页面、低频、个人学习用途）

**3.2 LLM 安全风险**
- Prompt 注入（用户输入进入 LLM）
- API Key 泄露
- 成本失控（限流是否足够）

**3.3 状态机数据完整性**
- 事务原子性是否真的保证（呼应 TASK-006/007 v2）
- 纠错机制是否会污染漏斗

### 四、残余风险清单与显式接受

列出审查后**显式接受**的残余风险（Demo 阶段不解决，但记录）：
- 单用户无认证（Demo 边界）
- SQLite 并发限制（单用户可接受）
- 等

### 五、验收结论

明确给出：
- 是否通过安全门禁（通过 / 有条件通过 / 不通过）
- 进入阶段 3 的前提条件
- 进入阶段 4 实现前的必做事项

## 质量要求

- **逐项核对，不能跳过**（安全审查的严谨性）
- **每项有证据**（文档定位）或明确的缺口
- **残余风险必须显式记录**（不能含糊）
- **诚实标注未覆盖项**（不为了"通过"而美化）

## 结果文件路径

`docs/architecture/security-test-gate-report.md`

## 结果格式（写入 outbox）

```markdown
# TASK-011 执行结果

## 摘要
<门禁结论：通过/有条件通过/不通过>

## 修改/新建的文件清单
- docs/architecture/security-test-gate-report.md（新建）

## 核对统计
- 安全清单：X 项已覆盖 / Y 部分覆盖 / Z 未覆盖
- 测试清单：...
- 残余风险：N 条

## 关键发现
- <最重要的 3 条发现>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有，特别是合规边界、是否允许进入阶段 3>
```
