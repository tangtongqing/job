"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  Bookmark,
  BriefcaseBusiness,
  CalendarClock,
  Check,
  CheckCircle2,
  Menu,
  MousePointer2,
  Play,
  Sparkles,
  X,
} from "lucide-react";

import { ProductFilm } from "./ProductFilm";

const FLOW_STAGES = ["收藏", "待投递", "已投递", "测评", "面试", "Offer"];

const WORKFLOW_FILMS = [
  {
    number: "01",
    title: "从分散信息，到一张清单",
    body: "按关键词、公司和地点筛选聚合岗位，保留来源与更新时间。",
    src: "/media/workflow-discover.webm",
    fallback: "discover",
  },
  {
    number: "02",
    title: "先收藏，再决定是否行动",
    body: "收藏与待投递分开，减少“存了很多，却不知道下一步”的混乱。",
    src: "/media/workflow-save.webm",
    fallback: "save",
  },
  {
    number: "03",
    title: "每次进展，都成为轨迹",
    body: "状态流转写入事件时间线，面试、测评和 Offer 不再靠记忆。",
    src: "/media/workflow-progress.webm",
    fallback: "progress",
  },
  {
    number: "04",
    title: "看板告诉你该做什么",
    body: "用真实到达阶段、近期安排和最近更新，保持稳定的求职节奏。",
    src: "/media/workflow-review.webm",
    fallback: "review",
  },
] as const;

export function MarketingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const reduceMotion = useReducedMotion();

  return (
    <main className="overflow-hidden bg-[#fbfbfc] text-[#151517] dark:bg-[#0d0d0f] dark:text-white">
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-black/[0.06] bg-[#fbfbfc]/92 backdrop-blur-xl dark:border-white/10 dark:bg-[#0d0d0f]/90" aria-label="官网导航">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
          <Link href="/" className="flex min-h-11 items-center gap-2.5 rounded-lg text-sm font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1]">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#6366f1] text-white"><Activity className="h-4 w-4" /></span>
            JobPulse
          </Link>
          <div className="hidden items-center gap-7 md:flex">
            <a href="#product" className="text-xs text-black/55 hover:text-black dark:text-white/55 dark:hover:text-white">产品</a>
            <a href="#workflow" className="text-xs text-black/55 hover:text-black dark:text-white/55 dark:hover:text-white">工作流</a>
            <a href="#pricing" className="text-xs text-black/55 hover:text-black dark:text-white/55 dark:hover:text-white">定价</a>
            <Link href="/case-study" className="text-xs text-black/55 hover:text-black dark:text-white/55 dark:hover:text-white">设计案例</Link>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/dashboard" className="hidden min-h-10 items-center px-3 text-xs font-medium text-black/60 hover:text-black sm:inline-flex dark:text-white/60 dark:hover:text-white">进入 Demo</Link>
            <Link href="/dashboard" className="inline-flex min-h-10 items-center gap-1.5 rounded-lg bg-[#151517] px-4 text-xs font-medium text-white hover:bg-black/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] dark:bg-white dark:text-black">
              免费体验 <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <button type="button" onClick={() => setMenuOpen((open) => !open)} aria-label={menuOpen ? "关闭菜单" : "打开菜单"} aria-expanded={menuOpen} className="grid h-11 w-11 place-items-center rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] md:hidden">
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
        {menuOpen && (
          <div className="border-t border-black/[0.06] bg-[#fbfbfc] px-5 py-3 md:hidden dark:border-white/10 dark:bg-[#0d0d0f]">
            {[['产品', '#product'], ['工作流', '#workflow'], ['定价', '#pricing'], ['设计案例', '/case-study']].map(([label, href]) => (
              <a key={href} href={href} onClick={() => setMenuOpen(false)} className="flex min-h-11 items-center text-sm text-black/65 dark:text-white/65">{label}</a>
            ))}
          </div>
        )}
      </nav>

      <section className="relative px-5 pb-24 pt-32 lg:pb-32 lg:pt-40">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-3xl text-center">
            <motion.p initial={reduceMotion ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }} className="inline-flex min-h-8 items-center gap-2 rounded-full border border-black/[0.08] bg-white px-3 text-[11px] font-medium text-black/60 dark:border-white/10 dark:bg-white/[0.05] dark:text-white/60">
              <Sparkles className="h-3.5 w-3.5 text-[#6366f1]" /> Job search workspace · Beta
            </motion.p>
            <motion.h1 initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.08 }} className="mt-6 text-balance text-[clamp(2.8rem,7vw,5rem)] font-semibold leading-[0.98] tracking-[-0.055em]">
              <span className="block sm:inline">求职，</span><span>不该靠记忆。</span>
            </motion.h1>
            <motion.p initial={reduceMotion ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.16 }} className="mx-auto mt-6 max-w-2xl text-balance text-base leading-7 text-black/55 md:text-lg dark:text-white/55">
              把分散岗位、收藏决策、投递状态和近期安排收进一个工作台。JobPulse 让每一次行动都有记录，下一步始终清楚。
            </motion.p>
            <motion.div initial={reduceMotion ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.24 }} className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link href="/dashboard" className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#151517] px-6 text-sm font-medium text-white hover:bg-black/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] dark:bg-white dark:text-black">
                打开完整 Demo <ArrowRight className="h-4 w-4" />
              </Link>
              <a href="#product" className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-black/10 bg-white px-6 text-sm font-medium hover:bg-black/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] dark:border-white/10 dark:bg-white/[0.04] dark:hover:bg-white/[0.07]">
                <Play className="h-4 w-4" /> 看 18 秒产品实录
              </a>
            </motion.div>
            <p className="mt-4 text-[11px] text-black/40 dark:text-white/40">Beta 期间免费 · 本地 Demo 无需注册 · 数据可一键重置</p>
          </div>

          <motion.div id="product" initial={reduceMotion ? false : { opacity: 0, y: 36, scale: 0.985 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.75, delay: 0.32 }} className="relative mx-auto mt-14 max-w-6xl scroll-mt-24">
            <div className="absolute -left-16 top-20 hidden text-[10px] font-medium uppercase tracking-[0.2em] text-black/35 xl:block dark:text-white/35">Real product<br />Real data</div>
            <div className="rounded-[1.35rem] border border-black/10 bg-[#111113] p-2 shadow-[0_30px_80px_-40px_rgba(0,0,0,0.45)] dark:border-white/15">
              <div className="flex h-9 items-center gap-1.5 px-3">
                <span className="h-2 w-2 rounded-full bg-white/25" /><span className="h-2 w-2 rounded-full bg-white/15" /><span className="h-2 w-2 rounded-full bg-white/10" />
                <span className="ml-3 text-[9px] text-white/35">jobpulse.local/dashboard</span>
              </div>
              <ProductFilm src="/media/product-overview.webm" label="JobPulse 求职概览产品实录" className="aspect-[16/9] rounded-xl">
                <HeroProductFallback />
              </ProductFilm>
            </div>
            <motion.svg aria-hidden="true" viewBox="0 0 1200 150" className="pointer-events-none absolute -bottom-[7.25rem] left-1/2 hidden h-36 w-[92%] -translate-x-1/2 overflow-visible md:block">
              <motion.path d="M 20 18 C 220 18, 210 112, 420 92 S 760 58, 1180 125" fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" initial={reduceMotion ? { pathLength: 1 } : { pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.4, delay: 1 }} />
              {[20, 420, 760, 1180].map((cx, index) => <motion.circle key={cx} cx={cx} cy={[18, 92, 77, 125][index]} r="5" fill="#fbfbfc" stroke="#6366f1" strokeWidth="2" initial={reduceMotion ? false : { scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 1.25 + index * 0.15 }} />)}
            </motion.svg>
          </motion.div>
        </div>
      </section>

      <section className="border-y border-black/[0.06] bg-white px-5 py-24 md:py-32 dark:border-white/10 dark:bg-[#111113]">
        <div className="mx-auto max-w-6xl">
          <motion.div initial={reduceMotion ? false : { opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-15%" }} className="grid gap-10 lg:grid-cols-[0.75fr_1.25fr] lg:items-end">
            <div>
              <p className="text-xs font-medium text-[#6366f1]">A TRACE, NOT A PILE</p>
              <h2 className="mt-3 text-balance text-3xl font-semibold tracking-[-0.035em] md:text-5xl">每一步，<br className="hidden lg:block" />都有记录。</h2>
            </div>
            <p className="max-w-2xl text-base leading-7 text-black/55 dark:text-white/55">收藏不是投递，面试也不是结果。JobPulse 用一条持续的状态轨迹连接每个决定，让求职过程从零散动作变成可回看、可调整的系统。</p>
          </motion.div>

          <div className="mt-16 overflow-x-auto pb-2">
            <div className="relative mx-auto flex min-w-[760px] max-w-5xl items-start justify-between">
              <div className="absolute left-[6%] right-[6%] top-5 h-px bg-black/12 dark:bg-white/15" />
              <motion.div initial={reduceMotion ? { scaleX: 1 } : { scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true, margin: "-20%" }} transition={{ duration: 1.1 }} className="absolute left-[6%] right-[6%] top-5 h-px origin-left bg-[#6366f1]" />
              {FLOW_STAGES.map((stage, index) => (
                <motion.div key={stage} initial={reduceMotion ? false : { opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * 0.08 }} className="relative z-10 w-24 text-center">
                  <span className={`mx-auto grid h-10 w-10 place-items-center rounded-full border-4 border-white text-xs font-semibold dark:border-[#111113] ${index < 5 ? "bg-[#6366f1] text-white" : "bg-[#ececf0] text-black/45 dark:bg-white/10 dark:text-white/45"}`}>{index < 5 ? <Check className="h-4 w-4" /> : index + 1}</span>
                  <p className="mt-3 text-xs font-medium">{stage}</p>
                  <p className="mt-1 text-[10px] text-black/40 dark:text-white/40">{index < 5 ? "已形成记录" : "继续前进"}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="workflow" className="scroll-mt-20 px-5 py-24 md:py-32">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
            <div>
              <p className="text-xs font-medium text-[#6366f1]">THE ACTUAL WORKFLOW</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-5xl">不是功能拼盘，<br />是一条完整工作流。</h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-black/50 dark:text-white/50">以下影片均由真实 Demo 自动操作录制。网络或减少动态效果模式下，会显示同一产品结构的静态预览。</p>
          </div>
          <div className="mt-14 grid gap-x-6 gap-y-12 md:grid-cols-2">
            {WORKFLOW_FILMS.map((film, index) => (
              <motion.article key={film.number} initial={reduceMotion ? false : { opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-10%" }} transition={{ duration: 0.55, delay: index % 2 * 0.08 }}>
                <ProductFilm src={film.src} label={`${film.title}产品实录`} className="aspect-[16/10] rounded-2xl border border-black/[0.08] dark:border-white/10">
                  <WorkflowFallback kind={film.fallback} />
                </ProductFilm>
                <div className="mt-5 grid grid-cols-[2rem_1fr] gap-3">
                  <span className="pt-0.5 text-[11px] font-medium text-[#6366f1]">{film.number}</span>
                  <div><h3 className="text-lg font-semibold tracking-[-0.02em]">{film.title}</h3><p className="mt-1.5 max-w-lg text-sm leading-6 text-black/50 dark:text-white/50">{film.body}</p></div>
                </div>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-[#111113] px-5 py-24 text-white md:py-32">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <p className="text-xs font-medium text-[#a5b4fc]">AI WITH A CONFIRM BUTTON</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-5xl">自动化负责建议，<br />你负责决定。</h2>
            <p className="mt-6 max-w-lg text-sm leading-7 text-white/55">粘贴招聘邮件后，系统可以建议公司、岗位和下一状态。但任何状态变化，都要经过你的确认。效率不应以失去控制为代价。</p>
            <Link href="/applications" className="mt-7 inline-flex min-h-11 items-center gap-2 rounded-lg bg-white px-5 text-sm font-medium text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#a5b4fc]">体验邮件解析 <ArrowRight className="h-4 w-4" /></Link>
          </div>
          <div className="rounded-2xl border border-white/12 bg-white/[0.055] p-4 md:p-6">
            <div className="rounded-xl bg-white p-4 text-black">
              <div className="flex items-center gap-2 border-b border-black/[0.06] pb-3"><Sparkles className="h-4 w-4 text-[#6366f1]" /><span className="text-xs font-semibold">解析建议</span><span className="ml-auto rounded-full bg-emerald-50 px-2 py-1 text-[10px] text-emerald-700">置信度 92%</span></div>
              <div className="grid grid-cols-2 gap-3 py-4 text-xs"><Info label="公司" value="美团" /><Info label="岗位" value="增长产品经理" /><Info label="建议状态" value="面试中" /><Info label="匹配投递" value="#2" /></div>
              <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-[11px] leading-5 text-amber-800"><MousePointer2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />建议不会自动写入。点击确认后，才会更新状态并记录事件。</div>
              <button type="button" className="mt-3 min-h-11 w-full rounded-lg bg-[#151517] text-xs font-medium text-white">确认更新为「面试中」</button>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="scroll-mt-20 px-5 py-24 md:py-32">
        <div className="mx-auto max-w-5xl rounded-3xl border border-black/[0.08] bg-white p-6 md:p-10 dark:border-white/10 dark:bg-[#111113]">
          <div className="grid gap-10 lg:grid-cols-[1fr_0.8fr] lg:items-center">
            <div>
              <p className="text-xs font-medium text-[#6366f1]">PUBLIC BETA</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-5xl">现在，完整体验免费。</h2>
              <p className="mt-5 max-w-xl text-sm leading-7 text-black/55 dark:text-white/55">当前版本用于完整产品演示与早期验证，不收取费用，也没有虚构的付费权益。未来若开放长期使用，将先验证同步、通知和数据托管的真实成本。</p>
              <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-xs text-black/65 dark:text-white/65">
                {["完整岗位与投递流程", "可重复 Demo 数据", "AI 建议需人工确认", "随时浏览设计案例"].map((item) => <span key={item} className="inline-flex items-center gap-1.5"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />{item}</span>)}
              </div>
            </div>
            <div className="rounded-2xl bg-[#f4f4f6] p-6 dark:bg-white/[0.06]">
              <p className="text-xs font-medium text-black/50 dark:text-white/50">Beta access</p>
              <p className="mt-3 text-4xl font-semibold tracking-tight">¥0</p>
              <p className="mt-1 text-xs text-black/45 dark:text-white/45">无需信用卡 · 当前无需注册</p>
              <Link href="/dashboard" className="mt-6 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-[#151517] text-sm font-medium text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] dark:bg-white dark:text-black">开始完整演示 <ArrowRight className="h-4 w-4" /></Link>
              <Link href="/case-study" className="mt-2 inline-flex min-h-11 w-full items-center justify-center text-xs font-medium text-black/55 hover:text-black dark:text-white/55 dark:hover:text-white">查看产品设计案例</Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-black/[0.07] px-5 py-8 dark:border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/" className="flex items-center gap-2 text-sm font-semibold"><Activity className="h-4 w-4 text-[#6366f1]" />JobPulse</Link>
          <div className="flex flex-wrap gap-5 text-xs text-black/45 dark:text-white/45"><a href="#product">产品</a><a href="#workflow">工作流</a><a href="#pricing">定价</a><Link href="/case-study">设计案例</Link></div>
          <p className="text-[11px] text-black/35 dark:text-white/35">© {new Date().getFullYear()} JobPulse · Beta</p>
        </div>
      </footer>
    </main>
  );
}

function HeroProductFallback() {
  return (
    <div className="flex h-full bg-[#f7f7f8] text-[#151517]">
      <aside className="hidden w-[18%] border-r border-black/[0.07] bg-white p-[2.2%] sm:block">
        <div className="flex items-center gap-2 text-[clamp(6px,1vw,13px)] font-semibold"><span className="grid aspect-square w-[14%] place-items-center rounded bg-[#6366f1] text-white"><Activity className="h-1/2 w-1/2" /></span>JobPulse</div>
        <div className="mt-[20%] space-y-[7%]">{["概览", "发现岗位", "收藏与待投递", "投递进展", "近期安排"].map((label, index) => <div key={label} className={`rounded px-[8%] py-[5%] text-[clamp(5px,.75vw,10px)] ${index === 0 ? "bg-[#eef2ff] text-[#4338ca]" : "text-black/40"}`}>{label}</div>)}</div>
      </aside>
      <div className="flex-1 p-[3.5%]">
        <p className="text-[clamp(5px,.65vw,9px)] font-medium text-[#4f46e5]">YOUR SEARCH, IN MOTION</p>
        <h3 className="mt-[1%] text-[clamp(12px,2vw,27px)] font-semibold tracking-tight">今天从清楚下一步开始</h3>
        <div className="mt-[3%] grid grid-cols-4 gap-[1.5%]">{[["今日新增", 8], ["岗位库", 42], ["投递记录", 5], ["进行中", 4]].map(([label, value], index) => <div key={label} className={`rounded-[8px] border p-[9%] ${index === 3 ? "border-[#c7d2fe] bg-[#eef2ff]" : "border-black/[0.07] bg-white"}`}><p className="text-[clamp(4px,.55vw,8px)] text-black/40">{label}</p><p className="mt-[10%] text-[clamp(10px,1.6vw,22px)] font-semibold">{value}</p></div>)}</div>
        <div className="mt-[2%] rounded-[10px] border border-black/[0.07] bg-white p-[3%]">
          <p className="text-[clamp(5px,.7vw,10px)] font-semibold">投递轨迹</p>
          <div className="relative mt-[5%] flex justify-between"><div className="absolute left-[5%] right-[5%] top-[22%] h-px bg-[#6366f1]" />{[1, 2, 2, 1, 0].map((count, i) => <div key={i} className="relative z-10 w-[16%] text-center"><span className={`mx-auto grid aspect-square w-[24%] place-items-center rounded-full text-[clamp(4px,.55vw,8px)] ${count ? "bg-[#6366f1] text-white" : "bg-[#ececf0]"}`}>{count}</span><p className="mt-[6%] text-[clamp(4px,.55vw,8px)]">{["已投递", "测评", "面试", "Offer", "已接受"][i]}</p></div>)}</div>
        </div>
      </div>
    </div>
  );
}

function WorkflowFallback({ kind }: { kind: typeof WORKFLOW_FILMS[number]["fallback"] }) {
  if (kind === "discover") return <div className="h-full p-[7%]"><div className="flex gap-[2%]">{["产品经理", "公司", "地点"].map((item) => <span key={item} className="rounded border border-black/10 bg-white px-[4%] py-[2%] text-[clamp(5px,.7vw,10px)] text-black/45">{item}</span>)}</div><div className="mt-[5%] space-y-[2.5%]">{["MiniMax · AI 产品经理", "大疆 · 硬件产品经理", "哔哩哔哩 · 社区产品经理"].map((item) => <div key={item} className="flex items-center rounded-lg border border-black/[0.07] bg-white p-[3%] text-[clamp(5px,.8vw,11px)]"><BriefcaseBusiness className="mr-[3%] h-[1em] w-[1em] text-[#6366f1]" />{item}<span className="ml-auto text-black/35">加入待投递</span></div>)}</div></div>;
  if (kind === "save") return <div className="h-full p-[7%]"><div className="inline-flex rounded-lg border border-black/10 bg-white p-[1%] text-[clamp(5px,.75vw,10px)]"><span className="rounded bg-[#151517] px-[8%] py-[4%] text-white">收藏 2</span><span className="px-[8%] py-[4%] text-black/45">待投递 2</span></div><div className="mt-[6%] grid grid-cols-2 gap-[3%]">{["社区产品经理", "硬件产品经理"].map((item) => <div key={item} className="rounded-lg border border-black/[0.07] bg-white p-[7%]"><Bookmark className="h-[1em] w-[1em] text-[#6366f1]" /><p className="mt-[8%] text-[clamp(5px,.8vw,11px)] font-semibold">{item}</p><p className="mt-[4%] text-[clamp(4px,.6vw,8px)] text-black/40">收藏 → 待投递</p></div>)}</div></div>;
  if (kind === "progress") return <div className="h-full p-[7%]"><p className="text-[clamp(6px,.85vw,12px)] font-semibold">美团 · 增长产品经理</p><div className="mt-[8%] space-y-[5%]">{[["面试中", "今天 14:20"], ["已投递", "7 月 8 日"], ["收藏", "7 月 6 日"]].map(([label, date], index) => <div key={label} className="flex gap-[4%]"><div className="flex flex-col items-center"><span className={`aspect-square w-[clamp(8px,1.2vw,16px)] rounded-full ${index === 0 ? "bg-[#6366f1]" : "bg-black/15"}`} /><span className="h-full w-px bg-black/10" /></div><div><p className="text-[clamp(5px,.75vw,10px)] font-medium">{label}</p><p className="text-[clamp(4px,.6vw,8px)] text-black/40">{date}</p></div></div>)}</div></div>;
  return <div className="grid h-full grid-cols-[1.2fr_.8fr] gap-[3%] p-[7%]"><div className="rounded-lg border border-black/[0.07] bg-white p-[6%]"><p className="text-[clamp(5px,.75vw,10px)] font-semibold">投递轨迹</p><div className="mt-[15%] flex items-end gap-[5%]">{[30, 62, 45, 80, 55].map((height, index) => <span key={index} className="flex-1 rounded-t bg-[#6366f1]/70" style={{ height: `${height}%` }} />)}</div></div><div className="rounded-lg bg-[#151517] p-[8%] text-white"><CalendarClock className="h-[1em] w-[1em] text-[#a5b4fc]" /><p className="mt-[10%] text-[clamp(5px,.75vw,10px)] font-semibold">下一步</p><p className="mt-[12%] text-[clamp(4px,.6vw,8px)] text-white/50">2 天后 · 在线测评</p><p className="mt-[8%] text-[clamp(4px,.6vw,8px)] text-white/50">3 天后 · 二轮面试</p></div></div>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><p className="text-[10px] text-black/40">{label}</p><p className="mt-1 font-medium">{value}</p></div>;
}
