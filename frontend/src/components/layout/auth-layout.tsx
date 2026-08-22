import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Logo } from "@/components/logo";

export function AuthLayout({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4 py-12">
      <div aria-hidden className="pointer-events-none absolute inset-0 dot-grid opacity-60" />
      <div aria-hidden className="pointer-events-none absolute inset-0 aurora" />

      <div className="relative w-full max-w-sm animate-fade-up">
        <div className="mb-8 flex justify-center">
          <Link to="/" className="rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Logo size="lg" />
          </Link>
        </div>
        <div className="rounded-xl border border-border/70 bg-card/80 p-6 shadow-lg backdrop-blur-xl sm:p-8">
          <div className="mb-6 text-center">
            <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
            {description && <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>}
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
