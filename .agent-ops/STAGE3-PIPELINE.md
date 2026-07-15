# 阶段 3 任务流水线 · Stage 3 Pipeline · UI/UX 设计

> 主智能体（Codex）维护。阶段 3 使用 `impeccable` 工作流做高保真页面设计。
> **v2 更新**（2026-06-24，配合 PROJECT.md v4 双面产品架构）：新增营销面任务（TASK-016b），寄存器扩展为双寄存器。

---

## 阶段目标

把阶段 1/2 的产品定义与架构，转化为**高保真、可演示的 UI 设计**：
- 建立设计语言（PRODUCT.md / BRAND.md / DESIGN.md）
- 5 个产品面页面 + 2 个营销面页面的设计简报（shape）
- 高保真实现（craft）

## 寄存器决策（v2 扩展为双寄存器）

本项目是**双面产品**，两套寄存器共存且隔离：

| 面 | 寄存器 | 页面 | 参考来源 | 设计文档 |
|----|--------|------|---------|---------|
| **产品面** | product register | 看板/岗位/投递/订阅/采集 | Linear / Vercel Dashboard / Greenhouse | PRODUCT.md + DESIGN.md |
| **营销面** | brand register | 落地页 / 定价页 | 用户提供的 8 张图（ClarityUI 等） | BRAND.md + DESIGN.md（共享令牌）|

**共享基础**：颜色/字体家族共享 DESIGN.md；应用规则各面独立（详见 BRAND.md §2.2）。

## 任务总览（v2 新增营销面任务）

| ID | 任务 | impeccable 命令 | 寄存器 | 依赖 | 说明 |
|----|------|----------------|--------|------|------|
| TASK-012 ✅ | 设计初始化 | `init` | product | 阶段2 | PRODUCT.md / DESIGN.md / 设计语言 |
| TASK-013 ✅ | 看板首页设计简报 | `shape dashboard` | product | TASK-012 | KPI / 漏斗 / 趋势 / 分布 |
| TASK-014 ✅ | 岗位列表+详情设计简报 | `shape jobs` | product | TASK-012 | 筛选 / 列表 / 详情 / 收藏待投递 |
| TASK-015 ✅ | 投递管理设计简报 | `shape applications` | product | TASK-012 | 状态机 / 时间线 / AI 解析 / 待办 |
| **TASK-016a** ⏸️ | 产品面高保真实现 | `craft` | product | TASK-013/014/015 + 后端完成 | 5 个核心页面生产级 UI |
| **TASK-016b** ✅ | 营销面高保真实现 | `craft` | brand | BRAND.md | 7 屏滚动叙事 + 视觉优化完成 |
| TASK-017 | 设计评审 | `critique` + `audit` | 两面 | TASK-016a/b | AI 检测 / 启发式 / 无障碍 / 性能 |
| TASK-018 | 设计收口 | `polish` + `harden` | 两面 | TASK-017 | 边界态 / 错误 / 空态 / 响应式 / PWA |

> 状态：✅ 完成 | ⏸️ 暂停（等参考）| 🆕 v2 新增 | 空白=待启动

## 产品面 5 个核心页面（基于 PRD v3 功能点）

1. **看板首页**（F-B.1~B.4）— KPI 卡片 + 投递漏斗 + 趋势 + 分布
2. **岗位列表**（F-A.3）— 筛选 + 搜索 + 分页 + 收藏/待投递快捷操作
3. **岗位详情**（F-A.4）— JD / 要求 / 投递链接 / 来源 / 有效性核验
4. **投递管理**（F-C.1~C.6）— 状态机交互 + 时间线 + AI 解析 + DDL + 待办
5. **订阅中心**（F-D.1）— 订阅规则 + 新岗位高亮

## 营销面 2 个页面（v3，真实营销型）

1. **落地首页** `/` — hero + 痛点 + 信息聚合 + 状态机 + 数据看板 + 能力全景 + 定价 + CTA（7 屏滚动叙事）
2. **定价页** `/pricing` — Free/Pro/Team 三档 + 真实营销说明（14天免费试用）

> v5 转向：营销面从"作品集展示型"转为"真实营销型"。详见 BRAND.md v5。
> TASK-016b 已完成：7 屏骨架 + 两轮视觉优化（TASK-VISUAL-OPTIMIZATION + TASK-VISUAL-APPLE-GRADE 进行中）。

详见 `docs/design/BRAND.md` §4 与 `docs/product/evolution-roadmap.md` §5。

## 关键设计原则（Codex 把关）

### 产品面（product register）
1. 效率优先，克制装饰
2. 状态可视化：9 状态机清晰可读（颜色/图标/标签）
3. 低成本交互：F-C.5 快捷状态更新 + AI 解析是体验亮点
4. 空态/错误态/加载态：每个页面都要有
5. **响应式**：桌面优先（≥1024px），手机端保投递管理 + AI 解析核心流程
6. 反 AI 模板：拒绝渐变文字、玻璃态、无意义卡片网格

### 营销面（brand register，v5 真实营销型）
1. 真实营销型定位（对标 Linear/Notion/Apple）
2. 允许 hero、大留白、入场动画（克制）、大字号
3. 用真实产品截图/mockup，不用抽象插画
4. 反 AI 模板底线与产品面一致

## TASK-016 拆分说明（v3）

原 TASK-016（单任务）拆为 016a + 016b：
- **TASK-016a（产品面）**：⏸️ 暂停，等后端完成有真实数据后再做
- **TASK-016b（营销面）**：✅ **已完成**。7 屏骨架 + 视觉优化（TASK-VISUAL-OPTIMIZATION 已验收，TASK-VISUAL-APPLE-GRADE 交 GPT 进行中）

## 与阶段 4（实现）的衔接

阶段 3 产出高保真原型，阶段 4 由 Mimo 按 craft 产出实现真实组件：
- 产品面：React + shadcn/ui + Tailwind（`(app)` 路由组）
- 营销面：同栈（`(marketing)` 路由组），组件放 `components/marketing/`
- PWA：manifest.json + Service Worker（简易离线壳）

---

*最后更新：2026-07-01（v3，TASK-016b 完成+视觉优化，营销面转真实营销型）*
