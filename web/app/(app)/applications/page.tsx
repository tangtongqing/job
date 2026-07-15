"use client";

import { useState } from "react";
import Link from "next/link";
import { api, type Application } from "@/lib/api";
import { Loading, ErrorState, EmptyState, useApi, StatusBadge } from "@/components/app/shared";
import { getNextStatuses, getStatusLabel } from "@/lib/status-config";
import { useToast } from "@/components/app/toast";

export default function ApplicationsPage() {
  const { toast } = useToast();
  const { data, loading, error, reload } = useApi<{ apps: Application[] }>(
    () => api.getApplications({ page: 1, page_size: 50 }).then((r) => ({ data: { apps: r.data } }))
  );
  const [transitioning, setTransitioning] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [batchStatus, setBatchStatus] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const handleTransition = async (id: number, toStatus: string) => {
    setTransitioning(id);
    setActionError(null);
    try {
      await api.transition(id, toStatus);
      toast(`已流转到「${getStatusLabel(toStatus)}」`);
      reload();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "状态流转失败";
      setActionError(msg);
      toast(msg, "error");
    } finally {
      setTransitioning(null);
    }
  };

  const handleBatch = async () => {
    if (!batchStatus || selected.size === 0) return;
    setActionError(null);
    try {
      const resp = await api.batchTransition([...selected], batchStatus);
      setSelected(new Set());
      setBatchStatus("");
      reload();
      if (resp.data.fail_count > 0) {
        const msg = `批量流转完成，${resp.data.success_count} 成功，${resp.data.fail_count} 失败`;
        setActionError(msg);
        toast(msg, "error");
      } else {
        toast(`批量流转 ${resp.data.success_count} 项成功`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "批量流转失败";
      setActionError(msg);
      toast(msg, "error");
    }
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-foreground">投递管理</h1>

      {/* 批量操作栏 */}
      {selected.size > 0 && (
        <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-secondary/40 px-4 py-2">
          <span className="text-xs text-muted-foreground">已选 {selected.size} 项</span>
          <select
            value={batchStatus}
            onChange={(e) => setBatchStatus(e.target.value)}
            className="rounded border border-border/60 bg-background px-2 py-1 text-xs"
          >
            <option value="">选择目标状态...</option>
            <option value="test">笔试/测评</option>
            <option value="interviewing">面试中</option>
            <option value="offer_pending">Offer待决定</option>
            <option value="rejected">拒绝</option>
            <option value="withdrawn">撤回</option>
          </select>
          <button
            onClick={handleBatch}
            disabled={!batchStatus}
            className="rounded bg-primary px-3 py-1 text-xs text-primary-foreground disabled:opacity-50"
          >
            批量流转
          </button>
          <button onClick={() => setSelected(new Set())} className="text-xs text-muted-foreground">
            取消
          </button>
        </div>
      )}

      {actionError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
          {actionError}
        </div>
      )}

      {/* 列表 */}
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : data && data.apps.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-border/60">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/60 text-left text-xs text-muted-foreground">
                <th className="px-3 py-2 font-normal w-8"></th>
                <th className="px-3 py-2 font-normal">投递</th>
                <th className="px-3 py-2 font-normal">岗位</th>
                <th className="px-3 py-2 font-normal">状态</th>
                <th className="px-3 py-2 font-normal">更新</th>
                <th className="px-3 py-2 font-normal text-right">流转</th>
              </tr>
            </thead>
            <tbody>
              {data.apps.map((app) => {
                const nextStatuses = getNextStatuses(app.status);
                return (
                  <tr key={app.id} className="border-b border-border/40 hover:bg-secondary/30">
                    <td className="px-3 py-2.5">
                      <input
                        type="checkbox"
                        checked={selected.has(app.id)}
                        onChange={() => toggleSelect(app.id)}
                        className="h-3.5 w-3.5"
                      />
                    </td>
                    <td className="px-3 py-2.5">
                      <Link href={`/applications/${app.id}`} className="text-foreground hover:underline">
                        #{app.id}
                      </Link>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="min-w-40">
                        <div className="font-medium text-foreground">
                          {app.job?.company || `岗位 #${app.job_id}`}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {app.job?.title || "未返回岗位详情"}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="px-3 py-2.5 text-xs text-muted-foreground">
                      {app.updated_at?.slice(0, 10)}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      {nextStatuses.length > 0 ? (
                        <select
                          defaultValue=""
                          onChange={(e) => {
                            if (e.target.value) handleTransition(app.id, e.target.value);
                            e.target.value = "";
                          }}
                          disabled={transitioning === app.id}
                          className="rounded border border-border/60 bg-background px-2 py-1 text-xs disabled:opacity-50"
                        >
                          <option value="">选择...</option>
                          {nextStatuses.map((s) => (
                            <option key={s} value={s}>{getStatusLabel(s)}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="text-xs text-muted-foreground">终态</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState message="暂无投递记录，去岗位页创建投递吧" />
      )}
    </div>
  );
}
