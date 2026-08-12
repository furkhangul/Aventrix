import { ShieldQuestion } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingState } from "@/components/ui/states";
import { isApiError } from "@/hooks/use-auth";
import { useLinkMeta, useResolveLink } from "@/hooks/use-tracking";

export function ConsentGatePage() {
  const { t } = useTranslation();
  const { code } = useParams<{ code: string }>();
  const { data: meta, isLoading, isError } = useLinkMeta(code);
  const resolve = useResolveLink(code);
  const [password, setPassword] = useState("");

  const proceed = (consent: boolean) => {
    resolve.mutate(
      { password: password || undefined, consent },
      { onSuccess: (data) => { window.location.href = data.target_url; } },
    );
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState label={t("consentGate.checkingLink")} />
      </div>
    );
  }

  if (isError || !meta) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
        <Logo mark className="h-10 w-10" />
        <h1 className="text-lg font-semibold">{t("consentGate.linkUnavailableTitle")}</h1>
        <p className="max-w-sm text-sm text-muted-foreground">{t("consentGate.linkUnavailableBody")}</p>
      </div>
    );
  }

  const errorMessage = resolve.isError
    ? isApiError(resolve.error)
      ? resolve.error.message
      : t("common.somethingWentWrong")
    : null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4 py-12">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8">
        <div className="mb-6 flex justify-center">
          <Logo />
        </div>

        {meta.needs_consent && (
          <div className="mb-6 space-y-2 rounded-lg border border-border bg-muted/40 p-4">
            <div className="flex items-center gap-2">
              <ShieldQuestion className="h-4 w-4 text-primary" />
              <p className="text-sm font-medium">{t("consentGate.beforeYouContinue")}</p>
            </div>
            <p className="text-sm text-muted-foreground">{t("consentGate.consentBody")}</p>
          </div>
        )}

        {meta.needs_password && (
          <div className="mb-6 space-y-1.5">
            <Label htmlFor="link-password">{t("consentGate.passwordProtectedLabel")}</Label>
            <Input
              id="link-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t("consentGate.passwordPlaceholder")}
              autoFocus
            />
          </div>
        )}

        {errorMessage && <p className="mb-4 text-sm text-destructive">{errorMessage}</p>}

        {meta.needs_consent ? (
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1" disabled={resolve.isPending} onClick={() => proceed(false)}>
              {t("consentGate.decline")}
            </Button>
            <Button className="flex-1" disabled={resolve.isPending} onClick={() => proceed(true)}>
              {resolve.isPending ? t("consentGate.continuing") : t("consentGate.acceptAndContinue")}
            </Button>
          </div>
        ) : (
          <Button className="w-full" disabled={resolve.isPending} onClick={() => proceed(true)}>
            {resolve.isPending ? t("consentGate.continuing") : t("consentGate.continueLabel")}
          </Button>
        )}
      </div>
    </div>
  );
}
