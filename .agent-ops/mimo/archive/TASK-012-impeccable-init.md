# TASK-012 · impeccable init（设计初始化）

## 背景与目标

阶段 1/2 已完成（产品定义 + 架构设计）。本任务是阶段 3（UI/UX 设计）的起点，执行 `impeccable init`——建立设计语言基础，为后续 shape（设计简报）和 craft（高保真实现）铺路。

**目标**：产出 PRODUCT.md 和 DESIGN.md，确立设计语言、配色、排版、组件库选型。

## 输入素材（必读）

- `docs/product/PRD.md` —— v3，§四 18 功能点、§九.2 面试官追问（含状态可视化要求）
- `docs/product/PROJECT.md` —— v3，技术栈（Next.js + shadcn/ui + Tailwind）
- `docs/architecture/system-architecture.md` —— v2，§2 技术栈（含 Zustand 本地状态）
- `docs/architecture/api-contract.md` —— v2，状态枚举（英文 code → 中文展示映射）
- `.agent-ops/STAGE3-PIPELINE.md` —— 寄存器决策（product register）

## 允许读取的路径

- 整个项目目录（只读参考）

## 允许修改的路径

- `docs/design/PRODUCT.md`（**新建**，产品/品牌定位上下文）
- `docs/design/DESIGN.md`（**新建**，设计语言系统）

## 禁止操作

- 不修改 `src/`、`config/`、`data/`、`scripts/`、`tests/` 下任何文件
- 不修改任何已存在文档（PRD/架构/调研等）
- 不创建实际前端代码（本任务是设计文档，代码在 TASK-016 craft）

## 实现要求

### 一、PRODUCT.md 内容

#### 1. 产品定位（引用 PRD/PROJECT）
- 一句话定位
- 目标用户（P1 高频跨平台投递者）
- 核心价值（信息统一 / 投递闭环 / 数据驱动）

#### 2. 寄存器决策
- 选择：**product register**
- 理由：应用/工具型（仪表盘+列表+表单+工作流），非品牌营销页
- 影响：设计服务于任务效率，克制装饰

#### 3. 产品性格关键词
- 建议关键词（如：高效 / 可信赖 / 清晰 / 专业 / 不过分花哨）
- 反向关键词（不要什么：花哨 / 模糊 / 信息过载 / 模板感）

#### 4. 核心用户任务（从 PRD 功能点提炼）
- 每个核心任务对应一个主页面（为 shape 铺路）

### 二、DESIGN.md 内容（设计语言核心）

#### 1. 设计原则（5 条）
基于 product register + PRD 的状态可视化要求，例如：
- **效率优先**：求职者时间宝贵，操作路径要短
- **状态可读**：9 状态机必须在 UI 上清晰区分（颜色+图标+标签）
- **信息分层**：仪表盘要一眼看到关键数据，详情要结构化
- **克制装饰**：拒绝渐变文字/玻璃态/无意义卡片（工作流反 AI 模板规则）
- **状态完整**：每个组件要有空/加载/错误态

#### 2. 色彩系统（重点）
基于状态机需求设计语义色：

**主色（Primary）**：
- 用于品牌识别、主要 CTA
- 建议：专业蓝（如 #2563EB）或沉稳绿（如 #059669）

**状态语义色（核心，呼应 9 状态机）**：
| 状态 | 颜色 | 用途 |
|------|------|------|
| applied（已投递） | 中性蓝 | 进行中-初始 |
| test（笔试） | 中性青 | 进行中 |
| interviewing（面试中） | 中性紫 | 进行中-关键 |
| offer_pending（Offer待决定） | 琥珀/橙 | 需用户行动 |
| offer_accepted（已接受） | 成功绿 | 终态-成功 |
| offer_declined（已婉拒） | 中性灰 | 终态-用户主动 |
| rejected（公司拒绝） | 警告红 | 终态-失败 |
| no_response（无回应关闭） | 中性灰深 | 终态-超时 |
| withdrawn（主动撤回） | 中性灰 | 终态-用户主动 |

**功能色**：
- success（成功反馈）、warning（警告，如 DDL 临近）、danger（危险操作）、info（提示）

**中性色阶**：10 级灰阶（用于文字、背景、边框、分隔线）

**背景**：亮色主题为主（暗色主题列为未来）

#### 3. 排版系统（Typography）
- 字体族：中文（如 PingFang/思源黑体）+ 英文（如 Inter）
- 字号阶梯：12/14/16/18/20/24/30/36（8 倍数）
- 行高、字重规则
- 中文展示与英文 code 的搭配（如状态标签：英文 code 存储但中文展示）

#### 4. 间距系统
- 8 倍数基准（4/8/12/16/24/32/48/64）
- 组件内/组件间/区块间规则

#### 5. 圆角与阴影
- 圆角：小（4px 控件）/ 中（8px 卡片）/ 大（12-16px 容器）
- 阴影：克制（product register 不用大阴影幽灵卡，工作流明令）

#### 6. 组件库选型
基于 PROJECT.md 技术栈：
- **基础组件**：shadcn/ui（Button/Card/Dialog/Select/Table/Badge 等）
- **图表**：Recharts（看板漏斗/趋势/分布）
- **状态管理**：Zustand（本地交互状态：筛选/批量选中/快捷按钮）
- **数据请求**：TanStack Query（服务端状态）
- **图标**：lucide-react

#### 7. 状态标签（Badge）设计规范（呼应状态机）
- 每个状态对应一个 Badge 变体（颜色+文字+图标）
- 给出 9 个状态的 Badge 设计表（颜色/文字/图标/使用场景）

#### 8. 反 AI 模板清单（工作流明令）
明确列出本项目**拒绝**的设计模式：
- ❌ 渐变文字（gradient text）
- ❌ 装饰性玻璃态（glassmorphism）
- ❌ 重复等大卡片网格
- ❌ 每个区块 all-caps eyebrow
- ❌ 无意义的 01/02/03 标记
- ❌ 大阴影幽灵卡
- ❌ 只有 happy path 的 UI

### 三、质量要求

- **色彩系统必须覆盖 9 状态**（这是状态机 UI 可读性的基础）
- **组件库选型必须呼应技术栈**（shadcn/ui + Recharts + Zustand，已在架构定）
- **反 AI 模板清单必须明确**（工作流硬要求）
- **product register 取舍要清晰**（效率优先，克制装饰）

## 验证命令

纯文档任务。自查清单：
- [ ] PRODUCT.md 含定位/寄存器/性格/核心任务
- [ ] DESIGN.md 含原则/色彩/排版/间距/圆角阴影/组件库/状态标签/反模板
- [ ] 色彩系统覆盖 9 状态语义色
- [ ] 状态标签 Badge 设计表完整（9 状态）
- [ ] 反 AI 模板清单明确（7 条以上）

## 结果文件路径

- `docs/design/PRODUCT.md`
- `docs/design/DESIGN.md`

## 结果格式（写入 outbox）

```markdown
# TASK-012 执行结果

## 摘要
<2-3 句话概述设计语言核心>

## 修改/新建的文件清单
- docs/design/PRODUCT.md（新建）
- docs/design/DESIGN.md（新建）

## 关键设计决策
- 寄存器：product
- 主色：...
- 状态语义色：9 个状态全覆盖
- 组件库：shadcn/ui + Recharts + Zustand

## 自查清单结果
<逐项打勾>

## 未解决的问题
- <如有>

## 需要 Codex 判断的风险
- <如有>
```
