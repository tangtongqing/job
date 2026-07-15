/**
 * Dashboard 演示数据配置（v3.1）。
 *
 * 用途：hero 里的投递看板预览，所有可变数据集中在此。
 * 后续接真实 API 时，只需把这里的常量改成从接口拉取，组件代码不动。
 *
 * 命名约定：演示数据用 DEMO_ 前缀，明确区分"占位"与"真实"。
 */

/* ---------- 顶栏 ---------- */
export const DEMO_USER = {
  /** 头像缩写，显示在顶栏右上 */
  initials: "LX",
  /** 问候语主名 */
  name: "林晓",
  greeting: "早上好",
};

/* ---------- 侧栏徽标（角标数字，体现"待处理"感） ---------- */
export const DEMO_BADGES = {
  jobs: "28", // 岗位数
  todo: "3", // 待办数
};

/* ---------- Hero 指标条 ---------- */
export interface MetricTile {
  label: string;
  value: string;
  delta: string;
}

export const DEMO_METRICS: MetricTile[] = [
  { label: "本周新增", value: "186", delta: "+32%" },
  { label: "待跟进", value: "11", delta: "3 个今天到期" },
  { label: "Offer 率", value: "4.2%", delta: "高于上月" },
];

/* ---------- 聚合来源概览 ---------- */
export interface SourceSummary {
  source: string;
  count: number;
  fresh: number;
  colorVar: string;
}

export const DEMO_SOURCE_SUMMARY: SourceSummary[] = [
  { source: "BOSS", count: 428, fresh: 36, colorVar: "--status-applied" },
  { source: "拉勾", count: 264, fresh: 18, colorVar: "--status-interview" },
  { source: "牛客", count: 217, fresh: 14, colorVar: "--status-testing" },
  { source: "实习僧", count: 191, fresh: 11, colorVar: "--accent" },
];

/* ---------- 投递趋势卡 ---------- */
export const DEMO_TREND = {
  /** 本月新投递数（count-up 目标值） */
  monthlyCount: 48,
  /** 近 30 天增量 */
  recentLabel: "近 30 天",
  increases: { label: "+12 笔试", tone: "positive" as const },
  decreases: { label: "-2 拒绝", tone: "negative" as const },
};

/* ---------- 状态分布卡（对应 9 状态机，此处展示进行中的 4 个） ---------- */
export interface StatusRow {
  label: string;
  count: number;
  /** CSS 变量名，对应 globals.css 的 --status-* token */
  colorVar: string;
}

export const DEMO_STATUS_ROWS: StatusRow[] = [
  { label: "已投递", count: 24, colorVar: "--status-applied" },
  { label: "笔试中", count: 8, colorVar: "--status-testing" },
  { label: "面试中", count: 5, colorVar: "--status-interview" },
  { label: "已拿 Offer", count: 2, colorVar: "--status-offer" },
];

/* ---------- 今日提醒 ---------- */
export interface ReminderRow {
  time: string;
  title: string;
  meta: string;
  tone: string;
}

export const DEMO_REMINDERS: ReminderRow[] = [
  {
    time: "10:30",
    title: "腾讯产品策划一面",
    meta: "会议链接已保存",
    tone: "--status-interview",
  },
  {
    time: "16:00",
    title: "美团笔试截止",
    meta: "还剩 5 小时",
    tone: "--status-testing",
  },
  {
    time: "明天",
    title: "字节 HR 跟进",
    meta: "建议发送邮件",
    tone: "--status-applied",
  },
];

/* ---------- 最近投递表 ---------- */
export interface ApplicationRow {
  date: string;
  company: string;
  role: string;
  status: string;
  /** 对应 TONE_CLASS 的 key */
  tone: string;
}

export const DEMO_APPLICATIONS: ApplicationRow[] = [
  { date: "06-24", company: "字节跳动", role: "产品经理", status: "笔试中", tone: "testing" },
  { date: "06-23", company: "美团", role: "高级产品", status: "面试中", tone: "interview" },
  { date: "06-22", company: "腾讯", role: "产品策划", status: "已投递", tone: "applied" },
  { date: "06-21", company: "小米", role: "产品实习", status: "已 Offer", tone: "offer" },
];
