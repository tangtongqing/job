/**
 * 产品面 App Shell —— 左侧导航（桌面）+ hamburger 菜单（移动）。
 * product register：工具型，信息密度，不做营销 hero。
 */

"use client";

import { useState } from "react";
import { LayoutDashboard, Briefcase, Send, CheckSquare, Cpu, Home, Menu, X } from "lucide-react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { ApiConnectionStatus } from "@/components/app/shared";
import { ToastProvider } from "@/components/app/toast";

const NAV_ITEMS = [
  { href: "/dashboard", label: "看板", icon: LayoutDashboard },
  { href: "/jobs", label: "岗位", icon: Briefcase },
  { href: "/applications", label: "投递管理", icon: Send },
  { href: "/todo", label: "待办", icon: CheckSquare },
  { href: "/crawler", label: "采集", icon: Cpu },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background">
      {/* 桌面侧边导航 */}
      <aside className="hidden md:flex w-56 shrink-0 flex-col border-r border-border/60 bg-card/50">
        <div className="flex items-center gap-2 px-5 py-4 border-b border-border/60">
          <Link href="/" className="text-lg font-semibold tracking-tight text-foreground">
            ✦ JobPulse
          </Link>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="px-3 py-3 border-t border-border/60">
          <Link
            href="/"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-muted-foreground hover:text-foreground"
          >
            <Home className="h-3.5 w-3.5" />
            返回首页
          </Link>
        </div>
      </aside>

      <div className="flex flex-1 flex-col min-w-0">
        {/* 移动端顶部栏 + hamburger */}
        <header className="flex items-center justify-between gap-2 border-b border-border/60 px-4 py-3 md:hidden">
          <span className="shrink-0 font-semibold text-foreground">✦ JobPulse</span>
          <div className="flex shrink-0 items-center gap-2">
            <ApiConnectionStatus compact />
            <ThemeToggle />
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="菜单"
              aria-expanded={menuOpen}
              className="h-9 w-9 inline-flex items-center justify-center text-foreground"
            >
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </header>

        {/* 移动端下拉菜单 */}
        {menuOpen && (
          <nav
            className="border-b border-border/60 bg-card px-4 py-2 md:hidden"
            role="menu"
          >
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                  role="menuitem"
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
            <Link
              href="/"
              onClick={() => setMenuOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-xs text-muted-foreground hover:text-foreground"
              role="menuitem"
            >
              <Home className="h-3.5 w-3.5" />
              返回首页
            </Link>
          </nav>
        )}

        {/* 桌面端顶部栏 */}
        <header className="hidden md:flex items-center justify-end gap-3 border-b border-border/60 px-6 py-2.5">
          <ApiConnectionStatus />
          <ThemeToggle />
        </header>

        <main className="flex-1 overflow-auto p-4 md:p-6">
          <ToastProvider>{children}</ToastProvider>
        </main>
      </div>
    </div>
  );
}
