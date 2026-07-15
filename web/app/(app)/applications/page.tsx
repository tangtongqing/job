"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, ChevronDown } from "lucide-react";

import { EmptyState, ErrorState, Loading, StatusBadge, useApi } from "@/components/app/shared";
import { useToast } from "@/components/app/toast";
import { api, type Application } from "@/lib/api";
import { APPLICATION_STATUSES, getNextStatuses, getStatusLabel, isTerminal } from "@/lib/status-config";
import { cn } from "@/lib/utils";

type ViewFilter = "all" | "active" | "closed";

export default function ApplicationsPage() {
  const { toast } = useToast();
  const applications = useApi<Application[]>(() => api.getApplications({ page: 1, page_size: 50 }));
  const [view, setView] = useState<ViewFilter>("all");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [batchStatus, setBatchStatus] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [batching, setBatching] = useState(false);

  const filtered = useMemo(() => {
    const items = applications.data || [];
    if (view === "active") return items.filter((item) => !isTerminal(item.status));
    if (view === "closed") return items.filter((item) => isTerminal(item.status));
    return items;
  }, [applications.data, view]);

  const counts = useMemo(() => {
    const result: Record<string, number> = {};
    (applications.data || []).forEach((item) => { result[item.status] = (result[item.status] || 0) + 1; });
    return result;
  }, [applications.data]);

  const transition = async (id: number, status: string) => {
    setBusyId(id);
    try {
      await api.transition(id, status);
      toast(`已更新为「${getStatusLabel(status)}」`);
      applications.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "状态更新失败", "error");
    } finally {
      setBusyId(null);
    }
  };

  const batchTransition = async () => {
    if (!batchStatus || selected.size === 0) return;
    setBatching(true);
    try {
      const response = await api.batchTransition([...selected], batchStatus);
      const { success_count, fail_count } = response.data;
      toast(fail_count ? `${success_count} 项成功，${fail_count} 项未更新` : `${success_count} 项已更新`, fail_count ? "error" : "success");
      setSelected(new Set());
      setBatchStatus("");
      applications.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "批量更新失败", "error");
    } finally {
      setBatching(false);
    }
  };

  const toggle = (id: number) => setSelected((current) => {
    const next = new Set(current);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-xs font-medium text-[#4f46e5]">EVERY STEP, RECORDED</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-[-0.025em]">推进投递，而不是维护表格</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">状态更新会写入时间线，并同步到看板与近期安排。</p>
        </div>
        <Link href="/jobs" className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-foreground px-4 text-sm font-medium text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">发现更多岗位 <ArrowRight className="h-4 w-4" /></Link>
      </header>

      <section className="overflow-x-auto rounded-2xl border border-black/[0.07] bg-white px-5 py-6 dark:border-white/10 dark:bg-card" aria-label="投递状态概览">
        <div className="relative mx-auto flex min-w-[680px] items-start justify-between">
          <div className="absolute left-[5%] right-[5%] top-4 h-px bg-black/10 dark:bg-white/15" />
          {APPLICATION_STATUSES.slice(0, 5).map((status) => {
            const count = counts[status.code] || 0;
            return <div key={status.code} className="relative z-10 w-24 text-center"><span className={cn("mx-auto grid h-8 w-8 place-items-center rounded-full border-4 border-white text-[11px] font-semibold dark:border-card", count ? "bg-[#6366f1] text-white" : "bg-[#ececf0] text-muted-foreground dark:bg-white/10")}>{count}</span><p className="mt-2 text-[11px] font-medium">{status.label}</p></div>;
          })}
        </div>
      </section>

      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div className="inline-flex w-fit rounded-xl border border-black/[0.07] bg-white p-1 dark:border-white/10 dark:bg-card" role="tablist" aria-label="投递筛选">
          <FilterTab active={view === "all"} onClick={() => setView("all")}>全部 {applications.data?.length || 0}</FilterTab>
          <FilterTab active={view === "active"} onClick={() => setView("active")}>进行中 {(applications.data || []).filter((item) => !isTerminal(item.status)).length}</FilterTab>
          <FilterTab active={view === "closed"} onClick={() => setView("closed")}>已结束 {(applications.data || []).filter((item) => isTerminal(item.status)).length}</FilterTab>
        </div>

        {selected.size > 0 && (
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[#c7d2fe] bg-[#eef2ff] p-2 dark:border-indigo-800 dark:bg-indigo-950/50">
            <span className="px-2 text-xs text-[#4338ca] dark:text-indigo-300">已选 {selected.size} 项</span>
            <label className="relative">
              <span className="sr-only">批量目标状态</span>
              <select value={batchStatus} onChange={(event) => setBatchStatus(event.target.value)} className="min-h-11 appearance-none rounded-lg border border-[#c7d2fe] bg-white py-2 pl-3 pr-9 text-xs outline-none focus:ring-2 focus:ring-[#6366f1] dark:border-indigo-800 dark:bg-card">
                <option value="">选择目标状态</option>
                <option value="test">笔试/测评</option><option value="interviewing">面试中</option><option value="offer_pending">Offer 待决定</option><option value="rejected">公司拒绝</option><option value="withdrawn">主动撤回</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            </label>
            <button type="button" onClick={batchTransition} disabled={!batchStatus || batching} className="min-h-11 rounded-lg bg-[#4338ca] px-4 text-xs font-medium text-white disabled:opacity-50">{batching ? "更新中…" : "批量更新"}</button>
            <button type="button" onClick={() => setSelected(new Set())} className="min-h-11 px-3 text-xs text-muted-foreground">取消</button>
          </div>
        )}
      </div>

      {applications.loading ? <Loading /> : applications.error ? <ErrorState message={applications.error} onRetry={applications.reload} /> : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-black/10 bg-white py-8 dark:border-white/10 dark:bg-card"><EmptyState message="当前筛选下没有投递记录" /></div>
      ) : (
        <div className="space-y-3">
          {filtered.map((application) => {
            const next = getNextStatuses(application.status);
            const checked = selected.has(application.id);
            return (
              <article key={application.id} className={cn("grid items-center gap-4 rounded-2xl border bg-white p-4 transition-colors dark:bg-card md:grid-cols-[auto_1fr_auto_auto]", checked ? "border-[#a5b4fc] bg-[#f8f9ff] dark:border-indigo-700 dark:bg-indigo-950/20" : "border-black/[0.07] dark:border-white/10")}>
                <label className="grid h-11 w-11 cursor-pointer place-items-center rounded-lg hover:bg-black/[0.03] focus-within:ring-2 focus-within:ring-accent dark:hover:bg-white/[0.06]">
                  <span className="sr-only">选择 {application.job?.company || `投递 ${application.id}`}</span>
                  <input type="checkbox" checked={checked} onChange={() => toggle(application.id)} className="peer sr-only" />
                  <span className={cn("grid h-5 w-5 place-items-center rounded border", checked ? "border-[#6366f1] bg-[#6366f1] text-white" : "border-black/20 dark:border-white/20")}><Check className={cn("h-3.5 w-3.5", checked ? "opacity-100" : "opacity-0")} /></span>
                </label>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2"><Link href={`/applications/${application.id}`} className="font-semibold tracking-tight hover:text-[#4f46e5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">{application.job?.company || `岗位 #${application.job_id}`} · {application.job?.title || "投递记录"}</Link><StatusBadge status={application.status} /></div>
                  <p className="mt-1 text-xs text-muted-foreground">投递 #{application.id} · 最后更新 {formatDate(application.updated_at)}</p>
                </div>
                <Link href={`/applications/${application.id}`} className="inline-flex min-h-11 items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">查看时间线 <ArrowRight className="h-3.5 w-3.5" /></Link>
                {next.length ? (
                  <label className="relative min-w-[10rem]">
                    <span className="sr-only">更新 {application.job?.company || application.id} 的状态</span>
                    <select defaultValue="" disabled={busyId === application.id} onChange={(event) => { if (event.target.value) transition(application.id, event.target.value); event.target.value = ""; }} className="min-h-11 w-full appearance-none rounded-lg border border-black/10 bg-white py-2 pl-3 pr-9 text-xs outline-none focus:border-[#6366f1] focus:ring-2 focus:ring-[#6366f1]/15 disabled:opacity-50 dark:border-white/10 dark:bg-background">
                      <option value="">更新状态…</option>{next.map((status) => <option key={status} value={status}>{getStatusLabel(status)}</option>)}
                    </select><ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                  </label>
                ) : <span className="inline-flex min-h-11 items-center text-xs text-muted-foreground">流程已结束</span>}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

function FilterTab({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" role="tab" aria-selected={active} onClick={onClick} className={cn("min-h-10 rounded-lg px-4 text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent", active ? "bg-[#171719] font-medium text-white dark:bg-white dark:text-black" : "text-muted-foreground hover:text-foreground")}>{children}</button>;
}

function formatDate(value: string) { return value.slice(0, 16).replace("T", " "); }
