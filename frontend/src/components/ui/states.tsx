import { AlertTriangle, Loader2, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LoadingState({ label, className }: { label?: string; className?: string }) {
  const { t } = useTranslation();
  return (
    <div
      className={cn("flex flex-col items-center justify-center gap-3 py-16 text-muted-foreground", className)}
      role="status"
    >
      <span className="relative flex h-9 w-9 items-center justify-center">
        <span aria-hidden className="absolute inset-0 rounded-full bg-primary/10" />
        <Loader2 className="h-5 w-5 animate-spin text-primary" />
      </span>
      <p className="text-sm">{label ?? t("states.loading")}</p>
    </div>
  );
}

export function ErrorState({
  title,
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="flex animate-fade-up flex-col items-center justify-center gap-3 rounded-xl border border-destructive/25 bg-destructive/5 py-16 text-center">
      <div className="rounded-full bg-destructive/10 p-3">
        <AlertTriangle className="h-5 w-5 text-destructive" />
      </div>
      <div>
        <p className="text-sm font-medium">{title ?? t("states.errorTitle")}</p>
        {message && <p className="mt-1 max-w-sm px-6 text-sm text-muted-foreground">{message}</p>}
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          {t("common.retry")}
        </Button>
      )}
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="relative flex animate-fade-up flex-col items-center justify-center gap-3 overflow-hidden rounded-xl border border-dashed border-border py-16 text-center">
      <div aria-hidden className="pointer-events-none absolute inset-0 dot-grid opacity-40" />
      {Icon && (
        <div className="relative rounded-2xl bg-brand-gradient p-[1px] shadow-sm">
          <div className="rounded-[calc(1rem-1px)] bg-card p-3">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
      )}
      <div className="relative">
        <p className="text-sm font-medium">{title}</p>
        {description && <p className="mt-1 max-w-sm px-6 text-sm text-muted-foreground">{description}</p>}
      </div>
      {action && <div className="relative">{action}</div>}
    </div>
  );
}

/** Neutral loading placeholder with a light sweep, for card/table skeletons. */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("relative overflow-hidden rounded-md bg-muted", className)}>
      <div
        aria-hidden
        className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-foreground/10 to-transparent"
      />
    </div>
  );
}
