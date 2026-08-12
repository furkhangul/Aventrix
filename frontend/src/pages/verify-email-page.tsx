import { CheckCircle2, XCircle } from "lucide-react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";
import { AuthLayout } from "@/components/layout/auth-layout";
import { LoadingState } from "@/components/ui/states";
import { isApiError, useVerifyEmail } from "@/hooks/use-auth";

export function VerifyEmailPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const verifyEmail = useVerifyEmail();

  useEffect(() => {
    if (token) verifyEmail.mutate({ token });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <AuthLayout title={t("auth.verifyEmail.title")}>
      {!token ? (
        <p className="text-center text-sm text-muted-foreground">{t("auth.verifyEmail.missingToken")}</p>
      ) : verifyEmail.isPending || verifyEmail.isIdle ? (
        <LoadingState label={t("auth.verifyEmail.verifying")} />
      ) : verifyEmail.isSuccess ? (
        <div className="flex flex-col items-center gap-3 text-center">
          <CheckCircle2 className="h-8 w-8 text-success" />
          <p className="text-sm text-muted-foreground">{t("auth.verifyEmail.verifiedBody")}</p>
          <Link to="/" className="text-sm font-medium text-primary hover:underline">
            {t("auth.verifyEmail.goToDashboard")}
          </Link>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3 text-center">
          <XCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm text-muted-foreground">
            {isApiError(verifyEmail.error) ? verifyEmail.error.message : t("auth.verifyEmail.invalidOrExpired")}
          </p>
          <Link to="/login" className="text-sm font-medium text-primary hover:underline">
            {t("auth.verifyEmail.backToSignIn")}
          </Link>
        </div>
      )}
    </AuthLayout>
  );
}
