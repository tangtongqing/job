"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, type Job } from "@/lib/api";
import { Loading, ErrorState, useApi } from "@/components/app/shared";
import { AlertTriangle, ExternalLink, Send } from "lucide-react";
import { useToast } from "@/components/app/toast";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const jobId = Number(params.id);
  const { data: job, loading, error, reload } = useApi<Job>(() => api.getJob(jobId), [jobId]);
  const [creating, setCreating] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleApply = async () => {
    if (!job) return;
    setCreating(true);
    setFeedback(null);
    try {
      const resp = await api.createApplication(job.id);
      setFeedback("投递创建成功！");
      toast("投递创建成功");
      setTimeout(() => router.push(`/applications/${resp.data.id}`), 1000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "创建失败";
      setFeedback(msg);
      toast(msg, "error");
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!job) return null;

  return (
    <div className="max-w-3xl space-y-5">
      {/* 头部 */}
      <div>
        <button
          onClick={() => router.back()}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          ← 返回
        </button>
        <h1 className="mt-2 text-xl font-semibold text-foreground">{job.title}</h1>
        <p className="text-sm text-muted-foreground">{job.company}</p>
      </div>

      {/* 基本信息 */}
      <div className="grid grid-cols-2 gap-3 rounded-xl border border-border/60 bg-card p-4 text-sm md:grid-cols-3">
        <InfoItem label="地点" value={job.location} />
        <InfoItem label="薪资" value={job.salary} />
        <InfoItem label="来源" value={sourceLabel(job.source)} />
        <InfoItem label="学历" value={job.education} />
        <InfoItem label="经验" value={job.experience} />
        <InfoItem label="毕业年份" value={job.graduation_year} />
        <InfoItem label="截止时间" value={job.deadline?.slice(0, 10)} />
        <InfoItem label="最后核验" value={job.last_verified_at?.slice(0, 10)} />
      </div>

      {job.source === "demo_snapshot" && (
        <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          这是用于稳定演示的岗位快照，字段完整但不代表官方当前仍在招聘。请在企业官方页面确认最新状态。
        </div>
      )}

      {/* JD */}
      {job.jd && (
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <h2 className="mb-2 text-sm font-medium text-foreground">岗位描述</h2>
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">{job.jd}</p>
        </div>
      )}

      {/* 要求 */}
      {job.requirement && (
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <h2 className="mb-2 text-sm font-medium text-foreground">岗位要求</h2>
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">{job.requirement}</p>
        </div>
      )}

      {/* 操作 */}
      <div className="flex flex-wrap items-center gap-3">
        {job.apply_url && (
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-11 items-center gap-1.5 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <ExternalLink className="h-4 w-4" />
            前往官方投递
          </a>
        )}
        <button
          onClick={handleApply}
          disabled={creating}
          className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-border/60 px-4 text-sm font-medium text-foreground hover:bg-secondary disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          {creating ? "创建中..." : "创建投递记录"}
        </button>
      </div>

      {feedback && (
        <p className="text-sm text-muted-foreground">{feedback}</p>
      )}
    </div>
  );
}

function sourceLabel(source: string) {
  if (source === "demo_snapshot") return "演示快照";
  if (source.startsWith("greenhouse_")) return `${source.replace("greenhouse_", "")} · 公开 API`;
  return source;
}

function InfoItem({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-sm text-foreground">{value || "-"}</dd>
    </div>
  );
}
