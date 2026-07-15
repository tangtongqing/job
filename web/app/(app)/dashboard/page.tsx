"use client";

import { api, type KPI, type FunnelItem, type TrendPoint, type DistributionItem } from "@/lib/api";
import { FUNNEL_ORDER, getStatusLabel } from "@/lib/status-config";
import { Loading, ErrorState, EmptyState, useApi } from "@/components/app/shared";
import { TrendingUp, Briefcase, Send, Clock } from "lucide-react";

export default function DashboardPage() {
  const kpi = useApi<{ today_new_jobs: number; total_jobs: number; total_applications: number; pending_applications: number }>(
    () => api.getKPI().then((r) => ({ data: r.data }))
  );
  const funnel = useApi<{ funnel: FunnelItem[]; total_applications: number }>(
    () => api.getFunnel()
  );
  const trend = useApi<{ trend: TrendPoint[]; total: number }>(
    () => api.getTrend(7)
  );
  const dist = useApi<{ distribution: DistributionItem[]; total: number }>(
    () => api.getDistribution("job_category")
  );

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-foreground">看板</h1>

      {/* KPI 卡片行 */}
      {kpi.loading ? (
        <Loading />
      ) : kpi.error ? (
        <ErrorState message={kpi.error} onRetry={kpi.reload} />
      ) : kpi.data ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <KpiCard icon={Briefcase} label="今日新增岗位" value={kpi.data.today_new_jobs} />
          <KpiCard icon={Briefcase} label="岗位总数" value={kpi.data.total_jobs} />
          <KpiCard icon={Send} label="投递总数" value={kpi.data.total_applications} />
          <KpiCard icon={Clock} label="待处理投递" value={kpi.data.pending_applications} />
        </div>
      ) : null}

      {/* 漏斗 + 趋势 并排 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* 漏斗 */}
        <div className="rounded-xl border border-border/60 bg-card p-5">
          <h2 className="mb-4 text-sm font-medium text-foreground">投递漏斗</h2>
          {funnel.loading ? (
            <Loading />
          ) : funnel.error ? (
            <ErrorState message={funnel.error} onRetry={funnel.reload} />
          ) : funnel.data && funnel.data.funnel.length > 0 ? (
            <div className="space-y-2">
              {funnel.data.funnel.map((item) => {
                const maxCount = Math.max(...funnel.data!.funnel.map((f) => f.count), 1);
                const widthPct = (item.count / maxCount) * 100;
                return (
                  <div key={item.status} className="flex items-center gap-3">
                    <span className="w-24 shrink-0 text-xs text-muted-foreground">
                      {getStatusLabel(item.status)}
                    </span>
                    <div className="flex-1">
                      <div
                        className="h-7 rounded bg-primary/20 flex items-center justify-end px-2"
                        style={{ width: `${Math.max(widthPct, 10)}%` }}
                      >
                        <span className="text-xs font-medium text-foreground">{item.count}</span>
                      </div>
                    </div>
                    <span className="w-12 text-right text-xs text-muted-foreground">
                      {(item.rate * 100).toFixed(0)}%
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyState message="暂无投递数据" />
          )}
        </div>

        {/* 趋势 */}
        <div className="rounded-xl border border-border/60 bg-card p-5">
          <div className="mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-medium text-foreground">近 7 天有效进展</h2>
          </div>
          {trend.loading ? (
            <Loading />
          ) : trend.error ? (
            <ErrorState message={trend.error} onRetry={trend.reload} />
          ) : trend.data && trend.data.trend.length > 0 ? (
            <TrendChart points={trend.data.trend} />
          ) : (
            <EmptyState message="暂无趋势数据" />
          )}
        </div>
      </div>

      {/* 分布 */}
      <div className="rounded-xl border border-border/60 bg-card p-5">
        <h2 className="mb-4 text-sm font-medium text-foreground">岗位类型分布</h2>
        {dist.loading ? (
          <Loading />
        ) : dist.error ? (
          <ErrorState message={dist.error} onRetry={dist.reload} />
        ) : dist.data && dist.data.distribution.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {dist.data.distribution.map((item) => (
              <div
                key={item.label}
                className="rounded-lg border border-border/60 px-3 py-2 text-xs"
              >
                <span className="text-muted-foreground">{item.label}</span>
                <span className="ml-2 font-medium text-foreground">{item.count}</span>
                <span className="ml-1 text-muted-foreground">
                  ({(item.rate * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="暂无分布数据" />
        )}
      </div>
    </div>
  );
}

function KpiCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="mt-1.5 text-2xl font-semibold text-foreground tabular-nums">
        {value}
      </div>
    </div>
  );
}

function TrendChart({ points }: { points: TrendPoint[] }) {
  const maxCount = Math.max(...points.map((p) => p.count), 1);
  return (
    <div className="flex items-end gap-1 h-36">
      {points.map((p, i) => (
        <div key={p.date} className="flex flex-1 flex-col items-center gap-1 group">
          <div className="relative flex w-full justify-center" style={{ height: `${(p.count / maxCount) * 100}%`, minHeight: p.count > 0 ? "4px" : "0" }}>
            <div className="w-full rounded-t bg-primary/40 group-hover:bg-primary/70 transition-colors h-full" />
            {/* hover tooltip */}
            <div className="pointer-events-none absolute -top-7 hidden whitespace-nowrap rounded bg-foreground px-1.5 py-0.5 text-[10px] text-background group-hover:block z-10">
              {p.count} ({p.date.slice(5)})
            </div>
          </div>
          {/* 隔行显示日期标签，避免 390px 拥挤 */}
          {(points.length <= 7 || i % 2 === 0) && (
            <span className="text-[9px] text-muted-foreground">{p.date.slice(5)}</span>
          )}
        </div>
      ))}
    </div>
  );
}
