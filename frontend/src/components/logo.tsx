import { cn } from "@/lib/utils";

export function Logo({ className, mark = false }: { className?: string; mark?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <svg viewBox="0 0 64 64" fill="none" className="h-7 w-7 shrink-0">
        <defs>
          <linearGradient id="logo-gradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#6366F1" />
            <stop offset="1" stopColor="#A855F7" />
          </linearGradient>
        </defs>
        <rect width="64" height="64" rx="16" fill="url(#logo-gradient)" />
        <rect x="14" y="24" width="22" height="16" rx="8" stroke="white" strokeWidth="4" />
        <rect x="28" y="24" width="22" height="16" rx="8" stroke="white" strokeWidth="4" fill="url(#logo-gradient)" />
        <circle cx="47" cy="17" r="3.5" fill="white" />
      </svg>
      {!mark && <span className="text-base font-semibold tracking-tight">FurOfTheWeak</span>}
    </div>
  );
}
