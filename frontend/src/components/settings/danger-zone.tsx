import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { isApiError, useDeleteAccount } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";

export function DangerZone() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const deleteAccount = useDeleteAccount();
  const { toast } = useToast();
  const navigate = useNavigate();

  return (
    <Card className="border-destructive/30">
      <CardHeader>
        <CardTitle className="text-destructive">{t("settings.danger.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-4 text-sm text-muted-foreground">{t("settings.danger.body")}</p>
        <Button variant="destructive" onClick={() => setOpen(true)}>
          {t("settings.danger.deleteAccount")}
        </Button>
      </CardContent>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("settings.danger.confirmTitle")}</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">{t("settings.danger.confirmBody")}</p>
          <div className="space-y-1.5">
            <Label htmlFor="delete-password">{t("settings.danger.password")}</Label>
            <Input id="delete-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {deleteAccount.isError && (
            <p className="text-xs text-destructive">
              {isApiError(deleteAccount.error) ? deleteAccount.error.message : t("common.somethingWentWrong")}
            </p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button
              variant="destructive"
              disabled={deleteAccount.isPending}
              onClick={() =>
                deleteAccount.mutate(password, {
                  onSuccess: () => {
                    toast({ title: t("settings.danger.accountDeleted") });
                    navigate("/login", { replace: true });
                  },
                })
              }
            >
              {deleteAccount.isPending ? t("common.deleting") : t("settings.danger.permanentlyDelete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
