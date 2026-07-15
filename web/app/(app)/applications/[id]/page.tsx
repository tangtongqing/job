"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, type Application, type ApplicationEvent, type ParseEmailResult } from "@/lib/api";
import { Loading, ErrorState, StatusBadge, useApi } from "@/components/app/shared";
import { getStatusLabel, getNextStatuses } from "@/lib/status-config";
import { Mail, Sparkles, ArrowRight, AlertTriangle } from "lucide-react";

export default function ApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const appId = Number(params.id);
  const { data: app, loading, error, reload } = useApi<Application>(
    () => api.getApplication(appId),
    [appId]
  );

  const [parsing, setParsing] = useState(false);
  const [parseResult, setParseResult] = useState<ParseEmailResult | null>(null);
  const [emailText, setEmailText] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleParse = async () => {
    if (!emailText.trim()) return;
    setParsing(true);
    setParseError(null);
    setParseResult(null);
    try {
      const resp = await api.parseEmail(emailText);
      setParseResult(resp.data);
    } catch (e: unknown) {
      setParseError(e instanceof Error ? e.message : "解析失败");
    } finally {
      setParsing(false);
    }
  };

  const handleConfirmTransition = async () => {
    if (!parseResult?.suggested_status) return;
    const targetId = parseResult.matched_application_id ?? appId;
    setConfirming(true);
    try {
      await api.transition(targetId, parseResult.suggested_status);
      setFeedback("状态已更新！");
      setParseResult(null);
      setEmailText("");
      reload();
    } catch (e: unknown) {
      setFeedback(e instanceof Error ? e.message : "更新失败");
    } finally {
      setConfirming(false);
    }
  };

  const handleTransition = async (toStatus: string) => {
    setFeedback(null);
    try {
      await api.transition(appId, toStatus);
      reload();
    } catch (e: unknown) {
      setFeedback(e instanceof Error ? e.message : "状态流转失败");
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!app) return null;

  const events = app.events || [];
  const nextStatuses = getNextStatuses(app.status);
  const upcomingEvents = events
    .filter((evt) => evt.scheduled_at && !evt.occurred_at)
    .sort((a, b) => String(a.scheduled_at).localeCompare(String(b.scheduled_at)));
  const historyEvents = events
    .filter((evt) => !evt.scheduled_at || evt.occurred_at)
    .sort((a, b) => String(b.occurred_at || b.scheduled_at || "").localeCompare(String(a.occurred_at || a.scheduled_at || "")));

  return (
    <div className="max-w-3xl space-y-5">
      {/* 头部 */}
      <div>
        <button onClick={() => router.back()} className="text-xs text-muted-foreground hover:text-foreground">
          ← 返回
        </button>
        <div className="mt-2 flex items-center gap-3">
          <h1 className="text-xl font-semibold text-foreground">投递 #{app.id}</h1>
          <StatusBadge status={app.status} />
        </div>
      </div>

      {/* 岗位信息 */}
      {app.job && (
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <h2 className="mb-2 text-sm font-medium text-foreground">关联岗位</h2>
          <div className="grid gap-3 text-sm md:grid-cols-3">
            <Field label="公司" value={app.job.company} />
            <Field label="岗位" value={app.job.title} />
            <Field label="地点" value={app.job.location} />
            <Field label="薪资" value={app.job.salary} />
            <Field label="来源" value={app.job.source} />
            <Field label="截止时间" value={app.job.deadline?.slice(0, 10) || null} />
          </div>
        </div>
      )}

      {/* 状态流转 */}
      {nextStatuses.length > 0 && (
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <h2 className="mb-2 text-sm font-medium text-foreground">流转状态</h2>
          <div className="flex flex-wrap gap-2">
            {nextStatuses.map((s) => (
              <button
                key={s}
                onClick={() => handleTransition(s)}
                className="inline-flex items-center gap-1 rounded-full border border-border/60 px-3 py-1 text-xs text-foreground hover:bg-secondary"
              >
                {getStatusLabel(s)}
                <ArrowRight className="h-3 w-3" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* AI 邮件解析 */}
      <div className="rounded-xl border border-border/60 bg-card p-4">
        <div className="mb-3 flex items-center gap-2">
          <Mail className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-medium text-foreground">AI 邮件解析</h2>
          <span className="text-xs text-muted-foreground">（粘贴 HR 邮件，AI 建议状态）</span>
        </div>

        <textarea
          value={emailText}
          onChange={(e) => setEmailText(e.target.value)}
          placeholder="粘贴招聘邮件或消息文本..."
          className="w-full rounded-lg border border-border/60 bg-background p-3 text-sm outline-none focus:border-primary/40 min-h-[80px] placeholder:text-muted-foreground"
        />

        <button
          onClick={handleParse}
          disabled={parsing || !emailText.trim()}
          className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <Sparkles className="h-4 w-4" />
          {parsing ? "解析中..." : "AI 解析"}
        </button>

        {parseError && <p className="mt-2 text-sm text-red-500">{parseError}</p>}

        {/* 解析结果 */}
        {parseResult && (
          <div className="mt-4 space-y-3 rounded-lg border border-border/60 p-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-foreground">解析结果</span>
              {parseResult.degraded ? (
                <span className="rounded bg-orange-100 px-1.5 py-0.5 text-[10px] text-orange-700 dark:bg-orange-900/40 dark:text-orange-300">
                  正则降级
                </span>
              ) : (
                <span className="rounded bg-green-100 px-1.5 py-0.5 text-[10px] text-green-700 dark:bg-green-900/40 dark:text-green-300">
                  LLM
                </span>
              )}
            </div>

            {parseResult.parsed ? (
              <div className="grid grid-cols-2 gap-2 text-sm">
                <Field label="公司" value={parseResult.company} />
                <Field label="岗位" value={parseResult.title} />
                <Field
                  label="建议状态"
                  value={parseResult.suggested_status ? getStatusLabel(parseResult.suggested_status) : null}
                />
                <Field label="置信度" value={`${(parseResult.confidence * 100).toFixed(0)}%`} />
                <Field
                  label="匹配投递"
                  value={parseResult.matched_application_id ? `#${parseResult.matched_application_id}` : `当前投递 #${appId}`}
                />
                {parseResult.reasoning && (
                  <div className="col-span-2">
                    <span className="text-xs text-muted-foreground">依据</span>
                    <p className="text-sm text-foreground">{parseResult.reasoning}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">未能解析出有效信息</p>
            )}

            {/* 确认提示 */}
            <div className="flex items-start gap-2 rounded bg-yellow-50 dark:bg-yellow-900/20 p-2">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <p className="text-xs text-yellow-700 dark:text-yellow-300">
                AI 结果仅为建议，确认后才会更新状态。
              </p>
            </div>
            {!parseResult.matched_application_id && (
              <p className="text-xs text-muted-foreground">
                未匹配到唯一投递，将以当前详情页投递 #{appId} 作为确认对象。
              </p>
            )}

            {/* 确认按钮 */}
            {parseResult.parsed && parseResult.suggested_status && (
              <button
                onClick={handleConfirmTransition}
                disabled={confirming}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {confirming ? "更新中..." : `确认将投递 #${parseResult.matched_application_id ?? appId} 流转到「${getStatusLabel(parseResult.suggested_status)}」`}
              </button>
            )}
          </div>
        )}
      </div>

      {/* 事件时间线 */}
      <div className="rounded-xl border border-border/60 bg-card p-4">
        <h2 className="mb-3 text-sm font-medium text-foreground">事件时间线</h2>
        {events.length > 0 ? (
          <div className="space-y-5">
            {upcomingEvents.length > 0 && (
              <section>
                <h3 className="mb-2 text-xs font-medium text-muted-foreground">即将到来</h3>
                <div className="space-y-3 rounded-lg bg-yellow-50/70 p-3 dark:bg-yellow-900/10">
                  {upcomingEvents.map((evt) => (
                    <TimelineItem key={evt.id} event={evt} tone="upcoming" />
                  ))}
                </div>
              </section>
            )}

            {historyEvents.length > 0 && (
              <section>
                <h3 className="mb-2 text-xs font-medium text-muted-foreground">历史</h3>
                <div className="space-y-3">
                  {historyEvents.map((evt) => (
                    <TimelineItem key={evt.id} event={evt} tone="history" />
                  ))}
                </div>
              </section>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">暂无事件记录</p>
        )}
      </div>

      {feedback && <p className="text-sm text-muted-foreground">{feedback}</p>}
    </div>
  );
}

function TimelineItem({
  event,
  tone,
}: {
  event: ApplicationEvent;
  tone: "upcoming" | "history";
}) {
  const time = event.scheduled_at || event.occurred_at;
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className={`h-2 w-2 rounded-full ${event.is_correction ? "bg-orange-400" : tone === "upcoming" ? "bg-yellow-500" : "bg-primary"}`} />
        <div className="w-px flex-1 bg-border/40" />
      </div>
      <div className="pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-foreground">{eventTitle(event)}</span>
          {event.is_correction && (
            <span className="rounded bg-orange-100 px-1 text-[9px] text-orange-700 dark:bg-orange-900/40 dark:text-orange-300">
              纠错
            </span>
          )}
          {tone === "upcoming" && event.scheduled_at && (
            <span className="rounded bg-yellow-100 px-1 text-[9px] text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300">
              {daysUntil(event.scheduled_at)}
            </span>
          )}
        </div>
        {time && (
          <p className="text-xs text-muted-foreground">{formatDateTime(time)}</p>
        )}
        {event.note && <p className="mt-0.5 text-xs text-muted-foreground">{event.note}</p>}
        {event.correction_reason && (
          <p className="mt-0.5 text-xs text-orange-600">{event.correction_reason}</p>
        )}
      </div>
    </div>
  );
}

function eventTitle(event: ApplicationEvent) {
  if ((event.event_type === "status_change" || event.event_type === "correction") && event.to_status) {
    const from = event.from_status ? getStatusLabel(event.from_status) : "未记录";
    return event.event_type === "correction"
      ? `纠错：${from} → ${getStatusLabel(event.to_status)}`
      : `状态变更：${from} → ${getStatusLabel(event.to_status)}`;
  }
  if (event.event_type === "interview") return event.round ? `面试（第 ${event.round} 轮）` : "面试";
  if (event.event_type === "test") return "笔试/测评";
  if (event.event_type === "material_submit") return "材料提交";
  if (event.event_type === "offer") return "Offer";
  if (event.event_type === "note") return "备注";
  return event.event_type;
}

function formatDateTime(value: string) {
  return value.slice(0, 16).replace("T", " ");
}

function daysUntil(value: string) {
  const target = new Date(value);
  const today = new Date();
  target.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  const days = Math.ceil((target.getTime() - today.getTime()) / 86400000);
  if (days < 0) return "已过期";
  if (days === 0) return "今天";
  return `${days} 天后`;
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm text-foreground">{value || "-"}</dd>
    </div>
  );
}
