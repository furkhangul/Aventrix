import {
  Check,
  Copy,
  Pencil,
  Plus,
  RefreshCw,
  Play,
  Smartphone,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { isApiError } from "@/hooks/use-auth";
import { isDeviceOnline, useCreatePairingCode, useDevices, useRenameDevice, useRevokeDevice } from "@/hooks/use-devices";
import { useToast } from "@/hooks/use-toast";
import { cn, formatDateTime } from "@/lib/utils";
import type { Device, PairingCodeCreated } from "@/lib/types";

function secondsUntil(iso: string): number {
  return Math.max(0, Math.floor((new Date(iso).getTime() - Date.now()) / 1000));
}

/**
 * Pairing is a two-screen flow (code here, entry on the phone) and the web
 * side used to give no sign it had worked — the dialog just sat there until
 * the user guessed to close it. The device list is already polling, so the
 * dialog watches it and flips to a confirmation the moment a new device
 * shows up.
 */
function PairDeviceDialog({ deviceCount }: { deviceCount: number }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [pairing, setPairing] = useState<PairingCodeCreated | null>(null);
  const [remaining, setRemaining] = useState(0);
  const [paired, setPaired] = useState(false);
  const countAtOpenRef = useRef(deviceCount);
  const createPairingCode = useCreatePairingCode();
  const { toast } = useToast();

  useEffect(() => {
    if (!pairing) return;
    setRemaining(secondsUntil(pairing.expires_at));
    const interval = setInterval(() => setRemaining(secondsUntil(pairing.expires_at)), 1000);
    return () => clearInterval(interval);
  }, [pairing]);

  useEffect(() => {
    if (open && !paired && deviceCount > countAtOpenRef.current) setPaired(true);
  }, [deviceCount, open, paired]);

  const generate = () => {
    setPaired(false);
    createPairingCode.mutate(undefined, {
      onSuccess: (data) => setPairing(data),
      onError: () => toast({ title: t("devices.pairFailed"), variant: "destructive" }),
    });
  };

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      countAtOpenRef.current = deviceCount;
      setPaired(false);
      if (!pairing) generate();
    } else {
      setPairing(null);
      setPaired(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          {t("devices.pairNewDevice")}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t("devices.pairDialogTitle")}</DialogTitle>
        </DialogHeader>

        {paired ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <div className="rounded-full bg-success/15 p-3">
              <Check className="h-6 w-6 text-success" />
            </div>
            <p className="font-medium">{t("devices.pairedTitle")}</p>
            <p className="text-sm text-muted-foreground">{t("devices.pairedBody")}</p>
          </div>
        ) : createPairingCode.isPending || !pairing ? (
          <LoadingState />
        ) : remaining <= 0 ? (
          <div className="space-y-3 py-6 text-center">
            <p className="text-sm text-muted-foreground">{t("devices.codeExpired")}</p>
            <Button onClick={generate}>
              <RefreshCw className="h-4 w-4" />
              {t("devices.generateNewCode")}
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="rounded-xl border border-border bg-white p-3 shadow-sm">
              <img src={pairing.qr_code_data_url} alt={t("devices.pairDialogTitle")} className="h-44 w-44" />
            </div>

            <div className="flex items-center gap-2">
              <code className="rounded-lg bg-muted px-4 py-2 text-xl font-semibold tracking-[0.3em]">
                {pairing.code}
              </code>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={t("common.copy")}
                onClick={() => {
                  void navigator.clipboard.writeText(pairing.code);
                  toast({ title: t("common.copiedToClipboard") });
                }}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>

            <ol className="w-full space-y-1.5 rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground">
              <li>1. {t("devices.pairStepInstall")}</li>
              <li>2. {t("devices.pairStepServer")}</li>
              <li>3. {t("devices.pairStepCode")}</li>
            </ol>

            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/70" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
              </span>
              {t("devices.codeExpiresIn", { seconds: remaining })}
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            {paired ? t("common.done") : t("common.cancel")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function RenameDeviceDialog({
  device,
  open,
  onOpenChange,
}: {
  device: Device;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState(device.name);
  const renameDevice = useRenameDevice(device.id);

  useEffect(() => {
    if (open) setName(device.name);
  }, [open, device.name]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>{t("devices.renameTitle")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor={`device-name-${device.id}`}>{t("devices.nameLabel")}</Label>
          <Input
            id={`device-name-${device.id}`}
            value={name}
            maxLength={64}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t("common.cancel")}
          </Button>
          <Button
            disabled={renameDevice.isPending || !name.trim() || name.trim() === device.name}
            onClick={() =>
              renameDevice.mutate(name.trim(), { onSuccess: () => onOpenChange(false) })
            }
          >
            {t("common.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DeviceCard({ device }: { device: Device }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const revokeDevice = useRevokeDevice();
  const [confirmRevoke, setConfirmRevoke] = useState(false);
  const [renaming, setRenaming] = useState(false);

  const online = isDeviceOnline(device);

  return (
    <Card className="card-interactive group relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-brand-gradient opacity-0 transition-opacity duration-300 group-hover:opacity-[0.05]"
      />
      <CardContent className="relative space-y-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className={cn(
                "relative flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
                device.is_active ? "bg-brand-gradient text-white" : "bg-muted text-muted-foreground",
              )}
            >
              <Smartphone className="h-5 w-5" />
              {online && (
                <span className="absolute -bottom-0.5 -right-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-card">
                  <span className="h-2.5 w-2.5 rounded-full bg-success" />
                </span>
              )}
            </span>
            <div className="min-w-0">
              <p className="truncate font-medium">{device.name}</p>
              <p className="truncate text-xs capitalize text-muted-foreground">{device.platform}</p>
            </div>
          </div>

          <Badge variant={!device.is_active ? "outline" : online ? "success" : "secondary"}>
            {!device.is_active ? t("devices.statusRevoked") : online ? t("devices.online") : t("devices.offline")}
          </Badge>
        </div>

        <dl className="space-y-1 text-xs text-muted-foreground">
          <div className="flex justify-between gap-3">
            <dt>{t("devices.columnLastSeen")}</dt>
            <dd className="truncate">
              {device.last_seen_at ? formatDateTime(device.last_seen_at) : t("devices.neverSeen")}
            </dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt>{t("devices.columnPaired")}</dt>
            <dd className="truncate">{formatDateTime(device.paired_at)}</dd>
          </div>
        </dl>

        <div className="flex items-center gap-2">
          <Button
            className="flex-1"
            size="sm"
            disabled={!device.is_active}
            onClick={() => navigate(`/devices/${device.id}/control`)}
          >
            <Play className="h-4 w-4" />
            {t("devices.connect")}
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            aria-label={t("devices.renameTitle")}
            disabled={!device.is_active}
            onClick={() => setRenaming(true)}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            aria-label={t("common.delete")}
            disabled={!device.is_active}
            onClick={() => setConfirmRevoke(true)}
          >
            <Trash2 className="h-3.5 w-3.5 text-destructive" />
          </Button>
        </div>

        {!online && device.is_active && (
          <p className="rounded-lg bg-muted/60 px-3 py-2 text-xs text-muted-foreground">{t("devices.offlineHint")}</p>
        )}
      </CardContent>

      <RenameDeviceDialog device={device} open={renaming} onOpenChange={setRenaming} />

      <Dialog open={confirmRevoke} onOpenChange={setConfirmRevoke}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("devices.revokeConfirmTitle")}</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">{t("devices.revokeConfirmBody")}</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmRevoke(false)}>
              {t("common.cancel")}
            </Button>
            <Button
              variant="destructive"
              disabled={revokeDevice.isPending}
              onClick={() => revokeDevice.mutate(device.id, { onSuccess: () => setConfirmRevoke(false) })}
            >
              {t("devices.revoke")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

export function DevicesPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, error, refetch } = useDevices();

  const notEnabled = isApiError(error) && error.status === 404;
  const devices = useMemo(() => data?.items ?? [], [data]);
  const onlineCount = devices.filter(isDeviceOnline).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("devices.title")}</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{t("devices.subtitle")}</p>
          {devices.length > 0 && (
            <p className="mt-2 text-xs text-muted-foreground">
              {t("devices.summary", { total: devices.length, online: onlineCount })}
            </p>
          )}
        </div>
        {!notEnabled && <PairDeviceDialog deviceCount={data?.total ?? 0} />}
      </div>

      {isLoading ? (
        <LoadingState />
      ) : notEnabled ? (
        <EmptyState
          icon={Smartphone}
          title={t("devices.notEnabledTitle")}
          description={t("devices.notEnabledDescription")}
        />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : devices.length === 0 ? (
        <EmptyState icon={Smartphone} title={t("devices.emptyTitle")} description={t("devices.emptyDescription")} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {devices.map((device) => (
            <DeviceCard key={device.id} device={device} />
          ))}
        </div>
      )}
    </div>
  );
}
