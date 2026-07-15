import type { MetadataRoute } from "next";

/**
 * PWA manifest（system-architecture.md §9.7 M0 必须）。
 * Next.js 14 Metadata Route，自动生成 /manifest.webmanifest。
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "JobPulse · 大学生招聘信息聚合与投递管理",
    short_name: "JobPulse",
    description:
      "聚合 5 大平台招聘信息，9 状态全流程管理投递，用数据看清你的求职节奏。",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#1f2937",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
      },
    ],
  };
}
