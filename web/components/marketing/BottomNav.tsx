"use client";

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";

/**
 * 底部悬浮导航（v4 · Viktor 样式，去 CTA）。
 *
 * 修订（响应反馈第 3 点）：去掉重复的 CTA 按钮。
 * 顶部导航已有「免费开始」+ 登录，底部再放 CTA 是重复。
 * 底部导航改为纯锚点快速跳转（长页面的"电梯"），更符合成熟落地页做法。
 *
 * 样式：实体胶囊，fixed bottom-6 居中。
 * 行为：滚动超过首屏才显示（避免遮挡 hero），向下滚隐藏、向上滚/停下显示。
 */
const QUICK_LINKS = [
  { label: "聚合", href: "#aggregation" },
  { label: "投递", href: "#status" },
  { label: "看板", href: "#dashboard" },
  { label: "功能", href: "#capabilities" },
  { label: "定价", href: "#pricing" },
];

export function BottomNav() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      // 滚动超过一屏高度才显示
      setVisible(window.scrollY > window.innerHeight * 0.8);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div
      className={`fixed bottom-4 left-1/2 z-50 hidden -translate-x-1/2 transition-all duration-300 sm:block md:bottom-6 ${
        visible
          ? "opacity-100 translate-y-0"
          : "opacity-0 translate-y-4 pointer-events-none"
      }`}
    >
      <div
        className="flex items-center gap-1 rounded-full border border-border/60 bg-card px-2 py-2"
        style={{
          boxShadow: "var(--shadow-dashboard)",
        }}
      >
        {/* Logo 标记 */}
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Activity className="h-3.5 w-3.5" />
        </span>

        {/* 快速锚点 —— 长页面的"电梯" */}
        {QUICK_LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="hidden sm:block rounded-full px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
          >
            {link.label}
          </a>
        ))}
      </div>
    </div>
  );
}
