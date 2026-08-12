import { Copy, Plus, Radio, Smartphone, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { isApiError } from "@/hooks/use-auth";
import { useCreatePairingCode, useDevices, useRevokeDevice } from "@/hooks/use-devices";
import { useToast } from "@/hooks/use-toast";
import { formatDateTime } from "@/lib/utils";
import type { Device, PairingCodeCreated } from "@/lib/types";

function secondsUntil(iso: string): number {
  return Math.max(0, Math.floor((new Date(iso).getTime() - Date.now()) / 1000));
}

function PairDeviceDialog() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [pairing, setPairing] = useState<PairingCodeCreated | null>(null);
  const [remaining, setRemaining] = useState(0);
  const createPairingCode = useCreatePairingCode();
  const { toast } = useToast();

  useEffect(() => {
    if (!pairing) return;
    setRemaining(secondsUntil(pairing.expires_at));
    const interval = setInterval(() => setRemaining(secondsUntil(pairing.expires_at)), 1000);
    return () => clearInterval(interval);
  }, [pairing]);

  const generate = () => {
    createPairingCode.mutate(undefined, {
      onSuccess: (data) => setPairing(data),
      onError: () =>
        toast({ title: t("devices.pairFailed"), variant: "destructive" }),
    });
  };

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next && !pairing) generate();
    if (!next) setPairing(null);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          {t("devices.pairNewDevice")}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>{t("devices.pairDialogTitle")}</DialogTitle>
        </DialogHeader>
        {createPairingCode.isPending || !pairing ? (
          <LoadingState />
        ) : remaining <= 0 ? (
          <div className="space-y-3 text-center">
            <p className="text-sm text-muted-foreground">{t("devices.codeExpired")}</p>
            <Button onClick={generate}>{t("devices.generateNewCode")}</Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <img
              src={pairing.qr_code_data_url}
              alt={t("devices.pairDialogTitle")}
              className="h-48 w-48 rounded-md border border-border"
            />
            <div className="flex items-center gap-2">
              <code className="rounded-md bg-muted px-3 py-1.5 text-lg font-semibold tracking-widest">
                {pairing.code}
              </code>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => {
                  navigator.clipboard.writeText(pairing.code);
                  toast({ title: t("common.copiedToClipboard") });
                }}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-center text-xs text-muted-foreground">
              {t("devices.pairInstructions")}
            </p>
            <p className="text-xs text-muted-foreground">{t("devices.codeExpiresIn", { seconds: remaining })}</p>
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            {t("common.done")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DeviceRow({ device }: { device: Device }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const revokeDevice = useRevokeDevice();
  const [confirmRevoke, setConfirmRevoke] = useState(false);

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center gap-2">
          <Smartphone className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="font-medium">{device.name}</p>
            <p className="text-xs text-muted-foreground">{device.platform}</p>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant={device.is_active ? "success" : "outline"}>
          {device.is_active ? t("devices.statusActive") : t("devices.statusRevoked")}
        </Badge>
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {device.last_seen_at ? formatDateTime(device.last_seen_at) : t("devices.neverSeen")}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">{formatDateTime(device.paired_at)}</TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            aria-label={t("devices.connect")}
            disabled={!device.is_active}
            onClick={() => navigate(`/devices/${device.id}/control`)}
          >
            <Radio className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label={t("common.delete")}
            disabled={!device.is_active}
            onClick={() => setConfirmRevoke(true)}
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>

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
      </TableCell>
    </TableRow>
  );
}

export function DevicesPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, error, refetch } = useDevices();

  const notEnabled = isApiError(error) && error.status === 404;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("devices.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("devices.subtitle")}</p>
        </div>
        {!notEnabled && <PairDeviceDialog />}
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
      ) : !data || data.items.length === 0 ? (
        <EmptyState icon={Smartphone} title={t("devices.emptyTitle")} description={t("devices.emptyDescription")} />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("devices.columnDevice")}</TableHead>
              <TableHead>{t("devices.columnStatus")}</TableHead>
              <TableHead>{t("devices.columnLastSeen")}</TableHead>
              <TableHead>{t("devices.columnPaired")}</TableHead>
              <TableHead className="w-24" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.map((device) => (
              <DeviceRow key={device.id} device={device} />
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
