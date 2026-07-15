"use client";

import { motion } from "framer-motion";
import { ArrowRight, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DashboardPreview } from "./DashboardPreview";

/**
 * Hero 区（v3 · 产品主角改造）。
 *
 * 设计转向（2026-06-24，与用户确认）：
 * - 去掉背景视频 + 遮罩，背景改由全局 <Background/> 提供（点阵+光晕+视差）。
 * - dashboard 从装饰浮层改为"实体主角"，内部加动态演示（数字滚动 / 图表绘制 / 状态浮现）。
 * - 理念：让产品本身动起来（Apple 展示 iPhone 的路数），而非靠背景装饰。
 *
 * 文案定位：作品集展示型（BRAND.md §1.2）。
 * 主标题英文保留 Instrument Serif italic 的设计灵魂；
 * 中文价值行作副标题，避免中文无 italic 字形导致风格断层。
 */
export function Hero() {
  return (
    <section className="relative flex min-h-[100dvh] w-full flex-col items-center justify-center overflow-hidden pt-20">
      {/* 内容层 */}
      <div className="relative z-10 flex flex-col items-center w-full px-6 pt-8 md:pt-12 pb-16">
        {/* 1. Badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-4 py-1.5 text-sm text-muted-foreground font-body mb-6"
        >
          聚合 5 大平台 · 9 状态全流程管理
        </motion.div>

        {/* 2. Headline —— 英文主标题，"rhythm" 用 italic */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-center font-display text-5xl md:text-6xl lg:text-[5rem] leading-[0.95] tracking-tight text-foreground max-w-xl"
        >
          Your job search, <em>in rhythm</em>.
        </motion.h1>

        {/* 3. Subheadline —— 中文价值行 */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-4 text-center text-base md:text-lg text-muted-foreground max-w-[650px] leading-relaxed font-body"
        >
          告别在 BOSS、拉勾、牛客、实习僧、企业官网之间来回切换。
          聚合招聘信息、管理投递状态、用数据看清你的求职节奏。
        </motion.p>

        {/* 4. CTA —— 真实营销型：免费开始 + 看产品 */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-5 flex items-center gap-3"
        >
          <a href="/dashboard">
            <Button variant="primary" size="default">
              免费开始
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </a>
          <a href="/dashboard">
            <Button variant="outline" size="default">
              <BookOpen className="mr-1.5 h-4 w-4" />
              看产品演示
            </Button>
          </a>
        </motion.div>

        {/* 5. Dashboard 预览（动态演示版，向下溢出被裁切） */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-8 w-full max-w-5xl"
        >
          <DashboardPreview />
        </motion.div>
      </div>
    </section>
  );
}
