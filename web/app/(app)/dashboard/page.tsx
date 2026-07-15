"use client";

import Link from "next/link";
import { ArrowRight, BellRing, BriefcaseBusiness, CalendarClock, CheckCircle2, Send, Sparkles } from "lucide-react";

import { ErrorState, Loading, StatusBadge, useApi } from "@/components/app/shared";
import { api, type Application, type FunnelItem, type Todo } from "@/lib/api";
import { getStatusLabel } from "@/lib/status-config";

const TRAJECTORY = [
  { code: "applied", label: "已投递" },
  { code: "test", label: "测评" },
  { code: "interviewing", label: "面试" },
  { code: "offer_pending", label: "Offer" },
  { code: "offer_accepted", label: "已接受" },
];

export default function DashboardPage() {
  const overview = useApi<{
    kpi: { today_new_jobs: number; total_jobs: number; total_applications: number; pending_applications: number };
    funnel: FunnelItem[];
    applications: Application[];
    todos: Todo[];
  }>(() =>
    Promise.all([api.getKPI(), api.getFunnel(), api.getApplications({ page: 1, page_size: 6 }), api.getTodo(14)]).then(
      ([kpi, funnel, applications, todos]) => ({
        data: {
          kpi: kpi.data,
          funnel: funnel.data.funnel,
          applications: applications.data,
          todos: todos.data,
        },
      })
    )
  );

  if (overview.loading) return <Loading text="正在整理你的求职进展…" />;
  if (overview.error) return <ErrorState message={overview.error} onRetry={overview.reload} />;
  if (!overview.data) return null;

  const { kpi, funnel, applications, todos } = overview.data;
  const funnelMap = new Map(funnel.map((item) => [item.status, item.count]));

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-xs font-medium text-[#4f46e5]">YOUR SEARCH, IN MOTION</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-[-0.025em]">今天从清楚下一步开始</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            {todos.length > 0 ? `未来 14 天有 ${todos.length} 个安排，需要你保持节奏。` : "近期没有临近安排，可以继续发现新机会。"}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/jobs" className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-black/10 bg-white px-4 text-sm font-medium hover:bg-black/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent dark:border-white/10 dark:bg-card dark:hover:bg-white/[0.06]">
            <BriefcaseBusiness className="h-4 w-4" /> 发现岗位
          </Link>
          <Link href="/saved" className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-foreground px-4 text-sm font-medium text-background hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
            查看待投递 <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </header>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="求职数据摘要">
        <Metric label="今日新增岗位" value={kpi.today_new_jobs} icon={Sparkles} detail="来自聚合数据源" />
        <Metric label="岗位库" value={kpi.total_jobs} icon={BriefcaseBusiness} detail="当前可浏览" />
        <Metric label="投递记录" value={kpi.total_applications} icon={Send} detail="含进行中与已结束" />
        <Metric label="进行中" value={kpi.pending_applications} icon={CalendarClock} detail="仍需要跟进" accent />
      </section>

      <section className="overflow-hidden rounded-2xl border border-black/[0.07] bg-white dark:border-white/10 dark:bg-card">
        <div className="flex flex-col justify-between gap-2 border-b border-black/[0.06] px-5 py-4 sm:flex-row sm:items-center dark:border-white/10">
          <div>
            <h2 className="text-sm font-semibold">投递轨迹</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">按到达阶段累计，清楚看到流程走到了哪里。</p>
          </div>
          <Link href="/applications" className="inline-flex min-h-10 items-center gap-1.5 text-xs font-medium text-[#4f46e5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
            管理全部投递 <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
        <div className="overflow-x-auto px-5 py-8">
          <div className="relative mx-auto flex min-w-[680px] max-w-4xl items-start justify-between">
            <div className="absolute left-[9%] right-[9%] top-[1.125rem] h-px bg-[#d9dbe2] dark:bg-white/15" />
            <div className="absolute left-[9%] top-[1.125rem] h-px bg-[#6366f1] transition-[width] duration-500" style={{ width: trajectoryProgress(funnelMap) }} />
            {TRAJECTORY.map((stage, index) => {
              const count = funnelMap.get(stage.code) || 0;
              const reached = count > 0;
              return (
                <div key={stage.code} className="relative z-10 w-28 text-center">
                  <span className={`mx-auto grid h-9 w-9 place-items-center rounded-full border-4 border-white text-xs font-semibold dark:border-card ${reached ? "bg-[#6366f1] text-white" : "bg-[#ececf0] text-muted-foreground dark:bg-white/10"}`}>
                    {reached && index === TRAJECTORY.length - 1 ? <CheckCircle2 className="h-4 w-4" /> : count}
                  </span>
                  <p className="mt-2 text-xs font-medium">{stage.label}</p>
                  <p className="mt-0.5 text-[10px] text-muted-foreground">{count ? `${count} 次到达` : "尚未到达"}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_0.9fr]">
        <section className="rounded-2xl border border-black/[0.07] bg-white p-5 dark:border-white/10 dark:bg-card">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">最近更新</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">当前状态和最后更新时间</p>
            </div>
            <span className="text-[11px] text-muted-foreground">{applications.length} 条显示</span>
          </div>
          <div className="divide-y divide-black/[0.06] dark:divide-white/10">
            {applications.map((application) => (
              <Link key={application.id} href={`/applications/${application.id}`} className="group flex min-h-[4.5rem] items-center gap-3 py-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-[#f1f1f3] text-xs font-semibold dark:bg-white/10">{application.job?.company?.slice(0, 1) || "投"}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium group-hover:text-[#4f46e5]">{application.job?.company || `岗位 #${application.job_id}`} · {application.job?.title || "投递记录"}</span>
                  <span className="mt-0.5 block text-[11px] text-muted-foreground">更新于 {formatDate(application.updated_at)}</span>
                </span>
                <StatusBadge status={application.status} />
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </Link>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-black/[0.07] bg-[#111113] p-5 text-white dark:border-white/10">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-sm font-semibold">下一步</h2>
              <p className="mt-0.5 text-xs text-white/55">未来 14 天的关键动作</p>
            </div>
            <BellRing className="h-4 w-4 text-[#a5b4fc]" />
          </div>
          <div className="mt-5 space-y-2">
            {todos.length > 0 ? todos.slice(0, 3).map((todo) => (
              <Link key={todo.event_id} href={`/applications/${todo.application_id}`} className="flex min-h-[4.5rem] items-center gap-3 rounded-xl border border-white/10 bg-white/[0.055] px-3 transition-colors hover:bg-white/[0.09] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#a5b4fc]">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-white/10 text-center">
                  <span className="text-sm font-semibold tabular-nums">{todo.days_left ?? "—"}</span>
                  <span className="sr-only">天后</span>
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-xs font-medium">{todo.job?.company} · {todoEventLabel(todo.event_type)}</span>
                  <span className="mt-0.5 block truncate text-[11px] text-white/50">{todo.note || todo.job?.title}</span>
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-white/40" />
              </Link>
            )) : (
              <div className="rounded-xl border border-dashed border-white/15 px-4 py-8 text-center text-xs text-white/50">当前没有临近安排</div>
            )}
          </div>
          <Link href="/todo" className="mt-4 inline-flex min-h-10 items-center gap-1.5 text-xs font-medium text-[#c7d2fe] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#a5b4fc]">打开近期安排 <ArrowRight className="h-3.5 w-3.5" /></Link>
        </section>
      </div>
    </div>
  );
}

function Metric({ label, value, icon: Icon, detail, accent = false }: { label: string; value: number; icon: React.ComponentType<{ className?: string }>; detail: string; accent?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${accent ? "border-[#c7d2fe] bg-[#eef2ff] dark:border-indigo-800 dark:bg-indigo-950/50" : "border-black/[0.07] bg-white dark:border-white/10 dark:bg-card"}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <Icon className={`h-4 w-4 ${accent ? "text-[#4f46e5] dark:text-indigo-300" : "text-muted-foreground"}`} />
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight tabular-nums">{value}</p>
      <p className="mt-1 text-[10px] text-muted-foreground">{detail}</p>
    </div>
  );
}

function trajectoryProgress(funnel: Map<string, number>) {
  let lastReached = -1;
  TRAJECTORY.forEach((stage, index) => {
    if ((funnel.get(stage.code) || 0) > 0) lastReached = index;
  });
  return `${Math.max(0, lastReached) * 20.5}%`;
}

function formatDate(value: string) {
  return value.slice(0, 16).replace("T", " ");
}

function todoEventLabel(eventType: string) {
  return eventType === "interview" ? "面试" : eventType === "test" ? "测评" : getStatusLabel(eventType);
}
