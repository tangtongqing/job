"use client";

import { FormEvent, useState } from "react";
import { BellRing, Building2, MapPin, Pencil, Plus, Search, Trash2, X } from "lucide-react";

import { EmptyState, ErrorState, Loading, useApi } from "@/components/app/shared";
import { useToast } from "@/components/app/toast";
import { api, type Subscription, type SubscriptionPayload } from "@/lib/api";

const EMPTY_FORM: SubscriptionPayload = { keyword: "", company: "", location: "" };

export default function SubscriptionsPage() {
  const { toast } = useToast();
  const subscriptions = useApi<Subscription[]>(() => api.getSubscriptions());
  const [form, setForm] = useState<SubscriptionPayload>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const payload: SubscriptionPayload = {
      keyword: form.keyword?.trim() || null,
      company: form.company?.trim() || null,
      location: form.location?.trim() || null,
    };
    if (!payload.keyword && !payload.company && !payload.location) {
      setFormError("至少填写关键词、公司或地点中的一项");
      return;
    }
    setFormError(null);
    setSaving(true);
    try {
      if (editingId) {
        await api.updateSubscription(editingId, payload);
        toast("订阅规则已更新");
      } else {
        await api.createSubscription(payload);
        toast("订阅规则已创建");
      }
      setForm(EMPTY_FORM);
      setEditingId(null);
      subscriptions.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "保存失败", "error");
    } finally {
      setSaving(false);
    }
  };

  const edit = (subscription: Subscription) => {
    setEditingId(subscription.id);
    setFormError(null);
    setForm({
      keyword: subscription.keyword || "",
      company: subscription.company || "",
      location: subscription.location || "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const remove = async (id: number) => {
    setDeletingId(id);
    try {
      await api.deleteSubscription(id);
      toast("订阅规则已删除");
      if (editingId === id) {
        setEditingId(null);
        setForm(EMPTY_FORM);
      }
      subscriptions.reload();
    } catch (error) {
      toast(error instanceof Error ? error.message : "删除失败", "error");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-medium text-[#4f46e5]">SIGNAL, NOT NOISE</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-[-0.025em]">只追踪真正关心的岗位</h1>
        <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted-foreground">
          用关键词、公司和地点组合规则。当前 Beta 版会在采集结果中保留匹配条件，通知能力列入下一阶段。
        </p>
      </header>

      <form onSubmit={submit} className="rounded-2xl border border-black/[0.07] bg-white p-5 dark:border-white/10 dark:bg-card">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold">{editingId ? "编辑订阅规则" : "创建订阅规则"}</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">至少填写一个条件，可组合提高精度。</p>
          </div>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(null); setForm(EMPTY_FORM); setFormError(null); }} className="grid h-11 w-11 place-items-center rounded-lg text-muted-foreground hover:bg-black/[0.04] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent dark:hover:bg-white/[0.06]" aria-label="取消编辑">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <RuleField label="关键词" icon={Search} value={form.keyword || ""} placeholder="如：AI 产品经理" invalid={Boolean(formError)} onChange={(value) => { setForm((current) => ({ ...current, keyword: value })); if (value.trim()) setFormError(null); }} />
          <RuleField label="公司" icon={Building2} value={form.company || ""} placeholder="如：MiniMax" invalid={Boolean(formError)} onChange={(value) => { setForm((current) => ({ ...current, company: value })); if (value.trim()) setFormError(null); }} />
          <RuleField label="地点" icon={MapPin} value={form.location || ""} placeholder="如：北京" invalid={Boolean(formError)} onChange={(value) => { setForm((current) => ({ ...current, location: value })); if (value.trim()) setFormError(null); }} />
        </div>
        {formError && <p id="subscription-form-error" role="alert" className="mt-3 text-sm text-red-600 dark:text-red-400">{formError}</p>}
        <div className="mt-4 flex justify-end">
          <button type="submit" disabled={saving} className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-foreground px-5 text-sm font-medium text-background hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50">
            {editingId ? <Pencil className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            {saving ? "保存中…" : editingId ? "保存修改" : "创建规则"}
          </button>
        </div>
      </form>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold">正在追踪</h2>
          <span className="text-xs tabular-nums text-muted-foreground">{subscriptions.data?.length || 0} 条规则</span>
        </div>
        {subscriptions.loading ? (
          <Loading />
        ) : subscriptions.error ? (
          <ErrorState message={subscriptions.error} onRetry={subscriptions.reload} />
        ) : subscriptions.data && subscriptions.data.length > 0 ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {subscriptions.data.map((subscription) => (
              <article key={subscription.id} className="rounded-2xl border border-black/[0.07] bg-white p-5 dark:border-white/10 dark:bg-card">
                <div className="flex items-start gap-4">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#eef2ff] text-[#4f46e5] dark:bg-indigo-950 dark:text-indigo-300">
                    <BellRing className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-semibold">{ruleTitle(subscription)}</h3>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {subscription.keyword && <RuleChip icon={Search}>{subscription.keyword}</RuleChip>}
                      {subscription.company && <RuleChip icon={Building2}>{subscription.company}</RuleChip>}
                      {subscription.location && <RuleChip icon={MapPin}>{subscription.location}</RuleChip>}
                    </div>
                  </div>
                </div>
                <div className="mt-5 flex items-center justify-between border-t border-black/[0.06] pt-3 dark:border-white/10">
                  <span className="text-[11px] text-muted-foreground">创建于 {subscription.created_at.slice(0, 10)}</span>
                  <div className="flex gap-1">
                    <button type="button" onClick={() => edit(subscription)} className="grid h-11 w-11 place-items-center rounded-lg text-muted-foreground hover:bg-black/[0.04] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent dark:hover:bg-white/[0.06]" aria-label="编辑订阅">
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button type="button" onClick={() => remove(subscription.id)} disabled={deletingId === subscription.id} className="grid h-11 w-11 place-items-center rounded-lg text-muted-foreground hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50 dark:hover:bg-red-950/30" aria-label="删除订阅">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-black/10 bg-white py-8 dark:border-white/10 dark:bg-card"><EmptyState message="还没有订阅规则" /></div>
        )}
      </section>
    </div>
  );
}

function RuleField({ label, icon: Icon, value, placeholder, invalid, onChange }: { label: string; icon: React.ComponentType<{ className?: string }>; value: string; placeholder: string; invalid: boolean; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-foreground">{label}</span>
      <span className="mt-1.5 flex min-h-11 items-center gap-2 rounded-lg border border-black/10 bg-[#fafafa] px-3 focus-within:border-[#6366f1] focus-within:ring-2 focus-within:ring-[#6366f1]/15 dark:border-white/10 dark:bg-background">
        <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
        <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} aria-invalid={invalid} aria-describedby={invalid ? "subscription-form-error" : undefined} className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/70" />
      </span>
    </label>
  );
}

function RuleChip({ icon: Icon, children }: { icon: React.ComponentType<{ className?: string }>; children: React.ReactNode }) {
  return <span className="inline-flex items-center gap-1.5 rounded-full bg-[#f3f4f6] px-2.5 py-1 text-xs text-muted-foreground dark:bg-white/10"><Icon className="h-3 w-3" />{children}</span>;
}

function ruleTitle(subscription: Subscription) {
  if (subscription.keyword) return subscription.keyword;
  if (subscription.company) return `${subscription.company} 的新岗位`;
  return `${subscription.location} 的新岗位`;
}
