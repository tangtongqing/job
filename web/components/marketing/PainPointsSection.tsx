"use client";

import { motion } from "framer-motion";
import { Layers, BrainCog, LineChart } from "lucide-react";

/**
 * 第 1 屏 · 痛点共鸣。
 *
 * 叙事作用：承接 Hero 的"产品演示"，让用户产生"对，这就是我"的共鸣，
 * 为后面三屏功能展示铺路。
 *
 * 内容来源：docs/product/pain-points-jtbd.md 真实调研痛点，非编造。
 * 痛点选取：P1 核心画像（高频跨平台投递者）的 top 3 痛点。
 */
const PAIN_POINTS = [
  {
    icon: Layers,
    title: "信息散落各处",
    desc: "投递记录分散在收藏夹、备忘录、聊天记录里，月底复盘拼不全。",
  },
  {
    icon: BrainCog,
    title: "状态记不住",
    desc: "投了 30 个岗位，谁发了笔试、谁约了面试、谁没回音，全靠脑子记。",
  },
  {
    icon: LineChart,
    title: "看不见节奏",
    desc: "瞎投一气没有复盘，不知道转化率、不知道瓶颈卡在哪一环。",
  },
];

export function PainPointsSection() {
  return (
    <section className="relative w-full py-32 md:py-40 px-6">
      <div className="mx-auto max-w-5xl">
        {/* 大标题问句 —— "投到哪了" 用 italic 强调 */}
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false }}
          transition={{ duration: 0.7 }}
          className="text-center font-display text-4xl md:text-5xl lg:text-6xl leading-[1.05] tracking-tight text-foreground max-w-3xl mx-auto"
        >
          投了 30 个岗位，<br />
          你还记得每个<em>投到哪了</em>吗？
        </motion.h2>

        {/* 3 个痛点卡 —— 错峰淡入 */}
        <div className="mt-16 md:mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {PAIN_POINTS.map((point, i) => {
            const Icon = point.icon;
            return (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: false }}
                transition={{ duration: 0.6, delay: 0.2 + i * 0.15 }}
                className="rounded-2xl border border-border/60 bg-card p-7 md:p-8"
              >
                {/* 图标圆 */}
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary text-foreground mb-5">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {point.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {point.desc}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
