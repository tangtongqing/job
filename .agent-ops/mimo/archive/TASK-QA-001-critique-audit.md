# TASK-QA-001 · 阶段 5 质量审查：产品面 + 营销面 critique/audit

## 背景与目标

项目已经完成阶段 4 核心实现并通过 Codex 验收：

- 后端地基 / API / 采集 / AI parse-email 均已通过验收。
- 产品面前端 `TASK-FE-PRODUCT-001` 已通过验收，并由 Codex 小范围补修。
- 当前进入阶段 5：质量审查、响应式、PWA、异常态、演示数据与作品集展示路径收口。

本任务是阶段 5 第一单，不要求大规模实现。目标是对当前 `web/` 做一次系统 critique/audit，产出可执行的返工清单：

> 找出产品面和营销面的真实质量缺口，按严重度排序，给出最小返工方案，避免后续 polish 盲改。

## 允许读取的路径

- `web/`
- `docs/design/`
- `docs/product/`
- `docs/architecture/api-contract.md`
- `.agent-ops/`
- `src/api/`
- `src/schemas/`

## 允许修改的路径

本任务默认以审查报告为主，**不要修改业务代码**。

允许新增/修改：

- `.agent-ops/mimo/outbox/TASK-QA-001-result.md`

如发现 P0 小问题（例如构建失败、明显语法错误、单行 typo 导致页面不可访问），可以小修，但必须在结果文件中说明：

- 修改了哪些文件
- 为什么属于 P0 小修
- 执行了哪些验证命令

## 禁止操作

- 不做大规模 UI 重构。
- 不新增依赖。
- 不修改后端 `src/`。
- 不接入真实外部服务、真实招聘网站、真实 LLM Key。
- 不删除或覆盖 `.agent-ops/visual-checks/` 中已有截图证据。
- 不把 mock 数据伪装成真实 API 数据。
- 不改变已通过验收的状态机/API 契约。

## 审查范围

### 1. 产品面 App 审查

重点页面：

- `/dashboard`
- `/jobs`
- `/jobs/[id]`
- `/applications`
- `/applications/[id]`
- `/todo`
- `/crawler`

审查点：

- 信息架构是否符合工具型产品，而不是营销页式 hero。
- 数据密度是否适合桌面工作台。
- loading / error / empty 是否完整、文案是否可信。
- 离线后端状态下是否可读，不出现崩溃或空白。
- 状态 badge / 合法流转是否与后端状态机一致。
- AI parse-email 是否坚持“建议 + 用户确认”，没有自动流转。
- 移动端是否至少不崩、不重叠、不出现明显横向溢出。
- 长文本、长公司名、长岗位名、长错误信息是否会撑爆布局。

### 2. 营销面审查

重点页面：

- `/`

审查点：

- 是否仍符合 `docs/design/BRAND.md` 的作品集展示型营销定位。
- Hero 是否第一屏清楚表达 JobPulse，而不是抽象模板页。
- 各 section 是否有真实产品/状态/数据感，不是空泛装饰。
- 亮色/暗色主题是否都可读。
- 移动端首屏和滚动体验是否可接受。
- CTA 是否能通往产品面核心路径。

### 3. 响应式与视觉证据

请至少检查以下视口：

- Desktop：1366 × 768
- Mobile：390 × 844

建议检查页面：

- `/`
- `/dashboard`
- `/jobs`
- `/applications`

如可使用 Playwright，请截图并将截图保存在：

```text
.agent-ops/visual-checks/TASK-QA-001/
```

如果无法截图，请在结果中说明原因，并至少用 HTTP 探测 + 代码审查覆盖。

### 4. 技术质量审查

请执行：

```bash
cd web
npm.cmd run lint
npm.cmd run build
```

如果在非 Windows shell 下，可用等价命令：

```bash
cd web
npm run lint
npm run build
```

并检查：

- 是否存在未使用代码、重复类型、明显临时变量。
- API client 是否还符合 `{data, meta}` / `{error}` envelope。
- 是否有容易导致 hydration/build/runtime 的 Next.js 边界问题。
- 是否有页面依赖后端在线才能 build 的问题。

### 5. PWA / 作品集演示准备度审查

只审查，不实现。请判断：

- 当前是否已有 manifest / icon / metadata 的 PWA 基础。
- 作品集演示路径是否清楚：从营销页进入产品面、看 dashboard/jobs/applications/AI parse。
- 是否需要 demo seed 数据或前端 demo mode。
- 是否需要一键启动脚本或 README 补充。

## 输出要求

请写入：

```text
.agent-ops/mimo/outbox/TASK-QA-001-result.md
```

结果文件必须包含以下结构：

```markdown
# TASK-QA-001 result

## 摘要

## 执行的检查
- 命令与结果
- 页面/视口/截图覆盖情况

## 发现的问题

### P0 阻断
- ...

### P1 必须返工
- ...

### P2 建议优化
- ...

### P3 可暂缓
- ...

## 建议返工任务拆分
1. TASK-QA-REWORK-001 ...
2. TASK-QA-REWORK-002 ...

## 已做的小修（如有）

## 残余风险

## 需要 Codex 判断的问题
```

## 严重度定义

- **P0 阻断**：build/lint 失败、核心路由打不开、产品核心链路不可用、严重状态机/API 契约错误。
- **P1 必须返工**：核心体验明显不完整，影响作品集演示可信度或用户主要任务。
- **P2 建议优化**：不阻断演示，但影响专业感、响应式、可读性或后续维护。
- **P3 可暂缓**：锦上添花、未来版本、非 MVP。

## 验收标准

Codex 验收时会检查：

- 报告是否覆盖产品面 + 营销面。
- 是否执行并记录 lint/build。
- 是否给出明确严重度和文件/页面定位。
- 是否区分“真实缺陷”和“个人偏好”。
- 是否提出可落地的返工任务，而不是泛泛建议。
- 未完成截图/浏览器检查时，是否解释原因并用替代证据覆盖。

## 备注

当前阶段不是继续堆功能，而是把已有系统收成一个可展示、可讲述、可验证的作品集项目。请优先发现影响可信度和演示路径的问题。
