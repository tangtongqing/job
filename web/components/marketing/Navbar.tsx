"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { Activity, ChevronDown, Menu, X } from "lucide-react";

/**
 * 顶部导航条（v4 · 真实营销型 + 完整产品导航）。
 *
 * 参考结构（Linear / Notion）：多分区产品导航，覆盖完整产品故事。
 * - 产品：核心功能入口
 * - 方案：按使用场景
 * - 定价
 * - 资源：设计过程/帮助（作品集差异化）
 *
 * 真实营销型 CTA：「免费开始」（替代作品集型的"查看 Live Demo"）。
 * 移动端：汉堡菜单。
 */
const NAV_SECTIONS = [
  {
    label: "产品",
    items: [
      { name: "信息聚合", href: "#aggregation" },
      { name: "投递管理", href: "#status" },
      { name: "数据看板", href: "#dashboard" },
      { name: "全部功能", href: "#capabilities" },
    ],
  },
  {
    label: "方案",
    items: [
      { name: "应届秋招", href: "#" },
      { name: "日常找实习", href: "#" },
      { name: "跨行转行", href: "#" },
    ],
  },
  {
    label: "资源",
    items: [
      { name: "设计过程", href: "#" },
      { name: "帮助文档", href: "#" },
      { name: "更新日志", href: "#" },
    ],
  },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-border/40 bg-background/95">
      <div className="flex items-center justify-between px-6 md:px-12 lg:px-20 py-3.5">
        {/* Logo */}
        <a href="#" className="flex shrink-0 items-center gap-2 text-xl font-semibold tracking-tight text-foreground">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-4 w-4" />
          </span>
          JobPulse
        </a>

        {/* 桌面端：多分区导航 */}
        <div className="hidden lg:flex items-center gap-1">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="relative group">
              <button className="flex items-center gap-1 px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                {section.label}
                <ChevronDown className="h-3 w-3 opacity-50" />
              </button>
              {/* 下拉菜单 */}
              <div className="absolute top-full left-0 pt-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                <div className="rounded-xl border border-border/60 bg-card p-2 min-w-[160px] shadow-dashboard">
                  {section.items.map((item) => (
                    <a
                      key={item.name}
                      href={item.href}
                      className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
                    >
                      {item.name}
                    </a>
                  ))}
                </div>
              </div>
            </div>
          ))}
          <a
            href="#pricing"
            className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            定价
          </a>
        </div>

        {/* 右侧操作区 */}
        <div className="flex items-center gap-3">
          <a
            href="#"
            className="hidden md:block text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            登录
          </a>
          <ThemeToggle />
          <a href="/dashboard">
            <Button variant="primary" size="sm" className="px-5 text-sm font-medium">
              免费开始
            </Button>
          </a>
          {/* 移动端汉堡 */}
          <button
            className="lg:hidden h-9 w-9 inline-flex items-center justify-center text-foreground"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="菜单"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* 移动端展开菜单 */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-border/40 bg-background px-6 py-4 space-y-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label}>
              <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">
                {section.label}
              </div>
              <div className="space-y-1">
                {section.items.map((item) => (
                  <a
                    key={item.name}
                    href={item.href}
                    className="block py-1.5 text-sm text-foreground"
                    onClick={() => setMobileOpen(false)}
                  >
                    {item.name}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </nav>
  );
}
