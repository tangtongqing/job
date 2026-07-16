"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, Database, Radio, RefreshCw, ShieldCheck } from "lucide-react";

import { EmptyState, ErrorState, Loading, useApi } from "@/components/app/shared";
import { useToast } from "@/components/app/toast";
import { api, type CrawlLog, type CrawlSource, type JobStats } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  success: "成功",
  failed: "失败",
  skipped: "说明",
};

const QUALITY_FIELDS = [
  ["jd", "完整 JD"],
  ["requirement", "岗位要求"],
  ["apply_url", "投递链接"],
  ["last_verified_at", "核验时间"],
] as const;

export default function CrawlerPage() {
  const { toast } = useToast();
  const overview = useApi<{ logs: CrawlLog[]; sources: CrawlSource[]; stats: JobStats }>(() =>
    Promise.all([api.getCrawlLogs(1, 20), api.getCrawlSources(), api.getJobStats()]).then(
      ([logs, sources, stats]) => ({ data: { logs: logs.data, sources: sources.data, stats: stats.data } })
    )
  );
  const [triggeringSource, setTriggeringSource] = useState<string | null>(null);

  const handleTrigger = async (source: CrawlSource) => {
    setTriggeringSource(source.name);
    try {
      const response = await api.triggerCrawl(source.name);
      const result = response.data;
      const label = STATUS_LABELS[result.status] || result.status;
      toast(
        result.status === "success"
          ? `${source.label} 采集完成：新增 ${result.count} 条`
          : `${source.label}：${label}`,
        result.status === "success" ? "success" : "error"
      );
      overview.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "触发失败", "error");
    } finally {
      setTriggeringSource(null);
    }
  };

  if (overview.loading) return <Loading text="正在检查数据源…" />;
  if (overview.error || !overview.data) return <ErrorState message={overview.error || "数据加载失败"} onRetry={overview.reload} />;

  const { logs, sources, stats } = overview.data;
  const enabledSources = sources.filter((source) => source.enabled);
  const restrictedSources = sources.filter((source) => source.kind === "restricted_platform");

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-xs font-medium text-[#4f46e5]">PUBLIC DATA, CLEAR PROVENANCE</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-[-0.025em]">采集管理</h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted-foreground">
            真实源使用企业公开招聘 API；演示快照与网络采集分开计数，不伪装实时结果。
          </p>
        </div>
        <div className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
          <Radio className="h-3.5 w-3.5" />
          {enabledSources.length} 个公开源已配置
        </div>
      </header>

      <section className="grid gap-3 sm:grid-cols-3" aria-label="数据类型概览">
        <SummaryCard label="岗位总数" value={stats.total} note="当前可浏览" icon={Database} />
        <SummaryCard label="演示快照" value={stats.demo_count} note="断网也可演示" icon={ShieldCheck} />
        <SummaryCard label="真实采集" value={stats.live_count} note="来自公开 API" icon={CheckCircle2} />
      </section>

      <section className="rounded-2xl border border-black/[0.07] bg-white p-5 dark:border-white/10 dark:bg-card">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold">字段完整度</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">用实际入库数据计算，不使用固定展示数字。</p>
          </div>
          <span className="text-xs tabular-nums text-muted-foreground">{stats.total} 条样本</span>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {QUALITY_FIELDS.map(([field, label]) => {
            const quality = stats.field_completeness[field] || { count: 0, percentage: 0 };
            return (
              <div key={field}>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-medium tabular-nums">{quality.percentage}%</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/10">
                  <div className="h-full rounded-full bg-[#6366f1]" style={{ width: `${quality.percentage}%` }} />
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">{quality.count} / {stats.total} 条</p>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-end justify-between">
          <div>
            <h2 className="text-sm font-semibold">公开招聘源</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">Greenhouse Job Board API · 无需登录</p>
          </div>
          <button type="button" onClick={() => overview.reload()} className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-black/10 px-3 text-xs font-medium hover:bg-black/[0.03] dark:border-white/10 dark:hover:bg-white/[0.05]">
            <RefreshCw className="h-3.5 w-3.5" />刷新状态
          </button>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {enabledSources.map((source) => (
            <article key={source.name} className="rounded-2xl border border-black/[0.07] bg-white p-5 dark:border-white/10 dark:bg-card">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#eef2ff] text-sm font-semibold text-[#4f46e5] dark:bg-indigo-950 dark:text-indigo-300">{source.label.slice(0, 1)}</span>
                    <div><h3 className="text-sm font-semibold">{source.label}</h3><p className="text-[11px] text-muted-foreground">{source.adapter} · {source.name}</p></div>
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {source.last_run ? `上次${STATUS_LABELS[source.last_run.status] || source.last_run.status}，新增 ${source.last_run.count} 条` : "尚未运行真实采集"}
                  </p>
                </div>
                <button type="button" onClick={() => handleTrigger(source)} disabled={triggeringSource !== null} className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-lg bg-foreground px-3 text-xs font-medium text-background hover:opacity-90 disabled:opacity-50">
                  <RefreshCw className={`h-3.5 w-3.5 ${triggeringSource === source.name ? "animate-spin" : ""}`} />
                  {triggeringSource === source.name ? "采集中" : "立即采集"}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950/30">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        <p className="text-xs leading-5 text-amber-800 dark:text-amber-300">
          {restrictedSources.map((source) => source.label).join(" / ")} 属于高风险平台源，继续禁用。JobPulse 不登录抓取，不绕过验证码或反爬限制。
        </p>
      </div>

      <section className="rounded-2xl border border-black/[0.07] bg-white p-5 dark:border-white/10 dark:bg-card">
        <h2 className="text-sm font-semibold">采集日志</h2>
        {logs.length > 0 ? (
          <div className="mt-3 divide-y divide-black/[0.06] dark:divide-white/10">
            {logs.map((log) => (
              <div key={log.id} className="py-3">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-2"><span className="font-medium">{log.source === "demo_snapshot" ? "演示快照" : log.source}</span><span className="rounded-full bg-black/[0.05] px-2 py-0.5 text-muted-foreground dark:bg-white/10">{STATUS_LABELS[log.status] || log.status}</span><span className="tabular-nums text-muted-foreground">{log.count} 条</span></div>
                  <span className="text-muted-foreground">{log.finished_at?.slice(0, 16).replace("T", " ") || "-"}</span>
                </div>
                {log.error && <p className="mt-1.5 text-[11px] leading-5 text-muted-foreground">{log.error}</p>}
              </div>
            ))}
          </div>
        ) : <div className="mt-3"><EmptyState message="尚未运行真实采集" /></div>}
      </section>
    </div>
  );
}

function SummaryCard({ label, value, note, icon: Icon }: { label: string; value: number; note: string; icon: React.ComponentType<{ className?: string }> }) {
  return <article className="rounded-2xl border border-black/[0.07] bg-white p-5 dark:border-white/10 dark:bg-card"><div className="flex items-center justify-between"><span className="text-xs text-muted-foreground">{label}</span><Icon className="h-4 w-4 text-[#6366f1]" /></div><p className="mt-3 text-3xl font-semibold tabular-nums tracking-tight">{value}</p><p className="mt-1 text-[11px] text-muted-foreground">{note}</p></article>;
}
