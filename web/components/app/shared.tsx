"use client";

/**
 * 产品面共享 UI 组件：StatusBadge / Loading / ErrorState / EmptyState。
 */

import { useEffect, useState } from "react";
import { Loader2, AlertCircle, Inbox } from "lucide-react";
import { getStatusConfig } from "@/lib/status-config";
import { ApiRequestError, API_BASE_URL } from "@/lib/api";

// ---------- Status Badge ----------

export function StatusBadge({ status }: { status: string }) {
  const cfg = getStatusConfig(status);
  if (!cfg) {
    return <span className="text-xs text-muted-foreground">{status}</span>;
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cfg.badgeClass}`}>
      {cfg.label}
    </span>
  );
}

// ---------- Loading ----------

export function Loading({ text = "加载中..." }: { text?: string }) {
  return (
    <div className="flex items-center justify-center py-12 text-muted-foreground">
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      {text}
    </div>
  );
}

// ---------- Error ----------

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <AlertCircle className="mb-2 h-8 w-8 text-red-500" />
      <p className="text-sm text-foreground">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded-md border border-border px-3 py-1 text-xs text-foreground hover:bg-secondary"
        >
          重试
        </button>
      )}
    </div>
  );
}

// ---------- Empty ----------

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
      <Inbox className="mb-2 h-8 w-8 opacity-50" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

// ---------- API Status ----------

export function ApiConnectionStatus({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE_URL}/dashboard/kpi`, { cache: "no-store" })
      .then((resp) => {
        if (!cancelled) setStatus(resp.ok ? "online" : "offline");
      })
      .catch(() => {
        if (!cancelled) setStatus("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const label =
    status === "checking" ? "API 检查中" : status === "online" ? "API 在线" : "API 离线";
  const dot =
    status === "checking" ? "bg-yellow-500" : status === "online" ? "bg-green-500" : "bg-red-500";

  return (
    <span
      className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border/60 px-2 py-1 text-[11px] text-muted-foreground"
      title={API_BASE_URL}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {compact ? label.replace("API ", "") : label}
    </span>
  );
}

// ---------- API Hook ----------

export function useApi<T>(
  fetcher: () => Promise<{ data: T }>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetcher()
      .then((resp) => setData(resp.data))
      .catch((e) => {
        setError(e instanceof ApiRequestError ? e.message : "请求失败");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, reload: load };
}
