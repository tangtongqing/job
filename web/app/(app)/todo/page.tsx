"use client";

import Link from "next/link";
import { api, type Todo } from "@/lib/api";
import { Loading, ErrorState, EmptyState, useApi } from "@/components/app/shared";
import { Calendar, Clock, MapPin } from "lucide-react";

const EVENT_TYPE_LABELS: Record<string, string> = {
  interview: "面试",
  test: "笔试",
  material_submit: "材料提交",
};

export default function TodoPage() {
  const { data, loading, error, reload } = useApi<{ todos: Todo[] }>(
    () => api.getTodo(14).then((r) => ({ data: { todos: r.data } }))
  );

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center gap-2">
        <h1 className="text-xl font-semibold text-foreground">待办</h1>
        <span className="text-xs text-muted-foreground">未来 14 天</span>
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : data && data.todos.length > 0 ? (
        <div className="space-y-2">
          {data.todos.map((todo) => (
            <Link
              key={todo.event_id}
              href={`/applications/${todo.application_id}`}
              className="block rounded-xl border border-border/60 bg-card p-4 hover:border-primary/40 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                      {EVENT_TYPE_LABELS[todo.event_type] || todo.event_type}
                    </span>
                    {todo.round && (
                      <span className="text-xs text-muted-foreground">第 {todo.round} 轮</span>
                    )}
                  </div>
                  <h3 className="mt-1 text-sm font-medium text-foreground">
                    {todo.job?.company} · {todo.job?.title}
                  </h3>
                  {todo.scheduled_at && (
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {todo.scheduled_at.slice(0, 16).replace("T", " ")}
                    </p>
                  )}
                  {todo.note && <p className="mt-1 text-xs text-muted-foreground">{todo.note}</p>}
                </div>
                {todo.days_left !== null && (
                  <div className={`text-right ${todo.days_left <= 1 ? "text-red-500" : "text-muted-foreground"}`}>
                    <div className="text-lg font-semibold tabular-nums">{todo.days_left}</div>
                    <div className="text-[10px]">天后</div>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState message="暂无未来 14 天待办" />
      )}
    </div>
  );
}
