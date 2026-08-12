import { zodResolver } from "@hookform/resolvers/zod";
import { useRef } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { isApiError, useMe, useUpdateProfile, useUploadAvatar } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";

const schema = z.object({ full_name: z.string().max(150).optional() });
type Form = z.infer<typeof schema>;

export function ProfileSection() {
  const { t } = useTranslation();
  const { data: user } = useMe();
  const updateProfile = useUpdateProfile();
  const uploadAvatar = useUploadAvatar();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { register, handleSubmit } = useForm<Form>({
    resolver: zodResolver(schema),
    values: { full_name: user?.full_name ?? "" },
  });

  const initials = (user?.full_name || user?.email || "?").slice(0, 2).toUpperCase();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("settings.profile.title")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            {user?.avatar_url && <AvatarImage src={user.avatar_url} alt={user.full_name ?? ""} />}
            <AvatarFallback className="text-lg">{initials}</AvatarFallback>
          </Avatar>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                uploadAvatar.mutate(file, {
                  onSuccess: () => toast({ title: t("settings.profile.avatarUpdated"), variant: "success" }),
                  onError: (error) =>
                    toast({ title: t("settings.profile.uploadFailed"), description: isApiError(error) ? error.message : undefined, variant: "destructive" }),
                });
              }}
            />
            <Button type="button" variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploadAvatar.isPending}>
              {uploadAvatar.isPending ? t("common.uploading") : t("settings.profile.changeAvatar")}
            </Button>
            <p className="mt-1 text-xs text-muted-foreground">{t("settings.profile.avatarHint")}</p>
          </div>
        </div>

        <form
          className="space-y-4"
          onSubmit={handleSubmit((data) =>
            updateProfile.mutate(data, { onSuccess: () => toast({ title: t("settings.profile.profileUpdated"), variant: "success" }) }),
          )}
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="full_name">{t("settings.profile.fullName")}</Label>
              <Input id="full_name" {...register("full_name")} />
            </div>
            <div className="space-y-1.5">
              <Label>{t("settings.profile.email")}</Label>
              <Input value={user?.email ?? ""} disabled />
            </div>
          </div>
          <Button type="submit" disabled={updateProfile.isPending}>
            {updateProfile.isPending ? t("common.saving") : t("common.saveChanges")}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
