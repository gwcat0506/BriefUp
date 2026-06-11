interface ProgressBarProps {
  pct: number;
  height?: "sm" | "md";
  color?: string;
  duration?: number;
  className?: string;
}

export default function ProgressBar({
  pct,
  height = "md",
  color,
  duration = 700,
  className = "",
}: ProgressBarProps) {
  const h = height === "sm" ? "h-1.5" : "h-2.5";
  const fillStyle: React.CSSProperties = {
    width: `${pct}%`,
    transition: `width ${duration}ms`,
    ...(color ? { background: color } : {}),
  };

  return (
    <div className={`w-full bg-[#F3F4F6] rounded-full ${h} overflow-hidden ${className}`}>
      <div
        className={`${h} rounded-full${color ? "" : " bg-gradient-to-r from-[#10B981] to-[#34D399]"}`}
        style={fillStyle}
      />
    </div>
  );
}
