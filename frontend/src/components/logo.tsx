import { useId } from "react";
import { cn } from "@/lib/utils";

/**
 * Aventrix brand marks — two separate marks, never combined into one lockup.
 *
 * `LogoMark` is the compact icon: a bold, symmetric X filling a gradient
 * tile, meant for tight spots (mobile top bar, empty-state pages, the
 * favicon). `Wordmark` is the full name set in text, with the final "x"
 * swapped for a custom glyph whose lower-right stroke keeps going past the
 * baseline as a tail. The two are drawn from unrelated geometry on purpose —
 * the icon needs to read as a balanced mark at 16px, the wordmark's glyph is
 * a large, decorative flourish — so keep them independent if either changes.
 */

/** Gradient stops, kept in one place so every mark uses the same brand ramp. */
function BrandGradient({ id }: { id: string }) {
  return (
    <linearGradient id={id} x1="0" y1="0" x2="1" y2="1" gradientUnits="objectBoundingBox">
      <stop offset="0" stopColor="#6366F1" />
      <stop offset="0.55" stopColor="#8B5CF6" />
      <stop offset="1" stopColor="#D946EF" />
    </linearGradient>
  );
}

/** The app-icon form: a bold, symmetric X on a gradient tile. Kept in sync with public/favicon.svg. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" fill="none" className={cn("h-9 w-9 shrink-0", className)} aria-hidden>
      <defs>
        <BrandGradient id="aventrix-tile" />
        <clipPath id="aventrix-tile-clip">
          <rect width="64" height="64" rx="18" />
        </clipPath>
      </defs>
      <g clipPath="url(#aventrix-tile-clip)">
        <rect width="64" height="64" fill="url(#aventrix-tile)" />
        <g stroke="white" strokeWidth="9" strokeLinecap="round">
          <path d="M16 16 L48 48" />
          <path d="M48 16 L16 48" />
        </g>
      </g>
    </svg>
  );
}

/**
 * The wordmark's final glyph on its own: an "x" built from two strokes
 * crossing at dead centre of the x-height box, where the descending stroke
 * keeps going in the same straight line past the baseline for a tail.
 * viewBox is "0 3 30 31" — content sits at x:2–27, y:6–31, with the crossing
 * point at (18, 15), the exact centre of the x-height box (x:9–27, y:6–24).
 */
function LogoGlyph({ className, gradientId }: { className?: string; gradientId: string }) {
  return (
    <svg viewBox="0 3 30 31" fill="none" className={className} aria-hidden>
      <defs>
        <BrandGradient id={gradientId} />
      </defs>
      <g stroke={`url(#${gradientId})`} strokeWidth="3.4" strokeLinecap="round">
        <path d="M9 6 L27 24" />
        <path d="M27 6 L2 31" />
      </g>
    </svg>
  );
}

export interface LogoProps {
  className?: string;
  /** Icon only, no wordmark. */
  mark?: boolean;
  size?: "sm" | "md" | "lg";
}

const MARK_SIZE = { sm: "h-7 w-7", md: "h-9 w-9", lg: "h-12 w-12" } as const;
const TEXT_SIZE = { sm: "text-base", md: "text-lg", lg: "text-2xl" } as const;

/** Renders exactly one of the two marks — the icon and the wordmark are never shown side by side. */
export function Logo({ className, mark = false, size = "md" }: LogoProps) {
  return mark ? (
    <LogoMark className={cn(MARK_SIZE[size], className)} />
  ) : (
    <Wordmark className={cn(TEXT_SIZE[size], className)} />
  );
}

/**
 * "Aventri" as live text plus the glyph as the final "x", so its tail can
 * drop below the baseline. The em-based sizing is derived from Inter's
 * lowercase x-height (~0.535em): the glyph's own x-height band (18 of its 31
 * viewBox units) is scaled to exactly 0.535em, which is what keeps the
 * crossing centred at cap height whatever font-size the caller sets. The
 * negative margin then pulls the tail (the remaining units, below the
 * viewBox's baseline row) down past the text baseline instead of the glyph
 * floating above it.
 */
export function Wordmark({ className }: { className?: string }) {
  const gradientId = useId();
  return (
    <span className={cn("flex items-baseline font-semibold tracking-tight text-foreground", className)}>
      <span>Aventri</span>
      <LogoGlyph
        gradientId={gradientId}
        className="mb-[-0.297em] h-[0.921em] w-[0.892em] shrink-0 self-baseline"
      />
    </span>
  );
}
