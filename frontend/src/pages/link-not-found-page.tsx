import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { Logo } from "@/components/logo";

const REASON_KEYS: Record<string, string> = {
  NOT_FOUND: "linkNotFound.reasonNotFound",
  EXPIRED: "linkNotFound.reasonExpired",
  DISABLED: "linkNotFound.reasonDisabled",
  CAMPAIGN_PAUSED: "linkNotFound.reasonCampaignPaused",
  CAMPAIGN_ARCHIVED: "linkNotFound.reasonCampaignArchived",
};

export function LinkNotFoundPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const reason = searchParams.get("reason") ?? "";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
      <Logo mark className="h-10 w-10" />
      <h1 className="text-lg font-semibold">{t("linkNotFound.title")}</h1>
      <p className="max-w-sm text-sm text-muted-foreground">
        {t(REASON_KEYS[reason] ?? "linkNotFound.reasonGeneric")}
      </p>
    </div>
  );
}
