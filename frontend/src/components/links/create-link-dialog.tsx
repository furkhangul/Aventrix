import { zodResolver } from "@hookform/resolvers/zod";
import { Copy, Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { isApiError } from "@/hooks/use-auth";
import { useCampaigns } from "@/hooks/use-campaigns";
import { useCreateLink } from "@/hooks/use-links";
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
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type Form = {
  target_url: string;
  campaign_id?: string;
  custom_alias?: string;
  description?: string;
  password?: string;
  requires_consent: boolean;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
};

const TR_CHAR_MAP: Record<string, string> = {
  ç: "c", Ç: "c", ğ: "g", Ğ: "g", ı: "i", İ: "i", ö: "o", Ö: "o", ş: "s", Ş: "s", ü: "u", Ü: "u",
};

// Turns a campaign name into a URL/UTM-friendly slug, e.g. "Yaz İndirimi 2026" -> "yaz-indirimi-2026".
function slugify(input: string): string {
  const withoutTurkishChars = input.replace(/[çÇğĞıİöÖşŞüÜ]/g, (ch) => TR_CHAR_MAP[ch] ?? ch);
  return withoutTurkishChars
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function CreateLinkDialog({ defaultCampaignId }: { defaultCampaignId?: string }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [createdUrl, setCreatedUrl] = useState<string | null>(null);
  const createLink = useCreateLink();
  const { data: campaignsData } = useCampaigns({ pageSize: 100 });
  const { toast } = useToast();

  const schema = z.object({
    target_url: z.string().url(t("createLink.urlInvalid")),
    campaign_id: z.string().optional(),
    custom_alias: z
      .string()
      .regex(/^[a-zA-Z0-9_-]{3,64}$/, t("createLink.aliasFormatError"))
      .optional()
      .or(z.literal("")),
    description: z.string().max(2000).optional(),
    password: z.string().min(4).optional().or(z.literal("")),
    requires_consent: z.boolean(),
    utm_source: z.string().optional(),
    utm_medium: z.string().optional(),
    utm_campaign: z.string().optional(),
    utm_term: z.string().optional(),
    utm_content: z.string().optional(),
  });

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { requires_consent: true, campaign_id: defaultCampaignId },
  });

  const requiresConsent = watch("requires_consent");
  const campaignId = watch("campaign_id");
  // Archived campaigns are done — you can't add new links to them. Paused
  // ones can still receive new links (they just won't redirect until the
  // campaign is resumed), so they stay selectable with a visible warning.
  const selectableCampaigns = campaignsData?.items.filter((c) => c.status !== "ARCHIVED") ?? [];

  // Selecting a campaign suggests a matching utm_campaign value, so the two
  // "campaign" concepts in this form (the real link and the UTM tag) don't
  // drift apart. Only overwrites what it auto-filled itself — a value the
  // user typed by hand is left alone.
  const lastAutoUtmCampaign = useRef("");
  useEffect(() => {
    const campaign = selectableCampaigns.find((c) => c.id === campaignId);
    const current = getValues("utm_campaign") ?? "";
    if (current !== "" && current !== lastAutoUtmCampaign.current) return;
    const suggested = campaign ? slugify(campaign.name) : "";
    setValue("utm_campaign", suggested);
    lastAutoUtmCampaign.current = suggested;
    // campaignsData is included so this re-runs once the list finishes
    // loading — otherwise a pre-selected defaultCampaignId (e.g. "add link"
    // from a campaign's own page) could resolve to no match on first run.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId, campaignsData]);

  const onSubmit = (data: Form) => {
    createLink.mutate(
      {
        target_url: data.target_url,
        campaign_id: data.campaign_id || undefined,
        custom_alias: data.custom_alias || undefined,
        description: data.description || undefined,
        password: data.password || undefined,
        requires_consent: data.requires_consent,
        utm: {
          utm_source: data.utm_source || undefined,
          utm_medium: data.utm_medium || undefined,
          utm_campaign: data.utm_campaign || undefined,
          utm_term: data.utm_term || undefined,
          utm_content: data.utm_content || undefined,
        },
      },
      {
        onSuccess: (link) => {
          toast({ title: t("createLink.linkCreated"), variant: "success" });
          setCreatedUrl(link.short_url);
          reset({ requires_consent: true, campaign_id: defaultCampaignId });
        },
        onError: (error) => {
          toast({
            title: t("createLink.createFailed"),
            description: isApiError(error) ? error.message : undefined,
            variant: "destructive",
          });
        },
      },
    );
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setCreatedUrl(null);
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          {t("createLink.newLink")}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("createLink.dialogTitle")}</DialogTitle>
        </DialogHeader>

        {createdUrl ? (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">{t("createLink.linkReady")}</p>
            <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-2.5">
              <code className="flex-1 truncate text-sm">{createdUrl}</code>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => {
                  navigator.clipboard.writeText(createdUrl);
                  toast({ title: t("common.copiedToClipboard") });
                }}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreatedUrl(null)}>
                {t("createLink.createAnother")}
              </Button>
              <Button onClick={() => setOpen(false)}>{t("common.done")}</Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Tabs defaultValue="basics">
              <TabsList>
                <TabsTrigger value="basics">{t("createLink.tabBasics")}</TabsTrigger>
                <TabsTrigger value="options">{t("createLink.tabOptions")}</TabsTrigger>
                <TabsTrigger value="utm">{t("createLink.tabUtm")}</TabsTrigger>
              </TabsList>

              <TabsContent value="basics" className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="target_url">{t("createLink.destinationUrl")}</Label>
                  <Input id="target_url" placeholder="https://example.com/landing" {...register("target_url")} />
                  <p className="text-xs text-muted-foreground">{t("createLink.destinationUrlHint")}</p>
                  {errors.target_url && <p className="text-xs text-destructive">{errors.target_url.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="campaign_id">{t("createLink.campaignOptional")}</Label>
                  <Select
                    value={watch("campaign_id") || "none"}
                    onValueChange={(v) => setValue("campaign_id", v === "none" ? undefined : v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t("createLink.noCampaign")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">{t("createLink.noCampaign")}</SelectItem>
                      {selectableCampaigns.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.name}
                          {c.status === "PAUSED" ? ` ${t("createLink.campaignPausedSuffix")}` : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">{t("createLink.campaignHint")}</p>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="custom_alias">{t("createLink.customAliasOptional")}</Label>
                  <Input id="custom_alias" placeholder="yaz-indirimi" {...register("custom_alias")} />
                  <p className="text-xs text-muted-foreground">{t("createLink.customAliasHint")}</p>
                  {errors.custom_alias && <p className="text-xs text-destructive">{errors.custom_alias.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="description">{t("createLink.descriptionOptional")}</Label>
                  <Input id="description" {...register("description")} />
                  <p className="text-xs text-muted-foreground">{t("createLink.descriptionHint")}</p>
                </div>
              </TabsContent>

              <TabsContent value="options" className="space-y-4">
                <div className="flex items-center justify-between rounded-md border border-border p-3">
                  <div>
                    <p className="text-sm font-medium">{t("createLink.requireConsent")}</p>
                    <p className="text-xs text-muted-foreground">{t("createLink.requireConsentHint")}</p>
                  </div>
                  <Switch checked={requiresConsent} onCheckedChange={(v) => setValue("requires_consent", v)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="password">{t("createLink.passwordOptional")}</Label>
                  <Input id="password" type="text" placeholder={t("createLink.passwordPlaceholder")} {...register("password")} />
                  <p className="text-xs text-muted-foreground">{t("createLink.passwordHint")}</p>
                  {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
                </div>
              </TabsContent>

              <TabsContent value="utm" className="space-y-4">
                <p className="text-xs text-muted-foreground">{t("createLink.utmIntro")}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="utm_source">{t("createLink.utmSource")}</Label>
                    <Input id="utm_source" placeholder="instagram" {...register("utm_source")} />
                    <p className="text-xs text-muted-foreground">{t("createLink.utmSourceHint")}</p>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="utm_medium">{t("createLink.utmMedium")}</Label>
                    <Input id="utm_medium" placeholder="sosyal-medya" {...register("utm_medium")} />
                    <p className="text-xs text-muted-foreground">{t("createLink.utmMediumHint")}</p>
                  </div>
                  <div className="col-span-2 space-y-1.5">
                    <Label htmlFor="utm_campaign">{t("createLink.utmCampaign")}</Label>
                    <Input id="utm_campaign" placeholder="yaz-indirimi-2026" {...register("utm_campaign")} />
                    <p className="text-xs text-muted-foreground">{t("createLink.utmCampaignHint")}</p>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="utm_term">{t("createLink.utmTerm")}</Label>
                    <Input id="utm_term" {...register("utm_term")} />
                    <p className="text-xs text-muted-foreground">{t("createLink.utmTermHint")}</p>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="utm_content">{t("createLink.utmContent")}</Label>
                    <Input id="utm_content" placeholder="mavi-buton" {...register("utm_content")} />
                    <p className="text-xs text-muted-foreground">{t("createLink.utmContentHint")}</p>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter>
              <Button type="submit" disabled={createLink.isPending}>
                {createLink.isPending ? t("common.creating") : t("createLink.createLink")}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
