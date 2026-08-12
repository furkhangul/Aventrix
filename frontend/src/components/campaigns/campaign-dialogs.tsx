import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle, Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { isApiError } from "@/hooks/use-auth";
import { useCreateCampaign, useUpdateCampaign } from "@/hooks/use-campaigns";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Campaign, CampaignStatus } from "@/lib/types";

type Form = { name: string; description?: string; tags?: string; status: CampaignStatus };

const schema = z.object({
  name: z.string().min(1).max(150),
  description: z.string().max(2000).optional(),
  tags: z.string().optional(),
  status: z.enum(["ACTIVE", "PAUSED", "ARCHIVED"]),
});

function tagsToInput(tags: string[] | null | undefined): string {
  return tags?.join(", ") ?? "";
}

function tagsFromInput(value: string | undefined): string[] | undefined {
  if (!value) return undefined;
  const parsed = value
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
  return parsed.length > 0 ? parsed : undefined;
}

export function CreateCampaignDialog() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const createCampaign = useCreateCampaign();
  const { toast } = useToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema), defaultValues: { status: "ACTIVE" } });

  const onSubmit = (data: Form) => {
    createCampaign.mutate(
      { name: data.name, description: data.description || undefined, tags: tagsFromInput(data.tags) },
      {
        onSuccess: () => {
          toast({ title: t("campaigns.campaignCreated"), variant: "success" });
          reset();
          setOpen(false);
        },
        onError: (error) => {
          toast({
            title: t("campaigns.createFailed"),
            description: isApiError(error) ? error.message : undefined,
            variant: "destructive",
          });
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          {t("campaigns.newCampaign")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("campaigns.dialogTitle")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="name">{t("campaigns.name")}</Label>
            <Input id="name" placeholder={t("campaigns.namePlaceholder")} {...register("name")} />
            <p className="text-xs text-muted-foreground">{t("campaigns.nameHint")}</p>
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="description">{t("campaigns.description")}</Label>
            <Input id="description" placeholder={t("campaigns.descriptionPlaceholder")} {...register("description")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tags">{t("campaigns.tags")}</Label>
            <Input id="tags" placeholder={t("campaigns.tagsPlaceholder")} {...register("tags")} />
            <p className="text-xs text-muted-foreground">{t("campaigns.tagsHint")}</p>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createCampaign.isPending}>
              {createCampaign.isPending ? t("common.creating") : t("campaigns.createCampaign")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function EditCampaignDialog({ campaign }: { campaign: Campaign }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const updateCampaign = useUpdateCampaign(campaign.id);
  const { toast } = useToast();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: campaign.name,
      description: campaign.description ?? "",
      tags: tagsToInput(campaign.tags),
      status: campaign.status,
    },
  });
  const watchedStatus = watch("status");

  const onSubmit = (data: Form) => {
    updateCampaign.mutate(
      {
        name: data.name,
        description: data.description || undefined,
        tags: tagsFromInput(data.tags) ?? [],
        status: data.status,
      },
      {
        onSuccess: () => {
          toast({ title: t("campaignDetail.campaignUpdated"), variant: "success" });
          setOpen(false);
        },
        onError: (error) =>
          toast({
            title: t("campaignDetail.updateFailed"),
            description: isApiError(error) ? error.message : undefined,
            variant: "destructive",
          }),
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Pencil className="h-3.5 w-3.5" /> {t("campaignDetail.edit")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("campaignDetail.editTitle")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="name">{t("campaignDetail.name")}</Label>
            <Input id="name" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="description">{t("campaignDetail.description")}</Label>
            <Input id="description" {...register("description")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tags">{t("campaigns.tags")}</Label>
            <Input id="tags" placeholder={t("campaigns.tagsPlaceholder")} {...register("tags")} />
          </div>
          <div className="space-y-1.5">
            <Label>{t("campaignDetail.status")}</Label>
            <Select value={watchedStatus} onValueChange={(v) => setValue("status", v as CampaignStatus)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVE">{t("campaignDetail.statusActive")}</SelectItem>
                <SelectItem value="PAUSED">{t("campaignDetail.statusPaused")}</SelectItem>
                <SelectItem value="ARCHIVED">{t("campaignDetail.statusArchived")}</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {watchedStatus === "ACTIVE" ? t("campaignDetail.statusActiveHint") : t("campaignDetail.statusHint")}
            </p>
            {watchedStatus !== "ACTIVE" && watchedStatus !== campaign.status && (
              <p className="flex items-start gap-1.5 rounded-md bg-warning/10 p-2 text-xs text-warning-foreground">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {watchedStatus === "PAUSED"
                  ? t("campaignDetail.pauseWarning", { count: campaign.link_count })
                  : t("campaignDetail.archiveWarning", { count: campaign.link_count })}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={updateCampaign.isPending}>
              {updateCampaign.isPending ? t("common.saving") : t("common.saveChanges")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
