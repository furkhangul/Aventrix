import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { AuthLayout } from "@/components/layout/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { isApiError, useLogin, useVerifyTwoFactorLogin } from "@/hooks/use-auth";

export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const login = useLogin();
  const verifyTwoFactor = useVerifyTwoFactorLogin();
  const [pendingToken, setPendingToken] = useState<string | null>(null);

  const loginSchema = z.object({
    email: z.string().email(t("auth.validation.emailInvalid")),
    password: z.string().min(1, t("auth.validation.passwordRequired")),
  });
  type LoginForm = z.infer<typeof loginSchema>;

  const codeSchema = z.object({ code: z.string().min(6, t("auth.validation.sixDigitCode")) });
  type CodeForm = z.infer<typeof codeSchema>;

  const from = (location.state as { from?: Location })?.from?.pathname ?? "/";

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const {
    register: registerCode,
    handleSubmit: handleCodeSubmit,
    formState: { errors: codeErrors },
  } = useForm<CodeForm>({ resolver: zodResolver(codeSchema) });

  const onSubmit = (data: LoginForm) => {
    login.mutate(data, {
      onSuccess: (result) => {
        if (result.requires_2fa && result.two_factor_pending_token) {
          setPendingToken(result.two_factor_pending_token);
        } else {
          navigate(from, { replace: true });
        }
      },
    });
  };

  const onSubmitCode = (data: CodeForm) => {
    if (!pendingToken) return;
    verifyTwoFactor.mutate(
      { two_factor_pending_token: pendingToken, code: data.code },
      { onSuccess: () => navigate(from, { replace: true }) },
    );
  };

  if (pendingToken) {
    return (
      <AuthLayout title={t("auth.login.twoFactorTitle")} description={t("auth.login.twoFactorSubtitle")}>
        <form onSubmit={handleCodeSubmit(onSubmitCode)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="code">{t("auth.login.authCode")}</Label>
            <Input id="code" inputMode="numeric" autoFocus placeholder="123456" {...registerCode("code")} />
            {codeErrors.code && <p className="text-xs text-destructive">{codeErrors.code.message}</p>}
          </div>
          {verifyTwoFactor.isError && (
            <p className="text-xs text-destructive">
              {isApiError(verifyTwoFactor.error) ? verifyTwoFactor.error.message : t("auth.login.verificationFailed")}
            </p>
          )}
          <Button type="submit" className="w-full" disabled={verifyTwoFactor.isPending}>
            {verifyTwoFactor.isPending ? t("auth.login.verifying") : t("auth.login.verify")}
          </Button>
        </form>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title={t("auth.login.title")} description={t("auth.login.subtitle")}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="email">{t("auth.login.email")}</Label>
          <Input id="email" type="email" autoComplete="email" placeholder="you@example.com" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">{t("auth.login.password")}</Label>
            <Link to="/forgot-password" className="text-xs text-primary hover:underline">
              {t("auth.login.forgotPassword")}
            </Link>
          </div>
          <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>
        {login.isError && (
          <p className="text-xs text-destructive">
            {isApiError(login.error) ? login.error.message : t("common.somethingWentWrong")}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? t("auth.login.signingIn") : t("auth.login.signIn")}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        {t("auth.login.noAccount")}{" "}
        <Link to="/register" className="font-medium text-primary hover:underline">
          {t("auth.login.createOne")}
        </Link>
      </p>
    </AuthLayout>
  );
}
