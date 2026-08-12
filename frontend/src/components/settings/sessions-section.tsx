import { Laptop } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/ui/states";
import { useRevokeSession, useSessions } from "@/hooks/use-auth";
import { formatDateTime } from "@/lib/utils";

export function SessionsSection() {
  const { t } = useTranslation();
  const { data: sessions, isLoading } = useSessions();
  const revokeSession = useRevokeSession();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("settings.sessions.title")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <LoadingState />
        ) : (
          sessions?.map((session) => (
            <div key={session.id} className="flex items-center justify-between gap-4 rounded-md border border-border p-3">
              <div className="flex items-start gap-3">
                <Laptop className="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{session.user_agent ?? t("settings.sessions.unknownDevice")}</p>
                    {session.is_current && <Badge variant="success">{t("settings.sessions.thisDevice")}</Badge>}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {session.ip_address ?? t("settings.sessions.unknownIp")} &middot;{" "}
                    {t("settings.sessions.lastActive", { date: formatDateTime(session.last_used_at) })}
                  </p>
                </div>
              </div>
              {!session.is_current && (
                <Button variant="outline" size="sm" onClick={() => revokeSession.mutate(session.id)} disabled={revokeSession.isPending}>
                  {t("settings.sessions.revoke")}
                </Button>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
