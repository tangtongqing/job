"use client";

import { motion } from "framer-motion";
import { Activity, Check, ArrowRight, Sparkles } from "lucide-react";

/**
 * 第 6 屏 · 定价 + 终极 CTA。
 *
 * 布局：居中三列定价卡（Free / Pro / Team），Pro 居中高亮。
 * 顶部标注免费试用政策（真实营销型定位）——
 * 这是作品集展示型定位的诚实声明（BRAND.md §1.2）。
 *
 * 定价分级来自 evolution-roadmap.md §5：
 * - Free：基础采集 + 投递管理（永久免费，无需注册）
 * - Pro：AI 解析额度 + 多源订阅 + 数据导出（主力变现）
 * - Team：组织共享（远期）
 *
 * 底部接终极 CTA 区，收口整个营销页。
 */
const TIERS = [
  {
    name: "Free",
    price: "¥0",
    period: "永久免费",
    tagline: "够用，且持续用",
    highlighted: false,
    features: [
      "基础招聘信息采集",
      "9 状态投递管理",
      "DDL 提醒",
      "基础看板（趋势 + 分布）",
    ],
    cta: "免费开始",
    note: "永久免费，无需注册",
  },
  {
    name: "Pro",
    price: "¥29",
    period: "/ 月",
    tagline: "为认真求职者设计",
    highlighted: true,
    features: [
      "Free 全部能力",
      "AI 邮件解析（100 次/月）",
      "多源订阅（5 条规则）",
      "数据导出 + DDL 推送",
      "投递漏斗深度分析",
    ],
    cta: "开始试用",
    note: "最受欢迎",
  },
  {
    name: "Team",
    price: "¥99",
    period: "/ 月 · 3 席位",
    tagline: "为求职互助场景",
    highlighted: false,
    features: [
      "Pro 全部能力",
      "组织共享看板",
      "成员角色管理",
      "批量导入",
      "导师视图",
    ],
    cta: "联系销售",
    note: "团队场景",
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="relative w-full py-32 md:py-40 px-6 scroll-mt-20">
      <div className="mx-auto max-w-6xl">
        {/* 顶部标题区 */}
        <div className="text-center mb-4">
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.5 }}
            className="inline-block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-3"
          >
            定价
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-3xl md:text-4xl lg:text-5xl leading-[1.1] tracking-tight text-foreground"
          >
            选一个<em>适合你</em>的节奏
          </motion.h2>
        </div>

        {/* 定位说明 —— 真实营销型 */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: false }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-center text-xs text-muted-foreground mb-12 max-w-xl mx-auto"
        >
          14 天免费试用全部 Pro 功能，无需信用卡，随时取消。
        </motion.p>

        {/* 三列定价卡 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-5 items-stretch">
          {TIERS.map((tier, i) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false }}
              transition={{ duration: 0.6, delay: 0.3 + i * 0.12 }}
              className={`relative rounded-2xl p-7 md:p-8 flex flex-col ${
                tier.highlighted
                  ? "bg-foreground text-background shadow-dashboard md:scale-105 md:-translate-y-1"
                  : "bg-card border border-border/60 text-foreground"
              }`}
            >
              {/* 高亮标签 */}
              {tier.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 inline-flex items-center gap-1 rounded-full bg-accent px-3 py-1 text-[10px] font-medium text-accent-foreground">
                  <Sparkles className="h-3 w-3" />
                  最受欢迎
                </div>
              )}

              {/* 档位名 + tagline */}
              <div className="mb-5">
                <h3
                  className={`text-lg font-semibold ${
                    tier.highlighted ? "text-background" : "text-foreground"
                  }`}
                >
                  {tier.name}
                </h3>
                <p
                  className={`text-xs mt-1 ${
                    tier.highlighted ? "text-background/70" : "text-muted-foreground"
                  }`}
                >
                  {tier.tagline}
                </p>
              </div>

              {/* 价格 */}
              <div className="mb-6">
                <span className="text-3xl font-bold tabular-nums">{tier.price}</span>
                <span
                  className={`text-sm ml-1.5 ${
                    tier.highlighted ? "text-background/70" : "text-muted-foreground"
                  }`}
                >
                  {tier.period}
                </span>
              </div>

              {/* 功能列表 */}
              <ul className="space-y-2.5 mb-8 flex-1">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <Check
                      className={`h-4 w-4 mt-0.5 shrink-0 ${
                        tier.highlighted ? "text-accent" : "text-accent"
                      }`}
                    />
                    <span
                      className={
                        tier.highlighted ? "text-background/90" : "text-foreground"
                      }
                    >
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <button
                className={`w-full rounded-full px-5 py-3 text-sm font-medium transition-colors ${
                  tier.highlighted
                    ? "bg-background text-foreground hover:bg-background/90"
                    : "bg-foreground text-background hover:bg-foreground/90"
                }`}
              >
                {tier.cta}
              </button>

              {/* 档位说明 */}
              <p
                className={`text-[10px] text-center mt-3 ${
                  tier.highlighted ? "text-background/50" : "text-muted-foreground"
                }`}
              >
                {tier.note}
              </p>
            </motion.div>
          ))}
        </div>

        {/* 终极 CTA 区 —— 收口整个营销页 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mt-20 md:mt-24 text-center"
        >
          <h3 className="font-display text-2xl md:text-3xl lg:text-4xl tracking-tight text-foreground mb-3">
            准备好<em>看清</em>你的求职节奏了吗？
          </h3>
          <p className="text-sm text-muted-foreground mb-6">
            无需信用卡，14 天免费试用全部 Pro 功能。
          </p>
          <button className="inline-flex items-center gap-2 rounded-full bg-foreground px-7 py-3.5 text-sm font-medium text-background hover:bg-foreground/90 transition-colors">
            免费开始
            <ArrowRight className="h-4 w-4" />
          </button>
        </motion.div>

        {/* Footer */}
        <footer className="mt-24 md:mt-32 pt-8 border-t border-border/40 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-sm font-semibold tracking-tight text-foreground">
            <Activity className="mr-1.5 inline h-4 w-4 align-[-2px]" />
            JobPulse
          </div>
          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">产品</a>
            <a href="#" className="hover:text-foreground transition-colors">定价</a>
            <a href="#" className="hover:text-foreground transition-colors">设计过程</a>
          </div>
          <div className="text-[11px] text-muted-foreground">
            © JobPulse · {new Date().getFullYear()}
          </div>
        </footer>
      </div>
    </section>
  );
}
