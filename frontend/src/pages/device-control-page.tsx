import {
  ArrowLeft,
  Check,
  ChevronLeft,
  Circle,
  Gauge,
  Loader2,
  Maximize2,
  MonitorSmartphone,
  MousePointerClick,
  Play,
  RefreshCw,
  Square,
  TriangleAlert,
  Wifi,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useDevice, isDeviceOnline } from "@/hooks/use-devices";
import { useDeviceSession, type DeviceSessionPhase } from "@/hooks/use-device-session";
import { cn } from "@/lib/utils";
import type { DeviceNavKey } from "@/lib/types";

/** Phases that mean "a session exists and we are still trying to get pixels". */
const CONNECTING_PHASES: DeviceSessionPhase[] = ["starting", "waiting_for_device", "negotiating"];

function StatusPill({ phase }: { phase: DeviceSessionPhase }) {
  const { t } = useTranslation();
  const isLive = phase === "connected";
  const isBusy = CONNECTING_PHASES.includes(phase);

  return (
    <Badge variant={isLive ? "success" : phase === "error" ? "destructive" : isBusy ? "default" : "outline"}>
      <span className="relative flex h-2 w-2">
        {isLive && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success/70" />}
        <span
          className={cn(
            "relative inline-flex h-2 w-2 rounded-full",
            isLive ? "bg-success" : phase === "error" ? "bg-destructive" : isBusy ? "bg-primary" : "bg-muted-foreground",
          )}
        />
      </span>
      {t(`devices.connectionState.${phase}`)}
    </Badge>
  );
}

/**
 * Three-step progress through the handshake. Which step is stuck is the
 * single most useful thing to show while connecting: "the phone never
 * joined" and "the phone joined but no video arrived" need completely
 * different fixes from the person holding it.
 */
function ConnectionSteps({ phase }: { phase: DeviceSessionPhase }) {
  const { t } = useTranslation();
  const order: DeviceSessionPhase[] = ["starting", "waiting_for_device", "negotiating"];
  const currentIndex = phase === "connected" ? order.length : order.indexOf(phase);

  return (
    <ol className="w-full max-w-xs space-y-3">
      {order.map((step, index) => {
        const done = index < currentIndex;
        const active = index === currentIndex;
        return (
          <li key={step} className="flex items-start gap-3">
            <span
              className={cn(
                "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px]",
                done && "border-success/40 bg-success/15 text-success",
                active && "border-primary/40 bg-primary/15 text-primary",
                !done && !active && "border-border text-muted-foreground/60",
              )}
            >
              {done ? (
                <Check className="h-3 w-3" />
              ) : active ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Circle className="h-2 w-2" />
              )}
            </span>
            <div className="min-w-0">
              <p className={cn("text-sm", active ? "font-medium text-foreground" : "text-muted-foreground")}>
                {t(`devices.step.${step}.title`)}
              </p>
              {active && (
                <p className="mt-0.5 text-xs text-muted-foreground">{t(`devices.step.${step}.hint`)}</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function StatRow({ icon: Icon, label, value }: { icon: typeof Gauge; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <span className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </span>
      <span className="text-xs font-medium tabular-nums">{value}</span>
    </div>
  );
}

export function DeviceControlPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { deviceId } = useParams<{ deviceId: string }>();
  const { data: device } = useDevice(deviceId);
  const session = useDeviceSession(deviceId);

  const videoRef = useRef<HTMLVideoElement>(null);
  const frameRef = useRef<HTMLDivElement>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const { phase, stream, connect } = session;

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = stream;
  }, [stream]);

  // Auto-start on arrival: this route is only ever reached by pressing
  // Connect on the devices page, so making the user press it again would be a
  // pointless second click.
  //
  // Deliberately not guarded by a "has started" ref. StrictMode mounts every
  // component twice in dev, and the hook's cleanup tears the session down in
  // between — a ref guard makes the second mount skip the reconnect and
  // leaves the page permanently dead on a dev server. [connect] is stable, so
  // this still runs exactly once per real mount; the backend supersedes the
  // throwaway first session.
  useEffect(() => {
    if (deviceId) connect();
  }, [deviceId, connect]);

  useEffect(() => {
    if (phase !== "connected") {
      setElapsedSeconds(0);
      return;
    }
    const startedAt = Date.now();
    const interval = setInterval(() => setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1000);
    return () => clearInterval(interval);
  }, [phase]);

  const pointerToNormalized = (event: React.PointerEvent<HTMLVideoElement>) => {
    const video = event.currentTarget;
    const rect = video.getBoundingClientRect();
    // The video is letterboxed inside its box (object-contain), so the raw
    // element rect is not the picture. Mapping against the rect instead of
    // the displayed picture put every tap in the wrong place on any screen
    // whose aspect ratio did not match the element's.
    const videoAspect = (video.videoWidth || rect.width) / (video.videoHeight || rect.height);
    const boxAspect = rect.width / rect.height;
    const displayedWidth = videoAspect > boxAspect ? rect.width : rect.height * videoAspect;
    const displayedHeight = videoAspect > boxAspect ? rect.width / videoAspect : rect.height;
    const offsetX = (rect.width - displayedWidth) / 2;
    const offsetY = (rect.height - displayedHeight) / 2;

    return {
      x: Math.min(1, Math.max(0, (event.clientX - rect.left - offsetX) / displayedWidth)),
      y: Math.min(1, Math.max(0, (event.clientY - rect.top - offsetY) / displayedHeight)),
    };
  };

  const toggleFullscreen = useCallback(() => {
    const frame = frameRef.current;
    if (!frame) return;
    if (document.fullscreenElement) void document.exitFullscreen();
    else void frame.requestFullscreen().catch(() => undefined);
  }, []);

  const navKeys: { key: DeviceNavKey; icon: typeof Square; labelKey: string }[] = [
    { key: "BACK", icon: ChevronLeft, labelKey: "devices.navBack" },
    { key: "HOME", icon: Circle, labelKey: "devices.navHome" },
    { key: "RECENTS", icon: Square, labelKey: "devices.navRecents" },
  ];

  if (!deviceId) return null;

  const isConnecting = CONNECTING_PHASES.includes(phase);
  const deviceOnline = device ? isDeviceOnline(device) : false;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" aria-label={t("common.back")} onClick={() => navigate("/devices")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">{device?.name ?? t("devices.controlTitle")}</h1>
            <div className="mt-1 flex items-center gap-2">
              <StatusPill phase={phase} />
              {phase === "connected" && (
                <span className="text-xs tabular-nums text-muted-foreground">
                  {Math.floor(elapsedSeconds / 60)
                    .toString()
                    .padStart(2, "0")}
                  :{(elapsedSeconds % 60).toString().padStart(2, "0")}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {phase === "connected" && (
            <Button variant="outline" size="sm" onClick={toggleFullscreen}>
              <Maximize2 className="h-4 w-4" />
              {t("devices.fullscreen")}
            </Button>
          )}
          {(phase === "ended" || phase === "error") ? (
            <Button size="sm" onClick={connect}>
              <RefreshCw className="h-4 w-4" />
              {t("devices.reconnect")}
            </Button>
          ) : (
            <Button variant="destructive" size="sm" onClick={session.disconnect} disabled={phase === "idle"}>
              {t("devices.disconnect")}
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        {/* --- Screen ------------------------------------------------------ */}
        <div
          ref={frameRef}
          className="relative flex min-h-[26rem] items-center justify-center overflow-hidden rounded-xl border border-border/70 bg-[#0b0a12] p-6"
        >
          <div aria-hidden className="pointer-events-none absolute inset-0 aurora opacity-50" />

          {phase === "connected" ? (
            <div className="relative rounded-[2rem] border-[6px] border-black/80 bg-black shadow-lg ring-1 ring-white/10">
              <span
                aria-hidden
                className="absolute left-1/2 top-1.5 z-10 h-1.5 w-16 -translate-x-1/2 rounded-full bg-white/20"
              />
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className={cn(
                  "max-h-[68vh] w-auto max-w-full rounded-[1.6rem] bg-black",
                  session.canSendInput ? "cursor-crosshair touch-none" : "cursor-not-allowed",
                )}
                onPointerDown={(e) => {
                  e.currentTarget.setPointerCapture(e.pointerId);
                  session.sendInput({ type: "pointer", action: "down", ...pointerToNormalized(e) });
                }}
                onPointerMove={(e) => {
                  if (e.buttons > 0) session.sendInput({ type: "pointer", action: "move", ...pointerToNormalized(e) });
                }}
                onPointerUp={(e) => {
                  e.currentTarget.releasePointerCapture(e.pointerId);
                  session.sendInput({ type: "pointer", action: "up", ...pointerToNormalized(e) });
                }}
              />
            </div>
          ) : phase === "error" ? (
            <div className="relative flex max-w-sm flex-col items-center gap-4 text-center">
              <div className="rounded-full bg-destructive/15 p-3">
                <TriangleAlert className="h-6 w-6 text-destructive" />
              </div>
              <div>
                <p className="font-medium text-white">{t(`devices.error.${session.errorCode ?? "start_failed"}.title`)}</p>
                <p className="mt-1.5 text-sm text-white/60">
                  {t(`devices.error.${session.errorCode ?? "start_failed"}.body`)}
                </p>
              </div>
              <Button size="sm" onClick={connect}>
                <RefreshCw className="h-4 w-4" />
                {t("devices.tryAgain")}
              </Button>
            </div>
          ) : phase === "ended" ? (
            <div className="relative flex max-w-sm flex-col items-center gap-4 text-center">
              <div className="rounded-full bg-white/10 p-3">
                <MonitorSmartphone className="h-6 w-6 text-white/70" />
              </div>
              <div>
                <p className="font-medium text-white">{t("devices.sessionEndedTitle")}</p>
                <p className="mt-1.5 text-sm text-white/60">{t("devices.sessionEndedBody")}</p>
              </div>
              <Button size="sm" onClick={connect}>
                <Play className="h-4 w-4" />
                {t("devices.reconnect")}
              </Button>
            </div>
          ) : (
            <div className="relative flex flex-col items-center gap-6">
              <div className="relative flex h-16 w-16 items-center justify-center">
                <span className="absolute inset-0 animate-ping rounded-full bg-primary/20" />
                <span className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-gradient">
                  <MonitorSmartphone className="h-6 w-6 text-white" />
                </span>
              </div>
              <ConnectionSteps phase={phase} />
            </div>
          )}
        </div>

        {/* --- Side panel --------------------------------------------------- */}
        <div className="space-y-4">
          <Card>
            <CardContent className="p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {t("devices.connectionPanel")}
              </p>
              <div className="mt-3 divide-y divide-border/70">
                <StatRow
                  icon={Wifi}
                  label={t("devices.statDevice")}
                  value={deviceOnline ? t("devices.online") : t("devices.offline")}
                />
                <StatRow
                  icon={Gauge}
                  label={t("devices.statResolution")}
                  value={session.stats ? `${session.stats.width}×${session.stats.height}` : "—"}
                />
                <StatRow
                  icon={Gauge}
                  label={t("devices.statFps")}
                  value={session.stats ? `${session.stats.framesPerSecond}` : "—"}
                />
                <StatRow
                  icon={Gauge}
                  label={t("devices.statBitrate")}
                  value={session.stats ? `${session.stats.kilobitsPerSecond} kbps` : "—"}
                />
                <StatRow
                  icon={Gauge}
                  label={t("devices.statLatency")}
                  value={session.stats?.roundTripMs != null ? `${session.stats.roundTripMs} ms` : "—"}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {t("devices.navKeys")}
              </p>
              <div className="mt-3 grid grid-cols-3 gap-2">
                {navKeys.map((navKey) => (
                  <Button
                    key={navKey.key}
                    variant="outline"
                    size="sm"
                    disabled={!session.canSendInput}
                    onClick={() => session.sendNavKey(navKey.key)}
                    className="flex-col gap-1 py-3 h-auto"
                  >
                    <navKey.icon className="h-4 w-4" />
                    <span className="text-[10px]">{t(navKey.labelKey)}</span>
                  </Button>
                ))}
              </div>
              <p className="mt-3 flex items-start gap-2 text-xs text-muted-foreground">
                <MousePointerClick className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {session.canSendInput ? t("devices.controlHint") : t("devices.inputUnavailable")}
              </p>
            </CardContent>
          </Card>

          {isConnecting && (
            <Card className="border-primary/25 bg-primary/5">
              <CardContent className="p-5">
                <p className="text-xs font-medium uppercase tracking-wide text-primary">{t("devices.onThePhone")}</p>
                <ol className="mt-2 space-y-1.5 text-xs text-muted-foreground">
                  <li>1. {t("devices.phoneStepOpen")}</li>
                  <li>2. {t("devices.phoneStepToggle")}</li>
                  <li>3. {t("devices.phoneStepAccept")}</li>
                </ol>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
