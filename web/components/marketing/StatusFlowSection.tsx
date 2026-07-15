"use client";

import { motion } from "framer-motion";
import {
  CalendarClock,
  CheckCircle2,
  FileText,
  MailCheck,
  Send,
  Star,
  Trophy,
  Users,
} from "lucide-react";

/**
 * 第 3 屏 · 功能②投递状态机。
 *
 * 叙事作用：把"状态记不住"翻译成投递管道、邮件解析和提醒。
 * 桌面端显示紧凑管道，移动端改为竖向时间线，避免 5 节点横向挤压。
 */
const STATES = [
  { icon: Star, label: "收藏", color: "--status-no-response", count: 36 },
  { icon: Send, label: "已投递", color: "--status-applied", count: 24 },
  { icon: FileText, label: "笔试中", color: "--status-testing", count: 8 },
  { icon: Users, label: "面试中", color: "--status-interview", count: 5 },
  { icon: Trophy, label: "已 Offer", color: "--status-offer", count: 2 },
];

const PIPELINE_CARDS = [
  {
    stage: "已投递",
    company: "腾讯",
    role: "内容产品策划",
    meta: "06-22 自动记录",
    color: "--status-applied",
  },
  {
    stage: "笔试中",
    company: "字节跳动",
    role: "产品经理校招",
    meta: "今天 20:00 截止",
    color: "--status-testing",
  },
  {
    stage: "面试中",
    company: "美团",
    role: "交易产品实习",
    meta: "明天 10:30 一面",
    color: "--status-interview",
  },
  {
    stage: "已 Offer",
    company: "小米",
    role: "IoT 产品运营",
    meta: "待确认入职时间",
    color: "--status-offer",
  },
];

export function StatusFlowSection() {
  return (
    <section id="status" className="relative w-full px-6 py-32 scroll-mt-20 md:py-40">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 md:grid-cols-2 md:gap-16">
        <div className="order-1">
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.5 }}
            className="mb-4 inline-block text-xs font-medium uppercase tracking-wider text-muted-foreground"
          >
            投递管理 · 状态机
          </motion.span>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-3xl leading-[1.1] tracking-tight text-foreground md:text-4xl lg:text-5xl"
          >
            从收藏到 Offer，<br />
            <em>9 个状态</em>全流程
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-5 max-w-md text-base leading-relaxed text-muted-foreground"
          >
            每一次状态变化都有记录。粘贴邮件一键解析、批量流转、状态修正，再也不会忘记谁发了笔试、谁约了面试。
          </motion.p>

          <motion.ul
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: false }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-6 space-y-2.5"
          >
            {[
              "粘贴邮件后 AI 自动解析状态",
              "投递时间线，未来和历史分离",
              "异常状态修正，防止漏环节",
            ].map((item) => (
              <li key={item} className="flex items-center gap-2.5 text-sm text-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                {item}
              </li>
            ))}
          </motion.ul>
        </div>

        <StatusWorkspace />
      </div>
    </section>
  );
}

function StatusWorkspace() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: false }}
      transition={{ duration: 0.7, delay: 0.25 }}
      className="order-2 overflow-hidden rounded-2xl border border-border/60 bg-card shadow-dashboard"
    >
      <div className="border-b border-border/60 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-foreground">投递管道</div>
            <div className="mt-0.5 text-[11px] text-muted-foreground">
              9 状态 · 邮件解析 · 批量流转
            </div>
          </div>
          <span className="rounded-full bg-secondary px-2.5 py-1 text-[10px] text-muted-foreground">
            实时同步
          </span>
        </div>
      </div>

      <div className="p-4">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false }}
          transition={{ duration: 0.4, delay: 0.45 }}
          className="rounded-xl border border-border/50 bg-background p-3"
        >
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-foreground">
              <MailCheck className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium text-foreground">HR 邮件已解析</div>
              <div className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                请于今晚 20:00 前完成笔试，已识别为笔试中，并生成截止提醒。
              </div>
            </div>
            <CheckCircle2 className="h-4 w-4 shrink-0 text-[hsl(var(--status-interview))]" />
          </div>
        </motion.div>

        <DesktopPipeline />
        <MobileTimeline />

        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {PIPELINE_CARDS.map((card, i) => (
            <motion.div
              key={`${card.company}-${card.stage}`}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false }}
              transition={{ duration: 0.4, delay: 0.8 + i * 0.08 }}
              className="rounded-xl border border-border/50 bg-background p-3"
            >
              <div className="flex items-center justify-between gap-2">
                <span
                  className="rounded-full px-2 py-0.5 text-[10px]"
                  style={{
                    background: `hsl(var(${card.color}) / 0.14)`,
                    color: `hsl(var(${card.color}))`,
                  }}
                >
                  {card.stage}
                </span>
                <CalendarClock className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div className="mt-2 text-sm font-semibold text-foreground">
                {card.company}
              </div>
              <div className="mt-0.5 text-[11px] text-muted-foreground">
                {card.role}
              </div>
              <div className="mt-2 text-[10px] text-muted-foreground">{card.meta}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

function DesktopPipeline() {
  return (
    <div className="mt-4 hidden md:block">
      <div className="flex items-center justify-between gap-1">
        {STATES.map((state, i) => {
          const Icon = state.icon;
          const isLast = i === STATES.length - 1;
          return (
            <div key={state.label} className="flex flex-1 items-center">
              <motion.div
                initial={{ opacity: 0.35, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: false }}
                transition={{ duration: 0.45, delay: 0.55 + i * 0.12 }}
                className="flex min-w-[56px] flex-col items-center gap-1.5"
              >
                <div
                  className="flex h-10 w-10 items-center justify-center rounded-full border"
                  style={{
                    borderColor: `hsl(var(${state.color}))`,
                    background: `hsl(var(${state.color}) / 0.1)`,
                  }}
                >
                  <Icon className="h-4 w-4" style={{ color: `hsl(var(${state.color}))` }} />
                </div>
                <span className="whitespace-nowrap text-[10px] font-medium text-foreground">
                  {state.label}
                </span>
                <span className="text-[10px] tabular-nums" style={{ color: `hsl(var(${state.color}))` }}>
                  {state.count}
                </span>
              </motion.div>

              {!isLast && (
                <div className="relative mx-1 h-0.5 flex-1 overflow-hidden rounded-full bg-border">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: "100%" }}
                    viewport={{ once: false }}
                    transition={{ duration: 0.35, delay: 0.7 + i * 0.12 }}
                    className="absolute inset-y-0 left-0 rounded-full"
                    style={{ background: `hsl(var(${state.color}))` }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MobileTimeline() {
  return (
    <div className="mt-4 space-y-2 md:hidden">
      {STATES.map((state, i) => {
        const Icon = state.icon;
        return (
          <motion.div
            key={state.label}
            initial={{ opacity: 0, x: -12 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: false }}
            transition={{ duration: 0.35, delay: 0.55 + i * 0.08 }}
            className="flex items-center gap-3 rounded-lg border border-border/50 bg-background px-3 py-2"
          >
            <div
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
              style={{
                background: `hsl(var(${state.color}) / 0.12)`,
                color: `hsl(var(${state.color}))`,
              }}
            >
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium text-foreground">{state.label}</div>
              <div className="text-[10px] text-muted-foreground">
                {i === STATES.length - 1 ? "主流程终点" : "进入下一状态时自动记录"}
              </div>
            </div>
            <span className="text-[11px] tabular-nums text-muted-foreground">
              {state.count}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
