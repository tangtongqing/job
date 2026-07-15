"use client";

import { motion, useScroll, useTransform } from "framer-motion";

/**
 * 营销页全局背景系统（v4 · Linear 风颗粒纹理）。
 *
 * 设计转向（真实营销型，参考 Linear）：
 * Linear 的背景极简——纯色底 + 颗粒纹理（grain），靠真实产品内容撑场。
 * 背景不再是"主角"，而是"质感底"。
 *
 * 三层叠加：
 * 1. 渐变底（fixed）—— 同色系明度渐变，亮暗各自一套
 * 2. 颗粒纹理（fixed，SVG feTurbulence）—— Linear 标志性的"胶片感"质感
 * 3. 极淡光晕（scroll 视差）—— 克制保留，制造一点点空间感
 *
 * 关键纪律：grain 不透明度极低（亮色 4% / 暗色 8%），
 * 它是"质感"不是"图案"，绝不抢戏。
 * 真正的视觉丰富度来自内容（下一步补真实产品 UI）。
 */
export function Background() {
  const { scrollYProgress } = useScroll();
  const blobX = useTransform(scrollYProgress, [0, 1], ["0%", "20%"]);
  const blobY = useTransform(scrollYProgress, [0, 1], ["0%", "40%"]);

  return (
    <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden bg-background">
      {/* 第 1 层：渐变底（同色系明度，Apple/Linear 式） */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background to-secondary/40 dark:via-background dark:to-background" />

      {/* 第 2 层：颗粒纹理（Linear 式 grain）—— SVG feTurbulence */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.04] dark:opacity-[0.08] mix-blend-overlay">
        <filter id="grainFilter">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.85"
            numOctaves="2"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grainFilter)" />
      </svg>

      {/* 第 3 层：极淡视差光晕（克制保留） */}
      <motion.div
        style={{ x: blobX, y: blobY }}
        className="absolute top-[20%] left-[10%] h-[36rem] w-[36rem] rounded-full blur-[140px]"
      >
        <div className="h-full w-full rounded-full bg-accent/[0.05] dark:bg-accent/[0.08]" />
      </motion.div>
    </div>
  );
}
