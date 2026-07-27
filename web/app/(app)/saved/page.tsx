"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Bookmark, BriefcaseBusiness, MapPin, Send, Trash2 } from "lucide-react";

import { EmptyState, ErrorState, Loading, useApi } from "@/components/app/shared";
import { useToast } from "@/components/app/toast";
import { api, type SavedJob } from "@/lib/api";
import { cn } from "@/lib/utils";

type SavedTab = "favorites" | "to_apply";

export default function SavedPage() {
  const { toast } = useToast();
  const [tab, setTab] = useState<SavedTab>("favorites");
  const [busyId, setBusyId] = useState<number | null>(null);
  const saved = useApi<{ favorites: SavedJob[]; toApply: SavedJob[] }>(() =>
    Promise.all([api.getFavorites(), api.getToApply()]).then(([favorites, toApply]) => ({
      data: { favorites: favorites.data, toApply: toApply.data },
    }))
  );

  const items = useMemo(
    () => (tab === "favorites" ? saved.data?.favorites : saved.data?.toApply) || [],
    [saved.data, tab]
  );
  const toApplyJobIds = useMemo(
    () => new Set((saved.data?.toApply || []).map((item) => item.job_id)),
    [saved.data?.toApply]
  );

  const remove = async (item: SavedJob) => {
    setBusyId(item.id);
    try {
      if (item.action_type === "favorited") await api.unfavoriteJob(item.job_id);
      else await api.removeToApply(item.job_id);
      toast(item.action_type === "favorited" ? "已取消收藏" : "已移出待投递");
      saved.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "操作失败", "error");
    } finally {
      setBusyId(null);
    }
  };

  const moveToApply = async (item: SavedJob) => {
    setBusyId(item.id);
    try {
      await api.markToApply(item.job_id);
      toast("已加入待投递");
      setTab("to_apply");
      saved.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "操作失败", "error");
    } finally {
      setBusyId(null);
    }
  };

  const createApplication = async (item: SavedJob) => {
    setBusyId(item.id);
    try {
      const response = await api.createApplication(item.job_id, "从待投递清单创建");
      toast("投递记录已创建");
      window.location.href = `/applications/${response.data.id}`;
    } catch (error) {
      toast(error instanceof Error ? error.message : "创建投递失败", "error");
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-medium text-[#4f46e5]">SAVE → DECIDE → APPLY</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-[-0.025em]">把心动岗位变成下一步</h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted-foreground">
            收藏用于保留可能性，待投递用于明确行动。两类清单彼此独立。
          </p>
        </div>
        <Link
          href="/jobs"
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-foreground px-4 text-sm font-medium text-background transition-colors hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <BriefcaseBusiness className="h-4 w-4" />
          继续发现岗位
        </Link>
      </header>

      <div className="inline-flex rounded-xl border border-black/[0.07] bg-white p-1 dark:border-white/10 dark:bg-card" role="tablist" aria-label="收藏分类">
        <TabButton active={tab === "favorites"} onClick={() => setTab("favorites")} count={saved.data?.favorites.length || 0}>
          收藏
        </TabButton>
        <TabButton active={tab === "to_apply"} onClick={() => setTab("to_apply")} count={saved.data?.toApply.length || 0}>
          待投递
        </TabButton>
      </div>

      {saved.loading ? (
        <Loading text="正在整理清单…" />
      ) : saved.error ? (
        <ErrorState message={saved.error} onRetry={saved.reload} />
      ) : items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-black/10 bg-white py-8 dark:border-white/10 dark:bg-card">
          <EmptyState message={tab === "favorites" ? "还没有收藏岗位" : "还没有待投递岗位"} />
        </div>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {items.map((item) => (
            <article key={item.id} className="group rounded-2xl border border-black/[0.07] bg-white p-5 transition-[border-color,transform] duration-200 hover:-translate-y-0.5 hover:border-black/15 dark:border-white/10 dark:bg-card dark:hover:border-white/20">
              <div className="flex items-start gap-4">
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#f2f2f4] text-sm font-semibold text-foreground dark:bg-white/10">
                  {item.job.company.slice(0, 1)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-muted-foreground">{item.job.company}</p>
                      <h2 className="mt-0.5 font-semibold tracking-tight">{item.job.title}</h2>
                    </div>
                    <span className="shrink-0 rounded-full bg-[#f3f4f6] px-2.5 py-1 text-[11px] text-muted-foreground dark:bg-white/10">
                      {item.job.source}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{item.job.location || "地点待确认"}</span>
                    <span>{item.job.salary || "薪资面议"}</span>
                    <span>截止 {item.job.deadline?.slice(5, 10) || "待确认"}</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-black/[0.06] pt-4 dark:border-white/10">
                <Link href={`/jobs/${item.job_id}`} className="inline-flex min-h-11 items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">
                  查看岗位 <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => remove(item)}
                    disabled={busyId === item.id}
                    aria-label={item.action_type === "favorited" ? "取消收藏" : "移出待投递"}
                    className="grid h-11 w-11 place-items-center rounded-lg border border-black/[0.08] text-muted-foreground hover:bg-black/[0.03] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50 dark:border-white/10 dark:hover:bg-white/[0.06]"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                  {item.action_type === "favorited" && toApplyJobIds.has(item.job_id) ? (
                    <button type="button" onClick={() => setTab("to_apply")} className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-black/[0.08] px-4 text-xs font-medium text-foreground hover:bg-black/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent dark:border-white/10 dark:hover:bg-white/[0.06]">
                      <Bookmark className="h-4 w-4" /> 查看待投递
                    </button>
                  ) : item.action_type === "favorited" ? (
                    <button type="button" onClick={() => moveToApply(item)} disabled={busyId === item.id} className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-[#eef2ff] px-4 text-xs font-medium text-[#4338ca] hover:bg-[#e0e7ff] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50 dark:bg-indigo-950 dark:text-indigo-300">
                      <Bookmark className="h-4 w-4" /> 加入待投递
                    </button>
                  ) : (
                    <button type="button" onClick={() => createApplication(item)} disabled={busyId === item.id} className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-foreground px-4 text-xs font-medium text-background hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50">
                      <Send className="h-4 w-4" /> 创建投递
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function TabButton({ active, onClick, count, children }: { active: boolean; onClick: () => void; count: number; children: React.ReactNode }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={cn(
        "inline-flex min-h-10 items-center gap-2 rounded-lg px-4 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        active ? "bg-[#111113] font-medium text-white dark:bg-white dark:text-black" : "text-muted-foreground hover:text-foreground"
      )}
    >
      {children}
      <span className={cn("rounded-full px-1.5 py-0.5 text-[10px]", active ? "bg-white/15 dark:bg-black/10" : "bg-black/[0.05] dark:bg-white/10")}>{count}</span>
    </button>
  );
}
