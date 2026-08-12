import { zodResolver } from "@hookform/resolvers/zod";
import { ShieldCheck, ShieldOff } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  isApiError,
  useChangePassword,
  useConfirmTwoFactor,
  useDisableTwoFactor,
  useMe,
  useSetupTwoFactor,
} from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";

type PasswordForm = { current_password: string; new_password: string };

function ChangePasswordForm() {
  const { t } = useTranslation();
  const changePassword = useChangePassword();
  const { toast } = useToast();
  const passwordSchema = z.object({
    current_password: z.string().min(1, t("auth.validation.required")),
    new_password: z
      .string()
      .min(10, t("auth.validation.passwordMinLength"))
      .regex(/[a-z]/, t("auth.validation.passwordLowercase"))
      .regex(/[A-Z]/, t("auth.validation.passwordUppercase"))
      .regex(/\d/, t("auth.validation.passwordDigit")),
  });
  const { register, handleSubmit, reset, formState: { errors } } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  });

  return (
    <form
      className="space-y-4"
      onSubmit={handleSubmit((data) =>
        changePassword.mutate(data, {
          onSuccess: () => {
            toast({ title: t("settings.security.passwordChanged"), variant: "success" });
            reset();
          },
          onError: (error) =>
            toast({ title: t("settings.security.changeFailed"), description: isApiError(error) ? error.message : undefined, variant: "destructive" }),
        }),
      )}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="current_password">{t("settings.security.currentPassword")}</Label>
          <Input id="current_password" type="password" {...register("current_password")} />
          {errors.current_password && <p className="text-xs text-destructive">{errors.current_password.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="new_password">{t("settings.security.newPassword")}</Label>
          <Input id="new_password" type="password" {...register("new_password")} />
          {errors.new_password && <p className="text-xs text-destructive">{errors.new_password.message}</p>}
        </div>
      </div>
      <Button type="submit" disabled={changePassword.isPending}>
        {changePassword.isPending ? t("settings.security.updating") : t("settings.security.updatePassword")}
      </Button>
    </form>
  );
}

function TwoFactorSetupDialog({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const setup = useSetupTwoFactor();
  const confirm = useConfirmTwoFactor();
  const { toast } = useToast();
  const [step, setStep] = useState<"start" | "confirm" | "codes">("start");
  const [code, setCode] = useState("");
  const [secretData, setSecretData] = useState<{ secret: string; provisioning_uri: string; backup_codes: string[] } | null>(null);

  const start = () => {
    setup.mutate(undefined, {
      onSuccess: (data) => {
        setSecretData(data);
        setStep("confirm");
      },
    });
  };

  const confirmCode = () => {
    confirm.mutate(code, {
      onSuccess: () => setStep("codes"),
      onError: (error) => toast({ title: t("settings.security.invalidCode"), description: isApiError(error) ? error.message : undefined, variant: "destructive" }),
    });
  };

  if (step === "start") {
    return (
      <div className="space-y-4 text-center">
        <p className="text-sm text-muted-foreground">{t("settings.security.setupIntro")}</p>
        <Button onClick={start} disabled={setup.isPending}>
          {setup.isPending ? t("settings.security.starting") : t("settings.security.getStarted")}
        </Button>
      </div>
    );
  }

  if (step === "confirm" && secretData) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">{t("settings.security.confirmIntro")}</p>
        <div className="break-all rounded-md border border-border bg-muted/40 p-3 text-center text-xs font-mono">
          {secretData.secret}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="totp-code">{t("settings.security.sixDigitCode")}</Label>
          <Input id="totp-code" value={code} onChange={(e) => setCode(e.target.value)} placeholder="123456" autoFocus />
        </div>
        <Button className="w-full" onClick={confirmCode} disabled={confirm.isPending || code.length < 6}>
          {confirm.isPending ? t("settings.security.verifying") : t("settings.security.enable2faButton")}
        </Button>
      </div>
    );
  }

  if (step === "codes" && secretData) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">{t("settings.security.backupCodesIntro")}</p>
        <div className="grid grid-cols-2 gap-2 rounded-md border border-border bg-muted/40 p-3 font-mono text-sm">
          {secretData.backup_codes.map((c) => (
            <span key={c}>{c}</span>
          ))}
        </div>
        <Button className="w-full" onClick={onDone}>
          {t("common.done")}
        </Button>
      </div>
    );
  }

  return null;
}

function DisableTwoFactorDialog({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const disable = useDisableTwoFactor();
  const { toast } = useToast();
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{t("settings.security.disableIntro")}</p>
      <div className="space-y-1.5">
        <Label htmlFor="disable-password">{t("settings.security.password")}</Label>
        <Input id="disable-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="disable-code">{t("settings.security.codeOrBackup")}</Label>
        <Input id="disable-code" value={code} onChange={(e) => setCode(e.target.value)} />
      </div>
      <Button
        variant="destructive"
        className="w-full"
        disabled={disable.isPending}
        onClick={() =>
          disable.mutate(
            { password, code },
            {
              onSuccess: () => {
                toast({ title: t("settings.security.twoFactorDisabled") });
                onDone();
              },
              onError: (error) => toast({ title: t("settings.security.disableFailed"), description: isApiError(error) ? error.message : undefined, variant: "destructive" }),
            },
          )
        }
      >
        {disable.isPending ? t("settings.security.disabling") : t("settings.security.disable2faButton")}
      </Button>
    </div>
  );
}

export function SecuritySection() {
  const { t } = useTranslation();
  const { data: user } = useMe();
  const [dialogOpen, setDialogOpen] = useState<"setup" | "disable" | null>(null);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{t("settings.security.changePasswordTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ChangePasswordForm />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>{t("settings.security.twoFactorTitle")}</CardTitle>
          {user?.is_2fa_enabled ? (
            <Badge variant="success">{t("settings.security.enabled")}</Badge>
          ) : (
            <Badge variant="outline">{t("settings.security.disabled")}</Badge>
          )}
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-muted-foreground">{t("settings.security.twoFactorBody")}</p>
          {user?.is_2fa_enabled ? (
            <Button variant="outline" onClick={() => setDialogOpen("disable")}>
              <ShieldOff className="h-4 w-4" /> {t("settings.security.disable2fa")}
            </Button>
          ) : (
            <Button onClick={() => setDialogOpen("setup")}>
              <ShieldCheck className="h-4 w-4" /> {t("settings.security.enable2fa")}
            </Button>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen === "setup"} onOpenChange={(open) => !open && setDialogOpen(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("settings.security.setupTitle")}</DialogTitle>
          </DialogHeader>
          <TwoFactorSetupDialog onDone={() => setDialogOpen(null)} />
        </DialogContent>
      </Dialog>

      <Dialog open={dialogOpen === "disable"} onOpenChange={(open) => !open && setDialogOpen(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("settings.security.disableTitle")}</DialogTitle>
          </DialogHeader>
          <DisableTwoFactorDialog onDone={() => setDialogOpen(null)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
