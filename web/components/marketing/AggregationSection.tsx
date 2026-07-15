"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Filter, RefreshCw, Search, SlidersHorizontal } from "lucide-react";

/**
 * 第 2 屏 · 功能①信息聚合。
 *
 * 叙事作用：把"散落在多个平台"翻译成一个真实岗位收件箱。
 * 右侧不再是抽象条形图，而是来源筛选、去重提示、岗位列表和同步日志。
 */
const PLATFORMS = [
  { name: "全部", count: 1284, color: "hsl(var(--foreground))" },
  { name: "BOSS", count: 428, color: "hsl(var(--status-applied))" },
  { name: "拉勾", count: 264, color: "hsl(var(--status-interview))" },
  { name: "牛客", count: 217, color: "hsl(var(--status-testing))" },
  { name: "实习僧", count: 191, color: "hsl(var(--accent))" },
];

const JOB_ROWS = [
  {
    source: "BOSS",
    company: "字节跳动",
    title: "产品经理校招",
    tags: ["北京", "校招", "AI 产品"],
    status: "新岗位",
    color: "hsl(var(--status-applied))",
  },
  {
    source: "拉勾",
    company: "美团",
    title: "交易平台产品实习",
    tags: ["上海", "实习", "可转正"],
    status: "已去重",
    color: "hsl(var(--status-interview))",
  },
  {
    source: "牛客",
    company: "腾讯",
    title: "内容产品策划",
    tags: ["深圳", "社招", "1-3 年"],
    status: "待确认",
    color: "hsl(var(--status-testing))",
  },
  {
    source: "官网",
    company: "小米",
    title: "IoT 产品运营",
    tags: ["武汉", "校招", "投递中"],
    status: "官网同步",
    color: "hsl(var(--accent))",
  },
];

const SYNC_LOGS = ["12 个重复岗位已合并", "36 个岗位今日新增", "5 条订阅规则运行正常"];

export function AggregationSection() {
  return (
    <section id="aggregation" className="relative w-full px-6 py-32 scroll-mt-20 md:py-40">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 md:grid-cols-2 md:gap-16">
        <div className="order-2 md:order-1">
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.5 }}
            className="mb-4 inline-block text-xs font-medium uppercase tracking-wider text-muted-foreground"
          >
            信息聚合 · 收录
          </motion.span>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-3xl leading-[1.1] tracking-tight text-foreground md:text-4xl lg:text-5xl"
          >
            一个面板，<br />
            收齐 <em>5 大平台</em>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-5 max-w-md text-base leading-relaxed text-muted-foreground"
          >
            自动采集、去重、归一化。BOSS、拉勾、牛客、实习僧、企业官网的岗位进入同一张列表，筛选和收藏都在一处完成。
          </motion.p>

          <motion.ul
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-6 space-y-2.5"
          >
            {["自动采集，每日更新", "跨平台去重，同一岗位不重复", "归一化字段，统一筛选"].map(
              (item) => (
                <li key={item} className="flex items-center gap-2.5 text-sm text-foreground">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                  {item}
                </li>
              )
            )}
          </motion.ul>
        </div>

        <div className="order-1 md:order-2">
          <AggregationPreview />
        </div>
      </div>
    </section>
  );
}

function AggregationPreview() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: false }}
      transition={{ duration: 0.7, delay: 0.25 }}
      className="overflow-hidden rounded-2xl border border-border/60 bg-card shadow-dashboard"
    >
      <div className="border-b border-border/60 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-foreground">岗位收件箱</div>
            <div className="mt-0.5 text-[11px] text-muted-foreground">
              5 个来源 · 自动归一化字段
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <RefreshCw className="h-3.5 w-3.5" />
            <SlidersHorizontal className="h-3.5 w-3.5" />
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2 rounded-lg border border-border/50 bg-secondary/40 px-3 py-2 text-xs text-muted-foreground">
          <Search className="h-3.5 w-3.5" />
          <span className="min-w-0 flex-1 truncate">产品经理 · 上海 · 实习</span>
          <Filter className="h-3.5 w-3.5" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[132px_minmax(0,1fr)]">
        <div className="border-b border-border/60 p-3 md:border-b-0 md:border-r">
          <div className="grid grid-cols-2 gap-2 md:grid-cols-1">
            {PLATFORMS.map((platform, i) => (
              <motion.div
                key={platform.name}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: false }}
                transition={{ duration: 0.35, delay: 0.45 + i * 0.07 }}
                className={`rounded-lg px-2.5 py-2 ${
                  i === 0 ? "bg-secondary text-foreground" : "text-muted-foreground"
                }`}
              >
                <div className="flex items-center gap-2 text-[11px] font-medium">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: platform.color }}
                  />
                  {platform.name}
                </div>
                <div className="mt-1 text-[10px] tabular-nums text-muted-foreground">
                  {platform.count} 个岗位
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="min-w-0 p-3">
          <div className="space-y-2">
            {JOB_ROWS.map((job, i) => (
              <motion.div
                key={`${job.company}-${job.title}`}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: false }}
                transition={{ duration: 0.4, delay: 0.6 + i * 0.1 }}
                className="rounded-xl border border-border/50 bg-background p-3 transition hover:border-accent/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ background: job.color }}
                      />
                      <span className="text-[11px] text-muted-foreground">{job.source}</span>
                      <span className="truncate text-[11px] font-medium text-foreground">
                        {job.company}
                      </span>
                    </div>
                    <div className="mt-1 truncate text-sm font-semibold text-foreground">
                      {job.title}
                    </div>
                  </div>
                  <span className="shrink-0 rounded-full bg-secondary px-2 py-1 text-[10px] text-muted-foreground">
                    {job.status}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {job.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-border/50 px-2 py-0.5 text-[10px] text-muted-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
            {SYNC_LOGS.map((log, i) => (
              <motion.div
                key={log}
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: false }}
                transition={{ duration: 0.35, delay: 1 + i * 0.08 }}
                className="flex items-center gap-1.5 rounded-lg bg-secondary/50 px-2 py-2 text-[10px] text-muted-foreground"
              >
                <CheckCircle2 className="h-3.5 w-3.5 text-[hsl(var(--status-interview))]" />
                <span>{log}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
