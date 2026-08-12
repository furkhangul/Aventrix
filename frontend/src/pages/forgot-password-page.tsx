import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { z } from "zod";
import { AuthLayout } from "@/components/layout/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useForgotPassword } from "@/hooks/use-auth";

export function ForgotPasswordPage() {
  const { t } = useTranslation();
  const forgotPassword = useForgotPassword();
  const schema = z.object({ email: z.string().email(t("auth.validation.emailInvalid")) });
  type Form = z.infer<typeof schema>;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema) });

  if (forgotPassword.isSuccess) {
    return (
      <AuthLayout title={t("auth.forgotPassword.checkEmailTitle")}>
        <div className="flex flex-col items-center gap-3 text-center">
          <CheckCircle2 className="h-8 w-8 text-success" />
          <p className="text-sm text-muted-foreground">{t("auth.forgotPassword.checkEmailBody")}</p>
          <Link to="/login" className="text-sm font-medium text-primary hover:underline">
            {t("auth.forgotPassword.backToSignIn")}
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title={t("auth.forgotPassword.title")} description={t("auth.forgotPassword.subtitle")}>
      <form onSubmit={handleSubmit((data) => forgotPassword.mutate(data))} className="space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="email">{t("auth.forgotPassword.email")}</Label>
          <Input id="email" type="email" autoComplete="email" placeholder="you@example.com" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <Button type="submit" className="w-full" disabled={forgotPassword.isPending}>
          {forgotPassword.isPending ? t("auth.forgotPassword.sending") : t("auth.forgotPassword.sendResetLink")}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        <Link to="/login" className="font-medium text-primary hover:underline">
          {t("auth.forgotPassword.backToSignIn")}
        </Link>
      </p>
    </AuthLayout>
  );
}
