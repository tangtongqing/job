/**
 * 9 状态机配置 —— code / 中文 label / terminal / color / 合法流转。
 *
 * 颜色呼应 docs/design/DESIGN.md，applied 用蓝系。
 * 合法流转映射与后端 TRANSITIONS（api-contract §四）一致。
 */

export interface StatusConfig {
  code: string;
  label: string;
  terminal: boolean;
  /** Tailwind 文字色类（呼应 DESIGN.md 状态色） */
  textClass: string;
  /** Tailwind 背景色类（Badge 用） */
  badgeClass: string;
  /** 合法的下一状态 code 列表 */
  nextStatuses: string[];
}

export const APPLICATION_STATUSES: StatusConfig[] = [
  {
    code: "applied",
    label: "已投递",
    terminal: false,
    textClass: "text-blue-600 dark:text-blue-400",
    badgeClass: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
    nextStatuses: ["test", "interviewing", "offer_pending", "withdrawn", "rejected", "no_response"],
  },
  {
    code: "test",
    label: "笔试/测评",
    terminal: false,
    textClass: "text-orange-600 dark:text-orange-400",
    badgeClass: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
    nextStatuses: ["interviewing", "offer_pending", "withdrawn", "rejected", "no_response"],
  },
  {
    code: "interviewing",
    label: "面试中",
    terminal: false,
    textClass: "text-purple-600 dark:text-purple-400",
    badgeClass: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
    nextStatuses: ["interviewing", "offer_pending", "withdrawn", "rejected", "no_response"],
  },
  {
    code: "offer_pending",
    label: "Offer待决定",
    terminal: false,
    textClass: "text-cyan-600 dark:text-cyan-400",
    badgeClass: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300",
    nextStatuses: ["offer_accepted", "offer_declined", "withdrawn", "rejected", "no_response"],
  },
  {
    code: "offer_accepted",
    label: "Offer已接受",
    terminal: true,
    textClass: "text-green-600 dark:text-green-400",
    badgeClass: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
    nextStatuses: [],
  },
  {
    code: "offer_declined",
    label: "Offer已婉拒",
    terminal: true,
    textClass: "text-gray-600 dark:text-gray-400",
    badgeClass: "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300",
    nextStatuses: [],
  },
  {
    code: "rejected",
    label: "公司拒绝",
    terminal: true,
    textClass: "text-red-600 dark:text-red-400",
    badgeClass: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
    nextStatuses: [],
  },
  {
    code: "no_response",
    label: "无回应关闭",
    terminal: true,
    textClass: "text-gray-500 dark:text-gray-500",
    badgeClass: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
    nextStatuses: [],
  },
  {
    code: "withdrawn",
    label: "主动撤回",
    terminal: true,
    textClass: "text-gray-500 dark:text-gray-500",
    badgeClass: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
    nextStatuses: [],
  },
];

const STATUS_MAP: Record<string, StatusConfig> = Object.fromEntries(
  APPLICATION_STATUSES.map((s) => [s.code, s])
);

export function getStatusConfig(code: string): StatusConfig | undefined {
  return STATUS_MAP[code];
}

export function getStatusLabel(code: string): string {
  return STATUS_MAP[code]?.label || code;
}

export function isTerminal(code: string): boolean {
  return STATUS_MAP[code]?.terminal ?? false;
}

export function getNextStatuses(code: string): string[] {
  return STATUS_MAP[code]?.nextStatuses ?? [];
}

export const JOB_STATUS_LABELS: Record<string, string> = {
  displaying: "展示中",
  closed: "已关闭",
};

// 漏斗展示顺序
export const FUNNEL_ORDER = [
  "applied",
  "test",
  "interviewing",
  "offer_pending",
  "offer_accepted",
];
