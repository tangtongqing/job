"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  BellRing,
  Bookmark,
  BriefcaseBusiness,
  CalendarCheck,
  Database,
  Home,
  LayoutDashboard,
  Menu,
  RotateCcw,
  Send,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ApiConnectionStatus } from "@/components/app/shared";
import { ToastProvider, useToast } from "@/components/app/toast";
import { ThemeToggle } from "@/components/theme-toggle";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const PRIMARY_NAV = [
  { href: "/dashboard", label: "概览", icon: LayoutDashboard },
  { href: "/jobs", label: "发现岗位", icon: BriefcaseBusiness },
  { href: "/saved", label: "收藏与待投递", icon: Bookmark },
  { href: "/applications", label: "投递进展", icon: Send },
  { href: "/todo", label: "近期安排", icon: CalendarCheck },
  { href: "/subscriptions", label: "岗位订阅", icon: BellRing },
];

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "求职概览",
  "/jobs": "发现岗位",
  "/saved": "收藏与待投递",
  "/applications": "投递进展",
  "/todo": "近期安排",
  "/subscriptions": "岗位订阅",
  "/crawler": "数据采集",
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <AppShell>{children}</AppShell>
    </ToastProvider>
  );
}

function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { toast } = useToast();
  const [menuOpen, setMenuOpen] = useState(false);
  const [resetArmed, setResetArmed] = useState(false);
  const [resetting, setResetting] = useState(false);

  useEffect(() => setMenuOpen(false), [pathname]);
  useEffect(() => {
    if (!resetArmed) return;
    const timer = window.setTimeout(() => setResetArmed(false), 5000);
    return () => window.clearTimeout(timer);
  }, [resetArmed]);

  const activeBase = `/${pathname.split("/").filter(Boolean)[0] || "dashboard"}`;
  const pageTitle = PAGE_TITLES[activeBase] || "JobPulse";

  const resetDemo = async () => {
    if (!resetArmed) {
      setResetArmed(true);
      return;
    }
    setResetting(true);
    try {
      const response = await api.resetDemo();
      toast(`${response.data.jobs} 个岗位与完整投递轨迹已恢复`);
      setResetArmed(false);
      window.setTimeout(() => window.location.reload(), 450);
    } catch (error) {
      toast(error instanceof Error ? error.message : "Demo 重置失败", "error");
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f7f7f8] text-foreground dark:bg-background">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 flex-col border-r border-black/[0.07] bg-white px-3 py-4 dark:border-white/10 dark:bg-card md:flex">
        <Link
          href="/"
          className="flex min-h-11 items-center gap-2.5 rounded-lg px-3 text-[15px] font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#6366f1] text-white">
            <Activity className="h-4 w-4" strokeWidth={2.25} />
          </span>
          JobPulse
          <span className="ml-auto rounded-full bg-[#eef2ff] px-2 py-0.5 text-[10px] font-medium text-[#4f46e5] dark:bg-indigo-950 dark:text-indigo-300">
            Beta
          </span>
        </Link>

        <p className="mb-2 mt-7 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Workspace
        </p>
        <nav className="space-y-1" aria-label="产品导航">
          {PRIMARY_NAV.map((item) => (
            <NavItem key={item.href} item={item} active={activeBase === item.href} />
          ))}
        </nav>

        <div className="mt-auto space-y-1 border-t border-black/[0.06] pt-3 dark:border-white/10">
          <NavItem
            item={{ href: "/crawler", label: "数据与采集", icon: Database }}
            active={activeBase === "/crawler"}
            secondary
          />
          <button
            type="button"
            onClick={resetDemo}
            disabled={resetting}
            className={cn(
              "flex min-h-11 w-full items-center gap-2.5 rounded-lg px-3 text-left text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50",
              resetArmed
                ? "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300"
                : "text-muted-foreground hover:bg-black/[0.035] hover:text-foreground dark:hover:bg-white/[0.06]"
            )}
          >
            <RotateCcw className="h-4 w-4" />
            {resetting ? "正在恢复…" : resetArmed ? "再次点击确认重置" : "重置演示数据"}
          </button>
          <Link
            href="/"
            className="flex min-h-11 items-center gap-2.5 rounded-lg px-3 text-xs text-muted-foreground transition-colors hover:bg-black/[0.035] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent dark:hover:bg-white/[0.06]"
          >
            <Home className="h-4 w-4" />
            返回产品官网
          </Link>
        </div>
      </aside>

      <div className="md:pl-60">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-black/[0.06] bg-[#f7f7f8]/95 px-4 backdrop-blur md:px-7 dark:border-white/10 dark:bg-background/95">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label={menuOpen ? "关闭导航" : "打开导航"}
              aria-expanded={menuOpen}
              className="grid h-11 w-11 place-items-center rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent md:hidden"
            >
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <div>
              <p className="text-sm font-semibold tracking-tight">{pageTitle}</p>
              <p className="hidden text-[11px] text-muted-foreground sm:block">把下一步放在眼前</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ApiConnectionStatus compact />
            <ThemeToggle />
          </div>
        </header>

        {menuOpen && (
          <div className="fixed inset-0 top-16 z-30 bg-black/20 md:hidden" onClick={() => setMenuOpen(false)}>
            <nav
              className="h-full w-[min(88vw,22rem)] space-y-1 border-r border-black/10 bg-white p-4 shadow-xl dark:bg-card"
              aria-label="移动端产品导航"
              onClick={(event) => event.stopPropagation()}
            >
              {PRIMARY_NAV.map((item) => (
                <NavItem key={item.href} item={item} active={activeBase === item.href} />
              ))}
              <div className="mt-4 border-t border-border pt-3">
                <NavItem
                  item={{ href: "/crawler", label: "数据与采集", icon: Database }}
                  active={activeBase === "/crawler"}
                  secondary
                />
              </div>
            </nav>
          </div>
        )}

        <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1440px] p-4 pb-24 md:p-7 md:pb-10">
          {children}
        </main>
      </div>

      <nav className="fixed inset-x-3 bottom-3 z-30 grid grid-cols-5 rounded-2xl border border-black/10 bg-white/95 p-1.5 shadow-lg backdrop-blur md:hidden dark:border-white/10 dark:bg-card/95" aria-label="快捷导航">
        {PRIMARY_NAV.slice(0, 5).map((item) => {
          const Icon = item.icon;
          const active = activeBase === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-xl text-[10px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                active ? "bg-[#eef2ff] font-medium text-[#4f46e5] dark:bg-indigo-950 dark:text-indigo-300" : "text-muted-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label.replace("收藏与", "")}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

function NavItem({
  item,
  active,
  secondary = false,
}: {
  item: { href: string; label: string; icon: React.ComponentType<{ className?: string }> };
  active: boolean;
  secondary?: boolean;
}) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex min-h-11 items-center gap-2.5 rounded-lg px-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        secondary ? "text-xs" : "text-[13px]",
        active
          ? "bg-[#eef2ff] font-medium text-[#4338ca] dark:bg-indigo-950/70 dark:text-indigo-300"
          : "text-muted-foreground hover:bg-black/[0.035] hover:text-foreground dark:hover:bg-white/[0.06]"
      )}
    >
      <Icon className="h-4 w-4" />
      {item.label}
      {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-[#6366f1]" />}
    </Link>
  );
}
