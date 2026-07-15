"use client";

import { motion } from "framer-motion";
import { CalendarRange, Filter, ListFilter, Target, TrendingUp } from "lucide-react";

/**
 * 第 4 屏 · 功能③数据驱动（全宽沉浸式布局）。
 *
 * 这屏改成复盘工作台：筛选器、漏斗、趋势、洞察和建议同屏出现，
 * 让数据像真实产品界面，而不只是营销页上的一组图。
 */
const FUNNEL = [
  { stage: "收藏", count: 120, color: "var(--status-no-response)" },
  { stage: "已投递", count: 48, color: "var(--status-applied)" },
  { stage: "笔试", count: 18, color: "var(--status-testing)" },
  { stage: "面试", count: 9, color: "var(--status-interview)" },
  { stage: "Offer", count: 2, color: "var(--status-offer)" },
];

const TREND_PATH =
  "M0,50 C30,48 45,52 70,45 C95,38 110,30 140,32 C170,34 185,18 210,14";

const FILTERS = [
  { label: "时间", value: "近 30 天" },
  { label: "岗位", value: "产品经理" },
  { label: "城市", value: "全部城市" },
];

const INSIGHTS = [
  {
    title: "最大瓶颈",
    value: "笔试到面试",
    meta: "18 进 9，转化率 50%",
    color: "--status-testing",
  },
  {
    title: "最佳来源",
    value: "企业官网",
    meta: "面试率 23%，高于均值",
    color: "--status-interview",
  },
  {
    title: "建议动作",
    value: "补 4 个投递",
    meta: "保持本周节奏",
    color: "--status-applied",
  },
];

export function DataDashboardSection() {
  return (
    <section id="dashboard" className="relative w-full px-6 py-32 scroll-mt-20 md:py-40">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 text-center md:mb-16">
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.5 }}
            className="mb-3 inline-block text-xs font-medium uppercase tracking-wider text-muted-foreground"
          >
            数据驱动 · 复盘
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-3xl leading-[1.1] tracking-tight text-foreground md:text-4xl lg:text-5xl"
          >
            用数据看清你的<em>求职节奏</em>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mx-auto mt-4 max-w-xl text-sm text-muted-foreground"
          >
            投递漏斗、转化趋势、瓶颈定位在同一个工作台里，复盘可以直接变成下一步动作。
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="overflow-hidden rounded-2xl border border-border/60 bg-card shadow-dashboard"
        >
          <DashboardToolbar />

          <div className="grid grid-cols-1 gap-0 lg:grid-cols-[170px_minmax(0,1fr)_230px]">
            <FilterRail />
            <div className="min-w-0 border-y border-border/60 p-4 lg:border-x lg:border-y-0 md:p-6">
              <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(260px,0.75fr)]">
                <FunnelPanel />
                <TrendPanel />
              </div>
            </div>
            <InsightPanel />
          </div>
        </motion.div>

        <KpiStrip />
      </div>
    </section>
  );
}

function DashboardToolbar() {
  return (
    <div className="flex flex-col gap-3 border-b border-border/60 px-4 py-3 md:flex-row md:items-center md:justify-between md:px-6">
      <div>
        <div className="text-sm font-semibold text-foreground">求职复盘工作台</div>
        <div className="mt-0.5 text-[11px] text-muted-foreground">
          数据来自岗位、投递、提醒和状态历史
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter.label}
            type="button"
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-[11px] text-foreground active:translate-y-px"
          >
            <span className="text-muted-foreground">{filter.label}</span>
            {filter.value}
          </button>
        ))}
      </div>
    </div>
  );
}

function FilterRail() {
  return (
    <div className="p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-foreground">
        <ListFilter className="h-4 w-4 text-muted-foreground" />
        复盘维度
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 lg:grid-cols-1">
        {["全部来源", "校招", "实习", "官网", "已收藏", "需跟进"].map((item, i) => (
          <motion.button
            key={item}
            type="button"
            initial={{ opacity: 0, x: -8 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.3, delay: 0.45 + i * 0.05 }}
            className={`rounded-lg px-3 py-2 text-left text-[11px] transition active:translate-y-px ${
              i === 0
                ? "bg-secondary text-foreground"
                : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
            }`}
          >
            {item}
          </motion.button>
        ))}
      </div>
    </div>
  );
}

function FunnelPanel() {
  return (
    <div className="rounded-xl border border-border/50 bg-background p-4">
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-foreground">投递漏斗</span>
        <span className="text-[11px] text-muted-foreground">达到该阶段的岗位数</span>
      </div>
      <div className="space-y-2">
        {FUNNEL.map((item, i) => {
          const maxCount = FUNNEL[0].count;
          const widthPct = (item.count / maxCount) * 100;
          const conversion =
            i === 0 ? 100 : Math.round((item.count / FUNNEL[i - 1].count) * 100);
          return (
            <motion.div
              key={item.stage}
              initial={{ opacity: 0, width: 0 }}
              whileInView={{ opacity: 1, width: `${Math.max(widthPct, 18)}%` }}
              viewport={{ once: false }}
              transition={{ duration: 0.6, delay: 0.55 + i * 0.12 }}
              className="relative flex h-11 min-w-[150px] items-center justify-between rounded-lg px-3"
              style={{
                background: `hsl(${item.color} / 0.15)`,
                borderLeft: `3px solid hsl(${item.color})`,
              }}
            >
              <span className="text-xs font-medium text-foreground">{item.stage}</span>
              <span className="flex items-center gap-2 text-[11px]">
                <span className="tabular-nums text-foreground">{item.count}</span>
                {i > 0 && <span className="text-muted-foreground">{conversion}%</span>}
              </span>
            </motion.div>
          );
        })}
      </div>
      <div className="mt-4 rounded-lg bg-secondary/45 px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
        看到瓶颈后，可以直接跳回对应状态列表批量跟进。
      </div>
    </div>
  );
}

function TrendPanel() {
  return (
    <div className="rounded-xl border border-border/50 bg-background p-4">
      <div className="mb-5 flex items-center gap-2">
        <TrendingUp className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-foreground">投递节奏</span>
      </div>
      <div className="relative h-48 rounded-lg bg-secondary/40 p-4">
        <svg viewBox="0 0 210 60" className="h-full w-full" preserveAspectRatio="none">
          <defs>
            <linearGradient id="trendAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity="0.2" />
              <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity="0" />
            </linearGradient>
          </defs>
          <motion.path
            d={`${TREND_PATH} L210,60 L0,60 Z`}
            fill="url(#trendAreaGrad)"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: false }}
            transition={{ duration: 1, delay: 0.9 }}
          />
          <motion.path
            d={TREND_PATH}
            fill="none"
            stroke="hsl(var(--accent))"
            strokeLinecap="round"
            strokeWidth="1.5"
            initial={{ pathLength: 0 }}
            whileInView={{ pathLength: 1 }}
            viewport={{ once: false }}
            transition={{ duration: 1.4, delay: 0.7 }}
          />
        </svg>
        <div className="absolute bottom-2 left-4 right-4 flex justify-between text-[9px] text-muted-foreground">
          <span>Day 1</span>
          <span>Day 15</span>
          <span>Day 30</span>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-secondary/45 px-3 py-2">
          <div className="text-muted-foreground">总投递</div>
          <div className="mt-1 font-semibold tabular-nums text-foreground">48</div>
        </div>
        <div className="rounded-lg bg-secondary/45 px-3 py-2">
          <div className="text-muted-foreground">高峰日</div>
          <div className="mt-1 font-semibold text-foreground">周三</div>
        </div>
      </div>
    </div>
  );
}

function InsightPanel() {
  return (
    <div className="p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-foreground">
        <Target className="h-4 w-4 text-muted-foreground" />
        自动洞察
      </div>
      <div className="mt-4 space-y-3">
        {INSIGHTS.map((insight, i) => (
          <motion.div
            key={insight.title}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.35, delay: 0.65 + i * 0.1 }}
            className="rounded-xl border border-border/50 bg-background p-3"
          >
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
              <span
                className="h-2 w-2 rounded-full"
                style={{ background: `hsl(var(${insight.color}))` }}
              />
              {insight.title}
            </div>
            <div className="mt-2 text-sm font-semibold text-foreground">
              {insight.value}
            </div>
            <div className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
              {insight.meta}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function KpiStrip() {
  const kpis = [
    { icon: Target, label: "Offer 转化率", value: "4.2%", hint: "高于行业均值" },
    { icon: TrendingUp, label: "本月新增投递", value: "+48", hint: "环比 +12%" },
    { icon: Filter, label: "最大瓶颈", value: "笔试到面试", hint: "转化率 50%" },
    { icon: CalendarRange, label: "待处理节点", value: "3", hint: "今天到期" },
  ];

  return (
    <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 md:mt-12">
      {kpis.map((kpi, i) => {
        const Icon = kpi.icon;
        return (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.5, delay: 0.8 + i * 0.1 }}
            className="rounded-xl border border-border/60 bg-card p-5"
          >
            <div className="mb-2 flex items-center gap-2 text-[11px] text-muted-foreground">
              <Icon className="h-3.5 w-3.5" />
              {kpi.label}
            </div>
            <div className="text-xl font-semibold tabular-nums text-foreground">
              {kpi.value}
            </div>
            <div className="mt-1 text-[11px] text-muted-foreground">{kpi.hint}</div>
          </motion.div>
        );
      })}
    </div>
  );
}
