"use client";

import { useState } from "react";
import { api, type CrawlLog } from "@/lib/api";
import { Loading, ErrorState, EmptyState, useApi } from "@/components/app/shared";
import { RefreshCw, AlertTriangle } from "lucide-react";
import { useToast } from "@/components/app/toast";

const STATUS_LABELS: Record<string, string> = {
  success: "成功",
  failed: "失败",
  skipped: "跳过",
};

const STATUS_COLORS: Record<string, string> = {
  success: "text-green-600",
  failed: "text-red-500",
  skipped: "text-muted-foreground",
};

export default function CrawlerPage() {
  const { toast } = useToast();
  const { data, loading, error, reload } = useApi<{ logs: CrawlLog[] }>(
    () => api.getCrawlLogs(1, 20).then((r) => ({ data: { logs: r.data } }))
  );
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState<string | null>(null);

  const handleTrigger = async (source: string) => {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const resp = await api.triggerCrawl(source);
      const d = resp.data;
      const msg = `${d.source}: ${STATUS_LABELS[d.status] || d.status}，采集 ${d.count} 条`;
      setTriggerResult(msg);
      toast(d.status === "success" ? `采集完成：${d.count} 条` : `采集${STATUS_LABELS[d.status] || d.status}`, d.status === "success" ? "success" : "error");
      reload();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "触发失败";
      setTriggerResult(msg);
      toast(msg, "error");
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-xl font-semibold text-foreground">采集管理</h1>

      {/* 触发区 */}
      <div className="rounded-xl border border-border/60 bg-card p-4">
        <h2 className="mb-3 text-sm font-medium text-foreground">手动触发采集</h2>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleTrigger("company")}
            disabled={triggering}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${triggering ? "animate-spin" : ""}`} />
            企业官网
          </button>
          <button
            disabled
            className="inline-flex items-center gap-1.5 rounded-lg border border-border/60 px-3 py-1.5 text-xs text-muted-foreground opacity-60 cursor-not-allowed"
            title="高风险源，robots fail-closed 将跳过"
          >
            BOSS（不可用，将跳过）
          </button>
          <button
            disabled
            className="inline-flex items-center gap-1.5 rounded-lg border border-border/60 px-3 py-1.5 text-xs text-muted-foreground opacity-60 cursor-not-allowed"
            title="高风险源，robots fail-closed 将跳过"
          >
            牛客（不可用，将跳过）
          </button>
        </div>
        {triggerResult && (
          <p className="mt-2 text-xs text-muted-foreground">{triggerResult}</p>
        )}
      </div>

      {/* 合规提示 */}
      <div className="flex items-start gap-2 rounded-lg bg-secondary/40 p-3">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-yellow-600 dark:text-yellow-400 mt-0.5" />
        <p className="text-xs text-muted-foreground">
          BOSS/牛客为高风险源，默认禁用。触发时若 robots.txt 无法确认允许，将安全跳过。
          不做登录、验证码绕过或反爬规避。
        </p>
      </div>

      {/* 日志 */}
      <div className="rounded-xl border border-border/60 bg-card p-4">
        <h2 className="mb-3 text-sm font-medium text-foreground">采集日志</h2>
        {loading ? (
          <Loading />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : data && data.logs.length > 0 ? (
          <div className="space-y-2">
            {data.logs.map((log) => (
              <div key={log.id} className="flex items-center justify-between border-b border-border/40 py-2 text-sm last:border-0">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground">{log.source}</span>
                  <span className={`text-xs font-medium ${STATUS_COLORS[log.status] || "text-muted-foreground"}`}>
                    {STATUS_LABELS[log.status] || log.status}
                  </span>
                  <span className="text-xs text-muted-foreground">{log.count} 条</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {log.finished_at?.slice(0, 16).replace("T", " ") || "-"}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="暂无采集日志" />
        )}
      </div>
    </div>
  );
}
