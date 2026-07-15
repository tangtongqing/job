"use client";

import { Navbar } from "@/components/marketing/Navbar";
import { Hero } from "@/components/marketing/Hero";
import { Background } from "@/components/marketing/Background";
import { PainPointsSection } from "@/components/marketing/PainPointsSection";
import { AggregationSection } from "@/components/marketing/AggregationSection";
import { StatusFlowSection } from "@/components/marketing/StatusFlowSection";
import { DataDashboardSection } from "@/components/marketing/DataDashboardSection";
import { CapabilitiesSection } from "@/components/marketing/CapabilitiesSection";
import { PricingSection } from "@/components/marketing/PricingSection";
import { BottomNav } from "@/components/marketing/BottomNav";

/**
 * 落地页（v3.1）。
 *
 * 架构：多屏滚动叙事。
 * - <Background/> 全局固定背景（点阵+光晕+视差），所有屏共享。
 * - <Navbar/> 顶部固定导航。
 * - 第 0 屏 Hero / 第 1 屏 痛点 / 第 2-6 屏 待追加。
 */
export default function LandingPage() {
  return (
    <main className="relative font-body">
      {/* 全局背景（fixed，所有屏共享） */}
      <Background />

      {/* 顶部导航 */}
      <Navbar />

      {/* 第 0 屏 · Hero */}
      <Hero />

      {/* 第 1 屏 · 痛点共鸣 */}
      <PainPointsSection />

      {/* 第 2 屏 · 信息聚合 */}
      <AggregationSection />

      {/* 第 3 屏 · 投递状态机 */}
      <StatusFlowSection />

      {/* 第 4 屏 · 数据看板（全宽沉浸式） */}
      <DataDashboardSection />

      {/* 第 5 屏 · 能力全景（图标网格墙） */}
      <CapabilitiesSection />

      {/* 第 6 屏 · 定价 + 终极 CTA + Footer */}
      <PricingSection />

      {/* 底部悬浮导航 */}
      <BottomNav />
    </main>
  );
}
