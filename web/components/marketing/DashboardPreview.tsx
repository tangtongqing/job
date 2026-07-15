"use client";

import {
  Activity,
  Bell,
  CalendarDays,
  ChevronDown,
  CircleDot,
  Inbox,
  LineChart,
  MoreHorizontal,
  Plus,
  Search,
} from "lucide-react";
import { motion } from "framer-motion";
import { CountUp } from "./CountUp";
import {
  DEMO_APPLICATIONS,
  DEMO_BADGES,
  DEMO_METRICS,
  DEMO_REMINDERS,
  DEMO_SOURCE_SUMMARY,
  DEMO_STATUS_ROWS,
  DEMO_TREND,
  DEMO_USER,
} from "@/lib/dashboard-data";

/**
 * Hero 内的产品工作台预览。
 * 纯 React 绘制，强调真实产品信息密度：来源、指标、状态、提醒和最近投递。
 */
export function DashboardPreview() {
  return (
    <div className="mt-8 w-full max-w-5xl overflow-hidden rounded-2xl border border-border/60 bg-card shadow-dashboard">
      <div className="w-full overflow-hidden rounded-xl select-none">
        <DashboardChrome />
        <div className="flex">
          <DashboardSidebar />
          <DashboardMain />
        </div>
      </div>
    </div>
  );
}

function DashboardChrome() {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/60 px-3 py-2.5 md:px-4">
      <div className="flex items-center gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Activity className="h-3.5 w-3.5" />
        </div>
        <span className="text-[11px] font-medium text-foreground">JobPulse</span>
        <ChevronDown className="hidden h-3 w-3 text-muted-foreground sm:block" />
      </div>

      <div className="hidden min-w-0 flex-1 max-w-sm items-center gap-2 rounded-md border border-border/60 bg-secondary/50 px-2.5 py-1 text-[11px] text-muted-foreground sm:flex">
        <Search className="h-3 w-3 shrink-0" />
        <span className="truncate">搜索岗位、公司或状态</span>
        <span className="ml-auto rounded border border-border px-1 text-[10px]">Ctrl K</span>
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        <span className="hidden text-[11px] text-muted-foreground md:inline">3 个提醒</span>
        <Bell className="h-3.5 w-3.5 text-muted-foreground" />
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent text-[10px] font-medium text-accent-foreground">
          {DEMO_USER.initials}
        </div>
      </div>
    </div>
  );
}

const SIDEBAR_MAIN = [
  { label: "看板", active: true },
  { label: "岗位", badge: DEMO_BADGES.jobs },
  { label: "投递管理" },
  { label: "收藏", chevron: true },
  { label: "待办", badge: DEMO_BADGES.todo },
  { label: "订阅" },
  { label: "采集", chevron: true },
];

const SIDEBAR_WORKFLOWS = ["简历库", "面试笔记", "DDL 提醒", "设置"];

function DashboardSidebar() {
  return (
    <aside className="hidden w-40 shrink-0 flex-col gap-0.5 border-r border-border/60 px-2.5 py-3 md:flex">
      {SIDEBAR_MAIN.map((item) => (
        <SidebarItem key={item.label} {...item} />
      ))}
      <div className="mb-1 mt-3 px-2 text-[9px] uppercase tracking-wider text-muted-foreground">
        工作流
      </div>
      {SIDEBAR_WORKFLOWS.map((label) => (
        <SidebarItem key={label} label={label} />
      ))}
    </aside>
  );
}

function SidebarItem({
  label,
  active,
  badge,
  chevron,
}: {
  label: string;
  active?: boolean;
  badge?: string;
  chevron?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between rounded px-2 py-1 text-[11px] ${
        active
          ? "bg-secondary text-foreground font-medium"
          : "text-muted-foreground"
      }`}
    >
      <span>{label}</span>
      {badge && (
        <span className="rounded-full bg-primary px-1.5 py-0.5 text-[9px] text-primary-foreground">
          {badge}
        </span>
      )}
      {chevron && <ChevronDown className="h-3 w-3" />}
    </div>
  );
}

function DashboardMain() {
  return (
    <div className="min-w-0 flex-1 bg-secondary/30 p-3 md:p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-semibold text-foreground">
            {DEMO_USER.greeting}，{DEMO_USER.name}
          </div>
          <div className="mt-0.5 text-[11px] text-muted-foreground">
            你有 3 个节点需要今天处理
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <PillButton variant="primary">新投递</PillButton>
          <PillButton>邮件解析</PillButton>
          <PillButton>批量流转</PillButton>
        </div>
      </div>

      <MetricStrip />

      <div className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1fr)_220px]">
        <div className="min-w-0 space-y-3">
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <TrendCard />
            <StatusCard />
          </div>
          <RecentApplicationsTable />
        </div>
        <ReminderPanel />
      </div>
    </div>
  );
}

function PillButton({
  children,
  variant = "default",
}: {
  children: React.ReactNode;
  variant?: "default" | "primary";
}) {
  return (
    <button
      type="button"
      className={`rounded-full px-2.5 py-1 text-[10px] font-medium transition active:translate-y-px ${
        variant === "primary"
          ? "bg-accent text-accent-foreground"
          : "border border-border bg-background text-foreground hover:bg-secondary"
      }`}
    >
      {children}
    </button>
  );
}

function MetricStrip() {
  return (
    <div className="mt-3 grid grid-cols-3 gap-2">
      {DEMO_METRICS.map((metric, i) => (
        <motion.div
          key={metric.label}
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false }}
          transition={{ duration: 0.35, delay: 0.5 + i * 0.08 }}
          className="rounded-lg border border-border/50 bg-background p-2.5"
        >
          <div className="text-[10px] text-muted-foreground">{metric.label}</div>
          <div className="mt-1 text-sm font-semibold tabular-nums text-foreground md:text-base">
            {metric.value}
          </div>
          <div className="mt-0.5 truncate text-[9px] text-muted-foreground">
            {metric.delta}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function TrendCard() {
  return (
    <div className="min-w-0 rounded-lg border border-border/50 bg-background p-3.5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <LineChart className="h-3.5 w-3.5" />
          本月投递趋势
        </div>
        <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground">
          {DEMO_TREND.recentLabel}
        </span>
      </div>

      <div className="mt-1.5 text-base font-semibold tabular-nums text-foreground">
        <CountUp end={DEMO_TREND.monthlyCount} />
        <span className="text-xs text-muted-foreground"> 个新投递</span>
      </div>

      <div className="mt-1.5 flex items-center gap-3 text-[10px]">
        <span className="text-[hsl(var(--status-interview))]">
          {DEMO_TREND.increases.label}
        </span>
        <span className="text-[hsl(var(--status-declined))]">
          {DEMO_TREND.decreases.label}
        </span>
      </div>

      <svg
        viewBox="0 0 200 80"
        className="mt-2 h-20 w-full"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity="0.15" />
            <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d="M0,55 C15,50 25,58 40,52 C55,46 65,35 80,38 C95,41 105,25 120,22 C135,19 145,32 160,26 C175,20 185,12 200,10 L200,80 L0,80 Z"
          fill="url(#trendGrad)"
          className="animate-fill-area"
        />
        <path
          d="M0,55 C15,50 25,58 40,52 C55,46 65,35 80,38 C95,41 105,25 120,22 C135,19 145,32 160,26 C175,20 185,12 200,10"
          fill="none"
          stroke="hsl(var(--accent))"
          strokeLinecap="round"
          strokeWidth="1.5"
          vectorEffect="non-scaling-stroke"
          className="animate-draw-curve"
        />
      </svg>

      <div className="grid grid-cols-4 gap-1.5">
        {DEMO_SOURCE_SUMMARY.map((source, i) => (
          <motion.div
            key={source.source}
            initial={{ opacity: 0, y: 6 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.35, delay: 1 + i * 0.08 }}
            className="rounded-md bg-secondary/50 px-2 py-1"
          >
            <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground">
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: `hsl(var(${source.colorVar}))` }}
              />
              {source.source}
            </div>
            <div className="mt-0.5 text-[10px] font-medium tabular-nums text-foreground">
              {source.count}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function StatusCard() {
  return (
    <div className="rounded-lg border border-border/50 bg-background p-3.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-foreground">投递状态分布</span>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Plus className="h-3 w-3" />
          <MoreHorizontal className="h-3 w-3" />
        </div>
      </div>

      <div className="mt-2 space-y-1.5">
        {DEMO_STATUS_ROWS.map((row, i) => (
          <motion.div
            key={row.label}
            initial={{ opacity: 0, x: -8 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.35, delay: 0.8 + i * 0.1 }}
            className="rounded-md border border-border/40 bg-secondary/30 px-2.5 py-2"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: `hsl(var(${row.colorVar}))` }}
                />
                {row.label}
              </span>
              <span className="tabular-nums text-foreground">
                <CountUp end={row.count} delay={900 + i * 100} />
              </span>
            </div>
            <div className="mt-1 h-1 overflow-hidden rounded-full bg-border/60">
              <motion.div
                initial={{ width: 0 }}
                whileInView={{ width: `${Math.min(row.count * 4, 100)}%` }}
                viewport={{ once: false }}
                transition={{ duration: 0.5, delay: 1 + i * 0.1 }}
                className="h-full rounded-full"
                style={{ background: `hsl(var(${row.colorVar}))` }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

const TONE_CLASS: Record<string, string> = {
  applied: "text-[hsl(var(--status-applied))]",
  testing: "text-[hsl(var(--status-testing))]",
  interview: "text-[hsl(var(--status-interview))]",
  offer: "text-[hsl(var(--status-offer))]",
  declined: "text-[hsl(var(--status-declined))]",
};

function RecentApplicationsTable() {
  return (
    <div className="rounded-lg border border-border/50 bg-background p-3.5">
      <div className="mb-1 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[11px] font-medium text-foreground">
          <Inbox className="h-3.5 w-3.5 text-muted-foreground" />
          最近投递
        </div>
        <span className="text-[10px] text-muted-foreground">自动同步 5 分钟前</span>
      </div>
      <table className="w-full text-[11px]">
        <thead>
          <tr className="text-left text-muted-foreground">
            <th className="hidden py-1.5 font-normal sm:table-cell">日期</th>
            <th className="py-1.5 font-normal">公司</th>
            <th className="py-1.5 font-normal">岗位</th>
            <th className="py-1.5 text-right font-normal">状态</th>
          </tr>
        </thead>
        <tbody>
          {DEMO_APPLICATIONS.map((app, i) => (
            <motion.tr
              key={app.company}
              initial={{ opacity: 0, y: 6 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false }}
              transition={{ duration: 0.35, delay: 1.1 + i * 0.08 }}
              className="text-foreground"
            >
              <td className="hidden py-1.5 text-muted-foreground sm:table-cell">
                {app.date}
              </td>
              <td className="py-1.5">{app.company}</td>
              <td className="py-1.5 text-muted-foreground">{app.role}</td>
              <td className={`py-1.5 text-right ${TONE_CLASS[app.tone]}`}>
                {app.status}
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReminderPanel() {
  return (
    <div className="rounded-lg border border-border/50 bg-background p-3.5">
      <div className="flex items-center gap-1.5 text-[11px] font-medium text-foreground">
        <CalendarDays className="h-3.5 w-3.5 text-muted-foreground" />
        今日提醒
      </div>
      <div className="mt-2 space-y-2">
        {DEMO_REMINDERS.map((item, i) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.35, delay: 1.2 + i * 0.1 }}
            className="rounded-md bg-secondary/40 px-2.5 py-2"
          >
            <div className="flex items-start gap-2">
              <CircleDot
                className="mt-0.5 h-3.5 w-3.5 shrink-0"
                style={{ color: `hsl(var(${item.tone}))` }}
              />
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] tabular-nums text-muted-foreground">
                    {item.time}
                  </span>
                  <span className="truncate text-[11px] font-medium text-foreground">
                    {item.title}
                  </span>
                </div>
                <div className="mt-0.5 text-[10px] text-muted-foreground">
                  {item.meta}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
