"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

/**
 * 主题切换按钮。mounted 守卫避免 SSR 闪烁（next-themes 挂载前不知当前主题）。
 */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => setMounted(true), []);

  if (!mounted) {
    // 占位，避免布局抖动
    return <div className="h-9 w-9" />;
  }

  const isDark = theme === "dark";

  return (
    <button
      aria-label="切换主题"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="h-9 w-9 inline-flex items-center justify-center rounded-full text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}
