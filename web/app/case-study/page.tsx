"use client";

import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { Activity, ArrowLeft, ArrowRight, Check, CircleDot, GitBranch, Play, ShieldCheck } from "lucide-react";

import { ProductFilm } from "@/components/marketing-v2/ProductFilm";

const DECISIONS = [
  {
    index: "01",
    title: "先降低维护成本，再扩展功能",
    body: "19 条公开求职记录显示，替代方案并不少，真正容易中断的是持续维护。产品因此从“再做一个岗位库”收敛为一条低成本推进主线。",
  },
  {
    index: "02",
    title: "收藏和待投递必须分开",
    body: "收藏表达兴趣，待投递表达承诺。模型允许同一岗位同时存在两种意图；创建投递后，待投递自动结束，收藏仍可保留。",
  },
  {
    index: "03",
    title: "状态变化写成事件，而不是覆盖字段",
    body: "投递状态仍保留当前值，但每次变化同步写入事件时间线，为漏斗、待办、纠错和复盘提供同一事实来源。",
  },
  {
    index: "04",
    title: "关键状态必须由用户确认",
    body: "AI 只提取公司、岗位、建议状态和明确时间；用户确认后才写入状态与计划事件，避免模型误判直接污染求职记录。",
  },
];

export default function CaseStudyPage() {
  const reduceMotion = useReducedMotion();

  return (
    <main className="bg-[#f7f7f5] text-[#171719] dark:bg-[#0d0d0f] dark:text-white">
      <nav className="sticky top-0 z-40 border-b border-black/[0.07] bg-[#f7f7f5]/92 backdrop-blur-xl dark:border-white/10 dark:bg-[#0d0d0f]/90">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <Link href="/" className="inline-flex min-h-11 items-center gap-2 text-xs font-medium text-black/55 hover:text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] dark:text-white/55 dark:hover:text-white"><ArrowLeft className="h-4 w-4" /> 返回 JobPulse 官网</Link>
          <Link href="/dashboard" className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[#171719] px-4 text-xs font-medium text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] dark:bg-white dark:text-black">打开产品 Demo <ArrowRight className="h-3.5 w-3.5" /></Link>
        </div>
      </nav>

      <section className="px-5 pb-20 pt-20 md:pb-28 md:pt-28">
        <div className="mx-auto max-w-6xl">
          <motion.div initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }} className="grid gap-10 lg:grid-cols-[1.35fr_.65fr] lg:items-end">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-[#6366f1]">Product case study · 2026</p>
              <h1 className="mt-5 max-w-4xl text-balance text-[clamp(2.8rem,7vw,5.4rem)] font-semibold leading-[0.96] tracking-[-0.055em]">把一次求职，设计成可管理的过程。</h1>
              <p className="mt-6 max-w-2xl text-base leading-7 text-black/55 dark:text-white/55">JobPulse 是一个招聘信息聚合与投递管理 SaaS。这个案例关注的不是“做了多少页面”，而是如何把分散信息、模糊意图和不断变化的进展，连接成一条可信的产品主线。</p>
            </div>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-5 border-t border-black/10 pt-5 text-xs dark:border-white/10 lg:grid-cols-1">
              <CaseMeta label="项目类型" value="0→1 产品重构 / 可演示 MVP" />
              <CaseMeta label="覆盖范围" value="产品策略、UX/UI、前后端实现、验证" />
              <CaseMeta label="当前状态" value="Public Beta · 线上可体验" />
              <CaseMeta label="证据边界" value="公开记录与专家走查，非真人测试" />
            </dl>
          </motion.div>

          <motion.div initial={reduceMotion ? false : { opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.12 }} className="mt-14 rounded-2xl border border-black/10 bg-[#111113] p-2 dark:border-white/15">
            <div className="flex h-9 items-center gap-1.5 px-3"><span className="h-2 w-2 rounded-full bg-white/25" /><span className="h-2 w-2 rounded-full bg-white/15" /><span className="h-2 w-2 rounded-full bg-white/10" /><span className="ml-3 text-[9px] text-white/35">完整产品讲解 · 约 75 秒</span></div>
            <ProductFilm src="/media/case-study-demo.webm" label="JobPulse 完整产品案例演示" className="aspect-video rounded-xl">
              <CaseFilmFallback />
            </ProductFilm>
          </motion.div>
        </div>
      </section>

      <section className="border-y border-black/[0.07] bg-white px-5 py-20 dark:border-white/10 dark:bg-[#111113] md:py-28">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[.7fr_1.3fr]">
          <div><p className="text-xs font-medium text-[#6366f1]">01 · PROBLEM FRAME</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-4xl">问题不是岗位太少，<br />而是上下文不断丢失。</h2></div>
          <div>
            <p className="text-lg leading-8 text-black/70 dark:text-white/70">求职者在多个招聘平台、表格、日历和聊天记录之间切换。每次切换都会重新回答三个问题：我为什么关注它？现在走到哪一步？下一步什么时候发生？</p>
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              <ProblemCard label="信息" value="岗位来源分散" note="重复搜索与去重成本" />
              <ProblemCard label="意图" value="收藏不等于行动" note="列表越长，决策越模糊" />
              <ProblemCard label="进展" value="状态靠手动回忆" note="关键安排容易遗漏" />
            </div>
            <div className="mt-5 grid gap-3 rounded-2xl border border-black/[0.08] bg-[#f7f7f5] p-4 text-center dark:border-white/10 dark:bg-white/[0.04] sm:grid-cols-4">
              <ResearchStat value="19" label="公开求职记录" />
              <ResearchStat value="6" label="主要竞品" />
              <ResearchStat value="4" label="行为角色" />
              <ResearchStat value="26" label="预设结果检查" />
            </div>
            <div className="mt-8 border-l-2 border-[#6366f1] pl-5"><p className="text-xs font-medium text-black/40 dark:text-white/40">核心产品问题</p><p className="mt-2 text-lg font-medium leading-7">如何让求职者在不增加维护负担的前提下，始终知道“这是什么机会、现在在哪里、接下来做什么”？</p></div>
          </div>
        </div>
      </section>

      <section className="px-5 py-20 md:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-8 lg:grid-cols-[.7fr_1.3fr]"><div><p className="text-xs font-medium text-[#6366f1]">02 · PRODUCT MODEL</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-4xl">用一条状态轨迹，<br />连接所有功能。</h2></div><p className="max-w-2xl text-base leading-7 text-black/55 dark:text-white/55">导航、数据模型和界面叙事共享同一主线。采集不再占据一级任务，AI 也不直接替用户做决定；它们都服务于核心的求职推进。</p></div>
          <div className="mt-12 overflow-x-auto rounded-2xl border border-black/[0.08] bg-white px-6 py-10 dark:border-white/10 dark:bg-[#111113]">
            <div className="relative mx-auto flex min-w-[760px] max-w-5xl items-start justify-between">
              <div className="absolute left-[6%] right-[6%] top-5 h-px bg-[#6366f1]" />
              {["发现岗位", "收藏 / 待投递", "创建投递", "更新状态", "近期安排", "看板复盘"].map((step, index) => <div key={step} className="relative z-10 w-28 text-center"><span className="mx-auto grid h-10 w-10 place-items-center rounded-full border-4 border-white bg-[#6366f1] text-xs font-semibold text-white dark:border-[#111113]">{index + 1}</span><p className="mt-3 text-xs font-medium">{step}</p></div>)}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-[#111113] px-5 py-20 text-white md:py-28">
        <div className="mx-auto max-w-6xl">
          <p className="text-xs font-medium text-[#a5b4fc]">03 · KEY DECISIONS</p>
          <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-[-0.035em] md:text-5xl">四个决定，定义产品边界。</h2>
          <div className="mt-14 divide-y divide-white/10 border-y border-white/10">
            {DECISIONS.map((decision) => <article key={decision.index} className="grid gap-4 py-8 md:grid-cols-[4rem_.8fr_1.2fr] md:gap-8"><span className="text-xs font-medium text-[#a5b4fc]">{decision.index}</span><h3 className="text-lg font-semibold leading-7">{decision.title}</h3><p className="text-sm leading-7 text-white/55">{decision.body}</p></article>)}
          </div>
        </div>
      </section>

      <section className="border-b border-black/[0.07] bg-white px-5 py-20 dark:border-white/10 dark:bg-[#111113] md:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-12 lg:grid-cols-[.7fr_1.3fr]">
            <div>
              <p className="text-xs font-medium text-[#6366f1]">04 · VALIDATE & ITERATE</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-4xl">不是证明方案正确，<br />而是主动寻找断点。</h2>
              <p className="mt-5 max-w-md text-sm leading-7 text-black/55 dark:text-white/55">首次专家模拟走查保留原始基线，不倒推改写。两个破坏主线的问题进入优先修复，其余能力继续留在边界清单。</p>
            </div>
            <div>
              <div className="grid gap-3 sm:grid-cols-2">
                <IterationCard
                  label="修复前"
                  core="核心 18 / 23"
                  boundary="边界 0 / 3"
                  note="通知时间没有进入待办；库外投递无法统一管理"
                />
                <IterationCard
                  label="修复后"
                  core="核心 19 / 23"
                  boundary="边界 1 / 3"
                  note="两项断点均关闭；全矩阵达到 20 / 26"
                  active
                />
              </div>
              <div className="mt-5 grid gap-4">
                <figure className="overflow-hidden rounded-2xl border border-black/[0.08] bg-[#f7f7f5] dark:border-white/10 dark:bg-white/[0.04]">
                  <Image src="/media/case-study/post-fix-schedule.png" alt="通知中的面试时间进入近期安排" width={1440} height={1000} className="aspect-[1.44/1] w-full object-cover object-top" />
                  <figcaption className="px-4 py-3 text-xs leading-5 text-black/50 dark:text-white/50">通知解析后仍需人工确认；确认一次，同时更新状态、时间线和近期安排。</figcaption>
                </figure>
                <figure className="overflow-hidden rounded-2xl border border-black/[0.08] bg-[#f7f7f5] dark:border-white/10 dark:bg-white/[0.04]">
                  <Image src="/media/case-study/post-fix-manual-application.png" alt="岗位库外投递补录后的详情与时间线" width={1440} height={1000} className="aspect-[1.44/1] w-full object-cover object-top" />
                  <figcaption className="px-4 py-3 text-xs leading-5 text-black/50 dark:text-white/50">公司和岗位为必填，其他字段可选；一次提交建立岗位、投递和初始时间线。</figcaption>
                </figure>
              </div>
              <p className="mt-4 text-xs leading-6 text-black/40 dark:text-white/40">19/23 与 20/26 是专家模拟走查的结果覆盖，不是用户任务完成率。尚未满足的能力包括实习硬条件、真实通知、细分转化、历史导入和未知通知自动建档。</p>
            </div>
          </div>
        </div>
      </section>

      <section className="px-5 py-20 md:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-12 lg:grid-cols-[.7fr_1.3fr]">
            <div><p className="text-xs font-medium text-[#6366f1]">05 · BUILD & EVIDENCE</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-4xl">验证的是产品判断，<br />不是虚构增长。</h2></div>
            <div>
              <div className="grid gap-3 sm:grid-cols-3"><Evidence value="19" label="公开求职记录编码" /><Evidence value="26" label="完整预设结果检查" /><Evidence value="2/2" label="核心断点完成关闭" /></div>
              <div className="mt-8 rounded-2xl border border-black/[0.08] bg-white p-5 dark:border-white/10 dark:bg-[#111113]">
                <h3 className="flex items-center gap-2 text-sm font-semibold"><ShieldCheck className="h-4 w-4 text-emerald-600" />证据边界</h3>
                <p className="mt-2 text-sm leading-7 text-black/55 dark:text-white/55">当前证据证明产品问题可以被发现、排序、修复和复测，并有 120 项后端测试与 14 条前端路由生产构建作为交付保障；不证明留存、付费意愿或求职成功率。</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-black/[0.07] bg-white px-5 py-20 dark:border-white/10 dark:bg-[#111113] md:py-28">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[1fr_1fr]">
          <div><p className="text-xs font-medium text-[#6366f1]">06 · NEXT</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-5xl">从专家走查，走向真人验证。</h2><p className="mt-5 max-w-xl text-sm leading-7 text-black/55 dark:text-white/55">未来计划不会阻塞当前 Demo。只有真实使用暴露出持续价值后，才进入账号同步、通知、数据托管与商业化。</p></div>
          <ol className="space-y-3">
            {["完成 3 次探索性访谈与 5 人任务测试", "以最小 CSV 模板验证历史迁移门槛", "验证真实通知渠道，再决定是否建设推送", "积累真实事件数据后再做细分转化分析"].map((item, index) => <li key={item} className="flex min-h-16 items-center gap-4 rounded-xl border border-black/[0.08] bg-[#f7f7f5] px-4 dark:border-white/10 dark:bg-white/[0.04]"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#eef2ff] text-xs font-semibold text-[#4f46e5] dark:bg-indigo-950 dark:text-indigo-300">{index + 1}</span><span className="text-sm">{item}</span></li>)}
          </ol>
        </div>
      </section>

      <section className="px-5 py-20 text-center md:py-28"><Activity className="mx-auto h-6 w-6 text-[#6366f1]" /><h2 className="mx-auto mt-5 max-w-2xl text-3xl font-semibold tracking-[-0.035em] md:text-5xl">看案例，也操作真实产品。</h2><div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row"><Link href="/dashboard" className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#171719] px-6 text-sm font-medium text-white dark:bg-white dark:text-black">打开完整 Demo <ArrowRight className="h-4 w-4" /></Link><Link href="/" className="inline-flex min-h-12 items-center justify-center rounded-lg border border-black/10 bg-white px-6 text-sm font-medium dark:border-white/10 dark:bg-white/[0.04]">返回产品官网</Link></div></section>
    </main>
  );
}

function CaseMeta({ label, value }: { label: string; value: string }) { return <div><dt className="text-[10px] uppercase tracking-[0.12em] text-black/35 dark:text-white/35">{label}</dt><dd className="mt-1.5 font-medium leading-5">{value}</dd></div>; }
function ProblemCard({ label, value, note }: { label: string; value: string; note: string }) { return <div className="rounded-xl border border-black/[0.08] bg-[#f7f7f5] p-4 dark:border-white/10 dark:bg-white/[0.04]"><p className="text-[10px] font-medium text-[#6366f1]">{label}</p><p className="mt-3 text-sm font-semibold">{value}</p><p className="mt-1 text-xs text-black/40 dark:text-white/40">{note}</p></div>; }
function Evidence({ value, label }: { value: string; label: string }) { return <div className="rounded-xl bg-[#171719] p-5 text-white"><p className="text-3xl font-semibold tabular-nums">{value}</p><p className="mt-2 text-[11px] leading-5 text-white/50">{label}</p></div>; }
function ResearchStat({ value, label }: { value: string; label: string }) { return <div><p className="text-xl font-semibold tabular-nums">{value}</p><p className="mt-1 text-[10px] text-black/40 dark:text-white/40">{label}</p></div>; }
function IterationCard({ label, core, boundary, note, active = false }: { label: string; core: string; boundary: string; note: string; active?: boolean }) { return <article className={`rounded-2xl border p-5 ${active ? "border-[#a5b4fc] bg-[#eef2ff] dark:border-indigo-700 dark:bg-indigo-950/50" : "border-black/[0.08] bg-[#f7f7f5] dark:border-white/10 dark:bg-white/[0.04]"}`}><p className="text-[10px] font-medium uppercase tracking-[0.12em] text-[#6366f1]">{label}</p><div className="mt-4 flex gap-4 text-sm font-semibold"><span>{core}</span><span>{boundary}</span></div><p className="mt-3 text-xs leading-6 text-black/50 dark:text-white/50">{note}</p></article>; }

function CaseFilmFallback() {
  return <div className="grid h-full place-items-center bg-[#f5f5f7] p-[8%] text-[#171719]"><div className="w-full max-w-2xl"><div className="mx-auto grid aspect-square w-[10%] place-items-center rounded-full bg-[#6366f1] text-white"><Play className="h-1/3 w-1/3 fill-current" /></div><p className="mt-[4%] text-center text-[clamp(10px,2vw,24px)] font-semibold">完整产品讲解</p><div className="mt-[7%] grid grid-cols-3 gap-[2%]">{[[CircleDot, "问题与主线"], [GitBranch, "关键决策"], [Check, "完整 Demo"]].map(([Icon, label]) => { const C = Icon as typeof CircleDot; return <div key={String(label)} className="rounded-lg border border-black/[0.08] bg-white p-[8%] text-center"><C className="mx-auto h-[1em] w-[1em] text-[#6366f1]" /><p className="mt-[8%] text-[clamp(5px,.85vw,11px)]">{String(label)}</p></div>; })}</div></div></div>;
}
