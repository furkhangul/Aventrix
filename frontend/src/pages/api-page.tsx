import { zodResolver } from "@hookform/resolvers/zod";
import { Copy, Key, Plus, RotateCw, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { isApiError } from "@/hooks/use-auth";
import { useApiKeys, useCreateApiKey, useRevokeApiKey, useRotateApiKey } from "@/hooks/use-api-keys";
import { useToast } from "@/hooks/use-toast";
import { formatDateTime } from "@/lib/utils";
import type { ApiKey, ApiKeyTier } from "@/lib/types";

const TIER_LIMIT_KEYS: Record<ApiKeyTier, string> = {
  FREE: "apiKeys.tierFree",
  PRO: "apiKeys.tierPro",
  BUSINESS: "apiKeys.tierBusiness",
};

type Form = { name: string; tier: ApiKeyTier };

function RevealKeyDialog({ apiKey, onClose }: { apiKey: string | null; onClose: () => void }) {
  const { t } = useTranslation();
  const { toast } = useToast();
  return (
    <Dialog open={!!apiKey} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("apiKeys.revealTitle")}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">{t("apiKeys.revealBody")}</p>
        <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-2.5">
          <code className="flex-1 truncate text-sm">{apiKey}</code>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => {
              if (apiKey) navigator.clipboard.writeText(apiKey);
              toast({ title: t("common.copiedToClipboard") });
            }}
          >
            <Copy className="h-4 w-4" />
          </Button>
        </div>
        <DialogFooter>
          <Button onClick={onClose}>{t("common.done")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function CreateApiKeyDialog({ onCreated }: { onCreated: (key: string) => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const createKey = useCreateApiKey();
  const { toast } = useToast();
  const schema = z.object({
    name: z.string().min(1, t("auth.validation.required")).max(150),
    tier: z.enum(["FREE", "PRO", "BUSINESS"]),
  });
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema), defaultValues: { tier: "FREE" } });

  const onSubmit = (data: Form) => {
    createKey.mutate(data, {
      onSuccess: (key) => {
        setOpen(false);
        reset({ tier: "FREE", name: "" });
        onCreated(key.api_key);
      },
      onError: (error) => {
        toast({ title: t("apiKeys.createFailed"), description: isApiError(error) ? error.message : undefined, variant: "destructive" });
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          {t("apiKeys.newKey")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("apiKeys.createDialogTitle")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="key-name">{t("apiKeys.name")}</Label>
            <Input id="key-name" placeholder={t("apiKeys.namePlaceholder")} {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>{t("apiKeys.tier")}</Label>
            <Select value={watch("tier")} onValueChange={(v) => setValue("tier", v as ApiKeyTier)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TIER_LIMIT_KEYS) as ApiKeyTier[]).map((tier) => (
                  <SelectItem key={tier} value={tier}>
                    {tier} — {t(TIER_LIMIT_KEYS[tier])}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createKey.isPending}>
              {createKey.isPending ? t("common.creating") : t("apiKeys.createKey")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ApiKeyRow({ apiKey, onRevealKey }: { apiKey: ApiKey; onRevealKey: (key: string) => void }) {
  const { t } = useTranslation();
  const rotate = useRotateApiKey();
  const revoke = useRevokeApiKey();
  const { toast } = useToast();
  const [confirmRevoke, setConfirmRevoke] = useState(false);

  return (
    <TableRow>
      <TableCell>
        <p className="font-medium">{apiKey.name}</p>
        <code className="text-xs text-muted-foreground">{apiKey.key_prefix}…</code>
      </TableCell>
      <TableCell>
        <Badge variant="outline">{apiKey.tier}</Badge>
      </TableCell>
      <TableCell>
        <Badge variant={apiKey.is_active ? "success" : "destructive"}>{apiKey.is_active ? t("apiKeys.active") : t("apiKeys.revoked")}</Badge>
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">{apiKey.last_used_at ? formatDateTime(apiKey.last_used_at) : t("apiKeys.neverUsed")}</TableCell>
      <TableCell className="text-xs text-muted-foreground">{formatDateTime(apiKey.created_at)}</TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            disabled={!apiKey.is_active || rotate.isPending}
            aria-label={t("common.retry")}
            onClick={() =>
              rotate.mutate(apiKey.id, {
                onSuccess: (key) => {
                  toast({ title: t("apiKeys.keyRotated") });
                  onRevealKey(key.api_key);
                },
              })
            }
          >
            <RotateCw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" disabled={!apiKey.is_active} aria-label={t("apiKeys.revoke")} onClick={() => setConfirmRevoke(true)}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>

        <Dialog open={confirmRevoke} onOpenChange={setConfirmRevoke}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("apiKeys.revokeConfirmTitle")}</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-muted-foreground">{t("apiKeys.revokeConfirmBody", { name: apiKey.name })}</p>
            <DialogFooter>
              <Button variant="outline" onClick={() => setConfirmRevoke(false)}>
                {t("common.cancel")}
              </Button>
              <Button
                variant="destructive"
                disabled={revoke.isPending}
                onClick={() => revoke.mutate(apiKey.id, { onSuccess: () => setConfirmRevoke(false) })}
              >
                {t("apiKeys.revoke")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </TableCell>
    </TableRow>
  );
}

export function ApiPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useApiKeys();
  const [revealedKey, setRevealedKey] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("apiKeys.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("apiKeys.subtitle")}</p>
        </div>
        <CreateApiKeyDialog onCreated={setRevealedKey} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("apiKeys.tierLimitsTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {(Object.keys(TIER_LIMIT_KEYS) as ApiKeyTier[]).map((tier) => (
            <div key={tier} className="rounded-md border border-border p-3 text-center">
              <p className="text-sm font-semibold">{tier}</p>
              <p className="text-xs text-muted-foreground">{t(TIER_LIMIT_KEYS[tier])}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState icon={Key} title={t("apiKeys.emptyTitle")} description={t("apiKeys.emptyDescription")} />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("apiKeys.columnKey")}</TableHead>
              <TableHead>{t("apiKeys.columnTier")}</TableHead>
              <TableHead>{t("apiKeys.columnStatus")}</TableHead>
              <TableHead>{t("apiKeys.columnLastUsed")}</TableHead>
              <TableHead>{t("apiKeys.columnCreated")}</TableHead>
              <TableHead className="w-20" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.map((key) => (
              <ApiKeyRow key={key.id} apiKey={key} onRevealKey={setRevealedKey} />
            ))}
          </TableBody>
        </Table>
      )}

      <RevealKeyDialog apiKey={revealedKey} onClose={() => setRevealedKey(null)} />
    </div>
  );
}
