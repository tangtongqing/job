# 任务交接 · 营销页视觉优化（TASK-VISUAL-OPTIMIZATION）

> **给高级智能体的交接文档。** Codex（主智能体）已完成营销页代码骨架，但缺乏渲染视觉验证能力（看不到浏览器渲染）。本任务需要具备**多模态视觉验证**能力的智能体接手，做像素级打磨和内容丰富度提升。
>
> **本文件自包含**——无需阅读之前的对话历史即可接手。

---

## 一、任务概述

**目标**：把一个大学生招聘信息聚合产品（JobPulse）的 SaaS 营销落地页，从"代码骨架"打磨到"成熟 SaaS 落地页"水准。

**定位**：真实营销型（类似 Linear / Notion / Vercel 的产品落地页），非作品集展示。

**核心问题**：当前页面结构、动画、导航、双主题都已就位，但**内容丰富度不足**——Linear 式落地页之所以不空，是因为每个 section 有真实产品 UI 撑场。我们的 section 内容（手绘图表、图标卡）偏单薄，需要补充更真实的、动态的产品界面展示。

---

## 二、技术栈与运行方式

| 项 | 说明 |
|----|------|
| 框架 | Next.js 14 (App Router) + TypeScript |
| 样式 | Tailwind CSS + CSS 变量（设计 token） |
| 动画 | framer-motion |
| 图标 | lucide-react |
| 主题 | next-themes（亮/暗双主题） |
| 组件 | shadcn/ui Button（精简版） |

### 运行

```bash
cd web
npm install
npm run dev
# 打开 http://localhost:3000
```

> 字体通过 Google Fonts CDN 加载（Instrument Serif + Inter），首屏可能有字体闪烁，属正常。

### 文件结构

```
web/
├── app/
│   ├── globals.css          # 设计 token（HSL 变量 + 亮暗主题 + 颗粒动画 keyframes）
│   ├── layout.tsx           # 根布局 + ThemeProvider
│   └── page.tsx             # 营销页入口（组装 7 屏 + Navbar + Background + BottomNav）
├── components/
│   ├── theme-provider.tsx   # next-themes 包装
│   ├── theme-toggle.tsx     # 亮/暗切换按钮
│   ├── ui/button.tsx        # shadcn Button
│   └── marketing/
│       ├── Background.tsx           # 全局背景（渐变 + SVG 颗粒纹理 + 视差光晕）
│       ├── Navbar.tsx               # 顶部多分区导航（产品/方案/资源/定价）
│       ├── BottomNav.tsx            # 底部悬浮胶囊（滚动超一屏显示）
│       ├── Hero.tsx                 # 第0屏：标题 + 看板动态演示
│       ├── PainPointsSection.tsx    # 第1屏：痛点共鸣（3 痛点卡）
│       ├── AggregationSection.tsx   # 第2屏：信息聚合（5平台漂入动画）
│       ├── StatusFlowSection.tsx    # 第3屏：投递状态机（横向流转图）
│       ├── DataDashboardSection.tsx # 第4屏：数据看板（漏斗+趋势+KPI）
│       ├── CapabilitiesSection.tsx  # 第5屏：能力全景（8 功能图标墙）
│       ├── PricingSection.tsx       # 第6屏：定价+CTA+Footer
│       ├── DashboardPreview.tsx     # Hero 里的看板预览组件
│       └── CountUp.tsx              # 数字滚动动画组件
└── lib/
    └── dashboard-data.ts    # 看板演示数据（可配置，后续接真实 API）
```

---

## 三、设计决策约束（不要推翻）

这些是和用户反复确认定的方向，优化时**保持一致**：

| 决策 | 不可推翻的理由 |
|------|--------------|
| **真实营销型定位** | 已从"作品集展示型"转向。CTA 用"免费开始"，不要"查看 Live Demo" |
| **双主题（亮+暗）** | 用户明确要。亮色默认（`defaultTheme="light"`） |
| **Linear 式背景** | 渐变 + SVG 颗粒纹理（feTurbulence）+ 极淡视差光晕。**不用背景视频**（已验证视频与多主题冲突） |
| **Instrument Serif italic 强调** | 这是字体灵魂。标题里关键词用 `<em>` 包裹（如 `Your job search, <em>in rhythm</em>.`） |
| **每屏布局不同** | 用户强调多元化：居中堆叠 / 居中三列 / 左右分栏 / 全宽沉浸 / 网格墙 / 居中三列 |
| **状态色用 CSS 变量** | `--status-applied` 等，亮暗各自调值，组件代码一份 |
| **反 AI 模板底线** | 两套主题都禁止：渐变文字（gradient text）/ 玻璃态（glassmorphism）/ 高饱和彩色光团 / "Trusted by" 灰度 logo 墙 / 抽象矢量插画占 hero |

---

## 四、当前完成状态（Codex 已做）

| 项 | 状态 |
|----|------|
| 7 屏结构 | ✅ Hero / 痛点 / 聚合 / 状态机 / 看板 / 能力 / 定价 |
| 双主题 | ✅ 亮暗 token 完整，9 状态色双主题 |
| 背景 | ✅ Linear 颗粒 + 渐变 + 视差光晕 |
| 导航 | ✅ 多分区下拉 + 移动端汉堡 + 底部悬浮胶囊 |
| 动画 | ✅ framer-motion 错峰淡入，`once:false` 可回放 |
| 看板可配置 | ✅ dashboard-data.ts 抽离 |
| CTA 去重 | ✅ 全改"免费开始"，底部导航无 CTA |

---

## 五、优化目标（按优先级）

### 🔴 P0：内容丰富度（根因问题，最重要）

**问题**：Linear 式落地页不空，是因为每屏有真实产品 UI 撑场。我们当前 section 的"系统图"是手绘的抽象图表（漏斗/趋势/状态机），单薄。

**优化方向**（任选可行的）：
1. **Hero 看板更真实**：当前 DashboardPreview 是简化版。可补充更多真实交互细节（hover 态、更多数据维度）
2. **功能屏用更丰富的产品截图/动画**：第 2-4 屏的右侧演示，从抽象图表升级为更接近真实产品界面的展示
3. **section 内容密度**：适当增加每屏的信息量，避免大片留白显得空（但保持呼吸感）

> 参考标杆：linear.app（每个 section 都是真实产品 UI 动画）

### 🔴 P0：多屏渲染视觉验证（Codex 做不到）

**问题**：Codex 看不到浏览器渲染，无法判断像素级问题。

**需要验证**：
1. 7 屏从头到尾滚动，每屏亮/暗两种模式都截图检查
2. 动画时序是否流畅（错峰 delay 是否自然）
3. 各 section 的间距、对齐、呼吸感
4. 文字可读性（暗色模式下状态色是否清晰）
5. 移动端（<768px）布局是否塌陷

### 🟡 P1：响应式优化

**已知问题**：
- 第 3 屏（状态机）横向 5 节点，移动端可能挤——考虑移动端改竖向时间线
- 第 6 屏（定价）三列卡，移动端单列堆叠需确认顺序和间距
- 底部悬浮导航移动端是否遮挡内容

### 🟡 P1：动画细节微调

**可能需要调整**：
- 第 2 屏聚合动画：5 个平台标签最终 `opacity:0` 消失，可能太快——用户可能想保留它们
- 看板 count-up 与曲线绘制的时序是否协调
- Background 视差光晕漂移幅度

### 🟢 P2：性能与细节

- 字体改用 next/font 本地加载（当前 Google Fonts CDN，生产前换）
- 图片/视频懒加载（如有）
- PWA manifest 配置（架构层已预留）

---

## 六、验收标准

| 验收项 | 标准 |
|--------|------|
| 视觉成熟度 | 整体观感接近 Linear / Notion 落地页水准，无"未完成感" |
| 内容丰富度 | 每个 section 有足够内容撑场，不空旷 |
| 双主题 | 亮/暗两种模式都成立，状态色清晰可辨 |
| 响应式 | 桌面/平板/手机三档都可用，核心流程不塌陷 |
| 动画 | 流畅自然，可回放，无卡顿 |
| 反 AI 模板 | 无渐变文字/玻璃态/高饱和光团 |

---

## 七、Codex 局限说明（为什么需要你接手）

| Codex 能做 | Codex 做不到 |
|-----------|-------------|
| 写代码、改样式、调动画参数 | 看浏览器渲染结果（无截图能力） |
| 维护设计 token、文档 | 判断像素级美观、间距是否舒服 |
| 多模态：分析图片（analyze_image） | 但**不能看自己写的代码渲染成什么样** |
| 联网研究标杆 | 实时操作浏览器交互验证 |

**核心**：本任务的 P0 项（视觉验证 + 内容丰富度打磨）**必须由具备渲染验证能力的智能体完成**。

---

## 八、接手指南

1. **先运行**：`cd web && npm install && npm run dev`，访问 localhost:3000
2. **完整走一遍**：7 屏 + 切换亮暗 + 移动端（DevTools 切设备）
3. **对照优化目标**：按优先级逐项处理
4. **保持设计约束**：第三节的决策不要推翻
5. **改动后同步**：更新 `.agent-ops/PROGRESS.md`

---

*创建日期：2026-06-24 | 上游：PROGRESS.md | 营销页代码：web/ 目录*
