import {
  ChevronDown,
  ChevronRight,
  Clock,
  Copy,
  ExternalLink,
  Fingerprint,
  History,
  FolderKanban,
  Lock,
  MapPin,
  Monitor,
  Server,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Tablet,
  Trash2,
} from "lucide-react";
import { useState, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Pagination } from "@/components/ui/pagination";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useDeleteLink, useLinkVisits, useUpdateLink } from "@/hooks/use-links";
import { useToast } from "@/hooks/use-toast";
import { cn, formatDate, formatDateTime, formatNumber } from "@/lib/utils";
import type { Link, TriState, Visit } from "@/lib/types";

const VISITS_PAGE_SIZE = 5;

// Stops a click on an interactive child (link, button, switch) from also
// toggling the row's expand/collapse state via the row's own onClick.
function stopRowToggle(e: MouseEvent) {
  e.stopPropagation();
}

function triStateBadgeVariant(value: TriState): "destructive" | "outline" | "secondary" {
  if (value === "YES") return "destructive";
  if (value === "NO") return "outline";
  return "secondary";
}

function deviceIcon(deviceType: string | null) {
  if (deviceType === "mobile") return Smartphone;
  if (deviceType === "tablet") return Tablet;
  return Monitor;
}

function botConfidenceBadgeVariant(value: string): "destructive" | "outline" | "secondary" {
  if (value === "LIKELY_BOT") return "destructive";
  if (value === "POSSIBLE_BOT") return "secondary";
  if (value === "LIKELY_HUMAN") return "outline";
  return "secondary";
}

// Converts a 2-letter ISO country code to its flag emoji (regional indicator
// symbols) — no image/icon set needed.
function countryFlag(countryCode: string | null): string | null {
  if (!countryCode || countryCode.length !== 2) return null;
  const codePoints = [...countryCode.toUpperCase()].map((c) => 127397 + c.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

// Converts lon/lat + zoom to a raw OSM XYZ tile coordinate, plus the exact
// pixel offset of the point within that 256x256 tile (Web Mercator).
function lonLatToTilePixel(lon: number, lat: number, zoom: number) {
  const n = 2 ** zoom;
  const x = ((lon + 180) / 360) * n;
  const latRad = (lat * Math.PI) / 180;
  const y = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n;
  const tileX = Math.floor(x);
  const tileY = Math.floor(y);
  return { tileX, tileY, pixelXPct: (x - tileX) * 100, pixelYPct: (y - tileY) * 100 };
}

// Approximate-location preview: a single raw OpenStreetMap tile image with
// our own small marker dot drawn on top via CSS. Deliberately NOT the
// openstreetmap.org iframe embed — at this thumbnail size its own zoom
// controls and attribution link render larger than the map itself. A plain
// <img> has no such chrome. Zoom is tightened when we know a district/city,
// since that means the underlying geo lookup was more precise.
function LocationThumbnail({
  latitude,
  longitude,
  precision,
  label,
}: {
  latitude: number;
  longitude: number;
  precision: "district" | "city" | "region" | "country";
  label: string;
}) {
  const zoom = { district: 14, city: 11, region: 7, country: 3 }[precision];
  const { tileX, tileY, pixelXPct, pixelYPct } = lonLatToTilePixel(longitude, latitude, zoom);
  const tileUrl = `https://tile.openstreetmap.org/${zoom}/${tileX}/${tileY}.png`;

  return (
    <div className="flex shrink-0 flex-col items-center gap-1">
      <a
        href={`https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=15/${latitude}/${longitude}`}
        target="_blank"
        rel="noreferrer"
        onClick={stopRowToggle}
        className="relative block h-32 w-32 shrink-0 overflow-hidden rounded-lg border border-border bg-muted shadow-sm transition-all duration-200 hover:scale-[1.03] hover:shadow-md"
        title={label}
      >
        <img src={tileUrl} alt="" loading="lazy" className="h-full w-full object-cover" />
        <span
          className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full border-2 border-white bg-red-500 shadow"
          style={{ left: `${pixelXPct}%`, top: `${pixelYPct}%` }}
        />
      </a>
      <span className="text-[9px] text-muted-foreground/70">© OpenStreetMap</span>
    </div>
  );
}

// A badge that's also a real <button> — clicking it toggles a plain-text
// explanation shown below the badge row (see `openSignal` in VisitCard).
// Not a hover-only title tooltip: those don't work on touch devices and are
// easy to miss, so the explanation has to be an explicit tap/click action.
function SignalToggle({
  label,
  variant,
  active,
  onClick,
}: {
  label: string;
  variant: "destructive" | "outline" | "secondary";
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button type="button" onClick={onClick} className="appearance-none border-0 bg-transparent p-0">
      <Badge variant={variant} className={cn("cursor-pointer select-none", active && "ring-2 ring-ring")}>
        {label}
      </Badge>
    </button>
  );
}

type SignalKey = "vpn" | "proxy" | "tor" | "hosting" | "bot";

function VisitCard({ visit }: { visit: Visit }) {
  const { t } = useTranslation();
  const [openSignal, setOpenSignal] = useState<SignalKey | null>(null);

  const flag = countryFlag(visit.country_code);
  const locationLine = [visit.district, visit.city, visit.region, visit.country].filter(Boolean).join(", ");
  const hasCoords = visit.latitude != null && visit.longitude != null;
  const DeviceIcon = deviceIcon(visit.device_type);
  const precision: "district" | "city" | "region" | "country" = visit.district
    ? "district"
    : visit.city
      ? "city"
      : visit.region
        ? "region"
        : "country";

  const signals: { key: SignalKey; label: string; variant: "destructive" | "outline" | "secondary"; explanation: string }[] = [
    {
      key: "vpn",
      label: "VPN",
      variant: triStateBadgeVariant(visit.is_vpn),
      explanation: t(`links.signalTooltip.vpn.${visit.is_vpn}`),
    },
    {
      key: "proxy",
      label: t("links.proxy"),
      variant: triStateBadgeVariant(visit.is_proxy),
      explanation: t(`links.signalTooltip.proxy.${visit.is_proxy}`),
    },
    {
      key: "tor",
      label: "Tor",
      variant: triStateBadgeVariant(visit.is_tor),
      explanation: t(`links.signalTooltip.tor.${visit.is_tor}`),
    },
    {
      key: "hosting",
      label: t("links.hosting"),
      variant: triStateBadgeVariant(visit.is_hosting),
      explanation: t(`links.signalTooltip.hosting.${visit.is_hosting}`),
    },
    {
      key: "bot",
      label: t(`links.botConfidence.${visit.bot_confidence}`, visit.bot_confidence),
      variant: botConfidenceBadgeVariant(visit.bot_confidence),
      explanation: t(`links.botConfidenceTooltip.${visit.bot_confidence}`, ""),
    },
  ];
  const openExplanation = signals.find((s) => s.key === openSignal)?.explanation;

  return (
    <div className="group rounded-xl border border-border bg-card p-4 transition-all duration-200 hover:border-primary/25 hover:shadow-md">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-sm font-medium">
          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
          {formatDateTime(visit.created_at)}
        </div>
        {visit.visit_number != null &&
          (visit.is_returning_visitor ? (
            <Badge
              variant="secondary"
              title={t("links.returningVisitorTooltip", { count: visit.visit_number })}
              className="gap-1"
            >
              <History className="h-3 w-3" />
              {t("links.returningVisitor", { count: visit.visit_number })}
            </Badge>
          ) : (
            <Badge variant="outline" title={t("links.firstVisitTooltip")} className="gap-1">
              <Sparkles className="h-3 w-3" />
              {t("links.firstVisit")}
            </Badge>
          ))}
      </div>

      {visit.consent_given ? (
        <div className="mt-3 flex flex-col gap-3 sm:flex-row">
          <div className="min-w-0 flex-1 space-y-3">
            {/* IP + ISP + ASN, grouped as one "network" pill instead of three separate rows. */}
            <div className="flex items-center gap-2.5 rounded-lg bg-muted/50 px-3 py-2 transition-colors duration-200 group-hover:bg-muted">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Fingerprint className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-mono text-sm font-medium leading-tight">
                  {visit.ip_address || t("links.unknownValue")}
                </p>
                {(visit.isp || visit.organization) && (
                  <p className="truncate text-xs text-muted-foreground">
                    {visit.isp || visit.organization}
                    {visit.asn && <span className="text-muted-foreground/70"> · {visit.asn}</span>}
                    {visit.is_mobile && (
                      <span className="ml-1.5 inline-flex items-center gap-0.5 align-middle text-muted-foreground/80">
                        <Smartphone className="h-3 w-3" />
                        {t("links.mobileCarrier")}
                      </span>
                    )}
                  </p>
                )}
                {visit.hostname && (
                  <p className="truncate font-mono text-[11px] text-muted-foreground/70">{visit.hostname}</p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-1.5 text-sm">
              <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <div className="truncate">
                  {flag && <span className="mr-1">{flag}</span>}
                  {locationLine || t("links.unknownLocation")}
                </div>
                <div className="text-xs text-muted-foreground">
                  {visit.timezone && <span>{visit.timezone} · </span>}
                  {t("links.approximateLocationNote")}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2.5 rounded-lg bg-muted/50 px-3 py-2 transition-colors duration-200 group-hover:bg-muted">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                <DeviceIcon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium leading-tight">
                  {[visit.browser, visit.browser_version].filter(Boolean).join(" ") || t("links.unknownValue")}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {[visit.os, visit.os_version].filter(Boolean).join(" ")}
                  {visit.device_type ? ` · ${t(`links.deviceType.${visit.device_type}`, visit.device_type)}` : ""}
                  {visit.language ? ` · ${visit.language}` : ""}
                </p>
              </div>
            </div>

            <div className="space-y-1">
              <p className="text-[11px] text-muted-foreground">{t("links.signalsLabel")}</p>
              <div className="flex flex-wrap gap-1">
                {signals.map((s) => (
                  <SignalToggle
                    key={s.key}
                    label={s.label}
                    variant={s.variant}
                    active={openSignal === s.key}
                    onClick={() => setOpenSignal((prev) => (prev === s.key ? null : s.key))}
                  />
                ))}
              </div>
              {openExplanation && (
                <p className="rounded-md bg-muted px-2 py-1 text-xs text-foreground">{openExplanation}</p>
              )}
            </div>

            {(visit.referrer || (visit.utm_snapshot && Object.keys(visit.utm_snapshot).length > 0)) && (
              <div className="space-y-1 border-t border-border/60 pt-2 text-xs text-muted-foreground">
                {visit.referrer && (
                  <div className="flex items-center gap-1.5">
                    <ExternalLink className="h-3 w-3 shrink-0" />
                    <span className="truncate">{visit.referrer}</span>
                  </div>
                )}
                {visit.utm_snapshot && Object.keys(visit.utm_snapshot).length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(visit.utm_snapshot).map(([key, value]) => (
                      <Badge key={key} variant="secondary" className="font-normal">
                        {key.replace("utm_", "")}: {value}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {hasCoords && (
            <LocationThumbnail
              latitude={visit.latitude as number}
              longitude={visit.longitude as number}
              precision={precision}
              label={locationLine || t("links.unknownLocation")}
            />
          )}
        </div>
      ) : (
        <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
          <Server className="h-3.5 w-3.5" />
          {t("links.consentNotGiven")}
        </p>
      )}
    </div>
  );
}

function LinkVisitorsPanel({ linkId }: { linkId: string }) {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, refetch } = useLinkVisits(linkId, page, VISITS_PAGE_SIZE);

  if (isLoading) return <LoadingState label={t("links.loadingVisitors")} />;
  if (isError) return <ErrorState onRetry={() => refetch()} />;
  if (!data || data.items.length === 0) {
    return <EmptyState title={t("links.noVisitsYet")} />;
  }

  return (
    <div className="flex flex-col gap-2 py-2" onClick={stopRowToggle}>
      <p className="px-0.5 text-xs font-medium text-muted-foreground">
        {t("links.visitorListTitle", { count: data.total })}
      </p>
      <div className="flex flex-col gap-2">
        {data.items.map((visit) => (
          <VisitCard key={visit.id} visit={visit} />
        ))}
      </div>
      <Pagination page={page} pageSize={VISITS_PAGE_SIZE} total={data.total} onPageChange={setPage} />
    </div>
  );
}

function LinkRow({ link }: { link: Link }) {
  const { t } = useTranslation();
  const { toast } = useToast();
  const updateLink = useUpdateLink(link.id);
  const deleteLink = useDeleteLink();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const canExpand = link.unique_visitors > 0;

  return (
    <>
      <TableRow
        className={canExpand ? "cursor-pointer" : undefined}
        onClick={() => canExpand && setExpanded((v) => !v)}
        aria-expanded={canExpand ? expanded : undefined}
      >
        <TableCell>
          <div className="flex items-start gap-1">
            <span
              className="mt-0.5 text-muted-foreground"
              aria-label={expanded ? t("links.hideVisitors") : t("links.showVisitors")}
              title={canExpand ? t("links.showVisitorsHint") : t("links.noVisitsYetHint")}
            >
              {canExpand ? (
                expanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )
              ) : (
                <ChevronRight className="h-4 w-4 opacity-30" />
              )}
            </span>
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-1.5">
                <a
                  href={link.short_url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={stopRowToggle}
                  className="font-medium text-primary hover:underline"
                >
                  /{link.short_code}
                </a>
                <button
                  onClick={(e) => {
                    stopRowToggle(e);
                    navigator.clipboard.writeText(link.short_url);
                    toast({ title: t("common.copiedToClipboard") });
                  }}
                  className="text-muted-foreground hover:text-foreground"
                  aria-label={t("links.copyLink")}
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                {link.is_password_protected && <Lock className="h-3.5 w-3.5 text-muted-foreground" />}
                {link.requires_consent && <ShieldCheck className="h-3.5 w-3.5 text-muted-foreground" />}
              </div>
              <a
                href={link.target_url}
                target="_blank"
                rel="noreferrer"
                onClick={stopRowToggle}
                className="flex max-w-xs items-center gap-1 truncate text-xs text-muted-foreground hover:underline"
              >
                {link.target_url}
                <ExternalLink className="h-3 w-3 shrink-0" />
              </a>
              {link.campaign_name && (
                <RouterLink
                  to={`/projects/${link.campaign_id}`}
                  onClick={stopRowToggle}
                  className="inline-flex w-fit items-center gap-1 text-xs text-muted-foreground hover:text-foreground hover:underline"
                >
                  <FolderKanban className="h-3 w-3" />
                  {link.campaign_name}
                  {link.campaign_status && link.campaign_status !== "ACTIVE" && (
                    <Badge variant="secondary" className="px-1.5 py-0 text-[10px] font-normal">
                      {link.campaign_status === "PAUSED"
                        ? t("links.campaignPausedShort")
                        : t("links.campaignArchivedShort")}
                    </Badge>
                  )}
                </RouterLink>
              )}
            </div>
          </div>
        </TableCell>
        <TableCell>{formatNumber(link.total_visits)}</TableCell>
        <TableCell>{formatNumber(link.unique_visitors)}</TableCell>
        <TableCell>
          {link.expires_at ? (
            <Badge variant={new Date(link.expires_at) < new Date() ? "destructive" : "outline"}>
              {formatDate(link.expires_at)}
            </Badge>
          ) : (
            <span className="text-xs text-muted-foreground">{t("links.neverExpires")}</span>
          )}
        </TableCell>
        <TableCell onClick={stopRowToggle}>
          <Switch
            checked={link.is_active}
            onCheckedChange={(checked) => updateLink.mutate({ is_active: checked })}
            aria-label={t("links.activeColumn")}
          />
        </TableCell>
        <TableCell onClick={stopRowToggle}>
          <Button variant="ghost" size="icon" onClick={() => setConfirmDelete(true)} aria-label={t("common.delete")}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>

          <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t("links.deleteConfirmTitle")}</DialogTitle>
              </DialogHeader>
              <p className="text-sm text-muted-foreground">{t("links.deleteConfirmBody", { code: link.short_code })}</p>
              <DialogFooter>
                <Button variant="outline" onClick={() => setConfirmDelete(false)}>
                  {t("common.cancel")}
                </Button>
                <Button
                  variant="destructive"
                  disabled={deleteLink.isPending}
                  onClick={() => deleteLink.mutate(link.id, { onSuccess: () => setConfirmDelete(false) })}
                >
                  {t("common.delete")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TableCell>
      </TableRow>
      {expanded && (
        <TableRow className="hover:bg-transparent">
          <TableCell colSpan={6} className="bg-muted/30 px-6">
            <LinkVisitorsPanel linkId={link.id} />
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

export function LinkTable({ links }: { links: Link[] }) {
  const { t } = useTranslation();
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t("nav.links")}</TableHead>
          <TableHead>{t("links.visits")}</TableHead>
          <TableHead>{t("links.uniques")}</TableHead>
          <TableHead>{t("links.expires")}</TableHead>
          <TableHead>{t("links.activeColumn")}</TableHead>
          <TableHead className="w-10" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {links.map((link) => (
          <LinkRow key={link.id} link={link} />
        ))}
      </TableBody>
    </Table>
  );
}
