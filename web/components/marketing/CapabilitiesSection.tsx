"use client";

import { motion } from "framer-motion";
import {
  RefreshCw,
  Mail,
  Bell,
  CopyCheck,
  Layers,
  Download,
  Smartphone,
  Shield,
} from "lucide-react";

/**
 * 第 5 屏 · 能力全景（用户视角）。
 *
 * 替换原"产品故事"（PM 术语用户看不懂）。
 * 内容：用户能感知到的核心能力，非内部方法论。
 *
 * 布局：图标网格墙（4-2 布局），与前 4 屏都不同：
 * - Hero（居中堆叠）
 * - 痛点（居中+三列）
 * - 聚合（左右分栏）
 * - 状态机（左右分栏）
 * - 数据看板（全宽沉浸）
 * - 本屏（网格墙）
 *
 * 文案规则：每条都是"用户能做什么/能感受到什么"，禁止 PM 术语。
 */
const CAPABILITIES = [
  {
    icon: RefreshCw,
    title: "跨平台自动同步",
    desc: "每日自动采集，新岗位第一时间出现在你的列表。",
  },
  {
    icon: Mail,
    title: "邮件一键解析",
    desc: "粘贴 HR 邮件，AI 自动识别公司、岗位、时间，省去手填。",
  },
  {
    icon: Bell,
    title: "DDL 提醒推送",
    desc: "笔试、面试时间自动提醒，重要节点不再错过。",
  },
  {
    icon: CopyCheck,
    title: "智能去重",
    desc: "同一岗位多个平台发布，自动合并，列表不再重复。",
  },
  {
    icon: Layers,
    title: "批量流转",
    desc: "选中多个投递，一键改状态，省去逐条点击。",
  },
  {
    icon: Download,
    title: "数据导出",
    desc: "投递记录、状态变化一键导出，方便复盘和分享。",
  },
  {
    icon: Smartphone,
    title: "移动端随时用",
    desc: "手机粘贴邮件即可更新，求职路上也能管理。",
  },
  {
    icon: Shield,
    title: "本地优先",
    desc: "数据在你自己的设备上，不上传云端，隐私可控。",
  },
];

export function CapabilitiesSection() {
  return (
    <section id="capabilities" className="relative w-full py-32 md:py-40 px-6 scroll-mt-20">
      <div className="mx-auto max-w-5xl">
        {/* 顶部标题区 —— 居中 */}
        <div className="text-center mb-12 md:mb-16">
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.5 }}
            className="inline-block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-3"
          >
            能力全景
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-3xl md:text-4xl lg:text-5xl leading-[1.1] tracking-tight text-foreground"
          >
            不止投递管理，<br />
            还能做<em>这些</em>
          </motion.h2>
        </div>

        {/* 能力网格墙 —— 4 列（桌面）/ 2 列（移动） */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5">
          {CAPABILITIES.map((cap, i) => {
            const Icon = cap.icon;
            return (
              <motion.div
                key={cap.title}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                whileInView={{ opacity: 1, y: 0, scale: 1 }}
                viewport={{ once: false }}
                transition={{
                  duration: 0.5,
                  delay: Math.floor(i / 4) * 0.15 + (i % 4) * 0.08,
                }}
                whileHover={{ y: -4 }}
                className="rounded-2xl border border-border/60 bg-card p-5 md:p-6 transition-colors hover:border-accent/40"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-foreground mb-4">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-foreground mb-1.5">
                  {cap.title}
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {cap.desc}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
