import { useTranslation } from "react-i18next";
import { DangerZone } from "@/components/settings/danger-zone";
import { ProfileSection } from "@/components/settings/profile-section";
import { SecuritySection } from "@/components/settings/security-section";
import { SessionsSection } from "@/components/settings/sessions-section";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function SettingsPage() {
  const { t } = useTranslation();
  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{t("settings.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("settings.subtitle")}</p>
      </div>

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">{t("settings.tabProfile")}</TabsTrigger>
          <TabsTrigger value="security">{t("settings.tabSecurity")}</TabsTrigger>
          <TabsTrigger value="sessions">{t("settings.tabSessions")}</TabsTrigger>
          <TabsTrigger value="danger">{t("settings.tabDanger")}</TabsTrigger>
        </TabsList>
        <TabsContent value="profile">
          <ProfileSection />
        </TabsContent>
        <TabsContent value="security">
          <SecuritySection />
        </TabsContent>
        <TabsContent value="sessions">
          <SessionsSection />
        </TabsContent>
        <TabsContent value="danger">
          <DangerZone />
        </TabsContent>
      </Tabs>
    </div>
  );
}
