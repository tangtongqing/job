# BLOCKED 清单 · 需高级智能体/用户完成的工作

> 本文档记录 Codex（主智能体）受执行环境限制**无法闭环**的工作。
> - **BLOCKED-VERIFY**：Codex 能产出，但无法验证效果（看不到渲染/图片）。需高级智能体验收。
> - **BLOCKED-DO**：Codex 无法执行。需高级智能体或用户本地执行。
> 协作原则：保证所有产品开发工作全部完成，做不了就标记阻塞，留给后续接手。
>
> **v2 更新**（2026-06-24，配合 PROJECT.md v4 双面产品+演进蓝图）：新增营销面渲染验证、响应式/PWA 验证、营销文案定稿。

---

## BLOCKED-VERIFY（我做了，需高级智能体验收）

| 任务 | 产出 | 为什么需要验收 | 交接说明 |
|------|------|--------------|---------|
| TASK-016a 产品面 craft 渲染效果 | Next.js 组件代码 + Mock 数据 | Codex 读代码能验状态色/流转合法性/反AI模板，但**看不到浏览器渲染效果** | 在 web/ 目录，`npm install && npm run dev`，访问 `(app)/*` 看效果，截图反馈 |
| TASK-016b 营销面 craft 渲染效果 | 落地页 + 定价页组件 | 同上，**hero 视觉/留白/入场动画/定价卡片**需看渲染图 | 访问 `/` 和 `/pricing`，截图反馈 |
| TASK-017 critique 视觉审查 | 代码层审查报告 | **AI 味检测、认知负荷、视觉一致性**需看渲染图（两面都要） | 需产品面+营销面渲染截图 + 代码，做视觉层 critique |
| TASK-018 polish 效果验证 | 代码层 polish | 微调后**看不到效果** | 同上，需渲染验证 |
| **响应式 + PWA 验证** 🆕 | 响应式样式 + manifest.json | Codex 能写断点样式，但**看不到不同屏幕尺寸的渲染** | DevTools 切设备（桌面/平板/手机），验投递管理+AI解析在手机可用；PWA 加桌面测试 |
| **营销面文案定稿** 🆕 | BRAND.md §6 候选文案 | Hero 标题/副标题/CTA 的最终语气需用户拍板 | 用户在 BRAND.md §6.1 三个候选里选，或给新方向 |

---

## BLOCKED-DO（我做不了，需高级智能体/用户执行）

| 任务 | 我做不到的原因 | 已完成的准备 | 交接说明 |
|------|--------------|------------|---------|
| **真实爬虫运行 + 数据采集** | Codex 无运行 Python 的执行环境，无法实际访问 BOSS/牛客、处理反爬 | `docs/architecture/crawler-module.md` v2 完整设计了适配器/调度/去重/合规。**代码图纸已就绪** | 高级智能体在本地/沙箱初始化项目，按图纸写 crawler 代码并运行；或用户本地 `python -m crawler.scheduler` 跑采集（可能需手动处理反爬、登录态） |
| **F-C.5 AI 解析真实验证** | 需真实 DeepSeek/OpenAI API Key + 真实求职邮件 | `docs/architecture/ai-parser-module.md` v2 设计了 Prompt + 三级降级 + 匹配逻辑 | 配置 .env 的 API Key，拿真实求职邮件测试解析准确率，反馈 Prompt 优化 |
| **用户访谈（路径B验证窗口）** | Codex 不能替用户和真人对话 | `docs/research/market-analysis.md` v3 写了验证窗口要求（5-8 次访谈 + 3-5 次原型测试） | 用户按 conducting-user-interviews skill 亲自访谈，记录反馈，迭代画像/优先级 |
| **真实 LLM API 联调** | 同上，需 API Key + 真实场景 | ai-parser-module.md 代码就绪 | 本地配置后联调 |
| **项目本地初始化与运行** | Codex 无执行环境 | 架构文档写了完整启动命令（uvicorn + npm run dev） | 用户或高级智能体在本地初始化：`pip install`、`npm install`、配 .env、建 SQLite |

---

## 高级智能体接手指南

如果引入高级智能体（如具备多模态/联网/执行环境的能力）：

1. **先读本文件**：了解哪些 BLOCKED 需要它处理
2. **读 `docs/architecture/`**：架构/数据库/API/采集/AI 设计已就绪（v3 含演进预留 §九），是代码图纸
3. **读 `docs/design/`**：设计语言（PRODUCT.md 产品面 + BRAND.md 营销面 + DESIGN.md 共享令牌）+ 5 份产品面 shape + 参考映射
4. **读 `docs/product/evolution-roadmap.md`**：M0→M1→M2 演进蓝图 + 付费分级
5. **优先级建议**：
   - P0：craft 渲染验证（产品面 016a + 营销面 016b，最快见效，让原型可见）
   - P0：爬虫运行 + 真实数据（解决 Demo 核心痛点）
   - P1：AI 解析真实验证
   - P1：响应式 + PWA 多设备验证
   - P2：用户访谈（用户自己做）

---

## Codex 角色说明

在高级智能体介入后：
- Codex 从"主智能体"**降级为"执行/协助角色"**
- 高级智能体接管 BLOCKED 项的策略判断与执行
- Codex 继续负责代码编写、文档维护、跨文档一致性
- 降级发生时在本文件追加记录

*最后更新：2026-07-01（v3，营销页 TASK-016b 已完成，视觉优化已验收）*
