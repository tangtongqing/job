"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Bookmark, Check, ChevronLeft, ChevronRight, MapPin, Search, Send, ShieldCheck } from "lucide-react";

import { EmptyState, ErrorState, Loading, useApi } from "@/components/app/shared";
import { useToast } from "@/components/app/toast";
import { api, type Job } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function JobsPage() {
  const { toast } = useToast();
  const [keyword, setKeyword] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [page, setPage] = useState(1);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const jobs = useApi<{ jobs: Job[]; total: number }>(
    () => api.getJobs({ keyword, company, location, page, page_size: 20 }).then((response) => ({ data: { jobs: response.data, total: response.meta?.total ?? 0 } })),
    [keyword, company, location, page]
  );
  const saved = useApi<{ favorites: number[]; toApply: number[] }>(() =>
    Promise.all([api.getFavorites(), api.getToApply()]).then(([favorites, toApply]) => ({
      data: {
        favorites: favorites.data.map((item) => item.job_id),
        toApply: toApply.data.map((item) => item.job_id),
      },
    }))
  );

  const favoriteIds = useMemo(() => new Set(saved.data?.favorites || []), [saved.data]);
  const toApplyIds = useMemo(() => new Set(saved.data?.toApply || []), [saved.data]);

  const toggleFavorite = async (job: Job) => {
    const active = favoriteIds.has(job.id);
    setBusyKey(`favorite-${job.id}`);
    try {
      if (active) await api.unfavoriteJob(job.id);
      else await api.favoriteJob(job.id);
      toast(active ? "已取消收藏" : `已收藏 ${job.company} · ${job.title}`);
      saved.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "收藏操作失败", "error");
    } finally {
      setBusyKey(null);
    }
  };

  const toggleToApply = async (job: Job) => {
    const active = toApplyIds.has(job.id);
    setBusyKey(`apply-${job.id}`);
    try {
      if (active) await api.removeToApply(job.id);
      else await api.markToApply(job.id);
      toast(active ? "已移出待投递" : `已加入待投递：${job.company}`);
      saved.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "待投递操作失败", "error");
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-xs font-medium text-[#4f46e5]">ONE SEARCH, ONE INBOX</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-[-0.025em]">找到值得投入时间的岗位</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">聚合结果保留来源与更新时间，你来决定收藏还是立刻行动。</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          {jobs.data?.total ?? 0} 个有效岗位
        </div>
      </header>

      <section className="grid gap-3 rounded-2xl border border-black/[0.07] bg-white p-4 md:grid-cols-[1.5fr_1fr_1fr] dark:border-white/10 dark:bg-card" aria-label="岗位筛选">
        <FilterField label="搜索岗位或描述" icon={Search} value={keyword} placeholder="产品经理、AI、增长…" onChange={(value) => { setKeyword(value); setPage(1); }} />
        <FilterField label="公司" value={company} placeholder="输入公司名称" onChange={(value) => { setCompany(value); setPage(1); }} />
        <FilterField label="地点" icon={MapPin} value={location} placeholder="北京、上海、深圳…" onChange={(value) => { setLocation(value); setPage(1); }} />
      </section>

      {jobs.loading || saved.loading ? (
        <Loading text="正在汇总最新岗位…" />
      ) : jobs.error ? (
        <ErrorState message={jobs.error} onRetry={jobs.reload} />
      ) : saved.error ? (
        <ErrorState message={saved.error} onRetry={saved.reload} />
      ) : jobs.data && jobs.data.jobs.length > 0 ? (
        <>
          <div className="hidden overflow-hidden rounded-2xl border border-black/[0.07] bg-white md:block dark:border-white/10 dark:bg-card">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#fafafa] text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground dark:bg-white/[0.025]">
                <tr>
                  <th className="px-5 py-3 font-medium">岗位</th>
                  <th className="px-4 py-3 font-medium">地点 / 薪资</th>
                  <th className="px-4 py-3 font-medium">来源 / 更新</th>
                  <th className="px-5 py-3 text-right font-medium">加入工作流</th>
                </tr>
              </thead>
              <tbody>
                {jobs.data.jobs.map((job) => (
                  <tr key={job.id} className="border-t border-black/[0.055] transition-colors hover:bg-[#fafafa] dark:border-white/[0.07] dark:hover:bg-white/[0.025]">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <CompanyMark name={job.company} />
                        <div className="min-w-0">
                          <Link href={`/jobs/${job.id}`} className="font-semibold tracking-tight hover:text-[#4f46e5] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">{job.title}</Link>
                          <p className="mt-0.5 text-xs text-muted-foreground">{job.company}{job.is_fresh ? " · 今日活跃" : ""}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <p className="text-xs text-foreground">{job.location || "地点待确认"}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{job.salary || "薪资面议"}</p>
                    </td>
                    <td className="px-4 py-4">
                      <p className="inline-flex items-center gap-1 text-xs"><ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />{sourceLabel(job.source)}</p>
                      <p className="mt-1 text-[11px] text-muted-foreground">{relativeCollectedAt(job.collected_at)}</p>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <WorkflowButton label={favoriteIds.has(job.id) ? "已收藏" : "收藏"} active={favoriteIds.has(job.id)} busy={busyKey === `favorite-${job.id}`} icon={Bookmark} onClick={() => toggleFavorite(job)} />
                        <WorkflowButton label={toApplyIds.has(job.id) ? "待投递" : "加入待投递"} active={toApplyIds.has(job.id)} busy={busyKey === `apply-${job.id}`} icon={Send} onClick={() => toggleToApply(job)} primary />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-3 md:hidden">
            {jobs.data.jobs.map((job) => (
              <article key={job.id} className="rounded-2xl border border-black/[0.07] bg-white p-4 dark:border-white/10 dark:bg-card">
                <div className="flex items-start gap-3">
                  <CompanyMark name={job.company} />
                  <div className="min-w-0 flex-1">
                    <Link href={`/jobs/${job.id}`} className="font-semibold tracking-tight">{job.title}</Link>
                    <p className="mt-0.5 text-xs text-muted-foreground">{job.company} · {job.location || "地点待确认"}</p>
                    <p className="mt-2 text-xs">{job.salary || "薪资面议"}</p>
                  </div>
                  <span className="rounded-full bg-[#f3f4f6] px-2 py-1 text-[10px] text-muted-foreground dark:bg-white/10">{sourceLabel(job.source)}</span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 border-t border-black/[0.06] pt-3 dark:border-white/10">
                  <WorkflowButton label={favoriteIds.has(job.id) ? "已收藏" : "收藏"} active={favoriteIds.has(job.id)} busy={busyKey === `favorite-${job.id}`} icon={Bookmark} onClick={() => toggleFavorite(job)} />
                  <WorkflowButton label={toApplyIds.has(job.id) ? "待投递" : "加入待投递"} active={toApplyIds.has(job.id)} busy={busyKey === `apply-${job.id}`} icon={Send} onClick={() => toggleToApply(job)} primary />
                </div>
              </article>
            ))}
          </div>
        </>
      ) : (
        <div className="rounded-2xl border border-dashed border-black/10 bg-white py-8 dark:border-white/10 dark:bg-card"><EmptyState message="没有符合当前条件的岗位" /></div>
      )}

      {jobs.data && jobs.data.total > 20 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>第 {page} 页 · 共 {jobs.data.total} 个岗位</span>
          <div className="flex gap-2">
            <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1} className="grid h-11 w-11 place-items-center rounded-lg border border-black/10 bg-white disabled:opacity-40 dark:border-white/10 dark:bg-card" aria-label="上一页"><ChevronLeft className="h-4 w-4" /></button>
            <button type="button" onClick={() => setPage((current) => current + 1)} disabled={page * 20 >= jobs.data.total} className="grid h-11 w-11 place-items-center rounded-lg border border-black/10 bg-white disabled:opacity-40 dark:border-white/10 dark:bg-card" aria-label="下一页"><ChevronRight className="h-4 w-4" /></button>
          </div>
        </div>
      )}
    </div>
  );
}

function FilterField({ label, icon: Icon, value, placeholder, onChange }: { label: string; icon?: React.ComponentType<{ className?: string }>; value: string; placeholder: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="text-[11px] font-medium text-muted-foreground">{label}</span>
      <span className="mt-1.5 flex min-h-11 items-center gap-2 rounded-lg border border-black/[0.08] bg-[#fafafa] px-3 focus-within:border-[#6366f1] focus-within:ring-2 focus-within:ring-[#6366f1]/15 dark:border-white/10 dark:bg-background">
        {Icon && <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />}
        <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/60" />
      </span>
    </label>
  );
}

function CompanyMark({ name }: { name: string }) {
  return <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#f0f0f2] text-sm font-semibold dark:bg-white/10">{name.slice(0, 1)}</span>;
}

function WorkflowButton({ label, active, busy, icon: Icon, onClick, primary = false }: { label: string; active: boolean; busy: boolean; icon: React.ComponentType<{ className?: string }>; onClick: () => void; primary?: boolean }) {
  return (
    <button type="button" onClick={onClick} disabled={busy} aria-pressed={active} className={cn("inline-flex min-h-11 items-center justify-center gap-1.5 rounded-lg border px-3 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50", active ? "border-[#c7d2fe] bg-[#eef2ff] text-[#4338ca] dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-300" : primary ? "border-foreground bg-foreground text-background hover:opacity-90" : "border-black/10 bg-white text-foreground hover:bg-black/[0.03] dark:border-white/10 dark:bg-card dark:hover:bg-white/[0.06]") }>
      {active ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
      {busy ? "处理中…" : label}
    </button>
  );
}

function relativeCollectedAt(value: string | null) {
  if (!value) return "更新时间未知";
  const hours = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 3600000));
  if (hours < 1) return "刚刚更新";
  if (hours < 24) return `${hours} 小时前更新`;
  return `${Math.floor(hours / 24)} 天前更新`;
}

function sourceLabel(source: string) {
  if (source === "demo_snapshot") return "演示快照";
  if (source.startsWith("greenhouse_")) return `${source.replace("greenhouse_", "")} 公开 API`;
  return source;
}
