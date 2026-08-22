import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  hint,
  className,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  hint?: string;
  className?: string;
}) {
  return (
    <Card className={cn("card-interactive group relative overflow-hidden", className)}>
      {/* Brand wash that fades in on hover — keeps the resting state calm. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-brand-gradient opacity-0 transition-opacity duration-300 group-hover:opacity-[0.06]"
      />
      <CardContent className="relative flex items-start justify-between p-5">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight tabular-nums">{value}</p>
          {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
        </div>
        <div className="rounded-lg bg-primary/10 p-2.5 text-primary transition-transform duration-300 group-hover:scale-110">
          <Icon className="h-4 w-4" />
        </div>
      </CardContent>
    </Card>
  );
}
