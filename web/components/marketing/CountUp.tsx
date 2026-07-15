"use client";

import { useEffect, useRef, useState } from "react";

/**
 * CountUp —— Apple 标志性的数字滚动动效。
 * 元素进入视口后开始从 0 滚动到目标值，用 IntersectionObserver 触发。
 *
 * 用于 dashboard 演示：投递数 / 状态计数 从 0 滚到真实值。
 */
export function CountUp({
  end,
  duration = 1400,
  suffix = "",
  className,
  delay = 0,
}: {
  end: number;
  duration?: number;
  suffix?: string;
  className?: string;
  delay?: number;
}) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const started = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const start = () => {
      if (started.current) return;
      started.current = true;

      const startTime = performance.now() + delay;

      const tick = (now: number) => {
        if (now < startTime) {
          requestAnimationFrame(tick);
          return;
        }
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // easeOutCubic —— 先快后慢，Apple 式缓动
        const eased = 1 - Math.pow(1 - progress, 3);
        setCount(Math.round(end * eased));
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) start();
      },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [end, duration, delay]);

  return (
    <span ref={ref} className={className}>
      {count}
      {suffix}
    </span>
  );
}
