# web · JobPulse 前端

> 阶段 3 TASK-016b 第一步：按 Nexora 提示词原样复现 hero 落地页。
> 当前为**风格骨架验证版**（内容仍是通用 SaaS "Nexora"，非招聘产品）。
> 风格确认后进入第二步：适配为招聘产品内容 + 补暗色主题。

## 运行

```bash
cd web
npm install
npm run dev
# 打开 http://localhost:3000
```

> 依赖：Node 18+。首次安装会拉取 next/react/framer-motion/lucide-react/tailwindcss。

## 当前文件结构

```
web/
├── app/
│   ├── globals.css          # 字体导入 + CSS 变量（配色 token，light only）
│   ├── layout.tsx           # 根布局
│   └── page.tsx             # 落地页（7 屏滚动叙事 + 产品预览）
├── components/
│   ├── ui/
│   │   └── button.tsx       # shadcn/ui Button（精简版）
│   └── marketing/
│       ├── Navbar.tsx       # 顶部导航
│       ├── Hero.tsx         # hero 区（视频背景 + 5 层 framer-motion 动画）
│       └── DashboardPreview.tsx  # 纯 React 代码绘制的仪表盘预览
├── lib/
│   └── utils.ts             # cn() 类名合并
├── tailwind.config.ts       # fontFamily + 语义色映射
├── tsconfig.json            # @/* 路径别名
├── next.config.js
├── postcss.config.js
└── package.json
```

## 设计 token（对应提示词）

| Token | 值 | 用途 |
|-------|-----|------|
| `--background` | `0 0% 100%` | 白底 |
| `--foreground` | `210 14% 17%` | 深炭灰文字 |
| `--accent` | `239 84% 67%` | 靛蓝（图表/CTA点缀） |
| `--muted-foreground` | `184 5% 55%` | 次要文字 |
| `--radius` | `0.5rem` | 圆角基准 |
| `--font-display` | Instrument Serif | 标题（italic 用于强调词） |
| `--font-body` | Inter | 正文 |
| `--shadow-dashboard` | 两层柔阴影 | 产品预览和实体卡片 |

## 已知待办（第二步处理）

- [ ] 内容替换为招聘产品（hero 文案 / dashboard 换成我们的看板）
- [ ] 补 `.dark` 主题（双主题决策已定，待风格确认后加）
- [ ] 字体改用 next/font 本地加载（当前用 Google Fonts CDN，生产前换）
- [ ] 视频背景是占位 URL，后续确认是否保留/替换

---

*TASK-016b step 1 · 2026-06-24*
