import { zodResolver } from "@hookform/resolvers/zod";
import { Copy, ListChecks, Plus, Send, Trash2, Webhook as WebhookIcon } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { isApiError } from "@/hooks/use-auth";
import {
  useCreateWebhook,
  useDeleteWebhook,
  useTestWebhook,
  useUpdateWebhook,
  useWebhookDeliveries,
  useWebhooks,
} from "@/hooks/use-webhooks";
import { useToast } from "@/hooks/use-toast";
import { formatDateTime } from "@/lib/utils";
import type { Webhook, WebhookEventType } from "@/lib/types";

const EVENT_OPTIONS: { value: WebhookEventType; key: string }[] = [
  { value: "link.created", key: "webhooks.eventLinkCreated" },
  { value: "link.clicked", key: "webhooks.eventLinkClicked" },
  { value: "campaign.created", key: "webhooks.eventCampaignCreated" },
  { value: "campaign.completed", key: "webhooks.eventCampaignCompleted" },
  { value: "security.alert", key: "webhooks.eventSecurityAlert" },
];

type Form = { url: string; description?: string; events: string[] };

function CreateWebhookDialog({ onCreated }: { onCreated: (secret: string) => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const createWebhook = useCreateWebhook();
  const { toast } = useToast();
  const schema = z.object({
    url: z.string().url(t("createLink.urlInvalid")),
    description: z.string().max(500).optional(),
    events: z.array(z.string()).min(1, t("webhooks.eventsRequired")),
  });
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema), defaultValues: { events: [] } });

  const selectedEvents = watch("events");

  const toggleEvent = (event: string) => {
    const next = selectedEvents.includes(event) ? selectedEvents.filter((e) => e !== event) : [...selectedEvents, event];
    setValue("events", next, { shouldValidate: true });
  };

  const onSubmit = (data: Form) => {
    createWebhook.mutate(
      { url: data.url, description: data.description || undefined, events: data.events as WebhookEventType[] },
      {
        onSuccess: (webhook) => {
          setOpen(false);
          reset({ events: [] });
          onCreated(webhook.secret);
        },
        onError: (error) => {
          toast({ title: t("webhooks.createFailed"), description: isApiError(error) ? error.message : undefined, variant: "destructive" });
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          {t("webhooks.newWebhook")}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("webhooks.createDialogTitle")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="webhook-url">{t("webhooks.endpointUrl")}</Label>
            <Input id="webhook-url" placeholder="https://example.com/hooks/inbound" {...register("url")} />
            {errors.url && <p className="text-xs text-destructive">{errors.url.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="webhook-description">{t("webhooks.descriptionOptional")}</Label>
            <Input id="webhook-description" {...register("description")} />
          </div>
          <div className="space-y-1.5">
            <Label>{t("webhooks.events")}</Label>
            <div className="flex flex-wrap gap-2">
              {EVENT_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => toggleEvent(option.value)}
                  className="focus-visible:outline-none"
                >
                  <Badge variant={selectedEvents.includes(option.value) ? "default" : "outline"} className="cursor-pointer">
                    {t(option.key)}
                  </Badge>
                </button>
              ))}
            </div>
            {errors.events && <p className="text-xs text-destructive">{errors.events.message as string}</p>}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createWebhook.isPending}>
              {createWebhook.isPending ? t("common.creating") : t("webhooks.createWebhook")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function RevealSecretDialog({ secret, onClose }: { secret: string | null; onClose: () => void }) {
  const { t } = useTranslation();
  const { toast } = useToast();
  return (
    <Dialog open={!!secret} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("webhooks.secretRevealTitle")}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">{t("webhooks.secretRevealBody")}</p>
        <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-2.5">
          <code className="flex-1 truncate text-sm">{secret}</code>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => {
              if (secret) navigator.clipboard.writeText(secret);
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

function DeliveriesDialog({ webhook, onClose }: { webhook: Webhook | null; onClose: () => void }) {
  const { t } = useTranslation();
  const { data, isLoading } = useWebhookDeliveries(webhook?.id);

  return (
    <Dialog open={!!webhook} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t("webhooks.deliveriesTitle", { url: webhook?.url })}</DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <LoadingState />
        ) : !data || data.items.length === 0 ? (
          <EmptyState icon={ListChecks} title={t("webhooks.noDeliveries")} description={t("webhooks.noDeliveriesDescription")} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("webhooks.columnEvent")}</TableHead>
                <TableHead>{t("webhooks.columnStatus")}</TableHead>
                <TableHead>{t("webhooks.columnResponse")}</TableHead>
                <TableHead>{t("webhooks.columnAttempts")}</TableHead>
                <TableHead>{t("webhooks.columnWhen")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((delivery) => (
                <TableRow key={delivery.id}>
                  <TableCell className="text-xs">{delivery.event_type}</TableCell>
                  <TableCell>
                    <Badge variant={delivery.status === "SUCCESS" ? "success" : delivery.status === "FAILED" ? "destructive" : "outline"}>
                      {delivery.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">{delivery.response_status_code ?? "—"}</TableCell>
                  <TableCell className="text-xs">{delivery.attempt_count}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDateTime(delivery.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </DialogContent>
    </Dialog>
  );
}

function WebhookRow({
  webhook,
  onViewDeliveries,
}: {
  webhook: Webhook;
  onViewDeliveries: (webhook: Webhook) => void;
}) {
  const { t } = useTranslation();
  const updateWebhook = useUpdateWebhook(webhook.id);
  const deleteWebhook = useDeleteWebhook();
  const testWebhook = useTestWebhook();
  const { toast } = useToast();
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <TableRow>
      <TableCell>
        <p className="max-w-xs truncate font-medium">{webhook.url}</p>
        {webhook.description && <p className="text-xs text-muted-foreground">{webhook.description}</p>}
        <code className="text-xs text-muted-foreground">{webhook.secret_preview}</code>
      </TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-1">
          {webhook.events.map((event) => (
            <Badge key={event} variant="outline" className="text-[10px]">
              {event}
            </Badge>
          ))}
        </div>
      </TableCell>
      <TableCell>
        <Switch checked={webhook.is_active} onCheckedChange={(checked) => updateWebhook.mutate({ is_active: checked })} aria-label={t("webhooks.columnActive")} />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            aria-label={t("webhooks.newWebhook")}
            disabled={testWebhook.isPending}
            onClick={() =>
              testWebhook.mutate(webhook.id, {
                onSuccess: (delivery) =>
                  toast({
                    title: delivery.status === "SUCCESS" ? t("webhooks.testDelivered") : t("webhooks.testPending"),
                  }),
              })
            }
          >
            <Send className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" aria-label={t("webhooks.deliveriesTitle", { url: "" })} onClick={() => onViewDeliveries(webhook)}>
            <ListChecks className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" aria-label={t("common.delete")} onClick={() => setConfirmDelete(true)}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>

        <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("webhooks.deleteConfirmTitle")}</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-muted-foreground">{t("webhooks.deleteConfirmBody")}</p>
            <DialogFooter>
              <Button variant="outline" onClick={() => setConfirmDelete(false)}>
                {t("common.cancel")}
              </Button>
              <Button
                variant="destructive"
                disabled={deleteWebhook.isPending}
                onClick={() => deleteWebhook.mutate(webhook.id, { onSuccess: () => setConfirmDelete(false) })}
              >
                {t("common.delete")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </TableCell>
    </TableRow>
  );
}

export function WebhooksPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useWebhooks();
  const [revealedSecret, setRevealedSecret] = useState<string | null>(null);
  const [viewingDeliveries, setViewingDeliveries] = useState<Webhook | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t("webhooks.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("webhooks.subtitle")}</p>
        </div>
        <CreateWebhookDialog onCreated={setRevealedSecret} />
      </div>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState icon={WebhookIcon} title={t("webhooks.emptyTitle")} description={t("webhooks.emptyDescription")} />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("webhooks.columnEndpoint")}</TableHead>
              <TableHead>{t("webhooks.columnEvents")}</TableHead>
              <TableHead>{t("webhooks.columnActive")}</TableHead>
              <TableHead className="w-32" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.map((webhook) => (
              <WebhookRow key={webhook.id} webhook={webhook} onViewDeliveries={setViewingDeliveries} />
            ))}
          </TableBody>
        </Table>
      )}

      <RevealSecretDialog secret={revealedSecret} onClose={() => setRevealedSecret(null)} />
      <DeliveriesDialog webhook={viewingDeliveries} onClose={() => setViewingDeliveries(null)} />
    </div>
  );
}
