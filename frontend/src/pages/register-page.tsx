import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { AuthLayout } from "@/components/layout/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { isApiError, useRegister } from "@/hooks/use-auth";

export function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const registerMutation = useRegister();

  const registerSchema = z.object({
    full_name: z.string().min(1, t("auth.validation.nameRequired")).max(150),
    email: z.string().email(t("auth.validation.emailInvalid")),
    password: z
      .string()
      .min(10, t("auth.validation.passwordMinLength"))
      .regex(/[a-z]/, t("auth.validation.passwordLowercase"))
      .regex(/[A-Z]/, t("auth.validation.passwordUppercase"))
      .regex(/\d/, t("auth.validation.passwordDigit")),
  });
  type RegisterForm = z.infer<typeof registerSchema>;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  const onSubmit = (data: RegisterForm) => {
    registerMutation.mutate(data, { onSuccess: () => navigate("/", { replace: true }) });
  };

  return (
    <AuthLayout title={t("auth.register.title")} description={t("auth.register.subtitle")}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="full_name">{t("auth.register.fullName")}</Label>
          <Input id="full_name" autoComplete="name" placeholder="Ada Lovelace" {...register("full_name")} />
          {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">{t("auth.register.email")}</Label>
          <Input id="email" type="email" autoComplete="email" placeholder="you@example.com" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">{t("auth.register.password")}</Label>
          <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
          {errors.password ? (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          ) : (
            <p className="text-xs text-muted-foreground">{t("auth.register.passwordHint")}</p>
          )}
        </div>
        {registerMutation.isError && (
          <p className="text-xs text-destructive">
            {isApiError(registerMutation.error) ? registerMutation.error.message : t("common.somethingWentWrong")}
          </p>
        )}
        <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
          {registerMutation.isPending ? t("auth.register.creatingAccount") : t("auth.register.createAccount")}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        {t("auth.register.haveAccount")}{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">
          {t("auth.register.signIn")}
        </Link>
      </p>
    </AuthLayout>
  );
}
