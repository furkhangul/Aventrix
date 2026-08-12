import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";
import { z } from "zod";
import { AuthLayout } from "@/components/layout/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { isApiError, useResetPassword } from "@/hooks/use-auth";

export function ResetPasswordPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const resetPassword = useResetPassword();

  const schema = z.object({
    new_password: z
      .string()
      .min(10, t("auth.validation.passwordMinLength"))
      .regex(/[a-z]/, t("auth.validation.passwordLowercase"))
      .regex(/[A-Z]/, t("auth.validation.passwordUppercase"))
      .regex(/\d/, t("auth.validation.passwordDigit")),
  });
  type Form = z.infer<typeof schema>;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema) });

  if (!token) {
    return (
      <AuthLayout title={t("auth.resetPassword.invalidLinkTitle")}>
        <p className="text-center text-sm text-muted-foreground">{t("auth.resetPassword.invalidLinkBody")}</p>
        <p className="mt-4 text-center">
          <Link to="/forgot-password" className="text-sm font-medium text-primary hover:underline">
            {t("auth.resetPassword.requestNewLink")}
          </Link>
        </p>
      </AuthLayout>
    );
  }

  if (resetPassword.isSuccess) {
    return (
      <AuthLayout title={t("auth.resetPassword.successTitle")}>
        <div className="flex flex-col items-center gap-3 text-center">
          <CheckCircle2 className="h-8 w-8 text-success" />
          <p className="text-sm text-muted-foreground">{t("auth.resetPassword.successBody")}</p>
          <Link to="/login" className="text-sm font-medium text-primary hover:underline">
            {t("auth.resetPassword.signIn")}
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title={t("auth.resetPassword.chooseNewTitle")}>
      <form
        onSubmit={handleSubmit((data) => resetPassword.mutate({ token, new_password: data.new_password }))}
        className="space-y-4"
      >
        <div className="space-y-1.5">
          <Label htmlFor="new_password">{t("auth.resetPassword.newPassword")}</Label>
          <Input id="new_password" type="password" autoComplete="new-password" {...register("new_password")} />
          {errors.new_password && <p className="text-xs text-destructive">{errors.new_password.message}</p>}
        </div>
        {resetPassword.isError && (
          <p className="text-xs text-destructive">
            {isApiError(resetPassword.error) ? resetPassword.error.message : t("common.somethingWentWrong")}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={resetPassword.isPending}>
          {resetPassword.isPending ? t("auth.resetPassword.saving") : t("auth.resetPassword.resetPassword")}
        </Button>
      </form>
    </AuthLayout>
  );
}
