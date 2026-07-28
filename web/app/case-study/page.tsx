"use client";

import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Check,
  CircleDot,
  GitBranch,
  Play,
  ShieldCheck,
} from "lucide-react";

import { ProductFilm } from "@/components/marketing-v2/ProductFilm";

const SECTION_NAV = [
  ["context", "问题"],
  ["research", "研究"],
  ["needs", "需求"],
  ["users", "用户"],
  ["scope", "范围"],
  ["solution", "方案"],
  ["interface", "设计"],
  ["validation", "验证"],
  ["results", "结果"],
] as const;

const RESEARCH_QUESTIONS = [
  "用户为什么开始记录投递，又为什么停止维护？",
  "Excel、Notion、飞书等替代方案在哪些环节失效？",
  "高频投递、定向求职和复盘再投的任务有什么不同？",
  "岗位聚合与进度维护，哪一个更值得优先验证？",
  "哪些缺口会破坏核心闭环，而不只是少一个功能？",
];

const EVIDENCE_THEMES = [
  {
    theme: "手工台账",
    strength: "较强",
    evidence: "用户主动使用 Excel、Notion、飞书或公开帖子记录进度。",
    decision: "把表格视为直接替代品，而不是假设用户没有工具。",
  },
  {
    theme: "维护中断",
    strength: "中等",
    evidence: "投递量增加后，记录会停止更新，渠道、日期与阶段开始混乱。",
    decision: "核心价值从“能记录”改为“更低成本地持续维护”。",
  },
  {
    theme: "日程遗漏",
    strength: "较强",
    evidence: "笔试、面试、电话和截止时间存在遗漏或冲突风险。",
    decision: "下一步安排进入核心闭环，不只保留历史状态。",
  },
  {
    theme: "跨渠道分散",
    strength: "中等",
    evidence: "岗位来自官网、社区、群聊和招聘平台，信息需要重复整理。",
    decision: "聚合作为入口，但不把岗位数量作为唯一价值。",
  },
  {
    theme: "无反馈跟进",
    strength: "中等",
    evidence: "长时间无回复使当前状态模糊，也让看板长期失真。",
    decision: "设计“无回应关闭”，由系统建议、用户确认。",
  },
  {
    theme: "复杂复盘",
    strength: "部分",
    evidence: "少量用户会统计阶段数据，但不足以证明复杂看板是普遍需求。",
    decision: "只保留基础累计漏斗，细分策略分析延后验证。",
  },
];

const COMPETITORS = [
  {
    name: "牛客",
    type: "校招社区",
    discovery: "浅",
    tracking: "无",
    timeline: "无",
    dashboard: "无",
    insight: "用户用“投递记录帖”绕过平台追踪缺口",
  },
  {
    name: "实习僧",
    type: "实习招聘",
    discovery: "浅",
    tracking: "无",
    timeline: "无",
    dashboard: "无",
    insight: "岗位发现较强，投递后的过程管理较弱",
  },
  {
    name: "看准",
    type: "公司信息",
    discovery: "浅",
    tracking: "无",
    timeline: "无",
    dashboard: "无",
    insight: "强在公司认知，招聘流程并非产品主线",
  },
  {
    name: "超级简历",
    type: "求职工具",
    discovery: "无",
    tracking: "浅",
    timeline: "无",
    dashboard: "浅",
    insight: "已有静态标记，但缺少事件和下一步",
  },
  {
    name: "LinkedIn",
    type: "海外标杆",
    discovery: "强",
    tracking: "强",
    timeline: "强",
    dashboard: "强",
    insight: "证明追踪模式成立，但本土学生场景较弱",
  },
  {
    name: "BOSS",
    type: "综合招聘",
    discovery: "强",
    tracking: "浅",
    timeline: "无",
    dashboard: "无",
    insight: "进展散落在聊天里，难以结构化复盘",
  },
] as const;

const DEMAND_MAP = [
  {
    evidence: "投递增加后，表格在第二周停止更新",
    problem: "记录本身成为第二份工作",
    story: "收到通知时，用最低成本更新对应岗位",
    response: "文本解析 + 人工确认",
    priority: "P0",
  },
  {
    evidence: "面试时间散落在邮件、微信和日历",
    problem: "状态更新后仍不知道下一步",
    story: "统一查看近期笔试、面试与材料安排",
    response: "计划事件 + 近期安排",
    priority: "P0",
  },
  {
    evidence: "收藏很多岗位，但没有形成行动",
    problem: "兴趣与投递承诺混在一起",
    story: "区分想保留与准备投递的机会",
    response: "收藏 / 待投递分离",
    priority: "P0",
  },
  {
    evidence: "表格只留下当前状态，历史过程丢失",
    problem: "无法复盘，也无法可靠纠错",
    story: "查看每一次状态变化和发生时间",
    response: "事件时间线",
    priority: "P0",
  },
  {
    evidence: "只有少量用户主动统计转化数据",
    problem: "复杂看板价值证据不足",
    story: "先看整体到达阶段，不做策略诊断",
    response: "基础累计漏斗",
    priority: "P1",
  },
];

const BEHAVIOR_ROLES = [
  {
    code: "P1",
    title: "高频跨平台维护者",
    scope: "核心角色",
    definition: "近一个月使用 3 个以上渠道、管理 20 个以上机会。",
    job: "用最低成本记录变化并看到下一步，避免错过机会。",
    fit: "高",
  },
  {
    code: "P2",
    title: "定向机会监控者",
    scope: "次要角色",
    definition: "只关注少量目标公司和明确岗位，投递量不高。",
    job: "尽快判断硬条件，先保留机会，再决定是否投递。",
    fit: "中",
  },
  {
    code: "P3",
    title: "复盘再投者",
    scope: "生命周期延伸",
    definition: "已经有一轮投递历史，准备开始下一轮求职。",
    job: "回看阶段轨迹和有效进展，判断下一步怎么调整。",
    fit: "中高",
  },
  {
    code: "P4",
    title: "低维护意愿者",
    scope: "边界角色",
    definition: "只在进入面试后记录，或完全不愿维护台账。",
    job: "真正需要处理时只保存最少信息，不迁移完整历史。",
    fit: "低",
  },
];

const PRIORITY_LANES = [
  {
    label: "P0 · 核心闭环",
    description: "缺少后，“发现—投递—下一步”无法成立。",
    items: ["岗位数据", "收藏 / 待投递", "投递状态", "低成本更新", "近期安排", "历史事件"],
  },
  {
    label: "P1 · 增强价值",
    description: "能够增强判断与复盘，但不应阻塞主线。",
    items: ["基础看板", "岗位订阅", "硬条件筛选", "投递元信息", "有效进展趋势"],
  },
  {
    label: "P2 · 等待证据",
    description: "只有真实使用产生足够数据后再判断。",
    items: ["细分转化", "复杂策略建议", "跨周期对比", "多人协作"],
  },
  {
    label: "OUT · 主动不做",
    description: "不直接验证“降低维护成本”的能力。",
    items: ["简历生成", "社区内容", "自动投递", "支付", "原生 App"],
  },
];

const OUTPUT_CHAIN = [
  ["01", "研究输入", "公开行为证据、竞品事实"],
  ["02", "问题定义", "主题编码、证据强度、机会判断"],
  ["03", "需求产出", "14 类痛点、20 条 Job Stories"],
  ["04", "范围产出", "行为角色、P0/P1/P2、IN/OUT"],
  ["05", "方案产出", "IA、用户流程、状态机、事件模型"],
  ["06", "交付产出", "PRD、界面、验收矩阵、公开 Demo"],
];

const DESIGN_PRINCIPLES = [
  {
    index: "01",
    title: "降低维护成本",
    evidence: "用户已经有表格，独立产品必须显著减少重复录入。",
    mechanism: "最少字段、文本辅助解析、一次确认写入多个下游。",
  },
  {
    index: "02",
    title: "区分不同意图",
    evidence: "收藏表达兴趣，待投递表达行动准备，两者不能互相覆盖。",
    mechanism: "收藏与待投递独立存在，创建投递后只结束待投递。",
  },
  {
    index: "03",
    title: "保留过程证据",
    evidence: "只覆盖当前状态会丢失多轮面试、纠错和复盘依据。",
    mechanism: "当前状态负责查询，事件时间线负责历史。",
  },
  {
    index: "04",
    title: "让下一步自然生成",
    evidence: "用户真正需要的不只是“发生过什么”，还有“接下来做什么”。",
    mechanism: "带时间的计划事件进入近期安排，并与详情共享。",
  },
  {
    index: "05",
    title: "关键决定由人确认",
    evidence: "通知文本有歧义，AI 误判会直接污染求职记录。",
    mechanism: "AI 提取与建议、规则降级、置信度、人工确认。",
  },
];

const STATE_MODEL = [
  ["applied", "已投递", "active"],
  ["test", "测评 / 笔试", "active"],
  ["interviewing", "面试中", "active"],
  ["offer_pending", "Offer 待决定", "active"],
  ["accepted", "Offer 已接受", "terminal"],
  ["declined", "Offer 已婉拒", "terminal"],
  ["rejected", "公司拒绝", "terminal"],
  ["no_response", "无回应关闭", "terminal"],
  ["withdrawn", "主动撤回", "terminal"],
] as const;

const INTERFACE_CASES = [
  {
    title: "01 · 发现岗位",
    image: "/media/case-study/job-detail-evidence.png",
    width: 1440,
    height: 1000,
    alt: "岗位发现页面展示关键词、公司、地点与岗位来源",
    problem: "跨平台岗位信息重复，用户需要先判断来源和有效性。",
    decision: "把来源、更新时间和行动入口放在同一浏览层级。",
    boundary: "演示快照不等于官方岗位仍在招聘，页面保留来源边界。",
  },
  {
    title: "02 · 形成意向",
    image: "/media/case-study/mobile-saved-evidence.png",
    width: 390,
    height: 844,
    alt: "移动端收藏与待投递页面",
    problem: "收藏不等于准备投递，混在一起会让机会列表失去行动意义。",
    decision: "两种意图独立存在，并在移动端保持同样的操作语义。",
    boundary: "是否理解两个概念仍需真人任务测试。",
    portrait: true,
  },
  {
    title: "03 · 推进投递",
    image: "/media/case-study/application-timeline-evidence.png",
    width: 1440,
    height: 1000,
    alt: "投递详情页面展示状态与事件时间线",
    problem: "静态状态无法解释发生过什么，也无法支持纠错。",
    decision: "当前值与历史事件分离，状态变化同时写入时间线。",
    boundary: "AI 只提供建议，用户确认后才改变业务数据。",
  },
  {
    title: "04 · 回看进展",
    image: "/media/case-study/dashboard-evidence.png",
    width: 1440,
    height: 1000,
    alt: "求职看板展示累计漏斗与近期安排",
    problem: "只看投递数量会鼓励无效海投，也无法说明真正到达的阶段。",
    decision: "看板读取累计到达事件，并突出近期安排和有效进展。",
    boundary: "小样本不输出细分策略建议。",
  },
];

const UNPROVEN = [
  "真实用户是否理解“收藏”与“待投递”的差异",
  "相比表格或招聘平台，是否真的降低持续维护负担",
  "用户能否连续 7 天维护投递，并主动回来查看下一步",
  "产品价值是否足以支持留存、付费或更高求职成功率",
];

export default function CaseStudyPage() {
  const reduceMotion = useReducedMotion();

  return (
    <main className="bg-[#f7f7f5] text-[#171719] dark:bg-[#0d0d0f] dark:text-white">
      <nav className="sticky top-0 z-40 border-b border-black/[0.07] bg-[#f7f7f5]/92 backdrop-blur-xl dark:border-white/10 dark:bg-[#0d0d0f]/90">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <Link
            href="/"
            className="inline-flex min-h-11 items-center gap-2 text-xs font-medium text-black/55 transition-colors hover:text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] dark:text-white/55 dark:hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            返回 JobPulse 官网
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[#171719] px-4 text-xs font-medium text-white transition-transform active:scale-[0.98] dark:bg-white dark:text-black"
          >
            打开产品 Demo
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </nav>

      <section className="px-5 pb-16 pt-20 md:pb-24 md:pt-28">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55 }}
            className="grid gap-10 lg:grid-cols-[1.35fr_.65fr] lg:items-end"
          >
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-[#6366f1]">
                Product design case study · 2026
              </p>
              <h1 className="mt-5 max-w-4xl text-balance text-[clamp(2.8rem,7vw,5.4rem)] font-semibold leading-[0.96] tracking-[-0.055em]">
                从公开行为证据，到一条可管理的求职主线。
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-7 text-black/55 dark:text-white/55">
                这不是一张功能展示页，而是一份完整的产品设计记录：我如何研究需求、定位用户、控制范围、建立产品模型，并用走查结果推动方案迭代。
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-5 border-t border-black/10 pt-5 text-xs dark:border-white/10 lg:grid-cols-1">
              <CaseMeta label="角色" value="产品经理（个人项目，AI 辅助开发）" />
              <CaseMeta label="周期" value="2026.06—2026.07" />
              <CaseMeta label="负责" value="研究、需求、规划、UX/UI、验收" />
              <CaseMeta label="交付" value="公开可体验 Web MVP" />
            </dl>
          </motion.div>

          <div className="mt-12 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {[
              ["19", "公开记录"],
              ["06", "竞品走查"],
              ["14", "痛点类型"],
              ["20", "Job Stories"],
              ["04", "行为角色"],
              ["26", "结果检查"],
            ].map(([value, label]) => (
              <div key={label} className="border-t border-black/10 pt-3 dark:border-white/10">
                <p className="font-mono text-2xl font-semibold tracking-[-0.04em]">{value}</p>
                <p className="mt-1 text-[10px] text-black/40 dark:text-white/40">{label}</p>
              </div>
            ))}
          </div>

          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.12 }}
            className="mt-12 rounded-2xl border border-black/10 bg-[#111113] p-2 dark:border-white/15"
          >
            <div className="flex h-9 items-center gap-1.5 px-3">
              <span className="h-2 w-2 rounded-full bg-white/25" />
              <span className="h-2 w-2 rounded-full bg-white/15" />
              <span className="h-2 w-2 rounded-full bg-white/10" />
              <span className="ml-3 text-[9px] text-white/35">当前产品演示 · 约 75 秒</span>
            </div>
            <ProductFilm
              src="/media/case-study-demo.webm"
              label="JobPulse 完整产品案例演示"
              className="aspect-video rounded-xl"
            >
              <CaseFilmFallback />
            </ProductFilm>
          </motion.div>

          <div className="mt-5 flex items-start gap-3 rounded-xl border border-black/[0.08] bg-white px-4 py-3 text-xs leading-6 text-black/50 dark:border-white/10 dark:bg-white/[0.04] dark:text-white/50">
            <ShieldCheck className="mt-1 h-4 w-4 shrink-0 text-emerald-600" />
            <p>
              证据边界：研究来自可追溯的公开记录与竞品事实，验证来自预设任务的专家模拟走查；不是用户访谈、真人可用性测试，也不代表留存、付费或求职成功率。
            </p>
          </div>
        </div>
      </section>

      <div className="sticky top-16 z-30 border-y border-black/[0.07] bg-white/94 backdrop-blur-xl dark:border-white/10 dark:bg-[#111113]/94">
        <div className="no-scrollbar mx-auto flex max-w-6xl gap-6 overflow-x-auto px-5">
          {SECTION_NAV.map(([href, label], index) => (
            <a
              key={href}
              href={`#${href}`}
              className="inline-flex min-h-12 shrink-0 items-center gap-2 border-b-2 border-transparent text-[11px] text-black/45 transition-colors hover:border-[#6366f1] hover:text-black dark:text-white/45 dark:hover:text-white"
            >
              <span className="font-mono text-[9px] text-[#6366f1]">{String(index + 1).padStart(2, "0")}</span>
              {label}
            </a>
          ))}
        </div>
      </div>

      <section id="context" className="scroll-mt-28 border-b border-black/[0.07] bg-white px-5 py-20 dark:border-white/10 dark:bg-[#111113] md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="01 · CONTEXT"
            title={
              <>
                先修正方向，
                <br />
                再讨论功能。
              </>
            }
            copy="项目最初来自自己的跨平台求职场景，但个人感受只能形成假设。研究之后，我把方向从“聚合更多岗位”收敛为“降低进度维护成本”。"
          />

          <div className="mt-12 grid gap-5 lg:grid-cols-[.9fr_1.1fr]">
            <div className="rounded-2xl bg-[#171719] p-6 text-white md:p-8">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/35">Direction shift</p>
              <div className="mt-8">
                <p className="text-xs text-white/35">最初假设</p>
                <p className="mt-2 text-2xl font-semibold tracking-[-0.03em]">用户缺少统一的岗位入口</p>
              </div>
              <div className="my-7 flex items-center gap-3">
                <div className="h-px flex-1 bg-white/10" />
                <ArrowDown className="h-4 w-4 text-[#a5b4fc]" />
                <div className="h-px flex-1 bg-white/10" />
              </div>
              <div>
                <p className="text-xs text-[#a5b4fc]">研究后的核心问题</p>
                <p className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
                  用户已有工具，但难以持续维护
                </p>
                <p className="mt-4 text-sm leading-7 text-white/55">
                  如果只是换一个地方继续手填，产品不会比表格更有迁移价值。
                </p>
              </div>
            </div>

            <div className="grid gap-px overflow-hidden rounded-2xl border border-black/[0.08] bg-black/[0.08] dark:border-white/10 dark:bg-white/10 sm:grid-cols-2">
              {[
                ["问题", "信息分散只是表象，真正的风险是上下文、安排和历史不断丢失。"],
                ["目标", "让求职者始终知道：这是什么机会、现在在哪里、接下来做什么。"],
                ["约束", "个人项目、无正式团队、无真人研究数据，不包装协作和增长。"],
                ["判断", "缺少真实用户证据前，先验证产品闭环与交付质量。"],
              ].map(([label, text]) => (
                <article key={label} className="bg-white p-5 dark:bg-[#111113]">
                  <p className="text-[10px] font-medium text-[#6366f1]">{label}</p>
                  <p className="mt-4 text-sm leading-7 text-black/60 dark:text-white/60">{text}</p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="research" className="scroll-mt-28 px-5 py-20 md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="02 · RESEARCH DESIGN"
            title={
              <>
                先定义研究问题，
                <br />
                再寻找支持与反例。
              </>
            }
            copy="我没有把公开帖子当成访谈，而是把它们作为行为证据：记录用户做过什么、用了什么工具、在哪里中断、造成什么后果，以及证据强弱。"
          />

          <figure className="mt-12 overflow-hidden rounded-[1.5rem] border border-black/[0.08] bg-[#efe8dc] dark:border-white/10">
            <Image
              src="/media/case-study/research-fragment-to-flow.png"
              alt="概念插画：分散的岗位、表格、邮件和日历汇入统一的求职时间线"
              width={1536}
              height={1024}
              className="aspect-[1.85/1] w-full object-cover"
              priority
            />
            <figcaption className="flex flex-col gap-2 border-t border-black/[0.07] bg-white px-5 py-4 text-xs text-black/45 dark:border-white/10 dark:bg-[#111113] dark:text-white/45 sm:flex-row sm:items-center sm:justify-between">
              <span>研究情境概念图：从分散记录到统一推进主线</span>
              <span className="text-[10px]">原创插画 · 非研究参与者照片</span>
            </figcaption>
          </figure>

          <div className="mt-8 grid gap-5 lg:grid-cols-[.85fr_1.15fr]">
            <div className="rounded-2xl border border-black/[0.08] bg-white p-6 dark:border-white/10 dark:bg-[#111113]">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-[#6366f1]">Research questions</p>
              <ol className="mt-6 space-y-4">
                {RESEARCH_QUESTIONS.map((question, index) => (
                  <li key={question} className="grid grid-cols-[2rem_1fr] gap-3 text-sm leading-6">
                    <span className="font-mono text-[10px] text-black/30 dark:text-white/30">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span>{question}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <ResearchMethod value="12" label="国内公开记录" note="8 条第一人称经历，4 条经验复盘 / 社区观察" />
              <ResearchMethod value="07" label="海外补充记录" note="用于寻找跨市场重复模式，不合并计算比例" />
              <ResearchMethod value="06" label="竞品与替代品" note="招聘平台、简历工具、海外标杆与表格" />
              <ResearchMethod value="07" label="编码字段" note="情境、工具、触发、后果、补救、反例、强度" />
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-black/[0.08] bg-white p-5 dark:border-white/10 dark:bg-[#111113]">
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ["A · 直接证据", "产品、代码、数据、验收记录，可以复核。"],
                ["B · 外部证据", "公开行为和竞品事实，证明现象存在。"],
                ["C · 待验证", "产品推断、目标和计划，不能写成结果。"],
              ].map(([label, text]) => (
                <div key={label} className="border-l border-black/10 pl-4 first:border-l-0 first:pl-0 dark:border-white/10">
                  <p className="text-xs font-semibold">{label}</p>
                  <p className="mt-2 text-[11px] leading-5 text-black/45 dark:text-white/45">{text}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-12">
            <SubsectionHeader
              index="02.1"
              title="编码结果不是痛点列表，而是证据强度与产品动作的对应。"
              copy="同样是“用户想要”，有些能从行为中观察到，有些仍只是假设。"
            />
            <div className="mt-6 overflow-hidden rounded-2xl border border-black/[0.08] bg-white dark:border-white/10 dark:bg-[#111113]">
              {EVIDENCE_THEMES.map((item) => (
                <article
                  key={item.theme}
                  className="grid gap-4 border-b border-black/[0.07] px-5 py-5 last:border-b-0 dark:border-white/10 md:grid-cols-[.45fr_.35fr_1.1fr_1.1fr]"
                >
                  <div>
                    <p className="text-[10px] text-black/30 dark:text-white/30">主题</p>
                    <p className="mt-1 text-sm font-semibold">{item.theme}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-black/30 dark:text-white/30">强度</p>
                    <span className="mt-1 inline-block border-b border-[#6366f1] text-xs font-medium">{item.strength}</span>
                  </div>
                  <div>
                    <p className="text-[10px] text-black/30 dark:text-white/30">可观察证据</p>
                    <p className="mt-1 text-xs leading-6 text-black/55 dark:text-white/55">{item.evidence}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[#6366f1]">产品动作</p>
                    <p className="mt-1 text-xs font-medium leading-6">{item.decision}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="mt-16">
            <SubsectionHeader
              index="02.2"
              title="竞品分析修正了“市场上没有投递管理”的过度判断。"
              copy="差异不在“有或没有”，而在静态标记与动态状态系统的深度。"
            />

            <div className="mt-6 overflow-x-auto rounded-2xl border border-black/[0.08] bg-white dark:border-white/10 dark:bg-[#111113]">
              <div className="min-w-[900px]">
                <div className="grid grid-cols-[1fr_.7fr_.65fr_.65fr_.65fr_1.55fr] border-b border-black/[0.07] px-5 py-3 text-[10px] font-medium text-black/35 dark:border-white/10 dark:text-white/35">
                  <span>产品 / 类型</span>
                  <span>岗位发现</span>
                  <span>进度管理</span>
                  <span>事件时间线</span>
                  <span>数据看板</span>
                  <span>关键观察</span>
                </div>
                {COMPETITORS.map((item) => (
                  <div
                    key={item.name}
                    className="grid grid-cols-[1fr_.7fr_.65fr_.65fr_.65fr_1.55fr] items-center border-b border-black/[0.07] px-5 py-4 text-xs last:border-b-0 dark:border-white/10"
                  >
                    <div>
                      <p className="font-semibold">{item.name}</p>
                      <p className="mt-1 text-[10px] text-black/35 dark:text-white/35">{item.type}</p>
                    </div>
                    <MatrixValue value={item.discovery} />
                    <MatrixValue value={item.tracking} />
                    <MatrixValue value={item.timeline} />
                    <MatrixValue value={item.dashboard} />
                    <p className="leading-5 text-black/50 dark:text-white/50">{item.insight}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
              <ComparisonCard label="招聘平台" title="擅长发现岗位" note="跨平台后的统一管理较弱" />
              <ArrowConnector />
              <ComparisonCard label="表格 / Notion" title="灵活且已被掌握" note="维护、同步和提醒依赖手工" />
              <ArrowConnector />
              <ComparisonCard label="JobPulse 机会" title="围绕进度推进" note="状态事件自然生成待办与复盘" accent />
            </div>
          </div>
        </div>
      </section>

      <section id="needs" className="scroll-mt-28 border-y border-black/[0.07] bg-white px-5 py-20 dark:border-white/10 dark:bg-[#111113] md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="03 · NEED ANALYSIS"
            title={
              <>
                把行为证据，
                <br />
                转译成可验收的需求。
              </>
            }
            copy="我没有直接从痛点跳到功能，而是先聚类问题，再使用 Job Stories 描述触发情境、用户任务和期望结果，最后建立需求到验证方式的映射。"
          />

          <div className="mt-12 overflow-x-auto pb-2">
            <div className="grid min-w-[860px] grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr_auto_1fr] items-center gap-3">
              {[
                ["19", "公开记录"],
                ["06", "行为主题"],
                ["14", "痛点类型"],
                ["20", "Job Stories"],
                ["P0", "首版范围"],
              ].map(([value, label], index, array) => (
                <div key={label} className="contents">
                  <div className="rounded-2xl bg-[#f7f7f5] p-5 text-center dark:bg-white/[0.04]">
                    <p className="font-mono text-3xl font-semibold tracking-[-0.05em] text-[#4f46e5] dark:text-indigo-300">
                      {value}
                    </p>
                    <p className="mt-2 text-xs">{label}</p>
                  </div>
                  {index < array.length - 1 ? <ArrowRight className="h-4 w-4 text-black/20 dark:text-white/20" /> : null}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8 space-y-3">
            {DEMAND_MAP.map((item, index) => (
              <article
                key={item.evidence}
                className="grid gap-5 rounded-2xl border border-black/[0.08] bg-[#f7f7f5] p-5 dark:border-white/10 dark:bg-white/[0.04] md:grid-cols-[2.2rem_1fr_1fr_1fr_.8fr]"
              >
                <span className="font-mono text-[10px] text-[#6366f1]">{String(index + 1).padStart(2, "0")}</span>
                <DemandCell label="行为证据" value={item.evidence} />
                <DemandCell label="问题定义" value={item.problem} />
                <DemandCell label="Job Story" value={item.story} />
                <div>
                  <p className="text-[9px] uppercase tracking-[0.12em] text-[#6366f1]">{item.priority} · 设计回应</p>
                  <p className="mt-2 text-xs font-semibold leading-5">{item.response}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-[.8fr_1.2fr]">
            <blockquote className="rounded-2xl bg-[#171719] p-6 text-white">
              <p className="text-[10px] uppercase tracking-[0.14em] text-[#a5b4fc]">Job Story template</p>
              <p className="mt-6 text-lg font-medium leading-8">
                当我收到一封笔试或面试通知时，我想用最低成本把进展记录到对应岗位，以便不用重新翻找和手填。
              </p>
              <p className="mt-5 text-xs leading-6 text-white/45">
                情境说明何时发生，任务说明用户要完成什么，结果说明为什么值得解决。
              </p>
            </blockquote>
            <div className="rounded-2xl border border-black/[0.08] bg-[#f7f7f5] p-6 dark:border-white/10 dark:bg-white/[0.04]">
              <p className="text-[10px] uppercase tracking-[0.14em] text-[#6366f1]">没有进入首版的需求</p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {[
                  ["复杂细分漏斗", "证据不足，小样本容易制造错误结论"],
                  ["实时首发通知", "当前采集能力无法可靠承诺时效"],
                  ["自动投递", "不服务降低维护成本的核心假设"],
                  ["个性化推荐", "缺少真实行为数据，不先做算法包装"],
                ].map(([title, note]) => (
                  <div key={title} className="border-l border-black/10 pl-4 dark:border-white/10">
                    <p className="text-sm font-semibold">{title}</p>
                    <p className="mt-1 text-[11px] leading-5 text-black/45 dark:text-white/45">{note}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="users" className="scroll-mt-28 px-5 py-20 md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="04 · USER POSITIONING"
            title={
              <>
                用行为复杂度定位用户，
                <br />
                不用人口属性制造画像。
              </>
            }
            copy="年龄、学校和城市只能帮助描述场景，不能决定需求强度。我用渠道数量、机会数量、维护意愿和求职阶段建立行为分群。"
          />

          <div className="mt-12 grid gap-5 lg:grid-cols-[1.08fr_.92fr]">
            <figure className="overflow-hidden rounded-[1.5rem] border border-black/[0.08] bg-[#efe8dc] dark:border-white/10">
              <Image
                src="/media/case-study/behavior-roles-concept.png"
                alt="概念插画：四类不同的求职记录行为模式"
                width={1536}
                height={1024}
                className="aspect-[1.2/1] w-full object-cover"
              />
              <figcaption className="flex justify-between gap-4 border-t border-black/[0.07] bg-white px-5 py-4 text-[10px] text-black/40 dark:border-white/10 dark:bg-[#111113] dark:text-white/40">
                <span>四类行为情境概念图</span>
                <span>非真人画像</span>
              </figcaption>
            </figure>

            <div className="relative grid min-h-[420px] grid-cols-2 grid-rows-2 gap-px overflow-hidden rounded-2xl border border-black/[0.08] bg-black/[0.08] p-8 pb-12 pl-12 dark:border-white/10 dark:bg-white/10">
              <span className="absolute bottom-3 left-1/2 -translate-x-1/2 text-[9px] text-black/35 dark:text-white/35">
                投递与渠道复杂度 →
              </span>
              <span className="absolute left-2 top-1/2 -translate-y-1/2 -rotate-90 text-[9px] text-black/35 dark:text-white/35">
                主动维护意愿 →
              </span>
              {[
                ["P2", "定向监控", "bg-[#f7f7f5] dark:bg-white/[0.04]"],
                ["P1", "高频维护", "bg-[#eef2ff] dark:bg-indigo-950/60"],
                ["P4", "低维护", "bg-[#ecece9] dark:bg-white/[0.03]"],
                ["P3", "复盘再投", "bg-[#f7f7f5] dark:bg-white/[0.04]"],
              ].map(([code, label, className]) => (
                <div key={code} className={`grid place-items-center p-4 text-center ${className}`}>
                  <div>
                    <p className="font-mono text-xl font-semibold text-[#4f46e5] dark:text-indigo-300">{code}</p>
                    <p className="mt-2 text-xs font-medium">{label}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {BEHAVIOR_ROLES.map((role) => (
              <article
                key={role.code}
                className="grid gap-4 rounded-2xl border border-black/[0.08] bg-white p-5 dark:border-white/10 dark:bg-[#111113] sm:grid-cols-[4rem_1fr]"
              >
                <span className="grid h-11 w-11 place-items-center rounded-full bg-[#171719] font-mono text-xs font-semibold text-white dark:bg-white dark:text-black">
                  {role.code}
                </span>
                <div>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-semibold">{role.title}</h3>
                    <span className="text-[9px] font-medium text-[#6366f1]">{role.scope} · 适配 {role.fit}</span>
                  </div>
                  <p className="mt-3 text-xs leading-6 text-black/50 dark:text-white/50">{role.definition}</p>
                  <p className="mt-2 text-xs font-medium leading-6">核心任务：{role.job}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="mt-6 border-l-2 border-[#6366f1] pl-5">
            <p className="text-xs font-medium text-black/40 dark:text-white/40">定位结论</p>
            <p className="mt-2 max-w-4xl text-lg font-medium leading-8">
              首版优先服务 P1，并用 P3 检查生命周期价值；P2 只覆盖发现与意向管理；P4 用来暴露迁移门槛，但不作为当前成功目标。
            </p>
          </div>
        </div>
      </section>

      <section id="scope" className="scroll-mt-28 bg-[#111113] px-5 py-20 text-white md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntroDark
            eyebrow="05 · OPPORTUNITY & SCOPE"
            title={
              <>
                用核心闭环控制范围，
                <br />
                而不是堆满功能。
              </>
            }
            copy="优先级不使用虚构的 RICE 分数，而是判断：是否服务核心用户、发生是否高频、缺失是否破坏闭环、证据是否足够、风险是否适合 MVP。"
          />

          <div className="mt-12 divide-y divide-white/10 border-y border-white/10">
            {PRIORITY_LANES.map((lane, index) => (
              <article key={lane.label} className="grid gap-5 py-7 md:grid-cols-[3rem_.8fr_1.2fr]">
                <span className="font-mono text-[10px] text-[#a5b4fc]">0{index + 1}</span>
                <div>
                  <h3 className="text-lg font-semibold">{lane.label}</h3>
                  <p className="mt-2 text-xs leading-6 text-white/45">{lane.description}</p>
                </div>
                <div className="flex flex-wrap content-start gap-2">
                  {lane.items.map((item) => (
                    <span key={item} className="border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/65">
                      {item}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>

          <div className="mt-14">
            <p className="text-[10px] uppercase tracking-[0.14em] text-[#a5b4fc]">Output chain</p>
            <div className="mt-6 overflow-x-auto">
              <div className="flex min-w-[900px] items-stretch gap-3">
                {OUTPUT_CHAIN.map(([index, title, output], itemIndex) => (
                  <div key={index} className="contents">
                    <div className="min-w-0 flex-1 border-t border-white/15 pt-4">
                      <p className="font-mono text-[9px] text-[#a5b4fc]">{index}</p>
                      <p className="mt-4 text-sm font-semibold">{title}</p>
                      <p className="mt-2 text-[10px] leading-5 text-white/40">{output}</p>
                    </div>
                    {itemIndex < OUTPUT_CHAIN.length - 1 ? (
                      <ArrowRight className="mt-16 h-4 w-4 shrink-0 text-white/20" />
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="solution" className="scroll-mt-28 px-5 py-20 md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="06 · SOLUTION DESIGN"
            title={
              <>
                让每个界面决定，
                <br />
                都能追溯到产品判断。
              </>
            }
            copy="方案不是从页面数量开始，而是从产品语义开始：机会、用户意图、投递阶段、历史事件和下一步安排分别表达什么。"
          />

          <div className="mt-12 divide-y divide-black/[0.08] border-y border-black/[0.08] dark:divide-white/10 dark:border-white/10">
            {DESIGN_PRINCIPLES.map((item) => (
              <article
                key={item.index}
                className="grid gap-5 py-7 md:grid-cols-[3rem_.75fr_1fr_1fr] md:gap-7"
              >
                <span className="font-mono text-[10px] text-[#6366f1]">{item.index}</span>
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <DemandCell label="依据" value={item.evidence} />
                <DemandCell label="产品机制" value={item.mechanism} accent />
              </article>
            ))}
          </div>

          <div className="mt-16">
            <SubsectionHeader
              index="06.1"
              title="信息架构按用户任务组织，而不是按技术模块组织。"
              copy="采集和 AI 都不是一级任务，它们服务于发现、行动、推进与复盘。"
            />
            <div className="mt-6 overflow-x-auto rounded-2xl border border-black/[0.08] bg-white px-6 py-10 dark:border-white/10 dark:bg-[#111113]">
              <div className="relative mx-auto flex min-w-[850px] max-w-5xl items-start justify-between">
                <div className="absolute left-[5%] right-[5%] top-5 h-px bg-[#6366f1]" />
                {[
                  ["发现", "岗位列表 / 详情"],
                  ["形成意向", "收藏 / 待投递"],
                  ["创建投递", "正式 / 外部补录"],
                  ["推进状态", "更新 / AI 建议"],
                  ["处理下一步", "笔试 / 面试 / 材料"],
                  ["回看进展", "时间线 / 看板"],
                ].map(([step, note], index) => (
                  <div key={step} className="relative z-10 w-32 text-center">
                    <span className="mx-auto grid h-10 w-10 place-items-center rounded-full border-4 border-white bg-[#6366f1] text-xs font-semibold text-white dark:border-[#111113]">
                      {index + 1}
                    </span>
                    <p className="mt-3 text-xs font-semibold">{step}</p>
                    <p className="mt-1 text-[9px] text-black/35 dark:text-white/35">{note}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-16">
            <SubsectionHeader
              index="06.2"
              title="三个状态维度必须分开，否则产品语义会互相污染。"
              copy="岗位是否有效、用户是否感兴趣、投递走到哪里，是三个不同的问题。"
            />
            <div className="mt-6 grid gap-4 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
              <ModelLayer
                index="01"
                label="岗位状态"
                title="岗位是否仍然有效"
                values={["展示中", "已关闭"]}
                note="属于岗位生命周期"
              />
              <ArrowConnector />
              <ModelLayer
                index="02"
                label="用户—岗位关系"
                title="用户当前是什么意图"
                values={["收藏", "待投递"]}
                note="可同时存在，不等于已投递"
              />
              <ArrowConnector />
              <ModelLayer
                index="03"
                label="投递状态"
                title="求职过程走到哪里"
                values={["进行中", "终态"]}
                note="进入九状态生命周期"
                accent
              />
            </div>
          </div>

          <div className="mt-16">
            <SubsectionHeader
              index="06.3"
              title="九状态描述生命周期，事件描述过程。"
              copy="当前状态用于查询；事件用于时间线、下一步、累计漏斗和纠错。"
            />
            <div className="mt-6 grid gap-5 lg:grid-cols-[1.05fr_.95fr]">
              <div className="rounded-2xl border border-black/[0.08] bg-white p-6 dark:border-white/10 dark:bg-[#111113]">
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.14em] text-[#6366f1]">9-state lifecycle</p>
                    <h3 className="mt-2 text-lg font-semibold">4 个进行中状态 + 5 个终态</h3>
                  </div>
                  <span className="font-mono text-4xl font-semibold text-black/10 dark:text-white/10">09</span>
                </div>
                <div className="mt-6 flex flex-wrap gap-2">
                  {STATE_MODEL.map(([code, label, type]) => (
                    <div
                      key={code}
                      className={`min-w-[8rem] flex-1 border px-3 py-3 ${
                        type === "active"
                          ? "border-[#c7d2fe] bg-[#eef2ff] dark:border-indigo-800 dark:bg-indigo-950/60"
                          : "border-black/[0.08] bg-[#f7f7f5] dark:border-white/10 dark:bg-white/[0.04]"
                      }`}
                    >
                      <p className="text-xs font-medium">{label}</p>
                      <p className="mt-1 font-mono text-[8px] text-black/30 dark:text-white/30">{code}</p>
                    </div>
                  ))}
                </div>
                <p className="mt-5 text-[10px] leading-5 text-black/40 dark:text-white/40">
                  多轮面试允许“面试中 → 面试中”；终态可通过纠错事件修正，但不直接覆盖历史。
                </p>
              </div>

              <div className="overflow-hidden rounded-2xl border border-black/[0.08] bg-white dark:border-white/10 dark:bg-[#111113]">
                {[
                  ["状态变化事件", "历史时间线", "保留每次变化与纠错原因"],
                  ["计划事件", "近期安排", "读取未完成且有 scheduled_at 的事件"],
                  ["阶段到达事件", "累计漏斗", "计算真正到达过的最高阶段"],
                  ["纠错事件", "审计记录", "修正错误但排除错误统计"],
                ].map(([source, output, note]) => (
                  <article
                    key={source}
                    className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 border-b border-black/[0.07] px-5 py-5 last:border-b-0 dark:border-white/10"
                  >
                    <div>
                      <p className="text-[9px] text-black/30 dark:text-white/30">事实来源</p>
                      <p className="mt-1 text-sm font-semibold">{source}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[#6366f1]" />
                    <div>
                      <p className="text-sm font-semibold">{output}</p>
                      <p className="mt-1 text-[9px] leading-4 text-black/40 dark:text-white/40">{note}</p>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-16">
            <SubsectionHeader
              index="06.4"
              title="AI 被限制为信息提取器，而不是替用户做决定。"
              copy="错误更新比少一次自动化更危险，因此模型必须被放进业务规则和人工确认之间。"
            />
            <div className="mt-6 overflow-x-auto">
              <div className="grid min-w-[900px] grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] items-stretch gap-3">
                {[
                  ["输入", "招聘通知文本", "邮件、微信或复制内容"],
                  ["提取", "公司 / 岗位 / 状态 / 时间", "LLM 不可用时降级到本地规则"],
                  ["确认", "展示依据与置信度", "用户确认或修改，不自动写入"],
                  ["写入", "状态事件 + 计划事件", "同一事务更新，避免部分成功"],
                ].map(([label, title, note], index, array) => (
                  <div key={label} className="contents">
                    <div className="rounded-2xl border border-black/[0.08] bg-white p-5 dark:border-white/10 dark:bg-[#111113]">
                      <p className="text-[9px] uppercase tracking-[0.12em] text-[#6366f1]">{label}</p>
                      <p className="mt-4 text-sm font-semibold">{title}</p>
                      <p className="mt-2 text-[10px] leading-5 text-black/40 dark:text-white/40">{note}</p>
                    </div>
                    {index < array.length - 1 ? <ArrowRight className="self-center text-black/20 dark:text-white/20" /> : null}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="interface" className="scroll-mt-28 border-y border-black/[0.07] bg-white px-5 py-20 dark:border-white/10 dark:bg-[#111113] md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="07 · INTERFACE OUTPUT"
            title={
              <>
                截图不是装饰，
                <br />
                用来解释设计决定。
              </>
            }
            copy="每个关键界面都用“问题—设计—边界”解释。这样展示的不是做了多少页面，而是产品语义如何落到具体交互。"
          />

          <div className="mt-12 space-y-10">
            {INTERFACE_CASES.map((item, index) => (
              <article
                key={item.title}
                className={`grid gap-6 lg:grid-cols-[1.25fr_.75fr] lg:items-center ${
                  index % 2 === 1 ? "lg:[&>*:first-child]:order-2" : ""
                }`}
              >
                <div
                  className={`overflow-hidden rounded-2xl border border-black/[0.08] bg-[#f7f7f5] dark:border-white/10 dark:bg-white/[0.04] ${
                    item.portrait ? "mx-auto max-w-sm p-3" : ""
                  }`}
                >
                  <Image
                    src={item.image}
                    alt={item.alt}
                    width={item.width}
                    height={item.height}
                    className={`w-full ${item.portrait ? "rounded-xl object-contain" : "aspect-[1.44/1] object-cover object-top"}`}
                  />
                </div>
                <div>
                  <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-[#6366f1]">{item.title}</p>
                  <div className="mt-6 space-y-5">
                    <Annotation label="问题" text={item.problem} />
                    <Annotation label="设计决定" text={item.decision} accent />
                    <Annotation label="边界" text={item.boundary} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="validation" className="scroll-mt-28 px-5 py-20 md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="08 · VALIDATE & ITERATE"
            title={
              <>
                先记录失败基线，
                <br />
                再修复破坏闭环的问题。
              </>
            }
            copy="我为 4 类行为角色预先定义 26 项结果检查，分别在桌面与移动环境走查。它能验证逻辑与路径，不替代真人可用性测试。"
          />

          <div className="mt-12 grid gap-3 sm:grid-cols-2">
            <IterationCard
              label="修复前 · 基线"
              core="核心 18 / 23"
              boundary="边界 0 / 3"
              note="通知时间没有进入待办；岗位库外的投递无法纳入统一管理。"
            />
            <IterationCard
              label="修复后 · 复测"
              core="核心 19 / 23"
              boundary="边界 1 / 3"
              note="两个 P0 断点关闭；完整矩阵达到 20 / 26。"
              active
            />
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <IterationFigure
              src="/media/case-study/post-fix-schedule.png"
              alt="通知中的面试时间进入近期安排"
              index="断点 A · 状态与下一步脱节"
              observation="通知中已有明确面试时间，但此前只更新状态，不进入待办。"
              reason="这会破坏 P1“更新一次就能看到下一步”的核心承诺，因此判定为 P0。"
              change="用户确认一次，同时写入状态事件与计划事件，详情和近期安排读取同一数据。"
            />
            <IterationFigure
              src="/media/case-study/post-fix-manual-application.png"
              alt="岗位库外投递补录后的详情与时间线"
              index="断点 B · 跨平台投递无法统一"
              observation="线下、内推等岗位库外机会不能记录，与产品定位直接冲突。"
              reason="系统不可能覆盖所有岗位来源，缺少补录会让主线在入口处中断。"
              change="仅要求公司和岗位两个必填字段，一次建立岗位、投递与初始事件。"
            />
          </div>

          <div className="mt-6 rounded-2xl border border-black/[0.08] bg-white p-5 dark:border-white/10 dark:bg-[#111113]">
            <p className="text-[10px] uppercase tracking-[0.14em] text-[#6366f1]">没有通过，但没有补做成“成果”</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {["实习硬条件筛选", "真实通知闭环", "CSV 历史迁移", "细分转化分析"].map((item) => (
                <div key={item} className="border-l border-black/10 pl-4 text-xs leading-6 dark:border-white/10">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <p className="mt-5 text-xs leading-6 text-black/40 dark:text-white/40">
            19/23 与 20/26 是专家模拟走查的结果覆盖，不是用户任务完成率。走查不记录满意度、任务耗时或推荐意愿。
          </p>
        </div>
      </section>

      <section id="results" className="scroll-mt-28 border-y border-black/[0.07] bg-white px-5 py-20 dark:border-white/10 dark:bg-[#111113] md:py-28">
        <div className="mx-auto max-w-6xl">
          <SectionIntro
            eyebrow="09 · RESULTS & BOUNDARY"
            title={
              <>
                产品判断与工程交付，
                <br />
                分开陈述。
              </>
            }
            copy="走查说明核心路径覆盖；测试、路由和数据验收说明 MVP 可以交付。两者都不是市场增长，也不能证明用户价值已经成立。"
          />

          <div className="mt-12 grid gap-5 lg:grid-cols-2">
            <EvidenceGroup
              label="产品设计证据"
              items={[
                ["19", "公开求职记录完成人工编码"],
                ["20", "Job Stories 形成需求池"],
                ["20 / 26", "修复后预设结果覆盖"],
              ]}
            />
            <EvidenceGroup
              label="交付与质量证据"
              items={[
                ["4 / 56", "公开 ATS 来源 / 验收岗位"],
                ["32 / 7", "业务 API / 核心数据表"],
                ["120 / 14", "后端测试 / 前端生产路由"],
              ]}
            />
          </div>

          <div className="mt-5 rounded-2xl border border-black/[0.08] bg-[#f7f7f5] p-6 dark:border-white/10 dark:bg-white/[0.04]">
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              当前能够证明
            </h3>
            <p className="mt-3 text-sm leading-7 text-black/55 dark:text-white/55">
              我能把公开研究转化为问题定义和产品范围，建立可实现的数据与交互模型，并通过预设检查发现、排序、修复和复测问题。
            </p>
          </div>

          <div className="mt-14 grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-[#6366f1]">Future validation</p>
              <h3 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">没有被证明的，留在未来验证。</h3>
              <p className="mt-4 text-sm leading-7 text-black/50 dark:text-white/50">
                下一阶段不以新增功能为目标，而是验证当前设计是否真的解决问题。
              </p>
            </div>
            <div className="grid gap-3">
              {UNPROVEN.map((item, index) => (
                <div
                  key={item}
                  className="grid grid-cols-[2rem_1fr] gap-3 border-b border-black/[0.08] py-4 text-sm leading-6 last:border-b-0 dark:border-white/10"
                >
                  <span className="font-mono text-[10px] text-[#6366f1]">{String(index + 1).padStart(2, "0")}</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-3">
            {[
              ["01", "3 次探索性访谈", "核对问题、语言、现有工具和迁移动机"],
              ["02", "5 人任务测试", "观察概念理解、入口发现和操作断点"],
              ["03", "3–5 人 7 天试用", "记录维护行为、回访原因和中断位置"],
            ].map(([index, title, note]) => (
              <div key={index} className="rounded-2xl bg-[#171719] p-5 text-white">
                <p className="font-mono text-[10px] text-[#a5b4fc]">{index}</p>
                <p className="mt-6 text-sm font-semibold">{title}</p>
                <p className="mt-2 text-[10px] leading-5 text-white/45">{note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-5 py-20 text-center md:py-28">
        <Activity className="mx-auto h-6 w-6 text-[#6366f1]" />
        <h2 className="mx-auto mt-5 max-w-3xl text-balance text-3xl font-semibold tracking-[-0.035em] md:text-5xl">
          从研究判断到真实产品，完整链路都可以现场操作。
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-black/50 dark:text-white/50">
          Demo 展示当前已实现范围；未来验证项不会被包装成现有能力。
        </p>
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Link
            href="/dashboard"
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#171719] px-6 text-sm font-medium text-white transition-transform active:scale-[0.98] dark:bg-white dark:text-black"
          >
            打开完整 Demo
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/"
            className="inline-flex min-h-12 items-center justify-center rounded-lg border border-black/10 bg-white px-6 text-sm font-medium dark:border-white/10 dark:bg-white/[0.04]"
          >
            返回产品官网
          </Link>
        </div>
      </section>
    </main>
  );
}

function SectionIntro({
  eyebrow,
  title,
  copy,
}: {
  eyebrow: string;
  title: React.ReactNode;
  copy: string;
}) {
  return (
    <div className="grid gap-8 lg:grid-cols-[.7fr_1.3fr]">
      <div>
        <p className="text-xs font-medium text-[#6366f1]">{eyebrow}</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-4xl">{title}</h2>
      </div>
      <p className="max-w-2xl text-base leading-7 text-black/55 dark:text-white/55">{copy}</p>
    </div>
  );
}

function SectionIntroDark({
  eyebrow,
  title,
  copy,
}: {
  eyebrow: string;
  title: React.ReactNode;
  copy: string;
}) {
  return (
    <div className="grid gap-8 lg:grid-cols-[.7fr_1.3fr]">
      <div>
        <p className="text-xs font-medium text-[#a5b4fc]">{eyebrow}</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em] md:text-4xl">{title}</h2>
      </div>
      <p className="max-w-2xl text-base leading-7 text-white/55">{copy}</p>
    </div>
  );
}

function SubsectionHeader({ index, title, copy }: { index: string; title: string; copy: string }) {
  return (
    <div className="grid gap-3 border-t border-black/[0.08] pt-5 dark:border-white/10 md:grid-cols-[4rem_1fr_1fr]">
      <span className="font-mono text-[10px] text-[#6366f1]">{index}</span>
      <h3 className="text-xl font-semibold leading-7 tracking-[-0.02em]">{title}</h3>
      <p className="text-sm leading-6 text-black/45 dark:text-white/45">{copy}</p>
    </div>
  );
}

function CaseMeta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-[0.12em] text-black/35 dark:text-white/35">{label}</dt>
      <dd className="mt-1.5 font-medium leading-5">{value}</dd>
    </div>
  );
}

function ResearchMethod({ value, label, note }: { value: string; label: string; note: string }) {
  return (
    <div className="rounded-2xl border border-black/[0.08] bg-white p-5 dark:border-white/10 dark:bg-[#111113]">
      <p className="font-mono text-3xl font-semibold tracking-[-0.05em]">{value}</p>
      <p className="mt-4 text-sm font-semibold">{label}</p>
      <p className="mt-2 text-[10px] leading-5 text-black/40 dark:text-white/40">{note}</p>
    </div>
  );
}

function MatrixValue({ value }: { value: "强" | "浅" | "无" }) {
  const styles = {
    强: "bg-[#171719] text-white dark:bg-white dark:text-black",
    浅: "bg-[#eef2ff] text-[#4f46e5] dark:bg-indigo-950 dark:text-indigo-300",
    无: "border border-black/10 text-black/30 dark:border-white/10 dark:text-white/30",
  };
  return <span className={`grid h-7 w-7 place-items-center text-[9px] font-medium ${styles[value]}`}>{value}</span>;
}

function ComparisonCard({
  label,
  title,
  note,
  accent = false,
}: {
  label: string;
  title: string;
  note: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        accent
          ? "border-[#a5b4fc] bg-[#eef2ff] dark:border-indigo-700 dark:bg-indigo-950/50"
          : "border-black/[0.08] bg-white dark:border-white/10 dark:bg-[#111113]"
      }`}
    >
      <p className="text-[9px] uppercase tracking-[0.12em] text-[#6366f1]">{label}</p>
      <p className="mt-4 text-sm font-semibold">{title}</p>
      <p className="mt-2 text-[10px] leading-5 text-black/40 dark:text-white/40">{note}</p>
    </div>
  );
}

function ArrowConnector() {
  return <ArrowRight className="hidden h-4 w-4 self-center text-black/20 dark:text-white/20 md:block" />;
}

function DemandCell({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p className={`text-[9px] uppercase tracking-[0.12em] ${accent ? "text-[#6366f1]" : "text-black/30 dark:text-white/30"}`}>
        {label}
      </p>
      <p className={`mt-2 text-xs leading-6 ${accent ? "font-medium" : "text-black/55 dark:text-white/55"}`}>{value}</p>
    </div>
  );
}

function ModelLayer({
  index,
  label,
  title,
  values,
  note,
  accent = false,
}: {
  index: string;
  label: string;
  title: string;
  values: string[];
  note: string;
  accent?: boolean;
}) {
  return (
    <article
      className={`rounded-2xl border p-5 ${
        accent
          ? "border-[#a5b4fc] bg-[#eef2ff] dark:border-indigo-700 dark:bg-indigo-950/50"
          : "border-black/[0.08] bg-white dark:border-white/10 dark:bg-[#111113]"
      }`}
    >
      <div className="flex justify-between">
        <p className="text-[9px] uppercase tracking-[0.12em] text-[#6366f1]">{label}</p>
        <span className="font-mono text-[9px] text-black/25 dark:text-white/25">{index}</span>
      </div>
      <h3 className="mt-5 text-sm font-semibold">{title}</h3>
      <div className="mt-4 flex flex-wrap gap-2">
        {values.map((value) => (
          <span key={value} className="border border-black/10 bg-white/50 px-2 py-1 text-[10px] dark:border-white/10 dark:bg-white/[0.04]">
            {value}
          </span>
        ))}
      </div>
      <p className="mt-4 text-[10px] leading-5 text-black/40 dark:text-white/40">{note}</p>
    </article>
  );
}

function Annotation({ label, text, accent = false }: { label: string; text: string; accent?: boolean }) {
  return (
    <div className="grid grid-cols-[4rem_1fr] gap-4 border-t border-black/[0.08] pt-4 dark:border-white/10">
      <p className={`text-[10px] font-medium ${accent ? "text-[#6366f1]" : "text-black/35 dark:text-white/35"}`}>{label}</p>
      <p className={`text-sm leading-7 ${accent ? "font-medium" : "text-black/55 dark:text-white/55"}`}>{text}</p>
    </div>
  );
}

function IterationCard({
  label,
  core,
  boundary,
  note,
  active = false,
}: {
  label: string;
  core: string;
  boundary: string;
  note: string;
  active?: boolean;
}) {
  return (
    <article
      className={`rounded-2xl border p-5 ${
        active
          ? "border-[#a5b4fc] bg-[#eef2ff] dark:border-indigo-700 dark:bg-indigo-950/50"
          : "border-black/[0.08] bg-white dark:border-white/10 dark:bg-[#111113]"
      }`}
    >
      <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-[#6366f1]">{label}</p>
      <div className="mt-4 flex flex-wrap gap-4 text-sm font-semibold">
        <span>{core}</span>
        <span>{boundary}</span>
      </div>
      <p className="mt-3 text-xs leading-6 text-black/50 dark:text-white/50">{note}</p>
    </article>
  );
}

function IterationFigure({
  src,
  alt,
  index,
  observation,
  reason,
  change,
}: {
  src: string;
  alt: string;
  index: string;
  observation: string;
  reason: string;
  change: string;
}) {
  return (
    <figure className="overflow-hidden rounded-2xl border border-black/[0.08] bg-white dark:border-white/10 dark:bg-[#111113]">
      <Image
        src={src}
        alt={alt}
        width={1440}
        height={1000}
        className="aspect-[1.44/1] w-full object-cover object-top"
      />
      <figcaption className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-[#6366f1]">{index}</p>
          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700 dark:text-emerald-400">
            <Check className="h-3 w-3" />
            复测通过
          </span>
        </div>
        <div className="mt-4 space-y-2 text-xs leading-6 text-black/50 dark:text-white/50">
          <p><span className="font-medium text-black/75 dark:text-white/75">观察：</span>{observation}</p>
          <p><span className="font-medium text-black/75 dark:text-white/75">判断：</span>{reason}</p>
          <p><span className="font-medium text-black/75 dark:text-white/75">方案：</span>{change}</p>
        </div>
      </figcaption>
    </figure>
  );
}

function EvidenceGroup({ label, items }: { label: string; items: [string, string][] }) {
  return (
    <div className="rounded-2xl bg-[#171719] p-5 text-white">
      <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-white/40">{label}</p>
      <div className="mt-5 grid grid-cols-3 gap-2">
        {items.map(([value, itemLabel]) => (
          <div key={itemLabel} className="bg-white/[0.06] p-4">
            <p className="font-mono text-xl font-semibold tracking-[-0.04em] md:text-2xl">{value}</p>
            <p className="mt-2 text-[10px] leading-5 text-white/45">{itemLabel}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function CaseFilmFallback() {
  return (
    <div className="grid h-full place-items-center bg-[#f5f5f7] p-[8%] text-[#171719]">
      <div className="w-full max-w-2xl">
        <div className="mx-auto grid aspect-square w-[10%] place-items-center rounded-full bg-[#6366f1] text-white">
          <Play className="h-1/3 w-1/3 fill-current" />
        </div>
        <p className="mt-[4%] text-center text-[clamp(10px,2vw,24px)] font-semibold">完整产品讲解</p>
        <div className="mt-[7%] grid grid-cols-3 gap-[2%]">
          {[
            [CircleDot, "问题与范围"],
            [GitBranch, "模型与决策"],
            [Check, "验证与结果"],
          ].map(([Icon, label]) => {
            const C = Icon as typeof CircleDot;
            return (
              <div key={String(label)} className="rounded-lg border border-black/[0.08] bg-white p-[8%] text-center">
                <C className="mx-auto h-[1em] w-[1em] text-[#6366f1]" />
                <p className="mt-[8%] text-[clamp(5px,.85vw,11px)]">{String(label)}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
