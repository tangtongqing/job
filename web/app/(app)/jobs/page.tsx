"use client";

import { useState } from "react";
import Link from "next/link";
import { api, type Job } from "@/lib/api";
import { Loading, ErrorState, EmptyState, useApi } from "@/components/app/shared";
import { JOB_STATUS_LABELS } from "@/lib/status-config";
import { Search, ShieldCheck } from "lucide-react";

export default function JobsPage() {
  const [keyword, setKeyword] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [jobCategory, setJobCategory] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [verifying, setVerifying] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, loading, error, reload } = useApi<{ jobs: Job[]; total: number }>(
    () => api.getJobs({
      keyword,
      company,
      location,
      job_category: jobCategory,
      status,
      page,
      page_size: 20,
    }).then((r) => ({ data: { jobs: r.data, total: r.meta?.total ?? 0 } })),
    [keyword, company, location, jobCategory, status, page]
  );

  const handleVerify = async (id: number) => {
    setVerifying(id);
    setActionError(null);
    try {
      await api.verifyJob(id);
      reload();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : "岗位核验失败");
    } finally {
      setVerifying(null);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-foreground">岗位</h1>

      {/* 筛选栏 */}
      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-1.5 rounded-lg border border-border/60 px-3 py-1.5">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={keyword}
            onChange={(e) => { setKeyword(e.target.value); setPage(1); }}
            placeholder="关键词"
            className="bg-transparent text-sm outline-none w-32 placeholder:text-muted-foreground"
          />
        </div>
        <input
          value={company}
          onChange={(e) => { setCompany(e.target.value); setPage(1); }}
          placeholder="公司"
          className="rounded-lg border border-border/60 px-3 py-1.5 text-sm outline-none w-32 placeholder:text-muted-foreground"
        />
        <input
          value={location}
          onChange={(e) => { setLocation(e.target.value); setPage(1); }}
          placeholder="地点"
          className="rounded-lg border border-border/60 px-3 py-1.5 text-sm outline-none w-28 placeholder:text-muted-foreground"
        />
        <input
          value={jobCategory}
          onChange={(e) => { setJobCategory(e.target.value); setPage(1); }}
          placeholder="类别"
          className="rounded-lg border border-border/60 px-3 py-1.5 text-sm outline-none w-28 placeholder:text-muted-foreground"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="rounded-lg border border-border/60 bg-background px-3 py-1.5 text-sm outline-none"
        >
          <option value="">全部状态</option>
          <option value="displaying">展示中</option>
          <option value="closed">已关闭</option>
        </select>
      </div>

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
      ) : data && data.jobs.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-border/60">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/60 text-left text-xs text-muted-foreground">
                <th className="px-3 py-2 font-normal">公司</th>
                <th className="px-3 py-2 font-normal">岗位</th>
                <th className="px-3 py-2 font-normal">地点</th>
                <th className="px-3 py-2 font-normal">薪资</th>
                <th className="px-3 py-2 font-normal">来源</th>
                <th className="px-3 py-2 font-normal">有效性</th>
                <th className="px-3 py-2 font-normal">采集时间</th>
                <th className="px-3 py-2 font-normal text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {data.jobs.map((job) => (
                <tr key={job.id} className="border-b border-border/40 hover:bg-secondary/30">
                  <td className="px-3 py-2.5 font-medium text-foreground">{job.company}</td>
                  <td className="px-3 py-2.5">
                    <Link href={`/jobs/${job.id}`} className="text-foreground hover:underline">
                      {job.title}
                    </Link>
                  </td>
                  <td className="px-3 py-2.5 text-muted-foreground">{job.location || "-"}</td>
                  <td className="px-3 py-2.5 text-muted-foreground">{job.salary || "-"}</td>
                  <td className="px-3 py-2.5 text-muted-foreground">{job.source}</td>
                  <td className="px-3 py-2.5">
                    <span className={`text-xs ${job.is_valid && job.status === "displaying" ? "text-green-600" : "text-red-500"}`}>
                      {job.is_valid ? "有效" : "失效"} · {JOB_STATUS_LABELS[job.status] || job.status}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-muted-foreground">
                    {formatDate(job.collected_at)}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <button
                      onClick={() => handleVerify(job.id)}
                      disabled={verifying === job.id}
                      className="inline-flex items-center gap-1 rounded-md border border-border/60 px-2 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
                    >
                      <ShieldCheck className="h-3 w-3" />
                      {verifying === job.id ? "..." : "核验"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState message="暂无岗位数据，请先在采集页触发采集" />
      )}

      {/* 分页 */}
      {data && data.total > 20 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>共 {data.total} 条</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded border border-border/60 px-2 py-1 disabled:opacity-50"
            >
              上一页
            </button>
            <span className="px-2 py-1">第 {page} 页</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * 20 >= data.total}
              className="rounded border border-border/60 px-2 py-1 disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return value.slice(0, 10);
}
