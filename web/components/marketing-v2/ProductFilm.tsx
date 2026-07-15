"use client";

import { useState } from "react";
import { Play } from "lucide-react";
import { cn } from "@/lib/utils";

export function ProductFilm({
  src,
  label,
  className,
  children,
}: {
  src: string;
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  const [ready, setReady] = useState(false);

  return (
    <div className={cn("relative overflow-hidden bg-[#f5f5f7] dark:bg-[#171719]", className)}>
      <div className="h-full w-full" aria-hidden={ready}>{children}</div>
      <video
        aria-label={label}
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        onCanPlay={() => setReady(true)}
        className={cn(
          "absolute inset-0 h-full w-full object-cover transition-opacity duration-500 motion-reduce:hidden",
          ready ? "opacity-100" : "pointer-events-none opacity-0"
        )}
      >
        <source src={src} type={src.endsWith(".webm") ? "video/webm" : "video/mp4"} />
      </video>
      {!ready && (
        <span className="absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-full border border-black/10 bg-white/90 px-2.5 py-1 text-[10px] text-muted-foreground backdrop-blur dark:border-white/10 dark:bg-black/70">
          <Play className="h-3 w-3" /> 产品实录
        </span>
      )}
    </div>
  );
}
