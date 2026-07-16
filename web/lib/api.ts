/**
 * API Client —— 统一处理后端 {data, meta} / {error} envelope。
 *
 * Base URL 从 NEXT_PUBLIC_API_BASE_URL 读，本地缺省使用后端标准 8000 端口。
 * 页面在浏览器运行时请求；build 阶段不强依赖后端在线。
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

// ---------- 通用类型 ----------

interface Meta {
  page?: number;
  page_size?: number;
  total?: number;
}

interface ApiSuccess<T> {
  data: T;
  meta?: Meta;
}

interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export class ApiRequestError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

// ---------- 核心请求函数 ----------

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<ApiSuccess<T>> {
  let resp: Response;
  try {
    resp = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });
  } catch {
    // 网络错误（后端未启动等）
    throw new ApiRequestError(
      "NETWORK_ERROR",
      "无法连接到后端服务，请确认后端已启动",
      0
    );
  }

  const body = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const err = (body as ApiError).error;
    throw new ApiRequestError(
      err?.code || "UNKNOWN_ERROR",
      err?.message || `请求失败 (${resp.status})`,
      resp.status
    );
  }

  return body as ApiSuccess<T>;
}

// ---------- 业务类型 ----------

export interface Job {
  id: number;
  company: string;
  title: string;
  location: string | null;
  salary: string | null;
  jd: string | null;
  requirement: string | null;
  apply_url: string | null;
  source: string;
  source_url: string | null;
  job_category: string | null;
  graduation_year: string | null;
  education: string | null;
  experience: string | null;
  collected_at: string | null;
  deadline: string | null;
  last_verified_at: string | null;
  is_valid: boolean;
  is_intern: boolean;
  is_fresh: boolean;
  status: string;
}

export interface Application {
  id: number;
  job_id: number;
  status: string;
  applied_at: string;
  updated_at: string;
  notes: string | null;
  job?: Job;
  events?: ApplicationEvent[];
}

export interface ApplicationEvent {
  id: number;
  application_id: number;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  round: number | null;
  scheduled_at: string | null;
  occurred_at: string | null;
  is_correction: boolean;
  correction_reason: string | null;
  note: string | null;
}

export interface KPI {
  today_new_jobs: number;
  total_jobs: number;
  total_applications: number;
  pending_applications: number;
  by_status: Record<string, number>;
}

export interface FunnelItem {
  status: string;
  count: number;
  rate: number;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface DistributionItem {
  label: string;
  count: number;
  rate: number;
}

export interface Todo {
  event_id: number;
  application_id: number;
  event_type: string;
  scheduled_at: string | null;
  occurred_at: string | null;
  round: number | null;
  note: string | null;
  job: { company: string | null; title: string | null };
  days_left: number | null;
}

export interface ParseEmailResult {
  parsed: boolean;
  company: string | null;
  title: string | null;
  suggested_status: string | null;
  confidence: number;
  degraded: boolean;
  matched_application_id: number | null;
  reasoning: string | null;
}

export interface CrawlLog {
  id: number;
  source: string;
  status: string;
  count: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface CrawlSource {
  name: string;
  label: string;
  adapter: string;
  enabled: boolean;
  kind: "public_api" | "website" | "restricted_platform";
  last_run: {
    status: string;
    count: number;
    error: string | null;
    finished_at: string | null;
  } | null;
}

export interface JobStats {
  today_new: number;
  total: number;
  valid: number;
  invalid: number;
  by_source: Record<string, number>;
  demo_count: number;
  live_count: number;
  field_completeness: Record<string, { count: number; percentage: number }>;
}

export interface SavedJob {
  id: number;
  job_id: number;
  action_type: "favorited" | "to_apply";
  job: Job;
  created_at: string;
}

export interface Subscription {
  id: number;
  keyword: string | null;
  company: string | null;
  location: string | null;
  created_at: string;
}

export interface SubscriptionPayload {
  keyword?: string | null;
  company?: string | null;
  location?: string | null;
}

// ---------- API 方法 ----------

export const api = {
  // Dashboard
  getKPI: () => request<KPI>("/dashboard/kpi"),
  getFunnel: () =>
    request<{ funnel: FunnelItem[]; total_applications: number }>(
      "/dashboard/funnel"
    ),
  getTrend: (days = 7) =>
    request<{ trend: TrendPoint[]; total: number }>(
      `/dashboard/trend?days=${days}`
    ),
  getDistribution: (dimension = "job_category") =>
    request<{
      dimension: string;
      distribution: DistributionItem[];
      total: number;
    }>(`/dashboard/distribution?dimension=${dimension}`),

  // Jobs
  getJobs: (params: Record<string, unknown> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null && v !== "") as [string, string][]
    ).toString();
    return request<Job[]>(`/jobs${qs ? "?" + qs : ""}`);
  },
  getJob: (id: number) => request<Job>(`/jobs/${id}`),
  getJobStats: () => request<JobStats>("/jobs/stats"),
  verifyJob: (id: number) => request<Job>(`/jobs/${id}/verify`, { method: "POST" }),
  favoriteJob: (id: number) =>
    request<{ id: number; job_id: number; action_type: "favorited"; created_at: string }>(
      `/jobs/${id}/favorite`,
      { method: "POST" }
    ),
  unfavoriteJob: (id: number) =>
    request<never>(`/jobs/${id}/favorite`, { method: "DELETE" }),
  markToApply: (id: number) =>
    request<{ id: number; job_id: number; action_type: "to_apply"; created_at: string }>(
      `/jobs/${id}/to-apply`,
      { method: "POST" }
    ),
  removeToApply: (id: number) =>
    request<never>(`/jobs/${id}/to-apply`, { method: "DELETE" }),
  getFavorites: () => request<SavedJob[]>("/user/favorites?page_size=100"),
  getToApply: () => request<SavedJob[]>("/user/to-apply?page_size=100"),

  // Applications
  getApplications: (params: Record<string, unknown> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null && v !== "") as [string, string][]
    ).toString();
    return request<Application[]>(`/applications${qs ? "?" + qs : ""}`);
  },
  getApplication: (id: number) => request<Application>(`/applications/${id}`),
  createApplication: (job_id: number, notes?: string) =>
    request<Application>("/applications", {
      method: "POST",
      body: JSON.stringify({ job_id, notes }),
    }),
  transition: (
    id: number,
    to_status: string,
    options?: { note?: string; is_correction?: boolean; correction_reason?: string }
  ) =>
    request<{ application: Application; event: ApplicationEvent }>(
      `/applications/${id}/transition`,
      {
        method: "POST",
        body: JSON.stringify({ to_status, ...options }),
      }
    ),
  batchTransition: (application_ids: number[], to_status: string, note?: string) =>
    request<{
      succeeded: number[];
      failed: { application_id: number; error_code: string; message: string }[];
      total: number;
      success_count: number;
      fail_count: number;
    }>("/applications/batch-transition", {
      method: "POST",
      body: JSON.stringify({ application_ids, to_status, note }),
    }),
  getEvents: (id: number) =>
    request<ApplicationEvent[]>(`/applications/${id}/events`),
  parseEmail: (email_text: string) =>
    request<ParseEmailResult>("/applications/parse-email", {
      method: "POST",
      body: JSON.stringify({ email_text }),
    }),

  // Todo
  getTodo: (days = 7) => request<Todo[]>(`/todo?days=${days}`),

  // Subscriptions
  getSubscriptions: () => request<Subscription[]>("/subscriptions?page_size=100"),
  createSubscription: (payload: SubscriptionPayload) =>
    request<Subscription>("/subscriptions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateSubscription: (id: number, payload: SubscriptionPayload) =>
    request<Subscription>(`/subscriptions/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteSubscription: (id: number) =>
    request<never>(`/subscriptions/${id}`, { method: "DELETE" }),

  // Demo
  resetDemo: () =>
    request<{
      message: string;
      jobs: number;
      applications: number;
      saved_jobs: number;
      subscriptions: number;
    }>("/demo/reset", { method: "POST" }),

  // Crawler
  triggerCrawl: (source?: string) =>
    request<{ source: string; status: string; count: number; error: string | null }>(
      "/crawler/trigger",
      { method: "POST", body: JSON.stringify({ source }) }
    ),
  getCrawlLogs: (page = 1, page_size = 20) =>
    request<CrawlLog[]>(`/crawler/logs?page=${page}&page_size=${page_size}`),
  getCrawlSources: () => request<CrawlSource[]>("/crawler/sources"),
};
