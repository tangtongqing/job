"use client";

import { useRef, useState } from "react";
import { Play, Square } from "lucide-react";
import { cn } from "@/lib/utils";

type PlaybackMode = "autoplay" | "controllable" | "hover";

export function ProductFilm({
  src,
  label,
  className,
  children,
  playback = "autoplay",
}: {
  src: string;
  label: string;
  className?: string;
  children: React.ReactNode;
  playback?: PlaybackMode;
}) {
  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(playback !== "hover");
  const videoRef = useRef<HTMLVideoElement>(null);

  function startPlayback() {
    const video = videoRef.current;
    if (!video || !video.paused) return;

    video.currentTime = 0;
    setPlaying(true);
    void video.play().catch(() => setPlaying(false));
  }

  function stopPlayback() {
    const video = videoRef.current;
    if (video) {
      video.pause();
      video.currentTime = 0;
    }
    setPlaying(false);
  }

  const hoverPlayback = playback === "hover";
  const showVideo = ready && playing;

  return (
    <div
      className={cn(
        "relative isolate overflow-hidden bg-[#f5f5f7] dark:bg-[#171719]",
        hoverPlayback && "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] focus-visible:ring-offset-2",
        className
      )}
      onMouseEnter={hoverPlayback ? startPlayback : undefined}
      onMouseLeave={hoverPlayback ? stopPlayback : undefined}
      onFocus={hoverPlayback ? startPlayback : undefined}
      onBlur={hoverPlayback ? stopPlayback : undefined}
      tabIndex={hoverPlayback ? 0 : undefined}
      aria-label={hoverPlayback ? `${label}，悬停或聚焦播放` : undefined}
    >
      <div className="relative z-0 h-full w-full" aria-hidden={showVideo}>{children}</div>
      <video
        ref={videoRef}
        aria-label={label}
        autoPlay={!hoverPlayback}
        muted
        loop
        playsInline
        preload="metadata"
        onCanPlay={() => setReady(true)}
        onLoadedData={() => setReady(true)}
        className={cn(
          "pointer-events-none absolute inset-0 z-10 h-full w-full object-cover motion-reduce:hidden",
          showVideo ? "opacity-100" : "opacity-0"
        )}
      >
        <source src={src} type={src.endsWith(".webm") ? "video/webm" : "video/mp4"} />
      </video>
      {playback === "controllable" && ready && (
        <button
          type="button"
          onClick={playing ? stopPlayback : startPlayback}
          aria-label={playing ? "停止产品演示并返回静态页面" : "从头播放产品演示"}
          aria-pressed={playing}
          className="absolute bottom-3 right-3 z-20 inline-flex min-h-9 items-center gap-1.5 rounded-full border border-white/15 bg-black/75 px-3 text-[11px] font-medium text-white shadow-sm backdrop-blur transition-colors hover:bg-black/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#a5b4fc] motion-reduce:hidden"
        >
          {playing ? <Square className="h-3 w-3 fill-current" /> : <Play className="h-3 w-3 fill-current" />}
          {playing ? "停止演示" : "播放演示"}
        </button>
      )}
      {(!ready || (hoverPlayback && !playing)) && (
        <span className="absolute bottom-3 right-3 z-20 inline-flex items-center gap-1.5 rounded-full border border-black/10 bg-white/90 px-2.5 py-1 text-[10px] text-muted-foreground backdrop-blur dark:border-white/10 dark:bg-black/70">
          <Play className="h-3 w-3" /> {hoverPlayback ? "悬停播放" : "产品实录"}
        </span>
      )}
    </div>
  );
}
